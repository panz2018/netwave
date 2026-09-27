//! netwave core (scaffold phase 0).
//!
//! # Interleaved complex layout (constitution rule 1)
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
//! [`fill_pattern`] is a phase-0 scaffold: its only purpose is to give
//! the three bindings real memory to pass around and a predictable
//! pattern to assert against. It is replaced by the real data model
//! (Network/SParameter) in phase 2 and is not part of the long-term
//! contract.

use num_complex::Complex64;

/// Allocate an `(nfreq, nports, nports)` interleaved complex f64 buffer
/// and fill it with a predictable pattern.
///
/// Pattern: `re = f*100 + p*10 + q`, `im = -re`. Every element is unique
/// and sign-checkable (`re>0`, `im<0`), so any misalignment, copy, or
/// byte-order error breaks the pattern. Expected values MUST be computed
/// independently by the caller (test) using the same closed-form formula —
/// never reuse this function's output as ground truth (constitution rule 2:
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
