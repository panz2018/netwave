# netwave core

The Rust core crate (`netwave`): the single source of truth for all
scattering-parameter math. The Python, Node (napi) and WASM bindings are
deliberately thin transports over this crate — they must never recompute values
(governance spec rule: bindings only move memory; see
[`openspec/specs/project-governance/spec.md`](../openspec/specs/project-governance/spec.md)).

Current stage: scaffold. The only public verb is `fill_pattern`, a
predictable-pattern allocator whose sole purpose is to give the bindings real
memory to pass around zero-copy. It is replaced by the real Network/SParameter
data model later.

## Layout

- `src/lib.rs` — public API + the interleaved complex layout contract
- `tests/` — integration tests (the API has no unit tests besides these; TDD
  applies to every future verb)
- `scripts/dump.rs` — cross-binding dump: writes `.cross-tmp/core.bin`
  (declared as `[[example]]` in `Cargo.toml`; cargo only auto-discovers
  `examples/`)
- `benches/scaffold.rs` — criterion benchmarks feeding the bench gate

## Commands

Run from this directory (or add `-p netwave` from the repo root).

```bash
cargo build                 # debug build
cargo fmt --check           # format check only (what CI runs)
cargo fmt                   # auto-fix formatting
cargo clippy -- -D warnings # lint, warnings are errors
cargo clippy --fix --allow-dirty  # auto-fix lint suggestions (review the diff!)
cargo test                  # all tests
cargo bench                 # criterion benchmarks
cargo llvm-cov -p netwave --fail-under-lines 100  # crate-scoped coverage gate
```

Cross-binding dump (core side of the four-way comparison) — run from the **repo
root**, so the output lands in the shared `.cross-tmp/` that all four dumps
write to (a relative path here would create `core/.cross-tmp/` and the
comparison would not find it):

```bash
cargo run -q -p netwave --example dump .cross-tmp
```
