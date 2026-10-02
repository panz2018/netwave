/** Browser entry roundtrip smoke: the shell self-hosts the resident
 * worker; same async contract behind the public `./standalone` dist
 * artifact. Runs under Node (fake Worker harness) unchanged. */
import { beforeAll, describe, expect, it } from "vitest";
import { type Harness, installResidentWorkerHarness } from "./harness.ts";

let h: Harness;

beforeAll(async () => {
  h = await installResidentWorkerHarness();
});

describe("browser entry", () => {
  it("upload -> readElement -> release via the resident worker", async () => {
    const m = await import("../../src/index.browser.ts");
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
