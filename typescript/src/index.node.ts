// netwave node conditional shell (ESM source; tsdown emits the .mjs and
// the .cjs twin): explicit named re-exports (no `export *`, preserves
// tree-shaking). The public compute surface is single-async: compute verbs
// return Promises; `_`-prefixed names are sync escape hatches. The
// generated binding index.node.generated.mjs is produced by `napi build`
// (sync passthrough implementation, kept external by tsdown).
import {
  fillPattern as _napiFill,
  readElement as _napiRead,
} from "../dist/index.node.generated.mjs";
import type { Handle, NetwaveBuffer } from "./types.js";

/**
 * Allocate and fill an (nfreq, nports, nports) interleaved complex f64
 * buffer (phase-0 scaffold). Public async surface: on Node small data
 * resolves immediately (large-data AsyncTask offload arrives in phase 6).
 * `shape`/`frequency` ride the result (metadata piggyback, same contract
 * as the browser end).
 */
export async function fillPattern(nfreq: number, nports: number): Promise<NetwaveBuffer> {
  return _fillPattern(nfreq, nports);
}

/**
 * Host a COPY of `view` in the in-process core and return its handle.
 * Node has no worker boundary, so bytes are copied (the caller's buffer
 * survives — nothing to detach). Handles are invalidated by `release`.
 */
export async function upload(view: Float64Array): Promise<Handle> {
  const handle = ++lastHandle;
  hosted.set(handle, new Float64Array(view));
  return handle;
}

/** Drop hosted data and invalidate its handle. Later calls through the
 * handle reject (the error names the handle). */
export async function release(handle: Handle): Promise<void> {
  if (!hosted.delete(handle)) {
    throw new Error(`unknown or released handle: ${handle}`);
  }
}

// In-process handle table (node mirrors the worker's contract without a
// worker: the napi core lives in this process).
const hosted = new Map<Handle, Float64Array>();
let lastHandle: Handle = 0;

/**
 * Read one f64 element from hosted data (handle) or an unhosted view
 * (read directly in-process, zero copy).
 */
export async function readElement(target: Handle | Float64Array, idx: number): Promise<number> {
  if (typeof target === "number") {
    const view = hosted.get(target);
    if (!view) throw new Error(`unknown or released handle: ${target}`);
    return _readElement(view, idx);
  }
  return _readElement(target, idx);
}

/**
 * @internal Sync passthrough escape hatch. Callable externally but the
 * signature carries no stability guarantee; do not use in new code.
 * napi returns an external Buffer (Uint8Array view, byteOffset 0 and the
 * underlying ArrayBuffer exactly the same length — external allocations are
 * not pooled). The shell converts it to the contract shape, referencing the
 * same memory with zero copies.
 */
export const _fillPattern = (nfreq: number, nports: number): NetwaveBuffer => {
  const buf = _napiFill(nfreq, nports);
  return {
    buffer: buf.buffer,
    byteOffset: 0,
    length: buf.byteLength / 16,
    shape: [nfreq, nports, nports],
    frequency: new Float64Array(0),
  };
};

/** @internal Sync passthrough escape hatch. */
export const _readElement: (view: Float64Array, idx: number) => number = _napiRead;
