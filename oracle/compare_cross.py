#!/usr/bin/env python3
"""Horizontal-axis grading: four-end binary dumps -> this script compares them.

Inputs (layered layout, oracle/tmp/): <dir>/<end>/freq.bin and
<dir>/<end>/<sample>/s.bin (+ z0.bin, version.txt) for each end — raw
little-endian f64 bytes, re/im interleaved. `sample` is the input sample
file name with spaces sanitized to underscores; the sample files themselves
keep their original names. Binary rather than JSON: JSON.stringify writes -0
as 0 and loses the sign bit, making bit-exact comparison impossible.

Rules (oracle-harness / zero-copy-roundtrip specs):
  - the three native ends (core/python/node) match bit-exactly
  - wasm within relative tolerance < oracle/manifest.json core_tol
  - anti-tautology self-check: every run perturbs an in-memory copy of
    each non-reference end's Touchstone data and requires the comparator to
    detect it (undetected -> fail); .bin files on disk are never modified

Usage: python3 oracle/compare_cross.py <dir>   (dir = oracle/tmp)
"""

import json
import random
import struct
import sys
from pathlib import Path

ENDS = ("core", "python", "node", "wasm")
# Input samples, as file names under oracle/samples/. The directory name
# used for dumps is the same name with spaces sanitized to underscores.
SAMPLES = ("dut.s1p", "dut.s2p", "dut.s4p")


def sanitize(sample: str) -> str:
    return sample.replace(" ", "_")


def load_f64s(path: Path) -> list:
    data = path.read_bytes()
    if len(data) % 8:
        raise ValueError(f"{path} size {len(data)} not multiple of 8")
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
    manifest = Path(__file__).resolve().parent / "manifest.json"
    tol = json.loads(manifest.read_text(encoding="utf-8"))["core_tol"]["relative"]

    # λ↔f round-trip axis: each end dumps its
    # f -> wavelength -> f axis; native ends must match core bit-exact,
    # wasm within tol (the same decision path as the S-matrix compare).
    freq = {name: load_f64s(root / name / "freq.bin") for name in ENDS}
    if len(freq["core"]) != 3:
        print(f"FAIL: core freq axis {len(freq['core'])} != 3 points")
        return 1
    fresult = compare(freq["core"], freq, tol)
    if fresult is not None:
        print(f"FAIL freq round-trip: {fresult[2]}")
        return 1
    print("FREQ ROUND-TRIP PASS: core==python==node bit-exact, wasm within tol")

    # Touchstone cross-compare: each end parses the same shared samples and
    # dumps the S master data (interleaved f64) + z0 + version. Native ends
    # must match core bit-exact, wasm within tol; version is a string
    # compared verbatim.
    ts_s = {}
    for sample in SAMPLES:
        name = sanitize(sample)
        s = {end: load_f64s(root / end / name / "s.bin") for end in ENDS}
        if len(s["core"]) != len(s["python"]):
            print(f"FAIL ts {sample}: core len {len(s['core'])} != python len")
            return 1
        sresult = compare(s["core"], s, tol)
        if sresult is not None:
            print(f"FAIL ts {sample} s: {sresult[2]}")
            return 1
        z0 = {end: load_f64s(root / end / name / "z0.bin") for end in ENDS}
        zresult = compare(z0["core"], z0, tol)
        if zresult is not None:
            print(f"FAIL ts {sample} z0: {zresult[2]}")
            return 1
        vers = {
            end: (root / end / name / "version.txt").read_text(encoding="utf-8").strip()
            for end in ENDS
        }
        if len(set(vers.values())) != 1:
            print(f"FAIL ts {sample} version: {vers}")
            return 1
        ts_s[sample] = s
    print("TOUCHSTONE PASS: core==python==node bit-exact, wasm within tol")

    # Anti-tautology self-check: perturb an in-memory copy of each
    # non-reference end's Touchstone S data at a RANDOM sample and RANDOM
    # index and require detection AT THE INJECTED END AND INDEX (proves each
    # dumped file participates, the comparator is not blind, scans beyond
    # element 0, and localizes mismatches correctly — detecting them
    # elsewhere would mean the perturbation was not what tripped it). core
    # is never a target: tampering the reference is indistinguishable from
    # tampering any native end.
    for end in ("python", "node", "wasm"):
        sample = random.choice(SAMPLES)
        ref = ts_s[sample]["core"]
        idx = random.randrange(len(ref))
        tampered = {k: list(v) for k, v in ts_s[sample].items()}
        # Scale the perturbation to the element's magnitude so it exceeds
        # the RELATIVE tolerance at any index (a fixed tol*2 would hide
        # under the threshold for elements with |value| > 2).
        v = tampered[end][idx]
        tampered[end][idx] = v + (abs(v) if v != 0 else 1.0) * tol * 2
        result = compare(ref, tampered, tol)
        if result is None:
            print(f"SELF-CHECK FAIL: tamper={end} {sample} not detected (tautology!)")
            return 1
        if result[0] != end or result[1] != idx:
            print(
                f"SELF-CHECK FAIL: tamper={end} {sample} idx {idx}, but "
                f"comparator localized it to {result[0]} idx {result[1]}"
            )
            return 1
        print(
            f"SELF-CHECK PASS: tamper={end} {sample} idx {idx} "
            "detected at the injected end and index"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
