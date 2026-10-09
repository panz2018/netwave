//! Constants contract: `SPEED_OF_LIGHT` is an exact SI-defined value.
//!
//! Expected value is an independent literal (the SI defined exact speed of
//! light in vacuum, 299 792 458 m/s — CODATA/SI brochure, exact by
//! definition since 1983). Compared with `==`, never a tolerance: manifest
//! tolerances govern computed cross-platform results, not exact constants
//! (ironclad rule 3).

#[test]
fn speed_of_light_is_the_si_exact_value() {
    assert_eq!(netwave::constants::SPEED_OF_LIGHT, 299_792_458.0);
}
