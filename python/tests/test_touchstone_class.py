"""Touchstone pyclass surface (spec: touchstone-core).

Expected values are independent literals / closed-form (ironclad rule 2).
Same-machine roundtrips are bit-exact for RI; MA/DB compare within the
manifest core_tol (ironclad rule 3).
"""

import math
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import netwave
import numpy as np
import pytest

S1P = """! comment one
# GHZ S RI R 50
1.0 1.0 0.1
2.0 0.9 -0.2
"""

# 2-port Z, v1.1 per-port R, MA format: z11=10∠0 z12=20∠90 z21=30∠-90
# z22=40∠180. v1.x 2-port files use legacy order (z11, z21, z12, z22).
Z2P = """# GHZ Z MA R 50 45
1.0 10 0 30 -90
20 90 40 180
"""


def test_from_text_metadata_and_data() -> None:
    ts = netwave.Touchstone.from_text(S1P, 1, "/tmp/dir/filter.s1p")
    assert ts.nports == 1
    assert ts.name == "filter"
    assert ts.version == "1.0"
    assert ts.parameter == "S"
    assert ts.comments == "comment one"
    assert ts.s.tolist() == [[[1.0 + 0.1j]], [[0.9 - 0.2j]]]
    assert ts.f.tolist() == [1e9, 2e9]
    assert ts.z0.tolist() == [50.0]


def test_from_text_nports_from_path() -> None:
    ts = netwave.Touchstone.from_text(S1P, path="/x/a.s1p")
    assert ts.nports == 1


def test_from_text_no_nports_no_path_raises() -> None:
    with pytest.raises(ValueError):
        netwave.Touchstone.from_text(S1P)


def test_from_text_missing_option_line_raises() -> None:
    # The `#` option line is mandatory; a file without one must error.
    with pytest.raises(ValueError, match="option line"):
        netwave.Touchstone.from_text("1.0 0.1 0.2\n", 1)


def test_from_text_partial_option_line_defaults_to_ma() -> None:
    # Spec defaults for omitted keywords: GHz / S / MA / R 50.
    ts = netwave.Touchstone.from_text("#\n1.0 0.5 -30\n", 1)
    assert ts.z0.tolist() == [50.0]
    c = ts.s.tolist()[0][0][0]
    assert c.real == pytest.approx(0.5 * math.cos(math.radians(-30)))
    assert c.imag == pytest.approx(0.5 * math.sin(math.radians(-30)))


def test_from_text_syntax_error_quotes_token() -> None:
    bad = "# GHZ S RI R 50\n1.0 abc 0.1\n"
    with pytest.raises(ValueError, match="abc"):
        netwave.Touchstone.from_text(bad, 1)


def test_from_text_duplicate_frequency_raises() -> None:
    dup = "# GHZ S RI R 50\n1.0 1.0 0.1\n1.0 0.5 0.0\n"
    with pytest.raises(ValueError, match="1"):
        netwave.Touchstone.from_text(dup, 1)


def test_from_file(tmp_path) -> None:
    p = tmp_path / "dut.s2p"
    p.write_text(Z2P, encoding="utf-8")
    ts = netwave.Touchstone.from_file(str(p))
    assert ts.name == "dut"
    assert ts.nports == 2
    assert ts.version == "1.1"
    assert ts.z0.tolist() == [50.0, 45.0]


def test_data_srI_is_zero_copy_complex() -> None:
    ts = netwave.Touchstone.from_text(S1P, 1)
    d = ts.data("S", "RI")
    assert d.shape == (2, 1, 1)
    assert d.dtype == np.complex128
    assert d.flags.owndata is False
    assert d[0, 0, 0] == 1.0 + 0.1j


def test_data_missing_args_raise() -> None:
    # Both parameters are mandatory; no silent (S, RI) default.
    ts = netwave.Touchstone.from_text(S1P, 1)
    with pytest.raises(TypeError):
        ts.data()
    with pytest.raises(TypeError):
        ts.data("S")


def test_data_ma_shape_and_values() -> None:
    ts = netwave.Touchstone.from_text(S1P, 1)
    ma = ts.data("S", "MA")
    assert ma.shape == (2, 1, 1, 2)
    assert ma.dtype == np.float64
    assert ma[0, 0, 0, 0] == pytest.approx(np.hypot(1.0, 0.1))
    assert ma[0, 0, 0, 1] == pytest.approx(np.degrees(np.arctan2(0.1, 1.0)))


def test_z_property_matches_parsed_domain() -> None:
    ts = netwave.Touchstone.from_text(Z2P, 2)
    z = ts.z
    assert z.shape == (1, 2, 2)
    expected = np.array([[[10 + 0j, 0 + 20j], [0 - 30j, -40 + 0j]]])
    np.testing.assert_allclose(z, expected, rtol=1e-12)


def test_gh_domain_requires_two_ports() -> None:
    ts = netwave.Touchstone.from_text(S1P, 1)
    with pytest.raises(ValueError, match="2-port"):
        _ = ts.g


def test_from_data_version_from_z0_values() -> None:
    f = netwave.Frequency.from_f([1.0, 2.0], "GHz")
    ts = netwave.Touchstone.from_data(f, [1.0, 0.1, 0.9, -0.2], 50.0, "S")
    assert ts.version == "1.0"
    assert ts.nports == 1
    f1 = netwave.Frequency.from_f([1.0], "GHz")
    ts2 = netwave.Touchstone.from_data(f1, [10, 0, 20, 90, 30, -90, 40, 180], [50.0, 45.0], "S")
    assert ts2.version == "1.1"


def test_from_data_parameter_required() -> None:
    f = netwave.Frequency.from_f([1.0], "GHz")
    with pytest.raises(TypeError):
        netwave.Touchstone.from_data(f, [1.0, 0.0], 50.0)  # type: ignore[call-arg]


def test_from_data_z0_shape_error() -> None:
    f = netwave.Frequency.from_f([1.0], "GHz")
    with pytest.raises(ValueError, match="z0"):
        netwave.Touchstone.from_data(f, [1.0, 0.0], [50.0, 45.0], "S")


def test_to_text_ri_roundtrip_bit_exact() -> None:
    ts = netwave.Touchstone.from_text(Z2P, 2)
    text = ts.to_text("S", "RI")
    back = netwave.Touchstone.from_text(text, 2)
    assert back.s.tobytes() == ts.s.tobytes()
    assert back.z0.tolist() == ts.z0.tolist()
    assert back.version == ts.version


def test_write_file_corrects_extension(tmp_path) -> None:
    ts = netwave.Touchstone.from_text(S1P, 1, "/tmp/dir/filter.s1p")
    ts.write_file(str(tmp_path / "filter.s9p"), "S", "RI")
    assert (tmp_path / "filter.s1p").exists()
    assert not (tmp_path / "filter.s9p").exists()


# --- byte boundary (from_bytes / to_bytes) -------------------------------------

# ASCII body; the µ comment marker is injected at the byte level so tests
# control the exact encoding bytes (ironclad rule 2: independent literals).
_BODY_1P = b"# GHZ S RI R 50\n1.0 1.0 0.1\n2.0 0.9 -0.2\n"
_LATIN1 = b"! \xb5\n" + _BODY_1P  # µ as single byte B5 (invalid UTF-8)
_UTF8 = "! \u00b5\n".encode("utf-8") + _BODY_1P  # µ as C2 B5


def test_from_bytes_guesses_latin1() -> None:
    ts = netwave.Touchstone.from_bytes(_LATIN1, 1)
    assert ts.comments == "\u00b5"
    assert ts.s.tolist() == [[[1.0 + 0.1j]], [[0.9 - 0.2j]]]


def test_from_bytes_default_guess_matches_explicit_latin1() -> None:
    guessed = netwave.Touchstone.from_bytes(_LATIN1, 1)
    explicit = netwave.Touchstone.from_bytes(_LATIN1, 1, encoding="ISO-8859-1")
    assert guessed.s.tobytes() == explicit.s.tobytes()
    assert guessed.comments == explicit.comments


def test_from_bytes_accepts_buffer_trio() -> None:
    # bytes / bytearray / memoryview all accepted (buffer protocol).
    for buf in (_LATIN1, bytearray(_LATIN1), memoryview(_LATIN1)):
        ts = netwave.Touchstone.from_bytes(buf, 1)
        assert ts.comments == "\u00b5"


def test_from_bytes_explicit_utf8_on_latin1_raises() -> None:
    with pytest.raises(ValueError, match="UTF-8"):
        netwave.Touchstone.from_bytes(_LATIN1, 1, encoding="UTF-8")


def test_from_bytes_rejects_numpy() -> None:
    # numpy uint8 is deliberately outside the accepted trio.
    with pytest.raises(ValueError, match="bytes"):
        netwave.Touchstone.from_bytes(np.frombuffer(_LATIN1, np.uint8), 1)


def test_from_bytes_bad_encoding_name_raises() -> None:
    with pytest.raises(ValueError, match="UTF-16"):
        netwave.Touchstone.from_bytes(_UTF8, 1, encoding="UTF-16")


def test_to_bytes_default_utf8_and_latin1() -> None:
    ts = netwave.Touchstone.from_bytes(_LATIN1, 1)
    # Default write = UTF-8: µ becomes C2 B5.
    assert ts.to_bytes("S", "RI").startswith(b"! \xc2\xb5\n")
    # Explicit latin-1: µ stays single byte B5.
    assert ts.to_bytes("S", "RI", "ISO-8859-1").startswith(b"! \xb5\n")


def test_to_bytes_returns_bytes() -> None:
    ts = netwave.Touchstone.from_text(S1P, 1)
    assert isinstance(ts.to_bytes("S", "RI"), bytes)


def test_to_bytes_rejects_char_beyond_latin1() -> None:
    body = b"# GHZ S RI R 50\n1.0 1.0 0.1\n"
    ts = netwave.Touchstone.from_bytes("! \u2103\n".encode("utf-8") + body, 1)
    with pytest.raises(ValueError, match="ISO-8859-1"):
        ts.to_bytes("S", "RI", "ISO-8859-1")


def test_bytes_roundtrip_bit_exact_same_encoding() -> None:
    ts = netwave.Touchstone.from_bytes(_LATIN1, 1, encoding="ISO-8859-1")
    written = ts.to_bytes("S", "RI", "ISO-8859-1")
    back = netwave.Touchstone.from_bytes(written, 1, encoding="ISO-8859-1")
    assert back.s.tobytes() == ts.s.tobytes()
    assert back.comments == ts.comments


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path.startswith("/data/"):
            body = S1P.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args: object) -> None:
        pass


def test_from_url_and_http_error() -> None:
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        ts = netwave.Touchstone.from_url(f"http://127.0.0.1:{port}/data/filter.s1p")
        assert ts.name == "filter"
        assert ts.nports == 1
        assert ts.s.tolist() == [[[1.0 + 0.1j]], [[0.9 - 0.2j]]]
        with pytest.raises(ValueError, match="404"):
            netwave.Touchstone.from_url(f"http://127.0.0.1:{port}/missing.s1p")
    finally:
        server.shutdown()


def test_drop_is_idempotent_and_post_drop_raises() -> None:
    ts = netwave.Touchstone.from_text(S1P, 1)
    assert ts.nports == 1
    ts.drop()
    with pytest.raises(ValueError, match="dropped"):
        _ = ts.nports
    with pytest.raises(ValueError, match="dropped"):
        _ = ts.s
    ts.drop()  # idempotent
