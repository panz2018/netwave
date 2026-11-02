#!/usr/bin/env python3
"""Version consistency rule gate — four structural laws, no registry.

Every version pin lives in the file that carries it (rust-toolchain.toml,
.python-version, pyproject.toml, package.json, .github/workflows/ci.yml).
This gate scans repo manifests against general laws and reads no manifest
list: a new subproject is covered automatically, and any violation fails on
the spot naming the offending file.

Laws:
  1. MSRV: every workspace member (root Cargo.toml `members`) carries
     `rust-version`, all values are equal, and none is above the
     rust-toolchain.toml channel (major.minor); the channel must be exact.
  2. Python project: every pyproject.toml declaring `[project]` declares
     `requires-python` and has a sibling `.python-version`.
  3. packageManager: every package.json carrying `packageManager` is an
     exact pnpm version, and all such values are equal across the repo.
  4. Matrix coverage: every .python-version pin appears among the python
     matrix cells of the CI workflows.

Whether a pin is the latest version is the job of
scripts/versions/check_outdated.py (manual, networked).

Usage: python3 scripts/versions/check_versions.py
"""

import json
import re
import sys
from collections.abc import Callable
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parent.parent.parent
SKIP_DIRS = ("target", "target-wasm", "node_modules", ".venv", ".git", "dist", "coverage")


def parse_ver(s: str) -> tuple[int, ...]:
    return tuple(int(x) for x in re.match(r"(\d+)\.(\d+)(?:\.(\d+))?", s).groups() if x)


def discover(fname: str, cond: Callable[[str], bool] = lambda t: True) -> set[str]:
    """Repo-relative paths of files named `fname` whose content matches cond."""
    found: set[str] = set()
    for f in ROOT.rglob(fname):
        if any(part in SKIP_DIRS for part in f.parts):
            continue
        if cond(f.read_text(encoding="utf-8")):
            found.add(str(f.relative_to(ROOT)))
    return found


def has_project(text: str) -> bool:
    """True if the TOML declares a [project] table (parsed, not substring, so
    comments mentioning it do not count as a Python project)."""
    try:
        doc = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return False
    return "project" in doc


def workspace_members() -> list[str]:
    """Repo-relative Cargo.toml paths of the members listed in the root
    Cargo.toml `members` — the authoritative list of subprojects."""
    doc = tomllib.loads((ROOT / "Cargo.toml").read_text(encoding="utf-8"))
    return [f"{m}/Cargo.toml" for m in doc.get("workspace", {}).get("members", [])]


def main() -> int:
    errors = []

    # Law 1 (MSRV): every workspace member must pin rust-version (missing =
    # FAIL, so deleting the field cannot silently escape); all values equal,
    # and none above the rust-toolchain pin.
    members = workspace_members()
    msrvs: dict[str, str] = {}
    for rel in members:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"{rel}: workspace member has no Cargo.toml")
            continue
        doc = tomllib.loads(path.read_text(encoding="utf-8"))
        rv = doc.get("package", {}).get("rust-version")
        if rv is None:
            errors.append(f"{rel}: workspace member missing rust-version pin")
        else:
            msrvs[rel] = rv
    if len(set(msrvs.values())) > 1:
        errors.append(f"rust-version drift: {msrvs}")
    pin_doc = tomllib.loads((ROOT / "rust-toolchain.toml").read_text(encoding="utf-8"))
    pin_ch = pin_doc["toolchain"]["channel"]
    if not re.fullmatch(r"\d+\.\d+(\.\d+)?", pin_ch):
        errors.append(f"rust-toolchain.toml: channel {pin_ch!r} is not an exact pin")
    else:
        for rel, v in msrvs.items():
            if parse_ver(v) > parse_ver(pin_ch):
                errors.append(f"{rel}: rust-version {v} above rust-toolchain pin {pin_ch}")

    # Law 2 (Python project): every pyproject.toml declaring [project] must
    # declare requires-python and have a sibling .python-version pin.
    for rel in sorted(discover("pyproject.toml", has_project)):
        doc = tomllib.loads((ROOT / rel).read_text(encoding="utf-8"))
        if "requires-python" not in doc.get("project", {}):
            errors.append(f"{rel}: [project] missing requires-python declaration")
        if not (ROOT / rel).parent.joinpath(".python-version").exists():
            errors.append(f"{rel}: no sibling .python-version pin")

    # Law 3 (packageManager): exact and equal across the repo.
    pms: dict[str, str] = {}
    for rel in sorted(discover("package.json", lambda t: '"packageManager"' in t)):
        pm = json.loads((ROOT / rel).read_text(encoding="utf-8")).get("packageManager", "")
        if not re.fullmatch(r"pnpm@\d+\.\d+\.\d+", pm):
            errors.append(f"{rel}: packageManager {pm!r} is not an exact pnpm version")
        pms[rel] = pm
    if len(set(pms.values())) > 1:
        errors.append(f"packageManager drift: {pms}")

    # Law 4 (matrix coverage): every .python-version pin appears among the
    # python matrix cells of the CI workflows.
    cells = set()
    for wf in sorted(discover("*.yml", lambda t: "python-version:" in t)):
        text = (ROOT / wf).read_text(encoding="utf-8")
        cells.update(re.findall(r'python-version:\s*"?(\d+\.\d+)"?', text))
    for rel in sorted(discover(".python-version")):
        pyver = (ROOT / rel).read_text(encoding="utf-8").strip()
        if cells and pyver not in cells:
            errors.append(f"{rel} {pyver} not among ci python matrix cells {sorted(cells)}")

    if errors:
        for err in errors:
            print(f"::error::{err}", file=sys.stderr)
        return 1
    print(
        f"version laws OK: {len(msrvs)} workspace members consistent "
        f"(rust-version {next(iter(msrvs.values()))}, pin {pin_ch})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
