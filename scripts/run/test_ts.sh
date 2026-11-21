#!/usr/bin/env bash
# TypeScript test entry: wasm build + napi glue coverage chain + tsc type gate +
# dts any check + node-driven wasm suite + stray-profraw drain. Single source of
# truth for typescript test command details — local `pnpm test:ts` and the CI
# node job both call this file, so parameters cannot drift apart.
set -euo pipefail

cd "$(dirname "$0")/../.."

# Toolchain probes: missing tools print the install command and
# exit non-zero — never auto-install (machine side effect; CI has its own install
# steps). node_modules is not probed: a missing dependency surfaces from
# pnpm/vitest itself.
if ! command -v cargo-llvm-cov >/dev/null 2>&1; then
  echo "cargo-llvm-cov not found — install it with: bash scripts/install_cargo_llvm_cov.sh" >&2
  exit 1
fi
if ! command -v wasm-pack >/dev/null 2>&1; then
  echo "wasm-pack not found — install it with: bash scripts/install_wasm_pack.sh" >&2
  exit 1
fi
if ! command -v wasm-opt >/dev/null 2>&1; then
  echo "wasm-opt (binaryen) not found — install it with: bash scripts/install_binaryen.sh" >&2
  exit 1
fi
if ! rustup target list --installed 2>/dev/null | grep -q '^wasm32-unknown-unknown$'; then
  echo "wasm32-unknown-unknown target not installed — add it with: rustup target add wasm32-unknown-unknown" >&2
  exit 1
fi

python3 scripts/run/clean_stray_profraw.py

# build:wasm first: build:native ends with tsdown, whose dts pass resolves BOTH
# generated glues (napi + wasm-web). Building wasm first keeps the browser
# shell's dts fully typed (a missing wasm glue makes tsdown emit `any` for the
# re-exported verbs). wasm-pack uses CARGO_TARGET_DIR=../target-wasm, so this
# build is not instrumented and is unaffected by the show-env below.
pnpm -C typescript build:wasm

# show-env, clean, instrumented build, vitest and report MUST share one process —
# the instrumentation env does not cross processes. debug build (not release):
# instrumented release is slow and optimization shifts line mappings off the
# source; the .node exports the same symbols and zero-copy protocol.
# `--no-cfg-coverage` keeps the napi glue compiled in (show-env would otherwise
# set cfg(coverage) and strip it). vitest runs on the threads pool with execArgv
# cleared and gc via NODE_OPTIONS: worker threads reject --expose-gc
# (ERR_WORKER_INVALID_EXEC_ARGV) and do not run libc atexit, so the threads
# pool's normal main-process exit is what flushes profraw; --no-file-parallelism
# serializes files because every worker shares one .node's Rust static live_count
# (memory-lifecycle counts would race). v8 TS coverage still hits its 100%
# threshold under the threads pool. The --coverage flag itself is baked into
# typescript/package.json's test:native, not repeated here.
# report needs --target: napi --platform builds objects under target/<triple>/,
# which report does not search by default. Floor 100: the #[napi] attribute lines
# (rustc#79651) are exempted by pattern in the gate. The ignore regex excludes
# python as well as core: report scans every object's covmap section under target/,
# so a shared local target/ that a prior `maturin develop` instrumented would pull
# python/src/lib.rs into the native report at 0% (CI's fresh-checkout node job has
# no python object, so the exclusion is a no-op there). The native report is the
# native glue's coverage; python rows belong to coverage-python.json (test_py.sh).
mkdir -p coverage
eval "$(cargo llvm-cov show-env --sh --no-cfg-coverage)"
export NODE_OPTIONS=--expose-gc
cargo llvm-cov clean --workspace
pnpm -C typescript build:native:debug
pnpm -C typescript test:native --pool=threads --execArgv="" --no-file-parallelism
cargo llvm-cov report --target "$(rustc -vV | sed -n 's/^host: //p')" \
  --codecov --output-path coverage/coverage-native.json \
  --ignore-filename-regex '[\\/](core|python)[\\/]'
python3 scripts/coverage_gate.py coverage/coverage-native.json 100

# Type gates after both glues exist: the shells import the generated bindings from
# dist/, so tsc needs napi + wasm glue present. Runs unconditionally (no node
# version special-case) so local and CI share one measurement standard.
pnpm -C typescript typecheck
node typescript/scripts/check_dts_any.mjs

# Node-driven wasm suite (unit-test nature): the same test/wasm code the browser
# job runs, here proving the wasm artifact loads and passes on this node version.
pnpm -C typescript test:wasm

# Post-run: drain first so its "broken chain this round" detection is never
# pushed to the end by a later-appended command; the stray scan (SKIP_DIRS
# covers target/) and the instrumented clean (target/ only) act on disjoint sets.
# Stale instrumented binaries are the pollution vector itself; the next run
# cleans again, so removing them here costs nothing.
python3 scripts/run/clean_stray_profraw.py
cargo llvm-cov clean --workspace
