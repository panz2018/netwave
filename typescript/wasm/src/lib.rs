//! netwave wasm binding (wasm-bindgen).
//!
//! Zero-copy: core allocates a `Vec<Complex64>`; `mem::forget` leaks it
//! into wasm linear memory and the function returns
//! `{buffer: memory.buffer, byteOffset: ptr, length}`. The JS shell cuts a
//! view directly with `new Float64Array(buffer, byteOffset, length*2)` —
//! no copy. The leak is acceptable at scaffold call volume; an explicit
//! arena with reclamation replaces it later.

use js_sys::{Object, Reflect, WebAssembly::Memory};
use netwave::frequency::{Frequency as CoreFrequency, FrequencyUnit};
use wasm_bindgen::prelude::*;

/// Allocate and fill interleaved complex f64, moving ownership into linear
/// memory, and return a view descriptor.
///
/// Returns `{ buffer: ArrayBuffer, byteOffset: number, length: number of
/// complex numbers }`.
#[wasm_bindgen]
pub fn fill_pattern(nfreq: u32, nports: u32) -> Result<Object, JsValue> {
    let v = netwave::fill_pattern(nfreq as usize, nports as usize);
    let len = v.len(); // number of complex numbers
    let byte_offset = v.as_ptr() as usize;
    std::mem::forget(v); // ownership moved to linear memory; JS view aliases it
    let mem = wasm_bindgen::memory()
        .dyn_into::<Memory>()
        .map_err(|_| JsValue::from_str("wasm memory not exported"))?;
    let obj = Object::new();
    Reflect::set(&obj, &"buffer".into(), &mem.buffer())?;
    Reflect::set(&obj, &"byteOffset".into(), &(byte_offset as f64).into())?;
    Reflect::set(&obj, &"length".into(), &(len as f64).into())?;
    Ok(obj)
}

/// Pass a Float64Array view back into wasm and read an element (roundtrip
/// verification, zero-copy borrow).
#[wasm_bindgen]
pub fn read_element(view: &[f64], idx: u32) -> f64 {
    view[idx as usize]
}

/// Wasm binding for the core `Frequency` (internalized: the TS shell does
/// NOT re-export it). wasm_bindgen's generated `free()` runs the Rust
/// `Drop` (RAII) — the single reclamation path.
#[wasm_bindgen]
pub struct Frequency(CoreFrequency);

#[wasm_bindgen]
impl Frequency {
    /// Build a sweep from hertz points + unit ordinal (the JS enum value).
    ///
    /// `unit` is a plain `u8`, not `FrequencyUnit`: the FFI signature must
    /// not name the core enum, because under `cargo clippy --workspace` the
    /// `node` and `browser` features merge onto one `netwave` build and
    /// neither binding macro applies (LL-044) — the same reason
    /// `fill_pattern`/`frequency_units` use primitives. The ordinal maps back
    /// to the variant in core (`from_ordinal`), so no name list is copied.
    #[wasm_bindgen]
    pub fn from_f(f_hz: &[f64], unit: u8) -> Frequency {
        let unit = FrequencyUnit::from_ordinal(unit).expect("invalid frequency unit ordinal");
        Frequency(CoreFrequency::from_f(f_hz.to_vec(), unit))
    }

    /// Number of frequency points.
    #[wasm_bindgen]
    pub fn npoints(&self) -> usize {
        self.0.npoints()
    }
}
