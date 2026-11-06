"""Repo scanning and pin extraction — discovery by filename, no manifest
list, so new subprojects are covered automatically. Every function takes
the repo root explicitly; the facades pass ROOT. SKIP_DIRS lives here and
only here: build outputs and dependency caches never carry pins."""

import json
import re
from collections.abc import Callable
from pathlib import Path

import tomllib

ROOT = Path(__file__).resolve().parent.parent.parent.parent
SKIP_DIRS = ("target", "target-wasm", "node_modules", ".venv", ".git", "dist", "coverage")


def _skip(root: Path, path: Path) -> bool:
    rel_parts = path.relative_to(root).parts
    return any(part in SKIP_DIRS for part in rel_parts)


def find_files(root: Path, fname: str, cond: Callable[[str], bool] = lambda t: True) -> set[str]:
    """Repo-relative paths of files named `fname` under `root` whose content
    matches `cond`, skipping SKIP_DIRS."""
    found: set[str] = set()
    for f in root.rglob(fname):
        if _skip(root, f):
            continue
        if cond(f.read_text(encoding="utf-8")):
            found.add(str(f.relative_to(root)))
    return found


def find_python_versions(root: Path) -> dict[str, str]:
    """Repo-relative `.python-version` paths mapped to their pinned value."""
    return {
        rel: (root / rel).read_text(encoding="utf-8").strip()
        for rel in sorted(find_files(root, ".python-version"))
    }


def find_ci_workflows(root: Path) -> list[Path]:
    """Workflow yml files under .github/workflows (sorted)."""
    return sorted((root / ".github" / "workflows").glob("*.yml"))


def is_python_project(text: str) -> bool:
    """True if the TOML declares a [project] table (parsed, not substring, so
    comments mentioning it do not count as a Python project)."""
    try:
        doc = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return False
    return "project" in doc


def workspace_members(root: Path) -> list[str]:
    """Repo-relative Cargo.toml paths of the members listed in the root
    Cargo.toml `members` — the authoritative list of subprojects."""
    doc = tomllib.loads((root / "Cargo.toml").read_text(encoding="utf-8"))
    return [f"{m}/Cargo.toml" for m in doc.get("workspace", {}).get("members", [])]


def rust_versions(root: Path) -> dict[str, str]:
    """Repo-relative member Cargo.toml paths mapped to their `rust-version`
    pin. Members without the field are omitted (the law reports those)."""
    found: dict[str, str] = {}
    for rel in workspace_members(root):
        path = root / rel
        if not path.exists():
            continue
        rv = tomllib.loads(path.read_text(encoding="utf-8")).get("package", {}).get("rust-version")
        if rv is not None:
            found[rel] = str(rv)
    return found


def toolchain_channel(root: Path) -> str:
    """The `channel` value pinned in rust-toolchain.toml."""
    doc = tomllib.loads((root / "rust-toolchain.toml").read_text(encoding="utf-8"))
    return str(doc["toolchain"]["channel"])


def ci_python_cells(root: Path) -> set[str]:
    """Python version cells declared in any workflow yml in the repo
    (`python-version:` entries, repo-wide so a matrix written outside
    .github/workflows cannot escape coverage)."""
    cells: set[str] = set()
    pattern = re.compile(r'python-version:\s*"?(\d+\.\d+)"?')
    for rel in sorted(find_files(root, "*.yml", lambda t: "python-version:" in t)):
        cells.update(pattern.findall((root / rel).read_text(encoding="utf-8")))
    return cells


def find_package_managers(root: Path) -> dict[str, str]:
    """Repo-relative package.json paths carrying `packageManager`, mapped to
    their value."""
    found: dict[str, str] = {}
    for rel in sorted(find_files(root, "package.json", lambda t: '"packageManager"' in t)):
        found[rel] = json.loads((root / rel).read_text(encoding="utf-8")).get("packageManager", "")
    return found
