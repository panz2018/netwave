/** Node binding roundtrip test (RED first: missing napi artifact / shell
 * throws → red). Single async surface: public verbs awaited; `_`-prefixed
 * sync escape hatch compared against. Node keeps `_` (in-process napi
 * core); upload copies bytes (no detach — there is no worker boundary). */
import { describe, expect, it } from "vitest";
import {
  _fillPattern,
  _readElement,
  fillPattern,
  readElement,
  release,
  upload,
} from "../../src/index.node.ts";

const NFREQ = 2;
const NPORTS = 2;
const closedForm = (f: number, p: number, q: number) => {
  const re = f * 100 + p * 10 + q;
  return { re, im: -re };
};

describe("native roundtrip", () => {
  it("public async surface: view + pattern + write-back", async () => {
    const { buffer, byteOffset, length } = await fillPattern(NFREQ, NPORTS);
    expect(length).toBe(NFREQ * NPORTS * NPORTS);
    const view = new Float64Array(buffer, byteOffset, length * 2);
    for (let f = 0; f < NFREQ; f++)
      for (let p = 0; p < NPORTS; p++)
        for (let q = 0; q < NPORTS; q++) {
          const { re, im } = closedForm(f, p, q);
          const i = (f * NPORTS * NPORTS + p * NPORTS + q) * 2;
          expect(view[i]).toBe(re);
          expect(view[i + 1]).toBe(im);
        }
    view[2] = 3.5; // re of f=0,p=0,q=1
    expect(await readElement(view, 2)).toBe(3.5);
  });

  it("_ escape hatch sync passthrough matches the async surface", () => {
    const sync = _fillPattern(NFREQ, NPORTS);
    const view = new Float64Array(sync.buffer, sync.byteOffset, sync.length * 2);
    expect(view[0]).toBe(0); // re(0,0,0)=0
    expect(_readElement(view, 0)).toBe(0);
  });

  it("upload copies (no detach on node); handle reads; release invalidates", async () => {
    const src = new Float64Array([1.5, -1.5, 2.5, -2.5]);
    const handle = await upload(src);
    // Node has no worker boundary: upload copies, caller buffer survives.
    expect(src.buffer.byteLength).toBe(32);
    expect(await readElement(handle, 2)).toBe(2.5);
    expect(await readElement(handle, 3)).toBe(-2.5);
    await release(handle);
    await expect(readElement(handle, 0)).rejects.toThrow(new RegExp(String(handle)));
    // Double release rejects too: the handle table has already dropped it.
    await expect(release(handle)).rejects.toThrow(new RegExp(String(handle)));
  });

  it("CJS twin shell exposes the same contract", async () => {
    const { createRequire } = await import("node:module");
    const require = createRequire(import.meta.url);
    // The CJS twin is a tsdown build artifact (dist/), not a source file.
    const cjs = require("../../dist/index.node.cjs");
    const r = await cjs.fillPattern(NFREQ, NPORTS);
    expect(r.length).toBe(NFREQ * NPORTS * NPORTS);
    expect(await cjs.readElement(new Float64Array(r.buffer, 0, r.length * 2), 2)).toBe(1); // re(0,0,1)
    expect(cjs._fillPattern(NFREQ, NPORTS).length).toBe(8);
    expect(cjs._readElement(new Float64Array(1), 0)).toBe(0);
  });
});
