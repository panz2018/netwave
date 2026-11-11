//! Parse-pipeline contract: option-line normalization (`#` units/domain/
//! format/R), case-insensitive reading, offending-token errors, z0 shape
//! validation, frequency-axis rules, stride divisibility, and the name
//! pipeline. All tests enter through the public surface (`from_text` and
//! the static pipeline trio).

use std::str::FromStr;

use netwave::touchstone::Touchstone;
use netwave::touchstone::TouchstoneEncoding;
use netwave::touchstone::TouchstoneError;

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
fn option_line_complex_r_errors_with_offending_token() {
    // Spec forbids complex reference resistance (v1.1: "real, positive
    // numbers"; v2.x: complex not supported). Parenthesized complex
    // forms must error naming the offending token.
    let err =
        Touchstone::from_text("# GHZ S RI R (10+10j)\n1.0 0.1 0.2", Some(1), None).unwrap_err();
    assert!(
        err.to_string().contains("(10+10j)"),
        "error must quote the complex R token: {err}"
    );
}

#[test]
fn option_line_second_line_ignored_first_wins() {
    // Spec v2.1 Option Line: "additional option lines after the first one
    // shall be ignored" — the first `#` line is authoritative; later lines
    // are skipped whole, even when they would change unit/format/R.
    let text = "# GHZ S MA R 50\n# MHZ S RI R 75\n1.0 0.5 -30";
    let ts = Touchstone::from_text(text, Some(1), None).unwrap();
    assert_eq!(ts.z0(), vec![50.0]);
    // MA from the first line: 0.5∠-30deg, not RI (0.5, -30).
    let s = ts.s();
    let re = 0.5f64 * (-30f64).to_radians().cos();
    let im = 0.5f64 * (-30f64).to_radians().sin();
    assert!((s[0] - re).abs() < 1e-15 && (s[1] - im).abs() < 1e-15);
}

#[test]
fn option_line_invalid_second_line_still_ignored() {
    // An invalid second option line must NOT error: spec ignores it before
    // validation. Only the first line is parsed and validated.
    let text = "# GHZ S RI R 50\n# GHZ Q RI R (10+10j)\n1.0 0.1 0.2";
    let ts = Touchstone::from_text(text, Some(1), None).unwrap();
    assert_eq!(ts.z0(), vec![50.0]);
    assert_eq!(ts.s(), vec![0.1, 0.2]);
}

// ---- layout variants: line endings, whitespace, notation, zero sign ----

#[test]
fn crlf_line_endings_and_missing_trailing_newline_parse_bit_exact() {
    // CRLF line endings and a file whose last line has no newline must parse
    // to bit-identical results as the LF-with-trailing-newline version
    // (exact comparison is bit-level, no tolerance — governance rule 3).
    let lf = "# GHZ S RI R 50\n1.0 0.1 -0.2 0.3 -0.4 0.5 -0.6 0.7 -0.8\n";
    let crlf = "# GHZ S RI R 50\r\n1.0 0.1 -0.2 0.3 -0.4 0.5 -0.6 0.7 -0.8";
    let base = Touchstone::from_text(lf, Some(2), None).unwrap();
    let variant = Touchstone::from_text(crlf, Some(2), None).unwrap();
    assert_eq!(variant.f(), base.f());
    assert_eq!(
        variant
            .s()
            .iter()
            .map(|v| v.to_bits())
            .collect::<Vec<u64>>(),
        base.s().iter().map(|v| v.to_bits()).collect::<Vec<u64>>(),
        "CRLF/no-trailing-newline must be bit-identical to LF"
    );
}

#[test]
fn odd_whitespace_and_scientific_notation_parse_bit_exact() {
    // Tabs, runs of spaces, and leading indentation between tokens are
    // whitespace; scientific-notation tokens equal their decimal spelling
    // bit-for-bit after f64 parsing.
    let decimal = "# GHZ S RI R 50\n1.0 0.1 -0.2\n2.0 0.3 -0.4\n";
    let odd = "#\tGHZ   S\tRI R  50\n   1.0e+0\t1e-1   -2e-1\n\t2.0E+0 3e-1\t-4e-1\n";
    let base = Touchstone::from_text(decimal, Some(1), None).unwrap();
    let variant = Touchstone::from_text(odd, Some(1), None).unwrap();
    assert_eq!(variant.f(), base.f());
    assert_eq!(
        variant
            .s()
            .iter()
            .map(|v| v.to_bits())
            .collect::<Vec<u64>>(),
        base.s().iter().map(|v| v.to_bits()).collect::<Vec<u64>>(),
        "odd whitespace / sci-notation must be bit-identical to decimal"
    );
}

#[test]
fn negative_zero_input_keeps_sign_bit() {
    // "-0.0" must store as negative zero (sign bit set), not normalize to
    // +0.0 — roundtrip fidelity of the exact input bits.
    let ts = Touchstone::from_text("# GHZ S RI R 50\n1.0 -0.0 0.0", Some(1), None).unwrap();
    let s = ts.s();
    assert_eq!(s[0].to_bits(), (-0.0f64).to_bits(), "re must keep -0.0");
    assert_eq!(s[1].to_bits(), (0.0f64).to_bits(), "im stays +0.0");
}

#[test]
fn thirty_two_port_single_point_end_to_end() {
    // Max-port e2e: stride = 1 + 2*32^2 = 2049 tokens for one frequency
    // point; S buffer is 2048 interleaved re/im values.
    let nports = 32usize;
    let stride = 1 + 2 * nports * nports;
    let mut tokens: Vec<String> = Vec::with_capacity(stride);
    tokens.push("1.0".to_owned());
    for i in 0..(stride - 1) {
        tokens.push(format!("{i}.5"));
    }
    let text = format!("# GHZ S RI R 50\n{}", tokens.join(" "));
    let ts = Touchstone::from_text(&text, Some(nports), None).unwrap();
    assert_eq!(ts.nports(), 32);
    assert_eq!(ts.s().len(), 2 * nports * nports);
    assert_eq!(ts.f(), vec![1.0e9]);
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

#[test]
fn encoding_vocabulary_normalizes_aliases() {
    // Matching trims, lowercases, and strips `-`/`_`/space before the
    // whitelist comparison, so every spelling of the two accepted encodings
    // resolves to the same variant.
    for name in ["UTF-8", "utf8", "Utf_8", " utf-8 ", "UTF 8"] {
        assert_eq!(
            TouchstoneEncoding::from_str(name).unwrap(),
            TouchstoneEncoding::Utf8,
            "{name:?} must resolve to Utf8"
        );
    }
    for name in [
        "ISO-8859-1",
        "latin1",
        "Latin_1",
        "iso88591",
        "LATIN-1",
        " ISO_8859_1 ",
    ] {
        assert_eq!(
            TouchstoneEncoding::from_str(name).unwrap(),
            TouchstoneEncoding::Iso88591,
            "{name:?} must resolve to Iso88591"
        );
    }
    // Canonical spellings for bindings reflecting the vocabulary.
    assert_eq!(TouchstoneEncoding::Utf8.as_ref(), "UTF-8");
    assert_eq!(TouchstoneEncoding::Iso88591.as_ref(), "ISO-8859-1");
}

#[test]
fn encoding_outside_whitelist_errors_with_original_token() {
    // Anything outside {UTF-8, ISO-8859-1} + the alias set errors, quoting
    // the original word. `latin`/`L1`/`cp819` are deliberate exclusions: the
    // alias list is an intentional subset, not the full codecs.lookup set.
    for bad in ["UTF-16", "ASCII", "latin", "L1", "cp819", "not-an-encoding"] {
        let err = TouchstoneEncoding::from_str(bad).unwrap_err();
        assert!(
            matches!(err, TouchstoneError::EncodingUnsupported { ref name } if name == bad),
            "{bad:?} must error as EncodingUnsupported quoting the original, got: {err}"
        );
    }
}

/// Minimal 1-port body, ASCII only; comment lines get the non-ASCII marker
/// at the byte level so tests control the exact encoding bytes.
const BODY_1P: &[u8] = b"# GHZ S RI R 50\n1.0 0.1 -0.2\n2.0 0.3 -0.4\n";

fn latin1_bytes() -> Vec<u8> {
    // `! µ` — micro sign as the single byte 0xB5 (latin-1), which is NOT
    // valid UTF-8 and forces the guess chain to fall through.
    let mut v = vec![b'!', b' ', 0xB5, b'\n'];
    v.extend_from_slice(BODY_1P);
    v
}

fn utf8_bytes() -> Vec<u8> {
    // Same content encoded UTF-8: µ = 0xC2 0xB5.
    let mut v = b"! \xc2\xb5\n".to_vec();
    v.extend_from_slice(BODY_1P);
    v
}

#[test]
fn from_bytes_guesses_latin1_when_utf8_invalid() {
    let ts = Touchstone::from_bytes(&latin1_bytes(), Some(1), None, None).unwrap();
    assert_eq!(ts.comments(), "\u{b5}");
    assert_eq!(ts.s(), vec![0.1, -0.2, 0.3, -0.4]);
}

#[test]
fn from_bytes_strips_bom_on_default_and_explicit_utf8() {
    let mut bom = vec![0xEF, 0xBB, 0xBF];
    bom.extend_from_slice(BODY_1P);
    let default = Touchstone::from_bytes(&bom, Some(1), None, None).unwrap();
    let explicit =
        Touchstone::from_bytes(&bom, Some(1), None, Some(TouchstoneEncoding::Utf8)).unwrap();
    assert_eq!(default.f(), explicit.f());
    assert_eq!(default.s(), explicit.s());
    // Explicit latin-1 keeps the BOM bytes as the three chars ï»¿ —
    // stripping belongs to the UTF-8 path. The first line reads
    // `ï»¿# ...`, which is not a valid option line, so the parse errors
    // (the BOM is never silently swallowed on the latin-1 path).
    let latin = Touchstone::from_bytes(&bom, Some(1), None, Some(TouchstoneEncoding::Iso88591));
    assert!(
        latin.is_err(),
        "explicit latin-1 must not strip the BOM: the option line breaks, got {:?}",
        latin.map(|t| t.comments().to_owned())
    );
}

#[test]
fn from_bytes_explicit_utf8_never_falls_back() {
    let err = Touchstone::from_bytes(
        &latin1_bytes(),
        Some(1),
        None,
        Some(TouchstoneEncoding::Utf8),
    )
    .unwrap_err();
    assert!(
        matches!(err, TouchstoneError::EncodingDecode { ref encoding } if encoding == "UTF-8"),
        "explicit UTF-8 on latin-1 bytes must error EncodingDecode, got: {err}"
    );
}

#[test]
fn from_bytes_default_guess_matches_explicit_latin1() {
    let bytes = latin1_bytes();
    let guessed = Touchstone::from_bytes(&bytes, Some(1), None, None).unwrap();
    let explicit =
        Touchstone::from_bytes(&bytes, Some(1), None, Some(TouchstoneEncoding::Iso88591)).unwrap();
    // Same implementation behind both entry points — bit-exact equality.
    assert_eq!(
        guessed.s().iter().map(|v| v.to_bits()).collect::<Vec<_>>(),
        explicit.s().iter().map(|v| v.to_bits()).collect::<Vec<_>>()
    );
    assert_eq!(guessed.comments(), explicit.comments());
    assert_eq!(guessed.version(), explicit.version());
    assert_eq!(guessed.z0(), explicit.z0());
}

#[test]
fn from_bytes_utf8_input_parses_and_keeps_name_pipeline() {
    let ts = Touchstone::from_bytes(&utf8_bytes(), Some(1), Some("/tmp/d/f.s1p"), None).unwrap();
    assert_eq!(ts.comments(), "\u{b5}");
    assert_eq!(ts.name(), "f");
}

#[test]
fn from_bytes_garbage_bytes_error_never_panics() {
    // NUL bytes, UTF-16 residue (ASCII with interleaved 0x00), and a
    // truncated multi-byte sequence: every input must surface a
    // TouchstoneError, never a panic.
    let cases: Vec<Vec<u8>> = vec![
        vec![0x00, 0x01, 0x02, 0x03],
        b"#\x00G\x00H\x00Z\x00".to_vec(),
        vec![
            b'#', b' ', b'G', b'H', b'Z', b' ', b'S', b' ', b'R', b'I', b' ', b'R', b' ', b'5',
            b'0', b'\n', 0xC3,
        ],
    ];
    for bytes in cases {
        let res = std::panic::catch_unwind(|| Touchstone::from_bytes(&bytes, Some(1), None, None));
        assert!(
            res.is_ok_and(|r| r.is_err()),
            "garbage must error, not panic: {bytes:?}"
        );
    }
}

#[test]
fn to_bytes_default_utf8_and_explicit_latin1() {
    let ts = Touchstone::from_bytes(&latin1_bytes(), Some(1), None, None).unwrap();
    // Default write = UTF-8: µ becomes the two bytes C2 B5.
    let out = ts
        .to_bytes(
            netwave::touchstone::TouchstoneParameter::S,
            netwave::touchstone::TouchstoneFormat::RI,
            None,
        )
        .unwrap();
    assert!(
        out.starts_with(b"! \xc2\xb5\n"),
        "default write must be UTF-8, got {out:?}"
    );
    // Explicit latin-1: µ stays the single byte B5.
    let out = ts
        .to_bytes(
            netwave::touchstone::TouchstoneParameter::S,
            netwave::touchstone::TouchstoneFormat::RI,
            Some(TouchstoneEncoding::Iso88591),
        )
        .unwrap();
    assert!(
        out.starts_with(b"! \xb5\n"),
        "explicit latin-1 must emit single byte B5, got {out:?}"
    );
}

#[test]
fn to_bytes_rejects_char_beyond_latin1() {
    // ℃ (U+2103) is outside latin-1's U+0000–U+00FF range.
    let text = "# GHZ S RI R 50\n1.0 0.1 -0.2\n";
    let mut v = "! \u{2103}\n".as_bytes().to_vec();
    v.extend_from_slice(text.as_bytes());
    let ts = Touchstone::from_bytes(&v, Some(1), None, None).unwrap();
    let err = ts
        .to_bytes(
            netwave::touchstone::TouchstoneParameter::S,
            netwave::touchstone::TouchstoneFormat::RI,
            Some(TouchstoneEncoding::Iso88591),
        )
        .unwrap_err();
    assert!(
        matches!(err, TouchstoneError::CharNotLatin1 { ch: '\u{2103}' }),
        "must quote the offending char, got: {err}"
    );
}

#[test]
fn bytes_roundtrip_bit_exact_same_encoding() {
    // from_bytes → to_bytes with the source encoding → from_bytes again:
    // the two objects agree bit-for-bit (closed loop at the byte level).
    let bytes = latin1_bytes();
    let first =
        Touchstone::from_bytes(&bytes, Some(1), None, Some(TouchstoneEncoding::Iso88591)).unwrap();
    let written = first
        .to_bytes(
            netwave::touchstone::TouchstoneParameter::S,
            netwave::touchstone::TouchstoneFormat::RI,
            Some(TouchstoneEncoding::Iso88591),
        )
        .unwrap();
    let second =
        Touchstone::from_bytes(&written, Some(1), None, Some(TouchstoneEncoding::Iso88591))
            .unwrap();
    assert_eq!(
        first.s().iter().map(|v| v.to_bits()).collect::<Vec<_>>(),
        second.s().iter().map(|v| v.to_bits()).collect::<Vec<_>>()
    );
    assert_eq!(first.comments(), second.comments());
}
