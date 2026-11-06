"""Unit tests for lib.repository — discovery with skip dirs, pin extraction."""

from lib.repository import SKIP_DIRS, find_files, find_python_versions


def test_skip_dirs_cover_build_outputs():
    # regression for the drift fix: the outdated script used to miss these
    assert {"target", "target-wasm", "node_modules", ".venv", ".git", "dist", "coverage"} <= set(
        SKIP_DIRS
    )


def test_find_files_skips_excluded_dirs(tmp_path):
    (tmp_path / "keep").mkdir()
    (tmp_path / "keep" / ".python-version").write_text("3.14\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / ".python-version").write_text("3.9\n")
    (tmp_path / "target-wasm").mkdir()
    (tmp_path / "target-wasm" / ".python-version").write_text("3.9\n")
    found = find_files(tmp_path, ".python-version")
    assert found == {"keep/.python-version"}


def test_find_python_versions_reads_values(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / ".python-version").write_text("3.14\n")
    assert find_python_versions(tmp_path) == {"a/.python-version": "3.14"}
