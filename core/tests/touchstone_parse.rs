//! Parse-pipeline contract: option-line normalization (`#` units/domain/
//! format/R), case-insensitive reading, offending-token errors, z0 shape
//! validation, frequency-axis rules, stride divisibility, and the name
//! pipeline. All tests enter through the public surface (`from_text` and
//! the static pipeline trio).

use netwave::touchstone::Touchstone;

const HEADER_1P: &str = "# GHZ S RI R 50";
const DATA_1P: &str = "1.0 0.1 -0.2\n2.0 0.3 -0.4";

#[test]
fn option_line_units_domain_format_r_normalized() {
    // GHz unit multiplier applied to the Hz master axis.
    let ts = Touchstone::from_text(&format!("{HEADER_1P}\n{DATA_1P}"), Some(1), None).unwrap();
    assert_eq!(ts.f(), vec![1.0e9, 2.0e9]);
    assert_eq!(ts.parameter().as_ref(), "S");
    assert_eq!(ts.z0(), vec![50.0]);
    assert_eq!(ts.version(), "1.0");
    // RI: re/im stored interleaved, bit-verbatim.
    assert_eq!(ts.s(), vec![0.1, -0.2, 0.3, -0.4]);
}

#[test]
fn option_line_v11_per_port_r_records_version_11() {
    // 2-port, per-port R (even all-equal): version recorded as "1.1" from
    // the R SHAPE, not derived from the values.
    let text = "# GHZ S RI R 50 50\n1.0 0.1 -0.2 0.3 -0.4 0.5 -0.6 0.7 -0.8";
    let ts = Touchstone::from_text(text, Some(2), None).unwrap();
    assert_eq!(ts.version(), "1.1");
    assert_eq!(ts.z0(), vec![50.0, 50.0]);
}

#[test]
fn option_line_mixed_case_read() {
    // Reading accepts any case; the parser normalizes internally.
    let text = "# ghz s ma r 50\n1.0 0.5 -30";
    let ts = Touchstone::from_text(text, Some(1), None).unwrap();
    assert_eq!(ts.parameter().as_ref(), "S");
    assert_eq!(ts.version(), "1.0");
    // MA: mag=0.5, deg=-30 -> re = 0.5*cos(-30deg), im = 0.5*sin(-30deg).
    let s = ts.s();
    let re = 0.5f64 * (-30f64).to_radians().cos();
    let im = 0.5f64 * (-30f64).to_radians().sin();
    assert!((s[0] - re).abs() < 1e-15 && (s[1] - im).abs() < 1e-15);
}

#[test]
fn db_format_uses_20log10_and_degrees() {
    // DB: mag = 10^(db/20), angle in degrees. -6.020599913279624 dB ~= 0.5.
    let text = "# GHZ S DB R 50\n1.0 -6.020599913279624 45";
    let ts = Touchstone::from_text(text, Some(1), None).unwrap();
    let s = ts.s();
    let mag = 0.5f64;
    let re = mag * 45f64.to_radians().cos();
    let im = mag * 45f64.to_radians().sin();
    assert!(
        (s[0] - re).abs() < 1e-12 && (s[1] - im).abs() < 1e-12,
        "db=-6.0206 deg=45 must decode to mag 0.5 at 45deg, got {s:?}"
    );
}

#[test]
fn invalid_option_token_errors_with_offending_text() {
    let text = "# GHZ Q RI R 50\n1.0 0.1 0.2";
    let err = Touchstone::from_text(text, Some(1), None).unwrap_err();
    assert!(
        err.to_string().contains('Q'),
        "error must quote offending token, got: {err}"
    );
}

#[test]
fn invalid_format_token_errors_with_offending_text() {
    let text = "# GHZ S XX R 50\n1.0 0.1 0.2";
    let err = Touchstone::from_text(text, Some(1), None).unwrap_err();
    assert!(
        err.to_string().contains("XX"),
        "error must quote offending token, got: {err}"
    );
}

#[test]
fn invalid_data_token_errors_with_offending_text() {
    let text = "# GHZ S RI R 50\n1.0 0.1 abc";
    let err = Touchstone::from_text(text, Some(1), None).unwrap_err();
    assert!(
        err.to_string().contains("abc"),
        "error must quote offending token, got: {err}"
    );
}

#[test]
fn missing_option_line_errors() {
    // The spec requires a `#` option line; a file without one is malformed
    // and MUST error, not silently fall back to defaults.
    let err = Touchstone::from_text(DATA_1P, Some(1), None).unwrap_err();
    assert!(
        err.to_string().contains("option line"),
        "error must name the missing option line, got: {err}"
    );
}

#[test]
fn partial_option_line_uses_spec_defaults_ma_ghz_s_r50() {
    // Spec defaults for keywords omitted from a present `#` line:
    // GHz / S / MA / R 50 (format default is MA, not RI).
    let text = "#\n1.0 0.5 -30";
    let ts = Touchstone::from_text(text, Some(1), None).unwrap();
    assert_eq!(ts.f(), vec![1.0e9]);
    assert_eq!(ts.parameter().as_ref(), "S");
    assert_eq!(ts.z0(), vec![50.0]);
    assert_eq!(ts.version(), "1.0");
    // MA decode: mag 0.5, deg -30.
    let s = ts.s();
    let re = 0.5f64 * (-30f64).to_radians().cos();
    let im = 0.5f64 * (-30f64).to_radians().sin();
    assert!(
        (s[0] - re).abs() < 1e-12 && (s[1] - im).abs() < 1e-12,
        "got {s:?}"
    );
}

#[test]
fn invalid_r_count_errors_with_z0_shape() {
    // 2-port file with 3 R values: neither 1 nor nports.
    let text = "# GHZ S RI R 50 45 50\n1.0 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8";
    let err = Touchstone::from_text(text, Some(2), None).unwrap_err();
    let msg = err.to_string();
    assert!(
        msg.contains('3') && msg.contains('2'),
        "error must quote actual len 3 and nports 2, got: {msg}"
    );
}

#[test]
fn comments_lines_collected() {
    let text = "! created by test\n! second comment\n# GHZ S RI R 50\n1.0 0.1 0.2";
    let ts = Touchstone::from_text(text, Some(1), None).unwrap();
    let c = ts.comments();
    assert!(c.contains("created by test") && c.contains("second comment"));
}

#[test]
fn shuffled_frequencies_sorted_ascending_silently() {
    // 3,1,2 GHz shuffled: stored ascending, data rows permuted with them.
    let text = "# GHZ S RI R 50\n3.0 0.30 0.31\n1.0 0.10 0.11\n2.0 0.20 0.21";
    let ts = Touchstone::from_text(text, Some(1), None).unwrap();
    assert_eq!(ts.f(), vec![1.0e9, 2.0e9, 3.0e9]);
    assert_eq!(ts.s(), vec![0.10, 0.11, 0.20, 0.21, 0.30, 0.31]);
}

#[test]
fn duplicate_frequency_errors_with_value() {
    let text = "# GHZ S RI R 50\n1.0 0.1 0.2\n1.0 0.3 0.4";
    let err = Touchstone::from_text(text, Some(1), None).unwrap_err();
    let msg = err.to_string();
    assert!(
        msg.contains('1'),
        "error must quote the duplicate frequency, got: {msg}"
    );
}

#[test]
fn token_count_not_divisible_by_stride_errors() {
    // 1-port stride = 3; 5 tokens is not divisible -> error quoting both.
    let text = "# GHZ S RI R 50\n1.0 0.1 0.2 3.0 0.3";
    let err = Touchstone::from_text(text, Some(1), None).unwrap_err();
    let msg = err.to_string();
    assert!(
        msg.contains('5') && msg.contains('3'),
        "error must quote token count 5 and stride 3, got: {msg}"
    );
}

#[test]
fn noise_rows_mixed_into_2port_file_error() {
    // 2-port stride = 9. Two data rows (18 tokens) + two noise rows
    // (5 tokens each) = 28 tokens, not divisible by 9 -> hard error.
    let text = "# GHZ S MA R 50\n\
                1.0 0.9 -10 0.1 170 0.1 170 0.9 -10\n\
                2.0 0.8 -20 0.2 160 0.2 160 0.8 -20\n\
                1.0 -1.0 0.5 30 10.0\n\
                2.0 -0.5 0.4 20 8.0";
    let err = Touchstone::from_text(text, Some(2), None).unwrap_err();
    let msg = err.to_string();
    assert!(
        msg.contains("28") && msg.contains('9'),
        "error must quote actual token count 28 and stride 9, got: {msg}"
    );
}

#[test]
fn data_row_spanning_multiple_physical_lines_parses() {
    // One 2-port frequency point split across two physical lines:
    // lines are formatting only; stride consumption is semantic.
    // freq 1.0 block = 9 tokens written as 5 + 4 across two lines.
    let text = "# GHZ S RI R 50\n1.0 0.1 0.2 0.3 0.4\n0.5 0.6 0.7 0.8\n2.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0.0";
    let ts = Touchstone::from_text(text, Some(2), None).unwrap();
    assert_eq!(ts.f(), vec![1.0e9, 2.0e9]);
    assert_eq!(
        ts.s(),
        vec![
            0.1, 0.2, 0.5, 0.6, 0.3, 0.4, 0.7, 0.8, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
        ]
    );
}

// ---- 2-port column order (v1.x legacy N11,N21,N12,N22) ----

#[test]
fn two_port_file_order_swaps_off_diagonals_to_row_major() {
    // v1.x 2-port files list columns N11, N21, N12, N22 (spec v2.1
    // "1-port and 2-port Networks"); 3+ port files are row-wise
    // (N11, N12, N13 / N21, ...). Internal storage MUST be row-major
    // for every port count, so the off-diagonal pairs swap at parse.
    // File: S11=1+2j, S21=3+4j, S12=5+6j, S22=7+8j.
    let text = "# GHZ S RI R 50\n1.0 1 2 3 4 5 6 7 8";
    let ts = Touchstone::from_text(text, Some(2), None).unwrap();
    // Row-major: S11, S12, S21, S22.
    assert_eq!(ts.s(), vec![1.0, 2.0, 5.0, 6.0, 3.0, 4.0, 7.0, 8.0]);
}

#[test]
fn three_port_file_order_is_row_major_no_swap() {
    // 3-port files are already row-wise; no swap applies. First row
    // S11,S12,S13 = (1,0),(2,0),(3,0) must land verbatim.
    // stride = 1 + 2*9 = 19: one frequency + 18 numbers (9 complex pairs).
    let mut text = String::from("# GHZ S RI R 50\n1.0");
    for v in 1..=9 {
        text.push(' ');
        text.push_str(&v.to_string());
        text.push_str(" 0");
    }
    let ts = Touchstone::from_text(&text, Some(3), None).unwrap();
    assert_eq!(&ts.s()[..6], &[1.0, 0.0, 2.0, 0.0, 3.0, 0.0]);
}

// ---- name pipeline (static trio) ----
#[test]
fn filename_from_path_strips_directory() {
    assert_eq!(Touchstone::filename_from_path("/tmp/a/b.s4p"), "b.s4p");
    assert_eq!(Touchstone::filename_from_path("b.s2p"), "b.s2p");
    // URL form: last '/' segment.
    assert_eq!(
        Touchstone::filename_from_path("https://x.io/y/d.s1p"),
        "d.s1p"
    );
}

#[test]
fn name_from_filename_grammar_strip() {
    assert_eq!(Touchstone::name_from_filename("b.s4p"), "b");
    assert_eq!(Touchstone::name_from_filename("filter.S2P"), "filter");
    // Grammar mismatch: whole string, not one character stripped.
    assert_eq!(Touchstone::name_from_filename("2026.10.09"), "2026.10.09");
    assert_eq!(Touchstone::name_from_filename("foo.txt"), "foo.txt");
}

#[test]
fn nports_from_filename_grammar_and_error() {
    assert_eq!(Touchstone::nports_from_filename("b.s4p").unwrap(), 4);
    assert_eq!(Touchstone::nports_from_filename("x.Z12p").unwrap(), 12);
    let err = Touchstone::nports_from_filename("foo.txt").unwrap_err();
    let msg = err.to_string();
    assert!(
        msg.contains("foo.txt") && msg.contains("nports"),
        "error must quote filename and guide explicit nports, got: {msg}"
    );
}

// ---- from_text end-to-end: nports priority ----

const DATA_2P_1F: &str = "# GHZ S RI R 50\n1.0 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8";

#[test]
fn from_text_without_nports_or_path_errors() {
    let err = Touchstone::from_text(DATA_2P_1F, None, None).unwrap_err();
    assert!(
        err.to_string().contains("nports"),
        "error must guide explicit nports, got: {err}"
    );
}

#[test]
fn from_text_infers_nports_from_path_and_stores_stem_name() {
    let ts = Touchstone::from_text(DATA_2P_1F, None, Some("/tmp/a/b.s2p")).unwrap();
    assert_eq!(ts.nports(), 2);
    assert_eq!(ts.name(), "b");
}

#[test]
fn from_text_explicit_nports_wins_over_filename() {
    // filename says 2 ports, explicit says 1: explicit wins.
    let text = "# GHZ S RI R 50\n1.0 0.1 0.2";
    let ts = Touchstone::from_text(text, Some(1), Some("x.s2p")).unwrap();
    assert_eq!(ts.nports(), 1);
    assert_eq!(ts.name(), "x");
}

#[test]
fn from_text_z_domain_named_s_file_keeps_parameter_z() {
    // Extension domain letter is NOT authoritative; the `#` line is.
    let text = "# GHZ Z RI R 50\n1.0 10 1 2 20 3 30 4 40";
    let ts = Touchstone::from_text(text, Some(2), Some("x.s2p")).unwrap();
    assert_eq!(ts.parameter().as_ref(), "Z");
}

#[test]
fn blank_lines_are_skipped() {
    // Empty lines between sections are ignored, not parsed as tokens.
    let text = "# GHZ S RI R 50\n\n1.0 0.1 0.2\n\n2.0 0.3 0.4\n";
    let ts = Touchstone::from_text(text, Some(1), None).unwrap();
    assert_eq!(ts.f(), vec![1.0e9, 2.0e9]);
}

#[test]
fn option_line_second_r_group_starts_new_run() {
    // `R 50 R 45`: the inner loop breaks on the second `R`, the outer
    // loop starts a new run — per-port z0 [50, 45] (v1.1).
    let text = "# GHZ S RI R 50 R 45\n1.0 0.1 0.2 0.3 0.4 0.5 0.6 0.7 0.8";
    let ts = Touchstone::from_text(text, Some(2), None).unwrap();
    assert_eq!(ts.z0(), &[50.0, 45.0]);
    assert_eq!(ts.version(), "1.1");
}

#[test]
fn option_line_r_non_number_errors() {
    let err = Touchstone::from_text("# GHZ S RI R abc\n1.0 0.1 0.2", Some(1), None).unwrap_err();
    assert!(
        err.to_string().contains("abc"),
        "error must quote the non-numeric R token: {err}"
    );
}

#[test]
fn ext_match_grammar_failures() {
    // Too short after the dot (no digit + p).
    assert!(Touchstone::nports_from_filename("x.s").is_err());
    // Domain letter outside the closed grammar.
    assert!(Touchstone::nports_from_filename("x.t1p").is_err());
    // Trailing character is not 'p'.
    assert!(Touchstone::nports_from_filename("x.s1q").is_err());
    // Empty port digits (domain letter directly followed by 'p').
    assert!(Touchstone::nports_from_filename("x.sp").is_err());
    // Port digits overflow usize.
    assert!(Touchstone::nports_from_filename("x.s99999999999999999999999p").is_err());
}
