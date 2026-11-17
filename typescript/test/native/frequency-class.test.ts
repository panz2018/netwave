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

  it("fromWavelength accepts a string unit", () => {
    // `resolve_wl_unit` Either::B arm: a string crosses as the string variant
    // (core FromStr), not only the numeric enum ordinal.
    const f = Frequency.fromWavelength([60.0], "mm", 2.2);
    const want = 299_792_458.0 / (2.2 * 0.06);
    expect(f.f[0]).toBe(want);
  });

  it("wavelength accepts a string unit matching the enum", () => {
    const f = Frequency.fromF([1e9, 2e9], "Hz");
    const byStr = f.wavelength("mm", 2.2);
    const byEnum = f.wavelength(WavelengthUnit.mm, 2.2);
    expect(Array.from(byStr)).toEqual(Array.from(byEnum));
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

  it("npoints returns the point count", () => {
    const f = Frequency.fromF([1.0, 2.0, 3.0], "GHz");
    expect(f.npoints()).toBe(3);
  });

  it("fromF rejects an out-of-range numeric unit ordinal", () => {
    // `resolve_freq_unit` Either::A arm past the last enum member: the
    // numeric ordinal has no `from_ordinal` match, so the ok_or_else arm
    // throws instead of silently defaulting.
    expect(() => Frequency.fromF([1.0], 99 as unknown as FrequencyUnit)).toThrow(/ordinal/);
  });

  it("fromWavelength rejects an out-of-range numeric unit ordinal", () => {
    expect(() => Frequency.fromWavelength([60.0], 99 as unknown as WavelengthUnit, 1.0)).toThrow(
      /ordinal/,
    );
  });

  it("accessors throw after drop", () => {
    const f = Frequency.fromF([1.0], "GHz");
    f.drop();
    expect(() => f.f).toThrow();
    expect(() => f.npoints()).toThrow();
    expect(() => f.fScaled).toThrow();
    expect(() => f.unit).toThrow();
    expect(() => f.wavelength("mm", 1.0)).toThrow();
    expect(() => f.copy()).toThrow();
  });
});
