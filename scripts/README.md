# netwave scripts

Workspace-level tools only: CI gates and toolchain helpers. Not part of any
published package. Cross-binding grading lives in
[`oracle/compare_cross.py`](../oracle/compare_cross.py). A dump that serves a
single subproject lives in that subproject's `scripts/`
(`core/scripts/dump.rs`, `python/scripts/dump.py`,
`typescript/scripts/dump.mjs`).

## Scripts

| Script                 | Purpose                                                                                                                                          | Usage (from repo root)                                       |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------ |
| `bench_gate.py`        | criterion regression gate: fails on mean regression above the threshold (default `0.20`, ci-matrix spec)                                         | `python3 scripts/bench_gate.py target/criterion [threshold]` |
| `install_binaryen.sh`  | installs `wasm-opt` from GitHub **latest** (never pinned; local + CI share it)                                                                   | `bash scripts/install_binaryen.sh`                           |
| `install_wasm_pack.sh` | installs `wasm-pack` from GitHub **latest** official prebuilt tarballs (linux/macOS/windows; faster than `cargo install`)                        | `bash scripts/install_wasm_pack.sh`                          |
| `check_md.py`          | markdown checker: links/anchors + cross-line code-span detection                                                                                 | `python3 scripts/check_md.py`                                |
| `check_ci.py`          | CI gate completeness: every `typescript` `test:*` script must be wired into `ci.yml` (LL-037)                                                    | `python3 scripts/check_ci.py`                                |
| `versions/`            | version governance domain: pin registry + offline reconciliation gate + networked freshness check (see [versions/README.md](versions/README.md)) | `uv run python scripts/versions/check_versions.py`           |

The cross-binding pipeline (`pnpm check:cross`) and the grading contract
live in [CONTRIBUTING.md](../CONTRIBUTING.md) and
[oracle/README.md](../oracle/README.md); tolerance tiers are defined in the
[governance spec](../openspec/specs/project-governance/spec.md).
