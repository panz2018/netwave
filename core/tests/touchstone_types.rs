//! Typing contract for the Touchstone surface: the two enums are the only
//! vocabulary source (exact members, case-insensitive `FromStr`), and every
//! `TouchstoneError` message quotes the offending input verbatim.

use std::str::FromStr;

use netwave::touchstone::{
    IntoEnumIterator, TouchstoneError, TouchstoneFormat, TouchstoneParameter,
};

#[test]
fn parameter_enum_members_are_exactly_s_y_z_g_h() {
    let names: Vec<String> = TouchstoneParameter::iter()
        .map(|p| p.as_ref().to_owned())
        .collect();
    assert_eq!(names, ["S", "Y", "Z", "G", "H"]);
}

#[test]
fn format_enum_members_are_exactly_ri_ma_db() {
    let names: Vec<String> = TouchstoneFormat::iter()
        .map(|f| f.as_ref().to_owned())
        .collect();
    assert_eq!(names, ["RI", "MA", "DB"]);
}

#[test]
fn parameter_from_str_is_case_insensitive() {
    assert_eq!(
        TouchstoneParameter::from_str("s").unwrap(),
        TouchstoneParameter::S
    );
    assert_eq!(
        TouchstoneParameter::from_str("Z").unwrap(),
        TouchstoneParameter::Z
    );
    assert_eq!(
        TouchstoneParameter::from_str("g").unwrap(),
        TouchstoneParameter::G
    );
    assert_eq!(
        TouchstoneParameter::from_str("h").unwrap(),
        TouchstoneParameter::H
    );
    assert_eq!(
        TouchstoneParameter::from_str("y").unwrap(),
        TouchstoneParameter::Y
    );
}

#[test]
fn format_from_str_is_case_insensitive() {
    assert_eq!(
        TouchstoneFormat::from_str("ri").unwrap(),
        TouchstoneFormat::RI
    );
    assert_eq!(
        TouchstoneFormat::from_str("Ma").unwrap(),
        TouchstoneFormat::MA
    );
    assert_eq!(
        TouchstoneFormat::from_str("db").unwrap(),
        TouchstoneFormat::DB
    );
}

#[test]
fn unknown_vocabulary_token_errors_with_offending_input() {
    let err = TouchstoneParameter::from_str("Q").unwrap_err();
    assert!(
        err.to_string().contains("Q"),
        "error must quote the offending token, got: {err}"
    );
    let err = TouchstoneFormat::from_str("XY").unwrap_err();
    assert!(
        err.to_string().contains("XY"),
        "error must quote the offending token, got: {err}"
    );
}

#[test]
fn error_display_quotes_offending_input() {
    let cases: Vec<(TouchstoneError, &str)> = vec![
        (
            TouchstoneError::DuplicateFrequency { f: 1.5e9 },
            "1500000000",
        ),
        (
            TouchstoneError::DimensionMismatch {
                data_len: 7,
                npoints: 2,
                nports: 2,
            },
            "7",
        ),
        (TouchstoneError::Z0Shape { len: 3, nports: 2 }, "3"),
        (
            TouchstoneError::Syntax {
                token: "X9.abc".to_owned(),
            },
            "X9.abc",
        ),
        (
            TouchstoneError::DomainPortCount {
                domain: "G".to_owned(),
                nports: 4,
            },
            "G",
        ),
        (
            TouchstoneError::NportsNoMatch {
                filename: "foo.txt".to_owned(),
            },
            "foo.txt",
        ),
        (
            TouchstoneError::StrideDivisibility { len: 14, stride: 9 },
            "14",
        ),
    ];
    for (err, needle) in cases {
        let msg = err.to_string();
        assert!(
            msg.contains(needle),
            "message {msg:?} must quote offending input {needle:?}"
        );
    }
}

#[test]
fn stride_divisibility_message_quotes_expected_stride() {
    let err = TouchstoneError::StrideDivisibility { len: 14, stride: 9 };
    let msg = err.to_string();
    assert!(msg.contains("9"), "message must quote stride: {msg}");
}

#[test]
fn nports_no_match_message_points_to_explicit_nports() {
    let err = TouchstoneError::NportsNoMatch {
        filename: "foo.txt".to_owned(),
    };
    let msg = err.to_string();
    assert!(
        msg.contains("nports"),
        "message must guide the user to pass nports explicitly: {msg}"
    );
}
