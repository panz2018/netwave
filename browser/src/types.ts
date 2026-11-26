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

/** @internal Coverage-chain control message (not a business verb): asks the
 * worker to dump its instrumented instance's profraw and reply base64, or to
 * install a fetch stub in its own realm so a later `fromUrl` drives core's
 * fetch error arms (only the worker realm can be stubbed — `fetch` runs on
 * its global scope). The fixed-template invariant (no verb names in the worker
 * source) is untouched — this channel never reaches core's dispatch table. */
export type ControlRequest =
  | { control: "dumpCoverage" }
  | { control: "driveCoverage" }
  | { control: "stubFetch"; mode: FetchStubMode };

/** @internal Which fetch failure a `stubFetch` control message installs:
 * `textthrow` makes `Response.text()` throw synchronously (drives the
 * `resp.text().map_err` arm); `reject` makes it return a rejected Promise
 * (drives the await error arm); `nonstring` resolves it to a non-string
 * (drives the non-utf8 arm); `invalid` resolves a string that is not valid
 * Touchstone (drives the parse-error arm in `fromUrl`). */
export type FetchStubMode = "textthrow" | "reject" | "nonstring" | "invalid";

/** Coverage-chain reply payload: the raw profraw bytes (structuredClone
 * carries them across the worker boundary; the base64 encoding is only for
 * the vitest browser-command transport, done test-side) plus the minicov
 * module signature used to name the profraw file. */
export interface CoverageDump {
  profraw: Uint8Array;
  signature: string;
}

/** Worker reply envelope (worker -> main thread). `result.shape` and
 * `result.frequency` ride the same message (metadata piggyback). `string[]`
 * carries the vocabulary list (`frequencyUnits`). `coverage` answers a
 * control dump (null when the instance is not instrumented). */
export interface WorkerResponse {
  id: number;
  result?: NetwaveBuffer | number | Handle | string[];
  error?: string;
  coverage?: CoverageDump | null;
  /** Acknowledges a `stubFetch` control message (the stub is now installed). */
  stubbed?: boolean;
  /** Acknowledges a `driveCoverage` control message (defensive arms driven). */
  drove?: boolean;
}
