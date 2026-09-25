# netwave testdata

Shared test data for all four bindings (core/python/node/wasm): the
tolerance manifest and golden files. Committed to git so the main CI has
zero Python dependency — golden values are generated offline, consumed at
test time.

## Files

- `manifest.json` — the single tolerance + case contract (constitution
  rule: tolerances live only here)
- `LICENSE-NOTES.md` — provenance and licenses of borrowed samples
- `golden/` — skrf-generated expected outputs (added in phase 1;
  phase 0 has the manifest only)

## manifest.json contract

- `schema_version`: manifest schema version (phase 0 is a skeleton, `0`).
- `core_tol`: default tolerances for the unit/property layers inside the
  Rust core (`relative: 1e-12`, placeholder until phase 1) plus
  `python_relative: 0.0` — bit-exact, because the python roundtrip views
  the same memory with no arithmetic.
- `cases[]`: per-case `input` / `op` / `golden` / `shape` / `tol_abs` /
  `tol_rel` — added in phase 1 with the golden files. wasm cases will
  declare `tol_rel` only (absolute tolerances false-positive on large
  values).
- Binary format contract: every `.bin` is raw little-endian f64 pairs
  `[re, im, re, im, ...]`, byte-identical to numpy `complex128` / C
  `double _Complex` (constitution rule 1).

## Who generates, who consumes

| Role | Path | Notes |
|---|---|---|
| generate | `gen_golden.py` (phase 1, offline, uv) | only place Python + skrf runs |
| consume | `core/tests/golden.rs` | `std::fs::read` → `&[f64]` |
| consume | `python/tests/` | `np.fromfile(dtype='<c16')` |
| consume | `typescript/` vitest | `new Float64Array(buf)` |

Comparison rule and cross-binding tiers (native bit-exact, wasm
relative) are defined in
[`../Plan/测试规划.md`](../Plan/测试规划.md) — this README only points
there, never restates.

## Gotchas

- **Never hand-edit `golden/*.bin`** — regenerate with `gen_golden.py`
  and review the diff.
- **Never hardcode tolerances in tests** — read them from
  `manifest.json` (constitution rule 3).
