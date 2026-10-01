/** Standalone entry smoke (task 3.3): zero-build HTML entry self-hosts
 * the resident worker; same async contract as the browser shell; no `_`.
 * Runs under Node (fake Worker harness) and in a real browser unchanged. */
import { beforeAll, describe, expect, it } from "vitest";
import { type Harness, installResidentWorkerHarness } from "./harness.ts";

let h: Harness;

beforeAll(async () => {
  h = await installResidentWorkerHarness();
});

describe("standalone entry", () => {
  it("upload -> readElement -> release via the resident worker", async () => {
    const m = await import("../../src/standalone.ts");
    const r = await m.fillPattern(2, 2);
    expect(r.length).toBe(8);
    expect(r.shape).toEqual([2, 2, 2]);
    const view = new Float64Array(r.buffer, r.byteOffset, r.length * 2);
    expect(await m.readElement(view, 2)).toBe(1); // re(0,0,1)
    const handle = await m.upload(new Float64Array([3, -3]));
    expect(await m.readElement(handle, 0)).toBe(3);
    await m.release(handle);
    expect(h.workerInstances()).toBe(1);
  });
});
