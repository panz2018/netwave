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

tag=$(curl -fsSL https://api.github.com/repos/WebAssembly/binaryen/releases/latest \
  | grep -oP '"tag_name":\s*"\K[^"]+')
arch=$(uname -m)
case "$arch" in
  x86_64) barch="x86_64" ;;
  aarch64) barch="aarch64" ;;
  *) echo "unsupported arch: $arch" >&2; exit 1 ;;
esac
url="https://github.com/WebAssembly/binaryen/releases/download/${tag}/binaryen-${tag}-${barch}-linux.tar.gz"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
curl -fsSL -o "$tmp/binaryen.tar.gz" "$url"
tar xzf "$tmp/binaryen.tar.gz" -C "$tmp"

bindir="$HOME/.local/bin"
mkdir -p "$bindir"
cp "$tmp/binaryen-${tag}/bin/"* "$bindir/"
chmod +x "$bindir"/wasm-opt*
echo "installed binaryen ${tag} -> $bindir"
wasm-opt --version

if [ -n "${GITHUB_PATH:-}" ]; then
  echo "$bindir" >> "$GITHUB_PATH"
fi
