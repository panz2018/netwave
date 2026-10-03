/** Node binding vocabulary test (RED first: shell lacks the export → red).
 *
 * Expected names are independent literals (spec: frequency-unit "vocabulary
 * single source"); if core renames a variant this test trips — its job as a
 * contract tripwire, not hand-copied drift (grep gate exempts tests). */
import { describe, expect, it } from "vitest";
import { FrequencyUnit, frequencyUnits } from "../../src/index.node.ts";

const CANONICAL = ["Hz", "kHz", "MHz", "GHz", "THz"];

describe("native frequency unit vocabulary", () => {
  it("frequencyUnits() returns the five canonical names in order", () => {
    expect(frequencyUnits()).toEqual(CANONICAL);
  });

  it("FrequencyUnit member names match core exactly", () => {
    // napi defines members as non-enumerable own properties, so Object.keys
    // is empty; getOwnPropertyNames yields exactly the member names.
    const members = Object.getOwnPropertyNames(FrequencyUnit);
    expect(members.sort()).toEqual([...CANONICAL].sort());
  });

  it("unknown member is a compile-time error", () => {
    // @ts-expect-error Hzz is not a FrequencyUnit member (proves the .d.ts
    // carries the real member set, not `any`).
    expect(FrequencyUnit.Hzz).toBeUndefined();
  });
});
