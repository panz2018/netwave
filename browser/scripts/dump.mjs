#!/usr/bin/env node
// Browser-end cross-binding dump: drive the PUBLISHED shell in a REAL browser
// (playwright + Chromium) — ironclad rule 8 / zero-copy-roundtrip spec: the
// browser path is verified in a real browser, never a node-simulated worker.
// A static server mounts the built shell (`browser/dist/`) and the shared
// samples (`oracle/samples/`); the page imports `index.browser.mjs` (main
// thread runs no wasm — compute goes through the resident worker, the same
// code path production uses). Sample bytes are fed in via a File through the
// real `fromFile` entry; the S master data, z0 and version come back through
// the shell getters (the historical dump contract — NOT the unshipped
// `to_file`/`writeFile` text-export path). Usage (from repo root):
//   node browser/scripts/dump.mjs <out_dir>
// Emits <out>/browser/freq.bin and <out>/browser/<sample>/s.bin|z0.bin|
// version.txt (raw little-endian f64, re/im interleaved — binary not JSON so
// the sign bit survives; oracle/compare_cross.py grades against the native ends).
import { createServer } from "node:http";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { extname, join, resolve } from "node:path";
import { chromium } from "playwright";

// Samples and artifacts resolve relative to this script, not cwd, so the dump
// runs identically from the repo root (test:cross) and browser/ (pnpm dump).
const repoRoot = resolve(import.meta.dirname, "../..");
const distDir = join(repoRoot, "browser", "dist");
const samplesDir = join(repoRoot, "oracle", "samples");

// Default output dir resolves relative to this script (repo root oracle/tmp),
// so `pnpm -C browser dump` works from any cwd; test_cross.sh passes an
// explicit path instead.
const out = process.argv[2] ?? resolve(repoRoot, "oracle/tmp");
mkdirSync(join(out, "browser"), { recursive: true });

// The page runs the shell and exposes two async probes; results cross back to
// node as plain arrays (structured clone), rebuilt into Float64Array on disk.
const PAGE = `<!doctype html><html><body><script type="module">
import * as m from "/index.browser.mjs";
// lambda<->f round-trip axis (spec: frequency-class): f -> wavelength -> f.
window.__freq = async () => {
  const f = await m.Frequency.fromF(new Float64Array([1.0, 2.0, 5.0]), m.FrequencyUnit.GHz);
  const wl = await f.wavelength(m.WavelengthUnit.mm, 2.2);
  const back = await m.Frequency.fromWavelength(Array.from(wl), m.WavelengthUnit.mm, 2.2);
  return Array.from(await back.f);
};
// Parse one shared sample through the real File entry; read S/z0/version back.
window.__ts = async (name) => {
  const buf = await (await fetch("/samples/" + name)).arrayBuffer();
  const ts = await m.Touchstone.fromFile(new File([buf], name));
  return { s: Array.from(await ts.s), z0: Array.from(await ts.z0), version: await ts.version() };
};
</script></body></html>`;

const MIME = {
  ".js": "text/javascript",
  ".mjs": "text/javascript",
  ".wasm": "application/wasm",
  ".html": "text/html",
};

const server = createServer(async (req, res) => {
  try {
    const { readFile } = await import("node:fs/promises");
    const url = req.url.split("?")[0];
    if (url === "/" || url === "/probe.html") {
      res.writeHead(200, { "content-type": "text/html" });
      res.end(PAGE);
      return;
    }
    const file = url.startsWith("/samples/")
      ? join(samplesDir, url.slice("/samples/".length))
      : join(distDir, url);
    const body = await readFile(file);
    res.writeHead(200, { "content-type": MIME[extname(file)] ?? "application/octet-stream" });
    res.end(body);
  } catch {
    res.writeHead(404).end("not found");
  }
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const port = server.address().port;

const writeF64 = (path, values) => {
  const a = new Float64Array(values);
  writeFileSync(path, Buffer.from(a.buffer, a.byteOffset, a.byteLength));
};

const browser = await chromium.launch();
try {
  const page = await browser.newPage();
  await page.goto(`http://127.0.0.1:${port}/probe.html`);

  // lambda<->f axis.
  const axis = await page.evaluate(() => window.__freq());
  writeF64(join(out, "browser", "freq.bin"), axis);

  // Touchstone samples: s/z0/version per sample (names match the node end).
  for (const c of ["s1p", "s2p", "s4p"]) {
    const sample = `dut.${c}`;
    const { s, z0, version } = await page.evaluate((n) => window.__ts(n), sample);
    const dir = join(out, "browser", sample.replace(/ /g, "_"));
    mkdirSync(dir, { recursive: true });
    writeF64(join(dir, "s.bin"), s);
    writeF64(join(dir, "z0.bin"), z0);
    writeFileSync(join(dir, "version.txt"), version);
  }
} finally {
  await browser.close();
  server.close();
}

console.log(`dumped ${resolve(join(out, "browser", "freq.bin"))}`);
