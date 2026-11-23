# netwave typescript binding

Single package, dual delivery: `node` resolves to the napi native addon built
here, `browser` to the WASM build produced by the sibling `netwave-browser`
package and merged into `dist/` at build time — dispatched by `exports`
conditions in `package.json`. Both are thin transports over the Rust core
(`../core`); they never recompute values (governance spec rule: bindings only
move memory; see
[`openspec/specs/project-governance/spec.md`](../openspec/specs/project-governance/spec.md)).

Current stage: the `Touchstone` class is the data authority on both ends
(`fromData`/`fromText`/`fromBytes`/`fromFile`/`fromUrl` factories; node `s` is a
zero-copy external view, browser `s` clones back from the worker) on the
resident-worker architecture (governance spec ironclad rule 8). `fromBytes`/
`toBytes` cross the byte boundary as `Uint8Array` (encoding whitelists
`UTF-8`/`ISO-8859-1`; read default guesses, write default UTF-8 — see the
touchstone-core spec).

Singleton worker: in browsers, all data and compute live inside ONE resident
worker (`getWorker()` registers it on `globalThis`); the main thread never
inits wasm and holds no data copy. Multiple imports, multiple handles, or
duplicate library copies on one page structurally share that single worker.
Load only ONE copy of the library per page — a second copy's handles run
against the first copy's worker (version skew). The browser entry exports no
`_`-prefixed sync compute (there is none without main-thread wasm); node
keeps `_` because the napi core is in-process.

wasm linear-memory high-water mark: the wasm heap only grows, never shrinks
toward the host. `drop()` (and the GC fallback) runs the Rust destructor,
which returns the freed bytes to the wasm allocator's free list for REUSE by
later allocations — it does NOT hand memory back to the browser. So the
process peak equals the largest set of simultaneously-live objects, not the
cumulative total ever allocated. To lower the peak, drop handles you no
longer need (the worker frees them deterministically); do not expect the
wasm module's footprint to shrink after drops.

## Layout

- `native/` — napi crate (`.node` addon), `build.rs` drives napi build
- `src/` — the node TypeScript shell (the single source of the public contract
  for the node end); tests run against `src/` (coverage measured there). The
  browser shell, worker and standalone live in the `netwave-browser` package.
- `tsdown.config.ts` — bundles `src/index.node.ts` into `dist/` (ESM + CJS +
  dts); the napi generated glue stays external (never bundled)
- `dist/` — build output; the only published directory (`files: ["dist"]`).
  Holds this package's node artifacts plus the browser artifacts merged in from
  `netwave-browser` (shell/standalone/worker/wasm/constants/dts)
- `scripts/merge_browser.mjs` — post-tsdown step: copies the browser package's
  already-built `browser/dist/` artifacts into `dist/` so the published package
  is self-contained (copies only, never rebuilds)
- `scripts/publish_shell.mjs` — post-merge step: rewrites `"../dist/` →
  `"./` inside the node dist output so the published package is self-contained,
  emits the `index.d.ts`/`index.d.mts` hubs, and prints the dumped manifest for
  the cross-binding compare
- `test/native/` — vitest suite (node end); the config globs `test/native/**`,
  so new tests just drop in
- `vitest.native.config.ts` — the node config, with 100% coverage thresholds

## Commands

Run from this directory (or `pnpm -C typescript <script>` from the root). The
browser artifacts come from the `netwave-browser` package — build it first with
`pnpm -C browser build:browser`, then the merge step below copies them in.

```bash
pnpm install                # workspace install (root package.json pins pnpm)
pnpm build:shells         # tsdown (src/index.node.ts -> dist ESM+CJS+dts) +
                          # merge_browser.mjs + publish_shell.mjs
pnpm build:native         # release: napi esm + commonjs two passes + build:shells
pnpm build:native:debug   # same pipeline without --release (fast local iteration)
pnpm typecheck              # tsc --noEmit type gate; run AFTER build:native +
                            # browser build (the shells import dist/ glue, so the
                            # gate needs both bindings present)
pnpm test:native            # vitest native + coverage (src/ only, 100% required);
                            # HTML report in coverage/; exemptions need
                            # /* v8 ignore start/stop */ + reason comment
                            # --coverage is baked into the test script so any
                            # caller gets coverage by default; for a coverage-free
                            # quick loop pass --coverage.enabled=false explicitly
```

Lint/format run from the repo root (both crates are workspace members —
member dirs must NOT keep their own `Cargo.lock`, the root lockfile is
authoritative):

```bash
pnpm check:rs             # cargo fmt + clippy (all workspace members)
pnpm fix:rs               # auto-fix Rust formatting + clippy
pnpm check:ts             # Biome lint+format (build-free; the tsc type gate
                          # runs in CI's node job after both glues are built)
pnpm fix:ts               # Biome auto-fix
```

Cross-binding dump (node + wasm ends; run from the repo root):

```bash
node typescript/scripts/dump.mjs oracle/tmp
```
