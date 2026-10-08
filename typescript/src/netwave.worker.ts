// netwave/worker — the resident worker: the single wasm instance and the
// single data authority (governance spec ironclad rule 8). wasm is inited
// HERE, never on the main thread. The handle table lives in core Rust
// (cfg=browser, type-erased): worker JS keeps ZERO state and every message
// is a mechanical forward of `{handle, method, args}` to the single core
// entry `call` (api-contract spec "worker generic dispatch and
// single-resident topology"). `handle` is a number (an instance in the core
// table) or a string (a core module namespace); `drop` removes the entry and
// runs the resource's Rust `Drop` — no wasm object ever floats up to JS.
// This template is verb-count-independent: adding a method — or a whole
// resource type — changes nothing here.

import wasmInit, { call as _wasmCall } from "../dist/wasm-web/netwave_wasm.js";
import type { WorkerRequest, WorkerResponse } from "./types.ts";

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

// The DOM lib types `self` as `Window` (postMessage requires targetOrigin);
// this module only ever runs inside a Worker, so pin the scope type.
interface WorkerScope {
  onmessage: ((ev: MessageEvent<WorkerRequest>) => Promise<void>) | null;
  postMessage(message: WorkerResponse, transfer?: ArrayBuffer[]): void;
}
const workerScope = self as unknown as WorkerScope;

// The fixed template: await wasm ready, forward `{handle, method, args}`
// verbatim to core `call`, relay the result or the error. No tables, no
// maps, no counters — core's handle table is the single data authority.
workerScope.onmessage = async ({ data }: MessageEvent<WorkerRequest>) => {
  await ready;
  try {
    const result = _wasmCall(data.handle, data.method, data.args);
    workerScope.postMessage({ id: data.id, result });
  } catch (err) {
    workerScope.postMessage({ id: data.id, error: String(err) });
  }
};
