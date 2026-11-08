"""Facade tests for check_outdated.main — report completeness, restriction
consumption, and exit codes.

Realistic failure modes only: networked helpers (fetch_json/latest_version/
refine_node_lts/package_versions) raise, run_cmd reports failure rc; offline
discovery (find_uv_projects/action_refs) returns empty — they are plain
filesystem scans, not probes, and are not wrapped in try by design (see
completion record in tasks.md).

Exit-code contract (dependency-upgrade spec): unreachable sources retry
once then SKIP and never affect the exit code; FAILED (non-zero exit) stays
reserved for local probe failures and contract corruption. Restriction
records are stubbed to [] by default so no test depends on whether the repo
currently has restrictions.json."""

import runpy

import check_outdated
import lib.latest
import lib.repository
import pytest
from lib.restrictions import RestrictionFormatError

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
    monkeypatch.setattr(check_outdated, "runtime_pins", lambda root: {})


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
        # local probes that cannot run stay FAILED/WARN; network probes degrade
        # to SKIP（spec「出错不得静默」）
        assert out.count("WARN") >= 8
        assert "python-version files: SKIP" in out
        assert "justowner@v1  (skip: not a github action path)" in out
        assert "actions/checkout@v4" in out and "SKIP" in out
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
        assert check_outdated.main() != 0  # actions/checkout v4 is a LAG -> gate fails
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
        assert check_outdated.main() != 0  # pnpm 1.0.0 is a LAG -> gate fails
        out = capsys.readouterr().out
        for section_no in ("2", "3"):
            lines = _lines_of(out, section_no)
            assert lines, f"section {section_no} has no lines"
            assert all(ln.endswith((" OK", " LAG", " ?")) for ln in lines), lines
        assert "pnpm 1.0.0" in out and "LAG" in out  # 1.0.0 behind 9.9.9
        assert "v26.1.1" in out  # node: current version = machine probe

    def test_node_line_uses_machine_probe_not_repo_pin(self, monkeypatch, capsys):
        # node has no auto-applied repo pin (.nvmrc is passive — nvm does not
        # read it on cd), so its current version is what the machine reports
        monkeypatch.setattr(check_outdated, "runtime_pins", lambda root: {"npm:node": "26.13.0"})
        _quiet_sections(monkeypatch)
        monkeypatch.setattr(check_outdated, "run_cmd", lambda cmd: (0, "v24.0.0"))
        monkeypatch.setattr(check_outdated, "refine_node_lts", lambda line: "26.13.0")
        assert check_outdated.main() != 0  # node behind latest -> gate fails
        line = next(ln for ln in _lines_of(capsys.readouterr().out, "2") if ln.startswith("node"))
        assert "v24.0.0" in line and "LAG" in line


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
        assert check_outdated.main() == 0  # unreachable source = SKIP, not FAILED
        out = capsys.readouterr().out
        assert "npm:tsdown" in out and "SKIP" in out
        assert "npm:typescript" in out and "target 7.0.0" in out

    def test_registry_answering_no_stable_version_is_a_skip(self, monkeypatch, capsys):
        # a source-side anomaly (registry reachable, nothing stable listed) is
        # not a local error: SKIP, exit code unaffected
        monkeypatch.setattr(check_outdated, "load_restrictions", lambda root: RECORDS)
        monkeypatch.setattr(check_outdated, "locked_versions", lambda root, names: LOCKED)
        monkeypatch.setattr(check_outdated, "package_versions", lambda eco, pkg: [])
        _quiet_sections(monkeypatch)
        assert check_outdated.main() == 0
        line = next(
            ln for ln in _lines_of(capsys.readouterr().out, "1") if ln.startswith("npm:tsdown")
        )
        assert "SKIP" in line

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


CLI_RECORDS = [
    {
        "reason": "pnpm 1.2.0 breaks workspace resolve",
        "combos": [{"npm:pnpm": "1.2.0", "npm:typescript": "7.0.0"}],
    }
]


class TestAllSegmentsFilterTargets:
    """Spec「过期体检命令」: every segment consumes restrictions before
    reporting — a latest that forms a recorded combo with the repo's peers
    (locked versions ∪ runtime pins) reports the highest free version and
    names the reason instead of recommending latest."""

    def test_cli_probe_target_filtered_by_combo(self, monkeypatch, capsys):
        monkeypatch.setattr(check_outdated, "load_restrictions", lambda root: CLI_RECORDS)
        monkeypatch.setattr(
            check_outdated, "locked_versions", lambda root, names: {"npm:typescript": "7.0.0"}
        )
        monkeypatch.setattr(check_outdated, "runtime_pins", lambda root: {})
        _quiet_sections(monkeypatch)
        monkeypatch.setattr(
            check_outdated,
            "latest_version",
            lambda source: "1.2.0" if source[1] == "pnpm" else "9.9.9",
        )
        monkeypatch.setattr(check_outdated, "package_versions", lambda eco, pkg: ["1.1.0", "1.2.0"])
        assert check_outdated.main() == 0
        line = next(ln for ln in _lines_of(capsys.readouterr().out, "2") if ln.startswith("pnpm"))
        assert "target 1.1.0" in line
        assert "SKIP pnpm 1.2.0 breaks workspace resolve" in line

    def test_python_version_target_filtered_by_combo(self, monkeypatch, capsys):
        records = [
            {
                "reason": "numpy 2.3.0 wheels missing for python 3.16",
                "combos": [{"pypi:python": "3.16", "pypi:numpy": "2.3.0"}],
            }
        ]
        monkeypatch.setattr(check_outdated, "load_restrictions", lambda root: records)
        monkeypatch.setattr(
            check_outdated, "locked_versions", lambda root, names: {"pypi:numpy": "2.3.0"}
        )
        monkeypatch.setattr(check_outdated, "runtime_pins", lambda root: {"pypi:python": "3.15"})
        monkeypatch.setattr(check_outdated, "package_versions", lambda eco, pkg: ["3.15", "3.16"])
        _quiet_sections(monkeypatch)
        monkeypatch.setattr(
            check_outdated, "find_python_versions", lambda root: {"python/.python-version": "3.15"}
        )
        monkeypatch.setattr(
            check_outdated, "fetch_json", lambda url: [{"cycle": "3.16"}, {"cycle": "3.15"}]
        )
        assert check_outdated.main() == 0
        line = next(
            ln for ln in _lines_of(capsys.readouterr().out, "1") if ln.startswith("python-version")
        )
        assert "target 3.15" in line
        assert "SKIP numpy 2.3.0 wheels missing for python 3.16" in line
        assert "LAG" not in line  # not recommending the restricted latest

    def test_target_line_all_candidates_restricted_reports_no_free(self, monkeypatch, capsys):
        records = [
            {"reason": "both broken", "combos": [{"npm:pnpm": "1.1.0"}, {"npm:pnpm": "1.2.0"}]}
        ]
        monkeypatch.setattr(check_outdated, "load_restrictions", lambda root: records)
        monkeypatch.setattr(check_outdated, "runtime_pins", lambda root: {})
        _quiet_sections(monkeypatch)
        monkeypatch.setattr(
            check_outdated,
            "latest_version",
            lambda source: "1.2.0" if source[1] == "pnpm" else "9.9.9",
        )
        monkeypatch.setattr(check_outdated, "package_versions", lambda eco, pkg: ["1.1.0", "1.2.0"])
        assert check_outdated.main() == 0
        line = next(ln for ln in _lines_of(capsys.readouterr().out, "2") if ln.startswith("pnpm"))
        assert "no free version" in line and "SKIP both broken" in line

    def test_rustc_probe_target_filtered(self, monkeypatch, capsys):
        records = [{"reason": "rustc 9.9.9 miscompiles", "combos": [{"cargo:rustc": "9.9.9"}]}]
        monkeypatch.setattr(check_outdated, "load_restrictions", lambda root: records)
        monkeypatch.setattr(check_outdated, "runtime_pins", lambda root: {})
        _quiet_sections(monkeypatch)
        assert check_outdated.main() == 0
        line = next(ln for ln in _lines_of(capsys.readouterr().out, "2") if ln.startswith("rustc"))
        assert "no free version" in line and "SKIP rustc 9.9.9 miscompiles" in line

    def test_cargo_subcommand_target_filtered(self, monkeypatch, capsys):
        records = [
            {
                "reason": "llvm-cov 9.9.9 broken",
                "combos": [{"cargo:cargo-llvm-cov": "9.9.9"}],
            }
        ]
        monkeypatch.setattr(check_outdated, "load_restrictions", lambda root: records)
        monkeypatch.setattr(check_outdated, "runtime_pins", lambda root: {})
        _quiet_sections(monkeypatch)
        assert check_outdated.main() == 0
        line = next(
            ln for ln in _lines_of(capsys.readouterr().out, "3") if ln.startswith("cargo-llvm-cov")
        )
        assert "no free version" in line and "SKIP llvm-cov 9.9.9 broken" in line

    def test_registry_unreachable_for_target_falls_back_to_latest(self, monkeypatch, capsys):
        # candidates unavailable -> judge latest alone (tasks 2.2)
        monkeypatch.setattr(check_outdated, "load_restrictions", lambda root: CLI_RECORDS)
        monkeypatch.setattr(
            check_outdated, "locked_versions", lambda root, names: {"npm:typescript": "7.0.0"}
        )
        monkeypatch.setattr(check_outdated, "runtime_pins", lambda root: {})
        _quiet_sections(monkeypatch)
        monkeypatch.setattr(
            check_outdated,
            "latest_version",
            lambda source: "1.2.0" if source[1] == "pnpm" else "9.9.9",
        )

        def boom(eco, pkg):
            raise RuntimeError("registry down")

        monkeypatch.setattr(check_outdated, "package_versions", boom)
        assert check_outdated.main() == 0
        line = next(ln for ln in _lines_of(capsys.readouterr().out, "2") if ln.startswith("pnpm"))
        assert "no free version" in line and "SKIP" in line


class TestSkipVsFailed:
    """Spec「过期体检命令」exit-code layering: unreachable sources retry
    once then SKIP (never FAILED, never the exit code); FAILED stays for
    local probe failures and contract corruption."""

    def test_unreachable_source_retries_once_then_skips(self, monkeypatch, capsys):
        calls = []

        def flaky(url):
            calls.append(url)
            raise RuntimeError("registry unreachable")

        _quiet_sections(monkeypatch)
        monkeypatch.setattr(check_outdated, "fetch_json", flaky)
        assert check_outdated.main() == 0
        out = capsys.readouterr().out
        assert "python-version files: SKIP (registry unreachable)" in out
        assert len(calls) == 2  # one immediate retry
        assert "FAILED" not in out

    def test_flaky_source_recovers_on_retry(self, monkeypatch, capsys):
        calls = []

        def flaky(url):
            calls.append(url)
            if len(calls) == 1:
                raise RuntimeError("transient")
            return [{"cycle": "3.14"}]

        _quiet_sections(monkeypatch)
        monkeypatch.setattr(check_outdated, "fetch_json", flaky)
        assert check_outdated.main() == 0
        assert "SKIP" not in capsys.readouterr().out
        assert len(calls) == 2

    def test_python_all_cycles_restricted_reports_no_free(self, monkeypatch, capsys):
        records = [
            {
                "reason": "both lines broken",
                "combos": [{"pypi:python": "3.16"}, {"pypi:python": "3.15"}],
            }
        ]
        monkeypatch.setattr(check_outdated, "load_restrictions", lambda root: records)
        monkeypatch.setattr(check_outdated, "runtime_pins", lambda root: {"pypi:python": "3.14"})
        _quiet_sections(monkeypatch)
        monkeypatch.setattr(
            check_outdated, "find_python_versions", lambda root: {"python/.python-version": "3.14"}
        )
        monkeypatch.setattr(
            check_outdated, "fetch_json", lambda url: [{"cycle": "3.16"}, {"cycle": "3.15"}]
        )
        assert check_outdated.main() == 0
        line = next(
            ln for ln in _lines_of(capsys.readouterr().out, "1") if ln.startswith("python-version")
        )
        assert "target ?" in line and "SKIP both lines broken" in line

    def test_cli_source_unreachable_after_retry_skips_line(self, monkeypatch, capsys):
        _quiet_sections(monkeypatch)
        monkeypatch.setattr(check_outdated, "run_cmd", lambda cmd: (0, "1.0.0"))
        monkeypatch.setattr(check_outdated, "latest_version", _raise("latest_version"))
        assert check_outdated.main() == 0
        out = capsys.readouterr().out
        assert "pnpm" in out and "SKIP (latest_version down)" in out
        assert "FAILED" not in out

    def test_tarball_tool_source_unreachable_skips_line(self, monkeypatch, capsys):
        _quiet_sections(monkeypatch)
        monkeypatch.setattr(check_outdated, "run_cmd", lambda cmd: (0, "1.0.0"))

        def fake_latest(source):
            if source[0] == "github":
                raise RuntimeError("api down")
            return "9.9.9"

        monkeypatch.setattr(check_outdated, "latest_version", fake_latest)
        assert check_outdated.main() != 0  # the SKIP is not a failure, but other CLIs lag
        out = capsys.readouterr().out
        assert "wasm-pack" in out and "SKIP (api down)" in out
        assert "FAILED" not in out

    def test_local_probe_cannot_run_is_failed(self, monkeypatch, capsys):
        def fake_run(cmd):
            if cmd == "pnpm --version":
                return (125, "pnpm: command not found")
            return (0, "1.0.0")

        _quiet_sections(monkeypatch)
        monkeypatch.setattr(check_outdated, "run_cmd", fake_run)
        assert check_outdated.main() != 0
        out = capsys.readouterr().out
        assert "FAILED: pnpm" in out
        assert "pnpm" in out and "WARN" in out

    def test_broken_restrictions_json_aborts_with_failed(self, monkeypatch, capsys):
        def broken(root):
            raise RestrictionFormatError("restrictions.json: bad")

        monkeypatch.setattr(check_outdated, "load_restrictions", broken)
        assert check_outdated.main() == 1
        assert "FAILED" in capsys.readouterr().out


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


class TestSummaryAndExit:
    """The trailing SUMMARY totals LAGs per source so a truncated view cannot
    hide a segment; the command is a gate — leftover LAGs mean a non-zero
    exit, SKIPs never do."""

    def test_count_uv_changes_clean_is_zero(self):
        out = "Resolved 17 packages\nNo lockfile changes detected"
        assert check_outdated.count_uv_changes(out) == 0

    def test_count_uv_changes_dirty_counts_package_lines(self):
        out = "Resolved 3 packages\nUpdated foo v1.0.0 -> v1.1.0\nAdding bar v2.0.0"
        assert check_outdated.count_uv_changes(out) == 2

    def test_summary_all_current_when_no_lag(self, monkeypatch, capsys):
        _quiet_sections(monkeypatch)
        assert check_outdated.main() == 0
        assert "SUMMARY: 0 LAG (all current)" in capsys.readouterr().out

    def test_lag_totals_per_source_and_fails_the_run(self, monkeypatch, capsys):
        # one CI action behind latest -> exactly one LAG, everything else clean
        _quiet_sections(monkeypatch)
        monkeypatch.setattr(check_outdated, "action_refs", lambda: {("actions/checkout", "v4")})
        assert check_outdated.main() != 0
        out = capsys.readouterr().out
        assert "SUMMARY: 1 LAG (actions 1)" in out
        assert "GATE:" not in out  # the exit code is the signal; no extra line

    def test_skip_does_not_count_toward_the_gate(self, monkeypatch):
        # an unreachable source SKIPs: network luck must never fail the run
        _quiet_sections(monkeypatch)
        monkeypatch.setattr(check_outdated, "fetch_json", _raise("fetch_json"))
        monkeypatch.setattr(check_outdated, "latest_version", _raise("latest_version"))
        monkeypatch.setattr(check_outdated, "refine_node_lts", _raise("refine_node_lts"))
        assert check_outdated.main() == 0
