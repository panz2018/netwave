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
curl -fL --retry 3 --retry-all-errors --progress-bar -o "$tmp/binaryen.tar.gz" "$url"
say "download done ($(du -h "$tmp/binaryen.tar.gz" | cut -f1)), extracting..."
tar xzf "$tmp/binaryen.tar.gz" -C "$tmp"

# Install the WHOLE tree (bin + lib), not just the bin files: the
# wasm-opt binary dlopen's libbinaryen.dylib/.dll via RUNPATH
# $ORIGIN/../lib. Copying only bin/ into ~/.local/bin breaks that
# relative path — macOS aborts with SIGABRT (exit 134, dyld:
# libbinaryen.dylib not found) and Windows fails to load
# binaryen.dll. Keeping the tree intact preserves $ORIGIN/../lib on
# every platform; executables are symlinked into ~/.local/bin (real
# copies on Windows, where symlinks need privileges).
prefix="$HOME/.local/opt/binaryen"
bindir="$HOME/.local/bin"
rm -rf "$prefix"
mkdir -p "$prefix" "$bindir"
say "installing to ${prefix}..."
mv "$tmp/binaryen-${tag}"/* "$prefix/"
for f in "$prefix"/bin/*; do
  name=$(basename "$f")
  rm -f "$bindir/$name"
  ln -s "$f" "$bindir/$name" 2>/dev/null || cp "$f" "$bindir/$name"
done
chmod +x "$bindir"/wasm-opt*
# Visible to this shell too (GITHUB_PATH only affects later steps).
# $prefix/bin goes on PATH as well: on Windows the copied
# wasm-opt.exe needs binaryen.dll next to it, and PATH is where
# wasm-pack looks for wasm-opt.
export PATH="$bindir:$prefix/bin:$PATH"
say "installed binaryen ${tag} -> $prefix"
wasm-opt --version

if [ -n "${GITHUB_PATH:-}" ]; then
  # GITHUB_PATH is consumed by later steps running in the *default*
  # Windows shell (pwsh), which cannot resolve MSYS paths like
  # /c/Users/... — convert to native form (cygpath exists only on
  # Windows; elsewhere it is a no-op passthrough).
  npath() { command -v cygpath >/dev/null 2>&1 && cygpath -w "$1" || echo "$1"; }
  echo "$(npath "$bindir")" >> "$GITHUB_PATH"
  echo "$(npath "$prefix/bin")" >> "$GITHUB_PATH"
fi
