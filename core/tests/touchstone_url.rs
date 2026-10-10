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

#[tokio::test]
async fn from_url_connection_failure_surfaces_verbatim() {
    // Port 1 has no listener: the transport failure is quoted verbatim.
    let err = Touchstone::from_url("http://127.0.0.1:1/x.s1p")
        .await
        .expect_err("connection refused must be an error");
    assert!(
        err.to_string().contains("127.0.0.1:1"),
        "error must quote the URL: {err}"
    );
}

#[tokio::test]
async fn from_url_truncated_body_surfaces_verbatim() {
    // A bare listener announces Content-Length: 100 then closes after a
    // few bytes: reqwest gets a 200 but the body read fails on the length
    // mismatch, so fetch_text's text() map_err branch fires.
    use std::io::{Read, Write};
    use std::net::TcpListener;
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let addr = listener.local_addr().unwrap();
    std::thread::spawn(move || {
        if let Ok((mut sock, _)) = listener.accept() {
            let mut buf = [0u8; 1024];
            let _ = sock.read(&mut buf);
            let _ = sock.write_all(b"HTTP/1.1 200 OK\r\nContent-Length: 100\r\n\r\nshort");
            let _ = sock.flush();
        }
    });
    let err = Touchstone::from_url(&format!("http://{addr}/x.s1p"))
        .await
        .expect_err("truncated body must be an error");
    assert!(
        err.to_string().contains("fetch failed"),
        "must surface the fetch failure: {err}"
    );
}

#[tokio::test]
async fn from_url_trailing_slash_has_no_filename() {
    // A URL ending in '/' yields an empty filename: nports cannot be
    // inferred and the parse errors, guiding explicit nports.
    let server = MockServer::start();
    server.mock(|when, then| {
        when.method(GET).path("/");
        then.status(200).body(S1P);
    });
    let err = Touchstone::from_url(&server.url("/"))
        .await
        .expect_err("empty filename cannot infer nports");
    assert!(
        err.to_string().contains("nports"),
        "error must guide explicit nports: {err}"
    );
}
