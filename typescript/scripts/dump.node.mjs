#!/usr/bin/env node
// Node (napi) cross-binding dump: emit the λ↔f axis and the Touchstone S
// master data per sample. Usage (from repo root): node
// typescript/scripts/dump.node.mjs <out_dir>. Emits <out>/node/freq.bin and
// <out>/node/<sample>/s.bin|z0.bin|version.txt (raw little-endian f64 bytes,
// re/im interleaved). Binary, not JSON: JSON.stringify writes -0 as 0 and
// loses the sign bit, making bit-exact comparison impossible. The browser end
// dumps separately via browser/scripts/dump.mjs (real-browser harness).
import { mkdirSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

// Samples resolve relative to this script, not cwd, so the dump runs the
// same from the repo root (test:cross) and from typescript/ (dump:node).
const samplesDir = resolve(import.meta.dirname, "../../oracle/samples");

const out = process.argv[2];
if (!out) {
  console.error("usage: node typescript/scripts/dump.node.mjs <out_dir>");
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

console.log(`dumped ${resolve(join(out, "node", "dut.s2p", "s.bin"))}`);
