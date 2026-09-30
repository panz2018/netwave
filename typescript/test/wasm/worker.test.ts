/** Worker dispatcher + standalone entry smoke tests (phase 0: structure +
 * passthrough). The worker holds zero numeric logic: cmds-table dispatch and
 * result transfer. `self` is simulated under Node. */
import { describe, expect, it } from "vitest";
import type { WorkerRequest, WorkerResponse } from "../../src/types.ts";

describe("worker dispatcher", () => {
  it("dispatches known cmds, reports unknown cmds, never transfers wasm memory", async () => {
    const posted: { msg: WorkerResponse; transfer: ArrayBuffer[] | undefined }[] = [];
    // Simulate the Worker global `self` under Node (the DOM lib types
    // `self` as Window; the worker module pins its own scope type).
    interface FakeScope {
      self: {
        postMessage: (msg: WorkerResponse, transfer?: ArrayBuffer[]) => void;
        onmessage: ((ev: MessageEvent<WorkerRequest>) => Promise<void>) | null;
      };
    }
    const fakeSelf: FakeScope["self"] = {
      postMessage: (msg: WorkerResponse, transfer?: ArrayBuffer[]) =>
        posted.push({ msg, transfer }),
      onmessage: null,
    };
    Object.defineProperty(globalThis, "self", {
      value: fakeSelf,
      writable: true,
      configurable: true,
    });
    await import("../../src/worker.ts");
    const onmessage = fakeSelf.onmessage;
    if (!onmessage) throw new Error("worker did not register onmessage");
    const ev = (data: WorkerRequest) => ({ data }) as unknown as MessageEvent<WorkerRequest>;
    await onmessage(ev({ id: 1, cmd: "fillPattern", args: [2, 2] }));
    expect(posted[0].msg.id).toBe(1);
    const result = posted[0].msg.result;
    if (!result) throw new Error(`expected a result, got: ${posted[0].msg.error}`);
    expect(result.length).toBe(8);
    // Results are always transferred back (the worker copies wasm linear
    // memory into a fresh detachable ArrayBuffer).
    expect(posted[0].transfer).toEqual([result.buffer]);
    const view = new Float64Array(result.buffer, 0, 16);
    expect(view[0]).toBe(0); // re(0,0,0)
    expect(view[1]).toBe(-0); // im(0,0,0) = -0 (sign preserved)
    expect(view[2]).toBe(1); // re(0,0,1)

    await onmessage(ev({ id: 2, cmd: "nope", args: [] }));
    expect(posted[1].msg.error).toContain("unknown cmd");

    // Compute errors take the catch path: error string returned.
    await onmessage(ev({ id: 3, cmd: "readElement", args: [null, 0] }));
    expect(posted[2].msg.id).toBe(3);
    expect(posted[2].msg.error).toBeTruthy();
  });
});

describe("standalone entry", () => {
  it("re-exports the same async contract as the browser shell", async () => {
    const m = await import("../../src/standalone.ts");
    const r = await m.fillPattern(2, 2);
    expect(r.length).toBe(8);
    expect(await m.readElement(new Float64Array(r.buffer, r.byteOffset, 16), 0)).toBe(0);
  });
});
