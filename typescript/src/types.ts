// netwave public API types — the single source of truth for the shared
// public contract. Compute verbs are single-async: every public verb
// returns a Promise. Platform-only surfaces live in their entry shells:
// the node entry exports the `_`-prefixed sync passthroughs (@internal,
// index.node.ts); the browser entry exports none (main thread has no
// wasm, ironclad rule 8).

/** @internal Protocol detail: opaque handle to a resource inside the
 * resident worker's core table (ironclad rule 8). Handles are allocated by
 * core's single counter and are invalidated by `drop`. Shells hold one;
 * users never pass a handle across the public API. */
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
  /** Frequency axis in Hz (f64) — piggybacked metadata. Empty when the
   * data carries no frequency axis. */
  frequency: Float64Array;
}

/** Worker request envelope (main thread -> resident worker). Generic
 * dispatch (api-contract spec): `{id, handle, method, args}` forwarded
 * verbatim to the single core entry `call`. A numeric handle addresses an
 * instance in the core table; a string handle names a core module namespace
 * (factories + free functions). Adding a method changes no protocol type. */
export interface WorkerRequest {
  id: number;
  handle: Handle | string;
  method: string;
  args: unknown[];
}

/** Worker reply envelope (worker -> main thread). `result.shape` and
 * `result.frequency` ride the same message (metadata piggyback). `string[]`
 * carries the vocabulary list (`frequencyUnits`). */
export interface WorkerResponse {
  id: number;
  result?: NetwaveBuffer | number | Handle | string[];
  error?: string;
}

/**
 * Allocate and fill an (nfreq, nports, nports) interleaved complex f64
 * buffer inside the resident worker and return a descriptor from which a
 * view can be rebuilt.
 */
export declare function fillPattern(nfreq: number, nports: number): Promise<NetwaveBuffer>;
