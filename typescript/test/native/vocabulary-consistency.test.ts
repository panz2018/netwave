/** Cross-end vocabulary consistency (spec: frequency-unit "vocabulary
 * single source" / "三端成员集合相等").
 *
 * The runtime three-end equality is already pinned by the per-end tests
 * (native / wasm / python each assert the same independent CANONICAL
 * list). This test closes the remaining gap: the *generated type
 * artifacts* — the Python `.pyi` and the two TypeScript `.d.ts` — must
 * carry the identical member-name set, so a stale build artifact (an
 * end rebuilt after a core rename) trips CI here rather than shipping a
 * drifted `.d.ts`.
 *
 * Reads the build outputs directly (no hand-copied vocabulary): each
 * artifact's member set is extracted from its own enum/class block. */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const read = (rel: string) => readFileSync(fileURLToPath(new URL(rel, import.meta.url)), "utf8");

/** Strip `/* *\/` and `//` comments so a doc line mentioning a name never
 * counts as a member. */
const stripComments = (src: string) =>
  src.replace(/\/\*[\s\S]*?\*\//g, "").replace(/\/\/.*$/gm, "");

/** TS enum members: the `Name = ...` lines inside the `enum FrequencyUnit`
 * block (delimited by braces). */
const tsMembers = (src: string): string[] => {
  const code = stripComments(src);
  const open = code.search(/enum FrequencyUnit\b/);
  if (open < 0) throw new Error("FrequencyUnit enum not found");
  const body = code.slice(open, code.indexOf("}", open));
  return [...body.matchAll(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=/gm)].map((m) => m[1]);
};

/** Python class members: the 4-space-indented `Name = ...` lines under
 * `class FrequencyUnit`. Blank lines and docstring prose (also 4-space
 * indented) are skipped; the body ends at the first dedented line (the
 * next top-level `def`/`class`/decorator) — a Python class has no closing
 * brace. */
const pyMembers = (src: string): string[] => {
  const lines = src.split("\n");
  const start = lines.findIndex((l) => /^class FrequencyUnit\b/.test(l));
  if (start < 0) throw new Error("FrequencyUnit class not found");
  const out: string[] = [];
  for (const line of lines.slice(start + 1)) {
    // pyo3-stub-gen emits every enum member as `    Name = ...`; the
    // literal `...` value distinguishes members from docstring prose.
    const member = line.match(/^ {4}([A-Za-z_][A-Za-z0-9_]*) = \.\.\./);
    if (member) out.push(member[1]);
    else if (line.trim() === "" || /^ {4}/.test(line))
      continue; // blank / docstring
    else break; // dedented: next top-level definition
  }
  return out;
};

const CANONICAL = ["Hz", "kHz", "MHz", "GHz", "THz"];

describe("generated type artifacts carry identical vocabulary", () => {
  it("python .pyi members match core", () => {
    expect(pyMembers(read("../../../python/netwave/_netwave.pyi"))).toEqual(CANONICAL);
  });

  it("node .d.mts members match core", () => {
    expect(tsMembers(read("../../dist/index.node.generated.d.mts"))).toEqual(CANONICAL);
  });

  it("wasm .d.ts members match core", () => {
    expect(tsMembers(read("../../dist/wasm-web/netwave_wasm.d.ts"))).toEqual(CANONICAL);
  });

  it("all three generated artifacts agree with each other", () => {
    const pyi = pyMembers(read("../../../python/netwave/_netwave.pyi"));
    const node = tsMembers(read("../../dist/index.node.generated.d.mts"));
    const wasm = tsMembers(read("../../dist/wasm-web/netwave_wasm.d.ts"));
    expect(node).toEqual(pyi);
    expect(wasm).toEqual(pyi);
  });
});
