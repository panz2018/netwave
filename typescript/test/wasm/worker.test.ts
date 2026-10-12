/** Resident-worker contract tests (ironclad rule 8 + zero-copy-roundtrip
 * rewrite). Runs unmodified under Node (fake scopes, real structuredClone
 * transfer) and in a real browser (native Worker) via the shared harness.
 *
 * Spec scenarios covered: fromData detaches the caller buffer (single
 * ownership); drop invalidates the handle; shells hold only a numeric
 * handle and every read is a worker roundtrip; multiple imports + shells
 * share ONE worker (singleton); the handle table lives in core, not JS. */
import { beforeAll, describe, expect, it } from "vitest";
// The worker source as a raw string (vite `?raw`): readable in BOTH realms
// (Node vitest and real-browser vitest), unlike node:fs which is absent in a
// browser. Used by the verb-count-zero-change sentinel below.
import workerSource from "../../src/netwave.worker.ts?raw";
import { type Harness, installResidentWorkerHarness } from "./harness.ts";

let h: Harness;

beforeAll(async () => {
  h = await installResidentWorkerHarness();
});

const shell = () => import("../../src/index.browser.ts");

/** Build a 1-port Touchstone through the worker (independent literals,
 * rule 2): S = 0.5+0.25j, z0 = 50. */
const makeTs = async () => {
  const m = await shell();
  const f = await m.Frequency.fromF(new Float64Array([1.0]), m.FrequencyUnit.GHz);
  return m.Touchstone.fromData(f, new Float64Array([0.5, 0.25]), [50.0], "S");
};

describe("resident worker contract", () => {
  it("Touchstone.fromData: shell over a core handle, reads round-trip", async () => {
    const m = await shell();
    const f = await m.Frequency.fromF(new Float64Array([1.0]), m.FrequencyUnit.GHz);
    const postsBefore = h.shellPosts();
    const ts = await m.Touchstone.fromData(f, new Float64Array([0.5, 0.25]), [50.0], "S");
    // One request out, one reply back — the handle rides the reply.
    expect(h.shellPosts()).toBe(postsBefore + 1);
    const s = await ts.s;
    expect(s[0]).toBeCloseTo(0.5, 12);
    expect(s[1]).toBeCloseTo(0.25, 12);
    // Derived Z = z0(1+s)/(1-s) = 110+80j, computed in the worker.
    const z = await ts.z;
    expect(z[0]).toBeCloseTo(110.0, 6);
    expect(z[1]).toBeCloseTo(80.0, 6);
    await ts.drop();
    void m;
  });

  it("fromData: caller buffer detached (single ownership); shell reads work", async () => {
    const m = await shell();
    const f = await m.Frequency.fromF(new Float64Array([1.0, 2.0]), m.FrequencyUnit.GHz);
    const src = new Float64Array([1.5, -1.5, 2.5, -2.5]);
    const ts = await m.Touchstone.fromData(f, src, [50.0], "S");
    // Explicit transfer: the caller's buffer is detached after the call.
    expect(src.buffer.byteLength).toBe(0);
    const s = await ts.s;
    expect(s[2]).toBe(2.5);
    // Hosted data stays readable repeatedly (input hosted, not consumed).
    const s2 = await ts.s;
    expect(s2[3]).toBe(-2.5);
    await ts.drop();
  });

  it("drop: handle invalidated, later reads reject naming the handle", async () => {
    const ts = await makeTs();
    const handle = ts.handle;
    await ts.drop();
    await expect(ts.s).rejects.toThrow(new RegExp(String(handle)));
    // Double drop is idempotent (the unified verb): no throw, no second
    // core Drop (the shell short-circuits after the first).
    await expect(ts.drop()).resolves.toBeUndefined();
  });

  it("multiple imports + multiple shells share ONE worker", async () => {
    const m1 = await shell();
    const m2 = await shell();
    const f1 = await m1.Frequency.fromF(new Float64Array([1.0]), m1.FrequencyUnit.GHz);
    const f2 = await m2.Frequency.fromF(new Float64Array([2.0]), m2.FrequencyUnit.GHz);
    const t1 = await m1.Touchstone.fromData(f1, new Float64Array([0.1, 0.1]), [50.0], "S");
    const t2 = await m2.Touchstone.fromData(f2, new Float64Array([0.2, 0.2]), [50.0], "S");
    expect(h.workerInstances()).toBe(1);
    // Handles address independently in the single core table.
    expect((await t1.s)[0]).toBeCloseTo(0.1, 12);
    expect((await t2.s)[1]).toBeCloseTo(0.2, 12);
  });

  it("unknown method / namespace replies with error", async () => {
    const m = await shell();
    await makeTs(); // ensure the worker is up
    const w = h.singleton();
    if (!w) throw new Error("shell did not register the singleton worker");
    const ask = (id: number, handle: number | string, method: string) =>
      new Promise<string | undefined>((resolve) => {
        const stop = h.onReply((res) => {
          if (res.id === id) {
            stop();
            resolve(res.error);
          }
        });
        w.postMessage({ id, handle, method, args: [] });
      });
    // Unknown method on a live instance handle (numeric half).
    expect(await ask(999_998, 1, "nope")).toContain("unknown method");
    // Unknown namespace (string half).
    expect(await ask(999_999, "circuit", "fromData")).toContain("unknown namespace");
  });

  it("加动词零改动: the worker source names no verb (fixed template)", () => {
    // Generic dispatch invariant: the worker is ONE forwarding template;
    // verb names must never appear in its source. Adding a method touches
    // only the core module's `match`.
    for (const verb of ["fromData", "fromF", "npoints", "frequencyUnits", "liveCount"]) {
      expect(workerSource).not.toContain(verb);
    }
  });
});
