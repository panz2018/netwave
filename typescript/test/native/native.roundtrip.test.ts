/** Node binding roundtrip test (RED first: `Touchstone.fromData` missing /
 * `get_s` still a `to_vec` copy → red). Data entry is the `fromData`
 * factory (ironclad rule 15 — no bare constructor); zero-copy evidence is
 * the external `s` view written in place and read back through a derived
 * domain (`data("S","MA")`), converted back to RI and compared to the
 * written value (independent channel, ironclad rule 2). Reclamation is
 * `drop()`. */
import { describe, expect, it } from "vitest";
import { Frequency, Touchstone } from "../../src/index.node.ts";

// 1-port S = 0.5+0.25j, z0 = 50 (independent literals, not reused output).
const F = [1.0];
const S0 = [0.5, 0.25];
const Z0 = [50.0];

// MA (mag, deg) back to RI — the independent verification channel.
const maToRi = (mag: number, deg: number): [number, number] => [
  mag * Math.cos((deg * Math.PI) / 180),
  mag * Math.sin((deg * Math.PI) / 180),
];

describe("native roundtrip", () => {
  it("fromData builds; s is a live view; write-through reaches derived readback", () => {
    const f = Frequency.fromF(F, "GHz");
    const ts = Touchstone.fromData(f, S0, Z0, "S");
    // Zero-copy witness 1: the view is the core buffer — writing it and
    // re-reading `s` (a fresh getter call) must show the write. A `to_vec`
    // copy would hand back the untouched 0.5.
    const view = ts.s;
    view[0] = 0.75; // re of the single S entry
    expect(ts.s[0]).toBe(0.75);
    // Zero-copy witness 2 (stronger): the derived MA, computed fresh from
    // the live `s`, converts back to the written value — proves the
    // computation reads through the same memory, not a snapshot.
    const ma = ts.data("S", "MA");
    const [re, im] = maToRi(ma.values[0], ma.values[1]);
    expect(re).toBeCloseTo(0.75, 12);
    expect(im).toBeCloseTo(0.25, 12);
    // z (derived) also reflects the write: Z = z0(1+s)/(1-s) = 150+200j.
    expect(ts.z[0]).toBeCloseTo(150.0, 6);
    ts.drop();
  });

  it("fromData requires parameter (no silent S default)", () => {
    const f = Frequency.fromF(F, "GHz");
    expect(() =>
      (Touchstone as unknown as { fromData(...args: unknown[]): unknown }).fromData(f, S0, Z0),
    ).toThrow();
  });

  it("drop invalidates access; double drop is idempotent", () => {
    const f = Frequency.fromF(F, "GHz");
    const ts = Touchstone.fromData(f, S0, Z0, "S");
    ts.drop();
    expect(() => ts.s).toThrow(/dropped/);
    ts.drop(); // idempotent
  });

  it("CJS twin shell exposes the same fromData contract", async () => {
    const { createRequire } = await import("node:module");
    const require = createRequire(import.meta.url);
    // The CJS twin is a tsdown build artifact (dist/), not a source file.
    const cjs = require("../../dist/index.node.cjs");
    const f = cjs.Frequency.fromF(F, "GHz");
    const ts = cjs.Touchstone.fromData(f, S0, Z0, "S");
    const view = ts.s;
    view[0] = 0.75;
    expect(ts.s[0]).toBe(0.75);
    ts.drop();
  });
});
