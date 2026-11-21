#!/usr/bin/env bash
# Install the LATEST wasi-sdk into ~/.local/opt/wasi-sdk (official GitHub
# tarballs, no sudo).
#
# Why this tool: the wasm rust coverage chain compiles minicov's wasm32 C
# runtime, whose build.rs hardcodes a clang that can target wasm32. gcc has no
# wasm32 backend and zig's wasm objects carry a non-standard ELF machine that
# rust-lld ignores, so wasi-sdk's stock clang is the tool. Its clang major
# tracks rustc's LLVM major (wasi-sdk 34 = clang 23, pinned rustc = LLVM 23).
#
# Why not pin: same policy as install_binaryen.sh — always latest, roll back
# only on a real break (dependency-upgrade spec). The version is read from the
# release asset name, not assumed, because the tag (wasi-sdk-34) and the file
# version (34.0) differ.
#
# Usage: scripts/install_wasi_sdk.sh
# In CI, the install dir is also appended to $GITHUB_PATH when present.
set -euo pipefail

say() { echo "[install_wasi_sdk] $*"; }

say "querying latest release..."
# Unauthenticated api.github.com is rate-limited to 60 req/h per IP — CI
# runners share IPs, so parallel jobs hit 403. In CI export GITHUB_TOKEN
# (the workflow's built-in token, 5000 req/h) on the step that runs this.
api=https://api.github.com/repos/WebAssembly/wasi-sdk/releases/latest
if [ -n "${GITHUB_TOKEN:-}" ]; then
  json=$(curl -fsSL -H "Authorization: Bearer $GITHUB_TOKEN" "$api")
else
  json=$(curl -fsSL "$api")
fi

os=$(uname -s)
arch=$(uname -m)
case "$os:$arch" in
  Linux:x86_64) plat="x86_64-linux" ;;
  Linux:aarch64) plat="arm64-linux" ;;
  Darwin:x86_64) plat="x86_64-macos" ;;
  Darwin:arm64) plat="arm64-macos" ;;
  MINGW*:x86_64|MSYS*:x86_64) plat="x86_64-windows" ;;
  *) echo "unsupported platform: $os/$arch" >&2; exit 1 ;;
esac

# Pick the clang tarball for this platform (the .deb is Debian-only; the
# libclang_rt / wasi-sysroot assets are not the full SDK). The download URL is
# taken verbatim from the release so no version format is assumed.
url=$(printf '%s' "$json" \
  | grep -oE '"browser_download_url": *"[^"]*wasi-sdk-[^"]*'"${plat}"'\.tar\.gz"' \
  | sed -n 's/.*"\(https[^"]*\)"/\1/p' | head -1)
if [ -z "$url" ]; then
  echo "no wasi-sdk tarball found for platform ${plat}" >&2
  exit 1
fi
say "downloading ${url}"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
curl -fL --retry 3 --retry-all-errors --progress-bar -o "$tmp/wasi-sdk.tar.gz" "$url"
say "download done ($(du -h "$tmp/wasi-sdk.tar.gz" | cut -f1)), extracting..."
tar xzf "$tmp/wasi-sdk.tar.gz" -C "$tmp"

# The archive has a single wrapper dir (wasi-sdk-<ver>-<plat>) holding the
# SDK tree (bin/clang, share/wasi-sysroot, ...). Install the whole tree to a
# stable prefix so callers reference ~/.local/opt/wasi-sdk/bin/clang.
prefix="$HOME/.local/opt/wasi-sdk"
rm -rf "$prefix"
mkdir -p "$(dirname "$prefix")"
mv "$tmp"/wasi-sdk-*-"${plat}" "$prefix"

# Visible to this shell too (GITHUB_PATH only affects later steps).
export PATH="$prefix/bin:$PATH"
say "installed wasi-sdk -> $prefix"
"$prefix/bin/clang" --version | head -1

if [ -n "${GITHUB_PATH:-}" ]; then
  # GITHUB_PATH is consumed by later steps in the *default* Windows shell
  # (pwsh), which cannot resolve MSYS paths — convert to native form
  # (cygpath exists only on Windows; elsewhere a no-op passthrough).
  npath() { command -v cygpath >/dev/null 2>&1 && cygpath -w "$1" || echo "$1"; }
  echo "$(npath "$prefix/bin")" >> "$GITHUB_PATH"
fi
