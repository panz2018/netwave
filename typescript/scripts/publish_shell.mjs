// Build step (runs after tsdown + merge_browser): rewrite the "../dist/" and
// ".ts" import specifiers inside the node dist output to "./" so the published
// package is self-contained (dist/ is the only published directory), emit the
// public dts hubs (index.d.ts / index.d.mts) that tsdown does not generate, and
// print the dumped manifest the cross-binding compare scripts consume. The
// browser artifacts merged in by merge_browser are already rewritten by the
// browser package's own publish_shell, so only the node outputs are touched here.
// The src/ sources keep "../dist/" and ".ts" specifiers so vitest can run
// against src/ directly (coverage is measured there).
import { copyFileSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

const outputs = ["index.node.mjs", "index.node.cjs", "index.node.d.mts", "index.node.d.cts"];

for (const name of outputs) {
  const p = join("dist", name);
  let fixed = readFileSync(p, "utf8").replaceAll('"../dist/', '"./');
  // The CJS twin must require the napi CJS glue, not the ESM one.
  if (name.endsWith(".cjs")) {
    fixed = fixed.replaceAll("./index.node.generated.mjs", "./index.node.generated.cjs");
  }
  writeFileSync(p, fixed);
}

// Public dts hubs. The contract is identical on both ends; each hub points
// at the shell matching its module format so TS resolves the right twin.
writeFileSync(join("dist", "index.d.mts"), 'export * from "./index.browser.mjs";\n');
writeFileSync(join("dist", "index.d.ts"), 'export * from "./index.node.cjs";\n');

// Ship both license full texts inside the package (license-compliance
// spec): npm's `files` cannot reference ../, so copy the root licenses into
// the package dir where `files` lists them.
for (const lic of ["LICENSE-MIT", "LICENSE-APACHE"]) {
  copyFileSync(join("..", lic), lic);
}

// Full paths, matching the per-end dump scripts' output format
// ("dumped <absolute path>", one per line).
for (const name of [...outputs, "index.d.ts", "index.d.mts"]) {
  console.log(`dumped ${resolve(join("dist", name))}`);
}
