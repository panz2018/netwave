import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["test/native/**/*.test.ts"],
    // Stray profraw outside target/ means the coverage chain did not take
    // effect; the hook deletes and fails at both ends of the run.
    globalSetup: ["./test/global-drain-profraw.ts"],
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
