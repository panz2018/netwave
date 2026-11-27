"""FrequencyUnit vocabulary test (RED first: binding lacks it → red).

Expected names are independent literals (spec: frequency-unit "vocabulary
single source"); if core ever renames a variant this test trips — that is
its job as a contract tripwire, not hand-copied drift (grep gate exempts
tests for exactly this reason).
"""

import netwave
import pytest


def test_frequency_units_lists_all_five() -> None:
    assert netwave.frequency_units() == ["Hz", "kHz", "MHz", "GHz", "THz"]


def test_members_are_accessible() -> None:
    assert netwave.FrequencyUnit.kHz is not None
    assert {m for m in dir(netwave.FrequencyUnit) if not m.startswith("_")} == {
        "Hz",
        "kHz",
        "MHz",
        "GHz",
        "THz",
    }


def test_unknown_member_raises_attribute_error() -> None:
    try:
        netwave.FrequencyUnit.Hzz  # noqa: B018
    except AttributeError:
        return
    raise AssertionError("FrequencyUnit.Hzz must raise AttributeError")


def test_every_frequency_unit_variant_round_trips() -> None:
    # Each member passed through the binding exercises its to_core/From arm;
    # multipliers are independent literals (contract tripwire, not drift).
    expected = {
        netwave.FrequencyUnit.Hz: 1.0,
        netwave.FrequencyUnit.kHz: 1e3,
        netwave.FrequencyUnit.MHz: 1e6,
        netwave.FrequencyUnit.GHz: 1e9,
        netwave.FrequencyUnit.THz: 1e12,
    }
    for unit, mult in expected.items():
        f = netwave.Frequency.from_f([1.0], unit)  # enum arm -> to_core
        assert f.f.tolist() == [mult]
        assert f.unit is unit  # getter -> From<core>


def test_every_wavelength_unit_variant_round_trips() -> None:
    # Each member passed through the wavelength API exercises its to_core arm.
    expected = {
        netwave.WavelengthUnit.m: 1.0,
        netwave.WavelengthUnit.cm: 1e-2,
        netwave.WavelengthUnit.mm: 1e-3,
        netwave.WavelengthUnit.um: 1e-6,
        netwave.WavelengthUnit.nm: 1e-9,
    }
    f = netwave.Frequency.from_f([1.0], "Hz")  # 1 Hz -> lambda = c metres
    c = 299_792_458.0  # independent literal; test_constants pins the constant
    for unit, mult in expected.items():
        wl = f.wavelength(unit, 1.0)  # enum arm -> to_core
        assert wl[0] == pytest.approx(c / mult)
