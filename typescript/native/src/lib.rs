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
use netwave::touchstone::Touchstone as CoreTouchstone;

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

/// The `{ values: Float64Array, shape: number[] }` result of `data()` —
/// the flat addressing contract shared across ends
/// (`idx = ((f*n + r)*n + c)*2`).
#[napi(object)]
pub struct TouchstoneData {
    /// Flat interleaved values (re/im for RI, mag|db/deg for MA/DB).
    pub values: Float64Array,
    /// Always `(nfreq, n, n, 2)` — JS has no complex type, so the last
    /// axis is the re/im (or mag|db/deg) pair.
    pub shape: Vec<u32>,
}

/// Resolve a domain/format keyword from a string (core `FromStr` quotes the
/// offending token in the error).
fn resolve_ts_kw<T: FromStr>(s: &str) -> Result<T>
where
    T::Err: std::fmt::Display,
{
    T::from_str(s).map_err(|e| Error::from_reason(e.to_string()))
}

/// napi binding for the core `Touchstone`: construction IS parsing; the
/// factories `fromText`/`fromFile`/`fromUrl` and the pure-data constructor
/// return a validated object or throw quoting the offending input. I/O
/// verbs (`fromFile`/`writeFile`/`fromUrl`) are async (napi AsyncTask).
#[napi(js_name = "Touchstone")]
pub struct Touchstone(CoreTouchstone, bool);

impl Touchstone {
    /// Guard shared by every instance accessor: a dropped shell must not hand
    /// back stale data (memory-lifecycle spec — post-drop access throws). The
    /// live core object is returned while still held; already-cloned views the
    /// caller holds stay valid (the buffer is never cleared).
    fn core(&self) -> Result<&CoreTouchstone> {
        if self.1 {
            return Err(Error::from_reason("Touchstone is dropped"));
        }
        Ok(&self.0)
    }
}

#[napi]
impl Touchstone {
    /// Pure-data constructor: `frequency` is a `Frequency` instance; `data`
    /// flat interleaved re/im in domain `parameter`; `z0` scalar-or-per-
    /// port real; `parameter` (S/Z/Y/G/H) required — no silent S default.
    #[napi(constructor)]
    pub fn new(
        frequency: &Frequency,
        data: Vec<f64>,
        z0: Vec<f64>,
        parameter: String,
        name: Option<String>,
        comments: Option<String>,
    ) -> Result<Self> {
        let parameter = resolve_ts_kw(&parameter)?;
        CoreTouchstone::new(
            &frequency.0,
            &data,
            &z0,
            parameter,
            &name.unwrap_or_default(),
            &comments.unwrap_or_default(),
        )
        .map(|t| Touchstone(t, false))
        .map_err(|e| Error::from_reason(e.to_string()))
    }

    /// Parse Touchstone text. `nports` explicit, else inferred from the
    /// `path` filename grammar; `path`'s stem becomes `name`.
    #[napi(factory)]
    pub fn from_text(text: String, nports: Option<u32>, path: Option<String>) -> Result<Self> {
        CoreTouchstone::from_text(&text, nports.map(|n| n as usize), path.as_deref())
            .map(|t| Touchstone(t, false))
            .map_err(|e| Error::from_reason(e.to_string()))
    }

    /// Read and parse a file (async AsyncTask; std::fs off the main thread).
    #[napi(factory)]
    pub async fn from_file(path: String) -> Result<Self> {
        let text = std::fs::read_to_string(&path)
            .map_err(|e| Error::from_reason(format!("{path}: {e}")))?;
        let filename = CoreTouchstone::filename_from_path(&path);
        CoreTouchstone::from_text(&text, None, Some(&filename))
            .map(|t| Touchstone(t, false))
            .map_err(|e| Error::from_reason(e.to_string()))
    }

    /// Fetch over HTTP and parse (async; reqwest rustls backend in core).
    #[napi(factory)]
    pub async fn from_url(url: String) -> Result<Self> {
        CoreTouchstone::from_url(&url)
            .await
            .map(|t| Touchstone(t, false))
            .map_err(|e| Error::from_reason(e.to_string()))
    }

    /// The stored S master data, flat interleaved re/im. Throws after `drop`.
    #[napi(getter, js_name = "s")]
    pub fn get_s(&self) -> Result<Float64Array> {
        Ok(Float64Array::from(self.core()?.s().to_vec()))
    }

    /// Z domain, computed fresh (flat interleaved re/im).
    #[napi(getter, js_name = "z")]
    pub fn get_z(&self) -> Result<Float64Array> {
        Ok(Float64Array::from(self.core()?.z()))
    }

    /// Y domain, computed fresh.
    #[napi(getter, js_name = "y")]
    pub fn get_y(&self) -> Result<Float64Array> {
        Ok(Float64Array::from(self.core()?.y()))
    }

    /// G domain (2-port only), computed fresh.
    #[napi(getter, js_name = "g")]
    pub fn get_g(&self) -> Result<Float64Array> {
        self.core()?
            .g()
            .map(Float64Array::from)
            .map_err(|e| Error::from_reason(e.to_string()))
    }

    /// H domain (2-port only), computed fresh.
    #[napi(getter, js_name = "h")]
    pub fn get_h(&self) -> Result<Float64Array> {
        self.core()?
            .h()
            .map(Float64Array::from)
            .map_err(|e| Error::from_reason(e.to_string()))
    }

    /// The frequency axis in hertz — a fresh COPY (read-only contract).
    #[napi(getter, js_name = "f")]
    pub fn get_f(&self) -> Result<Vec<f64>> {
        Ok(self.core()?.f())
    }

    /// Per-port reference impedance (the single authority).
    #[napi(getter, js_name = "z0")]
    pub fn get_z0(&self) -> Result<Vec<f64>> {
        Ok(self.core()?.z0().to_vec())
    }

    /// Port count.
    #[napi(getter)]
    pub fn nports(&self) -> Result<u32> {
        Ok(self.core()?.nports())
    }

    /// File stem without extension.
    #[napi(getter)]
    pub fn name(&self) -> Result<String> {
        Ok(self.core()?.name().to_owned())
    }

    /// Merged `!` comment text.
    #[napi(getter)]
    pub fn comments(&self) -> Result<String> {
        Ok(self.core()?.comments().to_owned())
    }

    /// File format version, `"1.0"` / `"1.1"`.
    #[napi(getter)]
    pub fn version(&self) -> Result<String> {
        Ok(self.core()?.version().to_owned())
    }

    /// Original parameter domain (metadata), canonical uppercase.
    #[napi(getter)]
    pub fn parameter(&self) -> Result<String> {
        Ok(self.core()?.parameter().as_ref().to_owned())
    }

    /// Unified accessor domain × format. JS has no complex type, so every
    /// format crosses as flat interleaved pairs and the shape always ends
    /// in `2` (`(nfreq,n,n,2)`): RI = re/im, MA/DB = (mag|db, deg). Both
    /// arguments are mandatory — use the `s` property for the zero-copy body.
    #[napi]
    pub fn data(&self, parameter: String, format: String) -> Result<TouchstoneData> {
        let p = resolve_ts_kw(&parameter)?;
        let f = resolve_ts_kw(&format)?;
        let core = self.core()?;
        let n = core.nports() as usize;
        let nf = core.f().len();
        let cow = core
            .data(p, f)
            .map_err(|e| Error::from_reason(e.to_string()))?;
        Ok(TouchstoneData {
            values: Float64Array::from(cow.to_vec()),
            shape: vec![nf as u32, n as u32, n as u32, 2],
        })
    }

    /// Render Touchstone text in `parameter`/`format` (shortest-roundtrip
    /// numbers; `#` line uses the stored version).
    #[napi]
    pub fn write_touchstone(&self, parameter: String, format: String) -> Result<String> {
        let p = resolve_ts_kw(&parameter)?;
        let f = resolve_ts_kw(&format)?;
        self.core()?
            .write_touchstone(p, f)
            .map_err(|e| Error::from_reason(e.to_string()))
    }

    /// Write to disk (async AsyncTask; the filename is corrected by core
    /// `write_path`, extension always `.{P}Np`). `parameter` and `format`
    /// are mandatory (no silent defaults).
    #[napi]
    pub async fn write_file(&self, path: String, parameter: String, format: String) -> Result<()> {
        let p = resolve_ts_kw(&parameter)?;
        let f = resolve_ts_kw(&format)?;
        self.core()?
            .write_file(&path, p, f)
            .map_err(|e| Error::from_reason(e.to_string()))
    }

    /// Path/URL → filename with extension.
    #[napi]
    pub fn filename_from_path(path: String) -> String {
        CoreTouchstone::filename_from_path(&path)
    }

    /// Filename → stem (Touchstone grammar; no match → whole string).
    #[napi]
    pub fn name_from_filename(filename: String) -> String {
        CoreTouchstone::name_from_filename(&filename)
    }

    /// Filename → port count (grammar `\.[ghsyz]\d+p`); no match throws
    /// guiding the caller to pass nports explicitly.
    #[napi]
    pub fn nports_from_filename(filename: String) -> Result<u32> {
        CoreTouchstone::nports_from_filename(&filename)
            .map(|n| n as u32)
            .map_err(|e| Error::from_reason(e.to_string()))
    }

    /// Deterministic manual reclamation (the unified cross-end verb,
    /// ironclad rule 12). Idempotent; post-drop access throws. The napi
    /// cleanup finalizer runs the Rust `Drop` on GC as the fallback.
    // clippy's trait-suggestion cannot be honored without renaming the
    // unified verb; the wrapper has no `impl Drop`, so nothing is shadowed.
    #[allow(clippy::should_implement_trait)]
    #[napi]
    pub fn drop(&mut self) {
        self.1 = true;
    }
}
