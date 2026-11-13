#!/usr/bin/env bash
# Install the LATEST cargo-llvm-cov into ~/.local/bin (official GitHub binaries).
#
# Why not `cargo install cargo-llvm-cov`: it compiles from source for minutes
# on every CI job; the official release tarballs are prebuilt for all our
# targets. Why not pin: same policy as install_wasm_pack.sh — always latest,
# fix forward on a real break (dependency-upgrade spec).
#
# Usage: scripts/install_cargo_llvm_cov.sh
# In CI, the install dir is also appended to $GITHUB_PATH when present.
set -euo pipefail

say() { echo "[install_cargo_llvm_cov] $*"; }

say "querying latest release tag..."
# Unauthenticated api.github.com is rate-limited to 60 req/h per IP —
# GitHub-hosted runners share IPs, so parallel jobs hit 403. In CI,
# export GITHUB_TOKEN (the workflow's built-in token, 5000 req/h) on
# the step that runs this script.
if [ -n "${GITHUB_TOKEN:-}" ]; then
  tag=$(curl -fsSL -H "Authorization: Bearer $GITHUB_TOKEN" \
    https://api.github.com/repos/taiki-e/cargo-llvm-cov/releases/latest \
    | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' | head -1)
else
  tag=$(curl -fsSL https://api.github.com/repos/taiki-e/cargo-llvm-cov/releases/latest \
    | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' | head -1)
fi
say "latest tag: ${tag}"
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
url="https://github.com/taiki-e/cargo-llvm-cov/releases/download/${tag}/cargo-llvm-cov-${plat}.tar.gz"

say "downloading ${url}"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
curl -fL --retry 3 --retry-all-errors --progress-bar -o "$tmp/cargo-llvm-cov.tar.gz" "$url"
say "download done ($(du -h "$tmp/cargo-llvm-cov.tar.gz" | cut -f1)), extracting..."

bindir="$HOME/.local/bin"
mkdir -p "$bindir"
say "installing to ${bindir}..."
# Unlike wasm-pack's tarball, this archive has no wrapper directory: the top
# level is the bare binary (cargo-llvm-cov, cargo-llvm-cov.exe on Windows),
# so extract straight into the install dir.
tar xzf "$tmp/cargo-llvm-cov.tar.gz" -C "$bindir"
chmod +x "$bindir"/cargo-llvm-cov*
say "installed cargo-llvm-cov ${tag} (${plat}) -> $bindir"

# LL-085: ~/.cargo/bin sits earlier on PATH than ~/.local/bin, so a leftover
# `cargo install` build silently shadows the freshly installed binary and the
# upgrade has no effect. Detect against the *pre-existing* PATH (before the
# export below prepends bindir), drop the shadowing copy, then re-verify.
hit=$(command -v cargo-llvm-cov 2>/dev/null || true)
case "$hit" in
  "$HOME"/.cargo/bin/cargo-llvm-cov*)
    say "removing PATH-shadowing stale binary: $hit"
    rm -f "$hit"
    ;;
esac
# Make the freshly installed binary visible to *this* shell too: CI's
# GITHUB_PATH only applies to later steps, and Windows runners do not
# have ~/.local/bin on PATH by default.
export PATH="$bindir:$PATH"
hit=$(command -v cargo-llvm-cov)
case "$hit" in
  "$bindir"/cargo-llvm-cov*) ;;
  *) echo "cargo-llvm-cov still resolves to $hit, not $bindir" >&2; exit 1 ;;
esac
# Smoke test through cargo: the binary is a cargo subcommand and rejects
# `--version` when invoked directly (it expects argv[1] = "llvm-cov").
cargo llvm-cov --version

if [ -n "${GITHUB_PATH:-}" ]; then
  # GITHUB_PATH is consumed by later steps running in the *default*
  # Windows shell (pwsh), which cannot resolve MSYS paths like
  # /c/Users/... — convert to native form (cygpath exists only on
  # Windows; elsewhere it is a no-op passthrough).
  npath() { command -v cygpath >/dev/null 2>&1 && cygpath -w "$1" || echo "$1"; }
  echo "$(npath "$bindir")" >> "$GITHUB_PATH"
fi
