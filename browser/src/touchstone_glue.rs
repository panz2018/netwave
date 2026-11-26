//! Browser dispatch glue for the `touchstone` namespace: instance + namespace
//! `match`es over core's [`Touchstone`], plus the browser fetch backend for
//! `fromUrl`. Rust has no reflection — the arm list IS the method table.

use std::str::FromStr;

use wasm_bindgen::prelude::*;

use netwave::touchstone::{Touchstone, TouchstoneEncoding};

use crate::resources;

/// Wrap an owned f64 block as a `Float64Array` for the worker reply
/// (structured-cloned across the realm boundary).
fn f64_array(v: &[f64]) -> JsValue {
    js_sys::Float64Array::from(v).into()
}

/// Read a domain/format keyword from a JS string argument (core `FromStr`
/// quotes the offending token in the error).
fn js_ts_kw<T: FromStr>(v: &JsValue) -> Result<T, JsValue>
where
    T::Err: std::fmt::Display,
{
    v.as_string()
        .ok_or_else(|| resources::js("argument must be a string"))
        .and_then(|s| T::from_str(&s).map_err(|e| resources::js(e.to_string())))
}

/// Read an optional keyword argument (`undefined`/`null` → `None`; a string
/// goes through core `FromStr`, which quotes the offending token).
fn js_ts_kw_opt<T: FromStr>(v: Option<&JsValue>) -> Result<Option<T>, JsValue>
where
    T::Err: std::fmt::Display,
{
    match v {
        Some(v) if !v.is_undefined() && !v.is_null() => js_ts_kw(v).map(Some),
        _ => Ok(None),
    }
}

/// Resolve the worker's global scope to a pending `fetch(url)` request. wasm
/// lives only inside the resident worker, so the global is a
/// `WorkerGlobalScope` — never a main-thread `Window`. A scope without fetch
/// capability errors synchronously (before any await), so the coverage driver
/// reaches that arm by polling `fetch_text` with a non-scope global.
fn resolve_fetch_scope(global: &JsValue, url: &str) -> Result<js_sys::Promise, JsValue> {
    if let Some(w) = global.dyn_ref::<web_sys::WorkerGlobalScope>() {
        Ok(w.fetch_with_str(url))
    } else {
        Err(resources::js("no fetch-capable global scope"))
    }
}

/// Coverage-chain driver: reach the "no fetch-capable global scope" arm AND its
/// `map_err` closure in [`fetch_text`]. The arm is synchronous (before any
/// await), so polling `fetch_text` once with a non-scope global runs the body
/// up to the error and completes it — counting both the reject branch and the
/// closure that wraps it into a `Fetch` error. Compiled only under the
/// `coverage` feature; production builds exclude it.
#[cfg(feature = "coverage")]
pub fn drive_fetch_reject_arm() {
    use std::future::Future;
    use std::pin::pin;
    use std::task::{Context, Waker};

    let fake_global = JsValue::from_str("not-a-scope");
    let mut future = pin!(fetch_text(&fake_global, "http://example.invalid/x.s1p"));
    // The future errors synchronously (before its first await), so a single
    // poll returns `Ready` and the noop waker is never invoked.
    let mut cx = Context::from_waker(Waker::noop());
    let _ = future.as_mut().poll(&mut cx);
}

/// Browser HTTP backend: `fetch` on the given scope (Promise; the main thread
/// never runs wasm during I/O — fetch runs in the worker). Non-OK status
/// surfaces verbatim.
///
/// The scope is a parameter, not `js_sys::global()`: production passes the real
/// worker global, the coverage driver passes a non-scope value so the "no
/// fetch-capable scope" arm is reachable.
async fn fetch_text(
    global: &JsValue,
    url: &str,
) -> Result<String, netwave::touchstone::TouchstoneError> {
    use netwave::touchstone::TouchstoneError;
    let pending = resolve_fetch_scope(global, url).map_err(|e| TouchstoneError::Fetch {
        url: url.to_owned(),
        reason: e.as_string().unwrap_or_default(),
    })?;
    let resp: web_sys::Response = wasm_bindgen_futures::JsFuture::from(pending)
        .await
        .map_err(|e| TouchstoneError::Fetch {
            url: url.to_owned(),
            reason: format!("{e:?}"),
        })?
        .into();
    let ok: bool = resp.ok();
    let status = resp.status();
    if !ok {
        return Err(TouchstoneError::Fetch {
            url: url.to_owned(),
            reason: status.to_string(),
        });
    }
    let text_promise = resp.text().map_err(|e| TouchstoneError::Fetch {
        url: url.to_owned(),
        reason: format!("{e:?}"),
    })?;
    let text = wasm_bindgen_futures::JsFuture::from(text_promise)
        .await
        .map_err(|e| TouchstoneError::Fetch {
            url: url.to_owned(),
            reason: format!("{e:?}"),
        })?;
    text.as_string().ok_or_else(|| TouchstoneError::Fetch {
        url: url.to_owned(),
        reason: "non-utf8 body".to_owned(),
    })
}

/// Instance dispatch: the numeric-handle half of the shell's `Touchstone`.
/// `drop` never reaches here — the dispatcher intercepts it (removing the
/// table entry is the table's own operation).
impl resources::Resource for Touchstone {
    fn as_any(&self) -> &dyn std::any::Any {
        self
    }

    fn call(&mut self, method: &str, args: &[JsValue]) -> Result<JsValue, JsValue> {
        use resources::{js, js_object, unknown_method};
        let n = self.nports() as usize;
        match method {
            "s" => Ok(f64_array(self.s())),
            "z" => Ok(f64_array(&self.z())),
            "y" => Ok(f64_array(&self.y())),
            "g" => self
                .g()
                .map(|v| f64_array(&v))
                .map_err(|e| js(e.to_string())),
            "h" => self
                .h()
                .map(|v| f64_array(&v))
                .map_err(|e| js(e.to_string())),
            "f" => Ok(f64_array(&self.f())),
            "z0" => Ok(f64_array(self.z0())),
            "nports" => Ok(JsValue::from_f64(self.nports() as f64)),
            "name" => Ok(JsValue::from_str(self.name())),
            "comments" => Ok(JsValue::from_str(self.comments())),
            "version" => Ok(JsValue::from_str(self.version())),
            "parameter" => Ok(JsValue::from_str(self.parameter().as_ref())),
            "data" => {
                let p = js_ts_kw(args.first().ok_or_else(|| js("parameter required"))?)?;
                let f = js_ts_kw(args.get(1).ok_or_else(|| js("format required"))?)?;
                let nf = self.f().len();
                let cow = self.data(p, f).map_err(|e| js(e.to_string()))?;
                // JS has no complex type: every format crosses as flat
                // interleaved pairs, so the shape always ends in 2.
                let shape = js_sys::Array::of4(
                    &JsValue::from_f64(nf as f64),
                    &JsValue::from_f64(n as f64),
                    &JsValue::from_f64(n as f64),
                    &JsValue::from_f64(2.0),
                );
                Ok(js_object(&[
                    ("values", f64_array(&cow)),
                    ("shape", shape.into()),
                ]))
            }
            "toText" => {
                let p = js_ts_kw(args.first().ok_or_else(|| js("parameter required"))?)?;
                let f = js_ts_kw(args.get(1).ok_or_else(|| js("format required"))?)?;
                self.to_text(p, f)
                    .map(|t| JsValue::from_str(&t))
                    .map_err(|e| js(e.to_string()))
            }
            // Byte-boundary output: encode in core (JS TextEncoder only
            // speaks UTF-8) and hand the bytes back as a Uint8Array
            // (structured clone; output direction never transfers).
            "toBytes" => {
                let p = js_ts_kw(args.first().ok_or_else(|| js("parameter required"))?)?;
                let f = js_ts_kw(args.get(1).ok_or_else(|| js("format required"))?)?;
                let enc = js_ts_kw_opt::<TouchstoneEncoding>(args.get(2))?;
                let bytes = self.to_bytes(p, f, enc).map_err(|e| js(e.to_string()))?;
                Ok(js_sys::Uint8Array::from(bytes.as_slice()).into())
            }
            // The browser has no filesystem: render in core and hand
            // `{text, filename}` back (structured clone); the shell's Blob +
            // `<a download>` is the platform glue.
            "writeFile" => {
                let p = js_ts_kw(args.first().ok_or_else(|| js("parameter required"))?)?;
                let f = js_ts_kw(args.get(1).ok_or_else(|| js("format required"))?)?;
                let path = resources::arg_opt_str(args, 2);
                let text = self.to_text(p, f).map_err(|e| js(e.to_string()))?;
                let filename = self.write_path(path.as_deref(), p);
                Ok(js_object(&[
                    ("text", JsValue::from_str(&text)),
                    ("filename", JsValue::from_str(&filename)),
                ]))
            }
            _ => Err(unknown_method("touchstone", method)),
        }
    }
}

/// Namespace dispatch: the `"touchstone"` namespace's factories and the name
/// pipeline (mechanical camelCase of the core snake names).
pub fn call_namespace(method: &str, args: &[JsValue]) -> Result<JsValue, JsValue> {
    use resources::{arg_opt_str, arg_str, insert, js, unknown_method};
    match method {
        "fromText" => {
            let text = arg_str(args, 0)?;
            let nports = args.get(1).and_then(|v| v.as_f64()).map(|v| v as usize);
            let path = arg_opt_str(args, 2);
            let ts = Touchstone::from_text(&text, nports, path.as_deref())
                .map_err(|e| js(e.to_string()))?;
            Ok(JsValue::from_f64(insert(Box::new(ts)) as f64))
        }
        // The bytes arrive transferred from the shell (`fromFile(file)` or
        // the public `fromBytes`); the filename rides along for the name
        // pipeline. Decoding (guess chain / explicit whitelist) lives in
        // core — the same `from_bytes` every other surface uses.
        "fromBytes" => {
            let bytes = args
                .first()
                .and_then(|v| v.dyn_ref::<js_sys::Uint8Array>())
                .map(js_sys::Uint8Array::to_vec)
                .ok_or_else(|| js("argument 0 must be a Uint8Array"))?;
            let nports = args.get(1).and_then(|v| v.as_f64()).map(|v| v as usize);
            let path = arg_opt_str(args, 2);
            let enc = js_ts_kw_opt::<TouchstoneEncoding>(args.get(3))?;
            let ts = Touchstone::from_bytes(&bytes, nports, path.as_deref(), enc)
                .map_err(|e| js(e.to_string()))?;
            Ok(JsValue::from_f64(insert(Box::new(ts)) as f64))
        }
        // Pure-data factory: arg 0 is the handle of an already-hosted
        // `Frequency` (the shell reads `frequency.handle` internally — the
        // user only ever passes the object). The table entry is type-
        // erased, so `as_any` downcasts it back to `Frequency` (internal,
        // never surfaces on a binding). The hosted axis is read out as owned
        // Hz (the lock is not reentrant, so the new `Frequency` is rebuilt
        // after `with_any` returns — same pattern as the `frequency`/`copy`
        // arm). `data` arrives moved via the shell's transfer list (the
        // `upload` replacement).
        "fromData" => {
            let freq_handle = resources::arg_u32(args, 0)?;
            let data = resources::arg_f64_vec(args, 1)?;
            let z0 = resources::arg_f64_vec(args, 2)?;
            let parameter = js_ts_kw(args.get(3).ok_or_else(|| js("parameter required"))?)?;
            let name = resources::arg_opt_str(args, 4).unwrap_or_default();
            let comments = resources::arg_opt_str(args, 5).unwrap_or_default();
            let axis_hz = resources::with_any(freq_handle, |any| {
                any.downcast_ref::<netwave::frequency::Frequency>()
                    .and_then(|f| f.f().ok())
            })
            .map_err(js)?
            .ok_or_else(|| js("handle is not a live Frequency"))?;
            let frequency = netwave::frequency::Frequency::from_f(
                axis_hz,
                netwave::frequency::FrequencyUnit::Hz,
            );
            let ts = Touchstone::from_data(&frequency, &data, &z0, parameter, &name, &comments)
                .map_err(|e| js(e.to_string()))?;
            Ok(JsValue::from_f64(insert(Box::new(ts)) as f64))
        }
        // Async in the browser glue (web_sys::fetch): the worker awaits the
        // Promise before posting the reply, so the main thread never runs
        // wasm. The fetch backend lives here (not core) because it is a
        // wasm-only dependency; the parsed text crosses into core via
        // `from_text`.
        "fromUrl" => {
            let url = arg_str(args, 0)?;
            let promise = wasm_bindgen_futures::future_to_promise(async move {
                let global = js_sys::global();
                let text = fetch_text(&global, &url)
                    .await
                    .map_err(|e| js(e.to_string()))?;
                let path = Touchstone::url_filename(&url);
                Touchstone::from_text(&text, None, path.as_deref())
                    .map(|ts| JsValue::from_f64(insert(Box::new(ts)) as f64))
                    .map_err(|e| js(e.to_string()))
            });
            Ok(promise.into())
        }
        "filenameFromPath" => Ok(JsValue::from_str(&Touchstone::filename_from_path(
            &arg_str(args, 0)?,
        ))),
        "nameFromFilename" => Ok(JsValue::from_str(&Touchstone::name_from_filename(
            &arg_str(args, 0)?,
        ))),
        "nportsFromFilename" => Touchstone::nports_from_filename(&arg_str(args, 0)?)
            .map(|n| JsValue::from_f64(n as f64))
            .map_err(|e| js(e.to_string())),
        _ => Err(unknown_method("touchstone", method)),
    }
}

/// Mount the `"touchstone"` namespace. Called once from the
/// `#[wasm_bindgen(start)]` hook in `lib.rs`.
pub fn register() {
    resources::register_namespace("touchstone", call_namespace);
}
