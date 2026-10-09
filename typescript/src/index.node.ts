// netwave node conditional shell (ESM source; tsdown emits the .mjs and
// the .cjs twin): explicit named re-exports (no `export *`, preserves
// tree-shaking). The public compute surface is single-async: compute verbs
// return Promises; `_`-prefixed names are sync escape hatches. The
// generated binding index.node.generated.mjs is produced by `napi build`
// (sync passthrough implementation, kept external by tsdown).
import {
  fillPattern as _napiFill,
  readElement as _napiRead,
  Frequency,
  FrequencyUnit,
  frequencyUnits,
  Network,
  SPEED_OF_LIGHT,
  WavelengthUnit,
} from "../dist/index.node.generated.mjs";
import type { NetwaveBuffer } from "./types.js";

// Vocabulary + class re-exports: the enum (numeric JS object), the
// passthrough function, and the Network/Frequency classes come straight from
// the napi-generated glue, never re-declared here — a second copy of any name
// list could drift from core (ironclad rule 12). The constructor is the data
// entry (no `upload` — that verb is browser-only); reclamation is the
// instance method `drop()`. `SPEED_OF_LIGHT` is the napi const re-export of
// the core constant (single definition site, ironclad rule 11).
export { Frequency, FrequencyUnit, frequencyUnits, Network, SPEED_OF_LIGHT, WavelengthUnit };

// Protocol hook (ironclad rule 9): `console.log(f)` auto-prints the core
// display string. The napi macro cannot attach a symbol-keyed method (its
// inspect attribute is disabled upstream), so the hook is this ONE line
// delegating to the generated `toString()` — a name passthrough, exempt from
// the thin-shell rule (same exemption as Python `__len__` -> `npoints`).
// `Symbol.for` resolves the same well-known symbol util.inspect looks up.
// The cast is needed because the napi-generated class type declares no
// symbol-keyed member (napi-derive cannot emit one); the prototype
// assignment itself is the only place the hook exists.
(Frequency.prototype as unknown as Record<symbol, () => string>)[
  Symbol.for("nodejs.util.inspect.custom")
] = function (this: Frequency): string {
  return this.toString();
};

/**
 * Allocate and fill an (nfreq, nports, nports) interleaved complex f64
 * buffer in the in-process napi core. `shape`/`frequency` ride the result
 * (metadata piggyback, same contract as the browser end).
 */
export async function fillPattern(nfreq: number, nports: number): Promise<NetwaveBuffer> {
  return _fillPattern(nfreq, nports);
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
  return {
    // napi external Buffers are always backed by a plain ArrayBuffer
    // (never SharedArrayBuffer); the typed glue reports `ArrayBufferLike`.
    buffer: buf.buffer as ArrayBuffer,
    byteOffset: 0,
    length: buf.byteLength / 16,
    shape: [nfreq, nports, nports],
    frequency: new Float64Array(0),
  };
};

/** @internal Sync passthrough escape hatch. */
export const _readElement: (view: Float64Array, idx: number) => number = _napiRead;
