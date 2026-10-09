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
use wasm_bindgen::prelude::*;

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
    /// A unit string did not match any [`WavelengthUnit`] spelling.
    UnknownWavelengthUnit(String),
}

impl std::fmt::Display for Error {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Error::UnknownFrequencyUnit(input) => {
                write!(f, "unknown frequency unit: {input:?}")
            }
            Error::UnknownWavelengthUnit(input) => {
                write!(f, "unknown wavelength unit: {input:?}")
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

impl FromStr for WavelengthUnit {
    type Err = Error;

    /// Parse a wavelength unit name case-insensitively (`"MM"`/`"mm"` both
    /// yield [`WavelengthUnit::mm`]). Hand-written over strum's `EnumString`
    /// for the same reason as [`FrequencyUnit::from_str`]: the error must
    /// carry the offending input, and the loop over `iter()` keeps the
    /// vocabulary in the enum definition only.
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        WavelengthUnit::iter()
            .find(|u| u.as_ref().eq_ignore_ascii_case(s))
            .ok_or_else(|| Error::UnknownWavelengthUnit(s.to_owned()))
    }
}

/// A wavelength unit: SI prefix + metre.
///
/// Mirrors [`FrequencyUnit`] exactly (same reflection shape, same helper
/// set). The variant name IS the canonical spelling; this enum is the only
/// place a wavelength unit name appears. Scoped to the wavelength API and
/// deliberately NOT named `LengthUnit` — in RF contexts "length" means
/// transmission-line length, a different quantity.
#[allow(non_camel_case_types)]
#[cfg_attr(
    feature = "pyo3-stub-gen",
    gen_stub_pyclass_enum(module = "netwave._netwave")
)]
#[cfg_attr(all(feature = "python", not(coverage)), pyclass(skip_from_py_object))]
#[cfg_attr(all(feature = "node", not(feature = "browser"), not(coverage)), napi)]
#[cfg_attr(
    all(feature = "browser", not(feature = "node"), not(coverage)),
    wasm_bindgen
)]
#[derive(Debug, Clone, Copy, PartialEq, Eq, AsRefStr, EnumIter)]
pub enum WavelengthUnit {
    /// Metre, 10^0 — the canonical SI unit of wavelength.
    m,
    /// Centimetre, 10^-2.
    cm,
    /// Millimetre, 10^-3.
    mm,
    /// Micrometre, 10^-6.
    um,
    /// Nanometre, 10^-9.
    nm,
}

impl WavelengthUnit {
    /// Multiply a value expressed in this unit to obtain metres.
    ///
    /// The multiplier of an SI prefix is exactly 10^−n by definition (centi
    /// 10^-2 … nano 10^-9); the decimal literals here are the nearest f64
    /// and every comparison in the suite uses the same literal, so the
    /// contract is bit-exact (ironclad rule 3). Internal helper: NOT
    /// exposed to py/ts — bindings see names via reflection only.
    ///
    /// The `match` is exhaustive on purpose: adding a variant without a
    /// multiplier fails to compile.
    pub const fn multiplier(self) -> f64 {
        match self {
            WavelengthUnit::m => 1e0,
            WavelengthUnit::cm => 1e-2,
            WavelengthUnit::mm => 1e-3,
            WavelengthUnit::um => 1e-6,
            WavelengthUnit::nm => 1e-9,
        }
    }

    /// Reconstruct a unit from its definition-order ordinal (0 = m, 1 = cm,
    /// …). Same role as [`FrequencyUnit::from_ordinal`] at the JS boundary.
    /// Internal helper: deliberately not exposed to py/ts.
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
#[cfg_attr(all(feature = "node", not(feature = "browser"), not(coverage)), napi)]
// Browser: NOT wasm_bindgen-exported. The browser reaches it through the
// `"frequency"` namespace (`call_namespace`), so the wasm export surface
// stays the single generic `call` plus the `FrequencyUnit` constant — the
// shell never computes the list itself (ironclad rule 11).
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
#[cfg_attr(
    feature = "pyo3-stub-gen",
    gen_stub_pyfunction(module = "netwave._netwave")
)]
#[cfg_attr(all(feature = "python", not(coverage)), pyfunction)]
#[cfg_attr(all(feature = "node", not(feature = "browser"), not(coverage)), napi)]
// Browser: NOT wasm_bindgen-exported — reached through the `"frequency"`
// namespace so the wasm export surface stays `call` + `FrequencyUnit`.
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
    /// Set once [`Frequency::drop`] has run, so the later RAII `Drop`
    /// does not double-decrement [`LIVE`].
    dropped: bool,
}

impl Frequency {
    /// Build a sweep from frequency points expressed in `unit`.
    ///
    /// The input values are in `unit`; they are multiplied by
    /// [`FrequencyUnit::multiplier`] and stored as f64 hertz (governance
    /// rule 1: the master axis is always Hz). `unit` is kept as display
    /// metadata (read by [`Frequency::f_scaled`]). Takes ownership of the
    /// vector; bumps [`LIVE`] (witness only).
    ///
    /// This is the ONLY frequency constructor (scikit-rf shape: one
    /// constructor whose `unit` describes the input). Points already in
    /// hertz pass `FrequencyUnit::Hz` — its multiplier is exactly 1e0, so
    /// the axis is stored bit-verbatim (the browser `copy` factory relies
    /// on this). Changing the display unit afterwards is [`Frequency::
    /// set_unit`], which never touches the master axis.
    pub fn from_f(f_in_unit: Vec<f64>, unit: FrequencyUnit) -> Self {
        let m = unit.multiplier();
        LIVE.fetch_add(1, std::sync::atomic::Ordering::SeqCst);
        Self {
            f_hz: f_in_unit.into_iter().map(|v| v * m).collect(),
            unit,
            dropped: false,
        }
    }

    /// Build a sweep from wavelength points expressed in `wl_unit`, through
    /// a medium of phase index `n`.
    ///
    /// `f = SPEED_OF_LIGHT / (n × λ)`, with λ first converted to metres via
    /// [`WavelengthUnit::multiplier`]. `n` (phase index, n = c/v_p =
    /// √ε_eff) is required by the API contract — defaulting to n=1 on a
    /// medium is physically wrong, and a silent wrong beats a loud error.
    /// The result is stored as f64 hertz (governance rule 1).
    pub fn from_wavelength(wl_in_unit: Vec<f64>, wl_unit: WavelengthUnit, n: f64) -> Self {
        let m = wl_unit.multiplier();
        let f_hz = wl_in_unit
            .into_iter()
            .map(|wl| crate::constants::SPEED_OF_LIGHT / (n * (wl * m)))
            .collect();
        LIVE.fetch_add(1, std::sync::atomic::Ordering::SeqCst);
        Self {
            f_hz,
            unit: FrequencyUnit::Hz,
            dropped: false,
        }
    }

    /// Number of frequency points. Errors after `drop()` — the post-drop
    /// access contract lives here in core, single-source, so no binding
    /// re-implements the check (node once returned 0 because the check
    /// existed only in the JS layer).
    pub fn npoints(&self) -> Result<usize, crate::Dropped> {
        if self.dropped {
            return Err(crate::Dropped);
        }
        Ok(self.f_hz.len())
    }

    /// The frequency axis in hertz, as a fresh `Vec<f64>` COPY.
    ///
    /// Copy, not a borrowed view: scikit-rf's `f` is a pure getter with no
    /// setter (the axis is read-only, there is no write-back), so a copy is
    /// the honest shape and keeps [`Frequency::drop`] able to free the
    /// master data immediately (no live view can dangle). Mutating the
    /// returned vector never touches core. Errors after `drop()`.
    pub fn f(&self) -> Result<Vec<f64>, crate::Dropped> {
        if self.dropped {
            return Err(crate::Dropped);
        }
        Ok(self.f_hz.clone())
    }

    /// The frequency axis in the current display unit: `f / multiplier`.
    ///
    /// Derived on every call — never stored (api-contract: derived values
    /// are not master data). Errors after `drop()`.
    pub fn f_scaled(&self) -> Result<Vec<f64>, crate::Dropped> {
        if self.dropped {
            return Err(crate::Dropped);
        }
        let m = self.unit.multiplier();
        Ok(self.f_hz.iter().map(|v| v / m).collect())
    }

    /// Angular frequency ω = 2πf (rad/s), derived on every call.
    ///
    /// Errors after `drop()`.
    pub fn w(&self) -> Result<Vec<f64>, crate::Dropped> {
        if self.dropped {
            return Err(crate::Dropped);
        }
        let tau = std::f64::consts::TAU;
        Ok(self.f_hz.iter().map(|v| tau * v).collect())
    }

    /// The display unit (getter returns the enum, not a string — ironclad
    /// rule 10 deviation, filed in design.md: the gain is IDE vocabulary
    /// checking + zero hand-copied name lists). Errors after `drop()`.
    pub fn unit(&self) -> Result<FrequencyUnit, crate::Dropped> {
        if self.dropped {
            return Err(crate::Dropped);
        }
        Ok(self.unit)
    }

    /// Set the display unit. Only the metadata changes — the f64 Hz master
    /// axis is untouched (governance rule 1).
    pub fn set_unit(&mut self, unit: FrequencyUnit) {
        self.unit = unit;
    }

    /// Wavelength λ = SPEED_OF_LIGHT / (n × f), expressed in `wl_unit`.
    ///
    /// `n` is the phase index (n = c/v_p = √ε_eff), required by the API
    /// contract. A DC point (f = 0) yields `inf` (skrf/numpy semantics: DC
    /// is a legal frequency, its wavelength is infinite), never NaN.
    /// Errors after `drop()`.
    pub fn wavelength(&self, wl_unit: WavelengthUnit, n: f64) -> Result<Vec<f64>, crate::Dropped> {
        if self.dropped {
            return Err(crate::Dropped);
        }
        let m = wl_unit.multiplier();
        Ok(self
            .f_hz
            .iter()
            .map(|f| crate::constants::SPEED_OF_LIGHT / (n * f) / m)
            .collect())
    }

    /// An independent copy with the same axis and unit. Errors after
    /// `drop()` (a dropped axis must not be cloned back to life).
    ///
    /// The copy is a live instance in its own right, so it bumps [`LIVE`]
    /// exactly like [`Frequency::from_f`] — otherwise its RAII `Drop` would
    /// decrement a count that was never incremented (witness corruption).
    pub fn copy(&self) -> Result<Self, crate::Dropped> {
        if self.dropped {
            return Err(crate::Dropped);
        }
        LIVE.fetch_add(1, std::sync::atomic::Ordering::SeqCst);
        Ok(Self {
            f_hz: self.f_hz.clone(),
            unit: self.unit,
            dropped: false,
        })
    }

    /// Drop the sweep and decrement the witness exactly once. Idempotent: a
    /// later RAII `Drop` (or a second call) is a no-op for the witness.
    ///
    /// This inherent method is the single cleanup implementation: the manual
    /// `drop()` escape hatch and RAII [`Drop`] both call it, so the witness
    /// never double-decrements. Inherent methods resolve before trait
    /// methods, so `self.drop()` inside `Drop::drop` lands here (no
    /// recursion).
    // The cross-end naming contract (ironclad rule 12) mandates this exact
    // name on every platform; clippy's trait-suggestion cannot be honored
    // without renaming the unified verb.
    #[allow(clippy::should_implement_trait)]
    pub fn drop(&mut self) {
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
        self.drop();
    }
}

/// Format an f64 the way Python's `str()` does for the display string:
/// integral values keep one decimal (`1.0`, not `1`), so the cross-end
/// display string matches scikit-rf character for character.
fn fmt_axis_value(v: f64) -> String {
    if v.is_finite() && v.fract() == 0.0 {
        format!("{v:.1}")
    } else {
        format!("{v}")
    }
}

/// The cross-end uniform display string: `Frequency(start-stop unit,
/// N pts)` (start/stop in the current display unit), or
/// `Frequency([no freqs])` for an empty axis. Single source (design.md
/// D6): every binding's protocol hook delegates here (ironclad rule 9).
impl std::fmt::Display for Frequency {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        if self.f_hz.is_empty() {
            return write!(f, "Frequency([no freqs])");
        }
        let m = self.unit.multiplier();
        let start = fmt_axis_value(self.f_hz[0] / m);
        let stop = fmt_axis_value(self.f_hz[self.f_hz.len() - 1] / m);
        write!(
            f,
            "Frequency({start}-{stop} {}, {} pts)",
            self.unit.as_ref(),
            self.f_hz.len()
        )
    }
}

/// `Debug` emits the same string as `Display` (design.md D6: one display
/// string, no second format to keep in sync).
impl std::fmt::Debug for Frequency {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        std::fmt::Display::fmt(self, f)
    }
}

// ---------------------------------------------------------------------------
// Browser dispatch (cfg=browser): the worker forwards `{handle, method,
// args}` to the single generic `resources::call`; this module owns the
// name→function `match`es (Rust has no reflection — the arm list IS the
// method table). Adding a method = one arm here; `resources.rs`, the
// worker, the shells and `types.ts` never change.
// ---------------------------------------------------------------------------

/// Instance dispatch: the numeric-handle half of the shell's `Frequency`.
/// `drop` never reaches here — the dispatcher intercepts it.
// Read a unit argument that is either a numeric enum ordinal or a string
// (case-insensitive, core FromStr quotes the offending input). Inlined here
// (not in resources.rs) so the generic dispatcher stays unit-agnostic.
#[cfg(all(feature = "browser", not(feature = "node"), not(coverage)))]
fn js_freq_unit(v: &JsValue) -> Result<FrequencyUnit, JsValue> {
    use std::str::FromStr;
    if let Some(s) = v.as_string() {
        return FrequencyUnit::from_str(&s).map_err(|e| crate::resources::js(e.to_string()));
    }
    let n = v
        .as_f64()
        .ok_or_else(|| crate::resources::js("unit must be a number or a string"))?
        as u8;
    FrequencyUnit::from_ordinal(n).ok_or_else(|| crate::resources::js("invalid unit ordinal"))
}

#[cfg(all(feature = "browser", not(feature = "node"), not(coverage)))]
fn js_wl_unit(v: &JsValue) -> Result<WavelengthUnit, JsValue> {
    use std::str::FromStr;
    if let Some(s) = v.as_string() {
        return WavelengthUnit::from_str(&s).map_err(|e| crate::resources::js(e.to_string()));
    }
    let n = v
        .as_f64()
        .ok_or_else(|| crate::resources::js("unit must be a number or a string"))?
        as u8;
    WavelengthUnit::from_ordinal(n).ok_or_else(|| crate::resources::js("invalid unit ordinal"))
}

/// Wrap an owned f64 axis as a `Float64Array` for the worker reply. The
/// worker's `postMessage` structured-clones it (a copy across the realm
/// boundary — matching the `f` copy semantics; the wasm buffer is not
/// transferred, so the high-water mark is the live-object peak, see docs).
#[cfg(all(feature = "browser", not(feature = "node"), not(coverage)))]
fn f64_array(v: &[f64]) -> JsValue {
    js_sys::Float64Array::from(v).into()
}

#[cfg(all(feature = "browser", not(feature = "node"), not(coverage)))]
impl crate::resources::Resource for Frequency {
    fn call(&mut self, method: &str, args: &[JsValue]) -> Result<JsValue, JsValue> {
        use crate::resources::{js, unknown_method};
        match method {
            // Post-drop access errors here — core is the single source of
            // the contract (no binding re-implements the check).
            "npoints" => self
                .npoints()
                .map(|n| JsValue::from_f64(n as u32 as f64))
                .map_err(|e| js(e.to_string())),
            "f" => self
                .f()
                .map(|v| f64_array(&v))
                .map_err(|e| js(e.to_string())),
            "fScaled" => self
                .f_scaled()
                .map(|v| f64_array(&v))
                .map_err(|e| js(e.to_string())),
            "w" => self
                .w()
                .map(|v| f64_array(&v))
                .map_err(|e| js(e.to_string())),
            "unit" => self
                .unit()
                .map(|u| JsValue::from_f64(u as u32 as f64))
                .map_err(|e| js(e.to_string())),
            "setUnit" => {
                let u = args
                    .first()
                    .map(js_freq_unit)
                    .ok_or_else(|| js("unit argument required"))??;
                self.set_unit(u);
                Ok(JsValue::NULL)
            }
            "wavelength" => {
                let wu = args
                    .first()
                    .map(js_wl_unit)
                    .ok_or_else(|| js("wl_unit argument required"))??;
                let n = args
                    .get(1)
                    .and_then(|v| v.as_f64())
                    .ok_or_else(|| js("n must be a number"))?;
                self.wavelength(wu, n)
                    .map(|v| f64_array(&v))
                    .map_err(|e| js(e.to_string()))
            }
            // `copy` is NOT dispatched here: it must allocate a NEW handle
            // via `insert`, which re-locks the registry that instance
            // dispatch already holds (std Mutex is not reentrant -> panic).
            // `copy` is a factory, so it rides the namespace channel below.
            "toString" => Ok(JsValue::from_str(&self.to_string())),
            _ => Err(unknown_method("frequency", method)),
        }
    }
}

/// Namespace dispatch: the `"frequency"` namespace's factory and free
/// functions. `live_count` lives here because it counts `Frequency`
/// instances (the witness is defined in this module) — no separate
/// diagnostic namespace.
#[cfg(all(feature = "browser", not(feature = "node"), not(coverage)))]
pub fn call_namespace(method: &str, args: &[JsValue]) -> Result<JsValue, JsValue> {
    use crate::resources::{arg_f64_vec, arg_u32, insert, instance_call, js, unknown_method};
    match method {
        // `unit` is a plain ordinal: the glue enum is numeric and the
        // feature-merge build must not put the enum in an FFI signature.
        "fromF" => {
            let view = arg_f64_vec(args, 0)?;
            let unit = args
                .get(1)
                .map(js_freq_unit)
                .ok_or_else(|| js("unit argument required"))??;
            let f = Frequency::from_f(view, unit);
            Ok(JsValue::from_f64(insert(Box::new(f)) as f64))
        }
        "fromWavelength" => {
            let view = arg_f64_vec(args, 0)?;
            let wl_unit = args
                .get(1)
                .map(js_wl_unit)
                .ok_or_else(|| js("wl_unit argument required"))??;
            let n = args
                .get(2)
                .and_then(|v| v.as_f64())
                .ok_or_else(|| js("n must be a number"))?;
            let f = Frequency::from_wavelength(view, wl_unit, n);
            Ok(JsValue::from_f64(insert(Box::new(f)) as f64))
        }
        // `copy` is a factory (it allocates a new handle), so it lives on
        // the namespace channel: the axis + unit are read back through
        // `instance_call` (each briefly locks and releases the registry),
        // then re-hosted verbatim — never re-locked while held (the
        // instance-dispatch path would deadlock here).
        "copy" => {
            let handle = arg_u32(args, 0)?;
            let axis = instance_call(handle, "f", &[]).map_err(js)?;
            let unit = instance_call(handle, "unit", &[]).map_err(js)?;
            let arr = axis
                .dyn_ref::<js_sys::Float64Array>()
                .ok_or_else(|| js("expected Float64Array"))?;
            let u = FrequencyUnit::from_ordinal(
                unit.as_f64().ok_or_else(|| js("unit must be a number"))? as u8,
            )
            .ok_or_else(|| js("invalid unit ordinal"))?;
            // The axis read back is Hz, so `from_f` with unit Hz stores it
            // bit-verbatim (multiplier 1e0); the display unit is then set
            // as metadata only.
            let mut f = Frequency::from_f(arr.to_vec(), FrequencyUnit::Hz);
            f.set_unit(u);
            Ok(JsValue::from_f64(insert(Box::new(f)) as f64))
        }
        "frequencyUnits" => {
            let units = frequency_units();
            let arr = js_sys::Array::new();
            for u in units {
                arr.push(&JsValue::from_str(&u));
            }
            Ok(arr.into())
        }
        "liveCount" => Ok(JsValue::from_f64(live_count() as f64)),
        _ => Err(unknown_method("frequency", method)),
    }
}

/// Mount the `"frequency"` namespace. Called once from the
/// `#[wasm_bindgen(start)]` hook in `lib.rs`.
#[cfg(all(feature = "browser", not(feature = "node"), not(coverage)))]
pub fn register() {
    crate::resources::register_namespace("frequency", call_namespace);
}
