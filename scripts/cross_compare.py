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
  - fake-golden self-check (--tamper=<end>): a tampered end MUST be
    detected (anti-tautology)

Usage: python3 scripts/cross_compare.py <dir> [--tamper=<end>]
"""

import json
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


def verdict(tamper, msg: str) -> int:
    """Normal mode: a mismatch fails. Tamper mode: detecting the injected
    mismatch (printing the failure) means the self-check passes."""
    print(msg)
    return 0 if tamper else 1


def main() -> int:
    tamper = next(
        (a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--tamper=")),
        None,
    )
    args = [a for a in sys.argv[1:] if not a.startswith("--tamper=")]
    if not args:
        print(__doc__, file=sys.stderr)
        return 2
    root = Path(args[0])
    # encoding="utf-8": manifest carries CJK notes; Windows cp1252 default fails
    manifest = root.parent / "testdata/manifest.json"
    tol = json.loads(manifest.read_text(encoding="utf-8"))["core_tol"]["relative"]

    ends = {name: load_f64s(root, name) for name in ENDS}
    if tamper:
        ends[tamper][0] += tol * 2  # fake-golden self-check: perturbation above tolerance

    ref = ends["core"]
    # Native ends: bit-exact.
    for name in ("python", "node"):
        for i, (a, b) in enumerate(zip(ref, ends[name], strict=True)):
            if bits(a) != bits(b):
                return verdict(tamper, f"FAIL bit-exact: core vs {name} idx {i}: {a!r} vs {b!r}")
    # wasm: relative tolerance.
    for i, (a, b) in enumerate(zip(ref, ends["wasm"], strict=True)):
        denom = abs(a) if a != 0 else 1.0
        if abs(a - b) / denom >= tol:
            return verdict(tamper, f"FAIL tol: core vs wasm idx {i}: {a!r} vs {b!r}")
    if tamper:
        # Unreachable when the perturbation works: the loops above must have
        # returned FAIL first. Reaching here means the comparator is blind
        # (tautology) — a hard failure, never a pass.
        print(f"SELF-CHECK FAIL: tamper={tamper} not detected (tautology!)")
        return 1
    print("cross-binding OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
