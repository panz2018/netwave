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
const { fillPattern } = await import("../dist/index.node.mjs");
const n = await fillPattern(NFREQ, NPORTS);
const nv = new Float64Array(n.buffer, n.byteOffset, n.length * 2);
const nodePath = join(out, "node.bin");
writeFileSync(nodePath, Buffer.from(nv.buffer, nv.byteOffset, nv.byteLength));

// wasm side (web-target glue needs async init; call the async verb first)
const { fillPattern: wfp } = await import("../dist/index.browser.mjs");
const w = await wfp(NFREQ, NPORTS);
const wv = new Float64Array(w.buffer, w.byteOffset, w.length * 2);
const wasmPath = join(out, "wasm.bin");
writeFileSync(wasmPath, Buffer.from(wv.buffer, wv.byteOffset, wv.byteLength));

console.log(`dumped ${resolve(nodePath)} ${resolve(wasmPath)}`);
