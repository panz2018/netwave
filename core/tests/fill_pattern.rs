//! fill_pattern roundtrip test (RED first: core/src/lib.rs has no
//! implementation yet → compile failure is red).
//!
//! Expected values are computed independently by a closed-form formula in
//! the test (constitution rule 2: never derive expectations from core's
//! output). Layout contract (rule 1): (nfreq, nports, nports) interleaved
//! complex f64, re before im.

use netwave::fill_pattern;

const NFREQ: usize = 2;
const NPORTS: usize = 2;

#[test]
fn length_and_layout() {
    let buf = fill_pattern(NFREQ, NPORTS);
    // 2×2×2 = 8 complex numbers; 16 bytes each → 128 bytes
    assert_eq!(buf.len(), NFREQ * NPORTS * NPORTS);
    assert_eq!(
        std::mem::size_of_val(buf.as_slice()),
        128,
        "total buffer bytes"
    );
    // per frequency point: 4 complexes × 16 bytes = 64 contiguous bytes
    assert_eq!(std::mem::size_of::<num_complex::Complex<f64>>(), 16);
}

#[test]
fn pattern_closed_form() {
    let buf = fill_pattern(NFREQ, NPORTS);
    for f in 0..NFREQ {
        for p in 0..NPORTS {
            for q in 0..NPORTS {
                let c = buf[f * NPORTS * NPORTS + p * NPORTS + q];
                let re = (f * 100 + p * 10 + q) as f64;
                assert_eq!(c.re, re, "re(f={f},p={p},q={q})");
                assert_eq!(c.im, -re, "im(f={f},p={p},q={q})");
            }
        }
    }
}
