#!/usr/bin/env node
// cross-binding dump: node (napi) and wasm ends each emit the (2,2)
// roundtrip values. Usage (from typescript/): node scripts/dump.mjs <out_dir>
// Emits <out>/node.bin and <out>/wasm.bin (raw little-endian f64 bytes,
// re/im interleaved). Binary, not JSON: JSON.stringify writes -0 as 0 and
// loses the sign bit, making bit-exact comparison impossible.
import { mkdirSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

const out = process.argv[2];
if (!out) {
  console.error("usage: node scripts/dump.mjs <out_dir>");
  process.exit(2);
}
mkdirSync(out, { recursive: true });

const NFREQ = 2;
const NPORTS = 2;

// node (napi) side — public async surface (dist = the published artifact;
// src/ is TS and runs only under vitest/Node type-stripping).
const { fillPattern, Frequency, FrequencyUnit, WavelengthUnit } = await import(
  "../dist/index.node.mjs"
);
const n = await fillPattern(NFREQ, NPORTS);
const nv = new Float64Array(n.buffer, n.byteOffset, n.length * 2);
const nodePath = join(out, "node.bin");
writeFileSync(nodePath, Buffer.from(nv.buffer, nv.byteOffset, nv.byteLength));
// λ↔f round-trip axis (spec: frequency-class): f -> wavelength -> f.
{
  const f = Frequency.fromF([1.0, 2.0, 5.0], FrequencyUnit.GHz);
  const wl = f.wavelength(WavelengthUnit.mm, 2.2);
  const back = Frequency.fromWavelength(Array.from(wl), WavelengthUnit.mm, 2.2);
  const axis = new Float64Array(back.f);
  const p = join(out, "node_freq.bin");
  writeFileSync(p, Buffer.from(axis.buffer, axis.byteOffset, axis.byteLength));
}

// wasm side — drive the DIST worker module through a faked worker scope
// (ironclad rule 8: wasm lives only in the resident worker; plain Node has
// no Worker global, so fake `self` and call its onmessage directly — the
// same code path the browser runs). The handle table lives in core: the
// reply carries a u32 handle, elements are read back through it. A fresh
// promise per roundtrip: a promise resolves exactly once.
let pending;
const reply = () =>
  new Promise((r) => {
    pending = r;
  });
globalThis.self = {
  onmessage: null,
  postMessage: (msg) => pending(msg),
};
await import("../dist/netwave.worker.js");
const ask = async (handle, method, args) => {
  const p = reply();
  self.onmessage({ data: { id: 1, handle, method, args } });
  const res = await p;
  if (res.error) throw new Error(`worker error: ${res.error}`);
  return res.result;
};
const handle = await ask("network", "fillPattern", [NFREQ, NPORTS]);
const wv = new Float64Array(NFREQ * NPORTS * NPORTS * 2);
for (let i = 0; i < wv.length; i++) wv[i] = await ask(handle, "readElement", [i]);
const wasmPath = join(out, "wasm.bin");
writeFileSync(wasmPath, Buffer.from(wv.buffer, wv.byteOffset, wv.byteLength));

// λ↔f round-trip axis through the resident worker (spec: frequency-class):
// fromF -> wavelength -> fromWavelength -> f. The worker's numeric unit
// ordinals: GHz=3, mm=2 (core enum definition order).
{
  const GHZ = 3;
  const MM = 2;
  const fh = await ask("frequency", "fromF", [new Float64Array([1.0, 2.0, 5.0]), GHZ]);
  const wl = await ask(fh, "wavelength", [MM, 2.2]);
  const back = await ask("frequency", "fromWavelength", [wl, MM, 2.2]);
  const axis = await ask(back, "f", []);
  const p = join(out, "wasm_freq.bin");
  writeFileSync(p, Buffer.from(axis.buffer, axis.byteOffset, axis.byteLength));
  await ask(fh, "drop", []);
  await ask(back, "drop", []);
}

console.log(`dumped ${resolve(nodePath)} ${resolve(wasmPath)}`);
