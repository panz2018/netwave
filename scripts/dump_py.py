"""cross-binding dump (python side): emit the (2,2) roundtrip values to
<out>/python.bin — raw little-endian f64 bytes, re/im interleaved.

Binary rather than JSON: JSON writes -0 as 0 and loses the sign bit.
Usage: uv run python scripts/dump_py.py <out_dir>
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
    arr = netwave.fill_pattern(2, 2)
    path = out / "python.bin"
    path.write_bytes(arr.tobytes())
    print(f"dumped {path.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
