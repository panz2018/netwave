/** Real-browser-only assertions (ironclad rule 8, LL-030 recurrence
 * check). These CANNOT run under Node — they assert the browser main
 * thread has no wasm and that the resident worker is the single data
 * authority. Run via `pnpm test:browser` (vitest browser mode, Chromium). */
import { describe, expect, it } from "vitest";

describe("real browser: main thread has no wasm (LL-030)", () => {
  it("no wasm instance / glue namespace on the main thread", async () => {
    const g = globalThis as Record<string, unknown>;
    // The web-target glue namespace must not exist on the main thread.
    expect(g.netwave_wasm).toBeUndefined();
    expect(g.__netwaveWasmMemory).toBeUndefined();
    // The only wasm-adjacent global is the worker singleton handle.
    const m = await import("../../src/index.browser.ts");
    await m.fillPattern(2, 2);
    expect(g.__netwaveWasmMemory).toBeUndefined();
    expect(g.__netwaveWorker).toBeInstanceOf(Worker);
  });

  it("compute happens in the resident worker, result transferred back", async () => {
    const m = await import("../../src/index.browser.ts");
    const r = await m.fillPattern(2, 2);
    // Result buffer is a transferred ArrayBuffer owned by the main thread
    // now (it was copied out of worker linear memory and moved).
    expect(r.buffer).toBeInstanceOf(ArrayBuffer);
    const view = new Float64Array(r.buffer, r.byteOffset, r.length * 2);
    expect(view[2]).toBe(1); // re(0,0,1), closed form
    expect(r.shape).toEqual([2, 2, 2]);
    // upload detaches the caller buffer (single ownership moved in).
    const src = new Float64Array([1, -1, 2, -2]);
    const handle = await m.upload(src);
    expect(src.buffer.byteLength).toBe(0);
    expect(await m.readElement(handle, 2)).toBe(2);
    await m.release(handle);
    await expect(m.readElement(handle, 0)).rejects.toThrow(new RegExp(String(handle)));
  });

  it("no `_` sync escape hatch on the browser entry", async () => {
    const m = await import("../../src/index.browser.ts");
    expect(Object.keys(m).filter((k) => k.startsWith("_"))).toEqual([]);
  });

  it("standalone self-hosts the same resident worker", async () => {
    const s = await import("../../src/standalone.ts");
    const r = await s.fillPattern(1, 1);
    expect(r.length).toBe(1);
    // Same singleton worker as the browser shell (one per page).
    expect(globalThis.__netwaveWorker).toBeInstanceOf(Worker);
  });
});
