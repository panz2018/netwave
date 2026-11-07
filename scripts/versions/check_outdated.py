#!/usr/bin/env python3
"""Freshness check (manual, networked — NOT a CI gate).

Four segments, per the dependency-upgrade spec:
  1. Project deps: pnpm -r outdated (all workspace packages) / cargo update
     --dry-run (whole workspace lock) / uv lock --upgrade --dry-run for every
     uv project found (any uv.lock, incl. oracle when it lands), plus every
     runtime pin (.python-version vs latest stable minor). For every package
     named in scripts/versions/restrictions.json, one target line per locked
     package: the highest published version that forms no recorded bad combo
     with the repo's other locked versions (SKIP names the recorded reason).
  2. Global CLIs: installed --version vs newest LTS/stable (endoflife.date,
     npm registry, GitHub releases; node refined to the newest patch on the
     LTS line via nodejs.org).
  3. GitHub-tarball tools & cargo subcommands: installed version vs the
     repo's latest release.
  4. CI actions: `uses:` tags in .github/workflows vs latest release tag.

A failing segment is reported and never aborts the rest; any failure makes
the command exit non-zero (FAILED names what could not be checked).
Exit code: 0 only when every probe answered.
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
from lib.repository import ROOT, find_python_versions
from lib.restrictions import is_restricted, load_restrictions, locked_versions, pick_unrestricted
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


def restricted_lines(failures: list[str]) -> None:
    """One target line per package locked here and named by a restriction
    record: the highest published version that avoids every recorded combo
    with the current peers (spec「版本限制记录与坏版本降级」). Only this
    package's target is adjusted; peer rows are untouched."""
    restrictions = load_restrictions(ROOT)
    names = sorted({pkg for r in restrictions for combo in r["combos"] for pkg in combo})
    locked = locked_versions(ROOT, names)
    for name in names:
        if name not in locked:
            continue  # not locked in this repo — record kept, can never hit
        ecosystem, _, package = name.partition(":")
        peers = {n: v for n, v in locked.items() if n != name}
        try:
            candidates = package_versions(ecosystem, package)
            if not candidates:
                raise RuntimeError("registry lists no stable version")
        except Exception as e:  # noqa: BLE001
            failures.append(name)
            print(f"{name:24s} locked {locked[name]:10s} latest: WARN ({e})")
            continue
        latest = candidates[-1]
        target = pick_unrestricted(name, candidates, peers, restrictions)
        if target is None:
            print(
                f"{name:24s} locked {locked[name]:10s} target ?  no free version (all restricted)"
            )
            continue
        reason = next(
            (r["reason"] for r in restrictions if is_restricted({**peers, name: latest}, [r])),
            None,
        )
        tail = f"  SKIP {reason}" if reason else ""
        mark = "LAG" if target != latest else "OK"
        cols = f"{name:24s} locked {locked[name]:10s} latest {latest:10s} target {target:10s}"
        print(f"{cols} {mark}{tail}")


def main() -> int:
    failures: list[str] = []

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
    # latest stable minor (dependency-upgrade spec line rule)
    try:
        py_data = fetch_json("https://endoflife.date/api/python.json")
        latest_py = str(py_data[0]["cycle"])
        for rel, pyver in find_python_versions(ROOT).items():
            mark = "LAG" if is_outdated(pyver, latest_py) else "OK"
            print(f"python-version {rel:24s} {pyver:8s} -> latest stable {latest_py:8s} {mark}")
    except Exception as e:  # noqa: BLE001
        failures.append("endoflife.date (python)")
        print(f"python-version files: WARN ({e})")

    restricted_lines(failures)

    # 2. global CLIs: installed vs newest LTS/stable
    section("2. global CLIs (installed vs newest LTS/stable)")
    for name, probe, source in PROBES:
        rc, installed = run_cmd(probe)
        installed = first_line(installed)
        try:
            latest = latest_version(source)
            if name == "node":
                latest = refine_node_lts(latest)
            print(
                f"{name:18s} installed: {installed:28s} latest: {latest:12s} "
                f"{freshness_mark(installed, latest)}"
            )
        except Exception as e:  # noqa: BLE001
            failures.append(name)
            print(f"{name:18s} installed: {installed:28s} latest: WARN ({e})")

    # 3. github-tarball tools & cargo subcommands
    section("3. github-tarball tools & cargo subcommands")
    for name, probe, repo in (
        ("wasm-pack", "wasm-pack --version", "wasm-bindgen/wasm-pack"),
        ("binaryen (wasm-opt)", "wasm-opt --version", "WebAssembly/binaryen"),
        ("cargo-llvm-cov", "cargo llvm-cov --version", "taiki-e/cargo-llvm-cov"),
    ):
        rc, installed = run_cmd(probe)
        installed = first_line(installed)
        try:
            latest = latest_version(("github", repo))
            print(
                f"{name:22s} installed: {installed:28s} latest: {latest:12s} "
                f"{freshness_mark(installed, latest)}"
            )
        except Exception as e:  # noqa: BLE001
            failures.append(name)
            print(f"{name:22s} installed: {installed:28s} latest: WARN ({e})")

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
            latest = latest_version(("github", repo))
            # A major-only tag (v7, v6) auto-tracks the newest release in that
            # major, so only a major bump is a lag. A full/partial pin
            # (v10.2.0, v0.0.11) is compared against the exact latest.
            mark = "LAG" if is_outdated(tag, latest, major_only=is_major_only(tag)) else "OK"
            print(f"{repo}@{tag:12s} latest: {latest:12s} {mark}")
        except Exception as e:  # noqa: BLE001
            failures.append(f"{repo}@{tag}")
            print(f"{repo}@{tag:12s} latest: WARN ({e})")

    if failures:
        print(f"\nFAILED: {', '.join(failures)}")
    print("\ncheck:outdated done (informational; not a gate)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
