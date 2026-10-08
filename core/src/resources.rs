//! Browser-only handle table + generic dispatch: the single resource
//! registry inside wasm.
//!
//! The resident worker is the single data authority (ironclad rule 8), so
//! the handle table and the dispatch live here in core — worker JS keeps
//! zero state and forwards `{handle, method, args}` mechanically: a fixed
//! template independent of the verb count (api-contract spec "worker
//! generic dispatch and single-resident topology").
//!
//! `handle` is `number | string`, never a sentinel: a number addresses an
//! instance in the table, a string names a core module namespace (class
//! factories + module free functions). Rust has no reflection, so
//! name→function dispatch is a hand-written `match` inside each resource
//! module (`network.rs`, `frequency.rs`, …): adding a method adds one arm
//! there and changes nothing else (a generic table is not a generic
//! dispatch).
//!
//! Structure: the table logic is plain Rust and natively callable under
//! `--features browser` (host/remove/namespace lookup/unknown-handle
//! errors); the `#[wasm_bindgen]` `call` below is a thin adapter that only
//! converts types. wasm_bindgen exported functions compile on the host but
//! abort when *called* there, so the argument unpacking and the real
//! method dispatch are covered by the worker roundtrip tests.
//!
//! Compiled only under the browser guard (`browser`, not `node`, not
//! `coverage` — the workspace clippy merge must not pull wasm glue into a
//! native build); node/Python hold objects directly and never see a handle
//! table.

use std::collections::BTreeMap;
use std::sync::{Mutex, OnceLock};

use wasm_bindgen::prelude::*;

/// A resource hosted in the table: run one method call by name.
///
/// Each resource type implements this with a hand-written `match` in its own
/// module. The registry never names a concrete type, so adding a method — or
/// a whole resource type — never changes this file.
/// `Send`: instances live in a process-global `Mutex<Registry>`, so every
/// hosted resource must be safe to move across the (single) worker thread.
pub trait Resource: Send {
    /// Run `method` on this instance. An unknown name falls into the
    /// implementation's error arm.
    fn call(&mut self, method: &str, args: &[JsValue]) -> Result<JsValue, JsValue>;
}

/// A module namespace: class factories and module-level free functions,
/// dispatched by the module's own `match`. The namespace routes by module
/// name and never renames a method — method names stay the mechanical
/// camelCase of the core snake names.
pub type NamespaceFn = fn(method: &str, args: &[JsValue]) -> Result<JsValue, JsValue>;

/// The single instance table, namespace table and monotonic counter.
struct Registry {
    instances: BTreeMap<u32, Box<dyn Resource>>,
    namespaces: BTreeMap<&'static str, NamespaceFn>,
    next_handle: u32,
}

impl Registry {
    fn new() -> Self {
        Self {
            instances: BTreeMap::new(),
            namespaces: BTreeMap::new(),
            next_handle: 1,
        }
    }

    /// Allocate the next handle and weld the resource in.
    fn insert(&mut self, resource: Box<dyn Resource>) -> u32 {
        let handle = self.next_handle;
        self.next_handle += 1;
        self.instances.insert(handle, resource);
        handle
    }

    /// Remove a handle, running its `Drop` immediately. A second `drop` of
    /// the same handle reports unknown (the Rust `Drop` already ran).
    fn remove(&mut self, handle: u32) -> Result<(), String> {
        match self.instances.remove(&handle) {
            Some(_) => Ok(()),
            None => Err(format!("unknown or dropped handle: {handle}")),
        }
    }

    /// Borrow the instance behind `handle` and dispatch into its `match`.
    /// An unknown handle reports through the plain-string error channel so
    /// the table path stays testable off-wasm (the instance's own `match`
    /// builds `JsValue` values, which abort off-wasm — the worker roundtrip
    /// covers that leg).
    fn instance_call(
        &mut self,
        handle: u32,
        method: &str,
        args: &[JsValue],
    ) -> Result<JsValue, String> {
        let resource = self
            .instances
            .get_mut(&handle)
            .ok_or_else(|| format!("unknown or dropped handle: {handle}"))?;
        resource
            .call(method, args)
            .map_err(|e| e.as_string().unwrap_or_else(|| format!("{e:?}")))
    }

    /// Mount a module namespace under its core module name.
    fn register(&mut self, name: &'static str, namespace: NamespaceFn) {
        self.namespaces.insert(name, namespace);
    }

    /// Look up a namespace by module name. A namespace has no instances, so
    /// `drop` is simply not registered there and lands in the namespace's
    /// own unknown-method arm — no special case in the dispatcher.
    fn namespace(&self, name: &str) -> Result<NamespaceFn, String> {
        self.namespaces
            .get(name)
            .copied()
            .ok_or_else(|| format!("unknown namespace: {name:?}"))
    }
}

static REGISTRY: OnceLock<Mutex<Registry>> = OnceLock::new();

fn registry() -> &'static Mutex<Registry> {
    REGISTRY.get_or_init(|| Mutex::new(Registry::new()))
}

/// Host a resource and return its globally unique handle.
pub fn insert(resource: Box<dyn Resource>) -> u32 {
    registry().lock().unwrap().insert(resource)
}

/// The single reclamation: remove the handle, which runs the resource's
/// Rust `Drop` right now (deterministic, GC-independent).
pub fn remove(handle: u32) -> Result<(), String> {
    registry().lock().unwrap().remove(handle)
}

/// Mount a module namespace (factories + free functions) under its core
/// module name. Called once per module from the `#[wasm_bindgen(start)]`
/// hook in `lib.rs`.
pub fn register_namespace(name: &'static str, namespace: NamespaceFn) {
    registry().lock().unwrap().register(name, namespace);
}

/// Look up a registered namespace (native-testable routing table).
pub fn namespace(name: &str) -> Result<NamespaceFn, String> {
    registry().lock().unwrap().namespace(name)
}

/// Dispatch one call against the instance behind `handle`.
pub fn instance_call(handle: u32, method: &str, args: &[JsValue]) -> Result<JsValue, String> {
    registry()
        .lock()
        .unwrap()
        .instance_call(handle, method, args)
}

/// The single wasm entry: the verb-count-independent fixed template.
///
/// Number handle → instance dispatch; `method == "drop"` is intercepted here
/// because removing the table entry is the table's own operation, and it runs
/// the resource's Rust `Drop` directly with no JS object in between. String
/// handle → namespace dispatch. There is no sentinel value: a message says
/// whom it is calling.
#[wasm_bindgen]
pub fn call(handle: JsValue, method: &str, args: Box<[JsValue]>) -> Result<JsValue, JsValue> {
    let args = &args[..];
    if let Some(n) = handle.as_f64() {
        let handle = n as u32;
        if method == "drop" {
            return remove(handle).map(|()| JsValue::NULL).map_err(js);
        }
        return instance_call(handle, method, args).map_err(js);
    }
    if let Some(name) = handle.as_string() {
        return namespace(&name).map_err(js)?(method, args);
    }
    Err(js(
        "handle must be a number (instance) or a string (namespace)",
    ))
}

/// A `JsValue` error carrying a plain message.
pub(crate) fn js(message: impl AsRef<str>) -> JsValue {
    JsValue::from_str(message.as_ref())
}

/// The unknown-method error used by every `match` fallback arm.
pub(crate) fn unknown_method(namespace: &str, method: &str) -> JsValue {
    js(format!("unknown method {method:?} for {namespace:?}"))
}

/// Read argument `i` as a `u32` (exact in f64 — cross-end type parity).
pub(crate) fn arg_u32(args: &[JsValue], i: usize) -> Result<u32, JsValue> {
    args.get(i)
        .and_then(|v| v.as_f64())
        .map(|v| v as u32)
        .ok_or_else(|| js(format!("argument {i} must be a number")))
}

/// Read argument `i` as a `Float64Array`, copied into an owned `Vec<f64>`.
pub(crate) fn arg_f64_vec(args: &[JsValue], i: usize) -> Result<Vec<f64>, JsValue> {
    args.get(i)
        .map(|v| js_sys::Float64Array::from(v.clone()).to_vec())
        .ok_or_else(|| js(format!("argument {i} must be a Float64Array")))
}
