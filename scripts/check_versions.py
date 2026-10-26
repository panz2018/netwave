#!/usr/bin/env python3
"""Version registry reconciliation gate.

Single source of truth: scripts/versions.json. Two-way check: every
registry entry points at a real pin location, and every mechanically
discoverable pin location in the repo appears in the registry. Consistency
rules (drift like a manual rust-toolchain bump leaving stale rust-version
fields behind) fail the gate on the spot.

pin_location values come in three forms: a repo file path; `machine:<name>`
(a pin that lives on the developer machine, checked for registration only);
and `discovered:<rule>` (the location is provided by a discovery rule named
in DISCOVERED_RULES below, so the registry never hand-copies file lists).

Checks:
  1. Entry structure: name / category (known enum) / pin_location /
     upgrade_method / paired_with / blocked (optional known-bad list:
     exact version + reason, optional issue; ci-actions unsupported).
  2. pin_location existence: repo paths exist; `machine:` entries are
     registration-only; `discovered:` rule names are known.
  3. MSRV: every workspace member (root Cargo.toml `members`) carries
     `rust-version`, all values are equal, and none is above the
     rust-toolchain.toml pin (major.minor); the channel must be an exact pin.
  4. Every package.json carrying `packageManager` is an exact pnpm version,
     and all such values are equal across the repo.
  5. Every .python-version pin appears among the python matrix cells of the
     CI workflows.
  6. Discovery: every mechanically discoverable pin location in the repo
     (Cargo.toml rust-version, package.json packageManager, pyproject.toml
     requires-python, uv.lock, .python-version) appears in the registry —
     locations covered by a `discovered:` rule count as registered, and a
     new subproject that forgets to register fails here.

This gate checks registration and consistency only. Whether a pin is the
latest version is the job of scripts/check_outdated.py (manual, networked).

Usage: python3 scripts/check_versions.py
"""

import json
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import tomllib

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "scripts" / "versions.json"
SKIP_DIRS = ("target", "target-wasm", "node_modules", ".venv", ".git", "dist", "coverage")

REQUIRED_FIELDS = ("name", "category", "pin_location", "upgrade_method", "paired_with")

# blocked entries name exact versions only; ranges/wildcards/major-only rejected.
EXACT_VERSION = re.compile(r"\d+(\.\d+){1,2}(?:[-+][0-9A-Za-z.-]+)?")

# One registry entry from versions.json `pins` (heterogeneous JSON fields).
Pin = dict[str, Any]


def locations(entry: Pin) -> list[str]:
    loc = entry["pin_location"]
    return loc if isinstance(loc, list) else [loc]


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


def has_rust_version(text: str) -> bool:
    """True if the TOML declares [package] rust-version (parsed, not substring,
    so comments mentioning it do not count as pin locations)."""
    try:
        doc = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return False
    return "rust-version" in doc.get("package", {})


def workspace_members() -> list[str]:
    """Repo-relative Cargo.toml paths of the members listed in the root
    Cargo.toml `members` — the authoritative list of subprojects."""
    doc = tomllib.loads((ROOT / "Cargo.toml").read_text(encoding="utf-8"))
    return [f"{m}/Cargo.toml" for m in doc.get("workspace", {}).get("members", [])]


# `discovered:<rule>` in pin_location resolves through this table.
DISCOVERED_RULES: dict[str, Callable[[], list[str]]] = {"workspace-members": workspace_members}


def discovered_locations(pins: list[Pin]) -> set[str]:
    """Repo-relative pin locations covered by `discovered:` rules in the registry."""
    covered: set[str] = set()
    for e in pins:
        for loc in locations(e):
            if loc.startswith("discovered:"):
                covered.update(DISCOVERED_RULES[loc[len("discovered:") :]]())
    return covered


def current_values(e: Pin) -> list[tuple[str, str]]:
    """(source, value) pairs of the current pin values an entry pins, limited
    to what the offline gate can read from repo files (no machine probes):
    rust-toolchain channel, packageManager, .python-version, CI python matrix
    cells, discovered workspace-member MSRVs. Entries whose pinned value lives
    on the machine or in a lockfile yield nothing here."""
    out: list[tuple[str, str]] = []
    for loc in locations(e):
        if loc.startswith("machine:") or loc.startswith("discovered:"):
            continue
        path = ROOT / loc
        if not path.exists():
            continue
        field = e.get("field")
        if field == "packageManager":
            pm = json.loads(path.read_text(encoding="utf-8")).get("packageManager", "")
            if "@" in pm:
                out.append((loc, pm.split("@", 1)[1]))
        elif loc.endswith(".python-version"):
            out.append((loc, path.read_text(encoding="utf-8").strip()))
        elif loc.endswith("rust-toolchain.toml"):
            ch = tomllib.loads(path.read_text(encoding="utf-8")).get("toolchain", {}).get("channel")
            if ch:
                out.append((loc, ch))
        elif e["category"] == "lang-matrix" and loc.endswith(".yml"):
            text = path.read_text(encoding="utf-8")
            out.extend((loc, v) for v in re.findall(r'python-version:\s*"?(\d+(?:\.\d+)?)"?', text))
            out.extend((loc, v) for v in re.findall(r'node-version:\s*"?(\d+(?:\.\d+)?)"?', text))
            # full-pin action tags (v10.2.0, not major-only v7) are readable too
            for tag in re.findall(r"uses:\s*\S+@v(\d+\.\d+(?:\.\d+)?)\b", text):
                out.append((loc, tag))
    if any(loc.startswith("discovered:") for loc in locations(e)):
        for rel in workspace_members():
            p = ROOT / rel
            if p.exists():
                rv = (
                    tomllib.loads(p.read_text(encoding="utf-8"))
                    .get("package", {})
                    .get("rust-version")
                )
                if rv:
                    out.append((rel, rv))
    return list(dict.fromkeys(out))


def main() -> int:
    errors = []
    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    categories = set(reg["categories"])
    pins = reg["pins"]
    names = set()

    # 1. structure
    for e in pins:
        missing = [f for f in REQUIRED_FIELDS if f not in e]
        if missing:
            errors.append(f"{e.get('name', '?')}: missing field(s) {missing}")
            continue
        if e["category"] not in categories:
            errors.append(f"{e['name']}: unknown category {e['category']!r}")
        if not isinstance(e["paired_with"], list):
            errors.append(f"{e['name']}: paired_with must be a list")
        if "blocked" in e:
            if e["category"] == "ci-actions":
                errors.append(f"{e['name']}: category ci-actions does not support blocked")
            if not isinstance(e["blocked"], list):
                errors.append(f"{e['name']}: blocked must be a list")
            else:
                for b in e["blocked"]:
                    if not isinstance(b, dict):
                        errors.append(f"{e['name']}: blocked entry must be an object, got {b!r}")
                        continue
                    if not b.get("reason"):
                        errors.append(
                            f"{e['name']}: blocked entry {b.get('version')!r} missing reason"
                        )
                    if "issue" in b and not isinstance(b["issue"], str):
                        errors.append(
                            f"{e['name']}: blocked {b.get('version')!r}: issue must be a string"
                        )
                    v = b.get("version")
                    if not isinstance(v, str) or not EXACT_VERSION.fullmatch(v):
                        errors.append(
                            f"{e['name']}: blocked version {v!r} must be an exact version "
                            "(ranges/wildcards rejected)"
                        )
        names.add(e["name"])
    for e in pins:
        for p in e.get("paired_with", []):
            if p not in names:
                errors.append(f"{e['name']}: paired_with references unknown entry {p!r}")

    # 1b. blocked blacklist: a current pin value readable from repo files must
    # not sit on a known-bad version. `machine:` entries are skipped here (the
    # gate runs offline; check_outdated.py probes installed versions instead).
    for e in pins:
        blocked = e.get("blocked") or []
        if not blocked or e["category"] == "ci-actions":
            continue
        bad = {
            b["version"]: b.get("reason", "")
            for b in blocked
            if isinstance(b, dict) and b.get("version")
        }
        for src, val in current_values(e):
            if val in bad:
                errors.append(
                    f"{e['name']}: {src} pins {val}, a blocked version"
                    + (f" ({bad[val]})" if bad[val] else "")
                )

    # 2. pin_location existence: repo paths must exist; `machine:` entries are
    # registration-only; `discovered:` rule names must be known.
    for e in pins:
        for loc in locations(e):
            if loc.startswith("machine:"):
                continue
            if loc.startswith("discovered:"):
                if loc[len("discovered:") :] not in DISCOVERED_RULES:
                    errors.append(f"{e['name']}: unknown discovery rule {loc!r}")
                continue
            if not (ROOT / loc).exists():
                errors.append(f"{e['name']}: pin_location {loc!r} does not exist")

    # 3. MSRV: every workspace member must pin rust-version (missing = FAIL,
    # so deleting the field cannot silently escape); all values equal, and
    # none above the rust-toolchain pin.
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

    # 4. packageManager exact and equal across the repo
    pms: dict[str, str] = {}
    for rel in sorted(discover("package.json", lambda t: '"packageManager"' in t)):
        pm = json.loads((ROOT / rel).read_text(encoding="utf-8")).get("packageManager", "")
        if not re.fullmatch(r"pnpm@\d+\.\d+\.\d+", pm):
            errors.append(f"{rel}: packageManager {pm!r} is not an exact pnpm version")
        pms[rel] = pm
    if len(set(pms.values())) > 1:
        errors.append(f"packageManager drift: {pms}")

    # 5. every .python-version pin appears among ci python matrix cells
    cells = set()
    for wf in sorted(discover("*.yml", lambda t: "python-version:" in t)):
        text = (ROOT / wf).read_text(encoding="utf-8")
        cells.update(re.findall(r'python-version:\s*"?(\d+\.\d+)"?', text))
    for rel in sorted(discover(".python-version")):
        pyver = (ROOT / rel).read_text(encoding="utf-8").strip()
        if cells and pyver not in cells:
            errors.append(f"{rel} {pyver} not among ci python matrix cells {sorted(cells)}")

    # 6. discovery: every mechanically discoverable pin location is registered
    # (a `discovered:` rule counts its members as registered).
    registered = {loc for e in pins for loc in locations(e) if not loc.startswith("machine:")}
    registered |= discovered_locations(pins)
    pin_files = discover("Cargo.toml", has_rust_version)
    pin_files |= discover("package.json", lambda t: '"packageManager"' in t)
    pin_files |= discover("pyproject.toml", lambda t: "requires-python" in t)
    pin_files |= discover("uv.lock")
    pin_files |= discover(".python-version")
    for rel in sorted(pin_files - registered):
        errors.append(f"pin location {rel!r} exists in repo but is not registered")

    if errors:
        for err in errors:
            print(f"::error::{err}", file=sys.stderr)
        return 1
    print(
        f"version registry OK: {len(pins)} entries, "
        f"{len(msrvs)} workspace members consistent "
        f"(rust-version {next(iter(msrvs.values()))}, pin {pin_ch})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
