//! Vocabulary tests for `FrequencyUnit` (spec: frequency-unit,
//! "frequency unit vocabulary single source").
//!
//! Expected values are independent literals (spec contract), never derived
//! from the code under test (ironclad rule 2: no tautology).

use netwave::frequency::{FrequencyUnit, IntoEnumIterator, frequency_units};

#[test]
fn iter_yields_exactly_the_five_units_in_order() {
    let names: Vec<FrequencyUnit> = FrequencyUnit::iter().collect();
    assert_eq!(
        names,
        vec![
            FrequencyUnit::Hz,
            FrequencyUnit::kHz,
            FrequencyUnit::MHz,
            FrequencyUnit::GHz,
            FrequencyUnit::THz,
        ]
    );
}

#[test]
fn as_ref_is_the_canonical_spelling() {
    assert_eq!(FrequencyUnit::Hz.as_ref(), "Hz");
    assert_eq!(FrequencyUnit::kHz.as_ref(), "kHz");
    assert_eq!(FrequencyUnit::MHz.as_ref(), "MHz");
    assert_eq!(FrequencyUnit::GHz.as_ref(), "GHz");
    assert_eq!(FrequencyUnit::THz.as_ref(), "THz");
}

#[test]
fn frequency_units_passthrough_matches_iter() {
    assert_eq!(frequency_units(), vec!["Hz", "kHz", "MHz", "GHz", "THz"]);
}

#[test]
fn parse_is_case_insensitive() {
    // Touchstone option lines use uppercase ("# GHZ"), users type lowercase;
    // both must map to the one canonical variant.
    assert_eq!("ghz".parse::<FrequencyUnit>().unwrap(), FrequencyUnit::GHz);
    assert_eq!("GHZ".parse::<FrequencyUnit>().unwrap(), FrequencyUnit::GHz);
    assert_eq!("GHz".parse::<FrequencyUnit>().unwrap(), FrequencyUnit::GHz);
}

#[test]
fn parse_error_carries_the_offending_input() {
    let err = "Hzz".parse::<FrequencyUnit>().unwrap_err();
    let msg = err.to_string();
    assert!(msg.contains("Hzz"), "error must quote input, got: {msg}");
}

#[test]
fn multipliers_are_exact_powers_of_ten() {
    // Exact constants (SI prefixes 10^3n, bit-representable in f64):
    // compared with ==, never a tolerance (LL-042 — core_tol governs
    // computed results across platforms, not exact constants).
    assert_eq!(FrequencyUnit::Hz.multiplier(), 1e0);
    assert_eq!(FrequencyUnit::kHz.multiplier(), 1e3);
    assert_eq!(FrequencyUnit::MHz.multiplier(), 1e6);
    assert_eq!(FrequencyUnit::GHz.multiplier(), 1e9);
    assert_eq!(FrequencyUnit::THz.multiplier(), 1e12);
}
