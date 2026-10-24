# Contributing to netwave

Developer-facing entry point: repository layout, workspace commands, toolchain
routing and the contribution workflow. User-facing description lives in
[README.md](README.md). Environment gotchas and implementation lessons live
in the [lessons-learned ledger](openspec/specs/lessons-learned/INDEX.md),
not here.

## Repository layout

```text
core/         Rust core crate — the single source of truth for all math
python/       PyO3 binding (numpy zero-copy views, maturin wheel)
typescript/   Single package, dual publish: napi native (node) + wasm (browser)
oracle/       Cross-validation: tolerance manifest, shared samples, grading
              (compare_cross.py); answer sheets in oracle/tmp/ (gitignored)
scripts/      Workspace-level helper scripts (gates, installers)
openspec/     OpenSpec: specs/ (governance + contracts + lessons-learned
              ledger) and changes/ (in-flight and archived change proposals)
Plan/         Unexecuted planning docs only; absorbed into openspec/ then
              deleted (lifecycle rules in AGENTS.md)
.github/      CI workflows (ci.yml matrix, gates)
```

## Quality gates

- **Lint/format/type**: `pnpm check` (md + ts + rs + py), auto-fix
  `pnpm fix`. Root `package.json` scripts are the single source of truth
  for command details — never restate them elsewhere.
- **Coverage floor**: thresholds are defined in the ci-matrix and
  project-governance specs (iron rule 7); the gate commands live in the
  root `package.json` scripts and CI.
- **Cross-binding compare**: `pnpm check:cross` dumps all four ends into
  `oracle/tmp/` and `oracle/compare_cross.py` verifies them (native ends
  bit-exact, wasm within manifest tolerance, plus an anti-tautology
  tamper self-check); contract in the oracle-harness and
  zero-copy-roundtrip specs.
- **Markdown**: editing any `.md` requires `pnpm check:md` to pass
  (markdownlint + prettier + link/anchor validation) before the change is
  considered done.

## Quick start (development)

```bash
pnpm install                        # JS dev tooling (biome, prettier, markdownlint)
cargo test --workspace            # Rust core + binding tests
pnpm -C typescript build:native   # napi .node addon
pnpm -C typescript build:wasm     # wasm-bindgen artifacts
uv sync --project python          # Python env (uv)
(cd python && uv run maturin develop)  # required after touching core
pnpm check:cross                  # four-end dump + compare
```

## Development workflow

Every core module (Touchstone / Network / Circuit / Frequency and their
sub-features) runs the same six-step loop:

```text
grill ──► spec ──► red ──► green ──► review ──► retro
```

- **grill**: surface ambiguities before writing code (port ranges, complex
  z0, edge cases, perf targets); decisions land in the change's
  `proposal.md` / `design.md`. No code in this step.
- **spec**: one module = one OpenSpec change (`/opsx:propose` generates
  proposal/specs/design/tasks). Every requirement must be testable, with
  tolerances referencing manifest keys, never hardcoded. `/opsx:sync` then
  `/opsx:archive` when done.
- **red**: write the failing test first and watch it fail (governance spec
  rule 2). Expected values come from independent oracles — skrf golden,
  closed-form solutions, physical invariants — never from the code under
  test.
- **green**: minimal code to pass, one vertical slice at a time; port
  skrf's proven algorithms, don't reinvent them.
- **review**: three-axis review before merge — Standards (governance spec
  rules + code smells) × Spec (fidelity to spec.md) × Lessons (check the
  change against every entry in the lessons-learned ledger; a hit bounces
  the change and is re-verified via the entry's detection method).
  Cross-binding changes additionally run `pnpm check:cross`. CI green is
  mandatory.
- **retro**: at archive time answer three questions — new tool gotchas or
  version drift? doc ambiguity or better pattern? tolerance/test-practice
  drift? — and write answers into the lessons-learned ledger (shard file +
  INDEX entry) or the governance spec directly (no separate issue lists).

### When to simplify

| Scenario                | Simplification                                         |
| ----------------------- | ------------------------------------------------------ |
| Docs/comments/constants | skip red/green; edit + review                          |
| Bug fix                 | full loop; red = a failing repro test first            |
| Throwaway prototype     | no tests, but code never reaches main; findings → spec |
| Pure binding glue       | skip unit/property; keep the cross-binding compare     |

### Toolchain (task → tool)

Versions are owned by lockfiles and `rust-toolchain.toml` — check them live
(`pnpm --version`, `uv --version`, `rustc --version`), never copy numbers
into docs.

| Task                  | Tool                                                  | Verify with                       |
| --------------------- | ----------------------------------------------------- | --------------------------------- |
| JS deps & workspace   | pnpm (corepack; non-interactive flag — ledger LL-009) | `pnpm --version`                  |
| Python envs           | uv + `pyproject.toml` (bare pip forbidden)            | `uv --version`                    |
| Python binding build  | maturin                                               | `uv run maturin develop`          |
| Rust build/test       | cargo (pinned by `rust-toolchain.toml`)               | `cargo test --workspace`          |
| Coverage gate         | cargo-llvm-cov (pre-install llvm-tools)               | see Quality gates                 |
| Node binding build    | napi-rs CLI                                           | `pnpm -C typescript build:native` |
| wasm build            | wasm-pack + binaryen (full-tree install)              | `pnpm -C typescript build:wasm`   |
| TS/JSON lint & format | Biome                                                 | `pnpm check:ts`                   |
| TS type gate          | `tsc --noEmit` (after both glues are built)           | `pnpm -C typescript typecheck`    |
| Markdown lint/format  | markdownlint-cli2 + Prettier + `check_md.py`          | `pnpm check:md`                   |
| Python lint & format  | ruff                                                  | `pnpm check:py`                   |
| Rust lint & format    | clippy + rustfmt                                      | `pnpm check:rs`                   |
| Spec workflow         | OpenSpec CLI (`/opsx:*`)                              | `openspec --help`                 |

### Toolchain freshness (project-owned upgrades)

Machine-wide CLIs (node, npm/pnpm, uv, rustup, markdownlint, OpenSpec CLI) are
upgraded by the knowledge-base upgrade guide; this section covers only what
netwave pins or ships itself.

- **Rust pin**: `rust-toolchain.toml` pins a stable on purpose; bumping the pin
  goes through an OpenSpec change (workspace-layout spec version floor). The
  toolchain rustup auto-installs for a new pin is bare — top it up:

  ```bash
  rustup component add rustfmt clippy
  rustup target add wasm32-unknown-unknown
  ```

- **pnpm version**: pinned by `packageManager` in the root `package.json` —
  that field is the source of truth; bump it to `pnpm@<latest>` (corepack then
  fetches it on the next run). Corepack is not bundled with Node ≥ 25; if the
  `corepack` command is missing, `npm install -g corepack && corepack enable`.
- **wasm toolchain**: wasm-pack and binaryen are always latest via the repo
  installers (never pinned — AGENTS.md dependency policy):

  ```bash
  bash scripts/install_wasm_pack.sh
  bash scripts/install_binaryen.sh
  ```

- **Playwright Chromium** (prerequisite for `test:browser` and the wasm dump
  in `check:cross`): `pnpm -C typescript exec playwright install --only-shell chromium`
- **cargo subcommands**: `cargo install cargo-llvm-cov --locked` (rustup
  updates do not touch cargo-installed subcommands).
- **Project dependencies** (dev deps, not global tools): periodic freshness
  check with `pnpm outdated`, `cargo update`, and
  `uv lock --upgrade --project python`
  (maturin/numpy/ruff/pytest live in the python dev group). Roll back
  only on a confirmed upstream bug (AGENTS.md dependency policy).
- **OpenSpec**: after upgrading the global CLI, run `openspec update` in this
  repo so the generated `/opsx:*` command files match the new CLI.

## Local reference mirrors (this machine only)

Authoritative terminology sources are kept as local clones for offline
reference; each book directory contains a `SKILL.md` with line-number
navigation. Portable citations (title + URL) live in
[README.md](README.md#references) — this table is the machine-bound lookup
entry only.

| Reference                                                    | License                                                       | Local path                                                              |
| ------------------------------------------------------------ | ------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Pupalaikis, _S-Parameters for Signal Integrity_, CUP 2020    | Copyright — never copy text/figures                           | `/config/GitHub/knowledge/RF/S-Parameters for Signal Integrity (2020)/` |
| Touchstone® File Format Specification v2.1 (IBIS Open Forum) | IBIS terms — full text never enters the repo                  | `/config/GitHub/knowledge/RF/Touchstone File Format Specification/`     |
| scikit-rf                                                    | BSD-3-Clause — code may be ported, notice ships               | `/config/GitHub/knowledge/RF/scikit-rf/`                                |
| SignalIntegrity                                              | GPL-3.0-or-later — **ideas only, never open its source code** | `/config/GitHub/knowledge/RF/SignalIntegrity/`                          |

On another machine these paths will not exist: run `ls` on each entry before
use; if missing, clone from the upstream URLs in
[README.md](README.md#references) to any path and update this table.

### Predecessor project (not a reference)

RF-Touchstone (MIT, panz2018) is netwave's **predecessor**: netwave
supersedes it and the wavelength API originates there. It is not an external
reference, so it is absent from the table above and from README References.
Local path `/config/GitHub/RF-Touchstone/` (same `ls` self-check applies);
code documentation must not cite it.
