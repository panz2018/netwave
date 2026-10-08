//! netwave wasm binding (wasm-bindgen).
//!
//! The glue crate is intentionally empty: every wasm entry lives in core
//! (`network.rs` / `frequency.rs` / `resources.rs`, cfg-gated browser) and
//! wasm-bindgen exports the whole crate graph into this binary. Handles are
//! plain `u32` crossing the boundary; no wasm class floats up to JS, so
//! wasm-bindgen's generated `free()` has no call site anywhere — the single
//! reclamation command is core `drop(handle)` → `remove` → Rust `Drop`.

// Force-link core: its `#[wasm_bindgen]` entries are the entire wasm
// surface, and an unreferenced crate is not linked into the cdylib. This
// single line is the glue crate's whole job.
extern crate netwave;
