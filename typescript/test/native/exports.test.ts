/** exports structure smoke test (task 1.5 acceptance + no-`export *`). */
import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const pkg = JSON.parse(readFileSync(new URL("../../package.json", import.meta.url), "utf8"));

describe("exports conditional dispatch", () => {
  it("node condition resolves to the napi shells (ESM + CJS)", () => {
    expect(pkg.exports["."].node.import).toBe("./dist/index.node.mjs");
    expect(pkg.exports["."].node.require).toBe("./dist/index.node.cjs");
  });

  it("browser/default point to the wasm shell", () => {
    expect(pkg.exports["."].browser).toBe("./dist/index.browser.mjs");
    expect(pkg.exports["."].default).toBe("./dist/index.browser.mjs");
  });

  it("includes standalone and worker subpaths", () => {
    expect(pkg.exports["./standalone"]).toBe("./dist/standalone.js");
    expect(pkg.exports["./worker"]).toBe("./dist/netwave.worker.js");
  });

  it("every exports target and the tsdown artifact manifest exist", () => {
    // tsdown emits both dts extensions; the shell names are fixed by
    // `fixedExtension` and must match exports exactly.
    const artifacts = [
      "index.node.mjs",
      "index.node.cjs",
      "index.browser.mjs",
      "standalone.js",
      "netwave.worker.js",
      "index.d.ts",
      "index.d.mts",
    ];
    for (const name of artifacts) {
      expect(existsSync(new URL(`../../dist/${name}`, import.meta.url)), name).toBe(true);
    }
    const targets = [
      pkg.exports["."].types,
      pkg.exports["."].node.import,
      pkg.exports["."].node.require,
      pkg.exports["."].browser,
      pkg.exports["."].default,
      pkg.exports["./standalone"],
      pkg.exports["./worker"],
    ];
    for (const target of targets) {
      expect(existsSync(new URL(`../../${target}`, import.meta.url)), target).toBe(true);
    }
  });

  it("engines node>=22, no UMD", () => {
    expect(pkg.engines.node).toBe(">=22");
    // Platform split packages (netwave-{os}-{arch}) are created at publish
    // time; the scaffold ships the .node addon inside dist/ and must NOT
    // list them as optionalDependencies — unpublished names break CI's
    // frozen-lockfile install.
    expect(pkg.optionalDependencies).toBeUndefined();
    expect(JSON.stringify(pkg)).not.toContain("umd");
  });
});

describe("tree-shaking: entries forbid export *", () => {
  const entries = ["index.node.ts", "index.browser.ts", "netwave.worker.ts"];
  for (const name of entries) {
    it(`${name} has no export *`, () => {
      const src = readFileSync(new URL(`../../src/${name}`, import.meta.url), "utf8");
      // Strip line comments before matching so prose like "no export *"
      // does not trigger a false positive.
      const code = src.replace(/\/\/.*$/gm, "");
      expect(code).not.toMatch(/export\s*\*/);
    });
  }
});

describe("node environment resolves to the napi shell", () => {
  it("the node-condition shell exists in the source tree (runtime check in native.roundtrip)", () => {
    const shell = fileURLToPath(new URL("../../src/index.node.ts", import.meta.url));
    expect(readFileSync(shell, "utf8")).toContain("export async function fillPattern");
  });
});
