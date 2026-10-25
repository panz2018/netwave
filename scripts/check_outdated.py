#!/usr/bin/env python3
"""Freshness check (manual, networked — NOT a CI gate).

Four segments, per the dependency-upgrade spec:
  1. Project deps: pnpm -r outdated (all workspace packages) / cargo update
     --dry-run (whole workspace lock) / uv lock --upgrade --dry-run for every
     uv project found (any uv.lock, incl. oracle when it lands), plus every
     runtime pin (.python-version vs latest stable minor).
  2. Global CLIs: installed --version vs newest LTS/stable (endoflife.date,
     npm registry, GitHub releases; node refined to the newest patch on the
     LTS line via nodejs.org).
  3. GitHub-tarball tools & cargo subcommands: installed version vs the
     repo's latest release.
  4. CI actions: `uses:` tags in .github/workflows vs latest release tag.

A failing segment degrades to a warning and never aborts the rest.
Usage: python3 scripts/check_outdated.py   (pnpm check:outdated)
"""

import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _req(url):
    req = urllib.request.Request(url)
    tok = os.environ.get("GITHUB_TOKEN")
    if tok and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {tok}")
    req.add_header("User-Agent", "netwave-check-outdated")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def run(cmd):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300, cwd=ROOT)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as e:  # noqa: BLE001
        return 125, str(e)


def first_line(text):
    """First non-empty line of a `--version` output (version lives on line 1
    for rustup/markdownlint multi-line banners)."""
    for ln in text.splitlines():
        if ln.strip():
            return ln.strip()
    return "?"


def _semver(tag):
    """Parse a `vX.Y.Z`-style tag into an int tuple for comparison."""
    nums = re.findall(r"\d+", tag)
    return tuple(int(n) for n in nums[:3]) + (0,) * (3 - len(nums[:3]))


def seg(title):
    print(f"\n=== {title} ===")


def main() -> int:
    # 1. project dependencies
    seg("1. project dependencies")
    # every uv project in the repo (python/, oracle/golden/, ...) — discovery
    # by uv.lock, no hardcoded list (spec: freshness covers all environments)
    skip = ("target", "node_modules", ".venv", ".git")
    for lock in sorted(ROOT.glob("**/uv.lock")):
        if any(part in skip for part in lock.parts):
            continue
        proj = lock.parent.relative_to(ROOT)
        rc, out = run(f"uv lock --upgrade --dry-run --project {proj}")
        print(f"$ uv lock --upgrade --dry-run --project {proj}  (rc={rc})")
        print(out if out else "(no output)")

    for cmd in ("pnpm -r outdated", "cargo update --dry-run"):
        rc, out = run(cmd)
        print(f"$ {cmd}  (rc={rc})")
        print(out if out else "(no output)")

    # every runtime pin in the repo (.python-version): single-line runtime ->
    # latest stable minor (dependency-upgrade spec line rule)
    try:
        latest_py = _req("https://endoflife.date/api/python.json")[0]["cycle"]
        for pv in sorted(ROOT.glob("**/.python-version")):
            if any(part in skip for part in pv.parts):
                continue
            pyver = pv.read_text(encoding="utf-8").strip()
            mark = "LAG" if _semver(pyver) < _semver(latest_py) else "OK"
            print(
                f"python pin {str(pv.relative_to(ROOT)):18s} {pyver:8s} "
                f"latest stable minor: {latest_py} {mark}"
            )
    except Exception as e:  # noqa: BLE001
        print(f"python runtime pins: WARN ({e})")

    # 2. global CLIs: name -> (probe, latest-source)
    seg("2. global CLIs (installed vs newest LTS/stable)")
    cli_checks = [
        ("node", "node --version", ("endoflife", "nodejs", "lts")),
        ("npm", "npm --version", ("npm", "npm")),
        ("pnpm", "pnpm --version", ("npm", "pnpm")),
        ("uv", "uv --version", ("github", "astral-sh/uv")),
        ("rustup", "rustup --version", ("github-tags", "rust-lang/rustup")),
        ("rustc", "rustc --version", ("endoflife", "rust", "stable")),
        ("openspec", "openspec --version", ("npm", "@fission-ai/openspec")),
        ("markdownlint-cli2", "markdownlint-cli2 --version", ("npm", "markdownlint-cli2")),
    ]
    for name, probe, source in cli_checks:
        rc, installed = run(probe)
        installed = first_line(installed)
        try:
            if source[0] == "npm":
                latest = _req(f"https://registry.npmjs.org/{source[1]}")["dist-tags"]["latest"]
            elif source[0] == "github":
                latest = _req(f"https://api.github.com/repos/{source[1]}/releases/latest")[
                    "tag_name"
                ]
            elif source[0] == "github-tags":
                # rustup ships git tags, not GitHub Releases.
                tags = _req(f"https://api.github.com/repos/{source[1]}/tags")
                latest = tags[0]["name"] if tags else "?"
            elif source[0] == "endoflife":
                data = _req(f"https://endoflife.date/api/{source[1]}.json")
                if source[2] == "lts":
                    lts = [c for c in data if c.get("lts")]
                    latest = lts[0]["cycle"] if lts else "?"
                elif source[2] == "stable":
                    latest = data[0]["cycle"]
                else:
                    raise ValueError(f"unknown endoflife kind {source[2]!r}")
            else:
                raise ValueError(f"unknown latest-source kind {source[0]!r}")
            if name == "node":
                # endoflife gives the LTS line ("26"); nodejs.org gives the
                # exact newest patch on that line ("26.12.1").
                dist = _req("https://nodejs.org/dist/index.json")
                latest = next(
                    (
                        d["version"].lstrip("v")
                        for d in dist
                        if d["version"].startswith(f"v{latest}.")
                    ),
                    latest,
                )
            print(f"{name:18s} installed: {installed:28s} latest: {latest}")
        except Exception as e:  # noqa: BLE001
            print(f"{name:18s} installed: {installed:28s} latest: WARN ({e})")

    # 3. github-tarball tools & cargo subcommands
    seg("3. github-tarball tools & cargo subcommands")
    for name, probe, repo in (
        ("wasm-pack", "wasm-pack --version", "wasm-bindgen/wasm-pack"),
        ("binaryen (wasm-opt)", "wasm-opt --version", "WebAssembly/binaryen"),
        ("cargo-llvm-cov", "cargo llvm-cov --version", "taiki-e/cargo-llvm-cov"),
    ):
        rc, installed = run(probe)
        installed = first_line(installed)
        try:
            latest = _req(f"https://api.github.com/repos/{repo}/releases/latest")["tag_name"]
            print(f"{name:22s} installed: {installed:28s} latest: {latest}")
        except Exception as e:  # noqa: BLE001
            print(f"{name:22s} installed: {installed:28s} latest: WARN ({e})")

    # 4. CI actions
    seg("4. CI actions (uses: tag vs latest release)")
    uses = set()
    for wf in (ROOT / ".github" / "workflows").glob("*.yml"):
        for line in wf.read_text(encoding="utf-8").splitlines():
            m = re.search(r"uses:\s*([\w./-]+)@([\w.\-]+)", line)
            if m and not m.group(1).startswith("docker://"):
                uses.add((m.group(1), m.group(2)))
    for repo, tag in sorted(uses):
        if "/" not in repo or repo.count("/") > 1:
            print(f"{repo}@{tag}  (skip: not a github action path)")
            continue
        # A non-version ref (stable/main/...) is a moving branch, not a pinned
        # release — dtolnay/rust-toolchain@stable is the documented usage, so
        # it is never a "lag". Only semver tags are compared.
        if not re.match(r"v?\d+(\.\d+)*$", tag):
            print(f"{repo}@{tag:12s} latest: {'(ref)':12s} REF")
            continue
        try:
            latest = _req(f"https://api.github.com/repos/{repo}/releases/latest")["tag_name"]
            # A major-only tag (v7, v6) auto-tracks the newest release in that
            # major, so only a major bump is a lag. A full/partial pin
            # (v10.2.0, v0.0.11) is compared against the exact latest.
            major_only = len(re.findall(r"\d+", tag)) == 1
            if major_only:
                mark = "LAG" if _semver(tag)[0] < _semver(latest)[0] else "OK"
            else:
                mark = "LAG" if _semver(tag) < _semver(latest) else "OK"
            print(f"{repo}@{tag:12s} latest: {latest:12s} {mark}")
        except Exception as e:  # noqa: BLE001
            print(f"{repo}@{tag:12s} latest: WARN ({e})")

    print("\ncheck:outdated done (informational; not a gate)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
