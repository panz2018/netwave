#!/usr/bin/env bash
# Install the LATEST wasm-pack into ~/.local/bin (official GitHub binaries).
#
# Why not `cargo install wasm-pack`: it compiles for minutes on every CI
# job; the official release tarballs are prebuilt for all our targets.
# Why not pin: same policy as install_binaryen.sh — always latest, fix
# forward on a real break (AGENTS.md dependency policy).
#
# Usage: scripts/install_wasm_pack.sh
# In CI, the install dir is also appended to $GITHUB_PATH when present.
set -euo pipefail

tag=$(curl -fsSL https://api.github.com/repos/wasm-bindgen/wasm-pack/releases/latest \
  | grep -oP '"tag_name":\s*"\K[^"]+')
os=$(uname -s)
arch=$(uname -m)
case "$os:$arch" in
  Linux:x86_64) plat="x86_64-unknown-linux-musl" ;;
  Linux:aarch64) plat="aarch64-unknown-linux-musl" ;;
  Darwin:x86_64) plat="x86_64-apple-darwin" ;;
  Darwin:arm64) plat="aarch64-apple-darwin" ;;
  MINGW*:x86_64|MSYS*:x86_64) plat="x86_64-pc-windows-msvc" ;;
  *) echo "unsupported platform: $os/$arch" >&2; exit 1 ;;
esac
url="https://github.com/wasm-bindgen/wasm-pack/releases/download/${tag}/wasm-pack-${tag}-${plat}.tar.gz"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
curl -fsSL -o "$tmp/wasm-pack.tar.gz" "$url"
tar xzf "$tmp/wasm-pack.tar.gz" -C "$tmp"

bindir="$HOME/.local/bin"
mkdir -p "$bindir"
# Windows ships wasm-pack.exe; cp keeps the name as-is on other platforms.
cp "$tmp/wasm-pack-${tag}-${plat}/"wasm-pack* "$bindir/"
chmod +x "$bindir"/wasm-pack*
echo "installed wasm-pack ${tag} (${plat}) -> $bindir"
"$bindir/wasm-pack" --version || "$bindir/wasm-pack.exe" --version

if [ -n "${GITHUB_PATH:-}" ]; then
  echo "$bindir" >> "$GITHUB_PATH"
fi
