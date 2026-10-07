//! Memory-lifecycle witness for the core `Frequency`: dropping an instance
//! must decrement the live allocation counter. One test per binary so the
//! global `LIVE` counter has no intra-binary contention.

use netwave::frequency::{Frequency, FrequencyUnit, live_count};

#[test]
fn from_f_bumps_and_drop_restores_live_count() {
    let base = live_count();
    {
        let f = Frequency::from_f(vec![1e9, 2e9, 3e9], FrequencyUnit::GHz);
        assert_eq!(f.npoints(), 3);
        assert_eq!(live_count(), base + 1);
    } // `f` dropped here -> RAII Drop -> LIVE -1
    assert_eq!(live_count(), base);
}
