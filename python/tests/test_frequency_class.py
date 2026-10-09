"""Frequency functional surface (spec: frequency-class).

Expected values are independent literals / closed-form (ironclad rule 2).
Same-machine round-trips are bit-exact; the manifest core_tol governs the
cross-platform (wasm) leg only (ironclad rule 3).
"""

import netwave
import numpy as np
import pytest


def test_from_f_array_multiplies_by_unit() -> None:
    f = netwave.Frequency.from_f(np.array([1.0, 2.0, 5.0]), "GHz")
    assert f.f.tolist() == [1e9, 2e9, 5e9]


def test_from_f_scalar_is_single_point() -> None:
    f = netwave.Frequency.from_f(2.5, "GHz")
    assert f.f.tolist() == [2.5e9]


def test_from_f_unit_required() -> None:
    with pytest.raises(TypeError):
        netwave.Frequency.from_f(np.array([1.0]))  # type: ignore[call-arg]


def test_f_is_a_copy_isolated_from_core() -> None:
    f = netwave.Frequency.from_f([1.0, 2.0], "GHz")
    arr = f.f
    arr[0] = 0.0
    assert f.f[0] == 1e9  # core untouched


def test_f_scaled_follows_unit() -> None:
    f = netwave.Frequency.from_f([1.0, 2.0, 5.0], "GHz")
    assert f.f_scaled.tolist() == [1.0, 2.0, 5.0]


def test_w_is_two_pi_f() -> None:
    f = netwave.Frequency.from_f([1.0, 2.0], "Hz")
    assert f.w.tolist() == pytest.approx([2 * np.pi, 4 * np.pi])


def test_unit_getter_returns_enum() -> None:
    f = netwave.Frequency.from_f([1.0], "GHz")
    assert f.unit is netwave.FrequencyUnit.GHz


def test_unit_setter_case_insensitive_string() -> None:
    f = netwave.Frequency.from_f([1.0], "GHz")
    f.unit = "mhz"
    assert f.unit is netwave.FrequencyUnit.MHz
    assert f.f.tolist() == [1e9]  # master data untouched
    assert f.f_scaled.tolist() == [1e3]


def test_unit_setter_illegal_quotes_input() -> None:
    f = netwave.Frequency.from_f([1.0], "GHz")
    with pytest.raises(ValueError, match="Hzz"):
        f.unit = "Hzz"


def test_wavelength_round_trip() -> None:
    core_tol = 1e-12
    f = netwave.Frequency.from_f([1e9, 2e9, 5e9], "Hz")
    wl = f.wavelength(netwave.WavelengthUnit.mm, 2.2)
    back = netwave.Frequency.from_wavelength(wl, netwave.WavelengthUnit.mm, 2.2)
    assert back.f.tolist() == pytest.approx([1e9, 2e9, 5e9], rel=core_tol)


def test_wavelength_dc_is_inf() -> None:
    f = netwave.Frequency.from_f([0.0, 1e9], "Hz")
    wl = f.wavelength(netwave.WavelengthUnit.m, 1.0)
    assert np.isinf(wl[0]) and not np.isnan(wl[0])


def test_from_wavelength_n_required() -> None:
    with pytest.raises(TypeError):
        netwave.Frequency.from_wavelength(np.array([60.0]), netwave.WavelengthUnit.mm)  # type: ignore[call-arg]


def test_copy_is_independent_and_equal() -> None:
    f = netwave.Frequency.from_f([1.0, 2.0], "GHz")
    c = f.copy()
    assert c.f.tolist() == f.f.tolist()
    assert c.unit is netwave.FrequencyUnit.GHz


def test_len_and_display_string() -> None:
    f = netwave.Frequency.from_f([1.0, 2.0, 5.0], "GHz")
    assert len(f) == 3
    assert str(f) == "Frequency(1.0-5.0 GHz, 3 pts)"
    assert repr(f) == "Frequency(1.0-5.0 GHz, 3 pts)"
    empty = netwave.Frequency.from_f([], "Hz")
    assert str(empty) == "Frequency([no freqs])"
