"""Multi-report invocation contract for coverage_gate (tasks 2.1/2.2).

The unified-coverage design measures core and each binding glue in separate
codecov.json reports and grades them with independent floors, so the gate must
be callable once per report file and must count only the lines present in that
file (llvm-cov's `--ignore-filename-regex` keeps core lines out of the glue
report — the gate itself never sees them, which is what stops double counting).

Fixtures are minimal codecov.json payloads in the exact shape llvm-cov emits
(`{"coverage": {path: {line: "hit/total"}}}`), so the assertions pin the real
parse contract rather than a test-only abstraction. The gate reads sys.argv,
so tests swap argv in place — the script needs zero changes to satisfy this
contract (the run below records the red/green evidence tasks 2.1 asks for)."""

import json
import sys

import coverage_gate
import pytest


def _codecov(files: dict[str, dict[str, str]]) -> str:
    return json.dumps({"coverage": files})


@pytest.fixture(autouse=True)
def _gate_argv(monkeypatch):
    """coverage_gate.main() reads sys.argv directly; give it an argv-based
    facade so tests call main([report, floor]) without touching the process."""
    real_main = coverage_gate.main

    def main(argv: list[str]) -> int:
        monkeypatch.setattr(sys, "argv", ["coverage_gate.py", *argv])
        return real_main()

    monkeypatch.setattr(coverage_gate, "main", main)


def _report(tmp_path, name: str, files: dict[str, dict[str, str]]) -> str:
    p = tmp_path / name
    p.write_text(_codecov(files), encoding="utf-8")
    return str(p)


class TestMultiReportFloors:
    def test_full_report_passes_floor_100(self, tmp_path, capsys):
        files = {"repo/core/src/lib.rs": {"10": "1/1", "11": "3/3"}}
        path = _report(tmp_path, "coverage-core.json", files)
        assert coverage_gate.main([path, "100"]) == 0
        assert "2/2 = 100.00%" in capsys.readouterr().out

    def test_gap_report_fails_floor_100_and_lists_the_line(self, tmp_path, capsys):
        files = {"repo/python/src/lib.rs": {"1": "1/1", "2": "0/1", "3": "2/2"}}
        path = _report(tmp_path, "coverage-glue.json", files)
        assert coverage_gate.main([path, "100"]) == 1
        assert "missed repo/python/src/lib.rs: [2]" in capsys.readouterr().out

    def test_calibration_floor_zero_never_red(self, tmp_path, capsys):
        files = {"repo/python/src/lib.rs": {"1": "1/1", "2": "0/1", "3": "2/2"}}
        path = _report(tmp_path, "coverage-glue.json", files)
        assert coverage_gate.main([path, "0"]) == 0
        out = capsys.readouterr().out
        assert "floor 0.0%" in out
        assert "missed repo/python/src/lib.rs: [2]" in out


class TestNoDoubleCounting:
    def test_glue_report_counts_only_glue_lines(self, tmp_path, capsys):
        files = {"repo/python/src/lib.rs": {"1": "1/1", "3": "2/2"}}
        path = _report(tmp_path, "coverage-glue.json", files)
        coverage_gate.main([path, "0"])
        out = capsys.readouterr().out
        assert "2/2 = 100.00%" in out
        assert "core/src" not in out


class TestMacroAttributeExemption:
    """Pattern-driven exemption for impl-block macro attribute lines.

    `#[pymethods]` / `#[napi ...]` on an `impl` block carry one llvm-cov
    region whose count never merges back from the macro-generated wrappers
    (rustc#79651), so the line shows 0 even when every method runs. llvm-cov
    honors no line-level exclusion marker (LCOV_EXCL_* is lcov-perl only;
    `#[coverage(off)]` is nightly-only, LL-020), so the grading layer exempts
    by pattern: line missed in the report + source line matches the macro
    attribute + the next code line (skipping attrs/comments) starts `impl`.
    A missed line whose source cannot be read is never exempted — it stays
    missed (red at the production floor) and is reported as unverifiable."""

    def _src(self, tmp_path, name: str, lines: list[str]) -> str:
        p = tmp_path / name
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return str(p)

    def test_pymethods_before_impl_is_exempted(self, tmp_path, capsys):
        src = self._src(
            tmp_path,
            "glue.rs",
            ["#[pymethods]", "impl Frequency {", "    fn m() {}", "}"],
        )
        files = {src: {"1": "0/1", "2": "1/1"}}
        path = _report(tmp_path, "coverage-glue.json", files)
        assert coverage_gate.main([path, "100"]) == 0
        out = capsys.readouterr().out
        # exempted lines count as covered; the denominator stays honest
        assert "2/2 = 100.00%" in out
        assert f"exempted {src}: [1]" in out

    def test_napi_with_args_before_impl_is_exempted(self, tmp_path, capsys):
        src = self._src(
            tmp_path,
            "native.rs",
            ['#[napi(js_name = "Touchstone")]', "impl Touchstone {", "}"],
        )
        files = {src: {"1": "0/1"}}
        path = _report(tmp_path, "coverage-native.json", files)
        assert coverage_gate.main([path, "100"]) == 0
        out = capsys.readouterr().out
        assert "1/1 = 100.00%" in out
        assert f"exempted {src}: [1]" in out

    def test_macro_attribute_before_fn_stays_red(self, tmp_path, capsys):
        # A macro attribute on a plain fn is a real untested line: the
        # exemption requires the next code line to be `impl`.
        src = self._src(tmp_path, "glue.rs", ["#[napi]", "fn from_url() {}", "}"])
        files = {src: {"1": "0/1", "2": "1/1"}}
        path = _report(tmp_path, "coverage-glue.json", files)
        assert coverage_gate.main([path, "100"]) == 1
        out = capsys.readouterr().out
        assert f"missed {src}: [1]" in out
        assert "exempted" not in out

    def test_non_macro_attribute_stays_red(self, tmp_path, capsys):
        src = self._src(tmp_path, "glue.rs", ["#[derive(Debug)]", "impl S {", "}"])
        files = {src: {"1": "0/1", "2": "1/1"}}
        path = _report(tmp_path, "coverage-glue.json", files)
        assert coverage_gate.main([path, "100"]) == 1
        out = capsys.readouterr().out
        assert f"missed {src}: [1]" in out
        assert "exempted" not in out

    def test_unreadable_source_is_never_exempted(self, tmp_path, capsys):
        files = {"no/such/dir/glue.rs": {"7": "0/1"}}
        path = _report(tmp_path, "coverage-glue.json", files)
        assert coverage_gate.main([path, "100"]) == 1
        out = capsys.readouterr().out
        assert "unverifiable no/such/dir/glue.rs: [7]" in out
        assert "exempted no/such/dir/glue.rs" not in out
