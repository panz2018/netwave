//! `Network`: the data-entry + read + drop surface.
//!
//! Zero compute, zero parsing, zero port semantics. The class shape holds on
//! every platform: the data entry returns an instance, `read_element`/`drop`
//! are instance methods, and the numeric handle stays `@internal`
//! (ironclad rule 12).

use crate::Dropped;
#[cfg(all(feature = "browser", not(feature = "node"), not(coverage)))]
use wasm_bindgen::prelude::*;

/// An S-matrix data container: `(nfreq, nports, nports)`
/// interleaved complex f64 (`[re, im, re, im, ...]`, governance rule 1).
///
/// # Memory contract
///
/// - Construction ([`Network::from_f64`], [`Network::fill_pattern`]) owns a
///   `Vec<f64>`.
/// - [`Drop`] is the only reclamation path (RAII). The inherent
///   [`Network::drop`] is the deterministic manual escape hatch shared with
///   RAII (inherent methods resolve first, so `Drop::drop` delegates here
///   without recursion). Idempotent; after `drop()` every data access errors.
pub struct Network {
    /// Frequency point count (axis length).
    nfreq: usize,
    /// Port count (each frequency point is an `nports × nports` matrix).
    nports: usize,
    /// Interleaved complex f64 data (re first).
    data: Vec<f64>,
    /// Set once dropped, so a second drop is a no-op and data access
    /// errors instead of reading freed dimensions.
    dropped: bool,
}

impl Network {
    /// Wrap an owned interleaved f64 buffer.
    ///
    /// `nfreq`/`nports` describe the shape; `data.len()` MUST equal
    /// `nfreq * nports * nports * 2` (re/im interleaved).
    pub fn from_f64(nfreq: usize, nports: usize, data: Vec<f64>) -> Self {
        assert_eq!(
            data.len(),
            nfreq * nports * nports * 2,
            "data length must be nfreq*nports*nports*2 (interleaved f64)"
        );
        Self {
            nfreq,
            nports,
            data,
            dropped: false,
        }
    }

    /// Allocate and fill an `(nfreq, nports, nports)` buffer with the
    /// scaffold pattern (`re = f*100 + p*10 + q`, `im = -re`), interleaved
    /// as `[re, im, ...]`.
    ///
    /// Same closed-form pattern as the scaffold free function so every
    /// binding's existing assertions transfer unchanged.
    pub fn fill_pattern(nfreq: usize, nports: usize) -> Self {
        let data = crate::fill_pattern(nfreq, nports)
            .into_iter()
            .flat_map(|c| [c.re, c.im])
            .collect();
        Self::from_f64(nfreq, nports, data)
    }

    /// Frequency point count.
    pub fn nfreq(&self) -> usize {
        self.nfreq
    }

    /// Port count.
    pub fn nports(&self) -> usize {
        self.nports
    }

    /// Read one interleaved f64 element (re/im index into the buffer).
    ///
    /// Errors after `drop()` (the data is gone; the dimensions are not
    /// readable either).
    pub fn read_element(&self, idx: usize) -> Result<f64, Dropped> {
        if self.dropped {
            return Err(Dropped);
        }
        Ok(self.data[idx])
    }

    /// Drop the buffer. Idempotent; RAII `Drop` calls the same body.
    // The cross-end naming contract (ironclad rule 12) mandates this exact
    // name on every platform; clippy's trait-suggestion cannot be honored
    // without renaming the unified verb.
    #[allow(clippy::should_implement_trait)]
    pub fn drop(&mut self) {
        if !self.dropped {
            self.data = Vec::new();
            self.dropped = true;
        }
    }
}

impl Drop for Network {
    /// RAII reclamation: frees the buffer. The single reclamation path.
    fn drop(&mut self) {
        self.drop();
    }
}

// ---------------------------------------------------------------------------
// Browser dispatch (cfg=browser): the worker forwards `{handle, method,
// args}` to the single generic `resources::call`; this module owns the
// name→function `match`es (Rust has no reflection — the arm list IS the
// method table). Adding a method = one arm here; `resources.rs`, the
// worker, the shells and `types.ts` never change.
// ---------------------------------------------------------------------------

/// Instance dispatch: the numeric-handle half of the shell's `Network`.
/// `drop` never reaches here — the dispatcher intercepts it (removing the
/// table entry is the table's own operation).
#[cfg(all(feature = "browser", not(feature = "node"), not(coverage)))]
impl crate::resources::Resource for Network {
    fn call(&mut self, method: &str, args: &[JsValue]) -> Result<JsValue, JsValue> {
        use crate::resources::{arg_u32, unknown_method};
        match method {
            "readElement" => self
                .read_element(arg_u32(args, 0)? as usize)
                .map(|v| JsValue::from_f64(v))
                .map_err(|e| crate::resources::js(e.to_string())),
            _ => Err(unknown_method("network", method)),
        }
    }
}

/// Namespace dispatch: the `"network"` namespace's factories.
#[cfg(all(feature = "browser", not(feature = "node"), not(coverage)))]
pub fn call_namespace(method: &str, args: &[JsValue]) -> Result<JsValue, JsValue> {
    use crate::resources::{arg_f64_vec, arg_u32, insert, js, unknown_method};
    match method {
        // Shape is explicit: a bare Float64Array length does not factor
        // uniquely into (nfreq, nports).
        "upload" => {
            let view = arg_f64_vec(args, 0)?;
            let nfreq = arg_u32(args, 1)? as usize;
            let nports = arg_u32(args, 2)? as usize;
            let want = nfreq * nports * nports * 2;
            if view.len() != want {
                return Err(js(format!(
                    "data length must be nfreq*nports*nports*2 ({want}), got {}",
                    view.len()
                )));
            }
            let network = Network::from_f64(nfreq, nports, view);
            Ok(JsValue::from_f64(insert(Box::new(network)) as f64))
        }
        // Same closed-form pattern as the scaffold free function, so every
        // binding's existing assertions transfer unchanged.
        "fillPattern" => {
            let nfreq = arg_u32(args, 0)? as usize;
            let nports = arg_u32(args, 1)? as usize;
            let network = Network::fill_pattern(nfreq, nports);
            Ok(JsValue::from_f64(insert(Box::new(network)) as f64))
        }
        _ => Err(unknown_method("network", method)),
    }
}

/// Mount the `"network"` namespace. Called once from the
/// `#[wasm_bindgen(start)]` hook in `lib.rs`.
#[cfg(all(feature = "browser", not(feature = "node"), not(coverage)))]
pub fn register() {
    crate::resources::register_namespace("network", call_namespace);
}
