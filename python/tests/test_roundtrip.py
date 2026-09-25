"""Zero-copy roundtrip test (RED first: binding raises → red).

Expected values are computed independently by a closed-form formula
(constitution rule 2). Layout contract: see the zero-copy-roundtrip spec.
Tolerances come from testdata/manifest.json — never hardcoded per test
(constitution rule 3).
"""

import json
from pathlib import Path

import numpy as np

import netwave

NFREQ, NPORTS = 2, 2

# Tolerance manifest (rule 3): python reads back the exact same f64 bits it
# wrote (same memory, no arithmetic), so the relative tolerance is 0.
# encoding="utf-8" is mandatory: the manifest carries CJK notes and
# Windows' default cp1252 would raise UnicodeDecodeError.
MANIFEST = json.loads(
    (Path(__file__).parents[2] / "testdata/manifest.json").read_text(encoding="utf-8")
)
PY_TOL = MANIFEST["core_tol"]["python_relative"]


def closed_form(f: int, p: int, q: int) -> complex:
    re = f * 100 + p * 10 + q
    return complex(re, -re)


def test_fill_pattern_view_zero_copy() -> None:
    arr = netwave.fill_pattern(NFREQ, NPORTS)
    assert isinstance(arr, np.ndarray)
    assert arr.dtype == np.complex128
    assert arr.shape == (NFREQ, NPORTS, NPORTS)
    # Zero-copy: the ndarray borrows core memory, it does not own it
    # (numpy 2.x lowercase attribute).
    assert arr.flags.owndata is False
    # Pattern closed-form expectation.
    for f in range(NFREQ):
        for p in range(NPORTS):
            for q in range(NPORTS):
                assert arr[f, p, q] == closed_form(f, p, q)


def test_write_back_visible_in_core() -> None:
    arr = netwave.fill_pattern(NFREQ, NPORTS)
    arr[0, 0, 1] = 1 + 2j
    # Pass back into core and read the same flat index (same memory, no copy).
    re, im = netwave.read_element(arr, 0 * 4 + 0 * 2 + 1)
    assert abs(re - 1.0) <= PY_TOL
    assert abs(im - 2.0) <= PY_TOL
