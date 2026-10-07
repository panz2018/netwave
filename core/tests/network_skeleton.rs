//! Skeleton contract for the core `Network`: construction, element read,
//! deterministic idempotent release, and post-release access errors.

use netwave::network::Network;

#[test]
fn from_f64_reads_back_by_interleaved_index() {
    // 1 freq, 1 port: one complex (re=7, im=-7).
    let net = Network::from_f64(1, 1, vec![7.0, -7.0]);
    assert_eq!(net.nfreq(), 1);
    assert_eq!(net.nports(), 1);
    assert_eq!(net.read_element(0).unwrap(), 7.0);
    assert_eq!(net.read_element(1).unwrap(), -7.0);
}

#[test]
fn fill_pattern_matches_closed_form() {
    // Expected values computed independently from the documented formula
    // (re = f*100 + p*10 + q, im = -re) — never from the function output.
    let net = Network::fill_pattern(2, 2);
    assert_eq!(net.nfreq(), 2);
    assert_eq!(net.nports(), 2);
    // f=1, p=0, q=1 -> re = 100 + 0 + 1 = 101; interleaved element index:
    // ((f*nports + p)*nports + q)*2 + 0.
    let (f, p, q) = (1usize, 0usize, 1usize);
    let idx = ((f * net.nports() + p) * net.nports() + q) * 2;
    assert_eq!(net.read_element(idx).unwrap(), 101.0);
    assert_eq!(net.read_element(idx + 1).unwrap(), -101.0);
}

#[test]
fn drop_frees_and_post_drop_read_errors_idempotently() {
    let mut net = Network::from_f64(1, 1, vec![1.0, -1.0]);
    assert_eq!(net.read_element(0).unwrap(), 1.0);

    net.drop();
    assert!(
        net.read_element(0).is_err(),
        "read after drop must error, not read freed data"
    );

    net.drop(); // idempotent: no panic, still dropped
    assert!(net.read_element(0).is_err());
}

#[test]
#[should_panic]
fn from_f64_rejects_wrong_length() {
    Network::from_f64(1, 1, vec![1.0]); // missing the imaginary part
}
