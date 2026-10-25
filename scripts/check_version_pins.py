#!/usr/bin/env python3
"""Version-pin registry reconciliation gate.

Single source of truth: scripts/version_pins.json (spec: dependency-upgrade).
Two-way check: every registry entry points at a real pin location, and every
mechanically discoverable pin location in the repo appears in the registry.
Consistency rules (drift like a manual rust-toolchain bump leaving stale
rust-version fields behind) fail the gate on the spot.

Checks (all discovery-based — no hardcoded file lists; new subprojects are
covered automatically):
  1. Entry structure: name / category (known enum) / pin_location /
     upgrade_method / paired_with.
  2. pin_location existence (repo paths; `machine:` entries are checked for
     presence in the registry only).
  3. Every Cargo.toml carrying `rust-version`: all values equal and not above
     the rust-toolchain.toml pin (major.minor); channel must be an exact pin.
  4. Every package.json carrying `packageManager` is an exact pnpm version,
     and all such values are equal across the repo.
  5. ci-actions: every `uses:` line in .github/workflows/*.yml appears in
     the registry watch list, and vice versa.
  6. Every .python-version pin appears among the python matrix cells of the
     CI workflows.
  7. Discovery: every mechanically discoverable pin location in the repo
     (Cargo.toml rust-version, package.json packageManager, pyproject.toml
     requires-python, uv.lock, .python-version) appears in the registry — a
     new subproject that forgets to register fails here.

This gate checks registration and consistency only. Whether a pin is the
latest version is the job of scripts/check_outdated.py (manual, networked).

Usage: python3 scripts/check_version_pins.py
"""

import json
import re
import sys
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "scripts" / "version_pins.json"
SKIP_DIRS = ("target", "target-wasm", "node_modules", ".venv", ".git", "dist", "coverage")

REQUIRED_FIELDS = ("name", "category", "pin_location", "upgrade_method", "paired_with")


def locations(entry):
    loc = entry["pin_location"]
    return loc if isinstance(loc, list) else [loc]


def parse_ver(s):
    return tuple(int(x) for x in re.match(r"(\d+)\.(\d+)(?:\.(\d+))?", s).groups() if x)


def discover(fname, cond=lambda t: True):
    """Repo-relative paths of files named `fname` whose content matches cond."""
    found = set()
    for f in ROOT.rglob(fname):
        if any(part in SKIP_DIRS for part in f.parts):
            continue
        if cond(f.read_text(encoding="utf-8")):
            found.add(str(f.relative_to(ROOT)))
    return found


def has_rust_version(text):
    """True if the TOML declares [package] rust-version (parsed, not substring,
    so comments mentioning it do not count as pin locations)."""
    try:
        doc = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return False
    return "rust-version" in doc.get("package", {})


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
        names.add(e["name"])
    for e in pins:
        for p in e.get("paired_with", []):
            if p not in names:
                errors.append(f"{e['name']}: paired_with references unknown entry {p!r}")

    # 2. pin_location existence
    for e in pins:
        for loc in locations(e):
            if loc.startswith("machine:"):
                continue
            if not (ROOT / loc).exists():
                errors.append(f"{e['name']}: pin_location {loc!r} does not exist")

    # 3. rust-version consistency (discovered, not registry-listed)
    msrvs = {}
    for rel in sorted(discover("Cargo.toml", has_rust_version)):
        doc = tomllib.loads((ROOT / rel).read_text(encoding="utf-8"))
        msrvs[rel] = doc["package"]["rust-version"]
    if len(set(msrvs.values())) > 1:
        errors.append(f"rust-version drift: {msrvs}")
    msrv_registered = {loc for e in pins if e["category"] == "msrv" for loc in locations(e)}
    for rel in sorted(msrv_registered - set(msrvs)):
        errors.append(f"{rel}: registered as msrv but rust-version missing")
    pin_doc = tomllib.loads((ROOT / "rust-toolchain.toml").read_text(encoding="utf-8"))
    pin_ch = pin_doc["toolchain"]["channel"]
    if not re.fullmatch(r"\d+\.\d+(\.\d+)?", pin_ch):
        errors.append(f"rust-toolchain.toml: channel {pin_ch!r} is not an exact pin")
    else:
        for rel, v in msrvs.items():
            if parse_ver(v) > parse_ver(pin_ch):
                errors.append(f"{rel}: rust-version {v} above rust-toolchain pin {pin_ch}")

    # 4. packageManager exact and equal across the repo
    pms = {}
    for rel in sorted(discover("package.json", lambda t: '"packageManager"' in t)):
        pm = json.loads((ROOT / rel).read_text(encoding="utf-8")).get("packageManager", "")
        if not re.fullmatch(r"pnpm@\d+\.\d+\.\d+", pm):
            errors.append(f"{rel}: packageManager {pm!r} is not an exact pnpm version")
        pms[rel] = pm
    if len(set(pms.values())) > 1:
        errors.append(f"packageManager drift: {pms}")

    # 5. ci-actions two-way
    actions_in_yml = set()
    for wf in (ROOT / ".github" / "workflows").glob("*.yml"):
        for line in wf.read_text(encoding="utf-8").splitlines():
            m = re.search(r"uses:\s*([\w./-]+@[\w.\-]+)", line)
            if m and not m.group(1).startswith("docker://"):
                actions_in_yml.add(m.group(1))
    action_entries = [e for e in pins if e["category"] == "ci-actions"]
    watched = set()
    for e in action_entries:
        watched.update(e.get("watch", []))
    for a in sorted(actions_in_yml - watched):
        errors.append(f"ci action {a!r} used in workflows but not registered")
    for a in sorted(watched - actions_in_yml):
        errors.append(f"registry watch {a!r} not used in any workflow")

    # 6. every .python-version pin appears among ci python matrix cells
    cells = set()
    for wf in sorted(discover("*.yml", lambda t: "python-version:" in t)):
        text = (ROOT / wf).read_text(encoding="utf-8")
        cells.update(re.findall(r'python-version:\s*"?(\d+\.\d+)"?', text))
    for rel in sorted(discover(".python-version")):
        pyver = (ROOT / rel).read_text(encoding="utf-8").strip()
        if cells and pyver not in cells:
            errors.append(f"{rel} {pyver} not among ci python matrix cells {sorted(cells)}")

    # 7. discovery: every mechanically discoverable pin location is registered
    registered = {loc for e in pins for loc in locations(e) if not loc.startswith("machine:")}
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
        f"version-pin registry OK: {len(pins)} entries, "
        f"{len(msrvs)} msrv files consistent (rust-version {next(iter(msrvs.values()))}, "
        f"pin {pin_ch}), {len(actions_in_yml)} ci actions registered"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
