#!/usr/bin/env bash
# Install the LATEST binaryen (wasm-opt) into ~/.local/bin.
#
# Why not pin: wasm-pack's built-in download is stuck on binaryen 117
# (weak optimizer, larger output), and a pinned URL rots within months.
# We always take the latest GitHub release; if a future release breaks
# compatibility the build fails loudly and we fix it then (AGENTS.md
# dependency policy: latest by default, roll back only on a real bug).
#
# Usage: scripts/install_binaryen.sh
# In CI, the install dir is also appended to $GITHUB_PATH when present.
set -euo pipefail

say() { echo "[install_binaryen] $*"; }

say "querying latest release tag..."
tag=$(curl -fsSL https://api.github.com/repos/WebAssembly/binaryen/releases/latest \
  | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' | head -1)
say "latest tag: ${tag}"
arch=$(uname -m)
os=$(uname -s)
case "$os:$arch" in
  Linux:x86_64) plat="x86_64-linux" ;;
  Linux:aarch64) plat="aarch64-linux" ;;
  Darwin:x86_64) plat="x86_64-macos" ;;
  Darwin:arm64) plat="arm64-macos" ;;
  MINGW*:x86_64|MSYS*:x86_64) plat="x86_64-windows" ;;
  *) echo "unsupported platform: $os/$arch" >&2; exit 1 ;;
esac
url="https://github.com/WebAssembly/binaryen/releases/download/${tag}/binaryen-${tag}-${plat}.tar.gz"

say "downloading ${url}"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
curl -fL --progress-bar -o "$tmp/binaryen.tar.gz" "$url"
say "download done ($(du -h "$tmp/binaryen.tar.gz" | cut -f1)), extracting..."
tar xzf "$tmp/binaryen.tar.gz" -C "$tmp"

bindir="$HOME/.local/bin"
mkdir -p "$bindir"
say "installing to ${bindir}..."
# Visible to this shell too (GITHUB_PATH only affects later steps;
# Windows runners lack ~/.local/bin on PATH by default).
export PATH="$bindir:$PATH"
cp "$tmp/binaryen-${tag}/bin/"* "$bindir/"
chmod +x "$bindir"/wasm-opt*
say "installed binaryen ${tag} -> $bindir"
wasm-opt --version

if [ -n "${GITHUB_PATH:-}" ]; then
  echo "$bindir" >> "$GITHUB_PATH"
fi
