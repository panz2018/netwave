#!/usr/bin/env bash
# Python test entry: rust-glue coverage chain + python-layer pytest + stray-profraw
# drain. Single source of truth for python test command details — local
# `pnpm test:py` and the CI python job both call this file, so parameters cannot
# drift apart.
set -euo pipefail

cd "$(dirname "$0")/../.."

if ! command -v cargo-llvm-cov >/dev/null 2>&1; then
  echo "cargo-llvm-cov not found — install it with: bash scripts/install_cargo_llvm_cov.sh" >&2
  exit 1
fi
if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found — install it with: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 1
fi

python3 scripts/run/clean_stray_profraw.py

# show-env, clean, build, test and report MUST share one process — the
# instrumentation env does not cross processes. maturin passes RUSTC_WRAPPER
# through to cargo, so the extension builds instrumented; pytest drives it and
# the profraw lands in root target/. `clean --workspace` is the cleanup command
# for this chain: maturin builds without --target, so the instrumented objects
# land in host target/debug (not target/llvm-cov-target).
eval "$(cargo llvm-cov show-env --sh --no-cfg-coverage)"
cargo llvm-cov clean --workspace

# coverage/ is gitignored and absent on a clean checkout, and llvm-cov does not
# create parent dirs of --output-path — create it first. maturin and pytest run
# inside python/ (the root pyproject.toml has no build-system section — maturin
# from the repo root misreads it); the `(cd python && ...)` subshells isolate
# the directory change.
mkdir -p coverage
(cd python && uv sync && uv run maturin develop)
(cd python && uv run pytest)
cargo llvm-cov report --codecov \
  --output-path coverage/coverage-python.json \
  --ignore-filename-regex '[\\/]core[\\/]'
python3 scripts/coverage_gate.py coverage/coverage-python.json 100

# Post-run: drain first so its "broken chain this round" detection is never
# pushed to the end by a later-appended command; the stray scan (SKIP_DIRS
# covers target/) and the instrumented clean (target/ only) act on disjoint sets.
python3 scripts/run/clean_stray_profraw.py
cargo llvm-cov clean --workspace
