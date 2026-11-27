#!/usr/bin/env bash
# Cross-binding test entry: four-end dump + grading + cross-end vocabulary
# gates. Single source of truth for cross-binding test command details — local
# `pnpm test:cross` and the CI node job both call this file, so parameters
# cannot drift apart. The napi/browser glues are built by test_ts.sh (probed
# here, never rebuilt); the python glue has no builder in this job, so this
# entry builds it via python/scripts/build.sh before dumping.
#
# Stages, in order: tool probes -> artifact probes -> build -> dump (core /
# python / node / browser) -> grading. Every probe runs before any dump so a
# missing tool or artifact fails fast with an actionable message.
set -euo pipefail

cd "$(dirname "$0")/../.."

# --- Stage 1: toolchain probes ---------------------------------------------
# Missing tools print the install hint and exit non-zero — never auto-install
# (machine side effect; CI has its own install steps).

# uv runs the python-end dump against the built glue.
if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found — install it with: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
  exit 1
fi

# Browser end: real-browser harness (playwright + chromium). Probe the chromium
# cache; never auto-install (CI installs it in its own step).
pw_cache="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/.cache/ms-playwright}"
case "$(uname)" in
  Darwin) pw_cache="${PLAYWRIGHT_BROWSERS_PATH:-$HOME/Library/Caches/ms-playwright}" ;;
  MINGW* | MSYS* | CYGWIN*) pw_cache="${PLAYWRIGHT_BROWSERS_PATH:-${LOCALAPPDATA:-$HOME/AppData/Local}/ms-playwright}" ;;
esac
if ! ls -d "$pw_cache"/chromium* >/dev/null 2>&1; then
  echo "chromium not installed — install it with: pnpm -C browser exec playwright install --only-shell chromium" >&2
  exit 1
fi

# --- Stage 2: artifact probes ----------------------------------------------
# The node/browser ends dump from glues test_ts.sh built; this entry never
# rebuilds them (build logic lives once in scripts/run/test_ts.sh for napi,
# browser/scripts/test.sh / pnpm -C browser build for the browser). Missing
# artifacts print the command that produces them.

if ! ls typescript/dist/index.node.mjs typescript/dist/index.*.node >/dev/null 2>&1; then
  echo "napi glue missing under typescript/dist/ — build it with: pnpm test:ts" >&2
  exit 1
fi
if [ ! -f browser/dist/wasm/netwave_browser_bg.wasm ]; then
  echo "browser wasm glue missing under browser/dist/wasm/ — build it with: pnpm -C browser build" >&2
  exit 1
fi

# --- Stage 3: build --------------------------------------------------------
# The python glue has no builder in this job (unlike napi/browser, which
# test_ts.sh built), so build it here via its single-source entry before the
# dump. uv was probed above; build.sh re-probes it and never auto-installs.
bash python/scripts/build.sh

# --- Stage 4: four-end dump ------------------------------------------------
# The core example and the napi .node may be the instrumented builds the
# coverage entries left in target/; running them would emit a stray profraw at
# the repo root (a coverage-chain-broken signal to the next entry's drain).
# This entry is a correctness gate, not a coverage one, so redirect the
# instrumented runtime's output to discard — no profraw is written.
export LLVM_PROFILE_FILE=/dev/null
cargo run -q -p netwave --example dump oracle/tmp
uv run --project python python python/scripts/dump.py oracle/tmp
node typescript/scripts/dump.node.mjs oracle/tmp
node browser/scripts/dump.mjs oracle/tmp

# --- Stage 5: grading + cross-end gates ------------------------------------
# Grading (native ends bit-exact, browser within manifest tolerance) with the
# built-in anti-tautology tamper self-check, then the cross-end vocabulary type
# gate and the verb-set gate — all assert against the artifacts dumped above.
python3 oracle/compare_cross.py oracle/tmp
python3 scripts/check_vocab_types.py
python3 scripts/check_verbs.py
