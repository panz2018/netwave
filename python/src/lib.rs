//! netwave Python binding (borrowed-view form).
//!
//! Zero-copy end state: core allocates the memory; a `#[pyclass] Owner` holds
//! it and is attached as the returned array's base object — the ndarray has
//! `owndata=False`, so Python writes land directly in core memory; the Owner
//! drops (freeing the memory) when the array is garbage collected (numpy's
//! base reference guarantees the view never outlives the data).

use std::str::FromStr;

use netwave::fill_pattern as core_fill_pattern;
use netwave::frequency::Frequency as CoreFrequency;
use netwave::frequency::FrequencyUnit;
use netwave::frequency::WavelengthUnit;
use netwave::network::Network as CoreNetwork;
use numpy::Complex64;
use numpy::ndarray;
use numpy::{PyArray1, PyArray3, PyReadonlyArray1, PyReadonlyArray3};
use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;

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
// The internal `Owner` pyclass is deliberately NOT annotated — it is not
// public API and must not appear in the stub.
#[cfg(feature = "stub-gen")]
use pyo3_stub_gen::define_stub_info_gatherer;
#[cfg(feature = "stub-gen")]
use pyo3_stub_gen::derive::{gen_stub_pyclass, gen_stub_pyfunction, gen_stub_pymethods};

/// Memory owner: attached as the returned array's base object; frees the
/// memory when the array is garbage collected.
#[pyclass(frozen)]
struct Owner {
    data: ndarray::Array3<Complex64>,
}

/// Allocate an `(nfreq, nports, nports)` interleaved complex f64 ndarray
/// (complex128).
///
/// The returned ndarray has `owndata=False`: the memory owner is the Rust
/// `Owner` (base object), and the Python side is a borrowed view. Writing
/// a view element == writing core memory.
#[cfg_attr(feature = "stub-gen", gen_stub_pyfunction)]
#[pyfunction]
fn fill_pattern<'py>(
    py: Python<'py>,
    nfreq: usize,
    nports: usize,
) -> PyResult<Bound<'py, PyArray3<Complex64>>> {
    let v = core_fill_pattern(nfreq, nports);
    let arr3 = ndarray::Array3::from_shape_vec((nfreq, nports, nports), v)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
    let owner = Bound::new(py, Owner { data: arr3 })?;
    let container = owner.clone().into_any();
    // SAFETY: the memory belongs to owner.data; owner (the same PyObject) is
    // attached as the base object (SetBaseObject takes the reference), and
    // numpy guarantees the base outlives the view; the frozen pyclass
    // guarantees the data is not reallocated while views exist.
    let view = unsafe { PyArray3::borrow_from_array(&owner.get().data, container) };
    Ok(view)
}

/// Pass a readonly ndarray back into Rust and read the complex element at a
/// flat index.
///
/// The view of the same memory is read directly by pointer — proving
/// "Python write → immediately visible in core".
#[cfg_attr(feature = "stub-gen", gen_stub_pyfunction)]
#[pyfunction]
fn read_element(arr: PyReadonlyArray3<Complex64>, idx: usize) -> (f64, f64) {
    let slice = arr.as_slice().unwrap();
    (slice[idx].re, slice[idx].im)
}

/// An S-matrix data container: the constructor is the data entry (no
/// `upload` — that verb is browser-only, it names the worker linear-memory
/// boundary which does not exist here). `read_element` reads one
/// interleaved f64 element; `drop` is the deterministic manual reclamation
/// (idempotent; post-drop access raises `ValueError`). RAII is the
/// fallback.
#[cfg_attr(feature = "stub-gen", gen_stub_pyclass(module = "netwave._netwave"))]
#[pyclass]
pub struct Network(CoreNetwork);

#[cfg_attr(feature = "stub-gen", gen_stub_pymethods)]
#[pymethods]
impl Network {
    /// Wrap an owned interleaved `[re, im, ...]` f64 buffer with explicit
    /// shape (`len == nfreq*nports*nports*2`). Shape is validated here and
    /// surfaced as a `ValueError` (core's `from_f64` asserts, which would
    /// panic across the FFI boundary).
    #[new]
    fn new(data: PyReadonlyArray1<f64>, nfreq: usize, nports: usize) -> PyResult<Self> {
        let want = nfreq * nports * nports * 2;
        let slice = data.as_slice()?;
        if slice.len() != want {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "data length must be nfreq*nports*nports*2 ({want}), got {}",
                slice.len()
            )));
        }
        Ok(Self(CoreNetwork::from_f64(nfreq, nports, slice.to_vec())))
    }

    /// Pattern-filled factory (the unified cross-end static, core
    /// `fill_pattern` verbatim).
    #[staticmethod]
    fn fill_pattern(nfreq: usize, nports: usize) -> Self {
        Self(CoreNetwork::fill_pattern(nfreq, nports))
    }

    /// Read one interleaved f64 element by flat index. Raises
    /// `ValueError` after `drop()`.
    fn read_element(&self, idx: usize) -> PyResult<f64> {
        self.0
            .read_element(idx)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
    }

    /// Deterministic manual reclamation (the unified cross-end verb,
    /// ironclad rule 12). Idempotent; post-drop access raises `ValueError`.
    fn drop(&mut self) {
        self.0.drop();
    }
}

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

#[pymodule]
#[pyo3(name = "_netwave")]
fn netwave_module(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fill_pattern, m)?)?;
    m.add_function(wrap_pyfunction!(read_element, m)?)?;
    // Physical constant re-exported from core (ironclad rules 11/12: the
    // value is defined once in core::constants, never hand-copied here).
    m.add("SPEED_OF_LIGHT", netwave::constants::SPEED_OF_LIGHT)?;
    #[cfg(not(coverage))]
    m.add_class::<Network>()?;
    #[cfg(not(coverage))]
    m.add_class::<Frequency>()?;
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
