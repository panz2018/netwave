//! Touchstone file model: the `Touchstone` class, its vocabulary enums, and
//! its error type.
//!
//! This module is the single source of truth for the Touchstone vocabulary
//! (parameter domains and text formats) and for every parse/construct error.
//! Bindings expose the enums by reflection, never by copying a name list.
//!
//! # Storage model
//!
//! A `Touchstone` owns a [`crate::frequency::Frequency`] axis, one interleaved
//! f64 S matrix (governance rule 1), a per-port real reference impedance
//! `z0`, and metadata (`name`/`comments`/`version`/`parameter`). Parsing,
//! domain conversion, and text rendering are all private helpers; the public
//! data surface is the domain shortcut properties plus the unified accessor
//! [`Touchstone::data`].

use std::str::FromStr;

use num_complex::Complex64;
use strum::{AsRefStr, EnumIter};

// Browser dispatch (cfg=browser): the worker forwards `{handle, method,
// args}` to the single generic `resources::call`; this module owns the
// name→function `match`es (Rust has no reflection — the arm list IS the
// method table). Adding a method = one arm here; `resources.rs`, the
// worker, the shells and `types.ts` never change.
#[cfg(all(feature = "browser", not(feature = "node"), not(coverage)))]
use wasm_bindgen::prelude::*;

/// Re-exported so callers can invoke `iter()` without adding a direct
/// `strum` dependency (the trait must be in scope for method call syntax).
pub use strum::IntoEnumIterator;

/// A Touchstone parameter domain: the `#` option-line keyword.
///
/// The variant name IS the canonical spelling. This enum is the only place
/// any domain name appears in the repository; bindings expose it by
/// reflection. Data read in any domain is converted to S at ingestion; the
/// domain is kept only as metadata ([`Touchstone::parameter`]).
#[derive(Debug, Clone, Copy, PartialEq, Eq, AsRefStr, EnumIter)]
pub enum TouchstoneParameter {
    /// Scattering parameters.
    S,
    /// Admittance parameters.
    Y,
    /// Impedance parameters.
    Z,
    /// Inverse hybrid parameters (2-port only).
    G,
    /// Hybrid parameters (2-port only).
    H,
}

impl TouchstoneParameter {
    /// Whether the domain is defined only for 2-port networks (G/H).
    pub fn requires_two_ports(self) -> bool {
        matches!(self, TouchstoneParameter::G | TouchstoneParameter::H)
    }
}

impl FromStr for TouchstoneParameter {
    type Err = TouchstoneError;

    /// Parse a domain keyword case-insensitively (`"s"`/`"S"`/`"z"` all
    /// match). The offending token is carried in the error.
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        TouchstoneParameter::iter()
            .find(|p| p.as_ref().eq_ignore_ascii_case(s))
            .ok_or_else(|| TouchstoneError::Syntax {
                token: s.to_owned(),
            })
    }
}

/// A Touchstone text data format: how complex numbers are written in the
/// file. Memory always holds complex numbers; this enum only matters at the
/// two text boundaries (parsing a `#` line, rendering with `writeTouchstone`).
#[derive(Debug, Clone, Copy, PartialEq, Eq, AsRefStr, EnumIter)]
pub enum TouchstoneFormat {
    /// Real / Imaginary.
    RI,
    /// Magnitude / Angle (degrees).
    MA,
    /// Decibel (20·log₁₀ magnitude) / Angle (degrees).
    DB,
}

impl FromStr for TouchstoneFormat {
    type Err = TouchstoneError;

    /// Parse a format keyword case-insensitively. The offending token is
    /// carried in the error.
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        TouchstoneFormat::iter()
            .find(|f| f.as_ref().eq_ignore_ascii_case(s))
            .ok_or_else(|| TouchstoneError::Syntax {
                token: s.to_owned(),
            })
    }
}

/// Core parse/construction errors.
///
/// Every variant carries the offending input verbatim so every binding
/// surface can quote it in its raised message (PyValueError / napi Error /
/// JS throw).
#[derive(Debug, Clone, PartialEq, thiserror::Error)]
pub enum TouchstoneError {
    /// Two data rows share the same frequency point — a genuine ambiguity.
    #[error("duplicate frequency point: {f}")]
    DuplicateFrequency {
        /// The repeated frequency in hertz.
        f: f64,
    },
    /// `data.len()` disagrees with `npoints × nports² × 2` (the ×2 is the
    /// interleaved real+imag pair).
    #[error("dimension mismatch: data length {data_len} != npoints {npoints} × nports² {nports_sq} × 2", nports_sq = nports * nports)]
    DimensionMismatch {
        /// Actual data length.
        data_len: usize,
        /// Expected frequency point count.
        npoints: usize,
        /// Port count.
        nports: usize,
    },
    /// A numeric token stream is not divisible by the stride `1 + 2×nports²`
    /// (noise rows mixed in break divisibility → hard error, v1).
    #[error("token count {len} is not divisible by stride {stride} (1 + 2×nports²)")]
    StrideDivisibility {
        /// Total numeric token count.
        len: usize,
        /// Expected stride `1 + 2×nports²`.
        stride: usize,
    },
    /// `z0` length is neither 1 (shared) nor `nports` (per-port).
    #[error("invalid z0 length {len}: must be 1 or nports {nports}")]
    Z0Shape {
        /// Actual z0 length.
        len: usize,
        /// Port count.
        nports: usize,
    },
    /// A malformed token on a `#` option line or data section.
    #[error("syntax error: invalid token {token:?}")]
    Syntax {
        /// The offending token, verbatim.
        token: String,
    },
    /// An HTTP fetch failed; the failure reason is quoted verbatim.
    #[error("fetch failed for {url}: {reason}")]
    Fetch {
        /// The requested URL.
        url: String,
        /// The transport/status failure, verbatim.
        reason: String,
    },
    /// G/H parameters are defined only for 2-port networks.
    #[error("{domain} parameters are defined only for 2-port networks, got {nports} ports")]
    DomainPortCount {
        /// The offending domain, canonical uppercase.
        domain: String,
        /// Actual port count.
        nports: usize,
    },
    /// A filename did not match the Touchstone extension grammar and no
    /// explicit nports was supplied.
    #[error("filename {filename:?} has no .[szygh]Np extension: pass nports explicitly")]
    NportsNoMatch {
        /// The offending filename.
        filename: String,
    },
    /// The file has no `#` option line. The spec requires one ("each
    /// Touchstone data file shall contain an option line"); individual
    /// keywords inside it may be omitted (spec defaults GHz / S / MA /
    /// R 50), but the line itself is mandatory.
    #[error("missing # option line: Touchstone files shall contain one")]
    MissingOptionLine,
    /// A domain reached a conversion path that cannot handle it — an
    /// internal dispatch bug, not user input (public surfaces answer S
    /// from storage before calling the conversion helpers).
    #[error("internal dispatch violation: {domain} reached an unsupported path")]
    DispatchViolation {
        /// The offending domain, canonical uppercase.
        domain: String,
    },
}

/// A parsed Touchstone file: the state class holding the frequency axis,
/// interleaved S data, per-port reference impedance, and metadata.
///
/// Construction IS parsing: every factory ([`Touchstone::from_text`] and the
/// binding-side file/URL factories) returns a fully validated object or a
/// [`TouchstoneError`]. There is no two-phase load.
// The Rust type is plain (no binding attributes): the wasm/napi/pyclass
// wrappers live in the glue crates (same pattern as `Frequency`).
#[derive(Debug)]
pub struct Touchstone {
    /// Frequency axis, canonical Hz, ascending (the single authority).
    frequency: crate::frequency::Frequency,
    /// Interleaved re/im flat S data (governance rule 1).
    s: Vec<f64>,
    /// Per-port real reference impedance (spec forbids complex).
    z0: Vec<f64>,
    /// Port count (redundant with z0 length; hot-path convenience).
    nports: u32,
    /// File stem without extension (empty when unnamed).
    name: String,
    /// Merged `!` comment text.
    comments: String,
    /// `"1.0"` / `"1.1"` — recorded from the file at parse time (R shape),
    /// derived from z0 values only for pure-data construction.
    version: String,
    /// Original parameter domain of the data (metadata; storage is S).
    parameter: TouchstoneParameter,
}

/// Parsed `#` option-line state.
struct OptionLine {
    unit: crate::frequency::FrequencyUnit,
    parameter: TouchstoneParameter,
    format: TouchstoneFormat,
    /// Reference impedances as written: 1 token (v1.0 scalar) or `nports`
    /// tokens (v1.1 per-port). The SHAPE records the version.
    r: Vec<f64>,
}

impl Touchstone {
    /// Parse Touchstone text. `nports` is the explicit port count; when
    /// absent it is inferred from the `path` filename grammar (the name
    /// pipeline). `path`'s directory part is ignored; its stem becomes
    /// [`Touchstone::name`].
    pub fn from_text(
        text: &str,
        nports: Option<usize>,
        path: Option<&str>,
    ) -> Result<Self, TouchstoneError> {
        let mut comments: Vec<&str> = Vec::new();
        let mut option: Option<OptionLine> = None;
        let mut tokens: Vec<f64> = Vec::new();
        for line in text.lines() {
            let line = line.trim();
            if line.is_empty() {
                continue;
            }
            if let Some(c) = line.strip_prefix('!') {
                comments.push(c.trim());
                continue;
            }
            if let Some(o) = line.strip_prefix('#') {
                option = Some(Self::parse_option_line(o)?);
                continue;
            }
            for tok in line.split_whitespace() {
                tokens.push(tok.parse::<f64>().map_err(|_| TouchstoneError::Syntax {
                    token: tok.to_owned(),
                })?);
            }
        }
        // The `#` option line is mandatory (Touchstone spec v2.1: "each
        // Touchstone data file shall contain an option line"). Missing
        // keywords INSIDE it fall back to spec defaults; a missing line is
        // a malformed file and errors.
        let option = option.ok_or(TouchstoneError::MissingOptionLine)?;
        let nports = match nports {
            Some(n) => n,
            None => {
                let filename = path.map(Self::filename_from_path).unwrap_or_default();
                Self::nports_from_filename(&filename)?
            }
        };
        if option.r.len() != 1 && option.r.len() != nports {
            return Err(TouchstoneError::Z0Shape {
                len: option.r.len(),
                nports,
            });
        }
        // v1.0 = scalar R, v1.1 = per-port R (shape, not values).
        let version = if option.r.len() == 1 { "1.0" } else { "1.1" }.to_owned();
        let stride = 1 + 2 * nports * nports;
        if !tokens.len().is_multiple_of(stride) {
            return Err(TouchstoneError::StrideDivisibility {
                len: tokens.len(),
                stride,
            });
        }
        let mut f_raw: Vec<f64> = Vec::with_capacity(tokens.len() / stride);
        let mut s: Vec<f64> = Vec::with_capacity(tokens.len() - tokens.len() / stride);
        for block in tokens.chunks(stride) {
            let (freq, block_s) = Self::parse_data_line(block, option.format, nports);
            f_raw.push(freq);
            s.extend_from_slice(&block_s);
        }
        Self::sort_and_check_f(&mut f_raw, &mut s, nports)?;
        // Storage holds S only: non-S domains convert at ingestion.
        let z0 = if option.r.len() == 1 {
            vec![option.r[0]; nports]
        } else {
            option.r.clone()
        };
        // S is the stored domain: the parsed buffer is kept as-is (no
        // copy — the hot ingestion path); every other domain converts
        // through the shared helper.
        let s = if option.parameter == TouchstoneParameter::S {
            s
        } else {
            Self::convert_to_s(&s, option.parameter, nports, &z0)?
        };
        let name = path
            .map(|p| Self::name_from_filename(&Self::filename_from_path(p)))
            .unwrap_or_default();
        Ok(Self {
            // from_f converts raw (in option.unit) to the Hz master axis and
            // keeps the unit as display metadata (write re-emits it).
            frequency: crate::frequency::Frequency::from_f(f_raw, option.unit),
            s,
            z0,
            nports: nports as u32,
            name,
            comments: comments.join("\n"),
            version,
            parameter: option.parameter,
        })
    }

    /// Fetch Touchstone text over HTTP and parse it via [`Touchstone::from_text`].
    /// The I/O backend is selected inside core by target (iron rule 11):
    /// native uses reqwest (rustls), browser uses `web_sys::fetch` — the
    /// wasm artifact never links reqwest. The URL's last path segment feeds
    /// the name pipeline (nports inference + stem).
    #[cfg(any(
        all(not(target_arch = "wasm32"), feature = "native-http"),
        all(target_arch = "wasm32", feature = "browser-http")
    ))]
    pub async fn from_url(url: &str) -> Result<Self, TouchstoneError> {
        let text = Self::fetch_text(url).await?;
        let path = Self::url_filename(url);
        Self::from_text(&text, None, path.as_deref())
    }

    /// URL → name-pipeline filename: strip any query/fragment so
    /// `https://host/d/filter.s1p?v=2` still names `filter` / infers 1,
    /// then take the last path segment. A bare path (`/`) or empty URL has
    /// no filename — `None`, so nports cannot be inferred from it.
    fn url_filename(url: &str) -> Option<String> {
        let clean = url.split(['?', '#']).next().unwrap_or(url);
        let name = Self::filename_from_path(clean);
        if name.is_empty() { None } else { Some(name) }
    }

    /// Native HTTP backend: reqwest (rustls). Non-2xx surfaces verbatim.
    #[cfg(all(not(target_arch = "wasm32"), feature = "native-http"))]
    async fn fetch_text(url: &str) -> Result<String, TouchstoneError> {
        let resp = reqwest::get(url)
            .await
            .map_err(|e| TouchstoneError::Fetch {
                url: url.to_owned(),
                reason: e.to_string(),
            })?;
        let status = resp.status();
        if !status.is_success() {
            return Err(TouchstoneError::Fetch {
                url: url.to_owned(),
                reason: status.as_str().to_owned(),
            });
        }
        resp.text().await.map_err(|e| TouchstoneError::Fetch {
            url: url.to_owned(),
            reason: e.to_string(),
        })
    }

    /// Browser HTTP backend: `web_sys::fetch` (Promise; main thread never
    /// runs wasm during I/O). Non-OK status surfaces verbatim.
    #[cfg(all(target_arch = "wasm32", feature = "browser-http"))]
    async fn fetch_text(url: &str) -> Result<String, TouchstoneError> {
        let pending = web_sys::window()
            .ok_or_else(|| TouchstoneError::Fetch {
                url: url.to_owned(),
                reason: "no window".to_owned(),
            })?
            .fetch_with_str(url);
        let resp: web_sys::Response = wasm_bindgen_futures::JsFuture::from(pending)
            .await
            .map_err(|e| TouchstoneError::Fetch {
                url: url.to_owned(),
                reason: format!("{e:?}"),
            })?
            .into();
        let ok: bool = resp.ok();
        let status = resp.status();
        if !ok {
            return Err(TouchstoneError::Fetch {
                url: url.to_owned(),
                reason: status.to_string(),
            });
        }
        let text_promise = resp.text().map_err(|e| TouchstoneError::Fetch {
            url: url.to_owned(),
            reason: format!("{e:?}"),
        })?;
        let text = wasm_bindgen_futures::JsFuture::from(text_promise)
            .await
            .map_err(|e| TouchstoneError::Fetch {
                url: url.to_owned(),
                reason: format!("{e:?}"),
            })?;
        text.as_string().ok_or_else(|| TouchstoneError::Fetch {
            url: url.to_owned(),
            reason: "non-utf8 body".to_owned(),
        })
    }

    /// Parse the body of a `#` option line (after the `#`): unit / domain /
    /// format / R (scalar or per-port). Keywords are case-insensitive;
    /// missing keywords fall back to the spec defaults (GHz / S / MA /
    /// R 50 — spec v2.1 Option Line section).
    fn parse_option_line(line: &str) -> Result<OptionLine, TouchstoneError> {
        let mut unit = crate::frequency::FrequencyUnit::GHz;
        let mut parameter = TouchstoneParameter::S;
        let mut format = TouchstoneFormat::MA;
        let mut r: Vec<f64> = Vec::new();
        let mut tokens = line.split_whitespace().peekable();
        while let Some(tok) = tokens.next() {
            if tok.eq_ignore_ascii_case("R") {
                while let Some(v) = tokens.peek() {
                    if v.eq_ignore_ascii_case("R") {
                        break;
                    }
                    let parsed = v.parse::<f64>().map_err(|_| TouchstoneError::Syntax {
                        token: (*v).to_owned(),
                    })?;
                    r.push(parsed);
                    tokens.next();
                }
                continue;
            }
            if let Ok(u) = tok.parse::<crate::frequency::FrequencyUnit>() {
                unit = u;
                continue;
            }
            if let Ok(p) = tok.parse::<TouchstoneParameter>() {
                parameter = p;
                continue;
            }
            if let Ok(f) = tok.parse::<TouchstoneFormat>() {
                format = f;
                continue;
            }
            return Err(TouchstoneError::Syntax {
                token: tok.to_owned(),
            });
        }
        if r.is_empty() {
            r.push(50.0);
        }
        Ok(OptionLine {
            unit,
            parameter,
            format,
            r,
        })
    }

    /// Convert one frequency-point block (`stride = 1 + 2×nports²` tokens,
    /// frequency first) into interleaved re/im pairs. A Touchstone data row
    /// is a formatting unit, not a semantic one — the block may have come
    /// from several physical lines.
    fn parse_data_line(block: &[f64], format: TouchstoneFormat, nports: usize) -> (f64, Vec<f64>) {
        let freq = block[0];
        let pairs = &block[1..];
        let mut s = Vec::with_capacity(pairs.len());
        for pair in pairs.chunks(2) {
            let (a, b) = (pair[0], pair[1]);
            let c = match format {
                TouchstoneFormat::RI => num_complex::Complex64::new(a, b),
                TouchstoneFormat::MA => num_complex::Complex64::from_polar(a, b.to_radians()),
                TouchstoneFormat::DB => {
                    num_complex::Complex64::from_polar(10f64.powf(a / 20.0), b.to_radians())
                }
            };
            s.push(c.re);
            s.push(c.im);
        }
        debug_assert_eq!(s.len(), 2 * nports * nports);
        // Touchstone v1.x 2-port files use N11, N21, N12, N22 column
        // order; swap off-diagonals so internal storage is always
        // row-major (N11, N12, N21, N22) regardless of port count.
        if nports == 2 {
            s.swap(2, 4);
            s.swap(3, 5);
        }
        (freq, s)
    }

    /// Sort frequency points ascending and permute their S blocks along with
    /// them; a duplicate frequency is a genuine ambiguity and errors.
    ///
    /// Frequency boundaries are set by the stride, never by the frequency
    /// order — so rejecting noise (stride divisibility) and accepting
    /// shuffled data (sorting) never conflict.
    fn sort_and_check_f(
        f_hz: &mut [f64],
        s: &mut Vec<f64>,
        nports: usize,
    ) -> Result<(), TouchstoneError> {
        let block = 2 * nports * nports;
        let n = f_hz.len();
        // Detect duplicates before reordering (report the offending value).
        let mut seen: Vec<(f64, usize)> = f_hz
            .iter()
            .copied()
            .enumerate()
            .map(|(i, f)| (f, i))
            .collect();
        seen.sort_by(|a, b| a.0.total_cmp(&b.0));
        for w in seen.windows(2) {
            if w[0].0 == w[1].0 {
                return Err(TouchstoneError::DuplicateFrequency { f: w[0].0 });
            }
        }
        // Ascending permutation, applied to f and its S blocks together.
        let mut order: Vec<usize> = (0..n).collect();
        order.sort_by(|&i, &j| f_hz[i].total_cmp(&f_hz[j]));
        let f_sorted: Vec<f64> = order.iter().map(|&i| f_hz[i]).collect();
        let mut s_sorted: Vec<f64> = Vec::with_capacity(s.len());
        for &i in &order {
            s_sorted.extend_from_slice(&s[i * block..(i + 1) * block]);
        }
        f_hz.copy_from_slice(&f_sorted);
        *s = s_sorted;
        Ok(())
    }

    /// Convert non-S domain data into S (the only stored domain). Shared by
    /// the parser and the data constructor — single implementation. Callers
    /// answer S themselves (storage passthrough, no copy) before calling,
    /// so `parameter` is always one of Z/Y/G/H here.
    ///
    /// Real reference impedances only (spec forbids complex), so the
    /// power-wave and traveling-wave definitions coincide:
    /// `S = √Z0⁻¹ (Z − Z0)(Z + Z0)⁻¹ √Z0` (and the Y-dual
    /// `S = √Z0⁻¹ (I − Z0·Y)(I + Z0·Y)⁻¹ √Z0`). G/H convert to Y/Z first
    /// (2-port closed form; other port counts error).
    // `inline(never)`: keep one instantiation in core so the defensive S
    // arm is not duplicated (uncovered) into every binding binary that
    // inlines this helper. Non-S ingestion already does matrix inversion,
    // so the call boundary is free.
    #[inline(never)]
    fn convert_to_s(
        data: &[f64],
        parameter: TouchstoneParameter,
        nports: usize,
        z0: &[f64],
    ) -> Result<Vec<f64>, TouchstoneError> {
        if parameter.requires_two_ports() && nports != 2 {
            return Err(TouchstoneError::DomainPortCount {
                domain: parameter.as_ref().to_owned(),
                nports,
            });
        }
        let block = 2 * nports * nports;
        let mut out = Vec::with_capacity(data.len());
        for freq_data in data.chunks(block) {
            let m = Self::matrix_from_interleaved(freq_data, nports);
            // Exhaustive match, no wildcard: adding a TouchstoneParameter
            // variant is a compile error here until it is handled — a new
            // domain can never silently fall into another domain's math.
            // S is answered from storage by the callers; reaching the S
            // arm is a dispatch bug (direct-tested below).
            let s_matrix = match parameter {
                TouchstoneParameter::S => {
                    return Err(TouchstoneError::DispatchViolation {
                        domain: parameter.as_ref().to_owned(),
                    });
                }
                TouchstoneParameter::Z => Self::z_to_s(&m, z0),
                TouchstoneParameter::Y => Self::y_to_s(&m, z0),
                TouchstoneParameter::H => Self::z_to_s(&Self::h_to_z(&m), z0),
                TouchstoneParameter::G => Self::y_to_s(&Self::g_to_y(&m), z0),
            };
            Self::push_interleaved(&s_matrix, &mut out);
        }
        Ok(out)
    }

    /// Row-major complex matrix from an interleaved f64 block.
    fn matrix_from_interleaved(data: &[f64], n: usize) -> Vec<Complex64> {
        data.chunks(2)
            .map(|p| Complex64::new(p[0], p[1]))
            .collect::<Vec<_>>()
            .chunks(n)
            .map(|row| row.to_vec())
            .collect::<Vec<_>>()
            .into_iter()
            .flatten()
            .collect()
    }

    /// Append a row-major complex matrix to an interleaved f64 buffer.
    fn push_interleaved(m: &[Complex64], out: &mut Vec<f64>) {
        for c in m {
            out.push(c.re);
            out.push(c.im);
        }
    }

    /// H → Z (2-port): `Z = [[Δh/h22, h12/h22], [-h21/h22, 1/h22]]`.
    fn h_to_z(h: &[Complex64]) -> Vec<Complex64> {
        let (h11, h12, h21, h22) = (h[0], h[1], h[2], h[3]);
        let dh = h11 * h22 - h12 * h21;
        vec![
            dh / h22,
            h12 / h22,
            -h21 / h22,
            Complex64::new(1.0, 0.0) / h22,
        ]
    }

    /// G → Y (2-port): `Y = [[Δg/g22, g12/g22], [-g21/g22, 1/g22]]`.
    fn g_to_y(g: &[Complex64]) -> Vec<Complex64> {
        let (g11, g12, g21, g22) = (g[0], g[1], g[2], g[3]);
        let dg = g11 * g22 - g12 * g21;
        vec![
            dg / g22,
            g12 / g22,
            -g21 / g22,
            Complex64::new(1.0, 0.0) / g22,
        ]
    }

    /// Z → S with real per-port z0: `S = √Z0⁻¹ (Z − Z0)(Z + Z0)⁻¹ √Z0`.
    fn z_to_s(z: &[Complex64], z0: &[f64]) -> Vec<Complex64> {
        let n = z0.len();
        let mut a = z.to_vec();
        let mut b = z.to_vec();
        for i in 0..n {
            for j in 0..n {
                if i == j {
                    a[i * n + j] -= Complex64::new(z0[i], 0.0);
                    b[i * n + j] += Complex64::new(z0[i], 0.0);
                }
            }
        }
        let inv = Self::invert(&b, n);
        let m = Self::mat_mul(&a, &inv, n);
        let mut s = m;
        for i in 0..n {
            for j in 0..n {
                s[i * n + j] *= z0[j].sqrt() / z0[i].sqrt();
            }
        }
        s
    }

    /// Y → S with real per-port z0: `S = √Z0⁻¹ (I − Z0·Y)(I + Z0·Y)⁻¹ √Z0`.
    fn y_to_s(y: &[Complex64], z0: &[f64]) -> Vec<Complex64> {
        let n = z0.len();
        let mut a = Vec::with_capacity(n * n);
        let mut b = Vec::with_capacity(n * n);
        for i in 0..n {
            for j in 0..n {
                let zy = Complex64::new(z0[i], 0.0) * y[i * n + j];
                let id = if i == j {
                    Complex64::new(1.0, 0.0)
                } else {
                    Complex64::new(0.0, 0.0)
                };
                a.push(id - zy);
                b.push(id + zy);
            }
        }
        let inv = Self::invert(&b, n);
        let m = Self::mat_mul(&a, &inv, n);
        let mut s = m;
        for i in 0..n {
            for j in 0..n {
                s[i * n + j] *= z0[j].sqrt() / z0[i].sqrt();
            }
        }
        s
    }

    /// Row-major complex matrix multiply.
    fn mat_mul(a: &[Complex64], b: &[Complex64], n: usize) -> Vec<Complex64> {
        let mut c = vec![Complex64::new(0.0, 0.0); n * n];
        for i in 0..n {
            for k in 0..n {
                let aik = a[i * n + k];
                if aik == Complex64::new(0.0, 0.0) {
                    continue;
                }
                for j in 0..n {
                    c[i * n + j] += aik * b[k * n + j];
                }
            }
        }
        c
    }

    /// Gauss–Jordan inverse of a row-major complex matrix.
    fn invert(m: &[Complex64], n: usize) -> Vec<Complex64> {
        let mut a: Vec<Complex64> = Vec::with_capacity(n * 2 * n);
        for i in 0..n {
            for j in 0..n {
                a.push(m[i * n + j]);
            }
            for j in 0..n {
                a.push(if i == j {
                    Complex64::new(1.0, 0.0)
                } else {
                    Complex64::new(0.0, 0.0)
                });
            }
        }
        let w = 2 * n;
        for col in 0..n {
            let pivot = (col..n)
                .find(|&r| a[r * w + col] != Complex64::new(0.0, 0.0))
                .unwrap_or(col);
            if pivot != col {
                for j in 0..w {
                    a.swap(col * w + j, pivot * w + j);
                }
            }
            let p = a[col * w + col];
            for j in 0..w {
                a[col * w + j] /= p;
            }
            for r in 0..n {
                if r == col {
                    continue;
                }
                let f = a[r * w + col];
                if f == Complex64::new(0.0, 0.0) {
                    continue;
                }
                for j in 0..w {
                    let pivot_val = a[col * w + j];
                    a[r * w + j] -= f * pivot_val;
                }
            }
        }
        let mut out = Vec::with_capacity(n * n);
        for i in 0..n {
            for j in n..2 * n {
                out.push(a[i * w + j]);
            }
        }
        out
    }

    /// The frequency axis in hertz (forwarded from the inner [`Frequency`]).
    pub fn f(&self) -> Vec<f64> {
        self.frequency.f().expect("live object")
    }

    /// The interleaved S data (the stored master copy).
    pub fn s(&self) -> &[f64] {
        &self.s
    }

    /// Build from pure data (no file): frequency axis, interleaved data in
    /// domain `parameter`, scalar-or-per-port real `z0`. The data converts
    /// to S at construction (shared [`Touchstone::convert_to_s`]); version
    /// derives from the z0 VALUES here (all-equal → `"1.0"`, differing →
    /// `"1.1"`) — unlike parsing, which records the version from the file.
    ///
    /// Validation: `data.len() == npoints × nports² × 2`; `z0` length 1 or
    /// nports; no duplicate frequencies (shuffled input sorts ascending);
    /// G/H only for 2 ports.
    pub fn new(
        frequency: &crate::frequency::Frequency,
        data: &[f64],
        z0: &[f64],
        parameter: TouchstoneParameter,
        name: &str,
        comments: &str,
    ) -> Result<Self, TouchstoneError> {
        // nports is inferred from the data shape (npoints known from the
        // axis); z0 must then be scalar or match it.
        let npoints = frequency.npoints().expect("live frequency");
        if !data.len().is_multiple_of(npoints * 2) {
            return Err(TouchstoneError::DimensionMismatch {
                data_len: data.len(),
                npoints,
                nports: 0,
            });
        }
        let cells = data.len() / (npoints * 2);
        let nports = (cells as f64).sqrt().round() as usize;
        if nports * nports != cells {
            return Err(TouchstoneError::DimensionMismatch {
                data_len: data.len(),
                npoints,
                nports,
            });
        }
        if z0.len() != 1 && z0.len() != nports {
            return Err(TouchstoneError::Z0Shape {
                len: z0.len(),
                nports,
            });
        }
        let z0v = if z0.len() == 1 {
            vec![z0[0]; nports]
        } else {
            z0.to_vec()
        };
        let version = if z0v.windows(2).all(|w| w[0] == w[1]) {
            "1.0".to_owned()
        } else {
            "1.1".to_owned()
        };
        let mut f_hz = frequency.f().expect("live frequency");
        let mut s = data.to_vec();
        Self::sort_and_check_f(&mut f_hz, &mut s, nports)?;
        // S is the stored domain: the sorted buffer is kept as-is (no
        // second copy); every other domain converts via the shared helper.
        let s = if parameter == TouchstoneParameter::S {
            s
        } else {
            Self::convert_to_s(&s, parameter, nports, &z0v)?
        };
        Ok(Self {
            frequency: crate::frequency::Frequency::from_f(
                f_hz,
                crate::frequency::FrequencyUnit::Hz,
            ),
            s,
            z0: z0v,
            nports: nports as u32,
            name: name.to_owned(),
            comments: comments.to_owned(),
            version,
            parameter,
        })
    }

    /// Unified data accessor: domain × format. `RI` returns interleaved
    /// re/im; `MA`/`DB` return interleaved (mag|db, deg) real pairs.
    /// `(S, RI)` borrows the stored body (zero copy); everything else is
    /// computed fresh.
    pub fn data(
        &self,
        parameter: TouchstoneParameter,
        format: TouchstoneFormat,
    ) -> Result<std::borrow::Cow<'_, [f64]>, TouchstoneError> {
        use std::borrow::Cow;
        if parameter == TouchstoneParameter::S {
            return match format {
                TouchstoneFormat::RI => Ok(Cow::Borrowed(&self.s)),
                TouchstoneFormat::MA => Ok(Cow::Owned(Self::to_ma(&self.s))),
                TouchstoneFormat::DB => Ok(Cow::Owned(Self::to_db(&self.s))),
            };
        }
        let domain = Self::s_to_domain(&self.s, parameter, self.nports as usize, &self.z0)?;
        Ok(match format {
            TouchstoneFormat::RI => Cow::Owned(domain),
            TouchstoneFormat::MA => Cow::Owned(Self::to_ma(&domain)),
            TouchstoneFormat::DB => Cow::Owned(Self::to_db(&domain)),
        })
    }

    /// Z property: interleaved re/im (computed, not cached).
    pub fn z(&self) -> Vec<f64> {
        Self::s_to_domain(
            &self.s,
            TouchstoneParameter::Z,
            self.nports as usize,
            &self.z0,
        )
        .expect("Z valid for any port count")
    }

    /// Y property.
    pub fn y(&self) -> Vec<f64> {
        Self::s_to_domain(
            &self.s,
            TouchstoneParameter::Y,
            self.nports as usize,
            &self.z0,
        )
        .expect("Y valid for any port count")
    }

    /// G property (2-port only).
    pub fn g(&self) -> Result<Vec<f64>, TouchstoneError> {
        if self.nports != 2 {
            return Err(TouchstoneError::DomainPortCount {
                domain: "G".to_owned(),
                nports: self.nports as usize,
            });
        }
        Ok(
            Self::s_to_domain(&self.s, TouchstoneParameter::G, 2, &self.z0)
                .expect("2-port checked"),
        )
    }

    /// H property (2-port only).
    pub fn h(&self) -> Result<Vec<f64>, TouchstoneError> {
        if self.nports != 2 {
            return Err(TouchstoneError::DomainPortCount {
                domain: "H".to_owned(),
                nports: self.nports as usize,
            });
        }
        Ok(
            Self::s_to_domain(&self.s, TouchstoneParameter::H, 2, &self.z0)
                .expect("2-port checked"),
        )
    }

    /// S → Z/Y/G/H (the backend of the domain shortcut properties and the
    /// non-S branch of [`Touchstone::data`]). S is answered from storage by
    /// the public accessor before this call; the S arm is a defensive error
    /// (direct-tested below), never a silent fallback.
    // `inline(never)`: see `convert_to_s` — one core instantiation keeps
    // the defensive S arm covered.
    #[inline(never)]
    fn s_to_domain(
        s: &[f64],
        domain: TouchstoneParameter,
        nports: usize,
        z0: &[f64],
    ) -> Result<Vec<f64>, TouchstoneError> {
        if matches!(domain, TouchstoneParameter::G | TouchstoneParameter::H) && nports != 2 {
            return Err(TouchstoneError::DomainPortCount {
                domain: domain.as_ref().to_owned(),
                nports,
            });
        }
        let block = 2 * nports * nports;
        let mut out = Vec::with_capacity(s.len());
        for freq_s in s.chunks(block) {
            let m = Self::matrix_from_interleaved(freq_s, nports);
            let z = Self::s_to_z(&m, z0);
            // Exhaustive match, no wildcard: adding a TouchstoneParameter
            // variant is a compile error here until it is handled — a new
            // domain can never silently compute as another domain. S is
            // answered from storage by the public accessor before this
            // call; reaching the S arm is a dispatch bug (tested below).
            let d = match domain {
                TouchstoneParameter::S => {
                    return Err(TouchstoneError::DispatchViolation {
                        domain: domain.as_ref().to_owned(),
                    });
                }
                TouchstoneParameter::Z => z.clone(),
                TouchstoneParameter::Y => Self::invert(&z, nports),
                TouchstoneParameter::G => Self::z_to_g(&z),
                TouchstoneParameter::H => Self::z_to_h(&z),
            };
            Self::push_interleaved(&d, &mut out);
        }
        Ok(out)
    }

    /// S → Z with real per-port z0: `Z = √z0 (I+S)(I−S)⁻¹ √z0` (the exact
    /// inverse of [`Touchstone::z_to_s`]).
    fn s_to_z(s: &[Complex64], z0: &[f64]) -> Vec<Complex64> {
        let n = z0.len();
        let mut a = Vec::with_capacity(n * n);
        let mut b = Vec::with_capacity(n * n);
        for i in 0..n {
            for j in 0..n {
                let id = if i == j {
                    Complex64::new(1.0, 0.0)
                } else {
                    Complex64::new(0.0, 0.0)
                };
                a.push(id + s[i * n + j]);
                b.push(id - s[i * n + j]);
            }
        }
        let inv = Self::invert(&b, n);
        let m = Self::mat_mul(&a, &inv, n);
        let mut z = m;
        for i in 0..n {
            for j in 0..n {
                z[i * n + j] *= (z0[i] * z0[j]).sqrt();
            }
        }
        z
    }

    /// Z → G (2-port), from the port definitions
    /// (`I1 = G11·V1 + G12·I2`, `V2 = G21·V1 + G22·I2`):
    /// `G = [[1/z11, -z12/z11],[z21/z11, Δz/z11]]`.
    fn z_to_g(z: &[Complex64]) -> Vec<Complex64> {
        let (z11, z12, z21, z22) = (z[0], z[1], z[2], z[3]);
        let dz = z11 * z22 - z12 * z21;
        vec![
            Complex64::new(1.0, 0.0) / z11,
            -z12 / z11,
            z21 / z11,
            dz / z11,
        ]
    }

    /// Z → H (2-port), from the port definitions
    /// (`V1 = H11·I1 + H12·V2`, `I2 = H21·I1 + H22·V2`):
    /// `H = [[Δz/z22, z12/z22],[-z21/z22, 1/z22]]`.
    fn z_to_h(z: &[Complex64]) -> Vec<Complex64> {
        let (z11, z12, z21, z22) = (z[0], z[1], z[2], z[3]);
        let dz = z11 * z22 - z12 * z21;
        vec![
            dz / z22,
            z12 / z22,
            -z21 / z22,
            Complex64::new(1.0, 0.0) / z22,
        ]
    }

    /// Complex interleaved → (mag, deg) pairs. Angles in degrees (spec).
    fn to_ma(data: &[f64]) -> Vec<f64> {
        data.chunks(2)
            .flat_map(|p| {
                let c = Complex64::new(p[0], p[1]);
                [c.norm(), c.arg().to_degrees()]
            })
            .collect()
    }

    /// Complex interleaved → (db, deg) pairs. dB = 20·log₁₀|c| (spec:
    /// S-parameters are amplitude ratios).
    fn to_db(data: &[f64]) -> Vec<f64> {
        data.chunks(2)
            .flat_map(|p| {
                let c = Complex64::new(p[0], p[1]);
                [20.0 * c.norm().log10(), c.arg().to_degrees()]
            })
            .collect()
    }

    /// Per-port reference impedance.
    pub fn z0(&self) -> &[f64] {
        &self.z0
    }

    /// Build the full write path (private: a property cannot take a
    /// parameter, and the native branch hides `is_dir()` disk I/O; the
    /// public `name`/`parameter`/`nports` already let users compose the
    /// name themselves). `parameter` is the domain actually being written
    /// (the write verb's argument), so the extension always matches the
    /// file's real content. Four shapes:
    /// - empty → `name.{P}Np`
    /// - directory → `dir/name.{P}Np` (native `is_dir()` probe)
    /// - dir+name → append `.{P}Np`
    /// - dir+name+extension → grammar-strip, rebuild the correct extension
    ///   (domain letter = real written parameter, n = real nports — a wrong
    ///   extension is mechanically impossible).
    fn write_path(&self, path: Option<&str>, parameter: TouchstoneParameter) -> String {
        // Lowercase extension (`.z2p`): the closed grammar `\.[ghsyz]\d+p`
        // in its canonical written form, matching the spec scenarios.
        let ext = format!(
            ".{}{}p",
            parameter.as_ref().to_ascii_lowercase(),
            self.nports
        );
        let name_ext = format!("{}{}", self.name, ext);
        let Some(path) = path else {
            return name_ext;
        };
        if path.is_empty() {
            return name_ext;
        }
        // Native: an existing directory segment gets the default name.
        // A trailing slash is the portable directory signal (the browser
        // has no filesystem to probe with `is_dir`).
        if path.ends_with('/') || std::path::Path::new(path).is_dir() {
            return format!("{}/{}", path.trim_end_matches('/'), name_ext);
        }
        let filename = Self::filename_from_path(path);
        let stem = Self::name_from_filename(&filename);
        let parent = &path[..path.len() - filename.len()];
        format!("{parent}{stem}{ext}")
    }

    /// Render Touchstone text: `#` option line (stored version — never
    /// re-derived) + comments + data rows in `parameter`/`format`.
    /// Numbers use shortest-roundtrip formatting (write→read bit-exact).
    pub fn write_touchstone(
        &self,
        parameter: TouchstoneParameter,
        format: TouchstoneFormat,
    ) -> Result<String, TouchstoneError> {
        let mut out = String::new();
        for c in self.comments.lines() {
            out.push_str(&format!("! {c}\n"));
        }
        out.push_str(&format!(
            "# {} {} {} R {}",
            // Option-line keywords are canonical uppercase (spec spelling:
            // GHZ/MA/RI...), matching the write-uppercase ruling.
            self.frequency
                .unit()
                .expect("owned axis, never dropped")
                .as_ref()
                .to_ascii_uppercase(),
            parameter.as_ref(),
            format.as_ref(),
            // v1.0 writes a single R; v1.1 writes per-port R (stored version).
            if self.version == "1.0" {
                self.z0[0].to_string()
            } else {
                self.z0
                    .iter()
                    .map(|v| Self::format_number(*v))
                    .collect::<Vec<_>>()
                    .join(" ")
            }
        ));
        out.push('\n');
        let n = self.nports as usize;
        let stride = 1 + 2 * n * n;
        let block = 2 * n * n;
        let mut domain = self.data(parameter, format)?.into_owned();
        // Internal storage is row-major (N11, N12, N21, N22); v1.x
        // 2-port files use N11, N21, N12, N22 — swap off-diagonals
        // back at the I/O boundary so consumers never see a special
        // 2-port order.
        if n == 2 {
            for blk in domain.chunks_mut(block) {
                blk.swap(2, 4);
                blk.swap(3, 5);
            }
        }
        // Frequencies are written in the display unit carried by the axis
        // (the file's unit when parsed; Hz for pure-data construction).
        let f = self
            .frequency
            .f_scaled()
            .expect("owned axis, never dropped");
        for (fi, freq) in f.iter().enumerate() {
            let row = &domain[fi * block..(fi + 1) * block];
            let mut parts = Vec::with_capacity(stride);
            parts.push(Self::format_number(*freq));
            parts.extend(row.iter().map(|v| Self::format_number(*v)));
            out.push_str(&parts.join(" "));
            out.push('\n');
        }
        Ok(out)
    }

    /// Shortest-roundtrip decimal: the shortest digit string that parses
    /// back to the exact same f64 (`to_string` is shortest-roundtrip since
    /// Rust 1.0 — verified by the roundtrip tests, no extra dependency).
    fn format_number(v: f64) -> String {
        if v == 0.0 {
            // Distinguish signed zero so roundtrip preserves the sign bit.
            if v.is_sign_negative() {
                "-0".to_owned()
            } else {
                "0".to_owned()
            }
        } else {
            let s = v.to_string();
            debug_assert_eq!(s.parse::<f64>(), Ok(v), "shortest-roundtrip broken");
            s
        }
    }

    /// Native file write: `write_path` + `std::fs::write` (cfg native).
    pub fn write_file(
        &self,
        path: &str,
        parameter: TouchstoneParameter,
        format: TouchstoneFormat,
    ) -> Result<(), TouchstoneError> {
        let full = self.write_path(Some(path), parameter);
        let text = self.write_touchstone(parameter, format)?;
        std::fs::write(&full, text).map_err(|e| TouchstoneError::Syntax {
            token: format!("{full}: {e}"),
        })
    }

    /// Port count.
    pub fn nports(&self) -> u32 {
        self.nports
    }

    /// File stem without extension.
    pub fn name(&self) -> &str {
        &self.name
    }

    /// Merged comment text.
    pub fn comments(&self) -> &str {
        &self.comments
    }

    /// File format version, `"1.0"` / `"1.1"`.
    pub fn version(&self) -> &str {
        &self.version
    }

    /// Original parameter domain (metadata).
    pub fn parameter(&self) -> TouchstoneParameter {
        self.parameter
    }

    /// Path/URL → filename with extension (last path segment).
    pub fn filename_from_path(path: &str) -> String {
        std::path::Path::new(path)
            .file_name()
            .map(|n| n.to_string_lossy().into_owned())
            .unwrap_or_default()
    }

    /// Filename → stem: strip a trailing Touchstone extension
    /// (`.s2p`/`.Z4p`…, grammar `\.[ghsyz]\d+p`, case-insensitive). On no
    /// match the whole string is returned unstripped — never a
    /// "last dot" guess (`2026.10.09` keeps `.09`).
    pub fn name_from_filename(filename: &str) -> String {
        match Self::ext_match(filename) {
            Some(start) => filename[..start].to_owned(),
            None => filename.to_owned(),
        }
    }

    /// Filename → port count from the Touchstone extension grammar.
    /// No match is an error guiding the caller to pass nports explicitly.
    pub fn nports_from_filename(filename: &str) -> Result<usize, TouchstoneError> {
        match Self::ext_match(filename) {
            Some(start) => {
                // grammar: '.' + domain letter + digits + 'p'
                let digits = &filename[start + 2..filename.len() - 1];
                digits
                    .parse::<usize>()
                    .map_err(|_| TouchstoneError::NportsNoMatch {
                        filename: filename.to_owned(),
                    })
            }
            None => Err(TouchstoneError::NportsNoMatch {
                filename: filename.to_owned(),
            }),
        }
    }

    /// Byte offset where the trailing Touchstone extension grammar
    /// (`\.[ghsyz]\d+p$`, case-insensitive) begins, or `None` when the
    /// filename does not match. Only the LAST dot is considered, and the
    /// grammar must run to the end of the string.
    fn ext_match(filename: &str) -> Option<usize> {
        let i = filename.rfind('.')?;
        // need at least: '.' + domain + digit(s) + 'p'
        let bytes = filename.as_bytes();
        if i + 3 > bytes.len() {
            return None;
        }
        let domain = bytes[i + 1];
        if !matches!(
            domain.to_ascii_lowercase(),
            b'g' | b'h' | b's' | b'y' | b'z'
        ) {
            return None;
        }
        if !bytes[bytes.len() - 1].eq_ignore_ascii_case(&b'p') {
            return None;
        }
        let digits = &bytes[i + 2..bytes.len() - 1];
        if digits.is_empty() || !digits.iter().all(u8::is_ascii_digit) {
            return None;
        }
        Some(i)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn two_port_z() -> Touchstone {
        let text = "# GHZ Z RI R 50\n1.0 50 0 0 0 0 0 50 0";
        Touchstone::from_text(text, Some(2), Some("/tmp/dir/x.s2p")).unwrap()
    }

    #[test]
    fn write_path_empty_uses_name() {
        assert_eq!(
            two_port_z().write_path(None, TouchstoneParameter::Z),
            "x.z2p"
        );
    }

    #[test]
    fn write_path_directory_appends_name() {
        let dir = std::env::temp_dir().join("netwave_wp_dir");
        std::fs::create_dir_all(&dir).unwrap();
        let p = two_port_z().write_path(Some(dir.to_str().unwrap()), TouchstoneParameter::Z);
        assert_eq!(p, format!("{}/x.z2p", dir.to_str().unwrap()));
        std::fs::remove_dir_all(&dir).ok();
    }

    #[test]
    fn write_path_dir_plus_name_appends_extension() {
        let p = two_port_z().write_path(Some("/tmp/outdir/renamed"), TouchstoneParameter::Z);
        assert_eq!(p, "/tmp/outdir/renamed.z2p");
    }

    #[test]
    fn write_path_wrong_extension_rebuilt() {
        let p = two_port_z().write_path(Some("/tmp/outdir/renamed.s3p"), TouchstoneParameter::Z);
        assert_eq!(p, "/tmp/outdir/renamed.z2p");
    }

    #[test]
    fn write_path_written_domain_not_stored_domain() {
        // S-domain object writing Z data: extension follows the WRITTEN
        // domain (the verb argument), keeping name and content consistent.
        let text = "# GHZ S RI R 50\n1.0 0.5 0.25";
        let ts = Touchstone::from_text(text, Some(1), Some("/tmp/d/a.s1p")).unwrap();
        assert_eq!(
            ts.write_path(Some("/tmp/d/a.s1p"), TouchstoneParameter::Z),
            "/tmp/d/a.z1p"
        );
    }

    #[test]
    fn write_path_empty_string_uses_name() {
        assert_eq!(
            two_port_z().write_path(Some(""), TouchstoneParameter::Z),
            "x.z2p"
        );
    }

    #[test]
    fn url_filename_strips_query_and_detects_empty() {
        assert_eq!(
            Touchstone::url_filename("http://h/d/filter.s1p?v=2").as_deref(),
            Some("filter.s1p")
        );
        // A bare path has no filename: nports cannot be inferred from it.
        assert_eq!(Touchstone::url_filename(""), None);
    }

    #[test]
    fn s_to_domain_rejects_s_as_dispatch_violation() {
        // Private helper: public surfaces answer S from storage before
        // calling, so S here is a dispatch bug and must error, never
        // silently compute as another domain.
        let err =
            Touchstone::s_to_domain(&[0.0, 0.0], TouchstoneParameter::S, 1, &[50.0]).unwrap_err();
        // to_string() also exercises the Display arm of the error variant.
        assert!(
            err.to_string().contains("internal dispatch violation: S"),
            "{err}"
        );
    }

    #[test]
    fn convert_to_s_rejects_s_as_dispatch_violation() {
        // Private helper: callers pass S through untouched, so S here is a
        // dispatch bug and must error, never silently copy or convert.
        let err = Touchstone::convert_to_s(&[0.0; 8], TouchstoneParameter::S, 2, &[50.0, 50.0])
            .unwrap_err();
        assert!(
            err.to_string().contains("internal dispatch violation: S"),
            "{err}"
        );
    }
}

/// Wrap an owned f64 block as a `Float64Array` for the worker reply
/// (structured-cloned across the realm boundary).
#[cfg(all(feature = "browser", not(feature = "node"), not(coverage)))]
fn f64_array(v: &[f64]) -> JsValue {
    js_sys::Float64Array::from(v).into()
}

/// Read a domain/format keyword from a JS string argument (core `FromStr`
/// quotes the offending token in the error).
#[cfg(all(feature = "browser", not(feature = "node"), not(coverage)))]
fn js_ts_kw<T: FromStr>(v: &JsValue) -> Result<T, JsValue>
where
    T::Err: std::fmt::Display,
{
    v.as_string()
        .ok_or_else(|| crate::resources::js("argument must be a string"))
        .and_then(|s| T::from_str(&s).map_err(|e| crate::resources::js(e.to_string())))
}

/// Instance dispatch: the numeric-handle half of the shell's `Touchstone`.
/// `drop` never reaches here — the dispatcher intercepts it (removing the
/// table entry is the table's own operation).
#[cfg(all(feature = "browser", not(feature = "node"), not(coverage)))]
impl crate::resources::Resource for Touchstone {
    fn call(&mut self, method: &str, args: &[JsValue]) -> Result<JsValue, JsValue> {
        use crate::resources::{js, js_object, unknown_method};
        let n = self.nports() as usize;
        match method {
            "s" => Ok(f64_array(self.s())),
            "z" => Ok(f64_array(&self.z())),
            "y" => Ok(f64_array(&self.y())),
            "g" => self
                .g()
                .map(|v| f64_array(&v))
                .map_err(|e| js(e.to_string())),
            "h" => self
                .h()
                .map(|v| f64_array(&v))
                .map_err(|e| js(e.to_string())),
            "f" => Ok(f64_array(&self.f())),
            "z0" => Ok(f64_array(self.z0())),
            "nports" => Ok(JsValue::from_f64(self.nports() as f64)),
            "name" => Ok(JsValue::from_str(self.name())),
            "comments" => Ok(JsValue::from_str(self.comments())),
            "version" => Ok(JsValue::from_str(self.version())),
            "parameter" => Ok(JsValue::from_str(self.parameter().as_ref())),
            "data" => {
                let p = js_ts_kw(args.first().ok_or_else(|| js("parameter required"))?)?;
                let f = js_ts_kw(args.get(1).ok_or_else(|| js("format required"))?)?;
                let nf = self.f().len();
                let cow = self.data(p, f).map_err(|e| js(e.to_string()))?;
                // JS has no complex type: every format crosses as flat
                // interleaved pairs, so the shape always ends in 2.
                let shape = js_sys::Array::of4(
                    &JsValue::from_f64(nf as f64),
                    &JsValue::from_f64(n as f64),
                    &JsValue::from_f64(n as f64),
                    &JsValue::from_f64(2.0),
                );
                Ok(js_object(&[
                    ("values", f64_array(&cow)),
                    ("shape", shape.into()),
                ]))
            }
            "writeTouchstone" => {
                let p = js_ts_kw(args.first().ok_or_else(|| js("parameter required"))?)?;
                let f = js_ts_kw(args.get(1).ok_or_else(|| js("format required"))?)?;
                self.write_touchstone(p, f)
                    .map(|t| JsValue::from_str(&t))
                    .map_err(|e| js(e.to_string()))
            }
            // The browser has no filesystem: render in core and hand
            // `{text, filename}` back (structured clone); the shell's Blob +
            // `<a download>` is the platform glue (ironclad rule 8/11).
            "writeFile" => {
                let p = js_ts_kw(args.first().ok_or_else(|| js("parameter required"))?)?;
                let f = js_ts_kw(args.get(1).ok_or_else(|| js("format required"))?)?;
                let path = crate::resources::arg_opt_str(args, 2);
                let text = self.write_touchstone(p, f).map_err(|e| js(e.to_string()))?;
                let filename = self.write_path(path.as_deref(), p);
                Ok(js_object(&[
                    ("text", JsValue::from_str(&text)),
                    ("filename", JsValue::from_str(&filename)),
                ]))
            }
            _ => Err(unknown_method("touchstone", method)),
        }
    }
}

/// Namespace dispatch: the `"touchstone"` namespace's factories and the name
/// pipeline (mechanical camelCase of the core snake names).
#[cfg(all(feature = "browser", not(feature = "node"), not(coverage)))]
pub fn call_namespace(method: &str, args: &[JsValue]) -> Result<JsValue, JsValue> {
    use crate::resources::{arg_opt_str, arg_str, insert, js, unknown_method};
    match method {
        "fromText" => {
            let text = arg_str(args, 0)?;
            let nports = args.get(1).and_then(|v| v.as_f64()).map(|v| v as usize);
            let path = arg_opt_str(args, 2);
            let ts = Touchstone::from_text(&text, nports, path.as_deref())
                .map_err(|e| js(e.to_string()))?;
            Ok(JsValue::from_f64(insert(Box::new(ts)) as f64))
        }
        // The bytes arrive transferred from the shell (`fromFile(file)`);
        // the filename rides along for the name pipeline.
        "fromBytes" => {
            let bytes = args
                .get(0)
                .and_then(|v| v.dyn_ref::<js_sys::Uint8Array>())
                .map(js_sys::Uint8Array::to_vec)
                .ok_or_else(|| js("argument 0 must be a Uint8Array"))?;
            let path = arg_str(args, 1)?;
            let text = String::from_utf8(bytes).map_err(|e| js(e.to_string()))?;
            let ts =
                Touchstone::from_text(&text, None, Some(&path)).map_err(|e| js(e.to_string()))?;
            Ok(JsValue::from_f64(insert(Box::new(ts)) as f64))
        }
        // Async in core (web_sys::fetch): the worker awaits the Promise
        // before posting the reply, so the main thread never runs wasm.
        #[cfg(feature = "browser-http")]
        "fromUrl" => {
            let url = arg_str(args, 0)?;
            let promise = wasm_bindgen_futures::future_to_promise(async move {
                Touchstone::from_url(&url)
                    .await
                    .map(|ts| JsValue::from_f64(insert(Box::new(ts)) as f64))
                    .map_err(|e| js(e.to_string()))
            });
            Ok(promise.into())
        }
        "filenameFromPath" => Ok(JsValue::from_str(&Touchstone::filename_from_path(
            &arg_str(args, 0)?,
        ))),
        "nameFromFilename" => Ok(JsValue::from_str(&Touchstone::name_from_filename(
            &arg_str(args, 0)?,
        ))),
        "nportsFromFilename" => Touchstone::nports_from_filename(&arg_str(args, 0)?)
            .map(|n| JsValue::from_f64(n as f64))
            .map_err(|e| js(e.to_string())),
        _ => Err(unknown_method("touchstone", method)),
    }
}

/// Mount the `"touchstone"` namespace. Called once from the
/// `#[wasm_bindgen(start)]` hook in `lib.rs`.
#[cfg(all(feature = "browser", not(feature = "node"), not(coverage)))]
pub fn register() {
    crate::resources::register_namespace("touchstone", call_namespace);
}
