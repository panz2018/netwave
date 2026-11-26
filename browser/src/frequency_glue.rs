//! Browser dispatch glue for the `frequency` namespace: instance + namespace
//! `match`es over core's [`Frequency`]. Rust has no reflection — the arm list
//! IS the method table. Adding a method = one arm here; `resources.rs`, the
//! worker, the shells and `types.ts` never change.

use wasm_bindgen::prelude::*;

use netwave::frequency::{Frequency, FrequencyUnit, WavelengthUnit};

use crate::resources;

// Read a unit argument that is either a numeric enum ordinal or a string
// (case-insensitive, core FromStr quotes the offending input). Inlined here
// (not in resources.rs) so the generic dispatcher stays unit-agnostic.
fn js_freq_unit(v: &JsValue) -> Result<FrequencyUnit, JsValue> {
    use std::str::FromStr;
    if let Some(s) = v.as_string() {
        return FrequencyUnit::from_str(&s).map_err(|e| resources::js(e.to_string()));
    }
    let n = v
        .as_f64()
        .ok_or_else(|| resources::js("unit must be a number or a string"))? as u8;
    FrequencyUnit::from_ordinal(n).ok_or_else(|| resources::js("invalid unit ordinal"))
}

fn js_wl_unit(v: &JsValue) -> Result<WavelengthUnit, JsValue> {
    use std::str::FromStr;
    if let Some(s) = v.as_string() {
        return WavelengthUnit::from_str(&s).map_err(|e| resources::js(e.to_string()));
    }
    let n = v
        .as_f64()
        .ok_or_else(|| resources::js("unit must be a number or a string"))? as u8;
    WavelengthUnit::from_ordinal(n).ok_or_else(|| resources::js("invalid unit ordinal"))
}

/// Wrap an owned f64 axis as a `Float64Array` for the worker reply. The
/// worker's `postMessage` structured-clones it (a copy across the realm
/// boundary — matching the `f` copy semantics; the wasm buffer is not
/// transferred, so the high-water mark is the live-object peak, see docs).
fn f64_array(v: &[f64]) -> JsValue {
    js_sys::Float64Array::from(v).into()
}

impl resources::Resource for Frequency {
    fn as_any(&self) -> &dyn std::any::Any {
        self
    }

    fn call(&mut self, method: &str, args: &[JsValue]) -> Result<JsValue, JsValue> {
        use resources::{js, unknown_method};
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
/// functions. `liveCount` lives here because it counts `Frequency` instances
/// (the witness is defined in core's `frequency.rs`) — no separate diagnostic
/// namespace.
pub fn call_namespace(method: &str, args: &[JsValue]) -> Result<JsValue, JsValue> {
    use resources::{arg_f64_vec, arg_u32, insert, instance_call, js, unknown_method};
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
        // `copy` is a factory (it allocates a new handle), so it lives on the
        // namespace channel: the axis + unit are read back through
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
            let units = netwave::frequency::frequency_units();
            let arr = js_sys::Array::new();
            for u in units {
                arr.push(&JsValue::from_str(&u));
            }
            Ok(arr.into())
        }
        "liveCount" => Ok(JsValue::from_f64(netwave::frequency::live_count() as f64)),
        _ => Err(unknown_method("frequency", method)),
    }
}

/// Mount the `"frequency"` namespace. Called once from the
/// `#[wasm_bindgen(start)]` hook in `lib.rs`.
pub fn register() {
    resources::register_namespace("frequency", call_namespace);
}

/// Coverage-chain driver: reach the `copy` factory's two malformed-source
/// arms. No real `Frequency` returns a non-array `f()` or an out-of-range
/// `unit()`, so the wasm coverage binary hosts a fake resource that does, and
/// runs `copy` over it to count the `expected Float64Array` and
/// `invalid unit ordinal` arms. Compiled only under the `coverage` feature;
/// production builds exclude it.
#[cfg(feature = "coverage")]
pub fn drive_copy_arms() {
    use resources::{Resource, insert, instance_call};

    // A source whose `f`/`unit` read back malformed: `axis_ok` picks whether
    // `f` is a valid Float64Array (so copy reaches the unit arm) or a plain
    // number (so copy fails at the axis arm).
    struct Malformed {
        axis_ok: bool,
    }
    impl Resource for Malformed {
        fn as_any(&self) -> &dyn std::any::Any {
            self
        }
        fn call(&mut self, method: &str, _args: &[JsValue]) -> Result<JsValue, JsValue> {
            match method {
                "f" if self.axis_ok => Ok(js_sys::Float64Array::from(&[1e9][..]).into()),
                "f" => Ok(JsValue::from_f64(1.0)),
                // A valid ordinal would succeed; 99 is out of range.
                "unit" => Ok(JsValue::from_f64(99.0)),
                _ => Ok(JsValue::UNDEFINED),
            }
        }
    }

    // axis malformed → copy fails at `expected Float64Array`. The direct
    // as_any call and the unknown-method dispatch cover this driver's own
    // trait arms so the mock adds no uncovered lines of its own.
    let bad_axis = Malformed { axis_ok: false };
    let _ = bad_axis.as_any();
    let h1 = insert(Box::new(bad_axis));
    let _ = instance_call(h1, "unknown", &[]);
    let _ = call_namespace("copy", &[JsValue::from_f64(h1 as f64)]);
    // axis valid but unit ordinal out of range → copy fails at `invalid unit`.
    let h2 = insert(Box::new(Malformed { axis_ok: true }));
    let _ = call_namespace("copy", &[JsValue::from_f64(h2 as f64)]);
}
