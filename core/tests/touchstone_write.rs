//! Write-out contract: `write_path` four shapes, `write_touchstone`
//! roundtrip bit-exactness, stored-version metadata preservation, and
//! native `write_file` landing.

use netwave::touchstone::{Touchstone, TouchstoneFormat, TouchstoneParameter};

fn two_port_z() -> Touchstone {
    let text = "# GHZ Z RI R 50\n1.0 50 0 0 0 0 0 50 0";
    Touchstone::from_text(text, Some(2), Some("/tmp/dir/x.s2p")).unwrap()
}

#[test]
fn write_two_port_emits_legacy_order() {
    // Internal storage is row-major (S11, S12, S21, S22); v1.x 2-port
    // files must be written in legacy order (S11, S21, S12, S22).
    // Construct with non-symmetric off-diagonals: S12=5+6j, S21=3+4j.
    let text = "# GHZ S RI R 50\n1.0 1 2 3 4 5 6 7 8";
    let ts = Touchstone::from_text(text, Some(2), None).unwrap();
    // Row-major storage: S11=1+2j, S12=5+6j, S21=3+4j, S22=7+8j.
    assert_eq!(ts.s(), vec![1.0, 2.0, 5.0, 6.0, 3.0, 4.0, 7.0, 8.0]);
    let out = ts
        .write_touchstone(TouchstoneParameter::S, TouchstoneFormat::RI)
        .unwrap();
    // Written data row must be legacy order: S11, S21, S12, S22
    // (frequency formats shortest: "1" not "1.0").
    assert!(
        out.contains("1 1 2 3 4 5 6 7 8"),
        "written 2-port row must be legacy order: {out}"
    );
    // Roundtrip: re-parsing the written text restores row-major storage.
    let back = Touchstone::from_text(&out, Some(2), None).unwrap();
    assert_eq!(ts.s(), back.s(), "roundtrip must be bit-exact");
}

#[test]
fn write_touchstone_roundtrip_bit_exact() {
    let ts = two_port_z();
    let text = ts
        .write_touchstone(TouchstoneParameter::Z, TouchstoneFormat::RI)
        .unwrap();
    let back = Touchstone::from_text(&text, Some(2), None).unwrap();
    assert_eq!(ts.s(), back.s(), "roundtrip must be bit-exact");
    assert_eq!(ts.z0(), back.z0());
    assert_eq!(ts.parameter(), back.parameter());
    assert_eq!(ts.version(), back.version());
}

#[test]
fn write_touchstone_ma_db_roundtrip_within_tol() {
    // RI roundtrips bit-exact (shortest-roundtrip decimal); MA/DB pass
    // through polar<->rectangular transcendental functions, so the bound
    // is the manifest core_tol (spec scenario "写出往返一致").
    const TOL: f64 = 1e-12;
    let text = "# GHZ S MA R 50\n1.0 0.5 -30 0.1 170 0.1 170 0.8 -45";
    let ts = Touchstone::from_text(text, Some(2), None).unwrap();
    let ri = ts
        .write_touchstone(TouchstoneParameter::S, TouchstoneFormat::RI)
        .unwrap();
    let back = Touchstone::from_text(&ri, Some(2), None).unwrap();
    assert_eq!(ts.s(), back.s(), "RI roundtrip must be bit-exact");
    for f in [TouchstoneFormat::MA, TouchstoneFormat::DB] {
        let out = ts.write_touchstone(TouchstoneParameter::S, f).unwrap();
        let back = Touchstone::from_text(&out, Some(2), None).unwrap();
        for (a, b) in ts.s().iter().zip(back.s()) {
            assert!(
                (a - b).abs() <= TOL * a.abs().max(1.0),
                "roundtrip via {f:?} within core_tol: {a} vs {b}"
            );
        }
    }
}

#[test]
fn write_preserves_stored_version_11_all_equal_z0() {
    // 1.1 file (per-port R, all equal 50): write must keep "# ... R 50 50"
    // (stored version), NOT re-derive "1.0" from equal values.
    let text = "# GHZ S MA R 50 50\n1.0 0.5 -30 0.1 170 0.1 170 0.8 -45";
    let ts = Touchstone::from_text(text, Some(2), None).unwrap();
    assert_eq!(ts.version(), "1.1");
    let out = ts
        .write_touchstone(TouchstoneParameter::S, TouchstoneFormat::MA)
        .unwrap();
    assert!(
        out.contains("# GHZ S MA R 50 50"),
        "option line must stay 1.1: {out}"
    );
    let back = Touchstone::from_text(&out, Some(2), None).unwrap();
    assert_eq!(back.version(), "1.1");
}

#[test]
fn write_touchstone_domain_conversion_matches_properties() {
    let ts = two_port_z();
    let z_text = ts
        .write_touchstone(TouchstoneParameter::Z, TouchstoneFormat::RI)
        .unwrap();
    // The written Z data must match the z property (both from stored S).
    let back = Touchstone::from_text(&z_text, Some(2), None).unwrap();
    assert_eq!(back.z(), ts.z());
}

#[test]
fn format_number_shortest_roundtrip_extremes() {
    // Values incl. 0, negatives, extremes must roundtrip bit-exact.
    // nports=1 stride=3: freq + re + im per point; distinct frequencies.
    let vals = [0.0, -0.0, 1.0, -1.0, 0.1, 1e-300, 1e300, f64::MIN_POSITIVE];
    let mut text = String::from("# HZ S RI R 50\n");
    for (i, v) in vals.iter().enumerate() {
        text.push_str(&format!("{} {v} {v}\n", i + 1));
    }
    let ts = Touchstone::from_text(&text, Some(1), None).unwrap();
    let out = ts
        .write_touchstone(TouchstoneParameter::S, TouchstoneFormat::RI)
        .unwrap();
    let back = Touchstone::from_text(&out, Some(1), None).unwrap();
    assert_eq!(ts.s(), back.s(), "extreme values must roundtrip bit-exact");
    assert_eq!(ts.f(), back.f());
}

#[test]
fn write_file_lands_with_corrected_name() {
    let dir = std::env::temp_dir().join("netwave_wfile");
    std::fs::create_dir_all(&dir).unwrap();
    let ts = two_port_z();
    ts.write_file(
        dir.join("renamed.s3p").to_str().unwrap(),
        TouchstoneParameter::Z,
        TouchstoneFormat::RI,
    )
    .unwrap();
    let landed = dir.join("renamed.z2p");
    assert!(landed.exists(), "file must land as renamed.z2p, not .s3p");
    let content = std::fs::read_to_string(&landed).unwrap();
    let back = Touchstone::from_text(&content, Some(2), None).unwrap();
    assert_eq!(ts.s(), back.s());
    std::fs::remove_dir_all(&dir).ok();
}

#[test]
fn write_file_directory_form() {
    let dir = std::env::temp_dir().join("netwave_wfile_dir");
    std::fs::create_dir_all(&dir).unwrap();
    let ts = two_port_z();
    ts.write_file(
        dir.to_str().unwrap(),
        TouchstoneParameter::Z,
        TouchstoneFormat::RI,
    )
    .unwrap();
    // Extension letter = the object's parameter domain.
    assert!(dir.join("x.z2p").exists());
    std::fs::remove_dir_all(&dir).ok();
}

#[test]
fn write_touchstone_emits_comments() {
    let text = "! first\n! second\n# GHZ S RI R 50\n1.0 0.1 0.2";
    let ts = Touchstone::from_text(text, Some(1), None).unwrap();
    let out = ts
        .write_touchstone(TouchstoneParameter::S, TouchstoneFormat::RI)
        .unwrap();
    assert!(out.starts_with("! first\n! second\n"), "got: {out}");
}

#[test]
fn write_touchstone_gh_on_non_two_port_errors() {
    let text = "# GHZ S RI R 50\n1.0 0.1 0.2";
    let ts = Touchstone::from_text(text, Some(1), None).unwrap();
    let err = ts
        .write_touchstone(TouchstoneParameter::H, TouchstoneFormat::RI)
        .unwrap_err();
    assert!(
        err.to_string().contains('H'),
        "must quote the offending domain: {err}"
    );
}

#[test]
fn write_file_unwritable_path_errors() {
    // A path whose parent directory does not exist fails at the fs layer
    // and surfaces as a Syntax error quoting the full path.
    let ts = two_port_z();
    let err = ts
        .write_file(
            "/nonexistent-netwave-dir-xyz/out.s2p",
            TouchstoneParameter::Z,
            TouchstoneFormat::RI,
        )
        .unwrap_err();
    assert!(
        err.to_string().contains("nonexistent-netwave-dir-xyz"),
        "error must quote the failing path: {err}"
    );
}
