//! Memory-lifecycle witness for the core `Frequency`: dropping an instance
//! must decrement the live allocation counter. One test per binary so the
//! global `LIVE` counter has no intra-binary contention.

use netwave::frequency::{Frequency, FrequencyUnit, live_count};

#[test]
fn from_f_bumps_and_drop_restores_live_count() {
    let base = live_count();
    {
        let f = Frequency::from_f(vec![1e9, 2e9, 3e9], FrequencyUnit::GHz);
        assert_eq!(f.npoints().unwrap(), 3);
        assert_eq!(live_count(), base + 1);
    } // `f` dropped here -> RAII Drop -> LIVE -1
    assert_eq!(live_count(), base);
}

// Manual `drop()` semantics run inside one test so the global LIVE counter
// has no intra-binary contention (see module doc).
#[test]
fn manual_drop_frees_idempotently_and_decrements_once() {
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
