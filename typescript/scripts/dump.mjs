#!/usr/bin/env node
// cross-binding dump: node (napi) and wasm ends each emit the λ↔f axis and
// the Touchstone S master data per sample. Usage (from repo root): node
// typescript/scripts/dump.mjs <out_dir>. Emits <out>/<end>/freq.bin and
// <out>/<end>/<sample>/s.bin|z0.bin|version.txt (raw little-endian f64
// bytes, re/im interleaved). Binary, not JSON: JSON.stringify writes -0 as
// 0 and loses the sign bit, making bit-exact comparison impossible.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

// Samples resolve relative to this script, not cwd, so the dump runs the
// same from the repo root (check:cross) and from typescript/ (cross-dump).
const samplesDir = resolve(import.meta.dirname, "../../oracle/samples");

const out = process.argv[2];
if (!out) {
  console.error("usage: node scripts/dump.mjs <out_dir>");
  process.exit(2);
}
mkdirSync(out, { recursive: true });

// node (napi) side — public async surface (dist = the published artifact;
// src/ is TS and runs only under vitest/Node type-stripping).
const { Frequency, FrequencyUnit, WavelengthUnit, Touchstone } = await import(
  "../dist/index.node.mjs"
);
// λ↔f round-trip axis (spec: frequency-class): f -> wavelength -> f.
{
  const f = Frequency.fromF([1.0, 2.0, 5.0], FrequencyUnit.GHz);
  const wl = f.wavelength(WavelengthUnit.mm, 2.2);
  const back = Frequency.fromWavelength(Array.from(wl), WavelengthUnit.mm, 2.2);
  const axis = new Float64Array(back.f);
  const nodeDir = join(out, "node");
  mkdirSync(nodeDir, { recursive: true });
  const p = join(nodeDir, "freq.bin");
  writeFileSync(p, Buffer.from(axis.buffer, axis.byteOffset, axis.byteLength));
}

// Touchstone cross-compare (node): parse each shared sample, dump the S
// master data (interleaved f64), z0, and version.
for (const c of ["s1p", "s2p", "s4p"]) {
  const ts = await Touchstone.fromFile(join(samplesDir, `dut.${c}`));
  const sampleDir = join(out, "node", `dut.${c}`);
  mkdirSync(sampleDir, { recursive: true });
  const sv = new Float64Array(ts.s);
  writeFileSync(join(sampleDir, "s.bin"), Buffer.from(sv.buffer, 0, sv.byteLength));
  const zv = new Float64Array(ts.z0);
  writeFileSync(join(sampleDir, "z0.bin"), Buffer.from(zv.buffer, 0, zv.byteLength));
  writeFileSync(join(sampleDir, "version.txt"), ts.version);
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
  const wasmDir = join(out, "wasm");
  mkdirSync(wasmDir, { recursive: true });
  const p = join(wasmDir, "freq.bin");
  writeFileSync(p, Buffer.from(axis.buffer, axis.byteOffset, axis.byteLength));
  await ask(fh, "drop", []);
  await ask(back, "drop", []);
}

// Touchstone cross-compare (wasm, through the resident worker): the bytes
// are read on the host and moved in via fromBytes (the worker has no
// filesystem); s/z0/version come back cloned and are dumped.
for (const c of ["s1p", "s2p", "s4p"]) {
  const buf = readFileSync(join(samplesDir, `dut.${c}`));
  const th = await ask("touchstone", "fromBytes", [new Uint8Array(buf), `dut.${c}`]);
  const sampleDir = join(out, "wasm", `dut.${c}`);
  mkdirSync(sampleDir, { recursive: true });
  const sarr = new Float64Array(await ask(th, "s", []));
  writeFileSync(join(sampleDir, "s.bin"), Buffer.from(sarr.buffer, 0, sarr.byteLength));
  const zarr = new Float64Array(await ask(th, "z0", []));
  writeFileSync(join(sampleDir, "z0.bin"), Buffer.from(zarr.buffer, 0, zarr.byteLength));
  writeFileSync(join(sampleDir, "version.txt"), await ask(th, "version", []));
  await ask(th, "drop", []);
}

console.log(
  `dumped ${resolve(join(out, "node", "dut.s2p", "s.bin"))} ${resolve(join(out, "wasm", "dut.s2p", "s.bin"))}`,
);
