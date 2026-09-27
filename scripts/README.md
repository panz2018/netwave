# netwave scripts

Workspace-level tools only: cross-binding comparison (consumes the four
per-end dumps), CI gates, and toolchain helpers. Not part of any published
package. A dump that serves a single subproject lives in that subproject's
`scripts/` (`core/scripts/dump.rs`, `python/scripts/dump.py`,
`typescript/scripts/dump.mjs`); this directory keeps only the cross-cutting
orchestration.

## Scripts

| Script                 | Purpose                                                                                                                   | Usage (from repo root)                                       |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------ |
| `cross_compare.py`     | compares the four dumps per the zero-copy-roundtrip spec                                                                  | `python3 scripts/cross_compare.py .cross-tmp`                |
| `bench_gate.py`        | criterion regression gate: fails on >20% mean regression                                                                  | `python3 scripts/bench_gate.py target/criterion [threshold]` |
| `install_binaryen.sh`  | installs `wasm-opt` from GitHub **latest** (never pinned; local + CI share it)                                            | `bash scripts/install_binaryen.sh`                           |
| `install_wasm_pack.sh` | installs `wasm-pack` from GitHub **latest** official prebuilt tarballs (linux/macOS/windows; faster than `cargo install`) | `bash scripts/install_wasm_pack.sh`                          |
| `check_md.py`          | markdown checker: links/anchors + cross-line code-span detection                                                          | `python3 scripts/check_md.py`                                |

## Notes

- **One-command pipeline**: `pnpm check:cross` (repo root) runs all four
  per-end dumps into `.cross-tmp/` then `cross_compare.py`. Requires the
  native/wasm artifacts to be freshly built first: run `build:native` and
  `build:wasm` in `typescript/`, and `maturin develop` in `python/`.
  contract as everywhere else (constitution rule 1). Binary, not JSON: JSON
  writes `-0` as `0` and loses the sign bit. Per-end dumps live in their
  subprojects: `cargo run -p netwave --example dump .cross-tmp`,
  `uv run --project python python python/scripts/dump.py .cross-tmp`,
  `node typescript/scripts/dump.mjs .cross-tmp` (node + wasm in one run).
- **`cross_compare.py` self-checks itself**: after a passing comparison it
  perturbs an in-memory copy of each non-reference end (python/node/wasm) and
  requires the comparator to detect every perturbation (anti-tautology;
  `.bin` files on disk are never modified. Comparison tiers (native bit-exact,
  wasm relative tolerance) are defined in
  [`../Plan/测试规划.md`](../Plan/测试规划.md).
- **`bench_gate.py` threshold** defaults to 0.20 (20%), from the ci-matrix spec;
  pass a second argument to override.
- **`install_binaryen.sh` deliberately does not pin a version** — wasm-pack's
  built-in download is stuck on binaryen 117 (worse optimization, bigger
  output); PATH-override with latest is required (AGENTS.md dependency policy).
- All dumps print the **resolved absolute path** of each file written, so a
  wrong cwd is visible immediately (`.cross-tmp/` must be shared by all four
  ends).
