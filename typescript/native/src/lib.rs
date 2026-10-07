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

/// napi binding for the core `Frequency` (internalized: the TS shell does
/// NOT re-export it). napi's cleanup finalizer runs the Rust `Drop` on GC,
/// and `free` is the deterministic early-release escape hatch (idempotent
/// via the core `release` guard).
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

    /// Number of frequency points.
    #[napi]
    pub fn npoints(&self) -> usize {
        self.0.npoints()
    }

    /// Deterministic early release (no GC needed). Named `free` to match
    /// the method wasm-bindgen auto-generates for the wasm class, so the
    /// two ends expose the same escape hatch (ironclad rule 9); it also
    /// avoids colliding with `std::ops::Drop::drop`.
    #[napi]
    pub fn free(&mut self) {
        self.0.release();
    }
}
