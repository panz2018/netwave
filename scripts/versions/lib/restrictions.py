"""Version restriction records (see scripts/versions/README.md).

A record states why a specific combination of package versions is unusable.
Single-package bugs and multi-package pairings are the same shape: a combo
with one package and a combo with N packages.

Pure functions only — no network, no subprocess (judgement must stay unit
testable offline)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import tomllib

from .repository import SKIP_DIRS
from .version import is_stable_version, parse_version

REL_PATH = ("scripts", "versions", "restrictions.json")

ECOSYSTEMS = ("npm", "cargo", "pypi")


class RestrictionFormatError(Exception):
    """restrictions.json exists but breaks its contract."""


def load_restrictions(root: Path) -> list[dict[str, Any]]:
    """Return the recorded restrictions, or [] when no file exists yet.

    Raises RestrictionFormatError when the file is present but malformed."""
    path = Path(root).joinpath(*REL_PATH)
    if not path.is_file():
        return []
    return _parse(_read(path), path)


def is_restricted(combo: dict[str, str], restrictions: list[dict[str, Any]]) -> bool:
    """True when the current locked versions match a recorded combo exactly.

    ``combo`` maps prefixed package names to their currently locked versions.
    A recorded combo hits when every package it names appears in ``combo``
    with the same version; packages it does not name are ignored. Combos that
    were never tested together therefore stay allowed (design D2).
    """
    return any(
        _combo_hits(recorded, combo) for record in restrictions for recorded in record["combos"]
    )


def _combo_hits(recorded: dict[str, str], current: dict[str, str]) -> bool:
    return all(current.get(name) == version for name, version in recorded.items())


def pick_unrestricted(
    package: str,
    candidates: list[str],
    peers: dict[str, str],
    restrictions: list[dict[str, Any]],
) -> str | None:
    """Highest candidate version of ``package`` that forms no recorded combo.

    ``peers`` holds the currently locked versions of the other packages the
    candidate would be used with. Returns None when every candidate is
    restricted. Newest-first: an unrestricted latest candidate is returned
    unchanged (design D4)."""
    for version in sorted(candidates, key=parse_version, reverse=True):
        if not is_restricted({**peers, package: version}, restrictions):
            return version
    return None


def locked_versions(root: Path, names: list[str]) -> dict[str, str]:
    """Currently locked version of each prefixed package name (design D3).

    `npm:` from pnpm-lock.yaml, `cargo:` from Cargo.lock, `pypi:` from every
    uv.lock in the repo. Names that no lockfile mentions are omitted, so a
    record naming a package this repo does not lock simply never hits."""
    root = Path(root)
    found: dict[str, str] = {}
    for name in names:
        ecosystem, _, package = name.partition(":")
        versions = _locked_in(root, ecosystem, package)
        if versions:
            found[name] = max(versions, key=parse_version)
    return found


def _locked_in(root: Path, ecosystem: str, package: str) -> list[str]:
    if ecosystem == "npm":
        return _npm_locked(root, package)
    if ecosystem == "cargo":
        return _toml_locked(root / "Cargo.lock", package)
    if ecosystem == "pypi":
        return [v for lock in _uv_locks(root) for v in _toml_locked(lock, package)]
    return []


# pnpm lockfile v9 package keys: two-space indent, quoted when the name is
# scoped, optionally peer-suffixed (`tsdown@0.23.0(typescript@7.0.2)`, which
# must not match — the plain key carries the version a fresh resolve lands on).
_NPM_KEY = re.compile(r"^  '?(@?[^\s@'\"]+)@([0-9][0-9A-Za-z.\-+]*)'?:")


def _npm_locked(root: Path, package: str) -> list[str]:
    path = root / "pnpm-lock.yaml"
    if not path.is_file():
        return []
    return [
        m.group(2)
        for m in (_NPM_KEY.match(line) for line in path.read_text(encoding="utf-8").splitlines())
        if m and m.group(1) == package
    ]


def _toml_locked(path: Path, package: str) -> list[str]:
    if not path.is_file():
        return []
    doc = tomllib.loads(path.read_text(encoding="utf-8"))
    return [str(p["version"]) for p in doc.get("package", []) if p.get("name") == package]


def _uv_locks(root: Path) -> list[Path]:
    return [
        lock
        for lock in root.glob("**/uv.lock")
        if not any(part in SKIP_DIRS for part in lock.relative_to(root).parts)
    ]


def _read(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RestrictionFormatError(f"{path}: not valid JSON ({exc})") from exc


def _parse(doc: Any, path: Path) -> list[dict[str, Any]]:
    if not isinstance(doc, dict) or not isinstance(doc.get("restrictions"), list):
        raise RestrictionFormatError(f"{path}: expected an object with a 'restrictions' list")
    return [_check_record(record, path) for record in doc["restrictions"]]


def _check_record(record: Any, path: Path) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise RestrictionFormatError(f"{path}: each restriction must be an object")
    reason = record.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise RestrictionFormatError(f"{path}: each restriction needs a non-empty 'reason'")
    combos = record.get("combos")
    if not isinstance(combos, list) or not combos:
        raise RestrictionFormatError(f"{path}: each restriction needs a non-empty 'combos' list")
    return {"reason": reason, "combos": [_check_combo(combo, path) for combo in combos]}


def _check_combo(combo: Any, path: Path) -> dict[str, str]:
    if not isinstance(combo, dict) or not combo:
        raise RestrictionFormatError(f"{path}: each combo must be a non-empty package/version map")
    for name, version in combo.items():
        ecosystem, _, package = name.partition(":") if isinstance(name, str) else ("", "", "")
        if ecosystem not in ECOSYSTEMS or not package:
            raise RestrictionFormatError(f"{path}: package {name!r} needs an ecosystem prefix")
        if not isinstance(version, str) or not is_stable_version(version):
            raise RestrictionFormatError(f"{path}: {name!r} version {version!r} must be exact")
    return dict(combo)
