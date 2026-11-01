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
