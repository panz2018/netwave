"""Repo scanning and pin extraction — discovery by filename, no manifest
list, so new subprojects are covered automatically. Every function takes
the repo root explicitly; the facades pass ROOT. SKIP_DIRS lives here and
only here: build outputs and dependency caches never carry pins."""

import json
import re
from collections.abc import Callable
from pathlib import Path

# tomllib is imported inside the functions that parse TOML, not at module top:
# `python/conftest.py` imports this module only for SKIP_DIRS and runs on the
# declared floor interpreter (3.10), where tomllib is not yet stdlib.

ROOT = Path(__file__).resolve().parent.parent.parent.parent
# target-wasm-cov: the instrumented wasm coverage build's cargo target dir (the
# rust coverage chain writes its profraw under it); whitelisted so the stray
# drain never deletes a legitimate report input.
SKIP_DIRS = (
    "target",
    "target-wasm",
    "target-wasm-cov",
    "node_modules",
    ".venv",
    ".git",
    "dist",
    "coverage",
)


def _skip(root: Path, path: Path) -> bool:
    rel_parts = path.relative_to(root).parts
    return any(part in SKIP_DIRS for part in rel_parts)


def drain_stray_profraw(root: Path) -> list[Path]:
    """Delete `*.profraw` under `root` outside build outputs and dependency
    caches (SKIP_DIRS), returning the sorted repo-relative paths removed.

    LLVM writes source-based coverage to `LLVM_PROFILE_FILE`; when that variable
    is unset at process exit it falls back to `default_%m_%p.profraw` in the
    process cwd. A profraw outside `target/` is therefore proof the coverage
    chain did not take effect, and such files are never report inputs — `cargo
    llvm-cov report` only reads what is registered under `target/`, so deleting
    them loses nothing."""
    removed: list[Path] = []
    for path in root.rglob("*.profraw"):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        path.unlink()
        removed.append(rel)
    return sorted(removed)


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
    import tomllib

    try:
        doc = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return False
    return "project" in doc


def workspace_members(root: Path) -> list[str]:
    """Repo-relative Cargo.toml paths of the members listed in the root
    Cargo.toml `members` — the authoritative list of subprojects."""
    import tomllib

    doc = tomllib.loads((root / "Cargo.toml").read_text(encoding="utf-8"))
    return [f"{m}/Cargo.toml" for m in doc.get("workspace", {}).get("members", [])]


def rust_versions(root: Path) -> dict[str, str]:
    """Repo-relative member Cargo.toml paths mapped to their `rust-version`
    pin. Members without the field are omitted (the law reports those)."""
    import tomllib

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
    import tomllib

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


def runtime_pins(root: Path) -> dict[str, str]:
    """Runtime and tool pins as combo peers keyed by ecosystem-prefixed
    names (`pypi:python`, `cargo:rustc`, `github:<repo>`) — merged with
    `locked_versions` so records naming runtimes can hit
    (「版本限制记录数据文件」(specs/dependency-upgrade/spec.md)). Python pins
    normalise to the minor line (the
    granularity the freshness report compares at); rustc and action pins
    keep their pinned value verbatim."""
    pins: dict[str, str] = {}
    for value in find_python_versions(root).values():
        parts = value.split(".")
        pins["pypi:python"] = ".".join(parts[:2]) if len(parts) >= 2 else value
    if (root / "rust-toolchain.toml").exists():
        pins["cargo:rustc"] = toolchain_channel(root)
    pm = find_package_managers(root).get("package.json", "")
    # corepack pins pnpm here (`pnpm@12.18.0` or `pnpm@12.18.0+sha512...`);
    # the repo field — not the machine's global — is pnpm's real version
    if pm.startswith("pnpm@"):
        pins["npm:pnpm"] = pm.partition("@")[2].partition("+")[0]
    uses = re.compile(r"uses:\s*([\w./-]+)@([\w.\-]+)")
    for wf in find_ci_workflows(root):
        for line in wf.read_text(encoding="utf-8").splitlines():
            m = uses.search(line)
            if m and "/" in m.group(1) and not m.group(1).startswith("docker://"):
                pins[f"github:{m.group(1)}"] = m.group(2)
    return pins


def find_package_managers(root: Path) -> dict[str, str]:
    """Repo-relative package.json paths carrying `packageManager`, mapped to
    their value."""
    found: dict[str, str] = {}
    for rel in sorted(find_files(root, "package.json", lambda t: '"packageManager"' in t)):
        found[rel] = json.loads((root / rel).read_text(encoding="utf-8")).get("packageManager", "")
    return found
