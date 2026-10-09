//! Functional surface of `Frequency`.
//!
//! Expected values are independent literals / closed-form, never derived
//! from the code under test (ironclad rule 2). Same-machine native
//! comparisons are bit-exact (`==`); the manifest `core_tol` governs
//! cross-platform (wasm) comparisons only (ironclad rule 3).

use netwave::frequency::{Frequency, FrequencyUnit, WavelengthUnit};

#[test]
fn from_f_multiplies_by_unit_into_hz() {
    // from_f takes values IN `unit` and stores Hz (governance rule 1).
    let f = Frequency::from_f(vec![1.0, 2.0, 5.0], FrequencyUnit::GHz);
    assert_eq!(f.f().unwrap(), vec![1e9, 2e9, 5e9]);
    let hz = Frequency::from_f(vec![2.5], FrequencyUnit::Hz);
    assert_eq!(hz.f().unwrap(), vec![2.5]);
}

#[test]
fn f_returns_a_copy_isolated_from_core() {
    let f = Frequency::from_f(vec![1.0, 2.0, 5.0], FrequencyUnit::GHz);
    let mut a = f.f().unwrap();
    a[0] = 0.0;
    // Mutating the returned copy must not touch core (f is read-only).
    assert_eq!(f.f().unwrap()[0], 1e9);
}

#[test]
fn f_scaled_divides_hz_by_multiplier() {
    let f = Frequency::from_f(vec![1.0, 2.0, 5.0], FrequencyUnit::GHz);
    assert_eq!(f.f_scaled().unwrap(), vec![1.0, 2.0, 5.0]);
}

#[test]
fn w_is_two_pi_f() {
    let f = Frequency::from_f(vec![1.0, 2.0], FrequencyUnit::Hz);
    let tau = std::f64::consts::TAU;
    assert_eq!(f.w().unwrap(), vec![tau, 2.0 * tau]);
}

#[test]
fn display_string_is_cross_end_uniform() {
    let f = Frequency::from_f(vec![1.0, 2.0, 5.0], FrequencyUnit::GHz);
    assert_eq!(f.to_string(), "Frequency(1.0-5.0 GHz, 3 pts)");
    assert_eq!(format!("{:?}", f), "Frequency(1.0-5.0 GHz, 3 pts)");
    let empty = Frequency::from_f(vec![], FrequencyUnit::Hz);
    assert_eq!(empty.to_string(), "Frequency([no freqs])");
}

#[test]
fn from_wavelength_computes_hz_from_meters() {
    // f = c / (n * lambda); lambda 60 mm, n 2.2.
    let f = Frequency::from_wavelength(vec![60.0], WavelengthUnit::mm, 2.2);
    let want = 299_792_458.0 / (2.2 * 0.060);
    assert_eq!(f.f().unwrap(), vec![want]);
}

#[test]
fn wavelength_round_trips_to_hz() {
    // λ↔f is a computed round-trip, so it is governed by the manifest
    // core_tol (relative), never bit-exact (ironclad rule 3).
    let core_tol = 1e-12;
    let f = Frequency::from_f(vec![1e9, 2e9, 5e9], FrequencyUnit::Hz);
    let wl = f.wavelength(WavelengthUnit::mm, 2.2).unwrap();
    let back = Frequency::from_wavelength(wl, WavelengthUnit::mm, 2.2);
    for (got, want) in back.f().unwrap().iter().zip([1e9, 2e9, 5e9]) {
        assert!(
            (got - want).abs() <= core_tol * want,
            "round-trip {got} vs {want}"
        );
    }
}

#[test]
fn wavelength_dc_is_inf_not_nan() {
    let f = Frequency::from_f(vec![0.0, 1e9], FrequencyUnit::Hz);
    let wl = f.wavelength(WavelengthUnit::m, 1.0).unwrap();
    assert!(wl[0].is_infinite() && !wl[0].is_nan());
}

#[test]
fn unit_getter_returns_enum_and_setter_swaps_metadata() {
    let mut f = Frequency::from_f(vec![1.0], FrequencyUnit::GHz);
    assert_eq!(f.unit().unwrap(), FrequencyUnit::GHz);
    assert_eq!(f.f_scaled().unwrap(), vec![1.0]);
    f.set_unit(FrequencyUnit::MHz);
    // unit changed, f master data untouched (still 1e9 Hz).
    assert_eq!(f.f().unwrap(), vec![1e9]);
    assert_eq!(f.f_scaled().unwrap(), vec![1e3]);
}

#[test]
fn copy_is_independent_and_equal() {
    let f = Frequency::from_f(vec![1.0, 2.0], FrequencyUnit::GHz);
    let c = f.copy().unwrap();
    assert_eq!(c.f().unwrap(), f.f().unwrap());
    assert_eq!(c.unit().unwrap(), FrequencyUnit::GHz);
}

#[test]
fn accessors_error_after_drop() {
    let mut f = Frequency::from_f(vec![1.0], FrequencyUnit::GHz);
    f.drop();
    assert!(f.f().is_err());
    assert!(f.f_scaled().is_err());
    assert!(f.w().is_err());
    assert!(f.unit().is_err());
    assert!(f.copy().is_err());
    assert!(f.wavelength(WavelengthUnit::m, 1.0).is_err());
}

#[test]
fn display_formats_non_integral_values() {
    // fmt_axis_value's non-integral branch: no forced `.0` padding.
    let f = Frequency::from_f(vec![1.5, 2.25], FrequencyUnit::GHz);
    assert_eq!(f.to_string(), "Frequency(1.5-2.25 GHz, 2 pts)");
}

#[test]
fn dropped_error_display_is_stable() {
    // The shared access-after-drop message is part of the cross-end error
    // text surfaced by every binding (single source of truth).
    assert_eq!(netwave::Dropped.to_string(), "data has been dropped");
}
