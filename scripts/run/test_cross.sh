#!/usr/bin/env bash
# Cross-binding test entry: python glue build + stub_gen + four-end dump +
# grading + cross-end vocabulary gates. Single source of truth for cross-binding
# test command details — local `pnpm test:cross` and the CI node job both call
# this file, so parameters cannot drift apart.
set -euo pipefail

cd "$(dirname "$0")/../.."

# Toolchain probe: uv missing prints the install hint and exits non-zero —
# never auto-install (machine side effect; CI has its own install steps).
# maturin needs no separate probe: it comes from the python project env that
# `uv sync` below resolves.
if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found — install it with: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 1
fi

# Artifact probes: the node/wasm ends dump from their built glues, and this
# entry never rebuilds them (build logic lives once in scripts/run/test_ts.sh).
# Missing artifacts print the command that produces them.
if ! ls typescript/dist/index.node.mjs typescript/dist/index.*.node >/dev/null 2>&1; then
  echo "napi glue missing under typescript/dist/ — build it with: pnpm test:ts" >&2
  exit 1
fi
if [ ! -f typescript/dist/wasm-web/netwave_wasm_bg.wasm ]; then
  echo "wasm glue missing under typescript/dist/wasm-web/ — build it with: pnpm test:ts" >&2
  exit 1
fi

uv sync --project python
(cd python && uv run maturin develop)

# stub_gen dynamically links libpython (pyo3 auto mode): the loader must find
# uv's libpython, so export its LIBDIR before generating the .pyi that
# check_vocab_types.py compares across ends.
export LD_LIBRARY_PATH="$(uv run --project python python -c "import sysconfig; print(sysconfig.get_config_var('LIBDIR'))")${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
(cd python && uv run --no-sync cargo run --features stub-gen --bin stub_gen)

# Four-end dump + grading (native ends bit-exact, wasm within manifest
# tolerance), the built-in anti-tautology tamper self-check, then the cross-end
# vocabulary type gate and the verb-set gate — all assert against the artifacts
# the steps above and test_ts.sh produced.
# The core example and the napi .node may be the instrumented builds the
# coverage entries left in target/; running them would emit a stray profraw at
# the repo root (a coverage-chain-broken signal to the next entry's drain).
# This entry is a correctness gate, not a coverage one, so redirect the
# instrumented runtime's output to discard — no profraw is written.
export LLVM_PROFILE_FILE=/dev/null
cargo run -q -p netwave --example dump oracle/tmp
uv run --project python python python/scripts/dump.py oracle/tmp
node typescript/scripts/dump.mjs oracle/tmp
python3 oracle/compare_cross.py oracle/tmp
python3 scripts/check_vocab_types.py
python3 scripts/check_verbs.py
