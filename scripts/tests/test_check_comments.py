"""Contract tests for the stale-reference gate (check_comments).

The gate scans comments in six source/config suffixes (rs, py, ts, yml, yaml,
toml) for a closed set of fixed-shape development markers and reports every
hit with its file and line. Fixtures here are real files written under a temp
root, so assertions pin the actual scan behaviour (suffix set, marker set,
file-level exemptions) rather than a mock.

Marker literals live in string literals or f-strings, never in this file's own
comments: this file is itself inside the gate's scan surface, so a marker in a
comment line would make the gate red on its own test suite.
"""

import os
import sys

import check_comments
import pytest


@pytest.fixture(autouse=True)
def _gate_argv(monkeypatch):
    """check_comments.main() reads sys.argv directly; give it an argv-based
    facade so tests call main([root]) without touching the process."""
    real_main = check_comments.main

    def main(argv: list[str]) -> int:
        monkeypatch.setattr(sys, "argv", ["check_comments.py", *argv])
        return real_main()

    monkeypatch.setattr(check_comments, "main", main)


def _write(root, relpath: str, *lines: str) -> str:
    path = os.path.join(str(root), relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return relpath


def _scan(root) -> int:
    return check_comments.main([str(root)])


class TestFixedShapeMarkers:
    """Each marker of the closed set must be reported."""

    @pytest.mark.parametrize(
        "line",
        [
            "// " + "LL-011 windows path handling",
            "# " + "CI run 43603143333 shows the failure",
            "# " + "Re-enabled 2026-09-26 after review",
            "# " + "重新启用 2026-09-26 于评审之后",
            "# " + "已标定 coverage floor",
            "// " + "design decision 7 chose the debug build",
            "// " + "design D7 chose the debug build",
            "// " + "spec: ci-matrix defines this step",
            "// " + "see openspec/specs/ci-matrix/spec.md",
            "// " + "tracked in Plan/ notes",
            "// " + "铁律七 requires the exemption note",
        ],
    )
    def test_marker_in_rs_comment_is_red(self, tmp_path, capsys, line):
        _write(tmp_path, "core/src/lib.rs", line, "fn main() {}")
        assert _scan(tmp_path) == 1
        assert "core/src/lib.rs:1" in capsys.readouterr().out

    def test_all_markers_reported_in_one_run(self, tmp_path, capsys):
        lines = [
            "// " + "LL-047 cross-end check",
            "# " + "CI run 12345678901",
            "# " + "Re-enabled 2025-01-02",
            "// " + "design decision 12",
            "// " + "spec: workspace-layout",
        ]
        _write(tmp_path, "core/src/lib.rs", *lines)
        assert _scan(tmp_path) == 1
        out = capsys.readouterr().out
        assert "check_comments: 5 stale reference(s) found" in out


class TestConfigSuffixes:
    """The gate covers config comments, not only source comments."""

    @pytest.mark.parametrize(
        "relpath,prefix",
        [
            (".github/workflows/ci.yml", "#"),
            ("pnpm-workspace.yaml", "#"),
            ("rust-toolchain.toml", "#"),
        ],
    )
    def test_marker_in_config_comment_is_red(self, tmp_path, capsys, relpath, prefix):
        line = f"{prefix} " + "LL-034 dts glue typing"
        _write(tmp_path, relpath, line, "key: value")
        assert _scan(tmp_path) == 1
        assert f"{relpath}:1" in capsys.readouterr().out

    def test_marker_in_ts_comment_is_red(self, tmp_path, capsys):
        _write(tmp_path, "typescript/src/index.ts", "// " + "LL-050 glue link", "export {};")
        assert _scan(tmp_path) == 1
        assert "typescript/src/index.ts:1" in capsys.readouterr().out


class TestFileLevelExemptions:
    """Whitelisted files are skipped even when they carry markers."""

    @pytest.mark.parametrize(
        "relpath",
        [
            "pnpm-lock.yaml",
            "openspec/config.yaml",
            "openspec/changes/archive/2026-01-01-demo/.openspec.yaml",
            "target/generated/bindings.rs",
            "node_modules/pkg/index.ts",
        ],
    )
    def test_exempt_paths_are_not_scanned(self, tmp_path, capsys, relpath):
        prefix = "//" if relpath.endswith((".rs", ".ts")) else "#"
        _write(tmp_path, relpath, f"{prefix} " + "LL-011 spec: ci-matrix Plan/")
        assert _scan(tmp_path) == 0
        assert "OK" in capsys.readouterr().out

    def test_in_flight_change_manifest_is_scanned(self, tmp_path, capsys):
        relpath = "openspec/changes/demo-change/.openspec.yaml"
        _write(tmp_path, relpath, "# " + "LL-011 pointer")
        assert _scan(tmp_path) == 1
        assert relpath in capsys.readouterr().out

    def test_is_exempt_matches_path_components(self):
        # Direct unit test of the component rule: an exempt directory name as
        # a path component exempts the file, while `.github` (which merely
        # contains `.git` as a substring) stays on the scan surface.
        assert check_comments.is_exempt("node_modules/pkg/index.ts")
        assert check_comments.is_exempt("target/generated/bindings.rs")
        assert not check_comments.is_exempt(".github/workflows/ci.yml")

    def test_generated_directory_is_skipped(self, tmp_path, capsys):
        # Build output under a non-exempt parent still leaves the scan
        # surface via the generated-path rule.
        _write(tmp_path, "core/generated/bindings.rs", "// " + "LL-011 pointer")
        assert _scan(tmp_path) == 0
        assert "OK" in capsys.readouterr().out


class TestNoFalsePositives:
    """Current-contract wording and data values must stay green."""

    @pytest.mark.parametrize(
        "line",
        [
            "// version string carries a bare date: rustc 1.99.1 (abc1234 2026-10-13)",
            "# the floor is 100 on every platform cell",
            "// Deprecated: use from_text instead",
            "// the worker owns all computation on the main thread",
            "# instrumented build, test and report share one step",
        ],
    )
    def test_current_contract_wording_is_green(self, tmp_path, capsys, line):
        _write(tmp_path, "core/src/lib.rs", line, "fn main() {}")
        assert _scan(tmp_path) == 0
        assert "OK" in capsys.readouterr().out

    def test_bare_date_in_string_literal_is_green(self, tmp_path, capsys):
        fixture = 'V = "rustc 1.99.1 (abc1234 2026-10-13)"'
        _write(tmp_path, "scripts/tests/versions/lib/test_latest.py", fixture)
        assert _scan(tmp_path) == 0

    def test_preserved_judgments_are_green(self, tmp_path, capsys):
        """Preserved judgments (tasks 3.7): Chinese "no longer a legal option
        line" is input-behaviour description and "contract retirement" is a
        rule-lifecycle criterion -- both are current contract statements, so
        the mechanical gate must not flag them; the semantic layer (AI review)
        keeps them."""
        for line in (
            "// encoding=ISO-8859-1 时 BOM 不剥，首行不再是合法选项行",
            "# 契约废止须附三类判据之一（覆盖对照 / 违规样例红 / 废止声明）",
        ):
            _write(tmp_path, "core/src/lib.rs", line, "fn main() {}")
            assert _scan(tmp_path) == 0
        assert "OK" in capsys.readouterr().out

    def test_non_comment_lines_are_not_scanned(self, tmp_path, capsys):
        _write(tmp_path, "core/src/lib.rs", 'const S: &str = "LL-011";')
        assert _scan(tmp_path) == 0


class TestDynamicChangeNames:
    """Change directory names are generated from the filesystem; live spec
    capability names stay legal vocabulary."""

    def test_change_name_in_comment_is_red(self, tmp_path, capsys):
        os.makedirs(os.path.join(str(tmp_path), "openspec/changes/retire-old-widget"))
        _write(tmp_path, "core/src/lib.rs", "// " + "retire-old-widget dropped this path")
        assert _scan(tmp_path) == 1
        assert "core/src/lib.rs:1" in capsys.readouterr().out

    def test_live_spec_capability_name_is_green(self, tmp_path, capsys):
        os.makedirs(os.path.join(str(tmp_path), "openspec/specs/frequency-unit"))
        with open(
            os.path.join(str(tmp_path), "openspec/specs/frequency-unit/spec.md"),
            "w",
            encoding="utf-8",
        ) as fh:
            fh.write("# spec\n")
        os.makedirs(os.path.join(str(tmp_path), "openspec/changes/frequency-unit"))
        _write(tmp_path, "core/src/units.rs", "// frequency-unit conversion helper")
        assert _scan(tmp_path) == 0


class TestMainGuard:
    """The process exit code is what CI consumes; pin it through runpy so the
    `sys.exit(main())` line is covered and a regression that drops the exit code
    fails the gate."""

    def test_module_exit_code_is_one_on_hit(self, tmp_path, monkeypatch):
        import runpy
        import sys

        _write(tmp_path, "core/src/lib.rs", "// " + "LL-011 pointer")
        script = os.path.join(os.getcwd(), "scripts", "check_comments.py")
        monkeypatch.setattr(sys, "argv", [script, str(tmp_path)])
        with pytest.raises(SystemExit) as excinfo:
            runpy.run_path(script, run_name="__main__")
        assert excinfo.value.code == 1
