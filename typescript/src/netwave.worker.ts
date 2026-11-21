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

import { dumpCoverage } from "./coverage-dump.ts";
import type { ControlRequest, WorkerRequest, WorkerResponse } from "./types.ts";

// The wasm glue + bytes live in dist/wasm-web by default. Under Node the rust
// coverage chain points them at an instrumented build via NETWAVE_WASM_DIR;
// unset (production + every browser path) keeps the default. The default
// specifiers MUST stay literal string constants: publish_shell.mjs rewrites
// the "../dist/" prefix to "./" for the published browser worker, and vite
// (browser mode) resolves them statically. The instrumented branch is a
// template literal (unresolvable at build time) so it carries @vite-ignore,
// and it only ever runs under the Node coverage chain — never in a browser.
/* v8 ignore next 1 -- environment probe; Node-only in this test suite */
const isNode = typeof process !== "undefined" && !!process.versions.node;
/* v8 ignore next 1 -- coverage-chain probe; unset in production and browser */
const covDir = isNode ? process.env.NETWAVE_WASM_DIR : undefined;

// The live wasm instance, exposed on globalThis so the coverage hook
// (registered in the same worker context via vitest setupFiles) can read
// profraw out of linear memory after calling the dump entry points. Unset
// outside the coverage chain; nothing else reads it.
const wasmInstanceSlot: { current?: Record<string, unknown> } = {};
(
  globalThis as unknown as { __netwaveWasmInstance?: typeof wasmInstanceSlot }
).__netwaveWasmInstance = wasmInstanceSlot;

// core `call` is typed `any` in the glue; pin it to the worker's result
// envelope field so postMessage stays type-checked (was implicit via the
// glue's any-typed named import before the dynamic-import refactor).
type WasmCall = (
  handle: number | string,
  method: string,
  args: unknown,
) => WorkerResponse["result"];

const initWasm = async (): Promise<WasmCall> => {
  /* v8 ignore start -- coverage-chain dispatch: the instrumented branch runs
     only under the rust coverage chain (NETWAVE_WASM_DIR set); production and
     browser always take the default specifier. */
  const glue = covDir
    ? await import(/* @vite-ignore */ `${covDir}/netwave_wasm.js`)
    : await import("../dist/wasm-web/netwave_wasm.js");
  /* v8 ignore stop */
  /* v8 ignore next 1 -- browser path: glue fetches relative to its own URL; exercised in real-browser tests */
  const bytes = isNode ? await readWasmBytes() : undefined;
  const instance = await glue.default({ module_or_path: bytes });
  wasmInstanceSlot.current = instance as unknown as Record<string, unknown>;
  return glue.call as WasmCall;
};

const readWasmBytes = async (): Promise<Uint8Array> => {
  const { readFile } = await import("node:fs/promises");
  /* v8 ignore start -- instrumented path; only the coverage chain sets covDir */
  if (covDir) return readFile(`${covDir}/netwave_wasm_bg.wasm`);
  /* v8 ignore stop */
  const { fileURLToPath } = await import("node:url");
  return readFile(fileURLToPath(new URL("../dist/wasm-web/netwave_wasm_bg.wasm", import.meta.url)));
};

const ready = initWasm();

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
// The one exception is the coverage-chain control channel: a
// `{control: "dumpCoverage"}` message asks THIS context to drain the
// instrumented instance's profraw (only the worker realm can read its
// memory). It never reaches core dispatch — it is not a business verb, so
// the fixed-template invariant (no verb names here) holds.
workerScope.onmessage = async ({ data }: MessageEvent<WorkerRequest | Partial<ControlRequest>>) => {
  const call = await ready;
  if (data && "control" in data && data.control === "dumpCoverage") {
    // Raw bytes ride structuredClone back to the caller (the base64 encoding
    // is only needed for the vitest browser-command transport, done there).
    workerScope.postMessage({ id: 0, coverage: dumpCoverage(wasmInstanceSlot.current) });
    return;
  }
  const request = data as WorkerRequest;
  try {
    // `await` is structural: core `call` returns a plain value for every
    // sync verb, and a JS Promise for async ones (`fromUrl` — fetch runs
    // inside the worker, ironclad rule 8). Awaiting a non-Promise is a
    // no-op, so the template stays verb-count-independent.
    const result = await call(request.handle, request.method, request.args);
    workerScope.postMessage({ id: request.id, result });
  } catch (err) {
    workerScope.postMessage({ id: request.id, error: String(err) });
  }
};
