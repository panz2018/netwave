"""Unit tests for the single stray-profraw implementation: the
`drain_stray_profraw` function in `lib/repository.py` and its CLI shell
`scripts/run/clean_stray_profraw.py`. Profraw files that land outside
`target/` prove the coverage chain did not take effect, so the cleanup
deletes them and reports them. Files under build outputs and dependency
caches are report inputs or unrelated and must survive untouched."""

import subprocess
import sys
from pathlib import Path

from lib.repository import drain_stray_profraw

CLI = Path(__file__).resolve().parents[2] / "scripts" / "run" / "clean_stray_profraw.py"


def _make_workspace(tmp_path: Path) -> None:
    (tmp_path / "stray.profraw").write_text("x", encoding="utf-8")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "deep.profraw").write_text("x", encoding="utf-8")
    (tmp_path / "target").mkdir()
    (tmp_path / "target" / "inside.profraw").write_text("x", encoding="utf-8")
    (tmp_path / "node_modules" / "pkg").mkdir(parents=True)
    (tmp_path / "node_modules" / "pkg" / "x.profraw").write_text("x", encoding="utf-8")
    (tmp_path / "keep.txt").write_text("x", encoding="utf-8")


def test_returns_relative_paths_of_strays(tmp_path: Path) -> None:
    _make_workspace(tmp_path)

    removed = drain_stray_profraw(tmp_path)

    assert removed == [Path("nested") / "deep.profraw", Path("stray.profraw")]


def test_target_files_survive(tmp_path: Path) -> None:
    _make_workspace(tmp_path)

    drain_stray_profraw(tmp_path)

    assert (tmp_path / "target" / "inside.profraw").exists()


def test_dependency_cache_and_other_files_survive(tmp_path: Path) -> None:
    _make_workspace(tmp_path)

    drain_stray_profraw(tmp_path)

    assert (tmp_path / "node_modules" / "pkg" / "x.profraw").exists()
    assert (tmp_path / "keep.txt").exists()


def test_clean_workspace_returns_empty(tmp_path: Path) -> None:
    (tmp_path / "target").mkdir()
    (tmp_path / "target" / "inside.profraw").write_text("x", encoding="utf-8")

    assert drain_stray_profraw(tmp_path) == []


def test_cli_deletes_strays_and_fails(tmp_path: Path) -> None:
    _make_workspace(tmp_path)

    proc = subprocess.run(
        [sys.executable, str(CLI), str(tmp_path)],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 1
    assert "stray.profraw" in proc.stderr
    assert "deep.profraw" in proc.stderr
    assert not (tmp_path / "stray.profraw").exists()
    assert (tmp_path / "target" / "inside.profraw").exists()


def test_cli_clean_workspace_exits_zero(tmp_path: Path) -> None:
    (tmp_path / "target").mkdir()
    (tmp_path / "target" / "inside.profraw").write_text("x", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(CLI), str(tmp_path)],
        capture_output=True,
        text=True,
    )

    assert proc.returncode == 0
    assert proc.stderr == ""
