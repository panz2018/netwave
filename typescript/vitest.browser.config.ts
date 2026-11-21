// Real-browser test line (vitest browser mode + playwright, Chromium only
// — governance spec ironclad rule 8 scenario "no wasm on the main thread"
// needs a REAL browser; node simulation cannot prove it). Same test code as the node
// wasm suite: test/wasm/** runs unmodified here; the harness detects the
// native Worker and wraps it instead of faking scopes.
//
// Under the rust coverage chain (NETWAVE_WASM_DIR + NETWAVE_COV_OUT set) this
// line ALSO measures core's browser-gated rust code: the worker is pointed at
// the instrumented glue via a resolve alias, and an afterAll hook drains its
// profraw back to node through a browser command (only the worker realm can
// read wasm memory). Unset (production browser run) keeps a plain TS-only v8
// coverage line.

import { writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { playwright } from "@vitest/browser-playwright";
import { defineConfig } from "vitest/config";

// The chain is active only when the driver points the worker at an
// instrumented build AND names where profraw lands. Both must be set.
const covDir = process.env.NETWAVE_WASM_DIR;
const covOut = process.env.NETWAVE_COV_OUT;
const chainOn = Boolean(covDir && covOut);

export default defineConfig({
  // Point the worker's static glue import at the instrumented build. The
  // worker imports "../dist/wasm-web/netwave_wasm.js" literally (vite
  // resolves it statically); aliasing that specifier to the instrumented glue
  // makes the worker load instrumented wasm in the browser too. The glue
  // fetches its own .wasm relative to its URL, so the alias also redirects
  // the binary — no worker source change needed.
  resolve: chainOn
    ? {
        alias: {
          "../dist/wasm-web/netwave_wasm.js": resolve(__dirname, covDir!, "netwave_wasm.js"),
        },
      }
    : undefined,
  test: {
    include: ["test/wasm/**/*.test.ts", "test/browser/**/*.test.ts"],
    ...(chainOn ? { setupFiles: ["./test/browser/coverage-dump.ts"] } : {}),
    browser: {
      enabled: true,
      headless: true,
      // Chromium exposes window.gc() via the V8 flag wrapped in --js-flags
      // (node's bare --expose-gc is not a chromium switch).
      provider: playwright({ launchOptions: { args: ["--js-flags=--expose-gc"] } }),
      instances: [{ browser: "chromium" }],
      // Coverage-chain only: receive the base64 profraw from the browser and
      // write it to node's disk for `llvm-profdata merge`. Named by the minicov
      // module signature so concurrent worker loads never overwrite one another.
      ...(chainOn
        ? {
            commands: {
              writeProfraw: async (_ctx, b64: string, signature: string) => {
                const bytes = Buffer.from(b64, "base64");
                await writeFile(resolve(covOut!, `browser-${signature}.profraw`), bytes);
                return bytes.length;
              },
            },
          }
        : {}),
    },
    coverage: {
      provider: "v8",
      reporter: ["text", "json-summary"],
      reportsDirectory: "./coverage/browser",
      // netwave.worker.ts runs in the worker context, which v8 browser
      // coverage does not instrument; its logic is covered to 100% by the
      // node wasm suite (the harness imports the worker module directly).
      include: ["src/index.browser.ts"],
      thresholds: { lines: 100, functions: 100, branches: 100, statements: 100 },
    },
  },
});
