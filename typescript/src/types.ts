// netwave public API types — the single source of truth for the public
// contract (replaces the hand-written index.d.ts). Compute verbs are
// single-async: every public verb returns a Promise. On the browser end
// there are NO sync escape hatches (`_`-prefixed): the main thread never
// inits wasm (governance spec ironclad rule 8), so sync compute has
// nowhere to run. On the node end `_`-prefixed sync passthroughs remain
// (@internal) because the napi core lives in-process.

/** Opaque handle to data hosted inside the resident worker (ironclad
 * rule 8: the worker is the single data authority). Handles are assigned
 * by the worker, monotonically increasing. A handle is invalid after
 * `release` or after the worker dies. */
export type Handle = number;

/** Buffer + view-rebuild metadata. Views MUST be rebuilt from this after
 * await (zero-copy-roundtrip contract). `shape`/`frequency` ride the
 * result back in the same message (metadata piggyback) — reading them
 * never costs an extra worker roundtrip. */
export interface NetwaveBuffer {
  /** The underlying ArrayBuffer (transferred in from the worker). */
  buffer: ArrayBuffer;
  /** Byte offset into `buffer` (always 0 on the node/napi path). */
  byteOffset: number;
  /** Number of f64 complex elements (= nfreq*nports*nports). */
  length: number;
  /** (nfreq, nports, nports) — piggybacked metadata. */
  shape: [number, number, number];
  /** Frequency axis in Hz (f64) — piggybacked metadata. Empty until the
   * real data model (phase 2) populates it. */
  frequency: Float64Array;
}

/** Worker command envelope (main thread -> resident worker). Generalized
 * dispatch per api-contract spec: `{id, cmd, args}`; adding a core verb
 * only extends the worker's static cmds table. */
export interface WorkerRequest {
  id: number;
  cmd: string;
  args: unknown[];
}

/** Worker reply envelope (worker -> main thread). `result.shape` and
 * `result.frequency` ride the same message (metadata piggyback). */
export interface WorkerResponse {
  id: number;
  result?: NetwaveBuffer | number | Handle;
  error?: string;
}

/**
 * Allocate and fill an (nfreq, nports, nports) interleaved complex f64
 * buffer inside the resident worker (phase-0 scaffold API) and return a
 * descriptor from which a view can be rebuilt.
 */
export declare function fillPattern(nfreq: number, nports: number): Promise<NetwaveBuffer>;

/**
 * Host a copy of `view` inside the resident worker and return its handle.
 * Browser: the view's buffer is moved via explicit transfer — the caller's
 * buffer is detached afterwards (single ownership, ironclad rule 8).
 * Node: the bytes are copied into the in-process core (no detach).
 */
export declare function upload(view: Float64Array): Promise<Handle>;

/** Drop hosted data and invalidate its handle. Later calls through the
 * handle MUST reject (the error message contains the handle number). */
export declare function release(handle: Handle): Promise<void>;

/**
 * Read one f64 element (re/im interleaved index) from hosted data
 * (handle) or from an unhosted view (browser: the view's bytes are
 * boundary-copied into the worker, the caller's buffer is NOT consumed;
 * node: read directly in-process).
 */
export declare function readElement(target: Handle | Float64Array, idx: number): Promise<number>;

/**
 * @internal Sync passthrough escape hatch — **node only**. Callable
 * externally, signature carries no stability guarantee. The browser entry
 * does not export any `_`-prefixed sync compute (main thread has no
 * wasm, ironclad rule 8).
 */
export declare function _fillPattern(nfreq: number, nports: number): NetwaveBuffer;

/** @internal Sync passthrough escape hatch — node only. */
export declare function _readElement(view: Float64Array, idx: number): number;
