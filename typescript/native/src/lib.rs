//! netwave Node binding (napi-rs).
//!
//! Zero-copy: core allocates a `Vec<Complex64>`; the bytes' ownership is
//! moved into a V8 external `Buffer` via `Buffer::from(Vec<u8>)` (no copy;
//! freed at GC finalize). The JS shell takes `buf.buffer` for the
//! underlying ArrayBuffer. `read_element` passes a Float64Array view back
//! into Rust and reads by pointer, proving it is the same memory.

use std::str::FromStr;

use napi::bindgen_prelude::*;
use napi_derive::napi;
use netwave::fill_pattern as core_fill_pattern;
use netwave::frequency::{Frequency as CoreFrequency, FrequencyUnit, WavelengthUnit};
use netwave::network::Network as CoreNetwork;

/// Resolve a `FrequencyUnit` from a numeric enum member OR a string (the
/// union lives here in the binding, ironclad rule 11). The numeric arm is
/// the JS enum value (ordinal); the string arm goes through core `FromStr`
/// (case-insensitive, error quotes the input).
fn resolve_freq_unit(u: Either<u8, String>) -> Result<FrequencyUnit> {
    match u {
        Either::A(n) => FrequencyUnit::from_ordinal(n)
            .ok_or_else(|| Error::from_reason("invalid frequency unit ordinal")),
        Either::B(s) => FrequencyUnit::from_str(&s).map_err(|e| Error::from_reason(e.to_string())),
    }
}

/// Resolve a `WavelengthUnit` (same shape as [`resolve_freq_unit`]).
fn resolve_wl_unit(u: Either<u8, String>) -> Result<WavelengthUnit> {
    match u {
        Either::A(n) => WavelengthUnit::from_ordinal(n)
            .ok_or_else(|| Error::from_reason("invalid wavelength unit ordinal")),
        Either::B(s) => WavelengthUnit::from_str(&s).map_err(|e| Error::from_reason(e.to_string())),
    }
}

/// Allocate an interleaved complex f64 buffer, moving byte ownership
/// zero-copy into a JS external Buffer.
///
/// Returns a Buffer (Uint8Array view); the JS shell extracts `.buffer`
/// and converts the length.
#[napi]
pub fn fill_pattern(nfreq: u32, nports: u32) -> Buffer {
    let v = core_fill_pattern(nfreq as usize, nports as usize);
    let len = v.len(); // number of complex numbers
    let ptr = v.as_ptr() as *mut u8;
    let cap = v.capacity() * 16; // byte capacity (Complex64 = 2×f64, 16B/elem)
    std::mem::forget(v); // ownership moved to the Vec<u8> below, no double free
    let bytes: Vec<u8> = unsafe { Vec::from_raw_parts(ptr, len * 16, cap) };
    Buffer::from(bytes) // Buffer::from calls mem::forget internally; GC frees
}

/// Pass a Float64Array view back into Rust and read an element by pointer
/// (same memory, zero copy).
#[napi]
pub fn read_element(view: Float64Array, idx: u32) -> Result<f64> {
    Ok(view.as_ref()[idx as usize])
}

/// Speed of light in vacuum (m/s): the core constant re-exported by name
/// (ironclad rules 11/12 — the value is defined once in `core::constants`,
/// the binding carries the name mechanically, no hand-copied literal).
#[napi]
pub const SPEED_OF_LIGHT: f64 = netwave::constants::SPEED_OF_LIGHT;

/// napi binding for the core `Network`: the constructor is the data entry
/// (no `upload` — that verb is browser-only, it names the worker linear-
/// memory boundary which does not exist here). `readElement` reads one
/// interleaved f64 element; `drop` is the deterministic manual reclamation
/// (idempotent; post-drop access throws). napi's cleanup finalizer runs the
/// Rust `Drop` on GC as the fallback. The wrapper has no `impl Drop`, so the
/// method name `drop` shadows nothing on the Rust side.
#[napi(js_name = "Network")]
pub struct Network(CoreNetwork);

#[napi]
impl Network {
    /// Wrap an owned interleaved `[re, im, ...]` f64 buffer with explicit
    /// shape (`len == nfreq*nports*nports*2`). Shape is validated here and
    /// surfaced as a JS `throw` (core's `from_f64` asserts, which would
    /// abort across the FFI boundary).
    #[napi(constructor)]
    pub fn new(data: Float64Array, nfreq: u32, nports: u32) -> Result<Self> {
        let want = nfreq as usize * nports as usize * nports as usize * 2;
        if data.len() != want {
            return Err(Error::from_reason(format!(
                "data length must be nfreq*nports*nports*2 ({want}), got {}",
                data.len()
            )));
        }
        Ok(Network(CoreNetwork::from_f64(
            nfreq as usize,
            nports as usize,
            data.as_ref().to_vec(),
        )))
    }

    /// Pattern-filled factory (same closed-form pattern as the scaffold free
    /// function, so existing assertions transfer).
    #[napi(factory)]
    pub fn fill_pattern(nfreq: u32, nports: u32) -> Self {
        Network(CoreNetwork::fill_pattern(nfreq as usize, nports as usize))
    }

    /// Read one interleaved f64 element by flat index. Throws after `drop`.
    #[napi]
    pub fn read_element(&self, idx: u32) -> Result<f64> {
        self.0
            .read_element(idx as usize)
            .map_err(|e| Error::from_reason(e.to_string()))
    }

    /// Deterministic manual reclamation (the unified cross-end verb,
    /// ironclad rule 12). Idempotent; post-drop access throws.
    // clippy's trait-suggestion cannot be honored without renaming the
    // unified verb; the wrapper has no `impl Drop`, so nothing is shadowed.
    #[allow(clippy::should_implement_trait)]
    #[napi]
    pub fn drop(&mut self) {
        self.0.drop();
    }
}

/// napi binding for the core `Frequency`. napi's cleanup finalizer runs the
/// Rust `Drop` on GC, and `drop` is the deterministic early-release escape
/// hatch (idempotent via the core guard). The wrapper has no `impl Drop`, so
/// the method name `drop` shadows nothing on the Rust side.
#[napi(js_name = "Frequency")]
pub struct Frequency(CoreFrequency);

#[napi]
impl Frequency {
    /// Build a sweep from points in `unit` (enum member | string, required)
    /// stored as f64 hertz. `unit` crosses as `number | string`: the numeric
    /// arm is the JS enum ordinal, the string arm is core `FromStr` — the
    /// core enum never enters an FFI signature (the `node`+`browser`
    /// feature-merge build would drop its napi attribute).
    #[napi(factory)]
    pub fn from_f(f: Vec<f64>, unit: Either<u8, String>) -> Result<Self> {
        let unit = resolve_freq_unit(unit)?;
        Ok(Frequency(CoreFrequency::from_f(f, unit)))
    }

    /// Build a sweep from wavelength points in `wl_unit` (enum | string)
    /// through a medium of phase index `n` (required): `f = c / (n × λ)`.
    #[napi(factory)]
    pub fn from_wavelength(wl: Vec<f64>, wl_unit: Either<u8, String>, n: f64) -> Result<Self> {
        let wl_unit = resolve_wl_unit(wl_unit)?;
        Ok(Frequency(CoreFrequency::from_wavelength(wl, wl_unit, n)))
    }

    /// The frequency axis in hertz — a fresh COPY (read-only contract).
    #[napi(getter, js_name = "f")]
    pub fn get_f(&self) -> Result<Vec<f64>> {
        self.0.f().map_err(|e| Error::from_reason(e.to_string()))
    }

    /// The axis in the current display unit (`f / multiplier`), derived.
    #[napi(getter, js_name = "fScaled")]
    pub fn get_f_scaled(&self) -> Result<Vec<f64>> {
        self.0
            .f_scaled()
            .map_err(|e| Error::from_reason(e.to_string()))
    }

    /// Angular frequency ω = 2πf (rad/s), derived.
    #[napi(getter, js_name = "w")]
    pub fn get_w(&self) -> Result<Vec<f64>> {
        self.0.w().map_err(|e| Error::from_reason(e.to_string()))
    }

    /// The display unit as its numeric enum ordinal (the JS enum is numeric;
    /// `f.unit === FrequencyUnit.GHz` holds). Errors after `drop`.
    #[napi(getter, js_name = "unit")]
    pub fn get_unit(&self) -> Result<u8> {
        self.0
            .unit()
            .map(|u| u as u8)
            .map_err(|e| Error::from_reason(e.to_string()))
    }

    /// Set the display unit (enum member | string, case-insensitive; illegal
    /// string throws quoting the input). Only metadata changes.
    #[napi(setter, js_name = "unit")]
    pub fn set_unit(&mut self, unit: Either<u8, String>) -> Result<()> {
        let unit = resolve_freq_unit(unit)?;
        self.0.set_unit(unit);
        Ok(())
    }

    /// Wavelength λ = c / (n × f) in `wl_unit` (enum | string); DC → inf.
    #[napi]
    pub fn wavelength(&self, wl_unit: Either<u8, String>, n: f64) -> Result<Vec<f64>> {
        let wl_unit = resolve_wl_unit(wl_unit)?;
        self.0
            .wavelength(wl_unit, n)
            .map_err(|e| Error::from_reason(e.to_string()))
    }

    /// An independent copy with the same axis and unit.
    #[napi]
    pub fn copy(&self) -> Result<Self> {
        self.0
            .copy()
            .map(Frequency)
            .map_err(|e| Error::from_reason(e.to_string()))
    }

    /// The cross-end uniform display string (core `Display`, single source).
    #[napi(js_name = "toString")]
    pub fn display(&self) -> String {
        self.0.to_string()
    }

    /// Number of frequency points. Throws after `drop` (the post-drop
    /// contract is core's, passed through unchanged). `u32` not `usize`:
    /// napi maps `usize` to JS bigint, breaking cross-end type parity
    /// (wasm/Python expose a plain number; ironclad rule 9).
    #[napi]
    pub fn npoints(&self) -> Result<u32> {
        self.0
            .npoints()
            .map(|n| n as u32)
            .map_err(|e| Error::from_reason(e.to_string()))
    }

    /// Deterministic early release (no GC needed). The unified cross-end
    /// verb (ironclad rule 12): identical name and semantics on every
    /// platform, no `free` alias.
    // clippy's trait-suggestion cannot be honored without renaming the
    // unified verb; the wrapper has no `impl Drop`, so nothing is shadowed.
    #[allow(clippy::should_implement_trait)]
    #[napi]
    pub fn drop(&mut self) {
        self.0.drop();
    }
}
