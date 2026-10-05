import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["test/native/**/*.test.ts"],
    // Memory tests force GC via globalThis.gc(); expose it on the worker
    // processes (vitest 5: top-level execArgv, poolOptions removed).
    execArgv: ["--expose-gc"],
    coverage: {
      provider: "v8",
      include: ["src/index.node.ts"],
      thresholds: { lines: 100, branches: 100 },
    },
  },
});
