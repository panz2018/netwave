"""Facade tests for check_outdated.main — report completeness, restriction
consumption, and exit codes.

Realistic failure modes only: networked helpers (fetch_json/latest_version/
refine_node_lts/package_versions) raise, run_cmd reports failure rc; offline
discovery (find_uv_projects/action_refs) returns empty — they are plain
filesystem scans, not probes, and are not wrapped in try by design (see
completion record in tasks.md).

Exit-code contract (change add-version-restrictions): a failed segment is
reported and the command exits non-zero; the old always-exit-0 behaviour is
gone. Restriction records are stubbed to [] by default so no test depends on
whether the repo currently has restrictions.json."""

import runpy

import check_outdated
import lib.latest
import lib.repository
import pytest

# tsdown 0.23.2 is the recorded bad pairing with typescript 7.0.0; the repo
# sits on tsdown 0.23.0, so the free target to advertise is 0.23.1.
RECORDS = [
    {
        "reason": "tsdown dts 管线与 TS7 初版不兼容",
        "combos": [{"npm:typescript": "7.0.0", "npm:tsdown": "0.23.2"}],
    }
]

LOCKED = {"npm:typescript": "7.0.0", "npm:tsdown": "0.23.0"}


def _raise(name):
    def boom(*args, **kwargs):
        raise RuntimeError(f"{name} down")

    return boom


@pytest.fixture(autouse=True)
def _no_repo_state(monkeypatch):
    monkeypatch.setattr(check_outdated, "load_restrictions", lambda root: [])
    monkeypatch.setattr(check_outdated, "locked_versions", lambda root, names: {})


def _quiet_sections(monkeypatch):
    """Everything except the restriction lines runs against empty/stub data."""
    monkeypatch.setattr(check_outdated, "find_uv_projects", lambda: [])
    monkeypatch.setattr(check_outdated, "run_cmd", lambda cmd: (0, "all current"))
    monkeypatch.setattr(check_outdated, "fetch_json", lambda url: [{"cycle": "3.14"}])
    monkeypatch.setattr(check_outdated, "find_python_versions", lambda root: {})
    monkeypatch.setattr(check_outdated, "latest_version", lambda source: "9.9.9")
    monkeypatch.setattr(check_outdated, "refine_node_lts", lambda line: "26.1.1")
    monkeypatch.setattr(check_outdated, "action_refs", lambda: set())


def _lines_of(out, section_no):
    lines = out.splitlines()
    start = next(i for i, ln in enumerate(lines) if ln.startswith(f"=== {section_no}."))
    body = []
    for ln in lines[start + 1 :]:
        if ln.startswith("==="):
            break
        if ln.strip():
            body.append(ln)
    return body


class TestOutdatedReportsAndExits:
    def test_all_networked_probes_fail_still_four_sections_and_nonzero_exit(
        self, monkeypatch, capsys
    ):
        monkeypatch.setattr(check_outdated, "find_uv_projects", lambda: [])
        monkeypatch.setattr(check_outdated, "run_cmd", lambda cmd: (125, "boom"))
        monkeypatch.setattr(check_outdated, "fetch_json", _raise("fetch_json"))
        monkeypatch.setattr(check_outdated, "latest_version", _raise("latest_version"))
        monkeypatch.setattr(check_outdated, "refine_node_lts", _raise("refine_node_lts"))
        # section 4 still iterates: a version tag hits the WARN path, a
        # non-action path (no slash) hits the skip path
        monkeypatch.setattr(
            check_outdated,
            "action_refs",
            lambda: {("actions/checkout", "v4"), ("justowner", "v1")},
        )
        assert check_outdated.main() != 0
        out = capsys.readouterr().out
        for n in ("1", "2", "3", "4"):
            assert f"=== {n}." in out
        assert out.count("WARN") >= 8  # every CLI/tool probe degraded, none aborted
        assert "python-version files: WARN" in out
        assert "justowner@v1  (skip: not a github action path)" in out
        assert "actions/checkout@v4" in out and "WARN" in out
        assert "FAILED:" in out  # names what could not be checked

    def test_normal_path_marks_lag_ok_and_ref(self, monkeypatch, capsys):
        monkeypatch.setattr(check_outdated, "find_uv_projects", lambda: ["python"])
        monkeypatch.setattr(check_outdated, "run_cmd", lambda cmd: (0, "all current"))
        monkeypatch.setattr(check_outdated, "fetch_json", lambda url: [{"cycle": "3.14"}])
        monkeypatch.setattr(
            check_outdated, "find_python_versions", lambda root: {"python/.python-version": "3.14"}
        )
        monkeypatch.setattr(check_outdated, "refine_node_lts", lambda line: "26.1.1")
        monkeypatch.setattr(
            check_outdated,
            "action_refs",
            lambda: {("actions/checkout", "v4"), ("dtolnay/rust-toolchain", "stable")},
        )

        def fake_latest(source):
            return "3.14" if source[0] == "endoflife" else "9.9.9"

        monkeypatch.setattr(check_outdated, "latest_version", fake_latest)
        assert check_outdated.main() == 0
        out = capsys.readouterr().out
        # python line: field name copied from the file it checks, arrow from
        # current to latest, status mark at the tail; column widths fixed so
        # long paths cannot overflow
        assert (
            f"python-version {'python/.python-version':24s} {'3.14':8s} "
            f"-> latest stable {'3.14':8s} OK"
        ) in out
        assert "actions/checkout@v4" in out and "LAG" in out
        # a moving branch ref (stable) is documented usage, never a lag
        assert "dtolnay/rust-toolchain@stable" in out and "REF" in out
        assert "WARN" not in out

    def test_global_cli_and_tarball_lines_carry_status_marks(self, monkeypatch, capsys):
        # sections 2/3 must end every comparison line with OK/LAG/? (same
        # mark system as section 4); unparseable installed strings get ?
        # instead of a guessed verdict
        monkeypatch.setattr(check_outdated, "find_uv_projects", lambda: [])
        monkeypatch.setattr(check_outdated, "find_python_versions", lambda root: {})
        monkeypatch.setattr(check_outdated, "action_refs", lambda: set())

        def fake_run(cmd):
            if cmd == "pnpm --version":
                return (0, "pnpm 1.0.0")
            if cmd == "node --version":
                return (0, "v26.1.1")
            return (0, "no digits here")

        monkeypatch.setattr(check_outdated, "run_cmd", fake_run)
        monkeypatch.setattr(check_outdated, "fetch_json", lambda url: [{"cycle": "3.14"}])
        monkeypatch.setattr(check_outdated, "latest_version", lambda source: "9.9.9")
        monkeypatch.setattr(check_outdated, "refine_node_lts", lambda line: "26.1.1")
        assert check_outdated.main() == 0  # probes answered; only the comparison is inconclusive
        out = capsys.readouterr().out
        for section_no in ("2", "3"):
            lines = _lines_of(out, section_no)
            assert lines, f"section {section_no} has no lines"
            assert all(ln.endswith((" OK", " LAG", " ?")) for ln in lines), lines
        assert "pnpm 1.0.0" in out and "LAG" in out  # 1.0.0 behind 9.9.9
        assert "v26.1.1" in out  # node: cleaned 26.1.1 equals latest -> OK


class TestRestrictedTargets:
    def test_latest_hitting_a_recorded_combo_advertises_the_next_free_version(
        self, monkeypatch, capsys
    ):
        monkeypatch.setattr(check_outdated, "load_restrictions", lambda root: RECORDS)
        monkeypatch.setattr(check_outdated, "locked_versions", lambda root, names: LOCKED)
        monkeypatch.setattr(
            check_outdated, "package_versions", lambda eco, pkg: ["0.23.1", "0.23.2"]
        )
        _quiet_sections(monkeypatch)
        assert check_outdated.main() == 0
        line = next(
            ln for ln in _lines_of(capsys.readouterr().out, "1") if ln.startswith("npm:tsdown")
        )
        assert "target 0.23.1" in line  # not the recorded 0.23.2
        assert "SKIP tsdown dts 管线与 TS7 初版不兼容" in line

    def test_unrestricted_package_keeps_latest_as_target(self, monkeypatch, capsys):
        monkeypatch.setattr(check_outdated, "load_restrictions", lambda root: RECORDS)
        monkeypatch.setattr(check_outdated, "locked_versions", lambda root, names: LOCKED)
        monkeypatch.setattr(check_outdated, "package_versions", lambda eco, pkg: ["7.0.0"])
        _quiet_sections(monkeypatch)
        assert check_outdated.main() == 0
        line = next(
            ln for ln in _lines_of(capsys.readouterr().out, "1") if ln.startswith("npm:typescript")
        )
        assert "target 7.0.0" in line and "SKIP" not in line

    def test_only_the_package_on_the_line_is_adjusted(self, monkeypatch, capsys):
        # tsdown gets a fallback target; the peer line keeps its own latest
        monkeypatch.setattr(check_outdated, "load_restrictions", lambda root: RECORDS)
        monkeypatch.setattr(check_outdated, "locked_versions", lambda root, names: LOCKED)
        monkeypatch.setattr(
            check_outdated,
            "package_versions",
            lambda eco, pkg: ["0.23.1", "0.23.2"] if pkg == "tsdown" else ["7.0.0"],
        )
        _quiet_sections(monkeypatch)
        assert check_outdated.main() == 0
        lines = {
            ln.split()[0]: ln for ln in _lines_of(capsys.readouterr().out, "1") if "target" in ln
        }
        assert "target 0.23.1" in lines["npm:tsdown"]
        assert "target 7.0.0" in lines["npm:typescript"]

    def test_no_free_version_is_reported_as_stuck(self, monkeypatch, capsys):
        monkeypatch.setattr(check_outdated, "load_restrictions", lambda root: RECORDS)
        monkeypatch.setattr(check_outdated, "locked_versions", lambda root, names: LOCKED)
        monkeypatch.setattr(check_outdated, "package_versions", lambda eco, pkg: ["0.23.2"])
        _quiet_sections(monkeypatch)
        assert check_outdated.main() == 0  # every probe answered; the finding is in the report
        line = next(
            ln for ln in _lines_of(capsys.readouterr().out, "1") if ln.startswith("npm:tsdown")
        )
        assert "target ?" in line and "no free version" in line

    def test_registry_failure_on_one_package_does_not_stop_the_others(self, monkeypatch, capsys):
        monkeypatch.setattr(check_outdated, "load_restrictions", lambda root: RECORDS)
        monkeypatch.setattr(check_outdated, "locked_versions", lambda root, names: LOCKED)

        def fake_versions(eco, pkg):
            if pkg == "tsdown":
                raise RuntimeError("registry down")
            return ["7.0.0"]

        monkeypatch.setattr(check_outdated, "package_versions", fake_versions)
        _quiet_sections(monkeypatch)
        assert check_outdated.main() != 0
        out = capsys.readouterr().out
        assert "npm:tsdown" in out and "WARN" in out
        assert "npm:typescript" in out and "target 7.0.0" in out

    def test_registry_answering_no_stable_version_is_a_failure(self, monkeypatch, capsys):
        monkeypatch.setattr(check_outdated, "load_restrictions", lambda root: RECORDS)
        monkeypatch.setattr(check_outdated, "locked_versions", lambda root, names: LOCKED)
        monkeypatch.setattr(check_outdated, "package_versions", lambda eco, pkg: [])
        _quiet_sections(monkeypatch)
        assert check_outdated.main() != 0
        line = next(
            ln for ln in _lines_of(capsys.readouterr().out, "1") if ln.startswith("npm:tsdown")
        )
        assert "WARN" in line

    def test_package_not_locked_here_gets_no_line(self, monkeypatch, capsys):
        monkeypatch.setattr(check_outdated, "load_restrictions", lambda root: RECORDS)
        monkeypatch.setattr(check_outdated, "locked_versions", lambda root, names: {})
        _quiet_sections(monkeypatch)
        assert check_outdated.main() == 0
        assert "npm:tsdown" not in capsys.readouterr().out

    def test_no_records_prints_no_target_lines(self, monkeypatch, capsys):
        _quiet_sections(monkeypatch)
        assert check_outdated.main() == 0
        assert "target" not in capsys.readouterr().out


class TestMainGuard:
    """Process-level contract: the report holds at the `sys.exit(main())` guard
    too. runpy re-executes the facade file, so stubs go on the source modules
    (lib.latest, lib.repository) its imports rebind from."""

    def test_guard_exits_nonzero_with_every_probe_degraded(self, monkeypatch, capsys):
        monkeypatch.setattr(lib.latest, "find_uv_projects", lambda: [])
        monkeypatch.setattr(lib.latest, "run_cmd", lambda cmd: (125, "boom"))
        monkeypatch.setattr(lib.latest, "fetch_json", _raise("fetch_json"))
        monkeypatch.setattr(lib.latest, "latest_version", _raise("latest_version"))
        monkeypatch.setattr(lib.latest, "refine_node_lts", _raise("refine_node_lts"))
        monkeypatch.setattr(lib.latest, "action_refs", lambda: set())
        monkeypatch.setattr(lib.repository, "find_python_versions", lambda root: {})
        with pytest.raises(SystemExit) as excinfo:
            runpy.run_path(check_outdated.__file__, run_name="__main__")
        assert excinfo.value.code != 0
        assert "check:outdated done" in capsys.readouterr().out
