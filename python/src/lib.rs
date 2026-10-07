//! netwave Python binding (borrowed-view form).
//!
//! Zero-copy end state: core allocates the memory; a `#[pyclass] Owner` holds
//! it and is attached as the returned array's base object — the ndarray has
//! `owndata=False`, so Python writes land directly in core memory; the Owner
//! drops (freeing the memory) when the array is garbage collected (numpy's
//! base reference guarantees the view never outlives the data).

use netwave::fill_pattern as core_fill_pattern;
use netwave::frequency::Frequency as CoreFrequency;
use netwave::frequency::FrequencyUnit;
use netwave::network::Network as CoreNetwork;
use numpy::Complex64;
use numpy::ndarray;
use numpy::{PyArray3, PyReadonlyArray1, PyReadonlyArray3};
use pyo3::prelude::*;

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

/// A frequency sweep. `from_f` is the data entry (static factory, core
/// name verbatim); `drop` is the deterministic manual reclamation shared
/// with RAII. Post-drop access raises `ValueError`.
#[cfg_attr(feature = "stub-gen", gen_stub_pyclass(module = "netwave._netwave"))]
#[pyclass]
pub struct Frequency(CoreFrequency);

#[cfg_attr(feature = "stub-gen", gen_stub_pymethods)]
#[pymethods]
impl Frequency {
    /// Build a sweep from hertz points + unit (the enum member, passed by
    /// member — never coerced, validation stays in core). `unit` is
    /// downcast rather than `FromPyObject` because the enum pyclass opts
    /// out of arbitrary-object coercion (`skip_from_py_object`).
    #[staticmethod]
    fn from_f<'py>(f_hz: PyReadonlyArray1<f64>, unit: &Bound<'py, PyAny>) -> PyResult<Self> {
        let unit = *unit.cast::<FrequencyUnit>()?.borrow();
        Ok(Self(CoreFrequency::from_f(f_hz.as_slice()?.to_vec(), unit)))
    }

    /// Number of frequency points. Raises `ValueError` after `drop()`.
    fn npoints(&self) -> PyResult<usize> {
        self.0
            .npoints()
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
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
    m.add_function(wrap_pyfunction!(netwave::frequency::frequency_units, m)?)?;
    Ok(())
}

// Gatherer used by `src/bin/stub_gen.rs` to collect every registered stub
// item and emit `netwave/_netwave.pyi`.
#[cfg(feature = "stub-gen")]
define_stub_info_gatherer!(stub_info);
