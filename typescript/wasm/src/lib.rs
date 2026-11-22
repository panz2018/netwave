//! netwave wasm binding (wasm-bindgen).
//!
//! The glue crate is intentionally empty: every wasm entry lives in core
//! (`frequency.rs` / `touchstone.rs` / `resources.rs`, cfg-gated browser) and
//! wasm-bindgen exports the whole crate graph into this binary. Handles are
//! plain `u32` crossing the boundary; no wasm class floats up to JS, so
//! wasm-bindgen's generated `free()` has no call site anywhere — the single
//! reclamation command is core `drop(handle)` → `remove` → Rust `Drop`.

// Force-link core: its `#[wasm_bindgen]` entries are the entire wasm
// surface, and an unreferenced crate is not linked into the cdylib. This
// single line is the glue crate's whole job.
extern crate netwave;

// Coverage dump entry points for the wasm rust coverage chain, compiled only
// under the `coverage` feature so production `build:wasm` exports none of
// them. minicov keeps the counters in this instance's linear memory and has
// no atexit, so the test harness calls `__cov_dump` from the worker context,
// then reads the captured profraw back out via `__cov_ptr`/`__cov_len`.
#[cfg(feature = "coverage")]
mod __cov {
    use std::cell::UnsafeCell;

    struct Buf(UnsafeCell<Vec<u8>>);
    // Single-threaded wasm instance: the buffer is only ever touched from one
    // worker, so sharing it across threads is sound here.
    unsafe impl Sync for Buf {}
    static BUF: Buf = Buf(UnsafeCell::new(Vec::new()));

    /// Capture the current coverage counters into the static buffer.
    #[wasm_bindgen::prelude::wasm_bindgen]
    pub fn __cov_dump() {
        unsafe {
            let b = &mut *BUF.0.get();
            b.clear();
            minicov::capture_coverage(b).unwrap();
        }
    }

    /// Pointer to the captured profraw bytes in linear memory (valid after
    /// `__cov_dump`).
    #[wasm_bindgen::prelude::wasm_bindgen]
    pub fn __cov_ptr() -> *const u8 {
        unsafe { (*BUF.0.get()).as_ptr() }
    }

    /// Length in bytes of the captured profraw (valid after `__cov_dump`).
    #[wasm_bindgen::prelude::wasm_bindgen]
    pub fn __cov_len() -> usize {
        unsafe { (*BUF.0.get()).len() }
    }

    /// The minicov module signature — a value unique to this load module, so
    /// the harness names each worker's profraw file with it and concurrent
    /// workers never overwrite one another before `llvm-profdata merge`.
    #[wasm_bindgen::prelude::wasm_bindgen]
    pub fn __cov_signature() -> u64 {
        minicov::module_signature()
    }

    /// Drive the core defensive arms that JS dispatch cannot reach, so they
    /// count in this instrumented binary. The browser worker's `drop` removes
    /// the table entry, so a post-drop call fails at the registry lookup and
    /// never enters core's `if self.dropped` guards or the dispatch `.map_err`
    /// arms — yet those lines are shared core logic that native reaches by
    /// calling the inherent methods directly. This entry reproduces that from
    /// the public API: build a sweep, drop it in place (the object survives,
    /// only its data is freed), then call every getter and the namespace copy
    /// path so each guard and error arm executes. Coverage-chain only;
    /// production `build:wasm` compiles none of this.
    #[wasm_bindgen::prelude::wasm_bindgen]
    pub fn __cov_drive() {
        use netwave::frequency::{Frequency, FrequencyUnit, WavelengthUnit};
        use netwave::resources::{insert, instance_call};

        // A dropped-but-still-owned sweep: every getter takes its
        // `if self.dropped { return Err(Dropped) }` arm, and formatting the
        // returned Dropped / the sweep exercises their Display/Debug impls.
        let mut f = Frequency::from_f(vec![1e9, 2e9], FrequencyUnit::GHz);
        // A live copy exercises the success path (LIVE bump + new instance);
        // then drop so every getter takes its `if self.dropped` arm.
        let _ = f.copy().map(|c| c.npoints());
        f.drop();
        // Second drop: the `if !self.dropped` guard takes its false path
        // (already freed), so the skip arm counts too.
        f.drop();
        let _ = f.npoints().map_err(|e| e.to_string());
        let _ = f.f().map_err(|e| e.to_string());
        let _ = f.f_scaled().map_err(|e| e.to_string());
        let _ = f.w().map_err(|e| e.to_string());
        let _ = f.unit().map_err(|e| e.to_string());
        let _ = f
            .wavelength(WavelengthUnit::m, 1.0)
            .map_err(|e| e.to_string());
        let _ = f.copy().map_err(|e| e.to_string());
        let _ = format!("{f}");
        let _ = format!("{f:?}");

        // The same dropped sweep hosted in the table: instance dispatch reads
        // it, the getter returns Err, and each `.map_err(js)` arm fires.
        let handle = insert(Box::new(f));
        for method in ["npoints", "f", "fScaled", "w", "unit"] {
            let _ = instance_call(handle, method, &[]);
        }
        // wavelength needs both args (unit ordinal + n) to reach the dropped
        // getter and its `.map_err` arm; a missing n short-circuits earlier.
        let wl_args = js_sys::Array::of2(
            &wasm_bindgen::JsValue::from_f64(0.0),
            &wasm_bindgen::JsValue::from_f64(1.0),
        );
        let _ = instance_call(handle, "wavelength", &wl_args.to_vec());

        // The namespace `copy` factory reads the source through instance_call;
        // a dropped source makes its `.map_err(js)?` arm fire.
        let _ = netwave::frequency::call_namespace(
            "copy",
            &[wasm_bindgen::JsValue::from_f64(handle as f64)],
        );

        // The private convert_to_s/s_to_domain dispatch-violation arms: no
        // public API passes S to them, so core's cov-drive entry calls them
        // directly (the wasm binary cannot run core's crate-internal tests).
        netwave::touchstone::drive_dispatch_violations();
    }
}
