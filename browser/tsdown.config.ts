// tsdown config: compiles the browser shells in src/ into dist/ (ESM + dts).
// The generated wasm-pack glue and constants are never bundled — they are
// build artifacts of the Rust pipeline and stay external. publish_shell.mjs
// rewrites the "../dist/" glue specifiers to "./" after this build.
import { defineConfig } from "tsdown";

// Relative specifiers of the generated glue (kept external).
const glue = (id: string) =>
  id.includes("constants.generated") || id.includes("wasm/netwave_browser.js");

export default defineConfig([
  {
    // Browser shell: ESM only — the exports map has no require() target for
    // it (browser consumers are bundlers), so no .cjs twin.
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
    // Worker + standalone: plain .js ESM (zero-build HTML entry; the package
    // is "type": "module" so .js is already ESM). `standalone.js` is the
    // browser shell compiled to a second name — the public `./standalone`
    // subpath is a dist artifact path, not a source file.
    entry: {
      "netwave.worker": "src/netwave.worker.ts",
      standalone: "src/index.browser.ts",
    },
    format: ["esm"],
    platform: "browser",
    fixedExtension: false,
    // No dts here: the public types ship as index.d.ts from the shell config;
    // a second dts pass would overwrite them.
    dts: false,
    // Compile-time flag: fill `false` so dce-only + tree-shaking strip the
    // coverage-chain scaffolding (control branches, the NETWAVE_WASM_DIR probe,
    // the globalThis instance slot, and the side-effect-free coverage-dump
    // module) from the published worker. tsdown does not share `define` across
    // array config blocks, so it lives on this worker block.
    define: { __NETWAVE_COVERAGE__: "false" },
    // index.browser stays a separate dist module (worker/standalone import
    // ./index.browser.mjs, zero duplication).
    deps: { neverBundle: (id: string) => glue(id) || id === "./index.browser.ts" },
    outDir: "dist",
    clean: false,
  },
]);
