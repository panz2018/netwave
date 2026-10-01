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

// wasm side — drive the DIST worker module through a faked worker scope
// (ironclad rule 8: wasm lives only in the resident worker; plain Node has
// no Worker global, so fake `self` and call its onmessage directly — the
// same code path the browser runs).
let resolveReply;
const replied = new Promise((r) => {
  resolveReply = r;
});
globalThis.self = {
  onmessage: null,
  postMessage: (msg) => resolveReply(msg),
};
await import("../dist/netwave.worker.js");
self.onmessage({ data: { id: 1, cmd: "fillPattern", args: [NFREQ, NPORTS] } });
const reply = await replied;
if (reply.error) throw new Error(`worker error: ${reply.error}`);
const wv = new Float64Array(reply.result.buffer, reply.result.byteOffset, reply.result.length * 2);
const wasmPath = join(out, "wasm.bin");
writeFileSync(wasmPath, Buffer.from(wv.buffer, wv.byteOffset, wv.byteLength));

console.log(`dumped ${resolve(nodePath)} ${resolve(wasmPath)}`);
