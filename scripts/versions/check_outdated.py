#!/usr/bin/env python3
"""Freshness check (networked — runs at the end of every OpenSpec apply;
never a CI gate).

Four segments, per the dependency-upgrade spec:
  1. Project deps: pnpm -r outdated (all workspace packages) / cargo update
     --dry-run (whole workspace lock) / uv lock --upgrade --dry-run for every
     uv project found (any uv.lock), plus every runtime pin
     (.python-version vs latest stable minor). For every package named in
     scripts/versions/restrictions.json, one target line per locked package:
     the highest published version that forms no recorded bad combo with the
     repo's current peers — locked versions ∪ runtime pins (SKIP names the
     recorded reason).
  2. Global CLIs: installed --version vs newest LTS/stable (endoflife.date,
     npm registry, GitHub releases; node refined to the newest patch on the
     LTS line via nodejs.org).
  3. GitHub-tarball tools & cargo subcommands: installed version vs the
     repo's latest release.
  4. CI actions: `uses:` tags in .github/workflows vs latest release tag.

Every segment filters its latest through the bad-combo judgement before
reporting (spec「过期体检命令」): a latest that forms a recorded combo with
the current peers reports the highest free target plus `SKIP <reason>`.

Exit codes: an unreachable source retries once, then SKIPs — the line names
the source and the exit code is unaffected (network luck is not a failure).
FAILED (non-zero exit) stays reserved for real errors: a local probe command
that cannot run, or restrictions.json breaking its contract (the judgement
baseline would be misleading, so the report aborts with FAILED instead).
Probes and section layout live here (spec: probe set is a program constant);
networking and comparison live in lib/latest.py and lib/version.py, bad-combo
judgement in lib/restrictions.py.
Usage: python3 scripts/versions/check_outdated.py   (pnpm check:outdated)
"""

import sys

from lib.latest import (
    action_refs,
    fetch_json,
    find_uv_projects,
    first_line,
    freshness_mark,
    is_version_tag,
    latest_version,
    package_versions,
    refine_node_lts,
    run_cmd,
)
from lib.repository import ROOT, find_python_versions, runtime_pins
from lib.restrictions import (
    RestrictionFormatError,
    is_restricted,
    load_restrictions,
    locked_versions,
    pick_unrestricted,
)
from lib.version import is_major_only, is_outdated


def section(title: str) -> None:
    print(f"\n=== {title} ===")


# probe set as program constants (add a probe = edit here)
PROBES = [
    ("node", "node --version", ("endoflife", "nodejs", "lts")),
    ("npm", "npm --version", ("npm", "npm")),
    ("pnpm", "pnpm --version", ("npm", "pnpm")),
    ("uv", "uv --version", ("github", "astral-sh/uv")),
    ("rustup", "rustup --version", ("github-tags", "rust-lang/rustup")),
    ("rustc", "rustc --version", ("endoflife", "rust", "stable")),
    ("openspec", "openspec --version", ("npm", "@fission-ai/openspec")),
    ("markdownlint-cli2", "markdownlint-cli2 --version", ("npm", "markdownlint-cli2")),
]

# probes whose latest is judgeable against records (registered names only —
# CI actions carry no ecosystem prefix and can never appear in a combo)
PROBE_NAMES = {
    "node": "npm:node",
    "npm": "npm:npm",
    "pnpm": "npm:pnpm",
    "rustc": "cargo:rustc",
    "cargo-llvm-cov": "cargo:cargo-llvm-cov",
}


def _retry(call):
    """Networked probe with one immediate retry (spec: 断网重试一次); the
    second failure propagates and the caller reports SKIP."""
    try:
        return call()
    except Exception:  # noqa: BLE001
        return call()


def target_line(
    name: str, installed: str, latest: str, peers: dict[str, str], restrictions: list
) -> str:
    """Tail of a comparison line: the plain OK/LAG/? mark when the latest is
    unrestricted or the probe has no registrable name; otherwise the highest
    free target plus `SKIP <reason>` (spec「过期体检命令」, all segments).
    Published candidates come from the registry; when unavailable the latest
    alone is judged (single candidate)."""
    rname = PROBE_NAMES.get(name)
    if rname is None:
        return freshness_mark(installed, latest)
    ecosystem, _, package = rname.partition(":")
    try:
        candidates = _retry(lambda: package_versions(ecosystem, package)) or [latest]
    except Exception:  # noqa: BLE001
        candidates = [latest]
    target = pick_unrestricted(rname, candidates, peers, restrictions)
    reason = next(
        (r["reason"] for r in restrictions if is_restricted({**peers, rname: latest}, [r])),
        None,
    )
    if reason is None:
        return freshness_mark(installed, latest)
    if target is None:
        return f"target ?  no free version (all restricted) SKIP {reason}"
    return f"target {target:12s} {freshness_mark(installed, target)} SKIP {reason}"


def restricted_lines(restrictions: list, peers: dict[str, str], failures: list[str]) -> None:
    """One target line per package pinned here and named by a restriction
    record: the highest published version that avoids every recorded combo
    with the current peers (spec「版本限制记录与坏版本降级」). Only this
    package's target is adjusted; peer rows are untouched."""
    names = sorted({pkg for r in restrictions for combo in r["combos"] for pkg in combo})
    for name in names:
        if name not in peers:
            continue  # not pinned in this repo — record kept, can never hit
        ecosystem, _, package = name.partition(":")
        others = {n: v for n, v in peers.items() if n != name}
        try:
            candidates = _retry(lambda eco=ecosystem, pkg=package: package_versions(eco, pkg))
        except Exception as e:  # noqa: BLE001
            print(f"{name:24s} locked {peers[name]:10s} latest: SKIP ({e})")
            continue
        if not candidates:
            print(f"{name:24s} locked {peers[name]:10s} latest: SKIP (no stable version listed)")
            continue
        latest = candidates[-1]
        target = pick_unrestricted(name, candidates, others, restrictions)
        if target is None:
            print(f"{name:24s} locked {peers[name]:10s} target ?  no free version (all restricted)")
            continue
        reason = next(
            (r["reason"] for r in restrictions if is_restricted({**others, name: latest}, [r])),
            None,
        )
        tail = f"  SKIP {reason}" if reason else ""
        mark = "LAG" if target != latest else "OK"
        cols = f"{name:24s} locked {peers[name]:10s} latest {latest:10s} target {target:10s}"
        print(f"{cols} {mark}{tail}")


def main() -> int:
    failures: list[str] = []
    try:
        restrictions = load_restrictions(ROOT)
    except RestrictionFormatError as e:
        print(f"FAILED: restrictions.json ({e})")
        print("\ncheck:outdated done (informational; not a gate)")
        return 1
    names = sorted({pkg for r in restrictions for combo in r["combos"] for pkg in combo})
    peers = {**locked_versions(ROOT, names), **runtime_pins(ROOT)}

    # 1. project dependencies
    section("1. project dependencies")
    # every uv project in the repo (python/, oracle/golden/, ...) — discovery
    # by uv.lock, no hardcoded list, so new environments are covered automatically
    for proj in find_uv_projects():
        rc, out = run_cmd(f"uv lock --upgrade --dry-run --project {proj}")
        print(f"$ uv lock --upgrade --dry-run --project {proj}  (rc={rc})")
        print(out if out else "(no output)")

    for cmd in ("pnpm -r outdated", "cargo update --dry-run"):
        rc, out = run_cmd(cmd)
        print(f"$ {cmd}  (rc={rc})")
        print(out if out else "(no output)")
        if rc == 125:  # run_cmd sentinel: the command could not be run at all
            failures.append(cmd)

    # every runtime pin in the repo (.python-version): single-line runtime ->
    # latest stable minor, filtered through recorded combos like any other
    # segment (endoflife cycles are the candidate list)
    try:
        py_data = _retry(lambda: fetch_json("https://endoflife.date/api/python.json"))
        latest_py = str(py_data[0]["cycle"])
        cycles = [str(c["cycle"]) for c in py_data]
        for rel, pyver in find_python_versions(ROOT).items():
            head = f"python-version {rel:24s} {pyver:8s}"
            reason = next(
                (
                    r["reason"]
                    for r in restrictions
                    if is_restricted({**peers, "pypi:python": latest_py}, [r])
                ),
                None,
            )
            if reason is None:
                mark = "LAG" if is_outdated(pyver, latest_py) else "OK"
                print(f"{head} -> latest stable {latest_py:8s} {mark}")
                continue
            target = pick_unrestricted("pypi:python", cycles, peers, restrictions)
            if target is None:
                print(f"{head} -> target ?  no free version (all restricted) SKIP {reason}")
                continue
            mark = "LAG" if is_outdated(pyver, target) else "OK"
            print(f"{head} -> target {target:8s} {mark} SKIP {reason}")
    except Exception as e:  # noqa: BLE001
        print(f"python-version files: SKIP ({e})")

    restricted_lines(restrictions, peers, failures)

    # 2. global CLIs: installed vs newest LTS/stable
    section("2. global CLIs (installed vs newest LTS/stable)")
    for name, probe, source in PROBES:
        rc, installed = run_cmd(probe)
        installed = first_line(installed)
        rname = PROBE_NAMES.get(name)
        if rname is not None and rname in peers:
            # a repo pin (.nvmrc / packageManager / rust-toolchain.toml) is the
            # reproducible current version; the machine probe only backs it up
            installed = peers[rname]
        head = f"{name:18s} installed: {installed:28s}"
        if rc == 125:  # local probe cannot run — a real error, not network luck
            failures.append(name)
            print(f"{head} latest: WARN ({installed})")
            continue
        try:
            latest = _retry(lambda src=source: latest_version(src))
            if name == "node":
                latest = _retry(lambda lin=latest: refine_node_lts(lin))
        except Exception as e:  # noqa: BLE001
            print(f"{head} latest: SKIP ({e})")
            continue
        tail = target_line(name, installed, latest, peers, restrictions)
        print(f"{head} latest: {latest:12s} {tail}")

    # 3. github-tarball tools & cargo subcommands
    section("3. github-tarball tools & cargo subcommands")
    for name, probe, repo in (
        ("wasm-pack", "wasm-pack --version", "wasm-bindgen/wasm-pack"),
        ("binaryen (wasm-opt)", "wasm-opt --version", "WebAssembly/binaryen"),
        ("cargo-llvm-cov", "cargo llvm-cov --version", "taiki-e/cargo-llvm-cov"),
    ):
        rc, installed = run_cmd(probe)
        installed = first_line(installed)
        head = f"{name:22s} installed: {installed:28s}"
        if rc == 125:
            failures.append(name)
            print(f"{head} latest: WARN ({installed})")
            continue
        try:
            latest = _retry(lambda r=repo: latest_version(("github", r)))
        except Exception as e:  # noqa: BLE001
            print(f"{head} latest: SKIP ({e})")
            continue
        tail = target_line(name, installed, latest, peers, restrictions)
        print(f"{head} latest: {latest:12s} {tail}")

    # 4. CI actions
    section("4. CI actions (uses: tag vs latest release)")
    for repo, tag in sorted(action_refs()):
        if "/" not in repo or repo.count("/") > 1:
            print(f"{repo}@{tag}  (skip: not a github action path)")
            continue
        # A non-version ref (stable/main/...) is a moving branch, not a pinned
        # release — dtolnay/rust-toolchain@stable is the documented usage, so
        # it is never a "lag". Only semver tags are compared.
        if not is_version_tag(tag):
            print(f"{repo}@{tag:12s} latest: {'(ref)':12s} REF")
            continue
        try:
            latest = _retry(lambda r=repo: latest_version(("github", r)))
            # A major-only tag (v7, v6) auto-tracks the newest release in that
            # major, so only a major bump is a lag. A full/partial pin
            # (v10.2.0, v0.0.11) is compared against the exact latest.
            mark = "LAG" if is_outdated(tag, latest, major_only=is_major_only(tag)) else "OK"
            print(f"{repo}@{tag:12s} latest: {latest:12s} {mark}")
        except Exception as e:  # noqa: BLE001
            print(f"{repo}@{tag:12s} latest: SKIP ({e})")

    if failures:
        print(f"\nFAILED: {', '.join(failures)}")
    print("\ncheck:outdated done (informational; not a gate)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
