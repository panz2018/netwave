//! `from_url` (native backend): fetch bytes over HTTP, then the same
//! `from_text` pipeline. HTTP failures surface verbatim.

#![cfg(feature = "native-http")]

use httpmock::Method::GET;
use httpmock::MockServer;
use netwave::touchstone::Touchstone;

const S1P: &str = "\
! header
# GHZ S RI R 50
1.0 1.0 0.1
2.0 0.9 -0.2
";

#[tokio::test]
async fn from_url_parses_and_names_from_url_path() {
    let server = MockServer::start();
    let mock = server.mock(|when, then| {
        when.method(GET).path("/data/filter.s1p");
        then.status(200)
            .header("content-type", "text/plain")
            .body(S1P);
    });

    let ts = Touchstone::from_url(&server.url("/data/filter.s1p"))
        .await
        .expect("fetch + parse must succeed");
    mock.assert();

    // nports inferred from the URL filename grammar; name from its stem.
    assert_eq!(ts.nports(), 1);
    assert_eq!(ts.name(), "filter");
    assert_eq!(ts.version(), "1.0");
    assert_eq!(ts.s(), &[1.0, 0.1, 0.9, -0.2]);
}

#[tokio::test]
async fn from_url_http_error_propagates_verbatim() {
    let server = MockServer::start();
    server.mock(|when, then| {
        when.method(GET).path("/missing.s2p");
        then.status(404).body("nope");
    });

    let err = Touchstone::from_url(&server.url("/missing.s2p"))
        .await
        .expect_err("404 must be an error");
    let msg = err.to_string();
    // Error message quotes the failing status (and the URL) verbatim.
    assert!(msg.contains("404"), "error must quote status: {msg}");
}
