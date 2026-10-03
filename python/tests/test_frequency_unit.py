"""FrequencyUnit vocabulary test (RED first: binding lacks it → red).

Expected names are independent literals (spec: frequency-unit "vocabulary
single source"); if core ever renames a variant this test trips — that is
its job as a contract tripwire, not hand-copied drift (grep gate exempts
tests for exactly this reason).
"""

import netwave


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
