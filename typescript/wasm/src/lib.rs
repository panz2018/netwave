//! netwave wasm binding (wasm-bindgen).
//!
//! Zero-copy: core allocates a `Vec<Complex64>`; `mem::forget` leaks it
//! into wasm linear memory and the function returns
//! `{buffer: memory.buffer, byteOffset: ptr, length}`. The JS shell cuts a
//! view directly with `new Float64Array(buffer, byteOffset, length*2)` —
//! no copy. The leak is acceptable at scaffold call volume; an explicit
//! arena with reclamation replaces it later.

use js_sys::{Object, Reflect, WebAssembly::Memory};
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
