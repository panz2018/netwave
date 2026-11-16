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
        f"profraw 散落在 target 外 = 覆盖率采集链未生效，本轮覆盖率数字不可信"
        f"（{phase}发现 {len(removed)} 个，已删除）：\n{names}",
        file=sys.stderr,
    )
    raise RuntimeError(f"{phase}发现 {len(removed)} 个散落 target 外的 profraw 文件")


@pytest.fixture(autouse=True, scope="session")
def drain_stray_profraw_session():
    """Scan once before the session and once after, deleting what is found so
    the next run starts clean and failing the run that produced the strays."""
    _drain_and_report("测试前")
    yield
    _drain_and_report("测试后")
