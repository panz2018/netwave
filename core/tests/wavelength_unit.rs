//! Vocabulary tests for `WavelengthUnit`: the enum definition is the single
//! source of wavelength-unit spellings.
//!
//! Expected values are independent literals, never derived from the code
//! under test (ironclad rule 2: no tautology).

use netwave::frequency::{IntoEnumIterator, WavelengthUnit};

#[test]
fn iter_yields_exactly_the_five_units_in_order() {
    let names: Vec<WavelengthUnit> = WavelengthUnit::iter().collect();
    assert_eq!(
        names,
        vec![
            WavelengthUnit::m,
            WavelengthUnit::cm,
            WavelengthUnit::mm,
            WavelengthUnit::um,
            WavelengthUnit::nm,
        ]
    );
}

#[test]
fn as_ref_is_the_canonical_spelling() {
    assert_eq!(WavelengthUnit::m.as_ref(), "m");
    assert_eq!(WavelengthUnit::cm.as_ref(), "cm");
    assert_eq!(WavelengthUnit::mm.as_ref(), "mm");
    assert_eq!(WavelengthUnit::um.as_ref(), "um");
    assert_eq!(WavelengthUnit::nm.as_ref(), "nm");
}

#[test]
fn multipliers_are_exact_powers_of_ten() {
    // SI prefixes (centi 10^-2 … nano 10^-9): exact decimal literals,
    // compared with ==, never a tolerance (ironclad rule 3).
    assert_eq!(WavelengthUnit::m.multiplier(), 1e0);
    assert_eq!(WavelengthUnit::cm.multiplier(), 1e-2);
    assert_eq!(WavelengthUnit::mm.multiplier(), 1e-3);
    assert_eq!(WavelengthUnit::um.multiplier(), 1e-6);
    assert_eq!(WavelengthUnit::nm.multiplier(), 1e-9);
}

#[test]
fn parse_is_case_insensitive() {
    assert_eq!("MM".parse::<WavelengthUnit>().unwrap(), WavelengthUnit::mm);
    assert_eq!("Nm".parse::<WavelengthUnit>().unwrap(), WavelengthUnit::nm);
    assert_eq!("m".parse::<WavelengthUnit>().unwrap(), WavelengthUnit::m);
}

#[test]
fn parse_error_carries_the_offending_input() {
    let err = "furlong".parse::<WavelengthUnit>().unwrap_err();
    let msg = err.to_string();
    assert!(
        msg.contains("furlong"),
        "error must quote input, got: {msg}"
    );
}

#[test]
fn from_ordinal_round_trips_definition_order() {
    assert_eq!(WavelengthUnit::from_ordinal(0), Some(WavelengthUnit::m));
    assert_eq!(WavelengthUnit::from_ordinal(1), Some(WavelengthUnit::cm));
    assert_eq!(WavelengthUnit::from_ordinal(2), Some(WavelengthUnit::mm));
    assert_eq!(WavelengthUnit::from_ordinal(3), Some(WavelengthUnit::um));
    assert_eq!(WavelengthUnit::from_ordinal(4), Some(WavelengthUnit::nm));
    assert_eq!(WavelengthUnit::from_ordinal(5), None);
}
