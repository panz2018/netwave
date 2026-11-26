//! Browser-only handle table + generic dispatch: the single resource
//! registry inside wasm.
//!
//! The resident worker is the single data authority, so the handle table and
//! the dispatch live here in the browser crate — worker JS keeps zero state
//! and forwards `{handle, method, args}` mechanically: a fixed template
//! independent of the verb count.
//!
//! `handle` is `number | string`, never a sentinel: a number addresses an
//! instance in the table, a string names a module namespace (class factories
//! and module free functions). Rust has no reflection, so name→function
//! dispatch is a hand-written `match` inside each resource glue module
//! (`frequency_glue.rs`, `touchstone_glue.rs`, …): adding a method adds one
//! arm there and changes nothing else (a generic table is not a generic
//! dispatch).
//!
//! Structure: the table logic is plain Rust and natively callable (host/
//! remove/namespace lookup/unknown-handle errors); the `#[wasm_bindgen]`
//! `call` below is a thin adapter that only converts types. wasm_bindgen
//! exported functions compile on the host but abort when *called* there, so
//! the argument unpacking and the real method dispatch are covered by the
//! worker roundtrip tests.

use std::collections::BTreeMap;
use std::sync::{Mutex, OnceLock};

use wasm_bindgen::prelude::*;

/// A resource hosted in the table: run one method call by name.
///
/// Each resource type implements this with a hand-written `match` in its own
/// glue module. The registry never names a concrete type, so adding a method —
/// or a whole resource type — never changes this file.
/// `Send`: instances live in a process-global `Mutex<Registry>`, so every
/// hosted resource must be safe to move across the (single) worker thread.
pub trait Resource: Send {
    /// Run `method` on this instance. An unknown name falls into the
    /// implementation's error arm.
    fn call(&mut self, method: &str, args: &[JsValue]) -> Result<JsValue, JsValue>;

    /// Internal downcast: recover the concrete type from a table entry (the
    /// `touchstone`/`fromData` arm needs the hosted `Frequency`). Never
    /// surfaces on any binding — `Any` is a Rust-only type, so it cannot
    /// cross an FFI boundary by construction.
    fn as_any(&self) -> &dyn std::any::Any;
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

    /// Mount a module namespace under its module name.
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

/// Mount a module namespace (factories + free functions) under its module
/// name. Called once per module from the `#[wasm_bindgen(start)]` hook in
/// `lib.rs`.
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

/// Borrow the instance behind `handle` as `&dyn Any` and run `f` on it,
/// releasing the lock before returning. Generic over the closure so the
/// table never names a concrete type (open/closed): the CALLER downcasts to
/// the type it hosts. Used by a namespace factory that consumes another
/// hosted resource (e.g. `touchstone`/`fromData` reading a hosted
/// `Frequency`). `f` MUST NOT re-enter the registry (std Mutex is not
/// reentrant) — extract owned data out, then build/insert after the return.
pub fn with_any<R: 'static>(
    handle: u32,
    f: impl FnOnce(&dyn std::any::Any) -> R,
) -> Result<R, String> {
    let reg = registry().lock().unwrap();
    let resource = reg
        .instances
        .get(&handle)
        .ok_or_else(|| format!("unknown or dropped handle: {handle}"))?;
    Ok(f(resource.as_any()))
}

/// The single wasm entry: the verb-count-independent fixed template.
///
/// Number handle → instance dispatch; `method == "drop"` is intercepted here
/// because removing the table entry is the table's own operation, and it runs
/// the resource's Rust `Drop` directly with no JS object in between. String
/// handle → namespace dispatch. There is no sentinel value: a message says
/// whom it is calling.
// `Box<[JsValue]>` is the signature wasm-bindgen requires for a JS array
// argument; clippy's boxed_local lint cannot see that constraint.
#[allow(clippy::boxed_local)]
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

/// Read argument `i` as a required string.
pub(crate) fn arg_str(args: &[JsValue], i: usize) -> Result<String, JsValue> {
    args.get(i)
        .and_then(|v| v.as_string())
        .ok_or_else(|| js(format!("argument {i} must be a string")))
}

/// Read argument `i` as an optional string (`undefined`/`null` → `None`).
pub(crate) fn arg_opt_str(args: &[JsValue], i: usize) -> Option<String> {
    args.get(i).and_then(|v| v.as_string())
}

/// Build a plain JS object from `(key, value)` pairs — the `data()` shape
/// payload (`{values, shape}`) and the download payload (`{text, filename}`).
pub(crate) fn js_object(pairs: &[(&str, JsValue)]) -> JsValue {
    let obj = js_sys::Object::new();
    for (k, v) in pairs {
        let _ = js_sys::Reflect::set(&obj, &JsValue::from_str(k), v);
    }
    obj.into()
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Mutex;
    use std::sync::atomic::{AtomicUsize, Ordering};

    // The registry and the LIVE witness are process-global, so tests share
    // them: serialize to keep live_count assertions race-free.
    static TEST_LOCK: Mutex<()> = Mutex::new(());

    /// A resource type invented by the test itself — the crate has never
    /// heard of it, yet it hosts and drops unchanged. Counts live instances to
    /// witness that `remove` runs `Drop`. Its `call` is never invoked natively
    /// (it would build a `JsValue`, which aborts off-wasm); the worker
    /// roundtrip exercises dispatch.
    struct TestResource {
        #[allow(dead_code)]
        value: u32,
    }

    static TEST_LIVE: AtomicUsize = AtomicUsize::new(0);

    impl Resource for TestResource {
        fn as_any(&self) -> &dyn std::any::Any {
            self
        }

        fn call(&mut self, _method: &str, _args: &[JsValue]) -> Result<JsValue, JsValue> {
            Ok(JsValue::UNDEFINED)
        }
    }

    impl Drop for TestResource {
        fn drop(&mut self) {
            TEST_LIVE.fetch_sub(1, Ordering::SeqCst);
        }
    }

    #[test]
    fn insert_allocates_unique_handles_and_remove_runs_drop() {
        let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        TEST_LIVE.store(0, Ordering::SeqCst);
        let h1 = insert(Box::new(TestResource { value: 1 }));
        TEST_LIVE.fetch_add(1, Ordering::SeqCst);
        let h2 = insert(Box::new(TestResource { value: 2 }));
        TEST_LIVE.fetch_add(1, Ordering::SeqCst);
        assert_ne!(h1, h2, "one counter serves every resource type");
        remove(h1).expect("remove");
        assert_eq!(TEST_LIVE.load(Ordering::SeqCst), 1, "Drop ran on remove");
        remove(h2).unwrap();
        assert_eq!(TEST_LIVE.load(Ordering::SeqCst), 0);
    }

    #[test]
    fn touchstone_and_frequency_host_through_the_same_table() {
        let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        let freq = netwave::frequency::Frequency::from_f(
            vec![1e9, 2e9],
            netwave::frequency::FrequencyUnit::GHz,
        );
        let ts = netwave::touchstone::Touchstone::from_data(
            &freq,
            &[0.1, 0.2, 0.3, 0.4],
            &[50.0],
            netwave::touchstone::TouchstoneParameter::S,
            "",
            "",
        )
        .unwrap();
        let h_ts = insert(Box::new(ts));
        let h_freq = insert(Box::new(freq));
        assert_ne!(h_ts, h_freq, "one counter serves every resource type");
        remove(h_ts).unwrap();
        remove(h_freq).unwrap();
    }

    #[test]
    fn as_any_downcasts_hosted_frequency() {
        // `Resource::as_any` is the internal downcast the `fromData` namespace
        // arm uses to recover a hosted `Frequency` from the type-erased table
        // entry. Native-testable on the trait object directly (no wasm call).
        let f = netwave::frequency::Frequency::from_f(
            vec![1e9, 2e9],
            netwave::frequency::FrequencyUnit::GHz,
        );
        let resource: Box<dyn Resource> = Box::new(f);
        let down = resource
            .as_any()
            .downcast_ref::<netwave::frequency::Frequency>()
            .expect("downcast to Frequency");
        assert_eq!(down.npoints().unwrap(), 2);
        // A wrong-type downcast yields None, never a panic.
        assert!(
            resource
                .as_any()
                .downcast_ref::<std::collections::BTreeMap<u8, u8>>()
                .is_none()
        );
    }

    #[test]
    fn remove_runs_rust_drop_and_is_visible_in_live_count() {
        let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        let before = netwave::frequency::live_count();
        let h = insert(Box::new(netwave::frequency::Frequency::from_f(
            vec![1e9, 2e9, 3e9],
            netwave::frequency::FrequencyUnit::GHz,
        )));
        assert_eq!(netwave::frequency::live_count(), before + 1);
        remove(h).unwrap(); // remove -> Rust Drop runs now, not at GC
        assert_eq!(netwave::frequency::live_count(), before);
    }

    #[test]
    fn unknown_or_double_dropped_handle_errors() {
        let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        let h = insert(Box::new(netwave::frequency::Frequency::from_f(
            vec![1e9],
            netwave::frequency::FrequencyUnit::GHz,
        )));
        remove(h).unwrap();
        let err = remove(h).expect_err("second drop must report unknown");
        assert!(err.contains("unknown or dropped handle"), "{err}");
    }

    #[test]
    fn namespace_routing_resolves_known_and_rejects_unknown() {
        let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
        // lib.rs's #[wasm_bindgen(start)] registers these in a real wasm
        // build; under native cargo test the start hook never runs, so register
        // here to exercise the routing table itself (the returned fn pointers
        // are looked up, never called — calling them would build JsValue and
        // abort).
        register_namespace("touchstone", crate::touchstone_glue::call_namespace);
        register_namespace("frequency", crate::frequency_glue::call_namespace);
        assert!(namespace("touchstone").is_ok());
        assert!(namespace("frequency").is_ok());
        let err = namespace("circuit").expect_err("unregistered namespace");
        assert!(err.contains("unknown namespace"), "{err}");
    }

    #[test]
    fn frequency_units_stay_free_of_state() {
        // Free functions unchanged by the table landing: no handle involved.
        assert!(!netwave::frequency::frequency_units().is_empty());
    }
}
