// netwave/worker — the resident worker: the single wasm instance and the
// single data authority (governance spec ironclad rule 8). wasm is inited
// HERE, never on the main thread. Hosted data lives in a handle table
// (handle -> Float64Array); handles are monotonically increasing and are
// invalidated by `release`. Zero numeric logic: cmds-table dispatch into
// the wasm glue; adding a core verb means editing the table only.
//
// Transfer decision table (zero-copy-roundtrip spec):
//   - upload: the caller's buffer arrives via the shell's transfer list
//     (single ownership moved in; the main-thread view is detached there)
//   - unhosted readElement: plain view, structured-cloned in (copied, NOT
//     consumed)
//   - results: buffer-bearing results are copied out of wasm linear memory
//     into a fresh ArrayBuffer and transferred back (linear memory itself
//     must never be transferred — that would detach the wasm instance);
//     metadata (shape/frequency) rides the same reply message.
// Explicit static table (no dynamic property access on the namespace,
// preserves tree-shaking). `.ts` specifier is legal under noEmit;
// publish_shell.mjs rewrites glue specifiers in the dist output.
import wasmInit, {
  fill_pattern as _wasmFill,
  read_element as _wasmRead,
} from "../dist/wasm-web/netwave_wasm.js";
import type { Handle, NetwaveBuffer, WorkerRequest, WorkerResponse } from "./types.ts";

// wasm init: the web-target glue fetches the .wasm relative to its own
// URL in browsers; under Node (vitest) fetch has no file: support, so read
// the bytes with node:fs. The node: import is dynamic and browser-invisible.
/* v8 ignore next 1 -- environment probe; Node-only in this test suite */
const isNode = typeof process !== "undefined" && !!process.versions.node;
const wasmSource = async (): Promise<Uint8Array | undefined> => {
  /* v8 ignore start -- browser-only path; exercised in real-browser tests */
  if (!isNode) return undefined; // glue default: fetch relative to its own URL
  /* v8 ignore stop */
  const { readFile } = await import("node:fs/promises");
  const { fileURLToPath } = await import("node:url");
  return readFile(fileURLToPath(new URL("../dist/wasm-web/netwave_wasm_bg.wasm", import.meta.url)));
};

const ready = (async () => wasmInit({ module_or_path: await wasmSource() }))();

// Handle table: the worker is the single data authority (ironclad rule 8).
const hosted = new Map<Handle, Float64Array>();
let nextHandle: Handle = 1;

// `frequency` stays empty until the real data model (phase 2) populates it;
// it still rides every reply so the piggyback contract holds from day one.
const emptyFreq = (): Float64Array => new Float64Array(0);

const cmds: Record<string, (args: unknown[]) => Promise<NetwaveBuffer | number | Handle>> = {
  fillPattern: async (args) => {
    const [nfreq, nports] = args as [number, number];
    await ready;
    const d = _wasmFill(nfreq, nports) as unknown as {
      buffer: ArrayBuffer;
      byteOffset: number;
      length: number;
    };
    return {
      // Copy out of live linear memory into a fresh detachable buffer.
      buffer: new Uint8Array(d.buffer, d.byteOffset, d.length * 16).slice().buffer,
      byteOffset: 0,
      length: d.length,
      shape: [nfreq, nports, nports],
      frequency: emptyFreq(),
    };
  },
  upload: async (args) => {
    await ready;
    const handle = nextHandle++;
    hosted.set(handle, args[0] as Float64Array);
    return handle;
  },
  release: async (args) => {
    await ready;
    const handle = args[0] as Handle;
    if (!hosted.delete(handle)) {
      throw new Error(`unknown or released handle: ${handle}`);
    }
    return 0;
  },
  readElement: async (args) => {
    await ready;
    const [target, idx] = args as [Handle | Float64Array, number];
    if (typeof target === "number") {
      const view = hosted.get(target);
      if (!view) throw new Error(`unknown or released handle: ${target}`);
      return _wasmRead(view, idx);
    }
    return _wasmRead(target, idx);
  },
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
    workerScope.postMessage({ id: data.id, error: `unknown cmd: ${data.cmd}` });
    return;
  }
  try {
    const result = await fn(data.args);
    if (typeof result === "object" && result !== null) {
      // Buffer-bearing: transfer the result buffer back (zero-copy).
      workerScope.postMessage({ id: data.id, result }, [(result as NetwaveBuffer).buffer]);
    } else {
      workerScope.postMessage({ id: data.id, result });
    }
  } catch (err) {
    workerScope.postMessage({ id: data.id, error: String(err) });
  }
};
