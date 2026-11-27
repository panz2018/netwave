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
import os
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


def _src(tmp_path, name: str, lines: list[str]) -> str:
    p = tmp_path / name
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
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

    def test_pymethods_before_impl_is_exempted(self, tmp_path, capsys):
        src = _src(
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
        src = _src(
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

    def test_pyclass_before_pub_enum_is_exempted(self, tmp_path, capsys):
        # A `#[pyclass]` on an enum carries one llvm-cov region whose count
        # never merges back from the generated wrappers (rustc#79651, same
        # class as #[pymethods]); the struct form is ABSENT so it never
        # reaches here. Exemption requires the next code line to be `pub enum`.
        src = _src(
            tmp_path,
            "glue.rs",
            ["#[pyclass]", "pub enum FrequencyUnit {", "    Hz,", "}"],
        )
        files = {src: {"1": "0/1", "2": "1/1"}}
        path = _report(tmp_path, "coverage-glue.json", files)
        assert coverage_gate.main([path, "100"]) == 0
        out = capsys.readouterr().out
        assert "2/2 = 100.00%" in out
        assert f"exempted {src}: [1]" in out

    def test_pyclass_before_struct_stays_red(self, tmp_path, capsys):
        # The exemption is narrow to enums (the only form that produces the
        # non-merging region); a missed pyclass over a struct is unexplained
        # and must stay red rather than be silently exempted.
        src = _src(
            tmp_path,
            "glue.rs",
            ["#[pyclass]", "pub struct Frequency(S);", "}"],
        )
        files = {src: {"1": "0/1", "2": "1/1"}}
        path = _report(tmp_path, "coverage-glue.json", files)
        assert coverage_gate.main([path, "100"]) == 1
        out = capsys.readouterr().out
        assert f"missed {src}: [1]" in out
        assert "exempted" not in out

    def test_macro_attribute_before_fn_stays_red(self, tmp_path, capsys):
        # A macro attribute on a plain fn is a real untested line: the
        # exemption requires the next code line to be `impl`.
        src = _src(tmp_path, "glue.rs", ["#[napi]", "fn from_url() {}", "}"])
        files = {src: {"1": "0/1", "2": "1/1"}}
        path = _report(tmp_path, "coverage-glue.json", files)
        assert coverage_gate.main([path, "100"]) == 1
        out = capsys.readouterr().out
        assert f"missed {src}: [1]" in out
        assert "exempted" not in out

    def test_non_macro_attribute_stays_red(self, tmp_path, capsys):
        src = _src(tmp_path, "glue.rs", ["#[derive(Debug)]", "impl S {", "}"])
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


class TestDefensiveAndArtifactExemption:
    """Two narrow exemptions for structurally-unreachable lines that llvm-cov
    1.100 stopped reporting as covered (the prior toolchain's false-positive
    hid them). Both are pattern-driven, never line-number whitelists:

    - defensive map_err: a `.map_err(` arm of a statement built on an always-
      succeeds constructor (`from_shape*`/`ArrayView`/`runtime::Builder`/
      `.build(`) whose argument is derived from the data, so the error arm
      cannot be reached by any input.
    - continuation artifact: a branch-free continuation line of a multi-line
      statement that demonstrably executed (a sibling line is hit), so its 0
      count is a region non-merge artifact, not a gap.

    The negative cases pin that reachable error paths and whole-statement gaps
    stay red — the exemption must not widen to cover a real untested line."""

    def test_defensive_map_err_on_from_shape_is_exempted(self, tmp_path, capsys):
        src = _src(
            tmp_path,
            "glue.rs",
            [
                "fn s() {",
                "    let view = ndarray::ArrayView3::from_shape((nf, n, n), c)",
                "        .map_err(|e| PyValueError::new_err(e.to_string()))?;",
                "}",
            ],
        )
        # line 2 (the from_shape call) executed; line 3 (the error arm) shows 0.
        files = {src: {"2": "1/1", "3": "0/6"}}
        path = _report(tmp_path, "coverage-glue.json", files)
        assert coverage_gate.main([path, "100"]) == 0
        out = capsys.readouterr().out
        assert "2/2 = 100.00%" in out
        assert f"exempted {src}: [3]" in out
        assert "defensive map_err" in out

    def test_defensive_map_err_on_runtime_build_is_exempted(self, tmp_path, capsys):
        src = _src(
            tmp_path,
            "glue.rs",
            [
                "fn from_url() {",
                "    let rt = tokio::runtime::Builder::new_current_thread()",
                "        .build()",
                "        .map_err(|e| PyValueError::new_err(e.to_string()))?;",
                "}",
            ],
        )
        files = {src: {"2": "1/1", "3": "1/1", "4": "0/6"}}
        path = _report(tmp_path, "coverage-glue.json", files)
        assert coverage_gate.main([path, "100"]) == 0
        assert f"exempted {src}: [4]" in capsys.readouterr().out

    def test_continuation_artifact_is_exempted(self, tmp_path, capsys):
        # A multi-line `let` whose first line shows 0 but whose continuation
        # executed: the statement ran, so the 0 is a region artifact.
        src = _src(
            tmp_path,
            "glue.rs",
            [
                "fn s() {",
                "    let c: &[Complex64] =",
                "        unsafe { std::slice::from_raw_parts(ptr, len / 2) };",
                "}",
            ],
        )
        files = {src: {"2": "0/2", "3": "3/4"}}
        path = _report(tmp_path, "coverage-glue.json", files)
        assert coverage_gate.main([path, "100"]) == 0
        out = capsys.readouterr().out
        assert f"exempted {src}: [2]" in out
        assert "region non-merge artifact" in out

    def test_reachable_map_err_stays_red(self, tmp_path, capsys):
        # A `.map_err(` on a core method (no always-succeeds constructor in
        # the statement) is a real untested error path: it must NOT be exempted.
        src = _src(
            tmp_path,
            "native.rs",
            [
                "fn get_f() {",
                "    self.0",
                "        .f()",
                "        .map_err(|e| Error::from_reason(e.to_string()))",
                "}",
            ],
        )
        files = {src: {"2": "1/1", "3": "1/1", "4": "0/2"}}
        path = _report(tmp_path, "coverage-native.json", files)
        assert coverage_gate.main([path, "100"]) == 1
        out = capsys.readouterr().out
        assert f"missed {src}: [4]" in out
        assert "exempted" not in out

    def test_whole_statement_gap_stays_red(self, tmp_path, capsys):
        # A multi-line statement where NO line executed is a genuine gap: the
        # artifact exemption requires a sibling hit, so it stays red.
        src = _src(
            tmp_path,
            "glue.rs",
            [
                "fn dead() {",
                "    let x = compute(",
                "        a, b);",
                "}",
            ],
        )
        files = {src: {"1": "1/1", "2": "0/2", "3": "0/1"}}
        path = _report(tmp_path, "coverage-glue.json", files)
        assert coverage_gate.main([path, "100"]) == 1
        out = capsys.readouterr().out
        assert f"missed {src}: [2, 3]" in out
        assert "exempted" not in out

    def test_branch_continuation_stays_red(self, tmp_path, capsys):
        # A continuation line that opens a branch (`if`) is a real decision
        # point, never a structural artifact, even inside an executed statement.
        src = _src(
            tmp_path,
            "glue.rs",
            [
                "fn f() {",
                "    let x = compute(a)",
                "        if b { 1 } else { 2 };",
                "}",
            ],
        )
        files = {src: {"2": "1/1", "3": "0/2"}}
        path = _report(tmp_path, "coverage-glue.json", files)
        assert coverage_gate.main([path, "100"]) == 1
        assert f"missed {src}: [3]" in capsys.readouterr().out

    def test_single_line_missed_statement_stays_red(self, tmp_path, capsys):
        # A missed line that is its own single-line statement has no sibling
        # to prove it ran, so it is a genuine gap and stays red.
        src = _src(tmp_path, "glue.rs", ["fn f() {", "    dead();", "}"])
        files = {src: {"1": "1/1", "2": "0/1"}}
        path = _report(tmp_path, "coverage-glue.json", files)
        assert coverage_gate.main([path, "100"]) == 1
        assert f"missed {src}: [2]" in capsys.readouterr().out

    def test_closure_continuation_stays_red(self, tmp_path, capsys):
        # A continuation carrying a closure param (`|`) is a real callable
        # region; a 0 count there is an untested closure, not an artifact.
        src = _src(
            tmp_path,
            "glue.rs",
            [
                "fn f() {",
                "    let x = v.iter()",
                "        .map(|n| n as u32);",
                "}",
            ],
        )
        files = {src: {"2": "1/1", "3": "0/1"}}
        path = _report(tmp_path, "coverage-glue.json", files)
        assert coverage_gate.main([path, "100"]) == 1
        assert f"missed {src}: [3]" in capsys.readouterr().out


class TestReportParsingBranches:
    """Parsing branches the four-line fixtures never exercised: real
    llvm-cov exports carry non-line keys, and the exemption lookahead must
    skip blank/comment/attribute lines and cope with EOF."""

    def test_non_digit_keys_are_skipped(self, tmp_path, capsys):
        # llvm-cov's codecov.json carries a `message` key alongside line
        # entries; only digit keys count toward the totals.
        files = {"repo/core/src/lib.rs": {"1": "1/1", "message": "llvm-cov export"}}
        path = _report(tmp_path, "coverage-core.json", files)
        assert coverage_gate.main([path, "100"]) == 0
        assert "1/1 = 100.00%" in capsys.readouterr().out

    def test_lookahead_skips_blank_and_comment_lines(self, tmp_path, capsys):
        src = _src(
            tmp_path,
            "glue.rs",
            ["#[pymethods]", "", "// separated by prose", "impl Frequency {", "}"],
        )
        files = {src: {"1": "0/1", "4": "1/1"}}
        path = _report(tmp_path, "coverage-glue.json", files)
        assert coverage_gate.main([path, "100"]) == 0
        assert f"exempted {src}: [1]" in capsys.readouterr().out

    def test_macro_attribute_at_eof_is_not_exempted(self, tmp_path, capsys):
        # Nothing follows the attribute line: the lookahead returns "" and
        # the exemption condition fails, so the line stays missed.
        src = _src(tmp_path, "glue.rs", ["impl S {", "}", "#[pymethods]"])
        files = {src: {"1": "1/1", "2": "1/1", "3": "0/1"}}
        path = _report(tmp_path, "coverage-glue.json", files)
        assert coverage_gate.main([path, "100"]) == 1
        assert f"missed {src}: [3]" in capsys.readouterr().out


class TestLcovInput:
    """The gate also grades an llvm-cov lcov tracefile (the wasm chain has no
    codecov export: `llvm-cov --codecov` does not exist, so the chain exports
    `-format=lcov` and feeds it here). Each `DA:<line>,<hits>` record is
    already llvm-cov's OR-merged per-line hit count, so it must map to the
    same `"<hits>/1"` shape the codecov path produces — grading below then
    runs unchanged. These cases pin the parse contract and its edge branches."""

    def _lcov(self, tmp_path, text: str) -> str:
        p = tmp_path / "coverage-browser.info"
        p.write_text(text, encoding="utf-8")
        return str(p)

    def test_lcov_full_file_passes_floor_100(self, tmp_path, capsys):
        path = self._lcov(
            tmp_path,
            "SF:no/such/wasm.rs\nDA:10,5\nDA:11,0\nLF:2\nLH:1\nend_of_record\n",
        )
        # line 11 shows 0 and its source is unreadable, so it stays missed
        # (never exempted): the parse must feed real per-line counts.
        assert coverage_gate.main([path, "100"]) == 1
        out = capsys.readouterr().out
        assert "1/2 = 50.00%" in out
        assert "missed no/such/wasm.rs: [11]" in out

    def test_lcov_hit_line_counts_as_covered(self, tmp_path, capsys):
        path = self._lcov(tmp_path, "SF:core/src/lib.rs\nDA:10,7\nend_of_record\n")
        assert coverage_gate.main([path, "100"]) == 0
        assert "1/1 = 100.00%" in capsys.readouterr().out

    def test_lcov_multi_field_da_uses_first_field(self, tmp_path, capsys):
        # llvm-cov emits `DA:line,hits,checksum`; only the hits field counts.
        path = self._lcov(tmp_path, "SF:f.rs\nDA:3,4,abc99\nend_of_record\n")
        assert coverage_gate.main([path, "100"]) == 0
        assert "1/1 = 100.00%" in capsys.readouterr().out

    def test_lcov_da_before_sf_is_ignored(self, tmp_path, capsys):
        # A DA record with no preceding SF has no file to attribute: skipped.
        # If it were wrongly counted the total would be 2/2, so 1/1 proves it
        # was dropped and only the SF-attributed line counted.
        path = self._lcov(tmp_path, "DA:1,5\nSF:f.rs\nDA:2,3\nend_of_record\n")
        assert coverage_gate.main([path, "100"]) == 0
        assert "1/1 = 100.00%" in capsys.readouterr().out

    def test_lcov_non_digit_line_number_is_skipped(self, tmp_path, capsys):
        path = self._lcov(tmp_path, "SF:f.rs\nDA:notanumber,5\nDA:2,1\nend_of_record\n")
        assert coverage_gate.main([path, "100"]) == 0
        assert "1/1 = 100.00%" in capsys.readouterr().out

    def test_lcov_multiple_files_are_all_counted(self, tmp_path, capsys):
        path = self._lcov(
            tmp_path,
            "SF:a.rs\nDA:1,2\nend_of_record\nSF:b.rs\nDA:1,0\nend_of_record\n",
        )
        assert coverage_gate.main([path, "100"]) == 1
        out = capsys.readouterr().out
        assert "1/2 = 50.00%" in out
        assert "missed b.rs: [1]" in out

    def test_lcov_exemption_applies_like_json(self, tmp_path, capsys):
        # The macro-attribute exemption must fire on lcov-fed data too: the
        # grading layer is format-agnostic.
        src = _src(tmp_path, "glue.rs", ["#[pymethods]", "impl Frequency {", "}"])
        path = self._lcov(tmp_path, f"SF:{src}\nDA:1,0\nDA:2,4\nend_of_record\n")
        assert coverage_gate.main([path, "100"]) == 0
        out = capsys.readouterr().out
        assert "2/2 = 100.00%" in out
        assert f"exempted {src}: [1]" in out


class TestMainGuard:
    """The process exit code is what CI consumes; pin it through runpy so
    the `sys.exit(main())` line is covered and a regression that drops the
    exit code fails the gate."""

    def test_module_exit_code_is_one_on_missed_lines(self, tmp_path, monkeypatch):
        import runpy
        import sys

        report = tmp_path / "codecov.json"
        report.write_text(_codecov({"repo/core/src/lib.rs": {"1": "0/1"}}), encoding="utf-8")
        script = os.path.join(os.getcwd(), "scripts", "coverage_gate.py")
        monkeypatch.setattr(sys, "argv", [script, str(report), "100"])
        with pytest.raises(SystemExit) as excinfo:
            runpy.run_path(script, run_name="__main__")
        assert excinfo.value.code == 1
