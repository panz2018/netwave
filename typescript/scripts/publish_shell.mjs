// Build step: copy the source shells into dist/ and rewrite their
// "../dist/" import specifiers to "./" so the published package is
// self-contained (dist/ is the only published directory).
// The src/ copies keep "../dist/" so tests can run against src/ directly
// (coverage is measured on src/).
import { copyFileSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

const shells = [
  "index.node.mjs",
  "index.node.cjs",
  "index.browser.mjs",
  "standalone.js",
  "netwave.worker.js",
];

for (const name of shells) {
  copyFileSync(join("src", name), join("dist", name));
  const p = join("dist", name);
  const fixed = readFileSync(p, "utf8").replaceAll('"../dist/', '"./');
  writeFileSync(p, fixed);
}
// Public consumer types (overwrite the napi-generated low-level d.ts).
copyFileSync(join("src", "index.d.ts"), join("dist", "index.d.ts"));
// Full paths, matching the per-end dump scripts' output format
// ("dumped <absolute path>", one per line).
for (const name of [...shells, "index.d.ts"]) {
  console.log(`dumped ${resolve(join("dist", name))}`);
}
