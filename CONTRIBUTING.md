# Contributing to netwave

Developer-facing entry point: workspace-level commands, environment setup and
the documentation map. User-facing description lives in [README.md](README.md).

## Quality gates

- **Lint/format/type**: `pnpm check` (md + ts + rs + py), auto-fix
  `pnpm fix`. Root `package.json` scripts are the single source of truth
  for command details — never restate them elsewhere.
- **Coverage floor (workspace)**:
  `cargo llvm-cov --workspace --fail-under-lines 100 --ignore-filename-regex '(python|typescript/(native|wasm))/src/lib\.rs'`
  — binding crates are covered by pytest/vitest in their own jobs (they need
  a JS/Python runtime; structurally unreachable under `cargo test`).
- **Cross-binding compare**: `pnpm check:cross` runs the four dumps (core,
  python, node, wasm) into `.cross-tmp/` and
  [`scripts/cross_compare.py`](scripts/cross_compare.py) verifies native ends
  bit-exact and wasm within the manifest tolerance, plus a built-in
  anti-tautology self-check (random-index tamper must be detected at the
  exact injected end and index); the rules themselves live in the
  zero-copy-roundtrip spec (openspec, once archived).
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

## Environment gotchas

- **corepack prompts**: prefix with `COREPACK_ENABLE_DOWNLOAD_PROMPT=0` or
  `pnpm` hangs waiting for an interactive download confirmation.
- **pyo3 linking outside VS Code**: the venv trio — `VIRTUAL_ENV`,
  `PYO3_PYTHON`, and `LD_LIBRARY_PATH` — must point at the uv-managed
  interpreter; `.vscode/settings.json` injects them automatically inside the
  editor.
- **nvm global packages** (local machines): `npm install -g` CLIs live under
  the Node version that installed them; after `nvm use` a command can
  "disappear" — reinstall or use `nvm install X --reinstall-packages-from=Y`.
- **GitHub Actions on Windows**: installer scripts run under git-bash but
  later steps default to pwsh — `GITHUB_PATH` entries must be native paths
  (`cygpath -w`), and `GITHUB_PATH` only affects _later_ steps, so an
  installer and the command that uses its binary cannot share one step.
- **binaryen layout**: `wasm-opt` resolves `libbinaryen.dylib`/`.dll` via
  RUNPATH `$ORIGIN/../lib`; install the release tree intact
  (`~/.local/opt/binaryen`), never copy `bin/` alone (macOS SIGABRT).
- **anonymous api.github.com** is capped at 60 req/h per shared runner IP;
  steps querying release tags must pass the workflow `GITHUB_TOKEN`
  (5000 req/h). Also: YAML flow mappings `{ k: ${{ ... }} }` break on the
  `}}` — use block style for `env:` with expressions.
- **manifest reads need explicit `encoding="utf-8"`**: `testdata/manifest.json`
  carries CJK notes; Windows' cp1252 default raises `UnicodeDecodeError`.
  Applies to every `read_text()` / `open()` in tests and scripts.

## Anti-rework checklist (phase-0 review lessons)

Each item below was a human-caught correction during phase 0; the goal is to
catch it before the review, not during. Before presenting any change for
human review, self-verify against this list:

- **CI: never iterate by pushing.** Simulate every matrix cell locally first
  (`bash -euo pipefail` + `shellcheck` on installer scripts; run each step's
  command verbatim). Known cross-platform traps hit in phase 0: Windows
  runner default shell is pwsh (not git-bash), macOS `grep` has no `-P`,
  `GITHUB_PATH` is native-path and next-step-only, YAML flow mappings break
  on `${{ }}`.
- **Never disable a gate or matrix cell to get green.** Fix the failing cell
  instead (phase-0 history: commented-out jobs / `if:`-skipped platforms /
  dropped wasm cells were all re-enabled after review). Coverage stays folded
  into the rust job as an if-gated step — a separate job reinstalled the
  whole toolchain for no reason.
- **Prove every gate can fail.** New gates get a negative test: an
  intentionally-uncovered probe to confirm `--fail-under-lines` goes red; a
  random-index tamper to confirm `cross_compare` detects it at the exact
  injected end and index (undetected tamper = hard failure, not a warning).
- **Verify commands exist before telling anyone to run them.** Phase 0
  suggested `openspec validate`, which is not a CLI subcommand. Run the
  command yourself, or quote `--help` output.
- **Default to latest dependencies; pin only as a documented fallback**
  (policy in [AGENTS.md](AGENTS.md)). Hardcoding a downloaded release number
  silently rots; use dynamic-latest installers (with retry) and record any
  `--precise` rollback + upstream issue in the child README's Gotchas.
  Paired deps (pyo3↔numpy, napi↔napi-derive) upgrade together, then rerun
  `pnpm check:cross`.
- **Output must name absolute paths.** Any script that writes a dump prints
  the full file path, not just "dumped bin".
- **Use the public surface in tests/examples** (e.g. the async `toY`
  contract: sync `_toY` computes in core, `async toY` wraps it and offloads
  to a worker only above the size threshold) — no `_` escape hatches in
  user-facing code or `dump_js`.
- **Docs: one fact, one home; then grep for the stale copy.** After changing
  a command, rename, or toolchain fact, grep all `.md` for the old form and
  update every occurrence (`409b057`/`4f5a9bd` fixed stale descriptions and
  four stale facts in archived tasks). Keep commands in the owning
  directory's README only; run `pnpm check:md` after every md edit.
- **Keep the toolchain status table current without being asked**: after
  verifying any tool install/upgrade, update the table in this file in the
  same change.
- **Binding glue stays glue.** No computation in py/ts shells — they call
  core's Rust functions; naming follows the api-contract spec (e.g.
  `f_scaled`, not invented synonyms). No unpublished platform placeholder
  packages in the workspace or CI.

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
- **review**: two-axis review before merge — Standards (governance spec
  rules + code smells) × Spec (fidelity to spec.md). Cross-binding changes
  additionally run `pnpm check:cross`. CI green is mandatory.
- **retro**: at archive time answer three questions — new tool gotchas or
  version drift? doc ambiguity or better pattern? tolerance/test-practice
  drift? — and write answers back into this file, child READMEs or the
  governance spec directly (no separate issue lists).

### When to simplify

| Scenario                | Simplification                                         |
| ----------------------- | ------------------------------------------------------ |
| Docs/comments/constants | skip red/green; edit + review                          |
| Bug fix                 | full loop; red = a failing repro test first            |
| Throwaway prototype     | no tests, but code never reaches main; findings → spec |
| Pure binding glue       | skip unit/property; keep the cross-binding compare     |

### Toolchain status (verified 2026-09-27)

| Tool                                                                                                                           | Status                                                                                            |
| ------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| OpenSpec CLI 1.13.1                                                                                                            | npm global under nvm v26; run`openspec update` in each initialized project after a CLI upgrade    |
| pnpm 12.5.1                                                                                                                    | corepack-managed; prefix`COREPACK_ENABLE_DOWNLOAD_PROMPT=0`                                       |
| uv 0.12.13                                                                                                                     | standalone install; Python envs per[python/README.md](python/README.md)                           |
| Rust 1.98.1 (rustup)                                                                                                           | `~/.cargo/bin`; `wasm32-unknown-unknown` target installed                                         |
| wasm-pack 0.15.0                                                                                                               | CI installs via[scripts/install_wasm_pack.sh](scripts/install_wasm_pack.sh)                       |
| cargo-llvm-cov / clippy / fmt / criterion                                                                                      | gate commands in Quality gates above                                                              |
| Harness skills (tdd, code-review, diagnosing-bugs, grilling, codebase-design, domain-modeling, prototype, research) + ponytail | installed under`~/.claude/skills/`                                                                |
| RF terminology routing                                                                                                         | two book SKILL.md under`~/GitHub/knowledge/RF/` (consult while writing; docs stay self-contained) |

## Documentation map

Permanent docs only. Planning documents (roadmap, test strategy) live under
`Plan/` temporarily and are absorbed into `openspec/` as changes land — they
are deliberately not linked here (Plan/ is deleted at the end of its
lifecycle; see [AGENTS.md](AGENTS.md)).

| Topic                          | Where                                            |
| ------------------------------ | ------------------------------------------------ |
| Rust core details              | [core/README.md](core/README.md)                 |
| Python binding details         | [python/README.md](python/README.md)             |
| Node/wasm binding details      | [typescript/README.md](typescript/README.md)     |
| Golden data & manifest schema  | [testdata/README.md](testdata/README.md)         |
| Workspace scripts              | [scripts/README.md](scripts/README.md)           |
| Agent working rules            | [AGENTS.md](AGENTS.md)                           |
| Specs (future source of truth) | `openspec/specs/` (populated as changes archive) |
