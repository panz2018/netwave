/** Resident-worker contract tests (ironclad rule 8 + zero-copy-roundtrip
 * rewrite). Runs unmodified under Node (fake scopes, real structuredClone
 * transfer) and in a real browser (native Worker) via the shared harness.
 *
 * Spec scenarios covered: upload detaches the caller buffer (single
 * ownership); release invalidates the handle; result buffers transfer back;
 * metadata (shape/frequency) rides the result message (no extra roundtrip);
 * unhosted-view read boundary-copies (input NOT consumed); multiple imports
 * + handles share ONE worker (singleton). */
import { beforeAll, describe, expect, it } from "vitest";
import type { Handle } from "../../src/types.ts";
import { type Harness, installResidentWorkerHarness } from "./harness.ts";

const NFREQ = 2;
const NPORTS = 2;
const closedForm = (f: number, p: number, q: number) => {
  const re = f * 100 + p * 10 + q;
  return { re, im: -re };
};

let h: Harness;

beforeAll(async () => {
  h = await installResidentWorkerHarness();
});

const shell = () => import("../../src/index.browser.ts");

describe("resident worker contract", () => {
  it("fillPattern: result transferred back, metadata rides the same message", async () => {
    const m = await shell();
    const postsBefore = h.shellPosts();
    const postedBefore = h.posted.length;
    const r = await m.fillPattern(NFREQ, NPORTS);
    // One request out, one response back — metadata piggyback costs zero
    // extra roundtrips.
    expect(h.shellPosts()).toBe(postsBefore + 1);
    expect(h.posted.length).toBe(postedBefore + 1);
    expect(r.shape).toEqual([NFREQ, NPORTS, NPORTS]);
    expect(r.frequency).toBeInstanceOf(Float64Array);
    const view = new Float64Array(r.buffer, r.byteOffset, r.length * 2);
    for (let f = 0; f < NFREQ; f++)
      for (let p = 0; p < NPORTS; p++)
        for (let q = 0; q < NPORTS; q++) {
          const { re, im } = closedForm(f, p, q);
          const i = (f * NPORTS * NPORTS + p * NPORTS + q) * 2;
          expect(view[i]).toBe(re);
          expect(view[i + 1]).toBe(im);
        }
    // Reading piggybacked metadata costs no worker message.
    const postsAfter = h.shellPosts();
    expect(r.shape[0]).toBe(NFREQ);
    expect(h.shellPosts()).toBe(postsAfter);
  });

  it("upload: caller buffer detached (single ownership); handle reads work", async () => {
    const m = await shell();
    const src = new Float64Array([1.5, -1.5, 2.5, -2.5]);
    const handle: Handle = await m.upload(src);
    // Explicit transfer: the caller's buffer is detached after upload.
    expect(src.buffer.byteLength).toBe(0);
    expect(await m.readElement(handle, 2)).toBe(2.5);
    // Hosted data stays readable repeatedly (input hosted, not consumed).
    expect(await m.readElement(handle, 3)).toBe(-2.5);
  });

  it("release: handle invalidated, later calls reject naming the handle", async () => {
    const m = await shell();
    const handle = await m.upload(new Float64Array([7, -7]));
    await m.release(handle);
    await expect(m.readElement(handle, 0)).rejects.toThrow(new RegExp(String(handle)));
    // Double release rejects too (handle table no longer holds it).
    await expect(m.release(handle)).rejects.toThrow(new RegExp(String(handle)));
  });

  it("unhosted view readElement: boundary copy, input NOT consumed", async () => {
    const m = await shell();
    const src = new Float64Array([9.25, -9.25]);
    expect(await m.readElement(src, 1)).toBe(-9.25);
    // Input survives (no transfer list for plain views).
    expect(src.buffer.byteLength).toBe(16);
    expect(src[1]).toBe(-9.25);
  });

  it("multiple imports + multiple handles share ONE worker", async () => {
    const m1 = await shell();
    const m2 = await shell();
    const h1 = await m1.upload(new Float64Array([1, 1]));
    const h2 = await m2.upload(new Float64Array([2, 2]));
    expect(h.workerInstances()).toBe(1);
    // Handles address independently in the single worker.
    expect(await m1.readElement(h1, 0)).toBe(1);
    expect(await m2.readElement(h2, 1)).toBe(2);
  });

  it("unknown cmd replies with error", async () => {
    const m = await shell();
    await m.fillPattern(1, 1); // ensure the worker is up
    const w = h.singleton();
    if (!w) throw new Error("shell did not register the singleton worker");
    const p = new Promise<string | undefined>((resolve) => {
      h.onReply((res) => {
        if (res.id === 999_999) resolve(res.error);
      });
    });
    w.postMessage({ id: 999_999, cmd: "nope", args: [] });
    expect(await p).toContain("unknown cmd");
  });
});
