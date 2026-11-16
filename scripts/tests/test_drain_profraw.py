"""Unit tests for `drain_stray_profraw` in conftest.py: profraw files that
land outside `target/` prove the coverage chain did not take effect, so the
hook deletes them and reports them. Files under build outputs and dependency
caches are report inputs or unrelated and must survive untouched."""

from pathlib import Path

from conftest import drain_stray_profraw


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
