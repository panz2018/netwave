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
if ! rustup target list --installed 2>/dev/null | grep -q '^wasm32-unknown-unknown$'; then
  echo "wasm32-unknown-unknown target not installed — add it with: rustup target add wasm32-unknown-unknown" >&2
  exit 1
fi
# Chromium probe: the real-browser suite needs a playwright chromium. Detect the
# playwright browser cache; never auto-install (CI installs it in its own step).
if ! node -e '
const os=require("os"),fs=require("fs"),path=require("path");
const home=os.homedir();
const dir=process.env.PLAYWRIGHT_BROWSERS_PATH||(process.platform==="darwin"?path.join(home,"Library","Caches","ms-playwright"):process.platform==="win32"?path.join(process.env.LOCALAPPDATA||path.join(home,"AppData","Local"),"ms-playwright"):path.join(home,".cache","ms-playwright"));
process.exit(fs.existsSync(dir)&&fs.readdirSync(dir).some((d)=>d.startsWith("chromium"))?0:1);
' 2>/dev/null; then
  echo "chromium not installed — install it with: pnpm -C typescript exec playwright install --only-shell chromium" >&2
  exit 1
fi

pnpm -C typescript build:wasm
pnpm -C typescript test:wasm
pnpm -C typescript test:browser
