"""cross-binding dump (python side): emit the λ↔f axis and the Touchstone
S master data per sample to <out>/python_freq.bin and
<out>/python_ts_<case>.bin — raw little-endian f64 bytes, re/im interleaved.

Binary rather than JSON: JSON writes -0 as 0 and loses the sign bit.
Usage (from repo root): uv run --project python python python/scripts/dump.py <out_dir>
"""

import sys
from pathlib import Path

import netwave


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: dump_py.py <out_dir>", file=sys.stderr)
        return 2
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    # λ↔f round-trip axis: f -> wavelength -> f.
    # The unit is the enum member, never a hand-copied string literal
    # (vocabulary single source).
    f = netwave.Frequency.from_f([1.0, 2.0, 5.0], netwave.FrequencyUnit.GHz)
    wl = f.wavelength(netwave.WavelengthUnit.mm, 2.2)
    back = netwave.Frequency.from_wavelength(wl, netwave.WavelengthUnit.mm, 2.2)
    fpath = out / "python_freq.bin"
    fpath.write_bytes(back.f.tobytes())
    # Touchstone cross-compare: parse each shared sample and dump the S
    # master data (interleaved f64), z0, and version.
    for case in ("s1p", "s2p", "s4p"):
        ts = netwave.Touchstone.from_file(f"testdata/touchstone/dut.{case}")
        (out / f"python_ts_{case}.bin").write_bytes(ts.s.tobytes())
        (out / f"python_ts_{case}_z0.bin").write_bytes(ts.z0.tobytes())
        (out / f"python_ts_{case}_version.txt").write_text(ts.version)
    print(f"dumped {fpath.resolve()} {(out / 'python_ts_s2p.bin').resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
