// Build step: extract physical constants from core/src/constants.rs and emit
// dist/constants.generated.mjs for the browser shell. wasm-bindgen cannot
// export constants (its parser rejects ItemConst), and the main thread must
// never init wasm (ironclad rule 8), so the value crosses to the browser at
// BUILD time: core stays the single definition site (ironclad rule 11), the
// generated file is a mechanical extraction, never a hand-copied table.
// Decimal literals parse to the nearest double identically in Rust and JS,
// so the extracted value is bit-exact.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

const core = readFileSync(join(import.meta.dirname, "../../core/src/constants.rs"), "utf8");
const consts = [...core.matchAll(/^pub const (\w+): f64 = ([\d_.]+);$/gm)];
if (consts.length === 0) {
  console.error("gen_constants: no `pub const NAME: f64 = ...` found in core/src/constants.rs");
  process.exit(1);
}
const body = consts
  .map(([, name, value]) => `export const ${name} = ${value.replaceAll("_", "")};`)
  .join("\n");
const out = join(import.meta.dirname, "../dist/constants.generated.mjs");
mkdirSync(dirname(out), { recursive: true });
writeFileSync(
  out,
  `// GENERATED at build time from core/src/constants.rs — do not edit.\n${body}\n`,
);
// Types ride the same extraction (tsdown's dts pass resolves the import).
const types = consts.map(([, name]) => `export declare const ${name}: number;`).join("\n");
writeFileSync(
  `${out.replace(/\.mjs$/, ".d.mts")}`,
  `// GENERATED at build time from core/src/constants.rs — do not edit.\n${types}\n`,
);
console.log(`generated ${out}`);
