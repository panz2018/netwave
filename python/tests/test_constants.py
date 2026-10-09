"""SPEED_OF_LIGHT constant contract (python end).

Expected value is an independent literal (the SI defined exact speed of
light, 299 792 458 m/s). Bit-exactness is asserted through the raw f64
bytes, not just `==` — the cross-end contract is bit-level (ironclad rule
3; exact constants never ride manifest tolerances, LL-042).
"""

import struct

import netwave.constants


def test_speed_of_light_is_si_exact_bit_pattern() -> None:
    assert netwave.constants.SPEED_OF_LIGHT == 299_792_458.0
    # Independent literal -> canonical little-endian f64 bytes; the value
    # shipped by the binding must match bit for bit.
    assert struct.pack("<d", netwave.constants.SPEED_OF_LIGHT) == struct.pack("<d", 299_792_458.0)
