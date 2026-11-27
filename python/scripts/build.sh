#!/usr/bin/env bash
# Python glue build entry: resolve the project env, compile the abi3 extension,
# and generate the .pyi stub. Single source of truth for python build command
# details — `scripts/run/test_cross.sh` and any local one-off build both call
# this file, so the build cannot drift between entries.
set -euo pipefail

cd "$(dirname "$0")/../.."

# Toolchain probe: uv missing prints the install hint and exits non-zero —
# never auto-install (machine side effect; CI has its own install steps).
# maturin needs no separate probe: it comes from the python project env that
# `uv sync` resolves.
if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found — install it with: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 1
fi

# maturin and stub_gen run inside python/ (the root pyproject.toml has no
# build-system section — maturin from the repo root misreads it); the
# `(cd python && ...)` subshells isolate the directory change.
uv sync --project python
(cd python && uv run maturin develop)

# stub_gen dynamically links libpython (pyo3 auto mode): the loader must find
# uv's libpython, so export its LIBDIR before generating the .pyi that
# check_vocab_types.py compares across ends.
export LD_LIBRARY_PATH="$(uv run --project python python -c "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))")${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
(cd python && uv run --no-sync cargo run --features stub-gen --bin stub_gen)
