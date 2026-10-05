import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["test/wasm/**/*.test.ts"],
    // Memory tests force GC via globalThis.gc(); expose it on the worker
    // processes (vitest 5: top-level execArgv, poolOptions removed).
    execArgv: ["--expose-gc"],
    coverage: {
      provider: "v8",
      include: ["src/index.browser.ts", "src/netwave.worker.ts"],
      thresholds: { lines: 100, branches: 100 },
    },
  },
});
