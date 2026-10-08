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
    await m.Network.fillPattern(2, 2);
    expect(g.__netwaveWasmMemory).toBeUndefined();
    expect(g.__netwaveWorker).toBeInstanceOf(Worker);
  });

  it("compute happens in the resident worker, handle rides the reply", async () => {
    const m = await import("../../src/index.browser.ts");
    const net = await m.Network.fillPattern(2, 2);
    // The shell holds only a numeric handle; the data never crosses into
    // the main thread (readElement round-trips through the worker).
    expect(net.handle).toBeTypeOf("number");
    expect(await net.readElement(2)).toBe(1); // re(0,0,1), closed form
    // upload detaches the caller buffer (single ownership moved in).
    const src = new Float64Array([1, -1, 2, -2]);
    const uploaded = await m.Network.upload(src, 2, 1);
    expect(src.buffer.byteLength).toBe(0);
    expect(await uploaded.readElement(2)).toBe(2);
    await uploaded.drop();
    await expect(uploaded.readElement(0)).rejects.toThrow(new RegExp(String(uploaded.handle)));
  });

  it("no `_` sync escape hatch on the browser entry", async () => {
    const m = await import("../../src/index.browser.ts");
    expect(Object.keys(m).filter((k) => k.startsWith("_"))).toEqual([]);
  });
});
