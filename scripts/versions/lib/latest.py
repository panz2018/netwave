"""Networked probes for the freshness check: fetch JSON from registries,
run local `--version` commands, and resolve the newest LTS/stable version
for a probe source. Only check_outdated.py consumes this module; the
offline gate must never import it."""

import json
import os
import re
import subprocess
import urllib.request
from typing import Any

from lib.repository import ROOT, SKIP_DIRS


def fetch_json(url: str) -> Any:
    req = urllib.request.Request(url)
    tok = os.environ.get("GITHUB_TOKEN")
    if tok and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {tok}")
    req.add_header("User-Agent", "netwave-check-outdated")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def run_cmd(cmd: str) -> tuple[int, str]:
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


def latest_version(source: tuple[str, ...]) -> str:
    """Resolve the newest version for a probe source tuple:
    ("npm", pkg) | ("github", repo) | ("github-tags", repo) |
    ("endoflife", product, "lts"|"stable")."""
    if source[0] == "npm":
        return fetch_json(f"https://registry.npmjs.org/{source[1]}")["dist-tags"]["latest"]
    if source[0] == "github":
        return fetch_json(f"https://api.github.com/repos/{source[1]}/releases/latest")["tag_name"]
    if source[0] == "github-tags":
        # rustup ships git tags, not GitHub Releases.
        tags = fetch_json(f"https://api.github.com/repos/{source[1]}/tags")
        return tags[0]["name"] if tags else "?"
    if source[0] == "endoflife":
        data = fetch_json(f"https://endoflife.date/api/{source[1]}.json")
        if source[2] == "lts":
            lts = [c for c in data if c.get("lts")]
            return lts[0]["cycle"] if lts else "?"
        if source[2] == "stable":
            return data[0]["cycle"]
        raise ValueError(f"unknown endoflife kind {source[2]!r}")
    raise ValueError(f"unknown latest-source kind {source[0]!r}")


def refine_node_lts(lts_line: str) -> str:
    """endoflife gives the LTS line ("26"); nodejs.org gives the exact
    newest patch on that line ("26.12.1")."""
    dist = fetch_json("https://nodejs.org/dist/index.json")
    return next(
        (d["version"].lstrip("v") for d in dist if d["version"].startswith(f"v{lts_line}.")),
        lts_line,
    )


def find_uv_projects() -> list[str]:
    """Repo-relative dirs of every uv project found by uv.lock (discovery,
    no hardcoded list — new environments are covered automatically).
    Sorted by lockfile path so `python/uv.lock` precedes `uv.lock`."""
    locks = [
        lock
        for lock in ROOT.glob("**/uv.lock")
        if not any(part in SKIP_DIRS for part in lock.parts)
    ]
    return [str(lock.parent.relative_to(ROOT)) for lock in sorted(locks)]


def action_refs() -> set[tuple[str, str]]:
    """(repo, ref) pairs from `uses:` lines in CI workflows, excluding
    docker:// refs."""
    refs: set[tuple[str, str]] = set()
    for wf in (ROOT / ".github" / "workflows").glob("*.yml"):
        for line in wf.read_text(encoding="utf-8").splitlines():
            m = re.search(r"uses:\s*([\w./-]+)@([\w.\-]+)", line)
            if m and not m.group(1).startswith("docker://"):
                refs.add((m.group(1), m.group(2)))
    return refs


def is_version_tag(tag: str) -> bool:
    """True for a version tag (v1, v1.2, v1.2.3); anything else (stable,
    main) is a moving branch ref, not a pinned release."""
    return bool(re.match(r"v?\d+(\.\d+)*$", tag))
