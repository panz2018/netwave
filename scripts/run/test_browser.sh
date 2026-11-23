#!/usr/bin/env bash
# Browser test entry: build the wasm artifact, run the node-driven unit suite and
# the real-browser suite. Single source of truth for browser test command details —
# local `pnpm test:browser` and the CI browser job both call this file, so parameters
# cannot drift apart.
set -euo pipefail

cd "$(dirname "$0")/../.."

# Toolchain probes: missing tools print the install command and exit non-zero —
# never auto-install (machine side effect; CI has its own install steps).
if ! command -v wasm-pack >/dev/null 2>&1; then
  echo "wasm-pack not found — install it with: bash scripts/install_wasm_pack.sh" >&2
  exit 1
fi
if ! command -v wasm-opt >/dev/null 2>&1; then
  echo "wasm-opt (binaryen) not found — install it with: bash scripts/install_binaryen.sh" >&2
  exit 1
fi
# rustup target list follows the rust-toolchain.toml override, so this probe
# checks the ACTIVE (pinned) toolchain — not @stable. It assumes CI added the
# target to that toolchain (the wasm job's "target for the pinned toolchain"
# step runs a bare `rustup target add`, which acts on the active toolchain).
if ! rustup target list --installed 2>/dev/null | grep -q '^wasm32-unknown-unknown$'; then
  echo "wasm32-unknown-unknown target not installed — add it with: rustup target add wasm32-unknown-unknown" >&2
  exit 1
fi
# Chromium probe: the real-browser suite needs a playwright chromium. Detect the
# playwright browser cache; never auto-install (CI installs it in its own step).
pw_cache="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/.cache/ms-playwright}"
case "$(uname)" in
  Darwin) pw_cache="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/Library/Caches/ms-playwright}" ;;
  MINGW* | MSYS* | CYGWIN*) pw_cache="${PLAYWRIGHT_BROWSERS_PATH:-${LOCALAPPDATA:-$HOME/AppData/Local}/ms-playwright}" ;;
esac
if ! find "$pw_cache" -maxdepth 1 -type d -name 'chromium*' 2>/dev/null | grep -q .; then
  echo "chromium not installed — install it with: pnpm -C browser exec playwright install --only-shell chromium" >&2
  exit 1
fi
# Linux only: a present chromium binary can still fail to launch when its system
# libraries are absent from the loader path. Catch it pre-flight with a clear
# hint instead of a cryptic linker error mid-suite.
if [[ "$(uname)" == "Linux" ]]; then
  shell_bin=$(find "$pw_cache" -name chrome-headless-shell -type f 2>/dev/null | head -1)
  if [[ -n "$shell_bin" ]] && ldd "$shell_bin" 2>/dev/null | grep -q "not found"; then
    echo "chromium system libraries missing — export LD_LIBRARY_PATH to the dir holding libglib-2.0.so.0 (find / -name 'libglib-2.0.so*')" >&2
    exit 1
  fi
fi

# Wasm rust coverage toolchain (the browser job measures core's browser-gated
# rust code): llc/llvm-profdata/llvm-cov come from the llvm-tools rustup
# component (pinned in rust-toolchain.toml), resolved under the active sysroot
# so local and CI share one path. wasi-sdk clang compiles the wasm32 C runtime
# minicov needs; wasm-bindgen-cli regenerates web glue from the instrumented
# cdylib (wasm-pack cannot build instrumented output). All three are probed,
# never auto-installed — CI has its own install steps.
LLVM_BIN="$(rustc --print sysroot)/lib/rustlib/$(rustc -vV | sed -n 's/^host: //p')/bin"
for tool in llc llvm-profdata llvm-cov; do
  if [ ! -x "$LLVM_BIN/$tool" ]; then
    echo "$tool not found under $LLVM_BIN — add it with: rustup component add llvm-tools" >&2
    exit 1
  fi
done
WASI_SDK_CLANG="$HOME/.local/opt/wasi-sdk/bin/clang"
if [ ! -x "$WASI_SDK_CLANG" ]; then
  echo "wasi-sdk clang not found at $WASI_SDK_CLANG — install it with: bash scripts/install_wasi_sdk.sh" >&2
  exit 1
fi
if ! command -v wasm-bindgen >/dev/null 2>&1; then
  echo "wasm-bindgen not found — install it with: bash scripts/install_wasm_bindgen_cli.sh" >&2
  exit 1
fi

# Pre-run: drain stray profraw left by a previous broken chain, so the post-run
# drain below can only ever flag THIS round's leaks (spec: chain runs it before
# and after). The instrumented dir is SKIP_DIRS-whitelisted so its own profraw
# survives.
python3 scripts/run/clean_stray_profraw.py

pnpm -C browser build:browser
# Node-driven wasm suite (unit-test nature): the same test/unit code the browser
# job runs, here proving the wasm artifact loads and passes on this node version.
# TS-only v8 coverage — rust coverage is measured by the browser job below (the
# node harness's global() is a fakeSelf, so fetch arms never fire there).
pnpm -C browser test:unit

# Wasm rust coverage chain (browser-driven): measures core's browser-gated code
# under the wasm target in a REAL browser. The fetch backends (web_sys::fetch on
# Window/WorkerGlobalScope) only resolve against a real browser global scope —
# the node harness's fakeSelf hits the "no fetch-capable scope" arm instead, so
# those lines are reachable ONLY here. wasm-pack cannot build instrumented output
# (release+LTO collides with the __covrec_* symbols), so this uses cargo build
# (debug) + wasm-bindgen-cli to regenerate the web glue the worker loads. The
# instrumented build, glue, profraw dump, merged profdata and llc host objects all
# live under browser/target-wasm-cov (gitignored, SKIP_DIRS-whitelisted) so the
# stray drain never deletes them and they are never committed. The grading signal
# is the lcov report (LL-093: a broken chain shows 0 hits, not a missing profraw).
# Floor 100: unmet lines are listed for human triage, never silently exempted.
# The ignore regex drops third-party crates so the denominator is netwave's own
# core/src only.
WASM_COV_DIR="$PWD/browser/target-wasm-cov"
mkdir -p "$WASM_COV_DIR/profraw" coverage
# Start the dump dir empty: the merge below globs profraw/*.profraw, so a stale
# profraw from an earlier chain (or a different driver) would silently union into
# this round's report and mask real gaps.
rm -f "$WASM_COV_DIR"/profraw/*.profraw
CC="$WASI_SDK_CLANG" RUSTC_BOOTSTRAP=1 \
  CFLAGS_wasm32_unknown_unknown="--target=wasm32-unknown-unknown --sysroot=" \
  RUSTFLAGS="-Cinstrument-coverage -Zno-profiler-runtime --emit=llvm-ir" \
  CARGO_TARGET_DIR="$WASM_COV_DIR" \
  cargo build --manifest-path browser/Cargo.toml \
    --target wasm32-unknown-unknown --features coverage
wasm-bindgen --target web --out-dir "$PWD/browser/dist/wasm-cov" \
  "$WASM_COV_DIR/wasm32-unknown-unknown/debug/netwave_browser.wasm"
# v8 coverage is disabled here: the instrumented dispatch branch skips the
# production default-import line, so v8's 100% threshold is enforced by the
# plain test:browser run in CI's own step instead. This run only drives the wasm
# to dump profraw (the worker drains it and ships it back via a browser command).
NETWAVE_WASM_DIR="$PWD/browser/dist/wasm-cov" \
  NETWAVE_COV_OUT="$WASM_COV_DIR/profraw" \
  pnpm -C browser test:e2e --coverage.enabled=false
"$LLVM_BIN/llvm-profdata" merge -sparse "$WASM_COV_DIR"/profraw/*.profraw \
  -o "$WASM_COV_DIR/merged.profdata"
# llc needs the short host arch, not the full triple. The instrumented core CGU
# .ll is found by its source mapping, not its hash name. llc spells the x86-64
# backend "x86-64" (hyphen) while rustc's host triple uses "x86_64" (underscore);
# aarch64 matches on both sides, so only x86_64 needs remapping — a host that
# never runs the x86 cell cannot catch this (LL-096).
HOST_ARCH="$(rustc -vV | sed -n 's/^host: //p' | cut -d- -f1)"
case "$HOST_ARCH" in x86_64) HOST_ARCH="x86-64" ;; esac
# Locate the instrumented core CGU .ll by its source mapping, not its hash name.
# The path separator inside the .ll debug info differs per host: Linux writes a
# single forward slash (core/src/...), Windows escapes backslashes in the LLVM
# string literal so the file bytes are core\\src\\... (double backslash). Match
# ONE-OR-MORE separators ([\\/]+) so every form works without guessing which the
# host emits — a single-separator class silently matches zero files on Windows,
# yielding no .o and a cryptic llvm-cov "no such file" (LL-096, three-round fix).
COV_LL="$(grep -rlE 'core[\\/]+src[\\/]+(frequency|resources|touchstone)\.rs' \
  "$WASM_COV_DIR" --include='*.ll')"
if [ -z "$COV_LL" ]; then
  echo "no instrumented core .ll matched under $WASM_COV_DIR — coverage chain broken" >&2
  echo "(expected core/src/{frequency,resources,touchstone}.rs source mappings in .ll)" >&2
  exit 1
fi
i=0
while IFS= read -r ll; do
  "$LLVM_BIN/llc" --march="$HOST_ARCH" --filetype=obj \
    -o "$WASM_COV_DIR/cgu$i.o" "$ll"
  i=$((i + 1))
done <<< "$COV_LL"
# The ignore regex must match both path forms: Linux reports .cargo/registry
# (forward slash) while Windows reports C:\Users\runneradmin\.cargo\registry
# (backslash), so the separator class is [\\/]+ — a bare / silently matches
# zero files on Windows and third-party lines leak into the denominator
# (LL-096).
"$LLVM_BIN/llvm-cov" export --format=lcov "$WASM_COV_DIR"/cgu*.o \
  -instr-profile="$WASM_COV_DIR/merged.profdata" \
  --ignore-filename-regex='\.cargo[\\/]+registry' > coverage/coverage-wasm.lcov
# Floor 99 (not 100): the fetch "no fetch-capable scope" arm reads
# js_sys::global() with no injection point, so it is unreachable by any test or
# mock (decision wasm地板99). All other chains keep a 100 floor.
python3 scripts/coverage_gate.py coverage/coverage-wasm.lcov 99

# Production browser suite (TS-only v8 coverage, 100% threshold): the chain run
# above disables v8 (the instrumented dispatch branch skips the production
# default-import line), so the browser shell's v8 threshold is enforced here on
# the PRODUCTION wasm (no chain env → no alias, no dump hook). Same test code.
pnpm -C browser test:e2e

# Post-run: drain stray profraw so a broken chain this round is detected, never
# pushed past the gate. The instrumented dir is SKIP_DIRS-whitelisted so its own
# profraw survives; only chain-external strays are removed.
python3 scripts/run/clean_stray_profraw.py
