//! netwave Python binding (scaffold phase 0, final borrowed-view form).
//!
//! Zero-copy end state: core allocates the memory; a `#[pyclass] Owner` holds
//! it and is attached as the returned array's base object — the ndarray has
//! `owndata=False`, so Python writes land directly in core memory; the Owner
//! drops (freeing the memory) when the array is garbage collected (numpy's
//! base reference guarantees the view never outlives the data).

use netwave::fill_pattern as core_fill_pattern;
use numpy::Complex64;
use numpy::ndarray;
use numpy::{PyArray3, PyReadonlyArray3};
use pyo3::prelude::*;

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
#[pyfunction]
fn read_element(arr: PyReadonlyArray3<Complex64>, idx: usize) -> (f64, f64) {
    let slice = arr.as_slice().unwrap();
    (slice[idx].re, slice[idx].im)
}

#[pymodule]
#[pyo3(name = "netwave")]
fn netwave_module(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(fill_pattern, m)?)?;
    m.add_function(wrap_pyfunction!(read_element, m)?)?;
    Ok(())
}
