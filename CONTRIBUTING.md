# Contributing to netwave

Thin gatehouse of the AI-required zone: repository layout, gate command
cheatsheet, machine-bound reference mirrors. Commands a human may type by
hand are collected in Quick start. Workflow bodies live in the governance
spec; environment gotchas and implementation lessons live in the
[lessons-learned ledger](openspec/specs/lessons-learned/INDEX.md).

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
Plan/         Unexecuted planning docs only; lifecycle rules live in
              openspec/config.yaml (operations hooks)
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
- **Proposal completeness**: `scripts/check_proposal.py` (wired into
  `pnpm check:meta`) validates every in-flight proposal; the contract body
  is the governance spec requirement
  [元规则 提案工件必带三节](openspec/specs/project-governance/spec.md#requirement-元规则-提案工件必带三节).

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

Every core module runs the six-step loop
`grill ──► spec ──► red ──► green ──► review ──► retro`; the binding rules of
each step live in the governance spec (TDD iron rule, review three axes) and
the [lessons-learned spec](openspec/specs/lessons-learned/spec.md) (retro
registration). This file keeps no workflow body.

### When to simplify

| Scenario                | Simplification                                         |
| ----------------------- | ------------------------------------------------------ |
| Docs/comments/constants | skip red/green; edit + review                          |
| Bug fix                 | full loop; red = a failing repro test first            |
| Throwaway prototype     | no tests, but code never reaches main; findings → spec |
| Pure binding glue       | skip unit/property; keep the cross-binding compare     |

### Toolchain (task → tool)

Tool choice and version pins are owned by lockfiles, `rust-toolchain.toml`
and the pin registry
[`scripts/versions/lib/registry.json`](scripts/versions/lib/registry.json) —
check them live (`pnpm --version`, `uv --version`, `rustc --version`), never
copy numbers into docs. Gate commands are defined once in root `package.json`
(see Quality gates above).

### Toolchain freshness (project-owned upgrades)

Upgrades are governed by the
[dependency-upgrade spec](openspec/specs/dependency-upgrade/spec.md):
strategy (latest stable, LTS lines), the pin registry
[`scripts/versions/lib/registry.json`](scripts/versions/lib/registry.json) as the single source
of truth for where versions are pinned, the reconciliation gate
(`scripts/versions/check_versions.py`, wired into `pnpm check:meta`), the fixed
upgrade order, and the manual freshness check `pnpm check:outdated` (project
deps + global CLIs + GitHub-tarball tools + CI actions). Machine-wide CLIs are
checked and upgraded as part of that flow too. This section keeps no rules of
its own (LL-065: pointer retargets to the main spec at sync).

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
