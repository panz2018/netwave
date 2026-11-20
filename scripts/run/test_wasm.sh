#!/usr/bin/env bash
# Wasm test entry: build the wasm artifact, run the node-driven wasm suite and
# the real-browser suite. Single source of truth for wasm test command details —
# local `pnpm test:wasm` and the CI wasm job both call this file, so parameters
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
  echo "chromium not installed — install it with: pnpm -C typescript exec playwright install --only-shell chromium" >&2
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

pnpm -C typescript build:wasm
pnpm -C typescript test:wasm
pnpm -C typescript test:browser
