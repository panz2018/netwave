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

## Documentation map

Permanent docs only. Planning documents (roadmap, test strategy, workflow)
live under `Plan/` temporarily and are absorbed into `openspec/` as changes
land — they are deliberately not linked here (Plan/ is deleted at the end of
its lifecycle; see [AGENTS.md](AGENTS.md)).

| Topic                          | Where                                            |
| ------------------------------ | ------------------------------------------------ |
| Rust core details              | [core/README.md](core/README.md)                 |
| Python binding details         | [python/README.md](python/README.md)             |
| Node/wasm binding details      | [typescript/README.md](typescript/README.md)     |
| Golden data & manifest schema  | [testdata/README.md](testdata/README.md)         |
| Workspace scripts              | [scripts/README.md](scripts/README.md)           |
| Agent working rules            | [AGENTS.md](AGENTS.md)                           |
| Specs (future source of truth) | `openspec/specs/` (populated as changes archive) |
