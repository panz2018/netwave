# netwave python binding

PyO3 binding over the Rust core (`../core`): a thin transport that hands
numpy a **borrowed view** of core-allocated memory. The binding never
recomputes values (constitution rule: bindings only move memory).

Current stage: phase-0 scaffold. Two verbs: `fill_pattern` (allocate +
view) and `read_element` (read back through the same memory), replaced by
the real data model in phase 2.

## Layout

- `src/lib.rs` — the binding: `Owner` pyclass + zero-copy view
- `src/netwave.pyi` — type stub, shipped inside the wheel
- `tests/test_roundtrip.py` — zero-copy roundtrip tests (pytest)
- `pyproject.toml` / `uv.lock` / `.python-version` — uv-managed env

## Commands

Run from this directory. Environment setup (venv, `PYO3_PYTHON`,
`LD_LIBRARY_PATH`) is injected by `.vscode/settings.json`; outside VS
Code see the root README.

```bash
uv sync                           # create/refresh .venv from uv.lock
uv run maturin develop            # build the extension into .venv
cargo fmt --check                 # format check of this crate's Rust (what CI runs)
cargo fmt                         # auto-fix formatting
cargo clippy -- -D warnings       # lint the Rust binding, warnings are errors
cargo clippy --fix --allow-dirty  # auto-fix lint (review the diff!)
uv run ruff check .               # lint the Python side (tests, config)
uv run ruff format .              # auto-format the Python side
uv run pytest                     # run tests (CI adds --cov-fail-under=100)
uv run pytest --cov=netwave --cov-fail-under=100
```

Cross-binding dump (python side of the four-way comparison; run from the
repo root):

```bash
uv run --project python python scripts/dump_py.py .cross-tmp
```

## Implementation notes

- **Zero-copy via base object**: core allocates, a `#[pyclass(frozen)] Owner` holds the buffer and is attached as the returned ndarray's
  `base`. The array has `owndata=False`; Python writes land directly in
  core memory, and the Owner drops (freeing it) only after the array is
  collected. `test_fill_pattern_view_zero_copy` asserts `owndata is False` so a silent regression to copying fails loudly.
- **`read_element` returns `(float, float)`**: a plain tuple, not a
  complex — keeps the roundtrip proof free of any conversion layer.
- **`python_relative: 0.0` tolerance** (in
  [`../testdata/manifest.json`](../testdata/manifest.json)): the
  roundtrip path performs no arithmetic — numpy views the same f64 bits
  Rust wrote — so any deviation is a bug, hence bit-exact.
- **`netwave.pyi` ships in the wheel**: maturin only packages `.so`/`.py`
  by default, so `[tool.maturin] include` adds the stub explicitly;
  without it, installed users lose type hints (the `.so` is opaque to
  mypy/pyright).
- **`[lib] name = "netwave"`** (same as the core crate) is deliberate:
  it is the Python `import` name.
- **`crate-type = ["cdylib"]`** avoids E0464: without it cargo also
  builds an rlib named `netwave`, which collides with the core crate's
  hash-named rlib in the same target dir. cdylib-only removes the clash.

## Gotchas

- **Rebuild after touching core**: always `uv run maturin develop` before
  `pytest` or any cross-binding comparison, otherwise you test stale
  artifacts.
- **Dumps are binary `.bin`** (little-endian f64): JSON loses the sign
  of `-0`, making bit-exact comparison impossible. Contract:
  [`../testdata/README.md`](../testdata/README.md).
