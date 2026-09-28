# netwave python binding

PyO3 binding over the Rust core (`../core`): a thin transport that hands numpy a
**borrowed view** of core-allocated memory. The binding never recomputes values
(governance spec rule: bindings only move memory; see
[`openspec/specs/project-governance/spec.md`](../openspec/specs/project-governance/spec.md)).

Current stage: phase-0 scaffold. Two verbs: `fill_pattern` (allocate + view) and
`read_element` (read back through the same memory), replaced by the real data
model in phase 2.

## Layout

- `src/lib.rs` — the binding: `Owner` pyclass + zero-copy view
- `src/netwave.pyi` — type stub, shipped inside the wheel
- `tests/test_roundtrip.py` — zero-copy roundtrip tests (pytest)
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
uv run pytest                     # run tests (CI adds --cov-fail-under=100)
uv run pytest --cov=netwave --cov-fail-under=100
```

Ruff config is the repo-root `ruff.toml` (single source of truth covering
`python/` AND `scripts/`; ruff walks up from each file to find it). For the
whole-repo Python gate run root `pnpm check:py` / `pnpm fix:py`.

Cross-binding dump (python side of the four-way comparison; run from the repo
root):

```bash
uv run --project python python python/scripts/dump.py .cross-tmp
```
