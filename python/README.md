# netwave python binding

PyO3 binding over the Rust core (`../core`): a thin transport that hands numpy a
**borrowed view** of core-allocated memory. The binding never recomputes values
(governance spec rule: bindings only move memory; see
[`openspec/specs/project-governance/spec.md`](../openspec/specs/project-governance/spec.md)).

Current stage: the `Touchstone` pyclass is the data authority — `from_data`
/`from_text`/`from_bytes`/`from_file`/`from_url` factories in, the writable
zero-copy `s` view (`owndata=False`) out; `Frequency` is the frequency axis.
`from_bytes` accepts `bytes`/`bytearray`/`memoryview` and `to_bytes` returns
`bytes`; encoding whitelists `UTF-8`/`ISO-8859-1` (read default guesses,
write default UTF-8 — see the touchstone-core spec).

## Layout

- `src/lib.rs` — the binding: pyclass base-object views of core memory
- `netwave/_netwave.pyi` — type stub, shipped inside the wheel
- `tests/` — pytest suite (roundtrip, memory lifecycle, units, classes)
- `pyproject.toml` / `uv.lock` / `.python-version` — uv-managed env

## Commands

Run from this directory. Environment setup (venv, `PYO3_PYTHON`,
`LD_LIBRARY_PATH`) is injected by `.vscode/settings.json`; outside VS Code see
[CONTRIBUTING.md](../CONTRIBUTING.md).

```bash
uv sync                           # create/refresh .venv from uv.lock
uv run maturin develop            # build the extension into .venv
cargo fmt --check                 # format check of this crate's Rust (what CI runs)
cargo fmt                         # auto-fix formatting
cargo clippy -- -D warnings       # lint the Rust binding, warnings are errors
cargo clippy --fix --allow-dirty  # auto-fix lint (review the diff!)
uv run ruff check .               # lint the Python side (tests, config)
uv run ruff format --check .      # format check only (what CI runs)
uv run ruff check --fix .         # auto-fix lint (review the diff!)
uv run ruff format .              # auto-format the Python side
uv run pytest                     # run tests with coverage (scope and 100% floor
                                  # come from [tool.coverage] in pyproject.toml)
```

Coverage scope and the floor are declared once in `pyproject.toml`
(`[tool.coverage.run].source = ["netwave"]`, `[tool.coverage.report].fail_under`);
CI runs the same bare `uv run pytest`, so local and CI grade the same set. The
`[tool.pytest.ini_options]` table is what keeps pytest from inheriting the repo
root's config — without it the root's bare `--cov` would widen this project's
floor to the whole repo.

Ruff config is the repo-root `ruff.toml` (single source of truth covering
`python/` AND `scripts/`; ruff walks up from each file to find it). For the
whole-repo Python gate run root `pnpm check:py` / `pnpm fix:py`.

Cross-binding dump (python side of the four-way comparison; run from the repo
root):

```bash
uv run --project python python python/scripts/dump.py oracle/tmp
```
