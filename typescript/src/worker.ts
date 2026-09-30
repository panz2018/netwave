// netwave/worker — single command dispatcher (zero numeric logic; adding a
// function means editing the table, not adding a file). Hosted internally by
// the library's async shell; power users may also
// `new Worker(new URL("netwave/worker", …))`.
// Transfer decision table (zero-copy-roundtrip spec):
//   - normal call: input enters via structured clone (never in the transfer
//     list — input is never consumed)
//   - result: always transferred back (the result buffer is freshly
//     computed and unowned)
//   - upload: input transferred only when explicitly hosted
// Explicit static table (no dynamic property access on the namespace,
// preserves tree-shaking).
// `.ts` specifier is legal under noEmit; publish_shell.mjs rewrites it to
// "./index.browser.mjs" in the dist output.
import { fillPattern, readElement } from "./index.browser.ts";
import type { NetwaveBuffer, WorkerRequest, WorkerResponse } from "./types.js";

// Explicit static table: each wrapper pins its argument tuple, so the
// dispatcher stays free of union-call casts.
const cmds: Record<string, (args: unknown[]) => Promise<NetwaveBuffer | number>> = {
  fillPattern: (args) => fillPattern(...(args as [number, number])),
  readElement: (args) => readElement(...(args as [Float64Array, number])),
};

// The DOM lib types `self` as `Window` (postMessage requires targetOrigin);
// this module only ever runs inside a Worker, so pin the scope type.
interface WorkerScope {
  onmessage: ((ev: MessageEvent<WorkerRequest>) => Promise<void>) | null;
  postMessage(message: WorkerResponse, transfer?: ArrayBuffer[]): void;
}
const workerScope = self as unknown as WorkerScope;

workerScope.onmessage = async ({ data }: MessageEvent<WorkerRequest>) => {
  const fn = cmds[data.cmd];
  if (!fn) {
    workerScope.postMessage({
      id: data.id,
      error: `unknown cmd: ${data.cmd}`,
    } satisfies WorkerResponse);
    return;
  }
  try {
    const result = await fn(data.args);
    // Results are always transferred back. wasm results alias the
    // instance's live linear memory, which must never be transferred
    // (transferring it would detach the wasm instance), so the bytes are
    // copied into a fresh, detachable ArrayBuffer first.
    // Only buffer-bearing results reach this point; numeric results are
    // posted as-is (the copy below throws on them into the catch path,
    // matching the pre-rewrite behaviour).
    const buffer = result as NetwaveBuffer;
    const bytes = new Uint8Array(buffer.buffer, buffer.byteOffset, buffer.length * 16).slice();
    workerScope.postMessage(
      {
        id: data.id,
        result: { buffer: bytes.buffer, byteOffset: 0, length: buffer.length },
      } satisfies WorkerResponse,
      [bytes.buffer],
    );
  } catch (err) {
    workerScope.postMessage({ id: data.id, error: String(err) } satisfies WorkerResponse);
  }
};
