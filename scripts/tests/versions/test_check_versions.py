"""Facade tests for check_versions.main — error aggregation and exit codes.

The facade binds `all_laws`/`summary` at import time, so the swap target is
the name on the facade module (check_versions.all_laws), not lib.rules."""

import check_versions


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
