import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["test/wasm/**/*.test.ts"],
    coverage: {
      provider: "v8",
      include: ["src/index.browser.mjs", "src/netwave.worker.js", "src/standalone.js"],
      thresholds: { lines: 100, branches: 100 },
    },
  },
});
