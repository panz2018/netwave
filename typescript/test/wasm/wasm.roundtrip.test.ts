/** wasm binding roundtrip test (RED first: missing wasm artifact → red).
 * View = new Float64Array(memory.buffer, offset, len). The web-target glue
 * needs async init; the `_` sync escape hatch is used only after the first
 * awaited call has completed init. */
import { describe, expect, it } from "vitest";
import { _fillPattern, _readElement, fillPattern, readElement } from "../../src/index.browser.ts";

const NFREQ = 2;
const NPORTS = 2;
const closedForm = (f: number, p: number, q: number) => {
  const re = f * 100 + p * 10 + q;
  return { re, im: -re };
};

describe("wasm roundtrip", () => {
  it("public async surface: linear-memory view + pattern + write-back", async () => {
    const { buffer, byteOffset, length } = await fillPattern(NFREQ, NPORTS);
    const view = new Float64Array(buffer, byteOffset, length * 2);
    for (let f = 0; f < NFREQ; f++)
      for (let p = 0; p < NPORTS; p++)
        for (let q = 0; q < NPORTS; q++) {
          const { re, im } = closedForm(f, p, q);
          const i = (f * NPORTS * NPORTS + p * NPORTS + q) * 2;
          expect(view[i]).toBe(re);
          expect(view[i + 1]).toBe(im);
        }
    view[4] = -7.25;
    expect(await readElement(view, 4)).toBe(-7.25);
  });

  it("_ escape hatch sync passthrough (after init)", async () => {
    await fillPattern(1, 1); // ensure init completed
    const s = _fillPattern(NFREQ, NPORTS);
    const view = new Float64Array(s.buffer, s.byteOffset, s.length * 2);
    expect(_readElement(view, 0)).toBe(0);
  });
});
