#!/usr/bin/env bash
# Install the wasm-bindgen CLI matching the crate version into ~/.local/bin.
#
# Why this tool: the wasm rust coverage chain builds an instrumented cdylib
# with `cargo build` (wasm-pack cannot — it forces release+LTO, which collides
# with the instrumentation symbols), then needs wasm-bindgen to turn that
# `.wasm` into the web-target JS glue the worker imports. wasm-pack bundles its
# own copy but does not expose it, so the CLI is installed separately.
#
# Why the version MATCHES THE CRATE (not "latest"): wasm-bindgen's generated
# glue and the linked `wasm-bindgen` crate must be the SAME version or the
# runtime aborts on a shim-version mismatch. So the version is read from
# Cargo.lock, not chased from GitHub's latest release (unlike binaryen).
#
# Why prebuilt first: the official GitHub release ships a tarball per target;
# `cargo install` compiles from source for minutes. Fall back to cargo install
# only when no tarball exists for this platform (dependency-upgrade spec:
# latest-by-default does not apply here — the crate pin is the ceiling).
#
# Usage: browser/scripts/install_wasm_bindgen_cli.sh
# In CI, the install dir is also appended to $GITHUB_PATH when present.
set -euo pipefail

say() { echo "[install_wasm_bindgen_cli] $*"; }

# The crate version is the single source of truth for the CLI version. The
# workspace has a single root Cargo.lock, two levels above this script.
version=$(sed -n '/^name = "wasm-bindgen"$/{n;s/^version = "\([^"]*\)".*/\1/p;}' \
  "$(dirname "$0")/../../Cargo.lock" | head -1)
if [ -z "$version" ]; then
  echo "could not read wasm-bindgen version from Cargo.lock" >&2
  exit 1
fi
say "crate version (CLI target): ${version}"

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
url="https://github.com/rustwasm/wasm-bindgen/releases/download/${version}/wasm-bindgen-${version}-${plat}.tar.gz"

bindir="$HOME/.local/bin"
mkdir -p "$bindir"

# Prebuilt tarball first; cargo install only if the release has no asset for
# this platform (curl -f fails on 404). The archive has a wrapper directory
# named wasm-bindgen-<version>-<plat>, so extract to a temp dir and move the
# binaries out.
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
if curl -fL --retry 3 --retry-all-errors --progress-bar -o "$tmp/wasm-bindgen.tar.gz" "$url"; then
  say "downloading ${url}"
  tar xzf "$tmp/wasm-bindgen.tar.gz" -C "$tmp"
  say "installing to ${bindir}..."
  # Copy (not symlink): the archive lives under $tmp, which the EXIT trap
  # deletes — a symlink into it would dangle. The CLI is a single static
  # binary with no runtime lib deps, so copying is self-contained.
  for f in "$tmp"/wasm-bindgen-${version}-${plat}/wasm-bindgen*; do
    [ -f "$f" ] || continue
    name=$(basename "$f")
    rm -f "$bindir/$name"
    cp "$f" "$bindir/$name"
  done
  chmod +x "$bindir"/wasm-bindgen*
else
  say "no prebuilt tarball for ${plat} — compiling from source (slow)"
  cargo install wasm-bindgen-cli --version "$version" --locked --root "$HOME/.local"
fi

# Make the freshly installed binary visible to *this* shell too: CI's
# GITHUB_PATH only applies to later steps, and Windows runners do not have
# ~/.local/bin on PATH by default.
export PATH="$bindir:$PATH"

# Verify the installed CLI matches the crate exactly — a mismatch would make
# the generated glue abort at runtime.
installed=$(wasm-bindgen --version | sed -n 's/.* \([0-9][^ ]*\)$/\1/p')
if [ "$installed" != "$version" ]; then
  echo "wasm-bindgen CLI $installed does not match crate $version" >&2
  exit 1
fi
say "installed wasm-bindgen ${installed} (${plat}) -> $bindir"

if [ -n "${GITHUB_PATH:-}" ]; then
  # GITHUB_PATH is consumed by later steps running in the *default* Windows
  # shell (pwsh), which cannot resolve MSYS paths like /c/Users/... — convert
  # to native form (cygpath exists only on Windows; elsewhere a no-op).
  npath() { command -v cygpath >/dev/null 2>&1 && cygpath -w "$1" || echo "$1"; }
  echo "$(npath "$bindir")" >> "$GITHUB_PATH"
fi
