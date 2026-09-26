# netwave typescript binding

Single package, dual delivery: `node` resolves to the napi native addon,
`browser` to the WASM build — dispatched by `exports` conditions in
`package.json`. Both are thin transports over the Rust core (`../core`); they
never recompute values (constitution rule: bindings only move memory).

Current stage: phase-0 scaffold (`fillPattern` / `readElement` roundtrip).

## Layout

- `native/` — napi crate (`.node` addon), `build.rs` drives napi build
- `wasm/` — wasm-bindgen crate (`cdylib` only)
- `src/` — shell modules (node/browser/worker/standalone) + public `index.d.ts`;
  tests run against `src/` (coverage measured there)
- `dist/` — build output; the only published directory (`files: ["dist"]`)
- `scripts/publish_shell.mjs` — copies shells to `dist/` and rewrites
  `"../dist/` → `"./` so the published package is self-contained
- `test/` — vitest suites (native/wasm/worker/exports)
- `vitest.native.config.ts` / `vitest.wasm.config.ts` — two configs, both with
  100% coverage thresholds

## Commands

Run from this directory (or `pnpm -C typescript <script>` from the root).

```bash
pnpm install                # workspace install (root package.json pins pnpm)
pnpm build:native           # release: napi esm + commonjs two passes + publish_shell.mjs
pnpm build:native:debug     # same pipeline without --release (fast local iteration)
pnpm build:wasm             # web target (wasm-pack defaults to release), CARGO_TARGET_DIR=../target-wasm
pnpm typecheck              # tsc --noEmit type gate (tsconfig.json)
pnpm test                   # all 4 suites, no coverage (quick smoke)
pnpm test:native            # vitest native (CI adds --coverage, 100% floor)
pnpm test:wasm              # vitest wasm  (CI adds --coverage, 100% floor)
pnpm test:native --coverage # native coverage gate (src/ only, 100% required)
pnpm test:wasm --coverage   # wasm coverage gate (src/ only, 100% required);
                            # HTML report in coverage/; exemptions need
                            # /* v8 ignore start/stop */ + reason comment
cargo fmt --manifest-path native/Cargo.toml --check
                            # + same for wasm/Cargo.toml: this directory has no
                            # Cargo.toml and native/ + wasm/ are workspace
                            # -excluded until manual review lands, so -p does not
                            # resolve — always pass --manifest-path here
cargo clippy --manifest-path native/Cargo.toml -- -D warnings
                            # + same for wasm/Cargo.toml; warnings are errors
```

JS/TS lint+format and the `tsc` type gate are owned by root-level
`pnpm check:ts` / `pnpm fix:ts` (Biome config: root `biome.json`); Markdown by
`pnpm check:md` / `pnpm fix:md` — see root [AGENTS.md](../AGENTS.md).

Cross-binding dump (node + wasm ends; run from the repo root):

```bash
node scripts/dump_js.mjs .cross-tmp
```

## Implementation notes

- **napi zero-copy Buffer**: `Buffer::from(vec)` internally `mem::forget`s the
  Vec. Rebuilding on the JS side must pass the full capacity
  (`v.capacity() * 16` bytes for `Complex<f64>`), otherwise the GC double-frees.
  Returning a raw `Vec` degrades to a per-element JS Array — always declare the
  explicit `Buffer` return type.
- **napi CLI flags drift on upgrade** (verified against the installed version):
  `--manifest-path` (not `--cargo-cwd`), `--format commonjs` (not `cjs`).
  Re-check after every napi upgrade.
- **wasm target = `web`**, not `bundler`: bundler glue cannot be loaded under
  node/vitest; web glue works on both ends. Long-term constraint pending
  decision (see Plan/阶段0复盘回写.md).
- **wasm init takes `{ module_or_path: bytes }`**: node has no
  `fetch("file:...")`; the string/URL init form is deprecated.
- **`js_sys::WebAssembly::Memory`**: `js_sys::Memory` does not exist.
- **wasm-opt**: `scripts/install_binaryen.sh` installs GitHub **latest**
  (local + CI share it, never pinned). wasm-pack's built-in download is stuck on
  binaryen 117 — worse optimization, bigger output — so the newer binaryen must
  shadow it on PATH.
- **worker memory is never transferable**: transferring the wasm linear memory
  detaches the instance. `.slice()` the bytes into a fresh ArrayBuffer and
  transfer that instead.
- **shell files**: `src/` shells import `"../dist/..."` (tests run against
  src/); `publish_shell.mjs` rewrites to `"./..."` when copying into `dist/`.
  Edit `src/`, never hand-edit `dist/`.
- **npm platform packages**: `optionalDependencies` maps `netwave-{os}-{arch}`
  names to per-platform packages (linux-x64-gnu, linux-arm64-gnu,
  win32-x64-msvc, darwin-arm64) — the directory name `typescript/` and the
  published package name `netwave` are deliberately decoupled.

## Gotchas

- **Rebuild after touching core**: `pnpm build:native` and `build:wasm` before
  any test or cross-binding comparison, otherwise you compare stale artifacts.
- **Dumps are binary `.bin`** (little-endian f64): `JSON.stringify(-0)` emits
  `"0"` and loses the sign bit. Contract:
  [`../testdata/README.md`](../testdata/README.md).
- **Coverage exemptions use `/* v8 ignore start/stop */`** and each one must
  carry a reason comment; blanket file-level exemptions are forbidden
  (测试规划 coverage rules).
- **napi in containers** may print
  `Skipping cross-process filesystem reconciliation lock ... (missing: machine)`:
  the CLI names its cross-process build lock after `/etc/machine-id`, which must
  match `^[0-9a-f]{32}$` (no dashes — a dashed UUID fails validation). Harmless
  (build proceeds, only the lock is skipped). To silence it:
  `cat /proc/sys/kernel/random/uuid | tr -d '-' | sudo tee /etc/machine-id`.
