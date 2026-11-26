// Build step: extract the cross-end shared values from core and emit a single
// dist/values.generated.mjs for the browser shell. Two kinds of value cross to
// the browser at BUILD time (never at runtime, so the main thread never inits
// wasm — ironclad rule 8):
//   - physical constants: wasm-bindgen cannot export `const` items, so the
//     value is read straight from core/src/constants.rs. Decimal literals parse
//     to the nearest double identically in Rust and JS, so the value is bit-exact.
//   - vocabulary enums (FrequencyUnit / WavelengthUnit): the ordinal a JS caller
//     passes is the variant's declaration index, matching core's
//     `from_ordinal = iter().nth()`. The member names and ordinals are read
//     straight from the core enum definitions.
// In both cases core stays the single definition site (ironclad rule 11); the
// generated file is a mechanical extraction, never a hand-copied table.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";

// Read the `pub const NAME: f64 = ...;` lines from core/src/constants.rs.
function readConstants(src) {
  const consts = [...src.matchAll(/^pub const (\w+): f64 = ([\d_.]+);$/gm)];
  if (consts.length === 0) {
    console.error("gen_values: no `pub const NAME: f64 = ...` found in core/src/constants.rs");
    process.exit(1);
  }
  return consts.map(([, name, value]) => [name, value.replaceAll("_", "")]);
}

// Read the variant names (declaration order = ordinal) of a `pub enum NAME { … }`
// block from core/src/frequency.rs. Only bare `Variant,` lines count: doc
// comments (`///`) and attributes are skipped, so the list tracks the enum body.
function readEnum(src, name) {
  const block = src.match(new RegExp(`pub enum ${name} \\{([\\s\\S]*?)\\n\\}`));
  if (!block) {
    console.error(`gen_values: enum ${name} not found in core/src/frequency.rs`);
    process.exit(1);
  }
  const variants = [...block[1].matchAll(/^\s+([A-Za-z_]\w*),\s*$/gm)].map((m) => m[1]);
  if (variants.length === 0) {
    console.error(`gen_values: enum ${name} has no variants`);
    process.exit(1);
  }
  return variants;
}

const coreDir = join(import.meta.dirname, "../../core/src");
const constants = readConstants(readFileSync(join(coreDir, "constants.rs"), "utf8"));
const frequencyUnit = readEnum(
  readFileSync(join(coreDir, "frequency.rs"), "utf8"),
  "FrequencyUnit",
);
const wavelengthUnit = readEnum(
  readFileSync(join(coreDir, "frequency.rs"), "utf8"),
  "WavelengthUnit",
);

const constLines = constants.map(([name, value]) => `export const ${name} = ${value};`);
const enumLines = [frequencyUnit, wavelengthUnit].map((variants, i) => {
  const name = i === 0 ? "FrequencyUnit" : "WavelengthUnit";
  const members = variants.map((v, ord) => `  ${v}: ${ord},`).join("\n");
  return `export const ${name} = {\n${members}\n};`;
});

const out = join(import.meta.dirname, "../dist/values.generated.mjs");
mkdirSync(dirname(out), { recursive: true });
writeFileSync(
  out,
  `// GENERATED at build time from core/src — do not edit.\n${[...constLines, ...enumLines].join("\n")}\n`,
);

// Types ride the same extraction (tsdown's dts pass resolves the import). The
// enums are numeric-constant objects; each also gets a type alias equal to the
// union of its member values, so callers can annotate a unit parameter exactly
// as they did with the old wasm_bindgen enum type.
const constTypes = constants.map(([name]) => `export declare const ${name}: number;`);
const enumTypes = [frequencyUnit, wavelengthUnit].map((variants, i) => {
  const name = i === 0 ? "FrequencyUnit" : "WavelengthUnit";
  const members = variants.map((v, ord) => `  readonly ${v}: ${ord};`).join("\n");
  return (
    `export declare const ${name}: {\n${members}\n};\n` +
    `export type ${name} = (typeof ${name})[keyof typeof ${name}];`
  );
});
writeFileSync(
  out.replace(/\.mjs$/, ".d.mts"),
  `// GENERATED at build time from core/src — do not edit.\n${[...constTypes, ...enumTypes].join("\n")}\n`,
);
console.log(`generated ${out}`);
