"""Wiring smoke test for the typescript test entry's wasm rust coverage chain.

The chain is a long shell sequence in scripts/run/test_ts.sh that CI's node job
and local `pnpm test:ts` share, so a silent edit that drops a step (the
instrumented build, the glue regeneration, the profraw merge, the lcov export,
or the gate) would quietly stop measuring core's browser-gated code. These
assertions pin that every link is present, that the toolchain probes head the
script before any build, and that ci.yml uploads the lcov artifact the chain
actually produces (not a codecov.json llvm-cov cannot emit)."""

import re

from lib.repository import ROOT

CI = ROOT / ".github" / "workflows" / "ci.yml"
TEST_TS = ROOT / "scripts" / "run" / "test_ts.sh"


def _script() -> str:
    return TEST_TS.read_text(encoding="utf-8")


def test_ci_uploads_wasm_lcov_not_json() -> None:
    ci = CI.read_text(encoding="utf-8")
    assert "path: coverage/coverage-wasm.lcov" in ci
    # the chain produces lcov; a stale .json upload path would fail CI.
    assert "coverage/coverage-wasm.json" not in ci


def test_chain_builds_instrumented_wasm_with_coverage_feature() -> None:
    s = _script()
    assert "--features coverage" in s
    # wasm-pack cannot build instrumented output, so the chain uses cargo build.
    assert "cargo build --manifest-path typescript/wasm/Cargo.toml" in s
    assert "-Cinstrument-coverage -Zno-profiler-runtime --emit=llvm-ir" in s


def test_chain_regenerates_glue_and_drives_test_wasm() -> None:
    s = _script()
    assert "wasm-bindgen --target web" in s
    # the dump run points the worker at the instrumented glue and a profraw dir.
    assert "NETWAVE_WASM_DIR=" in s
    assert "NETWAVE_COV_OUT=" in s
    # v8 coverage is off for the dump run; the plain test:wasm enforces it.
    assert "test:wasm --coverage.enabled=false" in s


def test_chain_grades_lcov_via_gate() -> None:
    s = _script()
    assert "llvm-profdata" in s and "merge -sparse" in s
    # llc needs the short host arch, not the full triple.
    assert re.search(r'llc"?\s+--march=', s) or "--march=" in s
    assert "llvm-cov" in s and "--format=lcov" in s
    # third-party crates must stay out of the denominator.
    assert "--ignore-filename-regex" in s and ".cargo/registry" in s
    assert "coverage_gate.py coverage/coverage-wasm.lcov 100" in s


def test_probes_head_the_script_before_any_build() -> None:
    lines = _script().splitlines()

    def first(pattern: str) -> int:
        return next(i for i, ln in enumerate(lines) if re.search(pattern, ln))

    probe_llvm = first(r"component add llvm-tools")
    probe_wasi = first(r"install_wasi_sdk\.sh")
    probe_bindgen = first(r"install_wasm_bindgen_cli\.sh")
    build = first(r"cargo build --manifest-path typescript/wasm/Cargo\.toml")
    # every coverage-tool probe must precede the instrumented build.
    assert max(probe_llvm, probe_wasi, probe_bindgen) < build


def test_post_block_drains_before_clean() -> None:
    lines = _script().splitlines()
    drain = [i for i, ln in enumerate(lines) if "clean_stray_profraw.py" in ln]
    clean = [i for i, ln in enumerate(lines) if "cargo llvm-cov clean" in ln]
    assert drain and clean and max(drain) < max(clean)
