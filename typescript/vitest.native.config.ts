import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["test/native/**/*.test.ts"],
    coverage: {
      provider: "v8",
      include: ["src/index.node.ts"],
      thresholds: { lines: 100, branches: 100 },
    },
  },
});
