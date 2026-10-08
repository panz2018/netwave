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
  it("upload -> readElement -> drop via the resident worker", async () => {
    const m = await import("../../src/index.browser.ts");
    const net = await m.Network.fillPattern(2, 2);
    expect(await net.readElement(2)).toBe(1); // re(0,0,1)
    const uploaded = await m.Network.upload(new Float64Array([3, -3]), 1, 1);
    expect(await uploaded.readElement(0)).toBe(3);
    await uploaded.drop();
    expect(h.workerInstances()).toBe(1);
  });
});
