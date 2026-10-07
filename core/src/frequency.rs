//! Frequency unit vocabulary: the single source of truth for unit names
//! and their multipliers.

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
// becomes a numeric JS enum (units cross the worker boundary as numbers).
// `not(browser)` avoids the clippy --workspace macro collision between the
// napi and wasm-bindgen derive macros; `not(coverage)` drops the
// JS-registration glue (pytest/vitest cover the binding surface).
#[cfg(all(feature = "node", not(feature = "browser"), not(coverage)))]
use napi_derive::napi;

// With the `browser` feature the same items carry wasm-bindgen attributes;
// the enum becomes a numeric JS constant object in the glue, so importing a
// unit name never instantiates the wasm module.
#[cfg(all(feature = "browser", not(feature = "node"), not(coverage)))]
use wasm_bindgen::prelude::wasm_bindgen;

/// Re-exported so callers can invoke [`FrequencyUnit::iter`] without adding
/// a direct `strum` dependency (the trait must be in scope for method call
/// syntax).
pub use strum::IntoEnumIterator;

/// Core parse/conversion errors.
///
/// The offending input is carried verbatim so every binding surface can
/// quote it in its raised error message.
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
/// name list.
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
// --workspace macro collision between the napi and wasm-bindgen derive
// macros. A real glue build enables exactly one of node/browser, so the
// enum is exported there either way.
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
    /// tolerance is ever needed. Internal helper: deliberately NOT exposed
    /// to py/ts — bindings see names via reflection and never numeric tables.
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

    /// Reconstruct a unit from its definition-order ordinal (0 = Hz, 1 = kHz,
    /// …). The JS boundary carries units as plain numbers (the glue enum is
    /// numeric), so glue converts back here — keeping the ordinal↔variant
    /// mapping in one place instead of duplicating the variant list per
    /// binding. Internal helper: deliberately not exposed to py/ts.
    pub fn from_ordinal(ordinal: u8) -> Option<Self> {
        Self::iter().nth(ordinal as usize)
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
// `browser` are mutually exclusive; a real glue build enables exactly one,
// so the function is still JS-exported there.
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

// Live `Frequency` count — a test witness, not memory management. The real
// reclamation is `Drop` (RAII); this counter only proves `Drop` actually ran
// (a Map entry vanishing does not prove the Rust destructor fired). Always
// compiled: `Frequency` is a large object (a whole sweep's `Vec<f64>`) built
// and dropped once, so one atomic increment/decrement is negligible next to
// that allocation.
// u32 (not usize): napi maps usize to JS bigint but wasm maps it to number;
// u32 is exact in f64 so both bindings expose a plain number (cross-end
// type parity, ironclad rule 9).
static LIVE: std::sync::atomic::AtomicU32 = std::sync::atomic::AtomicU32::new(0);

/// How many [`Frequency`] instances are currently alive. Test-only witness:
/// the memory-lifecycle suite polls this to confirm Rust `Drop` ran.
///
/// Read-only diagnostic probe: holds no data, no side effects. Always
/// compiled (see [`LIVE`]).
#[cfg_attr(all(feature = "node", not(feature = "browser"), not(coverage)), napi)]
#[cfg_attr(
    all(feature = "browser", not(feature = "node"), not(coverage)),
    wasm_bindgen
)]
pub fn live_count() -> u32 {
    LIVE.load(std::sync::atomic::Ordering::SeqCst)
}

/// A frequency sweep: the in-memory data model's frequency axis.
///
/// The core owns the sweep's `Vec<f64>` and reclaims it through `Drop`
/// (RAII). The class is deliberately NOT exported from the package entry
/// yet: the functional surface (`f`/`f_scaled`/`w`/`wavelength`/`Display`)
/// is not complete, and a half-public class would violate ironclad rules
/// 9/10.
///
/// # Memory contract
///
/// - Construction ([`Frequency::from_f`]) owns a `Vec<f64>` (Hz storage) and
///   bumps [`LIVE`].
/// - [`Drop`] is the ONLY reclamation path (RAII): when the last owner drops
///   the value, the `Vec` frees and [`LIVE`] decrements. There is zero manual
///   memory-management code.
/// - In wasm, `Drop` returns bytes to the allocator's free list; the linear
///   memory high-water mark does NOT shrink. That is why reclamation is
///   observed through [`live_count`], not by watching memory size.
// The Rust type is plain (no binding attributes): the wasm/napi class
// wrappers live in the glue crates, where each binding's macro decorates the
// impl its own way (wasm_bindgen marks the impl block, napi marks each
// method — they cannot share one cfg_attr'd impl). "Internalized" means the
// TS shell does not re-export the class, not that it is uncompiled.
pub struct Frequency {
    /// Frequency points in hertz (canonical storage unit, governance rule 1).
    f_hz: Vec<f64>,
    /// Display unit carried alongside the data. Read by the functional
    /// accessors (`f_scaled`/`set_unit`), not yet by the memory surface,
    /// hence the allow.
    #[allow(dead_code)]
    unit: FrequencyUnit,
    /// Set once [`Frequency::release`] has run, so the later RAII `Drop`
    /// does not double-decrement [`LIVE`].
    dropped: bool,
}

impl Frequency {
    /// Build a sweep from frequency points already in hertz.
    ///
    /// Takes ownership of `f_hz`; bumps [`LIVE`] (witness only).
    pub fn from_f(f_hz: Vec<f64>, unit: FrequencyUnit) -> Self {
        LIVE.fetch_add(1, std::sync::atomic::Ordering::SeqCst);
        Self {
            f_hz,
            unit,
            dropped: false,
        }
    }

    /// Number of frequency points.
    pub fn npoints(&self) -> usize {
        self.f_hz.len()
    }

    /// Free the sweep and decrement the witness exactly once. Idempotent: a
    /// later RAII `Drop` (or a second call) is a no-op for the witness.
    ///
    /// The glue `free` escape hatch calls this for deterministic early
    /// release; RAII `Drop` calls it too, so the witness never
    /// double-decrements.
    pub fn release(&mut self) {
        if !self.dropped {
            self.f_hz = Vec::new();
            LIVE.fetch_sub(1, std::sync::atomic::Ordering::SeqCst);
            self.dropped = true;
        }
    }
}

impl Drop for Frequency {
    /// RAII reclamation: frees the `Vec` and decrements the witness counter.
    /// This is the single reclamation path — no manual free exists.
    fn drop(&mut self) {
        self.release();
    }
}
