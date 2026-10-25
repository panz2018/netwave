#!/usr/bin/env python3
"""Version-pin registry reconciliation gate.

Single source of truth: scripts/version_pins.json (spec: dependency-upgrade).
Two-way check: every registry entry points at a real pin location, and every
mechanically discoverable pin location in the repo appears in the registry.
Consistency rules (drift like a manual rust-toolchain bump leaving stale
rust-version fields behind) fail the gate on the spot.

Checks:
  1. Entry structure: name / category (known enum) / pin_location /
     upgrade_method / paired_with.
  2. pin_location existence (repo paths; `machine:` entries are checked for
     presence in the registry only).
  3. All `rust-version` fields across Cargo.toml members are equal and not
     above the rust-toolchain.toml pin (major.minor).
  4. Root package.json `packageManager` is an exact pnpm version.
  5. ci-actions: every `uses:` line in .github/workflows/*.yml appears in
     the registry watch list, and vice versa.
  6. python matrix latest cell in ci.yml equals python/.python-version.
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

REQUIRED_FIELDS = ("name", "category", "pin_location", "upgrade_method", "paired_with")


def locations(entry):
    loc = entry["pin_location"]
    return loc if isinstance(loc, list) else [loc]


def parse_ver(s):
    return tuple(int(x) for x in re.match(r"(\d+)\.(\d+)(?:\.(\d+))?", s).groups() if x)


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

    # 3. rust-version consistency
    msrv_entries = [e for e in pins if e["category"] == "msrv"]
    msrv_files = [loc for e in msrv_entries for loc in locations(e)]
    msrvs = {}
    for rel in msrv_files:
        doc = tomllib.loads((ROOT / rel).read_text(encoding="utf-8"))
        v = doc.get("package", {}).get("rust-version")
        if v is None:
            errors.append(f"{rel}: rust-version missing but registered as msrv")
        else:
            msrvs[rel] = v
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

    # 4. packageManager exact
    pkg = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    pm = pkg.get("packageManager", "")
    if not re.fullmatch(r"pnpm@\d+\.\d+\.\d+", pm):
        errors.append(f"package.json: packageManager {pm!r} is not an exact pnpm version")

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

    # 6. python matrix latest == .python-version
    pyver = (ROOT / "python" / ".python-version").read_text(encoding="utf-8").strip()
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    cells = set(re.findall(r'python-version:\s*"?(\d+\.\d+)"?', ci))
    if cells and pyver not in cells:
        errors.append(
            f"python/.python-version {pyver} not among ci python matrix cells {sorted(cells)}"
        )

    # 7. discovery: every mechanically discoverable pin location is registered
    skip = ("target", "target-wasm", "node_modules", ".venv", ".git", "dist", "coverage")
    registered = {loc for e in pins for loc in locations(e) if not loc.startswith("machine:")}

    def discover(fname, cond):
        """Repo-relative paths of files named `fname` whose content matches cond."""
        found = set()
        for f in ROOT.rglob(fname):
            if any(part in skip for part in f.parts):
                continue
            rel = str(f.relative_to(ROOT))
            if cond(f.read_text(encoding="utf-8")):
                found.add(rel)
        return found

    pin_files = discover("Cargo.toml", lambda t: "rust-version" in t)
    pin_files |= discover("package.json", lambda t: '"packageManager"' in t)
    pin_files |= discover("pyproject.toml", lambda t: "requires-python" in t)
    pin_files |= discover("uv.lock", lambda t: True)
    pin_files |= discover(".python-version", lambda t: True)
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
