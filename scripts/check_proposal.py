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


def guidance_anchors():
    """Return the apply-guidance anchors, in order, parsed from the
    `operations.apply.guidance` block of openspec/config.yaml. Each guidance
    entry carries a trailing `（锚点 `X`）` marker; the anchors are extracted
    in document order so the gate mirrors the guidance exactly."""
    text = CONFIG_YAML.read_text(encoding="utf-8")
    apply_block = text.split("  apply:", 1)[1].split("  archive:", 1)[0]
    return ANCHOR_MARKER.findall(apply_block)


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
    if errors:
        for e in errors:
            print(f"::error::{e}", file=sys.stderr)
        return 1
    print(
        f"proposal gate OK: {len(proposals)} in-flight proposal(s) "
        "carry Non-goals + Prior art + 专家增补"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
