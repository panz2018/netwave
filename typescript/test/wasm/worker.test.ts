/** Resident-worker contract tests (ironclad rule 8 + zero-copy-roundtrip
 * rewrite). Runs unmodified under Node (fake scopes, real structuredClone
 * transfer) and in a real browser (native Worker) via the shared harness.
 *
 * Spec scenarios covered: upload detaches the caller buffer (single
 * ownership); drop invalidates the handle; shells hold only a numeric
 * handle and every read is a worker roundtrip; multiple imports + shells
 * share ONE worker (singleton); the handle table lives in core, not JS. */
import { beforeAll, describe, expect, it } from "vitest";
// The worker source as a raw string (vite `?raw`): readable in BOTH realms
// (Node vitest and real-browser vitest), unlike node:fs which is absent in a
// browser. Used by the verb-count-zero-change sentinel below.
import workerSource from "../../src/netwave.worker.ts?raw";
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
  it("Network.fillPattern: shell over a core handle, reads round-trip", async () => {
    const m = await shell();
    const postsBefore = h.shellPosts();
    const net = await m.Network.fillPattern(NFREQ, NPORTS);
    // One request out, one reply back — the handle rides the reply.
    expect(h.shellPosts()).toBe(postsBefore + 1);
    for (let f = 0; f < NFREQ; f++)
      for (let p = 0; p < NPORTS; p++)
        for (let q = 0; q < NPORTS; q++) {
          const { re, im } = closedForm(f, p, q);
          const i = (f * NPORTS * NPORTS + p * NPORTS + q) * 2;
          expect(await net.readElement(i)).toBe(re);
          expect(await net.readElement(i + 1)).toBe(im);
        }
  });

  it("upload: caller buffer detached (single ownership); shell reads work", async () => {
    const m = await shell();
    const src = new Float64Array([1.5, -1.5, 2.5, -2.5]);
    const net = await m.Network.upload(src, 2, 1); // shape 2×1×1×2 = 4 f64
    // Explicit transfer: the caller's buffer is detached after upload.
    expect(src.buffer.byteLength).toBe(0);
    expect(await net.readElement(2)).toBe(2.5);
    // Hosted data stays readable repeatedly (input hosted, not consumed).
    expect(await net.readElement(3)).toBe(-2.5);
  });

  it("drop: handle invalidated, later reads reject naming the handle", async () => {
    const m = await shell();
    const net = await m.Network.upload(new Float64Array([7, -7]), 1, 1);
    const handle = net.handle;
    await net.drop();
    await expect(net.readElement(0)).rejects.toThrow(new RegExp(String(handle)));
    // Double drop is idempotent (the unified verb): no throw, no second
    // core Drop (the shell short-circuits after the first).
    await expect(net.drop()).resolves.toBeUndefined();
  });

  it("multiple imports + multiple shells share ONE worker", async () => {
    const m1 = await shell();
    const m2 = await shell();
    const n1 = await m1.Network.upload(new Float64Array([1, 1]), 1, 1);
    const n2 = await m2.Network.upload(new Float64Array([2, 2]), 1, 1);
    expect(h.workerInstances()).toBe(1);
    // Handles address independently in the single core table.
    expect(await n1.readElement(0)).toBe(1);
    expect(await n2.readElement(1)).toBe(2);
  });

  it("unknown method / namespace replies with error", async () => {
    const m = await shell();
    await m.Network.fillPattern(1, 1); // ensure the worker is up
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
    expect(await ask(999_999, "circuit", "upload")).toContain("unknown namespace");
  });

  it("加动词零改动: the worker source names no verb (fixed template)", () => {
    // Generic dispatch invariant: the worker is ONE forwarding template;
    // verb names must never appear in its source. Adding a method touches
    // only the core module's `match`.
    for (const verb of [
      "upload",
      "fillPattern",
      "readElement",
      "fromF",
      "npoints",
      "frequencyUnits",
      "liveCount",
    ]) {
      expect(workerSource).not.toContain(verb);
    }
  });
});
