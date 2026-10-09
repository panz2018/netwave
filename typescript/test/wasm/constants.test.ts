/** Browser constant test: SPEED_OF_LIGHT is a build-time generated plain JS
 * literal (wasm-bindgen cannot export constants — its parser rejects
 * ItemConst; ironclad rule 8 keeps the main thread off wasm), so reading it
 * costs no worker roundtrip and never inits wasm. Expected value is an
 * independent literal (SI exact, bit-exact). Runs unmodified under
 * Node (fake worker) and in a real browser via the shared harness. */
import { beforeAll, describe, expect, it } from "vitest";
import { type Harness, installResidentWorkerHarness } from "./harness.ts";

/** The f64 bytes of a value (little-endian), for bit-level comparison. */
const f64Bytes = (v: number): number[] => {
  const view = new DataView(new ArrayBuffer(8));
  view.setFloat64(0, v);
  return [...new Uint8Array(view.buffer)];
};

let harness: Harness;

beforeAll(async () => {
  harness = await installResidentWorkerHarness();
});

describe("browser SPEED_OF_LIGHT", () => {
  it("equals the SI exact value bit for bit", async () => {
    const m = await import("../../src/index.browser.ts");
    expect(m.SPEED_OF_LIGHT).toBe(299_792_458);
    expect(f64Bytes(m.SPEED_OF_LIGHT)).toEqual(f64Bytes(299_792_458));
  });

  it("reading the constant costs no worker roundtrip", async () => {
    const m = await import("../../src/index.browser.ts");
    const before = harness.shellPosts();
    void m.SPEED_OF_LIGHT;
    // A pure JS literal: reading it posts nothing to the worker (so it
    // never touches wasm — ironclad rule 8).
    expect(harness.shellPosts()).toBe(before);
  });
});
