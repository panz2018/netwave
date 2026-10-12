/** Real-browser-only assertions: the browser main thread never runs wasm
 * and the resident worker is the single data authority. These CANNOT run
 * under Node. Run via `pnpm test:browser` (vitest browser mode, Chromium). */
import { describe, expect, it } from "vitest";

describe("real browser: main thread has no wasm (LL-030)", () => {
  it("no wasm instance / glue namespace on the main thread", async () => {
    const g = globalThis as Record<string, unknown>;
    // The web-target glue namespace must not exist on the main thread.
    expect(g.netwave_wasm).toBeUndefined();
    expect(g.__netwaveWasmMemory).toBeUndefined();
    // The only wasm-adjacent global is the worker singleton handle.
    const m = await import("../../src/index.browser.ts");
    const f = await m.Frequency.fromF(new Float64Array([1.0]), m.FrequencyUnit.GHz);
    await m.Touchstone.fromData(f, new Float64Array([0.5, 0.25]), [50.0], "S");
    expect(g.__netwaveWasmMemory).toBeUndefined();
    expect(g.__netwaveWorker).toBeInstanceOf(Worker);
  });

  it("compute happens in the resident worker, handle rides the reply", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await m.Frequency.fromF(new Float64Array([1.0]), m.FrequencyUnit.GHz);
    // 1-port S = 0.5+0.25j, z0 = 50 (independent literals, rule 2).
    const data = new Float64Array([0.5, 0.25]);
    const ts = await m.Touchstone.fromData(f, data, [50.0], "S");
    // The shell holds only a numeric handle; the data never crosses into
    // the main thread (every read round-trips through the worker).
    expect(ts.handle).toBeTypeOf("number");
    // The data buffer is MOVED via transfer (single ownership, rule 8):
    // afterwards the caller's buffer is detached.
    expect(data.buffer.byteLength).toBe(0);
    const s = await ts.s;
    expect(s[0]).toBeCloseTo(0.5, 12);
    // Hosted data stays readable repeatedly (input hosted, not consumed).
    const s2 = await ts.s;
    expect(s2[1]).toBeCloseTo(0.25, 12);
    await ts.drop();
    await expect(ts.s).rejects.toThrow(new RegExp(String(ts.handle)));
  });

  it("no `_` sync escape hatch on the browser entry", async () => {
    const m = await import("../../src/index.browser.ts");
    expect(Object.keys(m).filter((k) => k.startsWith("_"))).toEqual([]);
  });

  it("Touchstone.fromData moves data in and hosts it in the worker", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await m.Frequency.fromF(new Float64Array([1.0]), m.FrequencyUnit.GHz);
    // 1-port S = 0.5+0.25j, z0 = 50 (independent literals, rule 2).
    const data = new Float64Array([0.5, 0.25]);
    const ts = await m.Touchstone.fromData(f, data, new Float64Array([50.0]), "S");
    expect(ts).toBeInstanceOf(m.Touchstone);
    // The data buffer is MOVED via transfer (single ownership, rule 8):
    // afterwards the caller's buffer is detached.
    expect(data.buffer.byteLength).toBe(0);
    // The hosted data reads back correct (cloned from the worker).
    const s = await ts.s;
    expect(s[0]).toBeCloseTo(0.5, 12);
    expect(s[1]).toBeCloseTo(0.25, 12);
    // Derived Z = z0(1+s)/(1-s) = 110+80j, computed in the worker.
    const z = await ts.z;
    expect(z[0]).toBeCloseTo(110.0, 6);
    expect(z[1]).toBeCloseTo(80.0, 6);
    await ts.drop();
  });
});
