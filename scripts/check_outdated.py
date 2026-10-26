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
The registry's `blocked` lists (scripts/versions.json) are applied to the
enumerable segments (global CLIs, tarball tools, cargo subcommands, CI
action tags, python runtime pins): a blocked latest falls back to the next
available version, or reports "no known good target". Lockfile segments
(pnpm / cargo / uv dry-run) are left untouched — ecosystem mechanisms
(overrides, advisories, exclusions) handle versions inside lockfiles.
Usage: python3 scripts/check_outdated.py   (pnpm check:outdated)
"""

import json
import os
import re
import subprocess
import sys
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "scripts" / "versions.json"

# One registry entry from versions.json `pins` (heterogeneous JSON fields).
Pin = dict[str, Any]
# entry name -> (version -> reason, machine-pinned flag), read from `blocked`.
BlockedMap = dict[str, tuple[dict[str, str], bool]]


def locations(entry: Pin) -> list[str]:
    loc = entry["pin_location"]
    return loc if isinstance(loc, list) else [loc]


# probe name (what this script measures) -> registry entry whose `blocked`
# list applies. Repo-file pins (packageManager, .python-version cells) are
# consumed by the offline gate instead; `rustc` has no registry entry.
PROBE_TO_ENTRY: dict[str, str] = {
    "node": "node-global",
    "npm": "npm-global",
    "pnpm": "pnpm",
    "uv": "uv-global",
    "rustup": "rustup-global",
    "openspec": "openspec-global",
    "markdownlint-cli2": "markdownlint-cli2-global",
    "wasm-pack": "wasm-pack",
    "binaryen (wasm-opt)": "binaryen",
    "cargo-llvm-cov": "cargo-llvm-cov",
}


def load_blocked() -> BlockedMap:
    """entry name -> ({version: reason}, machine-pinned) from `blocked` fields."""
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    out: BlockedMap = {}
    for e in reg["pins"]:
        bad: dict[str, str] = {}
        for b in e.get("blocked", []):
            if isinstance(b, dict) and b.get("version"):
                bad[str(b["version"]).lstrip("v")] = b.get("reason", "")
        if bad:
            machine = any(str(loc).startswith("machine:") for loc in locations(e))
            out[e["name"]] = (bad, machine)
    return out


def _req(url: str) -> Any:
    req = urllib.request.Request(url)
    tok = os.environ.get("GITHUB_TOKEN")
    if tok and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {tok}")
    req.add_header("User-Agent", "netwave-check-outdated")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def run(cmd: str) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300, cwd=ROOT)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as e:  # noqa: BLE001
        return 125, str(e)


def first_line(text: str) -> str:
    """First non-empty line of a `--version` output (version lives on line 1
    for rustup/markdownlint multi-line banners)."""
    for ln in text.splitlines():
        if ln.strip():
            return ln.strip()
    return "?"


def _semver(tag: str) -> tuple[int, ...]:
    """Parse a `vX.Y.Z`-style tag into an int tuple for comparison."""
    nums = re.findall(r"\d+", tag)
    return tuple(int(n) for n in nums[:3]) + (0,) * (3 - len(nums[:3]))


def pick_target(cands: list[str], bad: dict[str, str]) -> str | None:
    """Newest candidate (already semver-sorted desc) not in the blocked set."""
    for v in cands:
        if v not in bad:
            return v
    return None


def npm_versions(pkg: str) -> list[str]:
    vs = [v for v in _req(f"https://registry.npmjs.org/{pkg}")["versions"] if "-" not in v]
    return sorted(vs, key=_semver, reverse=True)


def gh_tags(repo: str) -> list[str]:
    tags = _req(f"https://api.github.com/repos/{repo}/tags")
    vs = [t["name"].lstrip("v") for t in tags if re.fullmatch(r"v?\d+(\.\d+)*", t["name"])]
    return sorted(vs, key=_semver, reverse=True)


def blocked_target(
    blocked: BlockedMap, entry: str, latest: str, cands_fn: Callable[[], list[str]]
) -> tuple[str, str]:
    """If `latest` is blocked for `entry`, return (next-good-or-latest, note);
    otherwise (latest, ''). When every candidate is blocked the original
    `latest` is kept so the lag comparison still runs — the note says
    'no known good target'. `cands_fn()` lists all available versions, semver
    desc, and is only called when the latest is actually blocked."""
    bad = blocked.get(entry, (None,))[0]
    if not bad or latest.lstrip("v") not in bad:
        return latest, ""
    t = pick_target(cands_fn(), bad)
    note = f"  [latest {latest} blocked: {bad[latest.lstrip('v')]}]"
    if t:
        note += f" -> target {t}"
        return t, note
    note += " -> no known good target"
    return latest, note


def seg(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> int:
    blocked = load_blocked()
    consumed = set(PROBE_TO_ENTRY.values()) | {"python-runtime"}
    for entry, (bad, machine) in sorted(blocked.items()):
        if machine and entry not in consumed:
            print(
                f"warning: blocked entry {entry!r} is machine-pinned but maps to no "
                f"probe here ({len(bad)} version(s) unconsumed) — check PROBE_TO_ENTRY"
            )

    # 1. project dependencies
    seg("1. project dependencies")
    # every uv project in the repo (python/, oracle/golden/, ...) — discovery
    # by uv.lock, no hardcoded list, so new environments are covered automatically
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
    # latest stable minor (dependency-upgrade spec line rule); blocked latest
    # falls back to the next available cycle
    try:
        py_data = _req("https://endoflife.date/api/python.json")
        latest_py = str(py_data[0]["cycle"])
        latest_py, note = blocked_target(
            blocked,
            "python-runtime",
            latest_py,
            lambda: sorted((str(c["cycle"]) for c in py_data), key=_semver, reverse=True),
        )
        for pv in sorted(ROOT.glob("**/.python-version")):
            if any(part in skip for part in pv.parts):
                continue
            pyver = pv.read_text(encoding="utf-8").strip()
            mark = "LAG" if _semver(pyver) < _semver(latest_py) else "OK"
            print(
                f"python pin {str(pv.relative_to(ROOT)):18s} {pyver:8s} "
                f"latest stable minor: {latest_py} {mark}{note}"
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
                cands_fn = lambda d=dist: sorted(  # noqa: E731
                    (d2["version"].lstrip("v") for d2 in d), key=_semver, reverse=True
                )
            elif source[0] == "npm":
                cands_fn = lambda src=source: npm_versions(src[1])  # noqa: E731
            elif source[0] in ("github", "github-tags"):
                cands_fn = lambda src=source: gh_tags(src[1])  # noqa: E731
            elif source[0] == "endoflife":  # cycles list; LTS filter for lts lines
                cands_fn = lambda src=source: sorted(  # noqa: E731
                    (
                        str(c["cycle"])
                        for c in _req(f"https://endoflife.date/api/{src[1]}.json")
                        if src[2] != "lts" or c.get("lts")
                    ),
                    key=_semver,
                    reverse=True,
                )
            else:
                raise ValueError(f"unknown latest-source kind {source[0]!r}")
            entry = PROBE_TO_ENTRY.get(name, name)
            latest, note = blocked_target(blocked, entry, latest, cands_fn)
            print(f"{name:18s} installed: {installed:28s} latest: {latest}{note}")
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
            latest, note = blocked_target(
                blocked, PROBE_TO_ENTRY.get(name, name), latest, lambda r=repo: gh_tags(r)
            )
            print(f"{name:22s} installed: {installed:28s} latest: {latest}{note}")
        except Exception as e:  # noqa: BLE001
            print(f"{name:22s} installed: {installed:28s} latest: WARN ({e})")

    # 4. CI actions
    seg("4. CI actions (uses: tag vs latest release)")
    uses: set[tuple[str, str]] = set()
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
            # blocked lookup keyed by action repo path; the registry has no
            # action-level entries yet (ci-actions does not support blocked),
            # so this is inert until such entries are designed.
            latest, note = blocked_target(blocked, repo, latest, lambda r=repo: gh_tags(r))
            # A major-only tag (v7, v6) auto-tracks the newest release in that
            # major, so only a major bump is a lag. A full/partial pin
            # (v10.2.0, v0.0.11) is compared against the exact latest.
            major_only = len(re.findall(r"\d+", tag)) == 1
            if major_only:
                mark = "LAG" if _semver(tag)[0] < _semver(latest)[0] else "OK"
            else:
                mark = "LAG" if _semver(tag) < _semver(latest) else "OK"
            print(f"{repo}@{tag:12s} latest: {latest:12s} {mark}{note}")
        except Exception as e:  # noqa: BLE001
            print(f"{repo}@{tag:12s} latest: WARN ({e})")

    print("\ncheck:outdated done (informational; not a gate)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
