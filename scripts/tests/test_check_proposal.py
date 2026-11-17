"""Gate tests for check_proposal.py's apply-guidance coverage rule: an in-flight
change's tasks.md must map every `operations.apply.guidance` anchor into a checked
task line, so a closing step cannot be silently dropped (LL-104).

Fixtures use real closing lines from this repo's own tasks.md (the
gate-apply-guidance-coverage change and the archived drain-stray-profraw change),
not invented text, so the gate is graded against what tasks.md actually looks like
(LL-108)."""

from pathlib import Path

import check_proposal

# Closing task lines covering each apply-step anchor, in guidance order.
ALL = [
    "- [ ] 4.5 Plan/ 瘦身：本 change 结论若涉及 `Plan/` 对应章节则当场删除。",
    "- [ ] 4.4 三态时效检查：扫 `openspec/specs/` 全目录，产出更新/新增/退役结论。",
    "- [ ] 4.2 三轴 review：按 governance「元规则 review 三轴」审实现 diff。",
    "- [ ] 4.3 apply 态体检：对 diff 触碰文件全文只读体检。",
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
    # five expected ones in guidance order (no second hardcoded list to drift).
    assert check_proposal.guidance_anchors() == [
        "Plan/",
        "三态时效",
        "三轴",
        "体检",
        "check:outdated",
    ]
