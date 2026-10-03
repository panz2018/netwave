/** Browser binding vocabulary test (RED first: shell lacks the export → red).
 *
 * Runs unmodified under Node (fake worker) AND a real browser via the shared
 * harness. `frequencyUnits()` is async (resident-worker command, ironclad
 * rule 8: the main thread never runs wasm); `FrequencyUnit` is a numeric
 * constant re-exported from the glue (importing a constant does not init
 * wasm). Expected names are independent literals (spec: frequency-unit
 * "vocabulary single source") — a rename trips this test by design. */
import { beforeAll, describe, expect, it } from "vitest";
import { installResidentWorkerHarness } from "./harness.ts";

const CANONICAL = ["Hz", "kHz", "MHz", "GHz", "THz"];

beforeAll(async () => {
  await installResidentWorkerHarness();
});

describe("browser frequency unit vocabulary", () => {
  it("await frequencyUnits() returns the five canonical names in order", async () => {
    const m = await import("../../src/index.browser.ts");
    expect(await m.frequencyUnits()).toEqual(CANONICAL);
  });

  it("FrequencyUnit member names match core exactly", async () => {
    const m = await import("../../src/index.browser.ts");
    // wasm-bindgen emits a bidirectional enum object: named members map to
    // numbers (`kHz: 1`) AND numbers map back to names (`"1": "kHz"`).
    // Keep only the named members (numeric keys are the reverse map).
    const members = Object.getOwnPropertyNames(m.FrequencyUnit).filter((k) => !/^\d+$/.test(k));
    expect(members.sort()).toEqual([...CANONICAL].sort());
  });

  it("unknown member is a compile-time error", async () => {
    const m = await import("../../src/index.browser.ts");
    // @ts-expect-error Hzz is not a FrequencyUnit member (proves the .d.ts
    // carries the real member set, not `any`).
    expect(m.FrequencyUnit.Hzz).toBeUndefined();
  });
});
