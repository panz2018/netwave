//! netwave core.
//!
//! # Interleaved complex layout (governance spec rule 1)
//!
//! Network data in memory is a sequence of `(nfreq, nports, nports)`
//! complex matrices. Each complex number is stored as complex128,
//! interleaved: `[re, im, re, im, ...]` with `re` first.
//! `num_complex::Complex<f64>` is a `#[repr(C)]` two-field struct,
//! byte-identical to numpy `complex128` and C `double _Complex` —
//! this is the layout foundation that lets all four bindings share
//! the same memory with zero copies.
//!
//! # Temporary API notice
//!
//! [`fill_pattern`] is scaffold-only: its purpose is to give the three
//! bindings real memory to pass around and a predictable pattern to assert
//! against. It is not part of the long-term contract (the real data model
//! — Network/SParameter — replaces it).

use num_complex::Complex64;

pub mod frequency;
pub mod network;
// Same guard as the wasm entries below: under `cargo clippy --workspace`
// the node and browser features merge onto one build, and the handle table
// must not compile its wasm_bindgen glue there.
#[cfg(all(feature = "browser", not(feature = "node"), not(coverage)))]
pub mod resources;

/// wasm instantiation hook: mount every resource namespace into the handle
/// table once, before any worker message arrives. Adding a new resource TYPE
/// = one line here (plus the new module's own `match`es); adding a METHOD to
/// an existing resource touches only that module — never this hook, never the
/// worker, never the shells (api-contract spec "worker generic dispatch and
/// single-resident topology", LL-052).
#[cfg(all(feature = "browser", not(feature = "node"), not(coverage)))]
#[wasm_bindgen::prelude::wasm_bindgen(start)]
fn register_resources() {
    network::register();
    frequency::register();
}

/// Access-after-drop error, shared by every resource type. Post-drop access
/// erroring IS the contract on every platform — no separate `is_dropped`
/// witness exists anywhere (single source of truth).
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Dropped;

impl std::fmt::Display for Dropped {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "data has been dropped")
    }
}

impl std::error::Error for Dropped {}

/// Allocate an `(nfreq, nports, nports)` interleaved complex f64 buffer
/// and fill it with a predictable pattern.
///
/// Pattern: `re = f*100 + p*10 + q`, `im = -re`. Every element is unique
/// and sign-checkable (`re>0`, `im<0`), so any misalignment, copy, or
/// byte-order error breaks the pattern. Expected values MUST be computed
/// independently by the caller (test) using the same closed-form formula —
/// never reuse this function's output as ground truth (governance spec rule 2:
/// avoid tautology).
pub fn fill_pattern(nfreq: usize, nports: usize) -> Vec<Complex64> {
    (0..nfreq)
        .flat_map(|f| (0..nports).flat_map(move |p| (0..nports).map(move |q| (f, p, q))))
        .map(|(f, p, q)| {
            let re = (f * 100 + p * 10 + q) as f64;
            Complex64::new(re, -re)
        })
        .collect()
}
