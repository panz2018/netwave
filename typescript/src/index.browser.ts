// netwave browser conditional shell: a PURE TRANSPORT over the resident
// worker (governance spec ironclad rule 8). The main thread never inits
// wasm and holds no data copy — wasm lives only inside the single resident
// worker (src/netwave.worker.ts) and the handle table lives in core Rust
// inside that worker. The shells here hold nothing but a numeric handle
// (@internal protocol detail); every method body is one postMessage of
// `{handle, method, args}` (generic dispatch, api-contract spec): a string
// handle names a core module namespace for factories, a numeric handle
// addresses an instance. No shell ever computes (ironclad rule 11).
// Explicit named exports (no `export *`, preserves tree-shaking); NO
// `_`-prefixed sync compute exists here (sync compute has nowhere to run
// without main-thread wasm; node keeps `_`).
//
// Singleton: `getWorker()` registers the worker on `globalThis`, so
// multiple imports, multiple shells, or even duplicate library copies on
// one page structurally share ONE worker (never a second one).
// `FrequencyUnit` is re-exported straight from the glue: it is a plain JS
// numeric-constant object, so importing it never instantiates wasm
// (ironclad rule 8 holds — only worker commands touch wasm).
// `frequencyUnits()`/`liveCount()` DO run wasm, so they go through the
// worker's `"frequency"` namespace like every other verb — the list is
// built in Rust, the shell never derives it.

import type { FrequencyUnit as FrequencyUnitType } from "../dist/wasm-web/netwave_wasm.js";
import { FrequencyUnit } from "../dist/wasm-web/netwave_wasm.js";
import type { Handle, WorkerRequest, WorkerResponse } from "./types.js";

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
// demultiplexed by request id (generic dispatch, api-contract spec).
getWorker().addEventListener("message", ({ data }: MessageEvent<WorkerResponse>) => {
  const slot = pending.get(data.id);
  if (!slot) return;
  pending.delete(data.id);
  if (data.error) slot.reject(new Error(data.error));
  else slot.resolve(data.result);
});

/** Send one generic request to the resident worker and await its reply.
 * `handle`: string = core module namespace (factories/free functions),
 * number = instance in the core table. */
const call = <T>(
  handle: Handle | string,
  method: string,
  args: unknown[],
  transfer?: ArrayBuffer[],
): Promise<T> => {
  const id = ++seq;
  return new Promise<T>((resolve, reject) => {
    pending.set(id, { resolve: resolve as (v: unknown) => void, reject });
    getWorker().postMessage({ id, handle, method, args } satisfies WorkerRequest, {
      transfer: transfer ?? [],
    });
  });
};

/** GC safety net: when a shell is collected without `drop()`, tell the
 * worker to free the core resource. The held value is the handle NUMBER,
 * never the shell (a shell-referencing held value would pin the shell
 * alive and defeat reclamation). */
const registry = new FinalizationRegistry<Handle>((handle) => {
  // Fire-and-forget: no caller awaits a GC-driven drop. The worker frees
  // (core `drop` → `remove` → Rust `Drop`).
  getWorker().postMessage({ id: 0, handle, method: "drop", args: [] } satisfies WorkerRequest);
});

/**
 * An S-matrix data shell. `upload` is the browser data entry (the worker
 * linear-memory boundary is browser-only); data lives in the worker's core
 * handle table and this shell holds only its @internal numeric handle.
 * `readElement` reads one interleaved f64 element; `drop` is the
 * deterministic manual reclamation (idempotent; post-drop access rejects).
 * GC of the shell without `drop` fires the registry and the worker frees
 * the core resource (RAII fallback).
 */
export class Network {
  /** @internal Protocol detail — not public API. */
  readonly handle: Handle;
  private dropped = false;

  /** Host `view` in the resident worker and return a shell over its new
   * handle. The buffer is MOVED via explicit transfer (single ownership,
   * ironclad rule 8): afterwards the caller's buffer is detached. Shape is
   * explicit because a bare `Float64Array` length does not factor uniquely
   * into `(nfreq, nports)`. */
  static upload(view: Float64Array, nfreq: number, nports: number): Promise<Network> {
    return call<Handle>(
      "network",
      "upload",
      [view, nfreq, nports],
      [view.buffer as ArrayBuffer],
    ).then((handle) => new Network(handle));
  }

  /** Pattern-filled factory: allocates and fills inside the worker and
   * returns a shell over the new handle. */
  static fillPattern(nfreq: number, nports: number): Promise<Network> {
    return call<Handle>("network", "fillPattern", [nfreq, nports]).then(
      (handle) => new Network(handle),
    );
  }

  /** @internal Wrap a core handle in a shell and arm the GC fallback. */
  private constructor(handle: Handle) {
    this.handle = handle;
    registry.register(this, handle, this);
  }

  /** Read one interleaved f64 element by flat index. Rejects after `drop`. */
  readElement(idx: number): Promise<number> {
    return call<number>(this.handle, "readElement", [idx]);
  }

  /** Deterministic manual reclamation (the unified cross-end verb,
   * ironclad rule 12). Idempotent: the second call is a no-op and the GC
   * fallback is unregistered, so the core `Drop` runs exactly once. */
  drop(): Promise<void> {
    if (this.dropped) return Promise.resolve();
    this.dropped = true;
    registry.unregister(this);
    return call<void>(this.handle, "drop", []);
  }
}

/**
 * A frequency sweep shell. `fromF` is the data entry (core `from_f`
 * verbatim, mechanical camelCase); `drop` is the deterministic manual
 * reclamation shared with RAII. Post-drop access rejects.
 */
export class Frequency {
  /** @internal Protocol detail — not public API. */
  readonly handle: Handle;
  private dropped = false;

  /** Build a sweep inside the worker from hertz points + unit (the enum
   * member, passed by member — never coerced; validation stays in core). */
  static fromF(fHz: Float64Array, unit: FrequencyUnitType): Promise<Frequency> {
    return call<Handle>("frequency", "fromF", [fHz, unit]).then((handle) => new Frequency(handle));
  }

  /** @internal Wrap a core handle in a shell and arm the GC fallback. */
  private constructor(handle: Handle) {
    this.handle = handle;
    registry.register(this, handle, this);
  }

  /** Number of frequency points. Rejects after `drop`. */
  npoints(): Promise<number> {
    return call<number>(this.handle, "npoints", []);
  }

  /** Deterministic manual reclamation (the unified cross-end verb).
   * Idempotent; post-drop access rejects. */
  drop(): Promise<void> {
    if (this.dropped) return Promise.resolve();
    this.dropped = true;
    registry.unregister(this);
    return call<void>(this.handle, "drop", []);
  }
}

/**
 * List every frequency unit in canonical spelling, definition order. Runs
 * wasm, so it goes through the resident worker's `"frequency"` namespace
 * (ironclad rule 8: the main thread never executes wasm; ironclad rule 11:
 * the list is built in Rust, the shell never derives it).
 */
export const frequencyUnits = (): Promise<string[]> =>
  call<string[]>("frequency", "frequencyUnits", []);

/** Witness: how many `Frequency` resources are alive in the worker. Runs
 * wasm, so it goes through the resident worker's `"frequency"` namespace. */
export const liveCount = (): Promise<number> => call<number>("frequency", "liveCount", []);
