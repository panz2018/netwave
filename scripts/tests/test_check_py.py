"""Gate tests for check_py.py's project-scoping rule: a nested uv project that
has no pytest table of its own silently inherits the repo-root config, which
widens its coverage floor to the whole repo."""

from pathlib import Path

import check_py


def _project(tmp_path: Path, body: str) -> None:
    (tmp_path / "sub").mkdir(parents=True, exist_ok=True)
    (tmp_path / "sub" / "pyproject.toml").write_text(body, encoding="utf-8")


def test_nested_project_without_pytest_table_is_error(tmp_path: Path) -> None:
    _project(tmp_path, '[project]\nname = "sub"\n')

    errs = check_py.check_project_scoping(tmp_path)

    assert len(errs) == 1
    assert "sub/pyproject.toml" in errs[0]


def test_repo_root_pyproject_is_exempt(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "root"\n', encoding="utf-8")

    assert check_py.check_project_scoping(tmp_path) == []


def test_nested_project_with_pytest_table_passes(tmp_path: Path) -> None:
    _project(
        tmp_path,
        '[project]\nname = "sub"\n[tool.pytest.ini_options]\ntestpaths = ["tests"]\n',
    )

    assert check_py.check_project_scoping(tmp_path) == []


def test_coverage_floor_without_source_is_error(tmp_path: Path) -> None:
    _project(
        tmp_path,
        '[project]\nname = "sub"\n[tool.pytest.ini_options]\ntestpaths = ["tests"]\n'
        "[tool.coverage.report]\nfail_under = 100\n",
    )

    errs = check_py.check_project_scoping(tmp_path)

    assert len(errs) == 1
    assert "run.source" in errs[0]


def test_real_repo_passes() -> None:
    assert check_py.check_project_scoping(check_py.ROOT) == []
