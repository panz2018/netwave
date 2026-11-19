// dts glue typing gate: tsdown silently emits `any` for re-exported verbs when
// a generated glue (napi or wasm-web) is missing at dts time. Fail fast instead
// of shipping degraded types. Checks the published shell declarations for
// any-typed exports. Run after build:wasm + build:native (the glues must exist).
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const targets = ["index.browser.d.mts", "index.node.d.mts"].map((f) => join(here, "..", "dist", f));

let failed = false;
for (const file of targets) {
  let text;
  try {
    text = readFileSync(file, "utf8");
  } catch {
    console.error(`::error::${file} not found - shells were not built`);
    failed = true;
    continue;
  }
  const hits = text
    .split("\n")
    .map((line, i) => [i + 1, line])
    .filter(([, line]) => line.includes(": any"));
  if (hits.length > 0) {
    console.error(`::error::${file} has any-typed exports - glues were not built before tsdown`);
    for (const [lineNo, line] of hits) {
      console.error(`  ${file}:${lineNo}: ${line.trim()}`);
    }
    failed = true;
  }
}

if (failed) {
  process.exit(1);
}
console.log(`dts any check OK: ${targets.length} shell declarations free of any-typed exports`);
