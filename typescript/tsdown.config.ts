// tsdown config: compiles the node shell in src/ into dist/ (ESM + CJS +
// dts). The generated napi glue is never bundled — it is a build artifact of
// the Rust pipeline and stays external. The browser shell, worker, standalone
// and wasm assets are NOT built here: the netwave-browser package produces them
// and merge_browser.mjs copies them into dist/ at build time. publish_shell.mjs
// rewrites the "../dist/" glue specifiers to "./" after this build (it stays a
// specifier-rewriter, never a copier).
import { defineConfig } from "tsdown";

// Relative specifiers of the generated napi glue (kept external).
const glue = (id: string) => id.includes("index.node.generated");

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
]);
