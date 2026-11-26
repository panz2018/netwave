#!/usr/bin/env python3
"""Proposal gate: in-flight proposals must cite prior art and non-goals.

Every in-flight change proposal (`openspec/changes/*/proposal.md`, excluding
`archive/` — archived changes are settled history and are never retroactively
required to meet new rules) MUST carry two sections with substance:

- `## Non-goals`: at least one non-empty line before the next level-2
  heading — what this change explicitly will NOT do.
- `## Prior art`: at least one non-empty line, and at least one line that
  is a real citation: a URL, a repo-internal file path (a token ending in a
  known source/config extension), or the explicit statement 无现成方案
  ("no existing solution", which must be honest, not a dodge — the gate
  checks structure, review checks honesty).
- `## 专家增补` (expert blindspot): the section MUST exist, but content may
  be empty — an empty section or a lone 无 ("none") is a legal exit (the
  prompt asks "what would a top expert add that nobody requested"; honest
  silence is valid). When non-empty, every bullet line MUST carry a concrete
  reference — a backticked identifier, a repo file path, or a URL — or it
  is padding and red. Semantic quality stays with review.
- `## 已定裁决` (decision capture): the section MUST exist and be non-empty;
  each entry is `- `keyword`：explanation` and each keyword MUST be referenced
  (backticked) by a task line in tasks.md — the decision's execution carrier.
  At apply-complete state (every non-carrier task checked), each keyword's
  carrier task line must also be checked, so a late decision cannot close
  unchecked.

Zero exemptions: no skip markers, no allowlists. An honest 无现成方案 is a
legal exit, not an exemption. No in-flight changes means pass, so the gate
is green on the day it lands.

Section headings are matched case-insensitively at level 2 (`##` + space);
level-3 headings do not count as sections.

Quality of citations (authority, specificity) is a semantic judgement and
belongs to review, not here.

Usage: python3 scripts/check_proposal.py   (wired into pnpm check:meta)
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHANGES_DIR = ROOT / "openspec" / "changes"
ARCHIVE_DIR = CHANGES_DIR / "archive"

REQUIRED = ("Non-goals", "Prior art")
BLINDSPOT = "专家增补"
NO_PRIOR_STATEMENT = "无现成方案"
NO_ADDITION_STATEMENTS = {"无", "无。", "无."}
CITATION = re.compile(r"https?://|\S+\.(?:rs|py|ts|md|json|ya?ml|toml)\b", re.IGNORECASE)
BACKTICK = re.compile(r"`[^`]+`")

# Apply-step anchors are read from config.yaml at runtime (each guidance entry
# ends with a `（锚点 `X`）` marker), so config.yaml is the single source of
# truth and this gate cannot drift from the guidance it grades against. A
# closing task line in tasks.md must carry each anchor, otherwise an apply step
# was silently dropped.
ANCHOR_MARKER = re.compile(r"锚点\s*`([^`]+)`")
CHECKED_LINE = re.compile(r"^\s*-\s*\[[ xX]\]")
CONFIG_YAML = ROOT / "openspec" / "config.yaml"

# Decision-capture rule: an in-flight proposal must carry a `## 已定裁决`
# section listing every decision as `- `keyword`：explanation`, and every
# keyword must have a task line in tasks.md that references it (the keyword
# backticked anywhere in the line). At apply-complete state — every task that
# is not itself a decision carrier is checked — each keyword's carrier task
# line must also be checked, so a late decision cannot evaporate unchecked.
DECISION_SECTION = "已定裁决"
DECISION_KEYWORD = re.compile(r"^-\s*`([^`]+)`：")
TASK_LINE = re.compile(r"^\s*-\s*\[([ xX])\]")

# Reference-relocation rule: when a change renames/deletes/moves files, the
# `引用归位` closing task must list every such file so its prose references in
# specs/docs get updated. The authoritative file set is `git diff --name-status
# HEAD` (R/D entries; pure content edits M are out of scope — they change no
# reference). The gate checks list completeness only; whether the prose was
# actually updated is a semantic judgement left to review. This couples the gate
# to git state, so the step must run before commit (after commit `git diff HEAD`
# is empty and there is nothing to cross-check).
RELOCATE_ANCHOR = "引用归位"
NOT_APPLICABLE = {"不适用", "不适用。", "不适用."}


def renamed_or_deleted_files():
    """Return the set of file paths git reports as renamed or deleted against
    HEAD (R/D entries; renames contribute both old and new paths). Empty when
    git is unavailable, the tree is clean, or only adds/modifies exist — in
    those cases there is nothing for the `引用归位` step to list."""
    try:
        # core.quotePath=false so non-ASCII paths print as raw UTF-8 (git's
        # default octal-quotes+wraps them in quotes, which would never match
        # the plain path a task line lists).
        out = subprocess.run(
            ["git", "-c", "core.quotePath=false", "diff", "--name-status", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return set()
    paths = set()
    for line in out.splitlines():
        parts = line.split("\t")
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            paths.add(parts[1])
            paths.add(parts[2])
        elif status.startswith("D") and len(parts) >= 2:
            paths.add(parts[1])
    return paths


def _checked_item_texts(lines, anchor):
    """Concatenated text of every checked task item (a `- [x]` line plus its
    indented continuation lines) whose text carries `anchor`. Long task text
    wraps across lines, so the anchor and the listed paths may sit on any of
    them; only checked items count."""
    items = []
    cur = None
    for ln in lines:
        if TASK_LINE.match(ln):
            if cur is not None:
                items.append(cur)
            checked = TASK_LINE.match(ln).group(1) in "xX"
            cur = ln if checked else None
        elif cur is not None and ln.strip():
            cur += "\n" + ln
    if cur is not None:
        items.append(cur)
    return [it for it in items if anchor in it]


def check_reference_relocation(change_dir):
    """Return errors for the `引用归位` rule on one change. Active only when
    config.yaml declares the anchor. When git reports renamed/deleted files, a
    checked `引用归位` task line must list every one of them (or declare
    不适用); a missing path means a moved/renamed file's references were not
    accounted for."""
    if RELOCATE_ANCHOR not in guidance_anchors():
        return []
    rel = _rel(change_dir)
    tasks = change_dir / "tasks.md"
    if not tasks.is_file():
        return []
    items = _checked_item_texts(tasks.read_text(encoding="utf-8").splitlines(), RELOCATE_ANCHOR)
    if not items:
        return []  # anchor coverage (existence) is graded by check_guidance_coverage
    blob = "\n".join(items)
    if any(na in blob for na in NOT_APPLICABLE):
        return []
    missing = [p for p in sorted(renamed_or_deleted_files()) if p not in blob]
    return [
        f"{rel}: '引用归位' task does not list renamed/deleted file '{p}' "
        "(every R/D file from `git diff --name-status HEAD` must appear in the "
        "checked 引用归位 task, or it must declare 不适用)"
        for p in missing
    ]


def guidance_anchors():
    """Return the apply-guidance anchors, in order, parsed from the
    `operations.apply.guidance` block of openspec/config.yaml. Each guidance
    entry carries a trailing `（锚点 `X`）` marker; the anchors are extracted
    in document order so the gate mirrors the guidance exactly."""
    text = CONFIG_YAML.read_text(encoding="utf-8")
    apply_block = text.split("  apply:", 1)[1].split("  archive:", 1)[0]
    return ANCHOR_MARKER.findall(apply_block)


def _rel(path):
    """Repo-relative path for error messages; falls back to the path itself
    when it lies outside ROOT (test fixtures under tmp_path)."""
    try:
        return path.relative_to(ROOT)
    except ValueError:
        return path


def section_body(lines, title):
    """Return body lines of a level-2 `## <title>` section (case-insensitive),
    up to the next level-2 heading; None if the heading is absent."""
    pat = re.compile(rf"^##\s+{re.escape(title)}\s*$", re.IGNORECASE)
    for i, line in enumerate(lines):
        if pat.match(line):
            body = []
            for nxt in lines[i + 1 :]:
                if re.match(r"^##\s", nxt):
                    break
                body.append(nxt)
            return body
    return None


def check_blindspot(lines, rel):
    """`## 专家增补`: existence hard, content optional; non-empty bullets
    must each carry a concrete reference (backtick / path / URL)."""
    pat = re.compile(rf"^##\s+{re.escape(BLINDSPOT)}\s*$", re.IGNORECASE)
    start = None
    for i, line in enumerate(lines):
        if pat.match(line):
            start = i
            break
    if start is None:
        return [f"{rel}: missing required section '## {BLINDSPOT}'"]
    errs = []
    items = []  # (start_line_no, joined_text) — a bullet plus its continuations
    cur_no, cur = None, []
    for offset, line in enumerate(lines[start + 1 :], start=start + 2):
        if re.match(r"^##\s", line):
            break
        stripped = line.strip()
        if stripped.startswith(("- ", "* ")):
            if cur_no is not None:
                items.append((cur_no, " ".join(cur)))
            cur_no, cur = offset, [stripped[2:]]
        elif stripped and cur_no is not None:
            cur.append(stripped)
    if cur_no is not None:
        items.append((cur_no, " ".join(cur)))
    for no, text in items:
        if text in NO_ADDITION_STATEMENTS:
            continue
        if not (BACKTICK.search(text) or CITATION.search(text)):
            errs.append(
                f"{rel}:{no}: '{BLINDSPOT}' bullet lacks a concrete "
                "reference (need a backticked identifier, repo file path, or URL)"
            )
    return errs


def check_file(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    rel = path.relative_to(ROOT)
    errs = []
    for title in REQUIRED:
        body = section_body(lines, title)
        if body is None:
            errs.append(f"{rel}: missing required section '## {title}'")
            continue
        content = [ln for ln in body if ln.strip()]
        if not content:
            errs.append(f"{rel}: section '## {title}' has no content")
        elif title == "Prior art" and not any(
            CITATION.search(ln) or NO_PRIOR_STATEMENT in ln for ln in content
        ):
            errs.append(
                f"{rel}: '## Prior art' has no citation "
                "(need a URL, a repo file path, or 无现成方案)"
            )
    errs.extend(check_blindspot(lines, rel))
    return errs


def check_guidance_coverage(change_dir):
    """Return the apply-guidance anchors missing from `change_dir/tasks.md`.

    An anchor is covered when at least one checked task line (`- [ ]` or
    `- [x]`) contains it. Prose, headings and non-checkbox bullets do not
    count. Existence only, never a count — one guidance step may map to
    several tasks, and an explicit skip written as a checked task line
    (anchor + 跳过 + ISO date) still carries the anchor and so counts as
    covered. Returns the missing anchors in guidance order; empty means the
    closing tasks cover every apply step."""
    tasks = change_dir / "tasks.md"
    anchors = guidance_anchors()
    if not tasks.is_file():
        return list(anchors)
    checked = [
        ln for ln in tasks.read_text(encoding="utf-8").splitlines() if CHECKED_LINE.match(ln)
    ]
    return [anchor for anchor in anchors if not any(anchor in ln for ln in checked)]


def check_decision_capture(change_dir):
    """Return errors for the `## 已定裁决` decision-capture rule on one change.

    The proposal must carry a non-empty `## 已定裁决` section whose entries are
    `- `keyword`：explanation`, and every keyword must be referenced (backticked
    anywhere) by a task line in tasks.md — the decision's execution carrier.
    At apply-complete state — every task line that is not itself a decision
    carrier is checked — each keyword's carrier task line must also be checked,
    so a decision appended mid-apply cannot close unchecked."""
    rel = _rel(change_dir)
    lines = (change_dir / "proposal.md").read_text(encoding="utf-8").splitlines()
    body = section_body(lines, DECISION_SECTION)
    if body is None:
        return [f"{rel}: missing required section '## {DECISION_SECTION}'"]
    keywords = [m.group(1) for ln in body if (m := DECISION_KEYWORD.match(ln))]
    if not keywords:
        return [
            f"{rel}: section '## {DECISION_SECTION}' has no decision "
            "(need at least one `- `keyword`：` entry)"
        ]
    tasks = change_dir / "tasks.md"
    task_lines = tasks.read_text(encoding="utf-8").splitlines() if tasks.is_file() else []
    keyword_set = set(keywords)
    carriers = {kw: [] for kw in keywords}  # keyword -> checked flags of its task items
    other_unchecked = False  # a task item referencing no keyword stays unchecked
    # A task item is a `- [ ]`/`- [x]` line plus its indented continuation
    # lines (markdown wraps long task text); keywords may sit on any of them,
    # and the item's checked state is the checkbox on its first line.
    cur_checked = None
    cur_kws = set()

    def _flush():
        nonlocal other_unchecked
        if cur_checked is None:
            return
        if cur_kws:
            for kw in cur_kws:
                carriers[kw].append(cur_checked)
        elif not cur_checked:
            other_unchecked = True

    for ln in task_lines:
        m = TASK_LINE.match(ln)
        if m:
            _flush()
            cur_checked = m.group(1) != " "
            cur_kws = {k.strip("`") for k in BACKTICK.findall(ln)} & keyword_set
        elif cur_checked is not None and ln.strip():
            cur_kws |= {k.strip("`") for k in BACKTICK.findall(ln)} & keyword_set
    _flush()
    errs = [
        f"{rel}: decision keyword '{kw}' has no task line in tasks.md "
        "(every 已定裁决 keyword must map to a task carrying it)"
        for kw in keywords
        if not carriers[kw]
    ]
    if not other_unchecked:
        errs.extend(
            f"{rel}: decision keyword '{kw}' carrier task not checked at apply-complete "
            "state (all other tasks are done; the decision task must close too)"
            for kw in keywords
            if carriers[kw] and not all(carriers[kw])
        )
    return errs


def main() -> int:
    if not CHANGES_DIR.is_dir():
        print("proposal gate OK: no changes directory")
        return 0
    proposals = sorted(
        p
        for p in CHANGES_DIR.glob("*/proposal.md")
        if p.parent != ARCHIVE_DIR and not p.parent.name.startswith(".")
    )
    errors = []
    for p in proposals:
        errors.extend(check_file(p))
    for change_dir in sorted(
        d
        for d in CHANGES_DIR.glob("*/")
        if d != ARCHIVE_DIR and not d.name.startswith(".") and (d / "tasks.md").is_file()
    ):
        for anchor in check_guidance_coverage(change_dir):
            errors.append(
                f"{change_dir.relative_to(ROOT)}: tasks.md closing tasks miss apply-guidance "
                f"anchor '{anchor}' (every operations.apply.guidance step must map to a "
                "checked task; an explicit skip is a checked line with the anchor + 跳过 + "
                "ISO date)"
            )
        if (change_dir / "proposal.md").is_file():
            errors.extend(check_decision_capture(change_dir))
        errors.extend(check_reference_relocation(change_dir))
    if errors:
        for e in errors:
            print(f"::error::{e}", file=sys.stderr)
        return 1
    print(
        f"proposal gate OK: {len(proposals)} in-flight proposal(s) "
        "carry Non-goals + Prior art + 专家增补 + 已定裁决"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
