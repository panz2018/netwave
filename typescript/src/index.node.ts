// netwave node conditional shell (ESM source; tsdown emits the .mjs and
// the .cjs twin): explicit named re-exports (no `export *`, preserves
// tree-shaking). The public compute surface is single-async: compute verbs
// return Promises; `_`-prefixed names are sync escape hatches. The
// generated binding index.node.generated.mjs is produced by `napi build`
// (sync passthrough implementation, kept external by tsdown).
import {
  Frequency,
  FrequencyUnit,
  frequencyUnits,
  SPEED_OF_LIGHT,
  Touchstone,
  WavelengthUnit,
} from "../dist/index.node.generated.mjs";

// Vocabulary + class re-exports: the enum (numeric JS object), the
// passthrough function, and the Frequency/Touchstone classes come straight
// from the napi-generated glue, never re-declared here — a second copy of
// any name list could drift from core (ironclad rule 12). Construction is
// through `fromX` factories (ironclad rule 15); reclamation is the
// instance method `drop()`. `SPEED_OF_LIGHT` is the napi const re-export of
// the core constant (single definition site, ironclad rule 11).
export { Frequency, FrequencyUnit, frequencyUnits, SPEED_OF_LIGHT, Touchstone, WavelengthUnit };

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
