import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["test/unit/**/*.test.ts"],
    // Drains the worker's rust coverage counters in the same worker context
    // (afterAll). No-op unless NETWAVE_WASM_DIR is set, so the TS-only v8
    // coverage path and production runs are unaffected.
    setupFiles: ["./test/unit/coverage-dump.ts"],
    // Memory tests force GC via globalThis.gc(); expose it on the worker
    // processes (vitest 5: top-level execArgv, poolOptions removed).
    execArgv: ["--expose-gc"],
    coverage: {
      provider: "v8",
      include: ["src/index.browser.ts", "src/netwave.worker.ts"],
      thresholds: { lines: 100, branches: 100, functions: 100 },
    },
  },
});
