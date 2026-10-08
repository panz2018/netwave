/** Node binding roundtrip test (RED first: missing napi artifact / shell
 * throws → red). Single async surface: compute verbs awaited; `_`-prefixed
 * sync escape hatch compared against. Node keeps `_` (in-process napi
 * core). Data entry is the `Network` constructor (no `upload` — node has no
 * worker boundary, the constructor copies bytes and the caller's buffer
 * survives); reclamation is the instance method `drop()`. */
import { describe, expect, it } from "vitest";
import { _fillPattern, _readElement, fillPattern, Network } from "../../src/index.node.ts";

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
    expect(_readElement(view, 2)).toBe(3.5);
  });

  it("_ escape hatch sync passthrough matches the async surface", () => {
    const sync = _fillPattern(NFREQ, NPORTS);
    const view = new Float64Array(sync.buffer, sync.byteOffset, sync.length * 2);
    expect(view[0]).toBe(0); // re(0,0,0)=0
    expect(_readElement(view, 0)).toBe(0);
  });

  it("Network constructor copies (no detach on node); instance reads; drop invalidates", async () => {
    const src = new Float64Array([1.5, -1.5, 2.5, -2.5]);
    const net = new Network(src, 2, 1); // shape 2×1×1×2 = 4 f64
    // Node has no worker boundary: the constructor copies, caller buffer survives.
    expect(src.buffer.byteLength).toBe(32);
    expect(net.readElement(2)).toBe(2.5);
    expect(net.readElement(3)).toBe(-2.5);
    net.drop();
    expect(() => net.readElement(0)).toThrow(/dropped/);
    net.drop(); // double drop: idempotent, no throw
  });

  it("CJS twin shell exposes the same contract", async () => {
    const { createRequire } = await import("node:module");
    const require = createRequire(import.meta.url);
    // The CJS twin is a tsdown build artifact (dist/), not a source file.
    const cjs = require("../../dist/index.node.cjs");
    const r = await cjs.fillPattern(NFREQ, NPORTS);
    expect(r.length).toBe(NFREQ * NPORTS * NPORTS);
    expect(cjs._readElement(new Float64Array(r.buffer, 0, r.length * 2), 2)).toBe(1); // re(0,0,1)
    expect(cjs._fillPattern(NFREQ, NPORTS).length).toBe(8);
    expect(cjs._readElement(new Float64Array(1), 0)).toBe(0);
    // The Network class rides the CJS twin too (constructor = data entry).
    const net = new cjs.Network(new Float64Array([1.5, -1.5, 2.5, -2.5]), 2, 1);
    expect(net.readElement(2)).toBe(2.5);
    net.drop();
  });
});
