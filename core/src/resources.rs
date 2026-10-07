//! Browser-only handle table: the single resource registry inside wasm.
//!
//! The resident worker is the single data authority (ironclad rule 8), so
//! the handle table lives here in core — worker JS keeps zero state and
//! every command is a mechanical forward to these entries (ironclad rule 9
//! exemption: cmd names are the camelCase of these snake names).
//!
//! The table is **type-erased** (`Box<dyn Any + Send>` — Rust's generic
//! `T`): it names no resource type at all, only `insert<T>`/`with<T>`/
//! `remove`. Each resource type owns its own `#[wasm_bindgen]` entries in
//! its own module (`network.rs`, `frequency.rs`, …) and registers itself
//! through these generics, so adding a future resource (Circuit, …) touches
//! only that new module — this file never changes. Handles are globally
//! unique (one counter), and `drop(handle)` removes the entry, running the
//! resource's Rust `Drop` directly (RAII) — no wasm class floats up to JS.
//!
//! Structure: the table logic is plain Rust (natively testable under
//! `--features browser`); the `#[wasm_bindgen]` `drop` below is a thin
//! adapter that only converts types. wasm_bindgen functions compile on the
//! host but abort when *called* there, so native tests exercise the pure
//! generics and the worker roundtrip exercises the adapter.
//!
//! Compiled only under the browser guard (`browser`, not `node`, not
//! `coverage` — the workspace clippy merge must not pull wasm glue into a
//! native build); node/Python hold objects directly and never see a handle
//! table.

use std::any::Any;
use std::collections::BTreeMap;
use std::sync::{Mutex, OnceLock};

use wasm_bindgen::prelude::*;

/// The single handle table plus its monotonic counter. Type-erased: the
/// map values carry no type name, so this module compiles unchanged no
/// matter how many resource types exist.
struct Registry {
    table: BTreeMap<u32, Box<dyn Any + Send>>,
    next_handle: u32,
}

impl Registry {
    fn new() -> Self {
        Self {
            table: BTreeMap::new(),
            next_handle: 1,
        }
    }

    /// Allocate the next handle and weld the resource in (registration is
    /// part of the factory insert — there is no separate register fn).
    fn insert<T: Any + Send>(&mut self, resource: T) -> u32 {
        let handle = self.next_handle;
        self.next_handle += 1;
        self.table.insert(handle, Box::new(resource));
        handle
    }

    /// Remove a handle, running its `Drop` immediately. A second `drop` of
    /// the same handle reports unknown (the Rust `Drop` already ran).
    /// Errors are plain `String` so the logic is testable off-wasm.
    fn remove(&mut self, handle: u32) -> Result<(), String> {
        match self.table.remove(&handle) {
            Some(_) => Ok(()),
            None => Err(format!("unknown or dropped handle: {handle}")),
        }
    }

    /// Borrow the resource as `T` and run `f` on it. A handle holding a
    /// different type reports the mismatch (downcast failure).
    fn with<T: Any, R>(&self, handle: u32, f: impl FnOnce(&T) -> R) -> Result<R, String> {
        let resource = self
            .table
            .get(&handle)
            .ok_or_else(|| format!("unknown or dropped handle: {handle}"))?;
        let typed = resource
            .downcast_ref::<T>()
            .ok_or_else(|| format!("handle {handle} holds a different resource type"))?;
        Ok(f(typed))
    }
}

static REGISTRY: OnceLock<Mutex<Registry>> = OnceLock::new();

fn registry() -> &'static Mutex<Registry> {
    REGISTRY.get_or_init(|| Mutex::new(Registry::new()))
}

/// Host a resource and return its globally unique handle. Generic over any
/// `'static + Send` type — the table never learns what it is holding, so
/// new resource types need no change here.
pub fn insert<T: Any + Send>(resource: T) -> u32 {
    registry().lock().unwrap().insert(resource)
}

/// Borrow the resource behind `handle` as `T` and run `f` on it.
pub fn with<T: Any, R>(handle: u32, f: impl FnOnce(&T) -> R) -> Result<R, String> {
    registry().lock().unwrap().with(handle, f)
}

/// The single reclamation: remove the handle, which runs the resource's
/// Rust `Drop` right now (deterministic, GC-independent).
pub fn remove(handle: u32) -> Result<(), String> {
    registry().lock().unwrap().remove(handle)
}

// ---------------------------------------------------------------------------
// wasm handle entries. `drop` is the only type-free entry every resource
// shares; resource-specific entries live in their own modules and call
// the generics above (this file never names a resource type).
// ---------------------------------------------------------------------------

/// The single reclamation command: remove the handle, which runs the
/// resource's Rust `Drop` right now (deterministic, GC-independent).
#[wasm_bindgen]
pub fn drop(handle: u32) -> Result<(), JsValue> {
    remove(handle).map_err(|e| JsValue::from_str(&e))
}
