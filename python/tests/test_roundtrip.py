"""Zero-copy roundtrip test (RED first: `Touchstone.from_data` missing → red).

Data entry is the `from_data` factory (ironclad rule 15 — no bare
constructor); zero-copy evidence is the writable `s` view (`owndata is
False`) written in place and read back through derived domains (`z`,
`data("S","MA")`) converted back to RI and compared to the written value
(independent channel, ironclad rule 2). Tolerances come from
oracle/manifest.json — never hardcoded per test (ironclad rule 3).
"""

import json
from pathlib import Path

import netwave
import numpy as np
import pytest

# Tolerance manifest (rule 3): python_relative=0 — the same memory read
# back is bit-exact (no arithmetic on the roundtrip). encoding="utf-8" is
# mandatory: the manifest carries CJK notes and Windows' default cp1252
# would raise UnicodeDecodeError.
MANIFEST = json.loads(
    (Path(__file__).parents[2] / "oracle/manifest.json").read_text(encoding="utf-8")
)
PY_TOL = MANIFEST["core_tol"]["python_relative"]


def test_from_data_s_view_is_zero_copy() -> None:
    f = netwave.Frequency.from_f([1.0], "GHz")
    # 1-port S = 0.5+0.25j, z0 = 50 (independent literals, rule 2).
    ts = netwave.Touchstone.from_data(f, [0.5, 0.25], [50.0], "S")
    view = ts.s
    assert view.shape == (1, 1, 1)
    assert view.dtype == np.complex128
    # Zero-copy: the ndarray borrows core memory, it does not own it
    # (numpy 2.x lowercase attribute).
    assert view.flags.owndata is False
    # Write-through witness 1: mutate the view, re-read `s` (a fresh
    # getter call) — a copy would hand back the untouched 0.5.
    view[0, 0, 0] = 0.75 + 0.25j
    assert ts.s[0, 0, 0].real == pytest.approx(0.75, abs=PY_TOL)
    # Write-through witness 2 (stronger): the derived Z, computed fresh
    # from the live buffer, reflects the write: Z = z0(1+s)/(1-s) = 150+200j.
    z = ts.z[0, 0, 0]
    assert z.real == pytest.approx(150.0, abs=1e-6)
    assert z.imag == pytest.approx(200.0, abs=1e-6)
    # MA back to RI — the independent verification channel.
    ma = ts.data("S", "MA")
    re = ma[0, 0, 0, 0] * np.cos(np.radians(ma[0, 0, 0, 1]))
    im = ma[0, 0, 0, 0] * np.sin(np.radians(ma[0, 0, 0, 1]))
    assert re == pytest.approx(0.75, abs=1e-12)
    assert im == pytest.approx(0.25, abs=1e-12)
    ts.drop()


def test_from_data_parameter_required() -> None:
    f = netwave.Frequency.from_f([1.0], "GHz")
    with pytest.raises(TypeError):
        netwave.Touchstone.from_data(f, [1.0, 0.0], 50.0)  # type: ignore[call-arg]


def test_drop_invalidates_access() -> None:
    f = netwave.Frequency.from_f([1.0], "GHz")
    ts = netwave.Touchstone.from_data(f, [0.5, 0.25], [50.0], "S")
    ts.drop()
    with pytest.raises(ValueError, match="dropped"):
        _ = ts.s
    ts.drop()  # idempotent
