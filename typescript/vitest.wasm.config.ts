import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["test/wasm/**/*.test.ts"],
    coverage: {
      provider: "v8",
      include: ["src/index.browser.ts", "src/netwave.worker.ts"],
      thresholds: { lines: 100, branches: 100 },
    },
  },
});
