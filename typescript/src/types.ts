// netwave public API types — the single source of truth for the public
// contract (replaces the hand-written index.d.ts). Compute verbs are
// single-async: every public verb returns a Promise; `_`-prefixed names are
// sync escape hatches (@internal).

/** Buffer + view-rebuild metadata (views MUST be rebuilt from this after
 * await; zero-copy-roundtrip contract). */
export interface NetwaveBuffer {
  /** The underlying ArrayBuffer. */
  buffer: ArrayBuffer;
  /** Byte offset into `buffer` (always 0 on the node/napi path). */
  byteOffset: number;
  /** Number of f64 complex elements (= nfreq*nports*nports). */
  length: number;
}

/** Worker command envelope (main thread -> worker). */
export interface WorkerRequest {
  id: number;
  cmd: string;
  args: unknown[];
}

/** Worker reply envelope (worker -> main thread). */
export interface WorkerResponse {
  id: number;
  result?: NetwaveBuffer;
  error?: string;
}

/**
 * Allocate and fill an (nfreq, nports, nports) interleaved complex f64
 * buffer (phase-0 scaffold API).
 */
export declare function fillPattern(nfreq: number, nports: number): Promise<NetwaveBuffer>;

/** Pass a view back into core and read an element (zero-copy roundtrip). */
export declare function readElement(view: Float64Array, idx: number): Promise<number>;

/**
 * @internal Sync passthrough escape hatch: callable externally, signature
 * carries no stability guarantee.
 */
export declare function _fillPattern(nfreq: number, nports: number): NetwaveBuffer;

/** @internal Sync passthrough escape hatch. */
export declare function _readElement(view: Float64Array, idx: number): number;
