//! Browser handle-table tests (core `resources` module).
//!
//! Run with `cargo test -p netwave --features browser`. The table is a
//! generic dispatch (`insert`/`remove`/`namespace`), so the table logic is
//! natively callable. The `#[wasm_bindgen]` `call` adapter and the
//! per-resource `match`es build `JsValue` values, which abort when *called*
//! off-wasm (wasm-bindgen stubs) — argument unpacking and real method
//! dispatch are covered by the worker roundtrip tests instead.
//!
//! `TestResource` is defined HERE (not in core) to prove the open/closed
//! property: a brand-new resource type hosts and drops through the same
//! generic table with zero changes to `resources.rs`.

// Same guard as the module: `cargo clippy --workspace` merges node and
// browser onto one netwave build, where the module is cfg'd out.
#![cfg(all(feature = "browser", not(feature = "node"), not(coverage)))]

use std::sync::Mutex;
use std::sync::atomic::{AtomicUsize, Ordering};

use netwave::frequency::{Frequency, FrequencyUnit, frequency_units, live_count};
use netwave::network::Network;
use netwave::resources::{Resource, insert, namespace, register_namespace, remove};
use wasm_bindgen::prelude::*;

// The registry and the LIVE witness are process-global, so tests share
// them: serialize to keep live_count assertions race-free.
static TEST_LOCK: Mutex<()> = Mutex::new(());

/// A resource type invented by the test itself — core has never heard of
/// it, yet it hosts and drops unchanged. Counts live instances to witness
/// that `remove` runs `Drop`. Its `call` is never invoked natively (it
/// would build a `JsValue`, which aborts off-wasm); the worker roundtrip
/// exercises dispatch.
struct TestResource {
    #[allow(dead_code)]
    value: u32,
}

static TEST_LIVE: AtomicUsize = AtomicUsize::new(0);

impl Resource for TestResource {
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
fn network_and_frequency_host_through_the_same_table() {
    let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
    // 2 freq x 2 ports x 2 ports x 2 (re/im) = 16 f64
    let data: Vec<f64> = (0..16).map(|i| i as f64).collect();
    let h_net = insert(Box::new(Network::from_f64(2, 2, data)));
    let h_freq = insert(Box::new(Frequency::from_f(vec![1e9, 2e9], FrequencyUnit::GHz)));
    assert_ne!(h_net, h_freq, "one counter serves every resource type");
    remove(h_net).unwrap();
    remove(h_freq).unwrap();
}

#[test]
fn remove_runs_rust_drop_and_is_visible_in_live_count() {
    let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
    let before = live_count();
    let h = insert(Box::new(Frequency::from_f(
        vec![1e9, 2e9, 3e9],
        FrequencyUnit::GHz,
    )));
    assert_eq!(live_count(), before + 1);
    remove(h).unwrap(); // remove -> Rust Drop runs now, not at GC
    assert_eq!(live_count(), before);
}

#[test]
fn unknown_or_double_dropped_handle_errors() {
    let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
    let h = insert(Box::new(Network::fill_pattern(1, 1)));
    remove(h).unwrap();
    let err = remove(h).expect_err("second drop must report unknown");
    assert!(err.contains("unknown or dropped handle"), "{err}");
}

#[test]
fn namespace_routing_resolves_known_and_rejects_unknown() {
    let _guard = TEST_LOCK.lock().unwrap_or_else(|e| e.into_inner());
    // lib.rs's #[wasm_bindgen(start)] registers these in a real wasm build;
    // under native cargo test the start hook never runs, so register here to
    // exercise the routing table itself (the returned fn pointers are looked
    // up, never called — calling them would build JsValue and abort).
    register_namespace("network", netwave::network::call_namespace);
    register_namespace("frequency", netwave::frequency::call_namespace);
    assert!(namespace("network").is_ok());
    assert!(namespace("frequency").is_ok());
    let err = namespace("circuit").expect_err("unregistered namespace");
    assert!(err.contains("unknown namespace"), "{err}");
}

#[test]
fn frequency_units_stay_free_of_state() {
    // Free functions unchanged by the table landing: no handle involved.
    assert!(!frequency_units().is_empty());
}
