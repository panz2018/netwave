//! Memory-lifecycle witness for the core `Frequency`: dropping an instance
//! must decrement the live allocation counter. `LIVE` is process-global and
//! cargo runs tests of one binary on parallel threads, so both tests take
//! `TEST_LOCK`: without it a concurrent sibling's live instance makes
//! `live_count()` read `base + 2` where `base + 1` is asserted.

use std::sync::{Mutex, MutexGuard, OnceLock};

use netwave::frequency::{Frequency, FrequencyUnit, live_count};

/// Serializes the tests in this binary against the global `LIVE` counter.
fn lock_test() -> MutexGuard<'static, ()> {
    static LOCK: OnceLock<Mutex<()>> = OnceLock::new();
    LOCK.get_or_init(|| Mutex::new(()))
        .lock()
        .unwrap_or_else(|e| e.into_inner())
}

#[test]
fn from_f_bumps_and_drop_restores_live_count() {
    let _guard = lock_test();
    let base = live_count();
    {
        let f = Frequency::from_f(vec![1e9, 2e9, 3e9], FrequencyUnit::GHz);
        assert_eq!(f.npoints().unwrap(), 3);
        assert_eq!(live_count(), base + 1);
    } // `f` dropped here -> RAII Drop -> LIVE -1
    assert_eq!(live_count(), base);
}

// Manual `drop()` semantics run inside one test so the witness assertions see
// a single instance's lifecycle (the `TEST_LOCK` serializes against siblings).
#[test]
fn manual_drop_frees_idempotently_and_decrements_once() {
    let _guard = lock_test();
    let base = live_count();
    let mut f = Frequency::from_f(vec![1e9, 2e9, 3e9], FrequencyUnit::GHz);
    assert_eq!(live_count(), base + 1);

    f.drop();
    assert_eq!(
        f.npoints(),
        Err(netwave::Dropped),
        "post-drop access must error, not report 0"
    );
    assert_eq!(live_count(), base, "drop decrements the witness");

    f.drop(); // idempotent: no error, no second decrement
    assert_eq!(live_count(), base, "second drop must not re-decrement");

    drop(f); // RAII path after manual drop: still no double-decrement
    assert_eq!(live_count(), base, "RAII after manual drop is a no-op");
}
