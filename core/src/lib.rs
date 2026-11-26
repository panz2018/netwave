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

pub mod constants;
pub mod frequency;
pub mod touchstone;

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
