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
import { fillPattern, readElement } from "./index.browser.mjs";

const cmds = { fillPattern, readElement };

self.onmessage = async ({ data }) => {
  const fn = cmds[data.cmd];
  if (!fn) {
    self.postMessage({ id: data.id, error: `unknown cmd: ${data.cmd}` });
    return;
  }
  try {
    const result = await fn(...data.args);
    // Results are always transferred back. wasm results alias the
    // instance's live linear memory, which must never be transferred
    // (transferring it would detach the wasm instance), so the bytes are
    // copied into a fresh, detachable ArrayBuffer first.
    const bytes = new Uint8Array(result.buffer, result.byteOffset, result.length * 16).slice();
    self.postMessage(
      {
        id: data.id,
        result: { buffer: bytes.buffer, byteOffset: 0, length: result.length },
      },
      [bytes.buffer],
    );
  } catch (err) {
    self.postMessage({ id: data.id, error: String(err) });
  }
};
