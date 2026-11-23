// Build step (runs after tsdown): rewrite the "../dist/" and ".ts" import
// specifiers inside the dist output to "./" so the browser package is
// self-contained (dist/ holds every artifact), and emit the public dts hub
// (index.d.ts) that tsdown does not generate for a multi-entry build.
// The src/ sources keep "../dist/" and ".ts" specifiers so vitest can run
// against src/ directly (coverage is measured there).
import { readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

const outputs = [
  "index.browser.mjs",
  "standalone.js",
  "netwave.worker.js",
  "index.browser.d.mts",
];

for (const name of outputs) {
  const p = join("dist", name);
  const fixed = readFileSync(p, "utf8")
    .replaceAll('"../dist/', '"./')
    .replaceAll('"./index.browser.ts"', '"./index.browser.mjs"')
    .replaceAll('"./netwave.worker.ts"', '"./netwave.worker.js"');
  writeFileSync(p, fixed);
}

// Public dts hub: the browser package's only public entry is the shell.
writeFileSync(join("dist", "index.d.ts"), 'export * from "./index.browser.mjs";\n');

// Full paths, matching the per-end dump scripts' output format.
for (const name of [...outputs, "index.d.ts"]) {
  console.log(`dumped ${resolve(join("dist", name))}`);
}
