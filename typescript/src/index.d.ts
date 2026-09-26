/**
 * netwave public API types (scaffold phase 0). Compute verbs are
 * single-async (2026-09-22 contract): every public verb returns a Promise;
 * `_`-prefixed names are sync escape hatches (@internal).
 */

/** Buffer + view-rebuild metadata (views MUST be rebuilt from this after await; contract clause 4). */
export interface NetwaveBuffer {
  /** The underlying ArrayBuffer. */
  buffer: ArrayBuffer;
  /** Byte offset into `buffer` (always 0 on the node/napi path). */
  byteOffset: number;
  /** Number of f64 complex elements (= nfreq*nports*nports). */
  length: number;
}

/** Allocate and fill an interleaved complex f64 buffer (phase-0 temporary API). */
export function fillPattern(nfreq: number, nports: number): Promise<NetwaveBuffer>;

/** Pass a view back into core and read an element (zero-copy roundtrip verification). */
export function readElement(view: Float64Array, idx: number): Promise<number>;

/**
 * @internal Sync passthrough escape hatch: callable externally, signature
 * carries no stability guarantee. Counted normally by coverage (rule 7).
 */
export const _fillPattern: (nfreq: number, nports: number) => NetwaveBuffer;

/** @internal Sync passthrough escape hatch. */
export const _readElement: (view: Float64Array, idx: number) => number;
