//! Frequency unit vocabulary: the single source of truth for unit names
//! and their multipliers (spec: frequency-unit).

use std::str::FromStr;

use strum::{AsRefStr, EnumIter};

// With the `python` feature the enum/function below carry pyo3 attributes so
// the binding crate registers them by reflection (zero hand-copied names).
// `not(coverage)` drops the pyo3 registration glue (pytest covers the Python
// surface); the python glue crate gates its add_class/wrap_pyfunction calls
// the same way so the coverage build still compiles.
#[cfg(all(feature = "python", not(coverage)))]
use pyo3::prelude::*;

// With `pyo3-stub-gen` the same items also carry stub annotations so the
// .pyi generator discovers them (the annotations ride the pyclass/pyfunction
// items, so this feature implies `python`).
#[cfg(feature = "pyo3-stub-gen")]
use pyo3_stub_gen::derive::{gen_stub_pyclass_enum, gen_stub_pyfunction};

// With the `node` feature the same items carry napi attributes; the enum
// becomes a numeric JS enum (design: numeric across the worker boundary).
// `not(browser)` avoids the clippy --workspace macro collision (LL-044);
// `not(coverage)` drops the JS-registration glue (pytest/vitest cover it).
#[cfg(all(feature = "node", not(feature = "browser"), not(coverage)))]
use napi_derive::napi;

// With the `browser` feature the same items carry wasm-bindgen attributes;
// the enum becomes a numeric JS constant object in the glue (importing a
// constant does not instantiate wasm — ironclad rule 8 holds).
#[cfg(all(feature = "browser", not(feature = "node"), not(coverage)))]
use wasm_bindgen::prelude::wasm_bindgen;

/// Re-exported so callers can invoke [`FrequencyUnit::iter`] without adding
/// a direct `strum` dependency (the trait must be in scope for method call
/// syntax).
pub use strum::IntoEnumIterator;

/// Core parse/conversion errors.
///
/// The offending input is carried verbatim so every binding surface can
/// quote it (spec: frequency-unit "unknown unit error contract").
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Error {
    /// A unit string did not match any [`FrequencyUnit`] spelling.
    UnknownFrequencyUnit(String),
}

impl std::fmt::Display for Error {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Error::UnknownFrequencyUnit(input) => {
                write!(f, "unknown frequency unit: {input:?}")
            }
        }
    }
}

impl std::error::Error for Error {}

impl FromStr for FrequencyUnit {
    type Err = Error;

    /// Parse a unit name case-insensitively (`"ghz"`/`"GHZ"`/`"GHz"` all
    /// yield [`FrequencyUnit::GHz`]; Touchstone option lines use uppercase,
    /// user code often lowercase).
    ///
    /// Hand-written instead of strum's `EnumString`: the generated
    /// `ParseError` does not carry the offending input, which the error
    /// contract requires. Matching loops over `iter()` + `as_ref()`, so
    /// the vocabulary stays in the enum definition only.
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        FrequencyUnit::iter()
            .find(|u| u.as_ref().eq_ignore_ascii_case(s))
            .ok_or_else(|| Error::UnknownFrequencyUnit(s.to_owned()))
    }
}

/// A frequency unit: SI prefix + hertz.
///
/// The variant name IS the canonical spelling (`kHz` = kilo + hertz,
/// multiplier 10^3). This enum is the only place any unit name appears in
/// the repository; bindings expose it by reflection, never by copying a
/// name list (spec: frequency-unit "vocabulary single source").
/// Multipliers are exact powers of ten (10^3n), representable bit-exactly
/// in f64 — see [`FrequencyUnit::multiplier`].
// `kHz` is the correct SI spelling (lowercase prefix k); the Rust naming
// convention cannot apply to unit symbols.
#[allow(non_camel_case_types)]
// `skip_from_py_object`: a unit is passed by its enum member, never coerced
// from an arbitrary Python object (that would bypass FromStr validation).
#[cfg_attr(
    feature = "pyo3-stub-gen",
    gen_stub_pyclass_enum(module = "netwave._netwave")
)]
#[cfg_attr(all(feature = "python", not(coverage)), pyclass(skip_from_py_object))]
// `not(coverage)` drops the runtime-only registration glue (pytest/vitest
// cover the binding surface); `not(browser)`/`not(node)` avoid the clippy
// --workspace macro collision (LL-044). A real glue build enables exactly
// one of node/browser, so the enum is exported there either way.
#[cfg_attr(all(feature = "node", not(feature = "browser"), not(coverage)), napi)]
#[cfg_attr(
    all(feature = "browser", not(feature = "node"), not(coverage)),
    wasm_bindgen
)]
#[derive(Debug, Clone, Copy, PartialEq, Eq, AsRefStr, EnumIter)]
pub enum FrequencyUnit {
    /// Hertz, 10^0 — the canonical storage unit of the frequency axis.
    Hz,
    /// Kilohertz, 10^3.
    kHz,
    /// Megahertz, 10^6.
    MHz,
    /// Gigahertz, 10^9.
    GHz,
    /// Terahertz, 10^12.
    THz,
}

impl FrequencyUnit {
    /// Multiply a value expressed in this unit to obtain hertz.
    ///
    /// The multiplier of an SI prefix is exactly 10^3n (kilo 10^3, mega
    /// 10^6, giga 10^9, tera 10^12); every value here is a power of ten
    /// exactly representable in f64, so conversions are bit-exact and no
    /// tolerance applies (LL-042). Consumed internally by
    /// `Frequency.f_scaled` (stage 1); deliberately NOT exposed to py/ts —
    /// bindings see names via reflection and never numeric tables.
    ///
    /// The `match` is exhaustive on purpose: adding an enum variant without
    /// a multiplier here fails to compile, so a name can never ship without
    /// its value.
    pub const fn multiplier(self) -> f64 {
        match self {
            FrequencyUnit::Hz => 1e0,
            FrequencyUnit::kHz => 1e3,
            FrequencyUnit::MHz => 1e6,
            FrequencyUnit::GHz => 1e9,
            FrequencyUnit::THz => 1e12,
        }
    }
}

/// List every unit in canonical spelling, definition order.
///
/// One-line passthrough of [`FrequencyUnit::iter`] mapped through `as_ref` —
/// contains zero vocabulary of its own, so it can never drift from the enum.
/// This is the only self-discovery channel for bindings to enumerate units.
/// (`String` rather than `&'static str`: strum's generated `as_ref` borrows
/// `&self`, so owned strings are the cheapest honest signature.)
#[cfg_attr(
    feature = "pyo3-stub-gen",
    gen_stub_pyfunction(module = "netwave._netwave")
)]
#[cfg_attr(all(feature = "python", not(coverage)), pyfunction)]
// `not(coverage)` drops the runtime-only registration glue (pytest/vitest
// cover it). napi and wasm_bindgen cannot both decorate one function (napi's
// macro rejects an item that also carries `#[wasm_bindgen]`), so `node` and
// `browser` are mutually exclusive (LL-044); a real glue build enables
// exactly one, so the function is still JS-exported there.
#[cfg_attr(all(feature = "node", not(feature = "browser"), not(coverage)), napi)]
#[cfg_attr(
    all(feature = "browser", not(feature = "node"), not(coverage)),
    wasm_bindgen
)]
pub fn frequency_units() -> Vec<String> {
    FrequencyUnit::iter()
        .map(|u| u.as_ref().to_owned())
        .collect()
}
