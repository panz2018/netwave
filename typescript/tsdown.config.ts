// tsdown config: compiles the TS shells in src/ into dist/ (ESM + CJS +
// dts). The generated bindings (napi glue, wasm-pack glue) are never
// bundled — they are build artifacts of the Rust pipelines and stay
// external. publish_shell.mjs rewrites the "../dist/" glue specifiers to
// "./" after this build (it stays a specifier-rewriter, never a copier).
import { defineConfig } from "tsdown";

// Relative specifiers of the generated glue (kept external).
const glue = (id: string) =>
  id.includes("index.node.generated") || id.includes("wasm-web/netwave_wasm.js");

export default defineConfig([
  {
    // Node shell: fixed extensions (.mjs/.cjs) so the names match
    // package.json `exports` exactly.
    entry: { "index.node": "src/index.node.ts" },
    format: ["esm", "cjs"],
    platform: "node",
    fixedExtension: true,
    dts: true,
    deps: { neverBundle: glue },
    outDir: "dist",
    clean: false,
  },
  {
    // Browser shell: ESM only — the exports map has no require() target
    // for it (browser consumers are bundlers), so no .cjs twin.
    entry: { "index.browser": "src/index.browser.ts" },
    format: ["esm"],
    platform: "browser",
    fixedExtension: true,
    dts: true,
    deps: { neverBundle: glue },
    outDir: "dist",
    clean: false,
  },
  {
    // Worker + standalone: plain .js ESM (zero-build HTML entry; the
    // package is "type": "module" so .js is already ESM).
    entry: {
      "netwave.worker": "src/netwave.worker.ts",
      standalone: "src/standalone.ts",
    },
    format: ["esm"],
    platform: "browser",
    fixedExtension: false,
    // No dts here: the public types ship as index.d.ts / index.d.mts from
    // the shell config; a second dts pass would overwrite them.
    dts: false,
    // index.browser stays a separate dist module (mirrors the pre-rewrite
    // layout: worker/standalone import ./index.browser.mjs, zero duplication).
    deps: { neverBundle: (id) => glue(id) || id === "./index.browser.ts" },
    outDir: "dist",
    clean: false,
  },
]);
