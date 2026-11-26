"""Gate tests for check_proposal.py's apply-guidance coverage rule: an in-flight
change's tasks.md must map every `operations.apply.guidance` anchor into a checked
task line, so a closing step cannot be silently dropped (LL-104).

Fixtures use real closing lines from this repo's own tasks.md (the
gate-apply-guidance-coverage change and the archived drain-stray-profraw change),
not invented text, so the gate is graded against what tasks.md actually looks like
(LL-108)."""

from pathlib import Path

import check_proposal
import pytest

# Closing task lines covering each apply-step anchor, in guidance order.
ALL = [
    "- [ ] 4.5 Plan/ 瘦身：本 change 结论若涉及 `Plan/` 对应章节则当场删除。",
    "- [ ] 4.4 三态时效检查：扫 `openspec/specs/` 全目录，产出更新/新增/退役结论。",
    "- [ ] 4.9 旧名清零：全仓 grep 本次改名/删除的旧标识符，活文件零残留。",
    "- [ ] 4.9b 引用归位：逐个改名/删除/移动文件核对 spec/文档位置职责散文。",
    "- [ ] 4.2 三轴 review：按 governance「元规则 review 三轴」审实现 diff。",
    "- [ ] 4.3 apply 态体检：对 diff 触碰文件全文只读体检。",
    "- [ ] 4.7 apply 中途迟到追加的决定已当场写回已定裁决段并补任务。",
    "- [ ] 4.6 跑 `pnpm check:outdated` 并消化所报 LAG。",
]


def _write(tmp_path: Path, lines: list[str]) -> Path:
    change = tmp_path / "some-change"
    change.mkdir()
    (change / "tasks.md").write_text("# Tasks\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
    return change


def test_all_five_anchors_covered(tmp_path: Path) -> None:
    change = _write(tmp_path, ALL)
    assert check_proposal.check_guidance_coverage(change) == []


def test_missing_one_anchor_is_error(tmp_path: Path) -> None:
    change = _write(tmp_path, [ln for ln in ALL if "体检" not in ln])
    errs = check_proposal.check_guidance_coverage(change)
    assert errs == ["体检"]


def test_anchor_only_in_prose_is_not_covered(tmp_path: Path) -> None:
    # 体检 mentioned only in a non-checkbox prose line -> not a covered task.
    lines = [ln for ln in ALL if "体检" not in ln]
    lines.append("本 change 的体检步骤见上文说明。")
    change = _write(tmp_path, lines)
    assert check_proposal.check_guidance_coverage(change) == ["体检"]


def test_explicit_skip_line_counts_as_covered(tmp_path: Path) -> None:
    lines = [ln for ln in ALL if "体检" not in ln]
    lines.append("- [ ] 4.3 apply 态体检：经人工裁决跳过（2026-11-16）。")
    change = _write(tmp_path, lines)
    assert check_proposal.check_guidance_coverage(change) == []


def test_repeated_anchor_still_covered(tmp_path: Path) -> None:
    lines = ALL + ["- [ ] 9.9 再跑一次 check:outdated 复核归零。"]
    change = _write(tmp_path, lines)
    assert check_proposal.check_guidance_coverage(change) == []


def test_anchors_mirrored_in_config_yaml() -> None:
    # The gate reads anchors from config.yaml at runtime; assert it finds the
    # eight expected ones in guidance order (no second hardcoded list to drift).
    assert check_proposal.guidance_anchors() == [
        "Plan/",
        "三态时效",
        "旧名清零",
        "引用归位",
        "三轴",
        "体检",
        "迟到追加",
        "check:outdated",
    ]


VALID_PROPOSAL = """# Proposal

## Why
motivation

## Non-goals
- not this

## Prior art
- `scripts/check_proposal.py`

## 专家增补
- tighten `check_proposal.py`
"""


def _valid_tasks() -> str:
    return "# Tasks\n\n" + "\n".join(ALL) + "\n- [ ] 9.0 落地 `裁决段` 机制。\n"


def _make_change(tmp_path: Path, name: str, proposal: str, tasks: str | None) -> Path:
    change = tmp_path / "changes" / name
    change.mkdir(parents=True)
    (change / "proposal.md").write_text(proposal, encoding="utf-8")
    if tasks is not None:
        (change / "tasks.md").write_text(tasks, encoding="utf-8")
    return change


def test_section_body_present_and_absent() -> None:
    lines = ["## Foo", "body", "## Bar", "other"]
    assert check_proposal.section_body(lines, "Foo") == ["body"]
    assert check_proposal.section_body(lines, "Missing") is None


def test_blindspot_missing_section_is_error() -> None:
    errs = check_proposal.check_blindspot(["## Non-goals", "- x"], "p.md")
    assert errs == ["p.md: missing required section '## 专家增补'"]


def test_blindspot_empty_is_legal() -> None:
    assert check_proposal.check_blindspot(["## 专家增补", "", "## Next"], "p.md") == []


def test_blindspot_lone_none_is_legal() -> None:
    assert check_proposal.check_blindspot(["## 专家增补", "- 无"], "p.md") == []


def test_blindspot_padding_without_reference_is_error() -> None:
    errs = check_proposal.check_blindspot(["## 专家增补", "- just a vague idea"], "p.md")
    assert len(errs) == 1
    assert "lacks a concrete reference" in errs[0]


def test_check_file_valid_proposal_passes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_proposal, "ROOT", tmp_path)
    proposal = tmp_path / "p.md"
    proposal.write_text(VALID_PROPOSAL, encoding="utf-8")

    assert check_proposal.check_file(proposal) == []


def test_check_file_missing_section_is_error(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_proposal, "ROOT", tmp_path)
    proposal = tmp_path / "p.md"
    proposal.write_text(
        "# Proposal\n\n## Prior art\n- `x.py`\n\n## 专家增补\n- 无\n",
        encoding="utf-8",
    )

    errs = check_proposal.check_file(proposal)
    assert any("Non-goals" in e for e in errs)


def test_check_file_empty_section_is_error(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_proposal, "ROOT", tmp_path)
    proposal = tmp_path / "p.md"
    proposal.write_text(
        "# Proposal\n\n## Non-goals\n\n## Prior art\n- `x.py`\n\n## 专家增补\n- 无\n",
        encoding="utf-8",
    )

    errs = check_proposal.check_file(proposal)
    assert any("has no content" in e for e in errs)


def test_check_file_prior_art_without_citation_is_error(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_proposal, "ROOT", tmp_path)
    proposal = tmp_path / "p.md"
    proposal.write_text(
        "# Proposal\n\n## Non-goals\n- x\n\n## Prior art\n- vague prose\n\n## 专家增补\n- 无\n",
        encoding="utf-8",
    )

    errs = check_proposal.check_file(proposal)
    assert any("no citation" in e for e in errs)


def test_main_no_changes_dir_is_ok(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_proposal, "CHANGES_DIR", tmp_path / "absent")
    assert check_proposal.main() == 0


def test_main_valid_change_passes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_proposal, "ROOT", tmp_path)
    monkeypatch.setattr(check_proposal, "CHANGES_DIR", tmp_path / "changes")
    monkeypatch.setattr(check_proposal, "ARCHIVE_DIR", tmp_path / "changes" / "archive")
    _make_change(tmp_path, "good", _decision_proposal(["裁决段"]), _valid_tasks())

    assert check_proposal.main() == 0


def test_main_missing_anchor_is_error(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_proposal, "ROOT", tmp_path)
    monkeypatch.setattr(check_proposal, "CHANGES_DIR", tmp_path / "changes")
    monkeypatch.setattr(check_proposal, "ARCHIVE_DIR", tmp_path / "changes" / "archive")
    tasks = "\n".join(ln for ln in _valid_tasks().splitlines() if "体检" not in ln)
    _make_change(tmp_path, "bad", VALID_PROPOSAL, tasks + "\n")

    assert check_proposal.main() == 1


def test_main_skips_archive_dir(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_proposal, "CHANGES_DIR", tmp_path / "changes")
    monkeypatch.setattr(check_proposal, "ARCHIVE_DIR", tmp_path / "changes" / "archive")
    archived = tmp_path / "changes" / "archive" / "old"
    archived.mkdir(parents=True)
    (archived / "proposal.md").write_text("# Proposal\n", encoding="utf-8")

    assert check_proposal.main() == 0


def test_blindspot_multi_bullet_with_continuation(tmp_path: Path) -> None:
    lines = ["## 专家增补", "- ref `a.py`", "  continuation text", "- ref `b.py`"]
    assert check_proposal.check_blindspot(lines, "p.md") == []


def test_guidance_coverage_missing_tasks_returns_all(tmp_path: Path) -> None:
    change = tmp_path / "no-tasks"
    change.mkdir()
    assert check_proposal.check_guidance_coverage(change) == list(check_proposal.guidance_anchors())


def test_main_guard_exits_with_code(tmp_path: Path, monkeypatch) -> None:
    import runpy

    monkeypatch.setattr(check_proposal, "ROOT", tmp_path)
    monkeypatch.setattr(check_proposal, "CHANGES_DIR", tmp_path / "changes")
    monkeypatch.setattr(check_proposal, "ARCHIVE_DIR", tmp_path / "changes" / "archive")
    _make_change(tmp_path, "good", _decision_proposal(["裁决段"]), _valid_tasks())

    with pytest.raises(SystemExit) as excinfo:
        runpy.run_path(check_proposal.__file__, run_name="__main__")
    assert excinfo.value.code == 0


# --- 已定裁决 capture rule -------------------------------------------------


def _decision_proposal(keywords: list[str]) -> str:
    body = "\n".join(f"- `{k}`：决定。" for k in keywords)
    return VALID_PROPOSAL + "\n## 已定裁决\n" + body + "\n"


def test_decision_section_missing_is_error(tmp_path: Path) -> None:
    change = tmp_path / "c"
    change.mkdir()
    (change / "proposal.md").write_text(VALID_PROPOSAL, encoding="utf-8")
    (change / "tasks.md").write_text(_valid_tasks(), encoding="utf-8")
    errs = check_proposal.check_decision_capture(change)
    assert any("已定裁决" in e for e in errs)


def test_decision_section_empty_is_error(tmp_path: Path) -> None:
    change = tmp_path / "c"
    change.mkdir()
    (change / "proposal.md").write_text(VALID_PROPOSAL + "\n## 已定裁决\n\n", encoding="utf-8")
    (change / "tasks.md").write_text(_valid_tasks(), encoding="utf-8")
    errs = check_proposal.check_decision_capture(change)
    assert any("no decision" in e or "no content" in e for e in errs)


def test_decision_keyword_without_task_is_error(tmp_path: Path) -> None:
    change = tmp_path / "c"
    change.mkdir()
    (change / "proposal.md").write_text(_decision_proposal(["裁决段", "孤儿"]), encoding="utf-8")
    (change / "tasks.md").write_text(_valid_tasks(), encoding="utf-8")
    errs = check_proposal.check_decision_capture(change)
    assert any("孤儿" in e for e in errs)


def test_decision_keyword_with_task_passes(tmp_path: Path) -> None:
    change = tmp_path / "c"
    change.mkdir()
    (change / "proposal.md").write_text(_decision_proposal(["裁决段", "双层"]), encoding="utf-8")
    tasks = _valid_tasks() + "- [ ] 9.1 实现 `双层` 保障。\n"
    (change / "tasks.md").write_text(tasks, encoding="utf-8")
    assert check_proposal.check_decision_capture(change) == []


def test_decision_all_checked_requires_tick(tmp_path: Path) -> None:
    change = tmp_path / "c"
    change.mkdir()
    (change / "proposal.md").write_text(_decision_proposal(["裁决段", "双层"]), encoding="utf-8")
    # every task checked, but the 双层 carrier stays unchecked -> red.
    tasks = (
        "\n".join(ln.replace("[ ]", "[x]") for ln in _valid_tasks().splitlines())
        + "\n- [ ] 9.1 实现 `双层` 保障。\n"
    )
    (change / "tasks.md").write_text(tasks, encoding="utf-8")
    errs = check_proposal.check_decision_capture(change)
    assert any("双层" in e for e in errs)


def test_decision_carrier_checked_when_all_done(tmp_path: Path) -> None:
    change = tmp_path / "c"
    change.mkdir()
    (change / "proposal.md").write_text(_decision_proposal(["裁决段", "双层"]), encoding="utf-8")
    tasks = _valid_tasks() + "- [x] 9.1 实现 `双层` 保障。\n"
    tasks = "\n".join(ln.replace("[ ]", "[x]") for ln in tasks.splitlines()) + "\n"
    (change / "tasks.md").write_text(tasks, encoding="utf-8")
    assert check_proposal.check_decision_capture(change) == []


def test_decision_keyword_on_continuation_line_is_carrier(tmp_path: Path) -> None:
    # A long task wraps onto a continuation line; the keyword sits only on the
    # continuation, not on the checkbox line. The carrier is the whole item, so
    # the keyword is matched and, once every task is checked, the item closes.
    change = tmp_path / "c"
    change.mkdir()
    (change / "proposal.md").write_text(_decision_proposal(["裁决段", "双层"]), encoding="utf-8")
    tasks = _valid_tasks() + "- [ ] 9.1 落实跨边界单位约定，\n  由 `双层` 保障其一致性。\n"
    tasks = "\n".join(ln.replace("[ ]", "[x]") for ln in tasks.splitlines()) + "\n"
    (change / "tasks.md").write_text(tasks, encoding="utf-8")
    assert check_proposal.check_decision_capture(change) == []


def test_main_decision_missing_is_error(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_proposal, "ROOT", tmp_path)
    monkeypatch.setattr(check_proposal, "CHANGES_DIR", tmp_path / "changes")
    monkeypatch.setattr(check_proposal, "ARCHIVE_DIR", tmp_path / "changes" / "archive")
    # proposal without 已定裁决 section
    _make_change(tmp_path, "bad", VALID_PROPOSAL, _valid_tasks())
    assert check_proposal.main() == 1


# --- 引用归位 reference-relocation rule ------------------------------------


def _relocate_change(tmp_path: Path, relocate_line: str) -> Path:
    change = tmp_path / "c"
    change.mkdir()
    (change / "tasks.md").write_text("# Tasks\n\n" + relocate_line + "\n", encoding="utf-8")
    return change


def test_relocate_lists_all_rd_files_passes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        check_proposal, "renamed_or_deleted_files", lambda: {"a/old.py", "a/new.py"}
    )
    change = _relocate_change(
        tmp_path,
        "- [x] 9.0 引用归位：`a/old.py` → `a/new.py` 散文已核。",
    )
    assert check_proposal.check_reference_relocation(change) == []


def test_relocate_rd_path_on_continuation_line_is_carrier(tmp_path: Path, monkeypatch) -> None:
    # The 引用归位 item wraps across lines (the R/D path sits on an indented
    # continuation) and a later task line follows. Exercises _checked_item_texts's
    # continuation-append branch (cur += ...) and its flush-on-next-task branch
    # (items.append when a new task line arrives while cur is set).
    monkeypatch.setattr(check_proposal, "renamed_or_deleted_files", lambda: {"a/old.py"})
    change = _relocate_change(
        tmp_path,
        "- [x] 9.0 引用归位：R/D 清单见下行\n      `a/old.py` 散文已核。\n- [ ] 9.1 其他任务。",
    )
    assert check_proposal.check_reference_relocation(change) == []


def test_relocate_missing_rd_file_is_error(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        check_proposal, "renamed_or_deleted_files", lambda: {"a/old.py", "a/new.py"}
    )
    change = _relocate_change(tmp_path, "- [x] 9.0 引用归位：只提 `a/new.py`。")
    errs = check_proposal.check_reference_relocation(change)
    assert any("a/old.py" in e for e in errs)


def test_relocate_not_applicable_passes(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_proposal, "renamed_or_deleted_files", lambda: {"a/old.py"})
    change = _relocate_change(tmp_path, "- [x] 9.0 引用归位：不适用。")
    assert check_proposal.check_reference_relocation(change) == []


def test_relocate_no_checked_line_defers_to_coverage(tmp_path: Path, monkeypatch) -> None:
    # No checked 引用归位 task -> existence is graded elsewhere; no relocation error.
    monkeypatch.setattr(check_proposal, "renamed_or_deleted_files", lambda: {"a/old.py"})
    change = _relocate_change(tmp_path, "- [ ] 9.0 引用归位：待办。")
    assert check_proposal.check_reference_relocation(change) == []


def test_relocate_no_rd_files_passes(tmp_path: Path, monkeypatch) -> None:
    # Clean tree (no R/D): a checked 引用归位 line with no paths is fine.
    monkeypatch.setattr(check_proposal, "renamed_or_deleted_files", lambda: set())
    change = _relocate_change(tmp_path, "- [x] 9.0 引用归位：无改名删除移动。")
    assert check_proposal.check_reference_relocation(change) == []


def test_relocate_no_tasks_file_returns_empty(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_proposal, "renamed_or_deleted_files", lambda: {"a.py"})
    change = tmp_path / "c"
    change.mkdir()  # no tasks.md
    assert check_proposal.check_reference_relocation(change) == []


def test_relocate_inactive_when_anchor_absent(tmp_path: Path, monkeypatch) -> None:
    # config.yaml does not declare 引用归位 -> the rule is dormant.
    monkeypatch.setattr(check_proposal, "guidance_anchors", lambda: ["旧名清零"])
    monkeypatch.setattr(check_proposal, "renamed_or_deleted_files", lambda: {"a.py"})
    change = _relocate_change(tmp_path, "- [x] 9.0 引用归位：未列 a.py。")
    assert check_proposal.check_reference_relocation(change) == []


def test_renamed_or_deleted_files_parses_r_and_d(monkeypatch) -> None:
    class _Result:
        stdout = "R100\tsrc/old.py\tsrc/new.py\nD\tgone.py\nM\tmod.py\n"

    monkeypatch.setattr(check_proposal.subprocess, "run", lambda *a, **k: _Result())
    assert check_proposal.renamed_or_deleted_files() == {
        "src/old.py",
        "src/new.py",
        "gone.py",
    }


def test_renamed_or_deleted_files_swallows_git_error(monkeypatch) -> None:
    import subprocess

    def _boom(*a, **k):
        raise subprocess.CalledProcessError(128, ["git"])

    monkeypatch.setattr(check_proposal.subprocess, "run", _boom)
    assert check_proposal.renamed_or_deleted_files() == set()
