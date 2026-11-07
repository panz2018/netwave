"""Version string parsing and comparison — the single source of truth for
the versions domain. Missing components pad to zero, so "1.85" equals
"1.85.0" (the two old scripts disagreed here; see change
split-version-gates design)."""

import re

_EXACT = re.compile(r"\d+(\.\d+)+$")
_EXACT_PATCH = re.compile(r"\d+\.\d+\.\d+$")
_MAJOR_ONLY = re.compile(r"v?\d+$")
_NUMBERS = re.compile(r"\d+")
_STABLE = re.compile(r"^\d+(\.\d+)*$")


def is_stable_version(s: str) -> bool:
    """True for a plain numeric version like "1.2" or "1.2.3"; rejects
    pre-releases (rc/alpha/beta/alpha.1), build metadata and ranges, which
    carry letters."""
    return bool(_STABLE.match(s.strip()))


def parse_version(s: str) -> tuple[int, ...]:
    """Parse a version-ish string ("1.85", "v2.3.4", "7") into a
    zero-padded (major, minor, patch) tuple for comparison."""
    nums = tuple(int(n) for n in _NUMBERS.findall(s)[:3])
    return nums + (0,) * (3 - len(nums))


def is_exact(s: str) -> bool:
    """True for an exact pin like "1.99" or "1.99.1" (major.minor[.patch]);
    rejects major-only, ranges, and words like "stable"."""
    return bool(_EXACT.match(s.strip()))


def is_exact_patch(s: str) -> bool:
    """True only for a full major.minor.patch pin like "12.5.1" (rejects
    "12.5"); packageManager pins require all three components."""
    return bool(_EXACT_PATCH.match(s.strip()))


def is_major_only(tag: str) -> bool:
    """True for a major-only ref like "v7" or "3" — such refs auto-track
    the newest release within the major, so only a major bump is a lag."""
    return bool(_MAJOR_ONLY.match(tag.strip()))


def is_outdated(current: str, latest: str, major_only: bool = False) -> bool:
    """True when `current` lags `latest`. With major_only=True compare the
    major component only (for major-only tags)."""
    cur, new = parse_version(current), parse_version(latest)
    if major_only:
        return cur[0] < new[0]
    return cur < new
