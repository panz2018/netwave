#!/usr/bin/env python3
"""cross-binding comparison: four binary dumps -> this script compares them
(tasks 6.1/6.2).

Inputs: <dir>/core.bin python.bin node.bin wasm.bin — raw little-endian f64
bytes, re/im interleaved ((nfreq=2,nports=2) -> 16 f64 = 128B). Binary
rather than JSON: JSON.stringify writes -0 as 0 and loses the sign bit,
making bit-exact comparison impossible.

Rules (zero-copy-roundtrip spec):
  - the three native ends (core/python/node) match bit-exactly
  - wasm within relative tolerance < manifest core_tol
  - anti-tautology self-check: every run perturbs an in-memory copy of
    each non-reference end and requires the comparator to detect it
    (undetected -> fail); .bin files on disk are never modified

Usage: python3 scripts/cross_compare.py <dir>
"""

import json
import random
import struct
import sys
from pathlib import Path

ENDS = ("core", "python", "node", "wasm")


def load_f64s(root: Path, name: str) -> list:
    data = (root / f"{name}.bin").read_bytes()
    if len(data) % 8:
        raise ValueError(f"{name}.bin size {len(data)} not multiple of 8")
    return list(struct.unpack(f"<{len(data) // 8}d", data))


def bits(x: float) -> int:
    return struct.unpack("<Q", struct.pack("<d", x))[0]


def compare(ref: list, ends: dict, tol: float):
    """Return None when consistent, else (end, idx, message). Shared by the
    real comparison and the anti-tautology self-check so both exercise the
    exact same decision path."""
    # Native ends: bit-exact.
    for name in ("python", "node"):
        for i, (a, b) in enumerate(zip(ref, ends[name], strict=True)):
            if bits(a) != bits(b):
                return (name, i, f"bit-exact core vs {name} idx {i}: {a!r} vs {b!r}")
    # wasm: relative tolerance.
    for i, (a, b) in enumerate(zip(ref, ends["wasm"], strict=True)):
        denom = abs(a) if a != 0 else 1.0
        if abs(a - b) / denom >= tol:
            return ("wasm", i, f"tol core vs wasm idx {i}: {a!r} vs {b!r}")
    return None


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    # encoding="utf-8": manifest carries CJK notes; Windows cp1252 default fails
    manifest = root.parent / "testdata/manifest.json"
    tol = json.loads(manifest.read_text(encoding="utf-8"))["core_tol"]["relative"]

    ends = {name: load_f64s(root, name) for name in ENDS}
    n = len(ends["core"])
    print(f"comparing {n} f64 across {len(ENDS)} ends: {', '.join(ENDS)}")

    result = compare(ends["core"], ends, tol)
    if result is not None:
        print(f"FAIL: {result[2]}")
        return 1
    print("CROSS-BINDING PASS: core==python==node bit-exact, wasm within tol")

    # λ↔f round-trip axis: each end dumps its
    # f -> wavelength -> f axis; native ends must match core bit-exact,
    # wasm within tol (the same decision path as the S-matrix compare).
    freq = {name: load_f64s(root, f"{name}_freq") for name in ENDS}
    if len(freq["core"]) != 3:
        print(f"FAIL: core_freq axis {len(freq['core'])} != 3 points")
        return 1
    fresult = compare(freq["core"], freq, tol)
    if fresult is not None:
        print(f"FAIL freq round-trip: {fresult[2]}")
        return 1
    print("FREQ ROUND-TRIP PASS: core==python==node bit-exact, wasm within tol")

    # Anti-tautology self-check: perturb an in-memory copy of each
    # non-reference end at a RANDOM index and require detection AT THE
    # INJECTED END AND INDEX (proves each .bin participates, the comparator
    # is not blind, scans beyond element 0, and localizes mismatches
    # correctly — detecting them elsewhere would mean the perturbation was
    # not what tripped it). core is never a target: tampering the reference
    # is indistinguishable from tampering any native end.
    for name in ("python", "node", "wasm"):
        idx = random.randrange(n)
        tampered = {k: list(v) for k, v in ends.items()}
        # Scale the perturbation to the element's magnitude so it exceeds
        # the RELATIVE tolerance at any index (a fixed tol*2 would hide
        # under the threshold for elements with |value| > 2).
        v = tampered[name][idx]
        tampered[name][idx] = v + (abs(v) if v != 0 else 1.0) * tol * 2
        result = compare(ends["core"], tampered, tol)
        if result is None:
            print(f"SELF-CHECK FAIL: tamper={name} not detected (tautology!)")
            return 1
        if result[0] != name or result[1] != idx:
            print(
                f"SELF-CHECK FAIL: tamper={name} idx {idx}, but comparator "
                f"localized it to {result[0]} idx {result[1]}"
            )
            return 1
        print(f"SELF-CHECK PASS: tamper={name} idx {idx} detected at the injected end and index")
    return 0


if __name__ == "__main__":
    sys.exit(main())
