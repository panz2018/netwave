/** Node binding constant test: the napi const re-export of the core
 * constant. Expected value is an independent literal (SI exact; exact
 * constants never ride manifest tolerances — bit-exact). */
import { describe, expect, it } from "vitest";
import { SPEED_OF_LIGHT } from "../../src/index.node.ts";

/** The f64 bytes of a value (little-endian), for bit-level comparison. */
const f64Bytes = (v: number): number[] => {
  const view = new DataView(new ArrayBuffer(8));
  view.setFloat64(0, v);
  return [...new Uint8Array(view.buffer)];
};

describe("native SPEED_OF_LIGHT", () => {
  it("equals the SI exact value bit for bit", () => {
    expect(SPEED_OF_LIGHT).toBe(299_792_458);
    expect(f64Bytes(SPEED_OF_LIGHT)).toEqual(f64Bytes(299_792_458));
  });
});
