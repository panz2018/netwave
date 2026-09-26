// netwave node conditional shell (ESM): explicit named re-exports (no
// `export *`, preserves tree-shaking). The public compute surface is
// single-async: compute verbs return Promises; `_`-prefixed names are sync
// escape hatches. The generated binding index.node.generated.mjs is produced
// by `napi build` (sync passthrough implementation).
import {
  fillPattern as _napiFill,
  readElement as _napiRead,
} from "../dist/index.node.generated.mjs";

/**
 * Allocate and fill an (nfreq, nports, nports) interleaved complex f64
 * buffer (phase-0 scaffold). Public async surface: on Node small data
 * resolves immediately (large-data AsyncTask offload arrives in phase 6).
 * @returns {Promise<{buffer: ArrayBuffer, byteOffset: number, length: number}>}
 */
export async function fillPattern(nfreq, nports) {
  return _fillPattern(nfreq, nports);
}

/**
 * Pass a view back into core and read an element (zero-copy roundtrip).
 * @returns {Promise<number>}
 */
export async function readElement(buf, idx) {
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
export const _fillPattern = (nfreq, nports) => {
  const buf = _napiFill(nfreq, nports);
  return { buffer: buf.buffer, byteOffset: 0, length: buf.byteLength / 16 };
};

/** @internal Sync passthrough escape hatch. */
export const _readElement = _napiRead;
