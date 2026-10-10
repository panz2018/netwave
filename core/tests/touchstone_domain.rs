//! Domain conversion contract: Y/Z/G/H files convert to S at ingestion
//! (storage holds S only), verified against independently computed
//! closed-form expectations (independent truth — never the function output).

use netwave::touchstone::Touchstone;

/// Tolerance from testdata/manifest.json `core_tol.relative` (placeholder).
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

#[test]
fn one_port_z_file_converts_to_s() {
    // Z = 100 (real), z0 = 50 -> S = (Z - z0)/(Z + z0) = 1/3.
    let text = "# GHZ Z RI R 50\n1.0 100 0";
    let ts = Touchstone::from_text(text, Some(1), None).unwrap();
    approx_eq(ts.s(), &[1.0 / 3.0, 0.0], TOL);
    assert_eq!(ts.parameter().as_ref(), "Z");
}

#[test]
fn one_port_y_file_converts_to_s() {
    // Y = 0.02 (real) -> Z = 50 -> S = 0.
    let text = "# GHZ Y RI R 50\n1.0 0.02 0";
    let ts = Touchstone::from_text(text, Some(1), None).unwrap();
    approx_eq(ts.s(), &[0.0, 0.0], TOL);
}

#[test]
fn two_port_z_file_converts_to_s_scalar_z0() {
    // Z = [[50, 0],[0, 50]] (matched) -> S = 0 matrix. Row-major pairs:
    // (50,0),(0,0),(0,0),(50,0).
    let text = "# GHZ Z RI R 50\n1.0 50 0 0 0 0 0 50 0";
    let ts = Touchstone::from_text(text, Some(2), None).unwrap();
    approx_eq(ts.s(), &[0.0; 8], TOL);
}

#[test]
fn two_port_y_file_converts_to_s_matches_z_route() {
    // Y = inv(Z) for Z = [[50, 25],[25, 75]] (real symmetric).
    // det = 50*75 - 25*25 = 3125. Z^-1 = [[75, -25],[-25, 50]]/3125.
    // Expected S computed via the Z route: S = (Z - 50I)(Z + 50I)^-1.
    // Z - 50I = [[0, 25],[25, 25]]; Z + 50I = [[100, 25],[25, 125]].
    // inv(Z+50I) = [[125, -25],[-25, 100]] / (100*125 - 25*25 = 11875).
    // S = [[0,25],[25,25]] @ inv =
    //   s00 = (0*125 + 25*-25)/11875 = -625/11875 = -1/19
    //   s01 = (0*-25 + 25*100)/11875 = 2500/11875 = 4/19
    //   s10 = (25*125 + 25*-25)/11875 = 2500/11875 = 4/19
    //   s11 = (25*-25 + 25*100)/11875 = 1875/11875 = 3/19
    let y = [
        75.0 / 3125.0,
        0.0,
        -25.0 / 3125.0,
        0.0,
        -25.0 / 3125.0,
        0.0,
        50.0 / 3125.0,
        0.0,
    ];
    let mut text = String::from("# GHZ Y RI R 50\n1.0");
    for v in y {
        text.push(' ');
        text.push_str(&v.to_string());
    }
    let ts = Touchstone::from_text(&text, Some(2), None).unwrap();
    approx_eq(
        ts.s(),
        &[
            -1.0 / 19.0,
            0.0,
            4.0 / 19.0,
            0.0,
            4.0 / 19.0,
            0.0,
            3.0 / 19.0,
            0.0,
        ],
        TOL,
    );
}

#[test]
fn two_port_h_file_converts_to_s() {
    // H = [[0.5, 0.1],[0.2, 0.4]] (real). H->Z:
    //   Zh = [[Δh/h22, h12/h22],[-h21/h22, 1/h22]], Δh = 0.5*0.4-0.1*0.2 = 0.18
    //   Zh = [[0.45, 0.25],[-0.5, 2.5]]
    // S = (Zh - 50I)(Zh + 50I)^-1.
    // Zh - 50I = [[-49.55, 0.25],[-0.5, -47.5]]
    // Zh + 50I = [[50.45, 0.25],[-0.5, 52.5]]
    // det = 50.45*52.5 - 0.25*(-0.5) = 2648.625 + 0.125 = 2648.75
    // adj = [[52.5, -0.25],[0.5, 50.45]]
    // (Z-Z0)adj = [[-2601.375+0.125, 12.3875+12.6125],
    //             [-26.25-23.75,    0.125-2396.375]]
    //           = [[-2601.25, 25],[-50, -2396.25]]
    // S_ij = (num_ij / det) * sqrt(z0_i / z0_j); z0 all 50 -> factor 1.
    // File is v1.x legacy 2-port order (h11, h21, h12, h22); the
    // intended matrix H = [[0.5, 0.1],[0.2, 0.4]] is written as
    // h11=0.5, h21=0.2, h12=0.1, h22=0.4.
    let text = "# GHZ H RI R 50\n1.0 0.5 0 0.2 0 0.1 0 0.4 0";
    let ts = Touchstone::from_text(text, Some(2), None).unwrap();
    let d = 2648.75f64;
    approx_eq(
        ts.s(),
        &[
            -2601.25 / d,
            0.0,
            25.0 / d,
            0.0,
            -50.0 / d,
            0.0,
            -2396.25 / d,
            0.0,
        ],
        TOL,
    );
}

#[test]
fn two_port_g_file_converts_to_s() {
    // G = [[0.02, 0.001],[0.002, 0.01]] (real). G->Y:
    //   Yg = [[Δg/g22, g12/g22],[-g21/g22, 1/g22]], Δg = 0.000198
    //   Yg = [[0.0198, 0.1],[-0.2, 100]]
    // Yn = Yg * 50 (scalar z0): [[0.99, 5],[-10, 5000]]
    // S = (I − Yn)(I + Yn)⁻¹
    // I − Yn = [[0.01, -5],[10, -4999]]
    // I + Yn = [[1.99, 5],[-10, 5001]]
    // det = 1.99*5001 + 50 = 9951.99 + 50 = 10001.99
    // adj = [[5001, -5],[10, 1.99]]
    // (I−Yn)adj = [[50.01-50, -0.05-9.95],[50010-49990, -50-9948.01]]
    //          = [[0.01, -10],[20, -9998.01]]
    // File is v1.x legacy 2-port order (g11, g21, g12, g22); the
    // intended matrix G = [[0.02, 0.001],[0.002, 0.01]] is written as
    // g11=0.02, g21=0.002, g12=0.001, g22=0.01.
    let text = "# GHZ G RI R 50\n1.0 0.02 0 0.002 0 0.001 0 0.01 0";
    let ts = Touchstone::from_text(text, Some(2), None).unwrap();
    let d = 10001.99f64;
    approx_eq(
        ts.s(),
        &[
            0.01 / d,
            0.0,
            -10.0 / d,
            0.0,
            20.0 / d,
            0.0,
            -9998.01 / d,
            0.0,
        ],
        TOL,
    );
}

#[test]
fn g_h_non_two_port_errors() {
    // 3-port stride = 19: 1 freq + 18 matrix entries.
    let text = "# GHZ G RI R 50\n1.0 1 0 2 0 3 0 4 0 5 0 6 0 7 0 8 0 9 0";
    let err = Touchstone::from_text(text, Some(3), None).unwrap_err();
    let msg = err.to_string();
    assert!(
        msg.contains('G') && msg.contains('3'),
        "error must quote domain G and nports 3, got: {msg}"
    );
}
