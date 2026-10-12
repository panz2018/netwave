//! netwave Python binding (borrowed-view form).
//!
//! Zero-copy end state: core allocates the memory; the `Touchstone` pyclass
//! is attached as the returned array's base object — the ndarray has
//! `owndata=False`, so Python writes land directly in core memory; the
//! pyclass drops (freeing the memory) when the array is garbage collected
//! (numpy's base reference guarantees the view never outlives the data).

use std::str::FromStr;

use netwave::frequency::Frequency as CoreFrequency;
use netwave::frequency::FrequencyUnit;
use netwave::frequency::WavelengthUnit;
use netwave::touchstone::Touchstone as CoreTouchstone;
use netwave::touchstone::TouchstoneFormat;
use netwave::touchstone::TouchstoneParameter;
use numpy::Complex64;
use numpy::ndarray;
use numpy::{IntoPyArray, PyArray1, PyArray3, PyReadonlyArray1};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

/// Map a core `TouchstoneError` to `PyValueError` quoting the offending
/// input verbatim (the error Display carries it, single-source in core).
fn ts_err(e: netwave::touchstone::TouchstoneError) -> PyErr {
    PyValueError::new_err(e.to_string())
}

/// Read a `TouchstoneParameter` from a string (case-insensitive; the
/// offending token is quoted in the error).
fn arg_ts_str<T: FromStr>(s: &str) -> PyResult<T>
where
    T::Err: std::fmt::Display,
{
    T::from_str(s).map_err(|e| PyValueError::new_err(e.to_string()))
}

/// Read a frequency/wavelength argument that may be an array OR a scalar
/// (a scalar is a single point). Tries the 1-D array first, falls back to
/// a scalar f64. The union lives here in the binding (ironclad rule 11:
/// the shell never computes, the搬运 is in the rust binding段).
fn arg_f64_vec(obj: &Bound<'_, PyAny>) -> PyResult<Vec<f64>> {
    if let Ok(arr) = obj.extract::<PyReadonlyArray1<f64>>() {
        return Ok(arr.as_slice()?.to_vec());
    }
    if let Ok(v) = obj.extract::<Vec<f64>>() {
        return Ok(v);
    }
    Ok(vec![obj.extract::<f64>()?])
}

/// Read a `FrequencyUnit` from an enum member OR a string (case-insensitive,
/// core `FromStr` carries the offending input in the error).
// `not(coverage)`: core drops the pyclass attribute under cfg(coverage),
// so the cast below cannot compile there (two-sided glue sync).
#[cfg(not(coverage))]
fn arg_frequency_unit(obj: &Bound<'_, PyAny>) -> PyResult<FrequencyUnit> {
    if let Ok(u) = obj.cast::<FrequencyUnit>() {
        return Ok(*u.borrow());
    }
    FrequencyUnit::from_str(&obj.extract::<String>()?)
        .map_err(|e| PyValueError::new_err(e.to_string()))
}

/// Read a `WavelengthUnit` from an enum member OR a string (same shape as
/// [`arg_frequency_unit`]).
#[cfg(not(coverage))]
fn arg_wavelength_unit(obj: &Bound<'_, PyAny>) -> PyResult<WavelengthUnit> {
    if let Ok(u) = obj.cast::<WavelengthUnit>() {
        return Ok(*u.borrow());
    }
    WavelengthUnit::from_str(&obj.extract::<String>()?)
        .map_err(|e| PyValueError::new_err(e.to_string()))
}

// Stub generation (feature `stub-gen` only): registers the public functions
// and classes with pyo3-stub-gen so `stub_gen` emits `netwave/_netwave.pyi`.
#[cfg(feature = "stub-gen")]
use pyo3_stub_gen::define_stub_info_gatherer;
#[cfg(feature = "stub-gen")]
use pyo3_stub_gen::derive::{gen_stub_pyclass, gen_stub_pymethods};

/// A frequency sweep. `from_f`/`from_wavelength` are the data entries
/// (static factories, core names verbatim); the accessors are read-only
/// properties (`f` returns a COPY — scikit-rf `f` is a pure getter); `unit`
/// is a getter (returns the enum) + setter (enum | str); `drop` is the
/// deterministic manual reclamation shared with RAII. Post-drop access
/// raises `ValueError`.
#[cfg_attr(feature = "stub-gen", gen_stub_pyclass(module = "netwave._netwave"))]
#[pyclass]
pub struct Frequency(CoreFrequency);

// `not(coverage)`: the method signatures reference core's
// FrequencyUnit/WavelengthUnit, whose pyclass attributes core drops under
// cfg(coverage) — the pymethods cannot compile there (two-sided glue sync;
// the class registration in the module is gated the same way).
#[cfg(not(coverage))]
#[cfg_attr(feature = "stub-gen", gen_stub_pymethods)]
#[pymethods]
impl Frequency {
    /// Build a sweep from points in `unit` (enum | str, required — never
    /// defaults to Hz) stored as f64 hertz. `f` accepts an array or a
    /// scalar (single point).
    #[staticmethod]
    fn from_f(f: &Bound<'_, PyAny>, unit: &Bound<'_, PyAny>) -> PyResult<Self> {
        let v = arg_f64_vec(f)?;
        let unit = arg_frequency_unit(unit)?;
        Ok(Self(CoreFrequency::from_f(v, unit)))
    }

    /// Build a sweep from wavelength points in `wl_unit` (enum | str) through
    /// a medium of phase index `n` (required): `f = c / (n × λ)`.
    #[staticmethod]
    fn from_wavelength(
        wl: &Bound<'_, PyAny>,
        wl_unit: &Bound<'_, PyAny>,
        n: f64,
    ) -> PyResult<Self> {
        let v = arg_f64_vec(wl)?;
        let wl_unit = arg_wavelength_unit(wl_unit)?;
        Ok(Self(CoreFrequency::from_wavelength(v, wl_unit, n)))
    }

    /// The frequency axis in hertz — a fresh COPY (read-only contract).
    #[getter]
    fn f<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyArray1<f64>>> {
        Ok(PyArray1::from_slice(
            py,
            &self
                .0
                .f()
                .map_err(|e| PyValueError::new_err(e.to_string()))?,
        ))
    }

    /// The axis in the current display unit (`f / multiplier`), derived.
    #[getter]
    fn f_scaled<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyArray1<f64>>> {
        Ok(PyArray1::from_slice(
            py,
            &self
                .0
                .f_scaled()
                .map_err(|e| PyValueError::new_err(e.to_string()))?,
        ))
    }

    /// Angular frequency ω = 2πf (rad/s), derived.
    #[getter]
    fn w<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyArray1<f64>>> {
        Ok(PyArray1::from_slice(
            py,
            &self
                .0
                .w()
                .map_err(|e| PyValueError::new_err(e.to_string()))?,
        ))
    }

    /// The display unit (getter returns the enum, not a string — ironclad
    /// rule 10 deviation, filed in design.md).
    #[getter]
    fn unit(&self) -> PyResult<FrequencyUnit> {
        self.0
            .unit()
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// Set the display unit (enum | str, case-insensitive; illegal string
    /// raises `ValueError` quoting the input). Only metadata changes.
    #[setter]
    fn set_unit(&mut self, unit: &Bound<'_, PyAny>) -> PyResult<()> {
        let unit = arg_frequency_unit(unit)?;
        self.0.set_unit(unit);
        Ok(())
    }

    /// Wavelength λ = c / (n × f) in `wl_unit` (enum | str); DC → inf.
    fn wavelength<'py>(
        &self,
        py: Python<'py>,
        wl_unit: &Bound<'_, PyAny>,
        n: f64,
    ) -> PyResult<Bound<'py, PyArray1<f64>>> {
        let wl_unit = arg_wavelength_unit(wl_unit)?;
        Ok(PyArray1::from_slice(
            py,
            &self
                .0
                .wavelength(wl_unit, n)
                .map_err(|e| PyValueError::new_err(e.to_string()))?,
        ))
    }

    /// An independent copy with the same axis and unit.
    fn copy(&self) -> PyResult<Self> {
        self.0
            .copy()
            .map(Self)
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// Number of frequency points. Raises `ValueError` after `drop()`.
    fn npoints(&self) -> PyResult<usize> {
        self.0
            .npoints()
            .map_err(|e| PyValueError::new_err(e.to_string()))
    }

    /// `len(f)` — the protocol hook delegating one line to `npoints`
    /// (ironclad rule 9).
    fn __len__(&self) -> PyResult<usize> {
        self.npoints()
    }

    /// The cross-end uniform display string (core `Display`, single source).
    fn __str__(&self) -> String {
        self.0.to_string()
    }

    /// `repr(f)` — same string as `__str__` (design.md D6).
    fn __repr__(&self) -> String {
        self.0.to_string()
    }

    /// Deterministic manual reclamation (the unified cross-end verb).
    /// Idempotent; post-drop access raises `ValueError`.
    fn drop(&mut self) {
        self.0.drop();
    }
}

/// A parsed Touchstone file / pure-data network: the state class holding the
/// frequency axis, interleaved S master data, per-port z0, and metadata.
/// Construction IS parsing — the factories (`from_text`/`from_file`/
/// `from_url`/`from_data`) return a fully validated object or raise
/// `ValueError` quoting the offending input (ironclad rule 15: no bare
/// constructor on any end).
#[cfg_attr(feature = "stub-gen", gen_stub_pyclass(module = "netwave._netwave"))]
#[pyclass]
pub struct Touchstone(CoreTouchstone, bool);

impl Touchstone {
    /// Guard shared by every instance accessor: a dropped shell must not hand
    /// back stale data (memory-lifecycle spec — post-drop access raises
    /// `ValueError`). Already-acquired views stay valid (the buffer is never
    /// cleared; the pyclass owns it and numpy's base reference keeps it alive).
    fn core(&self) -> PyResult<&CoreTouchstone> {
        if self.1 {
            return Err(PyValueError::new_err("Touchstone is dropped"));
        }
        Ok(&self.0)
    }
}

// `not(coverage)`: the method signatures reference core's plain
// TouchstoneParameter/TouchstoneFormat enums parsed from strings; the class
// registration is gated the same way as the other pyclasses.
#[cfg(not(coverage))]
#[cfg_attr(feature = "stub-gen", gen_stub_pymethods)]
#[pymethods]
impl Touchstone {
    /// Pure-data factory (ironclad rule 15 — construction only through
    /// `fromX` factories, never a bare constructor): `frequency` is a
    /// `Frequency` object (the axis authority); `data` is a flat interleaved
    /// re/im sequence in domain `parameter`; `z0` a scalar or per-port real;
    /// `parameter` (S/Z/Y/G/H) is required — a silent default S would store
    /// Z data as S.
    #[staticmethod]
    #[pyo3(signature = (frequency, data, z0, parameter, name = "", comments = ""))]
    fn from_data(
        frequency: &Frequency,
        data: &Bound<'_, PyAny>,
        z0: &Bound<'_, PyAny>,
        parameter: &str,
        name: &str,
        comments: &str,
    ) -> PyResult<Self> {
        let data = arg_f64_vec(data)?;
        let z0 = arg_f64_vec(z0)?;
        let parameter = arg_ts_str::<TouchstoneParameter>(parameter)?;
        CoreTouchstone::from_data(&frequency.0, &data, &z0, parameter, name, comments)
            .map(|t| Touchstone(t, false))
            .map_err(ts_err)
    }

    /// Parse Touchstone text. `nports` explicit, else inferred from the
    /// `path` filename grammar; `path`'s stem becomes `name`.
    #[staticmethod]
    #[pyo3(signature = (text, nports = None, path = None))]
    fn from_text(text: &str, nports: Option<usize>, path: Option<&str>) -> PyResult<Self> {
        CoreTouchstone::from_text(text, nports, path)
            .map(|t| Touchstone(t, false))
            .map_err(ts_err)
    }

    /// Read and parse a file (sync; the GIL is released during I/O).
    #[staticmethod]
    fn from_file(py: Python<'_>, path: &str) -> PyResult<Self> {
        let owned = path.to_owned();
        py.detach(|| {
            let text = std::fs::read_to_string(&owned)
                .map_err(|e| PyValueError::new_err(format!("{owned}: {e}")))?;
            let filename = CoreTouchstone::filename_from_path(&owned);
            CoreTouchstone::from_text(&text, None, Some(&filename))
                .map(|t| Touchstone(t, false))
                .map_err(ts_err)
        })
    }

    /// Fetch over HTTP and parse (sync; the GIL is released during I/O;
    /// reqwest rustls backend in core).
    #[staticmethod]
    fn from_url(py: Python<'_>, url: &str) -> PyResult<Self> {
        let owned = url.to_owned();
        py.detach(|| {
            let rt = tokio::runtime::Builder::new_current_thread()
                .enable_all()
                .build()
                .map_err(|e| PyValueError::new_err(e.to_string()))?;
            rt.block_on(CoreTouchstone::from_url(&owned))
                .map(|t| Touchstone(t, false))
                .map_err(ts_err)
        })
    }

    /// The stored S master data: zero-copy complex view
    /// `(nfreq, nports, nports)`, `owndata=False` (base = this object).
    #[getter]
    fn s<'py>(slf: PyRef<'py, Self>, py: Python<'py>) -> PyResult<Bound<'py, PyArray3<Complex64>>> {
        let core = slf.core()?;
        let n = core.nports() as usize;
        let nf = core.f().len();
        let ptr = core.s().as_ptr();
        let len = core.s().len();
        // Move the pyclass into the container first, then rebuild the
        // slice from its raw parts: the bytes live exactly as long as
        // the container (the pyclass owns them).
        let obj: Bound<'py, PyAny> = Py::from(slf).into_bound(py).into_any();
        let c: &[Complex64] =
            unsafe { std::slice::from_raw_parts(ptr.cast::<Complex64>(), len / 2) };
        let view = ndarray::ArrayView3::from_shape((nf, n, n), c)
            .map_err(|e| PyValueError::new_err(e.to_string()))?;
        // SAFETY: the base object (the pyclass) outlives the view by
        // numpy's base reference; the frozen layout never reallocates.
        let arr = unsafe { PyArray3::borrow_from_array(&view, obj) };
        Ok(arr)
    }

    /// Z domain, computed fresh: complex `(nfreq, nports, nports)`.
    #[getter]
    fn z<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyArray3<Complex64>>> {
        let core = self.core()?;
        domain_array(py, &core.z(), core.nports() as usize)
    }

    /// Y domain, computed fresh.
    #[getter]
    fn y<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyArray3<Complex64>>> {
        let core = self.core()?;
        domain_array(py, &core.y(), core.nports() as usize)
    }

    /// G domain (2-port only), computed fresh.
    #[getter]
    fn g<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyArray3<Complex64>>> {
        let core = self.core()?;
        let v = core.g().map_err(ts_err)?;
        domain_array(py, &v, core.nports() as usize)
    }

    /// H domain (2-port only), computed fresh.
    #[getter]
    fn h<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyArray3<Complex64>>> {
        let core = self.core()?;
        let v = core.h().map_err(ts_err)?;
        domain_array(py, &v, core.nports() as usize)
    }

    /// The frequency axis in hertz — a fresh COPY (read-only contract).
    #[getter]
    fn f<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyArray1<f64>>> {
        Ok(PyArray1::from_slice(py, &self.core()?.f()))
    }

    /// Per-port reference impedance (the single authority).
    #[getter]
    fn z0<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyArray1<f64>>> {
        Ok(PyArray1::from_slice(py, self.core()?.z0()))
    }

    /// Port count.
    #[getter]
    fn nports(&self) -> PyResult<u32> {
        Ok(self.core()?.nports())
    }

    /// File stem without extension.
    #[getter]
    fn name(&self) -> PyResult<String> {
        Ok(self.core()?.name().to_owned())
    }

    /// Merged `!` comment text.
    #[getter]
    fn comments(&self) -> PyResult<String> {
        Ok(self.core()?.comments().to_owned())
    }

    /// File format version, `"1.0"` / `"1.1"`.
    #[getter]
    fn version(&self) -> PyResult<String> {
        Ok(self.core()?.version().to_owned())
    }

    /// Original parameter domain (metadata), canonical uppercase.
    #[getter]
    fn parameter(&self) -> PyResult<String> {
        Ok(self.core()?.parameter().as_ref().to_owned())
    }

    /// Unified accessor domain × format: RI → complex `(nfreq,n,n)`;
    /// MA/DB → real pairs `(nfreq,n,n,2)` (mag|db, deg). Both arguments
    /// are mandatory — use the `s` property for the zero-copy default.
    fn data<'py>(
        slf: PyRef<'py, Self>,
        py: Python<'py>,
        parameter: &str,
        format: &str,
    ) -> PyResult<Bound<'py, PyAny>> {
        let p = arg_ts_str::<TouchstoneParameter>(parameter)?;
        let f = arg_ts_str::<TouchstoneFormat>(format)?;
        let core = slf.core()?;
        let n = core.nports() as usize;
        let nf = core.f().len();
        if p == TouchstoneParameter::S && f == TouchstoneFormat::RI {
            // Zero-copy: raw parts of the stored body, taken before the
            // pyclass moves into the base object.
            let (ptr, len) = (core.s().as_ptr(), core.s().len());
            let obj: Bound<'py, PyAny> = Py::from(slf).into_bound(py).into_any();
            let c: &[Complex64] =
                unsafe { std::slice::from_raw_parts(ptr.cast::<Complex64>(), len / 2) };
            let view = ndarray::ArrayView3::from_shape((nf, n, n), c)
                .map_err(|e| PyValueError::new_err(e.to_string()))?;
            // SAFETY: the base object (the pyclass) owns the bytes and
            // outlives the view by numpy's base reference.
            let arr = unsafe { PyArray3::borrow_from_array(&view, obj) };
            return Ok(arr.into_any());
        }
        let v = core.data(p, f).map_err(ts_err)?.to_vec();
        match f {
            TouchstoneFormat::RI => domain_array(py, &v, n).map(|a| a.into_any()),
            TouchstoneFormat::MA | TouchstoneFormat::DB => {
                ndarray::Array4::from_shape_vec((nf, n, n, 2), v)
                    .map(|a| a.into_pyarray(py).into_any())
                    .map_err(|e| PyValueError::new_err(e.to_string()))
            }
        }
    }

    /// Render Touchstone text in `parameter`/`format` (shortest-roundtrip
    /// numbers; `#` line uses the stored version).
    fn write_touchstone(&self, parameter: &str, format: &str) -> PyResult<String> {
        let p = arg_ts_str::<TouchstoneParameter>(parameter)?;
        let f = arg_ts_str::<TouchstoneFormat>(format)?;
        self.core()?.write_touchstone(p, f).map_err(ts_err)
    }

    /// Write to disk (native; GIL released). The filename is corrected by
    /// core `write_path` (extension always `.{P}Np`). `parameter` and
    /// `format` are mandatory (no silent defaults).
    fn write_file(
        &self,
        py: Python<'_>,
        path: &str,
        parameter: &str,
        format: &str,
    ) -> PyResult<()> {
        let p = arg_ts_str::<TouchstoneParameter>(parameter)?;
        let f = arg_ts_str::<TouchstoneFormat>(format)?;
        let owned = path.to_owned();
        let inner = self.core()?;
        py.detach(move || inner.write_file(&owned, p, f).map_err(ts_err))
    }

    /// Path/URL → filename with extension.
    #[staticmethod]
    fn filename_from_path(path: &str) -> String {
        CoreTouchstone::filename_from_path(path)
    }

    /// Filename → stem (Touchstone grammar; no match → whole string).
    #[staticmethod]
    fn name_from_filename(filename: &str) -> String {
        CoreTouchstone::name_from_filename(filename)
    }

    /// Filename → port count (grammar `\.[ghsyz]\d+p`); no match raises
    /// `ValueError` guiding to pass nports explicitly.
    #[staticmethod]
    fn nports_from_filename(filename: &str) -> PyResult<usize> {
        CoreTouchstone::nports_from_filename(filename).map_err(ts_err)
    }

    /// Deterministic manual reclamation (the unified cross-end verb,
    /// ironclad rule 12). Idempotent; post-drop access raises `ValueError`.
    /// RAII (reference counting) is the fallback.
    fn drop(&mut self) {
        self.1 = true;
    }
}

/// Build an owned complex `(nfreq, n, n)` array from interleaved re/im.
fn domain_array<'py>(
    py: Python<'py>,
    v: &[f64],
    n: usize,
) -> PyResult<Bound<'py, PyArray3<Complex64>>> {
    let c: Vec<Complex64> = v
        .as_chunks::<2>()
        .0
        .iter()
        .map(|p| Complex64::new(p[0], p[1]))
        .collect();
    let nf = c.len() / (n * n);
    ndarray::Array3::from_shape_vec((nf, n, n), c)
        .map(|a| a.into_pyarray(py))
        .map_err(|e| PyValueError::new_err(e.to_string()))
}

#[pymodule]
#[pyo3(name = "_netwave")]
fn netwave_module(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Physical constant re-exported from core (ironclad rules 11/12: the
    // value is defined once in core::constants, never hand-copied here).
    m.add("SPEED_OF_LIGHT", netwave::constants::SPEED_OF_LIGHT)?;
    #[cfg(not(coverage))]
    m.add_class::<Frequency>()?;
    #[cfg(not(coverage))]
    m.add_class::<Touchstone>()?;
    #[cfg(not(coverage))]
    m.add_function(wrap_pyfunction!(netwave::frequency::live_count, m)?)?;
    // Gated with not(coverage): core drops the pyclass/pyfunction attributes
    // under cfg(coverage), so these registrations cannot compile there. The
    // coverage build excludes this glue crate anyway; pytest exercises the
    // Python surface in a normal (non-coverage) build.
    #[cfg(not(coverage))]
    m.add_class::<netwave::frequency::FrequencyUnit>()?;
    #[cfg(not(coverage))]
    m.add_class::<netwave::frequency::WavelengthUnit>()?;
    #[cfg(not(coverage))]
    m.add_function(wrap_pyfunction!(netwave::frequency::frequency_units, m)?)?;
    Ok(())
}

// Gatherer used by `src/bin/stub_gen.rs` to collect every registered stub
// item and emit `netwave/_netwave.pyi`.
#[cfg(feature = "stub-gen")]
define_stub_info_gatherer!(stub_info);
