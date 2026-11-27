"""Gate tests for check_ci.py's root-scope rule: every root `test:*` script must
be wired into ci.yml via its run-script file `scripts/run/test_<name>.sh`, and
the retired typescript-literal rule must not misfire once the node job calls the
root script instead of inlining `typescript test:<name>`."""

import json
import runpy
import sys
from pathlib import Path

import check_ci
import pytest


def _root(tmp_path: Path, scripts: dict[str, str], ci: str) -> Path:
    (tmp_path / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
    (tmp_path / "package.json").write_text(json.dumps({"scripts": scripts}), encoding="utf-8")
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text(ci, encoding="utf-8")
    return tmp_path


def test_missing_run_script_is_reported(tmp_path: Path) -> None:
    root = _root(
        tmp_path,
        {"test:ts": "bash scripts/run/test_ts.sh"},
        "jobs:\n  lint:\n    steps: []\n",
    )
    assert check_ci.check(root) == ["test:ts"]


def test_wired_run_script_passes(tmp_path: Path) -> None:
    root = _root(
        tmp_path,
        {"test:ts": "bash scripts/run/test_ts.sh"},
        "jobs:\n  node:\n    steps:\n      - run: bash scripts/run/test_ts.sh\n",
    )
    assert check_ci.check(root) == []


def test_typescript_literal_absence_does_not_misfire(tmp_path: Path) -> None:
    # The retired rule required the literal `typescript test:native` in ci.yml.
    # Once the node job calls the root script, that literal is gone; the new
    # root-scope rule must pass on the script path alone.
    root = _root(
        tmp_path,
        {"test:ts": "bash scripts/run/test_ts.sh"},
        "jobs:\n  node:\n    steps:\n      - run: bash scripts/run/test_ts.sh\n",
    )
    assert "typescript test:native" not in (root / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    assert check_ci.check(root) == []


def test_cross_entry_wired_in_real_repo() -> None:
    # The renamed cross gate (check:cross -> test:cross) must be wired through
    # scripts/run/test_cross.sh in the real repo, not just in fixtures.
    pkg = json.loads((check_ci.ROOT / "package.json").read_text(encoding="utf-8"))
    assert pkg["scripts"]["test:cross"] == "bash scripts/run/test_cross.sh"
    ci = (check_ci.ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "bash scripts/run/test_cross.sh" in ci
    assert "check:cross" not in ci


def test_multi_segment_name_maps_by_first_segment(tmp_path: Path) -> None:
    root = _root(
        tmp_path,
        {"test:rs:cov": "bash scripts/run/test_rs.sh"},
        "jobs:\n  rust:\n    steps:\n      - run: bash scripts/run/test_rs.sh\n",
    )
    assert check_ci.check(root) == []


def test_subproject_bash_script_wired_passes(tmp_path: Path) -> None:
    # A root `test:<seg>` whose value is a `bash <path>.sh` at a non-scripts/run
    # path (a subproject's own script, e.g. python/scripts/test.sh) must be
    # wired by its exact command string appearing in ci.yml.
    root = _root(
        tmp_path,
        {"test:py": "bash python/scripts/test.sh"},
        "jobs:\n  python:\n    steps:\n      - run: bash python/scripts/test.sh\n",
    )
    assert check_ci.check(root) == []


def test_subproject_bash_script_missing_is_reported(tmp_path: Path) -> None:
    root = _root(
        tmp_path,
        {"test:py": "bash python/scripts/test.sh"},
        "jobs:\n  lint:\n    steps: []\n",
    )
    assert check_ci.check(root) == ["test:py"]


def test_delegated_pnpm_command_wired_passes(tmp_path: Path) -> None:
    # A root `test:<seg>` whose value is a `pnpm -C <pkg> <cmd>` delegation has
    # no scripts/run/test_<seg>.sh file; the gate must instead require that
    # delegated command string to appear in ci.yml.
    root = _root(
        tmp_path,
        {"test:browser": "pnpm -C browser test"},
        "jobs:\n  browser:\n    steps:\n      - run: pnpm -C browser test\n",
    )
    assert check_ci.check(root) == []


def test_delegated_pnpm_command_missing_is_reported(tmp_path: Path) -> None:
    # The delegated command absent from ci.yml must be reported (the gate still
    # proves the command runs, just via the delegated form).
    root = _root(
        tmp_path,
        {"test:browser": "pnpm -C browser test"},
        "jobs:\n  lint:\n    steps: []\n",
    )
    assert check_ci.check(root) == ["test:browser"]


def test_delegated_form_only_triggers_on_pnpm_prefix(tmp_path: Path) -> None:
    # Only a value starting with the `pnpm -C` prefix (then a space) takes the
    # delegation branch; any other value keeps the bash run-script rule. A
    # non-delegated value pointing at a script absent from ci.yml is reported.
    root = _root(
        tmp_path,
        {"test:ts": "bash scripts/run/test_ts.sh"},
        "jobs:\n  node:\n    steps:\n      - run: pnpm -C browser test\n",
    )
    assert check_ci.check(root) == ["test:ts"]


def test_browser_delegation_wired_in_real_repo() -> None:
    # The real repo's root test:browser delegates to `pnpm -C browser test`, and
    # ci.yml's browser job runs that delegated command (not a run-script path).
    pkg = json.loads((check_ci.ROOT / "package.json").read_text(encoding="utf-8"))
    assert pkg["scripts"]["test:browser"] == "pnpm -C browser test"
    ci = (check_ci.ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert "pnpm -C browser test" in ci


def test_non_test_scripts_ignored(tmp_path: Path) -> None:
    root = _root(
        tmp_path,
        {"check:ts": "biome check .", "build": "tsc"},
        "jobs:\n  lint:\n    steps: []\n",
    )
    assert check_ci.check(root) == []


def test_main_reports_missing_and_exits_1(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(check_ci, "ROOT", tmp_path)
    _root(
        tmp_path,
        {"test:ts": "bash scripts/run/test_ts.sh"},
        "jobs:\n  lint:\n    steps: []\n",
    )
    assert check_ci.main() == 1
    assert "scripts/run/test_ts.sh" in capsys.readouterr().err


def test_main_reports_missing_delegation_and_exits_1(tmp_path: Path, monkeypatch, capsys) -> None:
    # main()'s delegation branch: a `pnpm -C` root script absent from ci.yml must
    # print the delegated command (not a run-script path) and exit 1.
    monkeypatch.setattr(check_ci, "ROOT", tmp_path)
    _root(
        tmp_path,
        {"test:browser": "pnpm -C browser test"},
        "jobs:\n  lint:\n    steps: []\n",
    )
    assert check_ci.main() == 1
    err = capsys.readouterr().err
    assert "pnpm -C browser test" in err
    assert "scripts/run/test_browser.sh" not in err


def test_main_all_wired_exits_0(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(check_ci, "ROOT", tmp_path)
    _root(
        tmp_path,
        {"test:ts": "bash scripts/run/test_ts.sh"},
        "jobs:\n  node:\n    steps:\n      - run: bash scripts/run/test_ts.sh\n",
    )
    assert check_ci.main() == 0
    assert "all wired" in capsys.readouterr().out


class TestMainGuard:
    """The process exit code is what CI consumes; pin it through runpy so the
    `sys.exit(main())` line is covered and a regression that drops the exit code
    fails the gate. The real repo has every root test wired, so the guard exits 0."""

    def test_module_exit_code_is_zero_on_real_repo(self, monkeypatch):
        script = str(Path(check_ci.__file__).resolve())
        monkeypatch.setattr(sys, "argv", [script])
        with pytest.raises(SystemExit) as excinfo:
            runpy.run_path(script, run_name="__main__")
        assert excinfo.value.code == 0
