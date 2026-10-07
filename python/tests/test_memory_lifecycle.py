"""Memory-lifecycle test for the class surface (RED first: classes not
exported → red).

Contract (api-contract + memory-lifecycle specs): data entry is the
constructor (no `upload` on node/Python), reclamation is the instance
method `drop()`, post-drop access raises ValueError, a second `drop()` is
silent, and RAII (reference counting) is the fallback that also decrements
the core witness exactly once.
"""

import gc

import netwave
import numpy as np
import pytest

NFREQ, NPORTS = 2, 2


def interleaved(nfreq: int, nports: int) -> np.ndarray:
    """Flat interleaved [re, im, ...] f64 buffer, re = flat index."""
    return np.arange(nfreq * nports * nports * 2, dtype=np.float64)


def test_network_constructor_reads_back() -> None:
    net = netwave.Network(interleaved(NFREQ, NPORTS), NFREQ, NPORTS)
    assert net.read_element(0) == 0.0
    assert net.read_element(5) == 5.0


def test_frequency_drop_is_deterministic_and_idempotent() -> None:
    before = netwave.live_count()
    f = netwave.Frequency.from_f(np.array([1.0, 2.0, 3.0]), netwave.FrequencyUnit.GHz)
    assert netwave.live_count() == before + 1
    f.drop()
    assert netwave.live_count() == before
    f.drop()  # second drop: silent no-op
    assert netwave.live_count() == before


def test_network_drop_frees_immediately() -> None:
    net = netwave.Network(interleaved(NFREQ, NPORTS), NFREQ, NPORTS)
    net.drop()
    with pytest.raises(ValueError):
        net.read_element(0)
    net.drop()  # idempotent


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
    # Data entry is the constructor; `upload` is browser-only (spec).
    assert not hasattr(netwave, "upload")
    assert not hasattr(netwave.Network, "upload")
    assert not hasattr(netwave.Frequency, "upload")
