// Real-browser test line (vitest browser mode + playwright, Chromium only
// — governance spec ironclad rule 8 scenario "主线程无 wasm" needs a REAL
// browser; node simulation cannot prove it). Same test code as the node
// wasm suite: test/wasm/** runs unmodified here; the harness detects the
// native Worker and wraps it instead of faking scopes.
import { playwright } from "@vitest/browser-playwright";
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["test/wasm/**/*.test.ts", "test/browser/**/*.test.ts"],
    browser: {
      enabled: true,
      headless: true,
      provider: playwright(),
      instances: [{ browser: "chromium" }],
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
