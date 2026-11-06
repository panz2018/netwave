"""The four version laws (dependency-upgrade spec). Each check takes the
repo root and returns a list of error strings — empty means the law holds.
Error wording is the gate's output contract: keep it byte-identical to the
pre-split check_versions.py."""

from pathlib import Path

import tomllib

from lib.repository import (
    ci_python_cells,
    find_files,
    find_package_managers,
    find_python_versions,
    is_python_project,
    rust_versions,
    toolchain_channel,
    workspace_members,
)
from lib.version import is_exact, is_exact_patch, is_outdated


def check_rust_version(root: Path) -> list[str]:
    """Law 1 (MSRV): every workspace member must pin rust-version (missing =
    FAIL, so deleting the field cannot silently escape); all values equal,
    and none above the rust-toolchain pin."""
    errors: list[str] = []
    msrvs: dict[str, str] = {}
    for rel in workspace_members(root):
        path = root / rel
        if not path.exists():
            errors.append(f"{rel}: workspace member has no Cargo.toml")
            continue
        rv = tomllib.loads(path.read_text(encoding="utf-8")).get("package", {}).get("rust-version")
        if rv is None:
            errors.append(f"{rel}: workspace member missing rust-version pin")
        else:
            msrvs[rel] = str(rv)
    if len(set(msrvs.values())) > 1:
        errors.append(f"rust-version drift: {msrvs}")
    pin_ch = toolchain_channel(root)
    if not is_exact(pin_ch):
        errors.append(f"rust-toolchain.toml: channel {pin_ch!r} is not an exact pin")
    else:
        for rel, v in msrvs.items():
            if is_outdated(pin_ch, v):
                errors.append(f"{rel}: rust-version {v} above rust-toolchain pin {pin_ch}")
    return errors


def check_python_projects(root: Path) -> list[str]:
    """Law 2 (Python project): every pyproject.toml declaring [project] must
    declare requires-python and have a sibling .python-version pin."""
    errors: list[str] = []
    for rel in sorted(find_files(root, "pyproject.toml", is_python_project)):
        doc = tomllib.loads((root / rel).read_text(encoding="utf-8"))
        if "requires-python" not in doc.get("project", {}):
            errors.append(f"{rel}: [project] missing requires-python declaration")
        if not (root / rel).parent.joinpath(".python-version").exists():
            errors.append(f"{rel}: no sibling .python-version pin")
    return errors


def check_package_manager(root: Path) -> list[str]:
    """Law 3 (packageManager): exact and equal across the repo."""
    errors: list[str] = []
    pms = find_package_managers(root)
    for rel, pm in pms.items():
        if not pm.startswith("pnpm@") or not is_exact_patch(pm.removeprefix("pnpm@")):
            errors.append(f"{rel}: packageManager {pm!r} is not an exact pnpm version")
    if len(set(pms.values())) > 1:
        errors.append(f"packageManager drift: {pms}")
    return errors


def check_ci_python_versions(root: Path) -> list[str]:
    """Law 4 (matrix coverage): every .python-version pin appears among the
    python matrix cells of the CI workflows."""
    errors: list[str] = []
    cells = ci_python_cells(root)
    for rel, pyver in find_python_versions(root).items():
        if cells and pyver not in cells:
            errors.append(f"{rel} {pyver} not among ci python matrix cells {sorted(cells)}")
    return errors


def summary(root: Path) -> str:
    """One-line pass report (output contract of the offline gate)."""
    msrvs = rust_versions(root)
    return (
        f"version laws OK: {len(msrvs)} workspace members consistent "
        f"(rust-version {next(iter(msrvs.values()))}, pin {toolchain_channel(root)})"
    )


def all_laws(root: Path) -> list[list[str]]:
    """The four laws as check functions, in report order."""
    return [
        check_rust_version(root),
        check_python_projects(root),
        check_package_manager(root),
        check_ci_python_versions(root),
    ]
