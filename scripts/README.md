# netwave scripts

Repo-level tools: cross-binding comparison, CI gates, and toolchain helpers. Not
part of any published package — if a script only serves one crate, it belongs in
that crate instead (see `core/examples/dump.rs`).

## Scripts

| Script                | Purpose                                                                            | Usage (from repo root)                                         |
| --------------------- | ---------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `dump_py.py`          | cross-binding dump, python end: writes `<out>/python.bin`                          | `uv run --project python python scripts/dump_py.py .cross-tmp` |
| `dump_js.mjs`         | cross-binding dump, node + wasm ends: writes `<out>/node.bin` and `<out>/wasm.bin` | `node scripts/dump_js.mjs .cross-tmp`                          |
| `cross_compare.py`    | compares the four dumps per the zero-copy-roundtrip spec                           | `python3 scripts/cross_compare.py .cross-tmp`                  |
| `bench_gate.py`       | criterion regression gate: fails on >20% mean regression                           | `python3 scripts/bench_gate.py target/criterion [threshold]`   |
| `install_binaryen.sh` | installs `wasm-opt` from GitHub **latest** (never pinned; local + CI share it)     | `bash scripts/install_binaryen.sh`                             |
| `check_md.py`         | markdown checker: links/anchors + cross-line code-span detection                   | `python3 scripts/check_md.py`                                  |

## Notes

- **Dump output is raw little-endian f64, re/im interleaved** — the same layout
  contract as everywhere else (constitution rule 1). Binary, not JSON: JSON
  writes `-0` as `0` and loses the sign bit.
- **`cross_compare.py --tamper=<end>`** injects a corruption into one end's dump
  and asserts the comparison _detects_ it (anti-tautology self-check). Normal
  mode: any mismatch fails. Comparison tiers (native bit-exact, wasm relative
  tolerance) are defined in [`../Plan/测试规划.md`](../Plan/测试规划.md).
- **`bench_gate.py` threshold** defaults to 0.20 (20%), from the ci-matrix spec;
  pass a second argument to override.
- **`install_binaryen.sh` deliberately does not pin a version** — wasm-pack's
  built-in download is stuck on binaryen 117 (worse optimization, bigger
  output); PATH-override with latest is required (AGENTS.md dependency policy).
- All dumps print the **resolved absolute path** of each file written, so a
  wrong cwd is visible immediately (`.cross-tmp/` must be shared by all four
  ends).
