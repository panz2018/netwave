"""Wiring smoke test for the browser rust coverage chain (browser-driven).

The chain is a long shell sequence in browser/scripts/test.sh that CI's
browser job and local `pnpm test:browser` share, so a silent edit that drops a step (the
instrumented build, the glue regeneration, the profraw merge, the lcov export,
or the gate) would quietly stop measuring core's browser-gated code. These
assertions pin that every link is present, that the toolchain probes head the
script before any build, that the dump run drives the REAL browser (the fetch
backends resolve only against a real global scope), and that ci.yml uploads the
lcov artifact the chain actually produces (not a codecov.json llvm-cov cannot
emit)."""

import re

import pytest
from lib.repository import ROOT

CI = ROOT / ".github" / "workflows" / "ci.yml"
TEST_BROWSER = ROOT / "browser" / "scripts" / "test.sh"
WORKER_BUNDLE = ROOT / "browser" / "dist" / "netwave.worker.js"


def _script() -> str:
    return TEST_BROWSER.read_text(encoding="utf-8")


def test_published_worker_bundle_has_no_coverage_code() -> None:
    # The published worker MUST NOT ship the coverage-chain scaffolding
    # (dumpCoverage/driveCoverage/installFetchStub, the __cov_* dump exports,
    # the NETWAVE_WASM_DIR probe). tsdown fills __NETWAVE_COVERAGE__=false and
    # dce-only + tree-shaking strip the guarded blocks and the side-effect-free
    # coverage-dump module. dist is a build artifact (gitignored); when present
    # it MUST be clean — the publish gate in publish_shell.mjs enforces this at
    # build time, this assertion re-checks the produced bundle.
    if not WORKER_BUNDLE.exists():
        pytest.skip("browser/dist is a build artifact; run `pnpm -C browser build:browser`")
    hits = re.findall(
        r"dumpCoverage|__cov|NETWAVE_WASM_DIR", WORKER_BUNDLE.read_text(encoding="utf-8")
    )
    assert not hits, f"published worker bundle leaks coverage code: {sorted(set(hits))}"


def test_ci_uploads_browser_lcov_not_json() -> None:
    ci = CI.read_text(encoding="utf-8")
    assert "path: coverage/coverage-browser.lcov" in ci
    # the chain produces lcov; a stale .json upload path would fail CI.
    assert "coverage/coverage-browser.json" not in ci


def test_chain_builds_instrumented_wasm_with_coverage_feature() -> None:
    s = _script()
    assert "--features coverage" in s
    # wasm-pack cannot build instrumented output, so the chain uses cargo build.
    assert "cargo build --manifest-path browser/Cargo.toml" in s
    assert "-Cinstrument-coverage -Zno-profiler-runtime --emit=llvm-ir" in s


def test_chain_regenerates_glue_and_drives_real_browser() -> None:
    s = _script()
    assert "wasm-bindgen --target web" in s
    # the dump run points the worker at the instrumented glue and a profraw dir.
    assert "NETWAVE_WASM_DIR=" in s
    assert "NETWAVE_COV_OUT=" in s
    # the dump run drives the REAL browser (fetch arms need a real global scope);
    # v8 coverage is off for it, the plain production test:e2e enforces that.
    assert "test:e2e --coverage.enabled=false" in s


def test_chain_grades_lcov_via_gate() -> None:
    s = _script()
    assert "llvm-profdata" in s and "merge -sparse" in s
    # llc needs the short host arch, not the full triple.
    assert re.search(r'llc"?\s+--march=', s) or "--march=" in s
    assert "llvm-cov" in s and "--format=lcov" in s
    # third-party crates must stay out of the denominator, on every host:
    # Windows reports C:\...\cargo\registry (backslash), so the regex must use
    # a [\\/]+ separator class, never a bare slash.
    assert "--ignore-filename-regex" in s
    assert re.search(r"\.cargo\[\\\\/\]\+registry", s)
    assert "coverage_gate.py coverage/coverage-browser.lcov 99" in s


def test_ignore_regex_excludes_third_party_on_both_hosts() -> None:
    # Behavioural check (not just a static substring): extract the real
    # --ignore-filename-regex value the script passes to llvm-cov and run it
    # against the exact path strings each host reports. A bare-slash regex
    # matches zero Windows paths, letting third-party lines leak into the
    # denominator. The pattern uses POSIX ERE semantics; for this
    # char-class-plus-quantifier form Python's re matches identically.
    m = re.search(r"--ignore-filename-regex='([^']+)'", _script())
    assert m, "the chain must pass --ignore-filename-regex to llvm-cov"
    pattern = m.group(1)
    # Windows: llvm-cov reports the cargo home with backslashes (CI log verbatim).
    windows = (
        r"C:\Users\runneradmin\.cargo\registry\src\index.crates.io-1949cf8c6b5b557f"
        r"\js-sys-0.3.107\src\futures\jspi.rs"
    )
    # Linux: forward slashes.
    linux = "/home/runner/.cargo/registry/src/index.crates.io/js-sys-0.3.107/jspi.rs"
    # netwave's own source must stay in the denominator on both hosts.
    own_windows = r"D:\a\netwave\netwave\core\src\touchstone.rs"
    own_linux = "/home/runner/netwave/core/src/touchstone.rs"
    assert re.search(pattern, windows), "must exclude third-party on Windows"
    assert re.search(pattern, linux), "must exclude third-party on Linux"
    assert not re.search(pattern, own_windows), "must keep netwave core (Windows)"
    assert not re.search(pattern, own_linux), "must keep netwave core (Linux)"


def test_probes_head_the_script_before_any_build() -> None:
    lines = _script().splitlines()

    def first(pattern: str) -> int:
        return next(i for i, ln in enumerate(lines) if re.search(pattern, ln))

    probe_llvm = first(r"component add llvm-tools")
    probe_wasi = first(r"install_wasi_sdk\.sh")
    probe_bindgen = first(r"install_wasm_bindgen_cli\.sh")
    build = first(r"cargo build --manifest-path browser/Cargo\.toml")
    # every coverage-tool probe must precede the instrumented build.
    assert max(probe_llvm, probe_wasi, probe_bindgen) < build


def test_post_block_drains_stray_profraw() -> None:
    # a broken chain this round must be detected by the stray drain, never
    # pushed past the gate by a later-appended command.
    lines = _script().splitlines()
    drain = [i for i, ln in enumerate(lines) if "clean_stray_profraw.py" in ln]
    gate = [i for i, ln in enumerate(lines) if "coverage_gate.py" in ln]
    assert drain and gate and max(drain) > max(gate)
