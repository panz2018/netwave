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
    # six expected ones in guidance order (no second hardcoded list to drift).
    assert check_proposal.guidance_anchors() == [
        "Plan/",
        "三态时效",
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


def test_main_decision_missing_is_error(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(check_proposal, "ROOT", tmp_path)
    monkeypatch.setattr(check_proposal, "CHANGES_DIR", tmp_path / "changes")
    monkeypatch.setattr(check_proposal, "ARCHIVE_DIR", tmp_path / "changes" / "archive")
    # proposal without 已定裁决 section
    _make_change(tmp_path, "bad", VALID_PROPOSAL, _valid_tasks())
    assert check_proposal.main() == 1
