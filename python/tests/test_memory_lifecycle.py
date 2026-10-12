"""Memory-lifecycle test for the class surface.

Contract (api-contract + memory-lifecycle specs): data entry is the
`fromX` factory (no `upload` on node/Python), reclamation is the instance
method `drop()`, post-drop access raises ValueError, a second `drop()` is
silent, and RAII (reference counting) is the fallback that also decrements
the core witness exactly once.
"""

import gc

import netwave
import numpy as np
import pytest


def _touchstone() -> netwave.Touchstone:
    """A minimal 1-port Touchstone built through the pure-data factory."""
    f = netwave.Frequency.from_f(np.array([1.0e9]), netwave.FrequencyUnit.GHz)
    return netwave.Touchstone.from_data(f, np.array([0.1, 0.2]), np.array([50.0]), "S")


def test_touchstone_factory_reads_back() -> None:
    ts = _touchstone()
    assert ts.s[0, 0, 0].real == pytest.approx(0.1)
    assert ts.s[0, 0, 0].imag == pytest.approx(0.2)


def test_frequency_drop_is_deterministic_and_idempotent() -> None:
    before = netwave.live_count()
    f = netwave.Frequency.from_f(np.array([1.0, 2.0, 3.0]), netwave.FrequencyUnit.GHz)
    assert netwave.live_count() == before + 1
    f.drop()
    assert netwave.live_count() == before
    f.drop()  # second drop: silent no-op
    assert netwave.live_count() == before


def test_touchstone_drop_frees_immediately() -> None:
    ts = _touchstone()
    ts.drop()
    with pytest.raises(ValueError):
        _ = ts.s
    ts.drop()  # idempotent


def test_frequency_drop_post_access_raises() -> None:
    f = netwave.Frequency.from_f(np.array([1.0, 2.0]), netwave.FrequencyUnit.Hz)
    assert f.npoints() == 2
    f.drop()
    with pytest.raises(ValueError):
        f.npoints()
    f.drop()  # idempotent


def test_raii_fallback_decrements_witness_once() -> None:
    before = netwave.live_count()
    f = netwave.Frequency.from_f(np.array([1.0]), netwave.FrequencyUnit.kHz)
    assert netwave.live_count() == before + 1
    del f
    gc.collect()
    assert netwave.live_count() == before


def test_no_upload_on_python_surface() -> None:
    # Data entry is the fromX factory; `upload` is browser-only (spec).
    assert not hasattr(netwave, "upload")
    assert not hasattr(netwave.Touchstone, "upload")
    assert not hasattr(netwave.Frequency, "upload")
