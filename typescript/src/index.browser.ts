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

import { SPEED_OF_LIGHT } from "../dist/constants.generated.mjs";
import type {
  FrequencyUnit as FrequencyUnitType,
  WavelengthUnit as WavelengthUnitType,
} from "../dist/wasm-web/netwave_wasm.js";
import { FrequencyUnit, WavelengthUnit } from "../dist/wasm-web/netwave_wasm.js";
import type { Handle, WorkerRequest, WorkerResponse } from "./types.js";

export { FrequencyUnit, SPEED_OF_LIGHT, WavelengthUnit };

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

  /** Build a sweep inside the worker from wavelength points in `wlUnit`
   * through a medium of phase index `n` (required): `f = c / (n × λ)`. */
  static fromWavelength(
    wl: Float64Array,
    wlUnit: WavelengthUnitType,
    n: number,
  ): Promise<Frequency> {
    return call<Handle>("frequency", "fromWavelength", [wl, wlUnit, n]).then(
      (handle) => new Frequency(handle),
    );
  }

  /** @internal Wrap a core handle in a shell and arm the GC fallback. */
  private constructor(handle: Handle) {
    this.handle = handle;
    registry.register(this, handle, this);
  }

  /** The frequency axis in hertz — a COPY built inside the worker and
   * structured-cloned back (ironclad rule 8: the main thread never runs
   * wasm; the copy crosses the realm boundary). */
  get f(): Promise<Float64Array> {
    return call<Float64Array>(this.handle, "f", []);
  }

  /** The axis in the current display unit (`f / multiplier`), derived in
   * core. */
  get fScaled(): Promise<Float64Array> {
    return call<Float64Array>(this.handle, "fScaled", []);
  }

  /** Angular frequency ω = 2πf (rad/s), derived in core. */
  get w(): Promise<Float64Array> {
    return call<Float64Array>(this.handle, "w", []);
  }

  /** The display unit (numeric enum member). Async getter: `await f.unit`. */
  get unit(): Promise<FrequencyUnitType> {
    return call<FrequencyUnitType>(this.handle, "unit", []);
  }

  /** Set the display unit (enum member | string). Fire-and-forget: the
   * resident worker is a single FIFO thread, so any later read observes the
   * new unit. A rejected setUnit (illegal string) is swallowed here — the
   * validation contract is observable on the awaited factory path
   * (`fromF`/`fromWavelength`), which is how the browser surfaces it (the
   * worker boundary makes a property setter inherently un-awaitable,
   * ironclad rule 8). Pure transport (ironclad rule 11). */
  set unit(value: FrequencyUnitType | string) {
    call<void>(this.handle, "setUnit", [value]).catch(() => {});
  }

  /** Wavelength λ = c / (n × f) in `wl_unit`; DC → Infinity. */
  wavelength(wlUnit: WavelengthUnitType, n: number): Promise<Float64Array> {
    return call<Float64Array>(this.handle, "wavelength", [wlUnit, n]);
  }

  /** An independent copy (a new handle in the worker). `copy` is a
   * factory (it allocates a new handle), so it rides the namespace channel
   * with this shell's handle as the source argument. */
  copy(): Promise<Frequency> {
    return call<Handle>("frequency", "copy", [this.handle]).then((handle) => new Frequency(handle));
  }

  /** The cross-end uniform display string (async: worker roundtrip). */
  toString(): Promise<string> {
    return call<string>(this.handle, "toString", []);
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

/** The `{ values, shape }` payload of `Touchstone.data()` (flat addressing:
 * `idx = ((f*n + r)*n + c)*2`, +0=re/mag/db, +1=im/deg). JS has no complex
 * type, so `shape` is always `(nfreq, n, n, 2)` — the last axis is the
 * interleaved pair. */
export interface TouchstoneData {
  values: Float64Array;
  shape: number[];
}

/**
 * A parsed Touchstone shell. Construction IS parsing: the factories
 * (`fromText`/`fromFile`/`fromUrl`) host a fully validated object in the
 * worker's core table and return a shell over its numeric handle. Data
 * lives in the worker (ironclad rule 8); the shell holds only the handle.
 * `writeFile`/`fromFile` are shell-only async platform glue (the browser
 * has no filesystem): `fromFile` transfers the bytes in, `writeFile`
 * receives `{text, filename}` back and triggers a download.
 */
export class Touchstone {
  /** @internal Protocol detail — not public API. */
  readonly handle: Handle;
  private dropped = false;

  /** Parse Touchstone text inside the worker. `nports` explicit, else
   * inferred from the `path` filename grammar; `path`'s stem becomes `name`. */
  static fromText(text: string, nports?: number, path?: string): Promise<Touchstone> {
    return call<Handle>("touchstone", "fromText", [text, nports ?? null, path ?? null]).then(
      (handle) => new Touchstone(handle),
    );
  }

  /** Read a `File` and parse it in the worker. The bytes are MOVED via
   * transfer (single ownership, ironclad rule 8): afterwards the caller's
   * buffer is detached. The filename rides along for the name pipeline. */
  static async fromFile(file: File): Promise<Touchstone> {
    const buf = (await file.arrayBuffer()) as ArrayBuffer;
    const handle = await call<Handle>(
      "touchstone",
      "fromBytes",
      [new Uint8Array(buf), file.name],
      [buf],
    );
    return new Touchstone(handle);
  }

  /** Fetch over HTTP inside the worker and parse (Promise; the main thread
   * never runs wasm — ironclad rule 8). CORS/network errors reject
   * verbatim. */
  static fromUrl(url: string): Promise<Touchstone> {
    return call<Handle>("touchstone", "fromUrl", [url]).then((handle) => new Touchstone(handle));
  }

  /** Pure-data factory (ironclad rule 15 — construction only through
   * `fromX` factories): hosts `(frequency, data, z0, parameter)` in the
   * worker's core table and returns a shell over its new handle. `data` is
   * a flat interleaved re/im `Float64Array` in domain `parameter`; `z0` a
   * scalar-or-per-port real; `parameter` (S/Z/Y/G/H) required — no silent
   * S default. The shell reads `frequency.handle` internally (the user
   * passes the object, never the handle). `data` is MOVED via transfer
   * (single ownership, ironclad rule 8): afterwards the caller's buffer is
   * detached. */
  static fromData(
    frequency: Frequency,
    data: Float64Array,
    z0: Float64Array | number[],
    parameter: string,
  ): Promise<Touchstone> {
    return call<Handle>(
      "touchstone",
      "fromData",
      [frequency.handle, data, z0, parameter],
      [data.buffer as ArrayBuffer],
    ).then((handle) => new Touchstone(handle));
  }

  /** @internal Wrap a core handle in a shell and arm the GC fallback. */
  private constructor(handle: Handle) {
    this.handle = handle;
    registry.register(this, handle, this);
  }

  /** The stored S master data (flat interleaved re/im), cloned back. */
  get s(): Promise<Float64Array> {
    return call<Float64Array>(this.handle, "s", []);
  }

  /** Z domain, computed fresh in core. */
  get z(): Promise<Float64Array> {
    return call<Float64Array>(this.handle, "z", []);
  }

  /** Y domain, computed fresh in core. */
  get y(): Promise<Float64Array> {
    return call<Float64Array>(this.handle, "y", []);
  }

  /** G domain (2-port only), computed fresh in core. */
  get g(): Promise<Float64Array> {
    return call<Float64Array>(this.handle, "g", []);
  }

  /** H domain (2-port only), computed fresh in core. */
  get h(): Promise<Float64Array> {
    return call<Float64Array>(this.handle, "h", []);
  }

  /** The frequency axis in hertz — a COPY built in the worker. */
  get f(): Promise<Float64Array> {
    return call<Float64Array>(this.handle, "f", []);
  }

  /** Per-port reference impedance (the single authority). */
  get z0(): Promise<Float64Array> {
    return call<Float64Array>(this.handle, "z0", []);
  }

  /** Port count. */
  nports(): Promise<number> {
    return call<number>(this.handle, "nports", []);
  }

  /** File stem without extension. */
  name(): Promise<string> {
    return call<string>(this.handle, "name", []);
  }

  /** Merged `!` comment text. */
  comments(): Promise<string> {
    return call<string>(this.handle, "comments", []);
  }

  /** File format version, `"1.0"` / `"1.1"`. */
  version(): Promise<string> {
    return call<string>(this.handle, "version", []);
  }

  /** Original parameter domain (metadata), canonical uppercase. */
  parameter(): Promise<string> {
    return call<string>(this.handle, "parameter", []);
  }

  /** Unified accessor domain × format (both mandatory; use `s` for the
   * zero-copy default). */
  data(parameter: string, format: string): Promise<TouchstoneData> {
    return call<TouchstoneData>(this.handle, "data", [parameter, format]);
  }

  /** Render Touchstone text in `parameter`/`format` (rendered in core). */
  writeTouchstone(parameter: string, format: string): Promise<string> {
    return call<string>(this.handle, "writeTouchstone", [parameter, format]);
  }

  /** Download the rendered text (shell-only platform glue). Core renders
   * the text and corrects the filename (`write_path`, extension always
   * `.{P}Np`); the shell only does Blob + `<a download>`. `path` is
   * optional here (the browser has no directories). */
  async writeFile(path: string | undefined, parameter: string, format: string): Promise<void> {
    const { text, filename } = await call<{ text: string; filename: string }>(
      this.handle,
      "writeFile",
      [parameter, format, path ?? null],
    );
    const url = URL.createObjectURL(new Blob([text], { type: "text/plain" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  /** Path/URL → filename with extension (worker `"touchstone"` namespace). */
  static filenameFromPath(path: string): Promise<string> {
    return call<string>("touchstone", "filenameFromPath", [path]);
  }

  /** Filename → stem (Touchstone grammar; no match → whole string). */
  static nameFromFilename(filename: string): Promise<string> {
    return call<string>("touchstone", "nameFromFilename", [filename]);
  }

  /** Filename → port count (grammar `\.[ghsyz]\d+p`); no match rejects. */
  static nportsFromFilename(filename: string): Promise<number> {
    return call<number>("touchstone", "nportsFromFilename", [filename]);
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
