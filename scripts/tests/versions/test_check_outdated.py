"""Facade tests for check_outdated.main — the always-exit-0 contract.

Realistic failure modes only: networked helpers (fetch_json/latest_version/
refine_node_lts) raise, run_cmd reports failure rc; offline discovery
(find_uv_projects/action_refs) returns empty — they are plain filesystem
scans, not probes, and are not wrapped in try by design (see completion
record in tasks.md)."""

import check_outdated


def _raise(name):
    def boom(*args, **kwargs):
        raise RuntimeError(f"{name} down")

    return boom


class TestOutdatedAlwaysZero:
    def test_all_networked_probes_fail_still_exit_0_with_four_sections(self, monkeypatch, capsys):
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
        assert check_outdated.main() == 0
        out = capsys.readouterr().out
        for n in ("1", "2", "3", "4"):
            assert f"=== {n}." in out
        assert out.count("WARN") >= 8  # every CLI/tool probe degraded, none aborted
        assert "python-version files: WARN" in out  # renamed from "python runtime pins"
        assert "justowner@v1  (skip: not a github action path)" in out
        assert "actions/checkout@v4" in out and "WARN" in out

    def test_normal_path_marks_lag_ok_and_ref(self, monkeypatch, capsys):
        monkeypatch.setattr(check_outdated, "find_uv_projects", lambda: ["python"])
        monkeypatch.setattr(check_outdated, "run_cmd", lambda cmd: (0, "all current"))
        monkeypatch.setattr(check_outdated, "fetch_json", lambda url: [{"cycle": "3.14"}])
        monkeypatch.setattr(
            check_outdated, "find_python_versions", lambda root: {"python/.python-version": "3.14"}
        )
        monkeypatch.setattr(check_outdated, "latest_version", lambda source: "9.9.9")
        monkeypatch.setattr(check_outdated, "refine_node_lts", lambda line: "26.1.1")
        monkeypatch.setattr(
            check_outdated,
            "action_refs",
            lambda: {("actions/checkout", "v4"), ("dtolnay/rust-toolchain", "stable")},
        )
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
        assert check_outdated.main() == 0
        out = capsys.readouterr().out
        out_lines = out.splitlines()
        for section_no in ("2", "3"):
            start = next(i for i, ln in enumerate(out_lines) if ln.startswith(f"=== {section_no}."))
            lines = []
            for ln in out_lines[start + 1 :]:
                if ln.startswith("==="):
                    break
                if ln.strip():
                    lines.append(ln)
            assert lines, f"section {section_no} has no lines"
            assert all(ln.endswith((" OK", " LAG", " ?")) for ln in lines), lines
        assert "pnpm 1.0.0" in out and "LAG" in out  # 1.0.0 behind 9.9.9
        assert "v26.1.1" in out  # node: cleaned 26.1.1 equals latest -> OK
