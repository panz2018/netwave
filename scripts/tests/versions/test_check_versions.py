"""Facade tests for check_versions.main — error aggregation and exit codes.

The facade binds `all_laws`/`summary` at import time, so the swap target is
the name on the facade module (check_versions.all_laws), not lib.rules.

The __main__-guard tests below re-execute the facade file with runpy, which
re-runs its `from lib.rules import ...` statements against sys.modules, so
their swap target is the source module (lib.rules), not the facade."""

import runpy

import check_versions
import lib.rules
import pytest


class TestGateFacade:
    def test_violations_print_error_prefixed_and_exit_1(self, monkeypatch, capsys):
        monkeypatch.setattr(
            check_versions,
            "all_laws",
            lambda root: [["core/Cargo.toml: missing pin", "drift"], [], ["pm bad"], []],
        )
        assert check_versions.main() == 1
        err = capsys.readouterr().err
        assert err.count("::error::") == 3
        assert "::error::core/Cargo.toml: missing pin" in err
        assert "::error::pm bad" in err

    def test_clean_repo_prints_summary_and_exit_0(self, monkeypatch, capsys):
        monkeypatch.setattr(check_versions, "all_laws", lambda root: [[], [], [], []])
        monkeypatch.setattr(check_versions, "summary", lambda root: "version laws OK: fake")
        assert check_versions.main() == 0
        out = capsys.readouterr().out
        assert out.strip() == "version laws OK: fake"


class TestMainGuard:
    """Process-level contract: main()'s return value becomes the exit code
    via the `sys.exit(main())` guard. runpy re-executes the facade file, so
    stubs go on lib.rules (the source module its imports rebind from)."""

    def test_guard_exits_1_on_violations(self, monkeypatch, capsys):
        monkeypatch.setattr(lib.rules, "all_laws", lambda root: [["x: bad"], [], [], []])
        with pytest.raises(SystemExit) as excinfo:
            runpy.run_path(check_versions.__file__, run_name="__main__")
        assert excinfo.value.code == 1
        assert "::error::x: bad" in capsys.readouterr().err

    def test_guard_exits_0_on_clean_repo(self, monkeypatch, capsys):
        monkeypatch.setattr(lib.rules, "all_laws", lambda root: [[], [], [], []])
        monkeypatch.setattr(lib.rules, "summary", lambda root: "version laws OK: fake")
        with pytest.raises(SystemExit) as excinfo:
            runpy.run_path(check_versions.__file__, run_name="__main__")
        assert excinfo.value.code == 0
        assert "version laws OK: fake" in capsys.readouterr().out
