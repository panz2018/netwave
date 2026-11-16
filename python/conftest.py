"""Coverage-artifact guard for the `python/` subproject: `python/` is an
independent uv project with its own pytest rootdir, so the repo-root conftest
does not apply here and the same check is repeated locally.

A `*.profraw` outside `target/` means `LLVM_PROFILE_FILE` was unset when the
instrumented process exited, so coverage for that run was never collected into
`target/` — the resulting coverage number is untrustworthy. Such files are not
inputs to `cargo llvm-cov report`, which reads only what is registered under
`target/`, so deleting them loses nothing."""

import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent / "scripts" / "versions"))
from lib.repository import SKIP_DIRS  # noqa: E402 — single source


def drain_stray_profraw(root: Path) -> list[Path]:
    """Delete `*.profraw` under `root` outside build outputs and dependency
    caches, returning the sorted relative paths removed."""
    removed: list[Path] = []
    for path in root.rglob("*.profraw"):
        rel = path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        path.unlink()
        removed.append(rel)
    return sorted(removed)


def _drain_and_report(phase: str) -> None:
    removed = drain_stray_profraw(_HERE)
    if not removed:
        return
    names = "\n".join(f"  {p}" for p in removed)
    print(
        f"profraw outside target/ = the coverage chain did not take effect, "
        f"so coverage numbers for this run are untrustworthy "
        f"({phase}: found {len(removed)}, deleted):\n{names}",
        file=sys.stderr,
    )
    raise RuntimeError(f"{phase}: found {len(removed)} stray profraw file(s) outside target/")


@pytest.fixture(autouse=True, scope="session")
def drain_stray_profraw_session():
    """Scan once before the session and once after, deleting what is found so
    the next run starts clean and failing the run that produced the strays."""
    _drain_and_report("pre-test")
    yield
    _drain_and_report("post-test")
