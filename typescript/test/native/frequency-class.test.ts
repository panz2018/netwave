/** Node functional surface.
 *
 * Expected values are independent literals / closed-form (ironclad rule 2).
 * Same-machine round-trips are bit-exact; the manifest core_tol governs the
 * cross-platform (wasm) leg only (ironclad rule 3). */
import { inspect } from "node:util";

import { describe, expect, it } from "vitest";
import { Frequency, FrequencyUnit, WavelengthUnit } from "../../src/index.node.ts";

describe("native frequency functional surface", () => {
  it("fromF multiplies by unit into Hz", () => {
    const f = Frequency.fromF([1.0, 2.0, 5.0], "GHz");
    expect(Array.from(f.f)).toEqual([1e9, 2e9, 5e9]);
  });

  it("fromF accepts the enum member too", () => {
    const f = Frequency.fromF([1.0], FrequencyUnit.GHz);
    expect(Array.from(f.f)).toEqual([1e9]);
  });

  it("f is a copy isolated from core", () => {
    const f = Frequency.fromF([1.0, 2.0], "GHz");
    const a = f.f;
    a[0] = 0.0;
    expect(f.f[0]).toBe(1e9);
  });

  it("fScaled follows unit", () => {
    const f = Frequency.fromF([1.0, 2.0, 5.0], "GHz");
    expect(Array.from(f.fScaled)).toEqual([1.0, 2.0, 5.0]);
  });

  it("w is 2πf", () => {
    const f = Frequency.fromF([1.0, 2.0], "Hz");
    const tau = Math.PI * 2;
    expect(Array.from(f.w)).toEqual([tau, 2 * tau]);
  });

  it("unit getter returns the numeric enum member", () => {
    const f = Frequency.fromF([1.0], "GHz");
    expect(f.unit).toBe(FrequencyUnit.GHz);
  });

  it("unit setter is case-insensitive and leaves f untouched", () => {
    const f = Frequency.fromF([1.0], "GHz");
    f.unit = "mhz";
    expect(f.unit).toBe(FrequencyUnit.MHz);
    expect(f.f[0]).toBe(1e9);
    expect(Array.from(f.fScaled)).toEqual([1e3]);
  });

  it("unit setter illegal string quotes the input", () => {
    const f = Frequency.fromF([1.0], "GHz");
    expect(() => {
      f.unit = "Hzz";
    }).toThrow(/Hzz/);
  });

  it("wavelength round-trips to Hz", () => {
    const coreTol = 1e-12;
    const f = Frequency.fromF([1e9, 2e9, 5e9], "Hz");
    const wl = f.wavelength(WavelengthUnit.mm, 2.2);
    const back = Frequency.fromWavelength(Array.from(wl), WavelengthUnit.mm, 2.2);
    back.f.forEach((got, i) => {
      const want = [1e9, 2e9, 5e9][i] as number;
      expect(Math.abs(got - want)).toBeLessThanOrEqual(coreTol * want);
    });
  });

  it("wavelength DC is Infinity", () => {
    const f = Frequency.fromF([0.0, 1e9], "Hz");
    const wl = f.wavelength(WavelengthUnit.m, 1.0);
    expect(Number.isFinite(wl[0])).toBe(false);
    expect(Number.isNaN(wl[0])).toBe(false);
  });

  it("fromWavelength computes Hz", () => {
    const f = Frequency.fromWavelength([60.0], WavelengthUnit.mm, 2.2);
    const want = 299_792_458.0 / (2.2 * 0.06);
    expect(f.f[0]).toBe(want);
  });

  it("copy is independent and equal", () => {
    const f = Frequency.fromF([1.0, 2.0], "GHz");
    const c = f.copy();
    expect(Array.from(c.f)).toEqual(Array.from(f.f));
    expect(c.unit).toBe(FrequencyUnit.GHz);
  });

  it("toString + inspect hook emit the display string", () => {
    const f = Frequency.fromF([1.0, 2.0, 5.0], "GHz");
    expect(f.toString()).toBe("Frequency(1.0-5.0 GHz, 3 pts)");
    // console.log path: util.inspect picks up the custom symbol hook.
    expect(inspect(f)).toBe("Frequency(1.0-5.0 GHz, 3 pts)");
    const empty = Frequency.fromF([], "Hz");
    expect(empty.toString()).toBe("Frequency([no freqs])");
  });

  it("accessors throw after drop", () => {
    const f = Frequency.fromF([1.0], "GHz");
    f.drop();
    expect(() => f.f).toThrow();
    expect(() => f.npoints()).toThrow();
  });
});
