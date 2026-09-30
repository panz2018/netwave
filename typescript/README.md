# netwave typescript binding

Single package, dual delivery: `node` resolves to the napi native addon,
`browser` to the WASM build — dispatched by `exports` conditions in
`package.json`. Both are thin transports over the Rust core (`../core`); they
never recompute values (governance spec rule: bindings only move memory; see
[`openspec/specs/project-governance/spec.md`](../openspec/specs/project-governance/spec.md)).

Current stage: phase-0 scaffold (`fillPattern` / `readElement` roundtrip).

## Layout

- `native/` — napi crate (`.node` addon), `build.rs` drives napi build
- `wasm/` — wasm-bindgen crate (`cdylib` only)
- `src/` — TypeScript shells (node/browser/worker/standalone) + `types.ts`
  (the single source of the public contract); tests run against `src/`
  (coverage measured there)
- `tsdown.config.ts` — bundles `src/*.ts` into `dist/` (ESM + CJS + dts);
  the napi/wasm generated glue stays external (never bundled)
- `dist/` — build output; the only published directory (`files: ["dist"]`)
- `scripts/publish_shell.mjs` — post-tsdown step: rewrites `"../dist/` →
  `"./` (and `.ts` specifiers → `.mjs`) inside the dist output so the
  published package is self-contained, emits the `index.d.ts`/`index.d.mts`
  hubs, and prints the dumped manifest for the cross-binding compare
- `test/native/` + `test/wasm/` — vitest suites split by platform; the two
  configs glob `test/native/**` / `test/wasm/**`, so new tests just drop in
- `vitest.native.config.ts` / `vitest.wasm.config.ts` — two configs, both with
  100% coverage thresholds

## Commands

Run from this directory (or `pnpm -C typescript <script>` from the root).

```bash
pnpm install                # workspace install (root package.json pins pnpm)
pnpm build:shells         # tsdown (src/*.ts -> dist ESM+CJS+dts) + publish_shell.mjs
pnpm build:native         # release: napi esm + commonjs two passes + build:shells
pnpm build:native:debug   # same pipeline without --release (fast local iteration)
pnpm build:wasm             # web target (wasm-pack defaults to release), CARGO_TARGET_DIR=../target-wasm
pnpm typecheck              # tsc --noEmit type gate (tsconfig.json)
pnpm test                   # all 4 suites, no coverage (quick smoke)
pnpm test:native            # vitest native (CI adds --coverage, 100% floor)
pnpm test:wasm              # vitest wasm  (CI adds --coverage, 100% floor)
pnpm test:native --coverage # native coverage gate (src/ only, 100% required)
pnpm test:wasm --coverage   # wasm coverage gate (src/ only, 100% required);
                            # HTML report in coverage/; exemptions need
                            # /* v8 ignore start/stop */ + reason comment
```

Lint/format/typecheck run from the repo root (both crates are workspace
members — member dirs must NOT keep their own `Cargo.lock`, the root lockfile
is authoritative):

```bash
pnpm check:rs             # cargo fmt + clippy (all workspace members)
pnpm fix:rs               # auto-fix Rust formatting + clippy
pnpm check:ts             # Biome + tsc --noEmit
pnpm fix:ts               # Biome auto-fix
```

Cross-binding dump (node + wasm ends; run from the repo root):

```bash
node typescript/scripts/dump.mjs .cross-tmp
```
