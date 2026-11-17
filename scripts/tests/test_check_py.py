"""Gate tests for check_py.py's project-scoping rule: a nested uv project that
has no pytest table of its own silently inherits the repo-root config, which
widens its coverage floor to the whole repo."""

from pathlib import Path

import check_py
import pytest


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


def _py(tmp_path: Path, rel: str, src: str) -> Path:
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(src, encoding="utf-8")
    return path


def test_elif_else_non_fallback_is_error(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_py, "ROOT", tmp_path)
    path = _py(
        tmp_path,
        "a.py",
        "def f(x):\n"
        "    if x == 1:\n"
        '        return "a"\n'
        "    elif x == 2:\n"
        '        return "b"\n'
        "    else:\n"
        '        return "c"\n',
    )

    errs, _defs = check_py.check_file(path)

    assert errs == ["a.py: else carries a non-fallback branch"]


def test_elif_else_raise_is_ok(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_py, "ROOT", tmp_path)
    path = _py(
        tmp_path,
        "a.py",
        "def f(x):\n"
        "    if x == 1:\n"
        "        return 1\n"
        "    elif x == 2:\n"
        "        return 2\n"
        "    else:\n"
        "        raise ValueError\n",
    )

    errs, _defs = check_py.check_file(path)

    assert errs == []


def test_boolean_if_else_is_exempt(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_py, "ROOT", tmp_path)
    path = _py(
        tmp_path,
        "a.py",
        "def f(x):\n    if x:\n        return 1\n    else:\n        return 2\n",
    )

    errs, _defs = check_py.check_file(path)

    assert errs == []


def test_read_text_without_encoding_is_error(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_py, "ROOT", tmp_path)
    path = _py(tmp_path, "a.py", "def f(p):\n    return p.read_text()\n")

    errs, _defs = check_py.check_file(path)

    assert any("read_text() without encoding" in e for e in errs)


def test_text_open_without_encoding_is_error(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_py, "ROOT", tmp_path)
    path = _py(tmp_path, "a.py", "def f(p):\n    return open(p)\n")

    errs, _defs = check_py.check_file(path)

    assert any("text open() without encoding" in e for e in errs)


def test_binary_open_is_exempt(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_py, "ROOT", tmp_path)
    path = _py(tmp_path, "a.py", 'def f(p):\n    return open(p, "rb")\n')

    errs, _defs = check_py.check_file(path)

    assert errs == []


def test_skip_dirs_def_is_detected(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_py, "ROOT", tmp_path)
    path = _py(tmp_path, "a.py", 'SKIP_DIRS = {"target"}\n')

    _errs, defs = check_py.check_file(path)

    assert defs == ["a.py:1"]


def test_main_ok_single_skip_dirs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_py, "ROOT", tmp_path)
    _py(tmp_path, "versions/lib/repository.py", 'SKIP_DIRS = {"target"}\n')
    _py(tmp_path, "clean.py", "x = 1\n")

    assert check_py.main() == 0


def test_main_double_skip_dirs_is_error(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_py, "ROOT", tmp_path)
    _py(tmp_path, "versions/lib/repository.py", 'SKIP_DIRS = {"target"}\n')
    _py(tmp_path, "extra.py", 'SKIP_DIRS = {"build"}\n')

    assert check_py.main() == 1


def test_main_else_violation_is_error(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_py, "ROOT", tmp_path)
    _py(tmp_path, "versions/lib/repository.py", 'SKIP_DIRS = {"target"}\n')
    _py(
        tmp_path,
        "bad.py",
        "def f(x):\n"
        "    if x == 1:\n"
        "        return 1\n"
        "    elif x == 2:\n"
        "        return 2\n"
        "    else:\n"
        "        return 3\n",
    )

    assert check_py.main() == 1


def test_elif_chain_without_else_is_exempt(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_py, "ROOT", tmp_path)
    path = _py(
        tmp_path,
        "a.py",
        "def f(x):\n    if x == 1:\n        return 1\n    elif x == 2:\n        return 2\n",
    )

    errs, _defs = check_py.check_file(path)

    assert errs == []


def test_scoping_skips_skip_dirs(tmp_path: Path) -> None:
    _py(tmp_path, "target/sub/pyproject.toml", '[project]\nname = "x"\n')

    assert check_py.check_project_scoping(tmp_path) == []


def test_main_skips_skip_dirs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_py, "ROOT", tmp_path)
    _py(tmp_path, "versions/lib/repository.py", 'SKIP_DIRS = {"target"}\n')
    _py(tmp_path, "target/vendored/bad.py", "def f(p):\n    return p.read_text()\n")

    assert check_py.main() == 0


def test_main_guard_exits_with_code(tmp_path: Path, monkeypatch) -> None:
    import runpy

    monkeypatch.setattr(check_py, "ROOT", tmp_path)
    _py(tmp_path, "versions/lib/repository.py", 'SKIP_DIRS = {"target"}\n')
    _py(tmp_path, "clean.py", "x = 1\n")

    with pytest.raises(SystemExit) as excinfo:
        runpy.run_path(check_py.__file__, run_name="__main__")
    assert excinfo.value.code == 0
