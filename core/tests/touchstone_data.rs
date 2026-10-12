//! Data-plane contract: domain shortcut properties (z/y/g/h computed from
//! stored S), the unified accessor `data(parameter, format)` over all 20
//! combinations, MA/DB closed-form semantics, and the pure-data constructor.

use netwave::touchstone::{Touchstone, TouchstoneError, TouchstoneFormat, TouchstoneParameter};

const TOL: f64 = 1e-12;

fn approx_eq(a: &[f64], b: &[f64], tol: f64) {
    assert_eq!(a.len(), b.len(), "length mismatch: {a:?} vs {b:?}");
    for (x, y) in a.iter().zip(b) {
        assert!(
            (x - y).abs() <= tol * y.abs().max(1.0),
            "value mismatch: {a:?} vs {b:?}"
        );
    }
}

/// 1-port S = 0.5+0.25j, z0 = 50.
fn one_port_s() -> Touchstone {
    let text = "# GHZ S RI R 50\n1.0 0.5 0.25";
    Touchstone::from_text(text, Some(1), None).unwrap()
}

/// 2-port diagonal S = diag(0.5, 0.25), z0 = 50.
fn two_port_s() -> Touchstone {
    let text = "# GHZ S RI R 50\n1.0 0.5 0 0 0 0 0 0.25 0";
    Touchstone::from_text(text, Some(2), None).unwrap()
}

#[test]
fn one_port_z_property_from_s() {
    // Z = z0 (1+s)(1-s)^-1 = 50 * (1.5+0.25j)/(0.5-0.25j).
    // (1.5+0.25j)(0.5+0.25j) = 0.75-0.0625 + j(0.375+0.125) = 0.6875+0.5j
    // |0.5-0.25j|^2 = 0.3125
    // Z = 50*(0.6875+0.5j)/0.3125 = 110 + 80j
    let ts = one_port_s();
    approx_eq(&ts.z(), &[110.0, 80.0], TOL);
}

#[test]
fn one_port_y_property_from_s() {
    // Y = (1/s) / z0... Y = (1-s)(1+s)^-1 / z0 = ((0.5-0.25j)/(1.5+0.25j))/50
    // (0.5-0.25j)(1.5-0.25j) = 0.75-0.0625 - j(0.125+0.375) = 0.6875-0.5j
    // |1.5+0.25j|^2 = 2.3125
    // Y = (0.6875-0.5j)/(2.3125*50) = 0.0059537037037037036-0.004320987654320988j
    let ts = one_port_s();
    let re = 0.6875 / (2.3125 * 50.0);
    let im = -0.5 / (2.3125 * 50.0);
    approx_eq(&ts.y(), &[re, im], TOL);
}

#[test]
fn two_port_z_property_diagonal() {
    // Diagonal S -> diagonal Z: Z_ii = z0(1+s_ii)/(1-s_ii).
    // s00=0.5 -> Z00 = 50*1.5/0.5 = 150; s11=0.25 -> Z11 = 50*1.25/0.75 = 83.333...
    let ts = two_port_s();
    approx_eq(
        &ts.z(),
        &[150.0, 0.0, 0.0, 0.0, 0.0, 0.0, 50.0 * 1.25 / 0.75, 0.0],
        TOL,
    );
}

#[test]
fn g_h_non_two_port_property_errors() {
    let ts = two_port_s();
    assert!(ts.g().is_ok());
    assert!(ts.h().is_ok());
    let text = "# GHZ S RI R 50\n1.0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0";
    let ts3 = Touchstone::from_text(text, Some(3), None).unwrap();
    assert!(ts3.g().is_err());
    assert!(ts3.h().is_err());
}

#[test]
fn data_default_returns_s_body() {
    let ts = one_port_s();
    // Default (S, RI) returns the stored data itself (same pointer).
    let d = ts
        .data(TouchstoneParameter::S, TouchstoneFormat::RI)
        .unwrap();
    assert_eq!(d.as_ptr(), ts.s().as_ptr());
}

#[test]
fn data_ma_roundtrip_matches_stored_complex() {
    // MA pairs (mag, deg) reconstruct the stored re/im exactly.
    let ts = one_port_s();
    let ma = ts
        .data(TouchstoneParameter::S, TouchstoneFormat::MA)
        .unwrap();
    assert_eq!(ma.len(), 2);
    let mag = (0.5f64 * 0.5 + 0.25 * 0.25).sqrt();
    let deg = 0.25f64.atan2(0.5).to_degrees();
    approx_eq(&ma, &[mag, deg], TOL);
    // Closed-form inverse: mag = 10^(db/20).
    let db = ts
        .data(TouchstoneParameter::S, TouchstoneFormat::DB)
        .unwrap();
    let db_val = 20.0 * mag.log10();
    approx_eq(&db, &[db_val, deg], TOL);
}

#[test]
fn data_all_twenty_combinations_shapes() {
    let ts = two_port_s();
    for p in [
        TouchstoneParameter::S,
        TouchstoneParameter::Y,
        TouchstoneParameter::Z,
        TouchstoneParameter::G,
        TouchstoneParameter::H,
    ] {
        for f in [
            TouchstoneFormat::RI,
            TouchstoneFormat::MA,
            TouchstoneFormat::DB,
        ] {
            let d = ts.data(p, f).unwrap();
            assert_eq!(d.len(), 8, "2-port: 4 entries x 2");
        }
    }
}

#[test]
fn data_z_matches_z_property() {
    let ts = two_port_s();
    approx_eq(
        &ts.data(TouchstoneParameter::Z, TouchstoneFormat::RI)
            .unwrap(),
        &ts.z(),
        TOL,
    );
}

// ---- pure-data factory ----

#[test]
fn from_data_writes_through_to_derived_readback() {
    // Zero-copy proof inside core: `s_mut` writes the master buffer in
    // place, and `data(S, MA)` — computed fresh from the live `s` —
    // reflects the write. Converting MA back to RI must equal what was
    // written (independent verification channel, stronger than re-reading
    // `s`: it also proves the computation reads through the same memory).
    let f =
        netwave::frequency::Frequency::from_f(vec![1.0e9], netwave::frequency::FrequencyUnit::Hz);
    let mut ts =
        Touchstone::from_data(&f, &[0.5, 0.25], &[50.0], TouchstoneParameter::S, "", "").unwrap();
    ts.s_mut().unwrap()[0] = 0.75;
    let ma = ts
        .data(TouchstoneParameter::S, TouchstoneFormat::MA)
        .unwrap();
    let re = ma[0] * ma[1].to_radians().cos();
    let im = ma[0] * ma[1].to_radians().sin();
    approx_eq(&[re, im], &[0.75, 0.25], TOL);
    // The master buffer itself holds the write (same memory, no copy).
    approx_eq(ts.s(), &[0.75, 0.25], TOL);
}

#[test]
fn from_data_data_ri_borrows_master_buffer() {
    // `(S, RI)` must hand back the stored buffer itself, not a copy —
    // the zero-copy accessor contract the bindings build on.
    let f =
        netwave::frequency::Frequency::from_f(vec![1.0e9], netwave::frequency::FrequencyUnit::Hz);
    let ts =
        Touchstone::from_data(&f, &[0.5, 0.25], &[50.0], TouchstoneParameter::S, "", "").unwrap();
    let d = ts
        .data(TouchstoneParameter::S, TouchstoneFormat::RI)
        .unwrap();
    assert_eq!(d.as_ptr(), ts.s().as_ptr());
}

#[test]
fn s_arc_shares_master_buffer_and_blocks_s_mut_until_dropped() {
    // `s_arc` hands the node binding an `Arc` clone whose finalizer keeps
    // the buffer alive: the clone must point at the very same memory, and
    // while it is live `s_mut` must refuse in-place writes (BufferShared).
    let f =
        netwave::frequency::Frequency::from_f(vec![1.0e9], netwave::frequency::FrequencyUnit::Hz);
    let mut ts =
        Touchstone::from_data(&f, &[0.5, 0.25], &[50.0], TouchstoneParameter::S, "", "").unwrap();
    let view = ts.s_arc();
    assert_eq!(
        view.as_ptr(),
        ts.s().as_ptr(),
        "arc clone must alias master"
    );
    assert_eq!(&*view, ts.s());
    let err = ts.s_mut().unwrap_err();
    assert!(matches!(err, TouchstoneError::BufferShared), "{err}");
    drop(view);
    // Unique owner again: in-place writes are allowed.
    ts.s_mut().unwrap()[0] = 0.75;
    approx_eq(ts.s(), &[0.75, 0.25], TOL);
}

#[test]
fn constructor_validates_dimension_interleaved() {
    // frequency 2 points, nports 2: data must be 2*4*2 = 16.
    let f = netwave::frequency::Frequency::from_f(
        vec![1.0e9, 2.0e9],
        netwave::frequency::FrequencyUnit::Hz,
    );
    let err = Touchstone::from_data(
        &f,
        &[0.0; 15],
        &[50.0, 50.0],
        TouchstoneParameter::S,
        "",
        "",
    )
    .unwrap_err();
    let msg = err.to_string();
    assert!(
        msg.contains('1') && msg.contains("15"),
        "error must quote data_len 15, got: {msg}"
    );
}

#[test]
fn constructor_validates_z0_shape() {
    let f =
        netwave::frequency::Frequency::from_f(vec![1.0e9], netwave::frequency::FrequencyUnit::Hz);
    let err = Touchstone::from_data(
        &f,
        &[0.0; 8],
        &[50.0, 45.0, 50.0],
        TouchstoneParameter::S,
        "",
        "",
    )
    .unwrap_err();
    assert!(err.to_string().contains('3'), "must quote z0 len 3: {err}");
}

#[test]
fn constructor_derives_version_from_z0_values() {
    let f =
        netwave::frequency::Frequency::from_f(vec![1.0e9], netwave::frequency::FrequencyUnit::Hz);
    // all-equal z0 -> "1.0"
    let ts = Touchstone::from_data(&f, &[0.0; 8], &[50.0, 50.0], TouchstoneParameter::S, "", "")
        .unwrap();
    assert_eq!(ts.version(), "1.0");
    // differing z0 -> "1.1"
    let ts = Touchstone::from_data(&f, &[0.0; 8], &[50.0, 45.0], TouchstoneParameter::S, "", "")
        .unwrap();
    assert_eq!(ts.version(), "1.1");
}

#[test]
fn constructor_converts_non_s_domain() {
    // Z data = [[100]] 1-port -> S = (100-50)/(100+50) = 1/3.
    let f =
        netwave::frequency::Frequency::from_f(vec![1.0e9], netwave::frequency::FrequencyUnit::Hz);
    let ts =
        Touchstone::from_data(&f, &[100.0, 0.0], &[50.0], TouchstoneParameter::Z, "", "").unwrap();
    approx_eq(ts.s(), &[1.0 / 3.0, 0.0], TOL);
    assert_eq!(ts.parameter().as_ref(), "Z");
}

#[test]
fn constructor_rejects_duplicate_frequency() {
    let f = netwave::frequency::Frequency::from_f(
        vec![1.0e9, 1.0e9],
        netwave::frequency::FrequencyUnit::Hz,
    );
    let err =
        Touchstone::from_data(&f, &[0.0; 4], &[50.0], TouchstoneParameter::S, "", "").unwrap_err();
    assert!(err.to_string().contains('1'), "must quote dup freq: {err}");
}

#[test]
fn constructor_sorts_shuffled_frequency() {
    let f = netwave::frequency::Frequency::from_f(
        vec![2.0e9, 1.0e9],
        netwave::frequency::FrequencyUnit::Hz,
    );
    // point at 2GHz has re=0.1, at 1GHz re=0.2
    let ts = Touchstone::from_data(
        &f,
        &[0.1, 0.0, 0.2, 0.0],
        &[50.0],
        TouchstoneParameter::S,
        "",
        "",
    )
    .unwrap();
    assert_eq!(ts.f(), vec![1.0e9, 2.0e9]);
    assert_eq!(ts.s(), &[0.2, 0.0, 0.1, 0.0]);
}

#[test]
fn constructor_data_len_not_multiple_of_npoints_errors() {
    // 1 frequency point needs an even data length (re/im pairs); 3 is not.
    let f =
        netwave::frequency::Frequency::from_f(vec![1.0e9], netwave::frequency::FrequencyUnit::Hz);
    let err =
        Touchstone::from_data(&f, &[0.0; 3], &[50.0], TouchstoneParameter::S, "", "").unwrap_err();
    assert!(
        err.to_string().contains('3'),
        "must quote data_len 3: {err}"
    );
}

#[test]
fn constructor_rejects_gh_on_non_two_port() {
    // 1-port data with a G parameter: G/H are 2-port only.
    let f =
        netwave::frequency::Frequency::from_f(vec![1.0e9], netwave::frequency::FrequencyUnit::Hz);
    let err =
        Touchstone::from_data(&f, &[0.0; 2], &[50.0], TouchstoneParameter::G, "", "").unwrap_err();
    assert!(
        err.to_string().contains('G'),
        "must quote the offending domain: {err}"
    );
}

#[test]
fn constructor_rejects_non_square_cells() {
    // 1 frequency point, data length 6 -> 3 cells, not a perfect square
    // (sqrt rounds to 2, 2² = 4 ≠ 3). The error quotes data_len 6 and
    // the rounded nports² 4.
    let f =
        netwave::frequency::Frequency::from_f(vec![1.0e9], netwave::frequency::FrequencyUnit::Hz);
    let err =
        Touchstone::from_data(&f, &[0.0; 6], &[50.0], TouchstoneParameter::S, "", "").unwrap_err();
    let msg = err.to_string();
    assert!(
        msg.contains('6') && msg.contains('4'),
        "must quote data_len 6 and rounded nports² 4: {msg}"
    );
}

#[test]
fn data_gh_on_non_two_port_errors() {
    // The unified accessor reaches the same G/H port guard as the
    // shortcut properties.
    let ts = one_port_s();
    let err = ts
        .data(TouchstoneParameter::G, TouchstoneFormat::RI)
        .unwrap_err();
    assert!(
        err.to_string().contains('G'),
        "must quote the offending domain: {err}"
    );
}
