// netwave browser conditional shell: a PURE TRANSPORT over the resident
// worker (governance spec ironclad rule 8). The main thread never inits
// wasm and holds no data copy — wasm lives only inside the single resident
// worker (src/netwave.worker.ts). Explicit named exports (no `export *`, preserves
// tree-shaking); NO `_`-prefixed sync compute exists here (sync compute
// has nowhere to run without main-thread wasm; node keeps `_`).
//
// Singleton: `getWorker()` registers the worker on `globalThis`, so
// multiple imports, multiple handles, or even duplicate library copies on
// one page structurally share ONE worker (never a second one).
// `FrequencyUnit` is re-exported straight from the glue: it is a plain JS
// numeric-constant object, so importing it never instantiates wasm
// (ironclad rule 8 holds — only `wasmInit()`/compute touch wasm, and those
// live in the worker). `frequencyUnits()` DOES run wasm, so it goes
// through the worker like every other compute verb.

import type { FrequencyUnit as FrequencyUnitType } from "../dist/wasm-web/netwave_wasm.js";
import { FrequencyUnit } from "../dist/wasm-web/netwave_wasm.js";
import type { Handle, NetwaveBuffer, WorkerRequest, WorkerResponse } from "./types.js";

export { FrequencyUnit };

/** The shell's singleton worker, registered on globalThis. */
declare global {
  var __netwaveWorker: Worker | undefined;
}

/** Lazily construct the ONE resident worker; return the existing one if a
 * shell (this module or a duplicate copy of it) already created it. */
const getWorker = (): Worker =>
  (globalThis.__netwaveWorker ??= new Worker(
    // `.ts` specifier is legal under noEmit and resolvable by vite in
    // browser tests; publish_shell.mjs rewrites it to
    // "./netwave.worker.js" in the dist output.
    new URL("./netwave.worker.ts", import.meta.url),
    { type: "module" },
  ));

let seq = 0;
const pending = new Map<number, { resolve: (v: unknown) => void; reject: (e: Error) => void }>();

// One persistent message listener on the resident worker; replies are
// demultiplexed by request id (generalized dispatch, api-contract spec).
getWorker().addEventListener("message", ({ data }: MessageEvent<WorkerResponse>) => {
  const slot = pending.get(data.id);
  if (!slot) return;
  pending.delete(data.id);
  if (data.error) slot.reject(new Error(data.error));
  else slot.resolve(data.result);
});

/** Send one command to the resident worker and await its reply. */
const call = <T>(cmd: string, args: unknown[], transfer?: ArrayBuffer[]): Promise<T> => {
  const id = ++seq;
  return new Promise<T>((resolve, reject) => {
    pending.set(id, { resolve: resolve as (v: unknown) => void, reject });
    getWorker().postMessage({ id, cmd, args } satisfies WorkerRequest, {
      transfer: transfer ?? [],
    });
  });
};

/**
 * Allocate and fill an (nfreq, nports, nports) interleaved complex f64
 * buffer inside the resident worker and return a descriptor from which a
 * view can be rebuilt. The result buffer is transferred in (zero-copy);
 * `shape`/`frequency` ride the same reply.
 */
export const fillPattern = (nfreq: number, nports: number): Promise<NetwaveBuffer> =>
  call<NetwaveBuffer>("fillPattern", [nfreq, nports]);

/**
 * Host `view` inside the resident worker and return its handle. The view's
 * buffer is MOVED via explicit transfer (single ownership, ironclad rule
 * 8): after this call the caller's buffer is detached. Hosted data is
 * reusable across calls until `release`.
 */
export const upload = (view: Float64Array): Promise<Handle> =>
  call<Handle>("upload", [view], [view.buffer as ArrayBuffer]);

/** Drop hosted data and invalidate its handle. Later calls through the
 * handle reject (the error names the handle). */
export const release = (handle: Handle): Promise<void> =>
  call<void>("release", [handle]).then(() => undefined);

/**
 * Read one f64 element (re/im interleaved index). `target` is either a
 * hosted handle (no data moves) or an unhosted view (bytes are
 * boundary-copied into the worker; the caller's buffer is NOT consumed).
 */
export const readElement = (target: Handle | Float64Array, idx: number): Promise<number> =>
  call<number>("readElement", [target, idx]);

/**
 * List every frequency unit in canonical spelling, definition order. Runs
 * wasm, so it goes through the resident worker (ironclad rule 8: the main
 * thread never executes wasm). The names come from the core enum by
 * reflection — zero hand-copied vocabulary.
 */
export const frequencyUnits = (): Promise<string[]> => call<string[]>("frequencyUnits", []);

// --- Memory test seam (internalized) -------------------------------------
// NOT part of the public API. The main thread holds only a numeric-handle
// wrapper; the real wasm object lives in the worker (ironclad rule 8). When
// the wrapper is GC'd, the registry tells the worker to free it -> Rust Drop.
// The held value is the handle NUMBER, never the wrapper (a wrapper-referencing
// held value would pin the wrapper alive and defeat reclamation).
interface FrequencyRef {
  readonly handle: Handle;
}

const registry = new FinalizationRegistry<Handle>((handle) => {
  // Fire-and-forget: no caller awaits a GC-driven release. The worker frees
  // (Rust Drop) and deletes its address-table entry.
  getWorker().postMessage({ id: 0, cmd: "dropFrequency", args: [handle] } satisfies WorkerRequest);
});

/** Internal memory-pipeline surface (test seam; see the block comment). */
export const internals = {
  /** Allocate a sweep in the worker; return a GC-able wrapper holding its handle. */
  newFrequency: async (fHz: Float64Array, unit: FrequencyUnitType): Promise<FrequencyRef> => {
    const handle = await call<Handle>("newFrequency", [fHz, unit]);
    const ref: FrequencyRef = { handle };
    registry.register(ref, handle, ref); // held = handle number, never the ref
    return ref;
  },
  /** Deterministic early release (no GC needed); unregisters so no later GC double-frees. */
  drop: (ref: FrequencyRef): Promise<void> => {
    registry.unregister(ref);
    return call<void>("dropFrequency", [ref.handle]).then(() => undefined);
  },
  /** Witness: how many Rust `Frequency` objects are alive in the worker. */
  liveCount: (): Promise<number> => call<number>("liveCount", []),
};
