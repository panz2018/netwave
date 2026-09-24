# netwave core

The Rust core crate (`netwave`): the single source of truth for all
scattering-parameter math. The Python, Node (napi) and WASM bindings are
deliberately thin transports over this crate — they must never recompute
values (constitution rule: bindings only move memory).

Current stage: phase-0 scaffold. The only public verb is `fill_pattern`,
a predictable-pattern allocator whose sole purpose is to give the bindings
real memory to pass around zero-copy. It is replaced by the real
Network/SParameter data model in phase 2.

## Layout

- `src/lib.rs` — public API + the interleaved complex layout contract
- `tests/` — integration tests (the API has no unit tests besides these;
  TDD applies to every future verb)
- `examples/dump.rs` — cross-binding dump: writes `.cross-tmp/core.bin`
- `benches/scaffold.rs` — criterion benchmarks feeding the bench gate

## Commands

Run from this directory (or add `-p netwave` from the repo root).

```bash
cargo build                 # debug build
cargo fmt                   # format
cargo clippy -- -D warnings # lint, warnings are errors
cargo test                  # all tests
cargo bench                 # criterion benchmarks
cargo llvm-cov -p netwave --fail-under-lines 100  # crate-scoped coverage gate
```

Cross-binding dump (core side of the four-way comparison):

```bash
cargo run -q -p netwave --example dump .cross-tmp
```

## Implementation notes

- **Interleaved complex layout** (constitution rule 1): network data is an
  `(nfreq, nports, nports)` sequence of `Complex<f64>`, stored as
  `[re, im, re, im, ...]`. `num_complex::Complex<f64>` is `#[repr(C)]`
  and byte-identical to numpy `complex128` / C `double _Complex` — this
  is what lets all four bindings share one buffer with zero copies.
- **`fill_pattern` pattern**: `re = f*100 + p*10 + q`, `im = -re`. Every
  element is unique and sign-checkable, so any misalignment, silent copy or
  byte-order error breaks the pattern.
- **No tautology** (constitution rule 2): tests must compute expected
  values independently with the same closed-form formula — never reuse
  `fill_pattern` output as ground truth.

## Gotchas

- **Rebuild all bindings after touching core.** Run `maturin develop`
  (python), `pnpm -C typescript build:native` and `build:wasm` before any
  cross-binding comparison, otherwise you compare against stale artifacts.
- **Dumps must be binary `.bin`** (little-endian f64): `JSON.stringify(-0)`
  emits `"0"` and loses the sign bit, making bit-exact comparison
  impossible.
- **`#[coverage(off)]` is nightly-only** — do not add it; the stable
  toolchain pinned in `rust-toolchain.toml` will not compile. There are
  currently no coverage exemptions in this crate.
- `publish = false`: the crate is not released standalone; its version
  moves with the workspace.
