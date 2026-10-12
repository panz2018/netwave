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
  it("fromData -> s -> z -> drop via the resident worker", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await m.Frequency.fromF(new Float64Array([1.0]), m.FrequencyUnit.GHz);
    // 1-port S = 0.5+0.25j, z0 = 50 (independent literals, rule 2).
    const data = new Float64Array([0.5, 0.25]);
    const ts = await m.Touchstone.fromData(f, data, [50.0], "S");
    expect(data.buffer.byteLength).toBe(0); // transfer: buffer detached
    const s = await ts.s;
    expect(s[0]).toBeCloseTo(0.5, 12);
    // Derived Z = z0(1+s)/(1-s) = 110+80j, computed in the worker.
    const z = await ts.z;
    expect(z[0]).toBeCloseTo(110.0, 6);
    expect(z[1]).toBeCloseTo(80.0, 6);
    await ts.drop();
    expect(h.workerInstances()).toBe(1);
  });
});
