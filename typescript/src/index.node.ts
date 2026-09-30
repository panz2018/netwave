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
import type { NetwaveBuffer } from "./types.js";

/**
 * Allocate and fill an (nfreq, nports, nports) interleaved complex f64
 * buffer (phase-0 scaffold). Public async surface: on Node small data
 * resolves immediately (large-data AsyncTask offload arrives in phase 6).
 */
export async function fillPattern(nfreq: number, nports: number): Promise<NetwaveBuffer> {
  return _fillPattern(nfreq, nports);
}

/** Pass a view back into core and read an element (zero-copy roundtrip). */
export async function readElement(buf: Float64Array, idx: number): Promise<number> {
  return _readElement(buf, idx);
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
  return { buffer: buf.buffer, byteOffset: 0, length: buf.byteLength / 16 };
};

/** @internal Sync passthrough escape hatch. */
export const _readElement: (view: Float64Array, idx: number) => number = _napiRead;
