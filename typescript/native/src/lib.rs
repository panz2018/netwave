//! netwave Node binding (napi-rs, scaffold phase 0).
//!
//! Zero-copy: core allocates a `Vec<Complex64>`; the bytes' ownership is
//! moved into a V8 external `Buffer` via `Buffer::from(Vec<u8>)` (no copy;
//! freed at GC finalize). The JS shell takes `buf.buffer` for the
//! underlying ArrayBuffer. `read_element` passes a Float64Array view back
//! into Rust and reads by pointer, proving it is the same memory.

use napi::bindgen_prelude::*;
use napi_derive::napi;
use netwave::fill_pattern as core_fill_pattern;

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
