#!/usr/bin/env bash
# Rust test entry: core coverage chain + build watchdog + stray-profraw drain.
# Single source of truth for rust test command details — local `pnpm test:rs`
# and the CI rust job both call this file, so parameters cannot drift apart.
set -euo pipefail

cd "$(dirname "$0")/../.."

if ! command -v cargo-llvm-cov >/dev/null 2>&1; then
  echo "cargo-llvm-cov not found — install it with: bash scripts/install_cargo_llvm_cov.sh" >&2
  exit 1
fi

python3 scripts/run/clean_stray_profraw.py

# coverage/ is gitignored and absent on a clean checkout, and llvm-cov
# does not create parent dirs of --output-path — create it first.
mkdir -p coverage
cargo llvm-cov -p netwave --codecov --output-path coverage/coverage-core.json
python3 scripts/coverage_gate.py coverage/coverage-core.json 100
cargo build --workspace --all-targets

python3 scripts/run/clean_stray_profraw.py
