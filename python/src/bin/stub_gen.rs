//! `.pyi` generator entry point (task 3.3).
//!
//! Run from `python/` so pyo3-stub-gen finds `pyproject.toml`:
//!
//! ```text
//! cargo run --features stub-gen --bin stub_gen
//! ```
//!
//! The stub is generated, never hand-written: the vocabulary single-source
//! rule (spec: frequency-unit) forbids a second copy of any name list, and
//! the exports test (task 6.1) asserts the generated members match core.

use std::fs;
use std::path::Path;

use pyo3_stub_gen::Result;

fn main() -> Result<()> {
    let stub = _netwave::stub_info()?;
    stub.generate()?;
    relocate_stub()?;
    Ok(())
}

/// Move the generated stub to the single-file location beside the extension.
///
/// In mixed layout pyo3-stub-gen hardcodes the submodule stub to
/// `netwave/_netwave/__init__.pyi` (a package dir). That leaves a
/// `netwave/_netwave/` directory next to the `netwave/_netwave.abi3.so`
/// extension, which makes Python's import path ambiguous (namespace package
/// vs extension module). Relocating to `netwave/_netwave.pyi` — the
/// canonical single-file stub — removes the directory and keeps the stub
/// exactly where type checkers expect a module named `netwave._netwave`.
fn relocate_stub() -> Result<()> {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("netwave");
    let from = root.join("_netwave").join("__init__.pyi");
    let to = root.join("_netwave.pyi");
    fs::rename(&from, &to)?;
    // The stub dir is now empty; drop it so only the .so remains for `netwave._netwave`.
    fs::remove_dir(root.join("_netwave"))?;
    Ok(())
}
