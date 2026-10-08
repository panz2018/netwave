//! netwave Node binding (napi-rs).
//!
//! Zero-copy: core allocates a `Vec<Complex64>`; the bytes' ownership is
//! moved into a V8 external `Buffer` via `Buffer::from(Vec<u8>)` (no copy;
//! freed at GC finalize). The JS shell takes `buf.buffer` for the
//! underlying ArrayBuffer. `read_element` passes a Float64Array view back
//! into Rust and reads by pointer, proving it is the same memory.

use napi::bindgen_prelude::*;
use napi_derive::napi;
use netwave::fill_pattern as core_fill_pattern;
use netwave::frequency::{Frequency as CoreFrequency, FrequencyUnit};
use netwave::network::Network as CoreNetwork;

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
    /// Build a sweep from hertz points + unit ordinal (the JS enum value;
    /// factory, not constructor).
    ///
    /// `unit` is a plain `u8`, not `FrequencyUnit`: the FFI signature must
    /// not name the core enum, because under `cargo clippy --workspace` the
    /// `node` and `browser` features merge onto one `netwave` build and
    /// neither binding macro applies — the same reason
    /// `fill_pattern`/`frequency_units` use primitives. The ordinal maps back
    /// to the variant in core (`from_ordinal`), so no name list is copied.
    #[napi(factory)]
    pub fn from_f(f_hz: Vec<f64>, unit: u8) -> Self {
        let unit = FrequencyUnit::from_ordinal(unit).expect("invalid frequency unit ordinal");
        Frequency(CoreFrequency::from_f(f_hz, unit))
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
