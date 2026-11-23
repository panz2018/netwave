/** Browser functional surface roundtrip.
 *
 * Runs under Node (fake worker harness) AND a real browser unchanged.
 * Expected values are independent literals / closed-form (ironclad rule 2).
 * The λ↔f roundtrip crosses the worker realm, so it references the manifest
 * core_tol (relative); the constant is exact (ironclad rule 3). */
import { beforeAll, describe, expect, it } from "vitest";
import { type Harness, installResidentWorkerHarness } from "./harness.ts";

let h: Harness;

beforeAll(async () => {
  h = await installResidentWorkerHarness();
});

describe("browser frequency functional surface", () => {
  it("fromF multiplies by unit into Hz", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await m.Frequency.fromF(new Float64Array([1.0, 2.0, 5.0]), m.FrequencyUnit.GHz);
    expect(Array.from(await f.f)).toEqual([1e9, 2e9, 5e9]);
    expect(await f.npoints()).toBe(3);
    await f.drop();
  });

  it("fScaled follows unit", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await m.Frequency.fromF(new Float64Array([1.0, 2.0, 5.0]), m.FrequencyUnit.GHz);
    expect(Array.from(await f.fScaled)).toEqual([1.0, 2.0, 5.0]);
    await f.drop();
  });

  it("w is 2πf", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await m.Frequency.fromF(new Float64Array([1.0, 2.0]), m.FrequencyUnit.Hz);
    const tau = Math.PI * 2;
    expect(Array.from(await f.w)).toEqual([tau, 2 * tau]);
    await f.drop();
  });

  it("unit getter + setter roundtrip (FIFO worker)", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await m.Frequency.fromF(new Float64Array([1.0]), m.FrequencyUnit.GHz);
    expect(await f.unit).toBe(m.FrequencyUnit.GHz);
    f.unit = m.FrequencyUnit.MHz; // fire-and-forget; FIFO worker
    expect(await f.unit).toBe(m.FrequencyUnit.MHz); // observed after setUnit
    expect(Array.from(await f.f)).toEqual([1e9]); // master data untouched
    await f.drop();
  });

  it("illegal unit string rejects quoting the input", async () => {
    const m = await import("../../src/index.browser.ts");
    // The setter is fire-and-forget (worker boundary, ironclad rule 8), so
    // the error contract is observable on the awaited factory path instead:
    // fromF with an illegal unit string rejects, quoting the input.
    await expect(m.Frequency.fromF(new Float64Array([1.0]), "Hzz" as never)).rejects.toThrow(/Hzz/);
  });

  it("setter swallows an illegal unit rejection (fire-and-forget)", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await m.Frequency.fromF(new Float64Array([1.0]), m.FrequencyUnit.GHz);
    // The setter's .catch(() => {}) must run when the worker rejects the
    // illegal unit (no unhandled rejection escapes to the test runner).
    f.unit = "Hzz" as never;
    await new Promise((r) => setTimeout(r, 0)); // let the rejection settle
    expect(await f.unit).toBe(m.FrequencyUnit.GHz); // unit unchanged
    await f.drop();
  });

  it("wavelength round-trips to Hz (manifest core_tol)", async () => {
    const m = await import("../../src/index.browser.ts");
    const coreTol = 1e-12;
    const f = await m.Frequency.fromF(new Float64Array([1e9, 2e9, 5e9]), m.FrequencyUnit.Hz);
    const wl = await f.wavelength(m.WavelengthUnit.mm, 2.2);
    const back = await m.Frequency.fromWavelength(wl, m.WavelengthUnit.mm, 2.2);
    const got = await back.f;
    [1e9, 2e9, 5e9].forEach((want, i) => {
      expect(Math.abs((got[i] as number) - want)).toBeLessThanOrEqual(coreTol * want);
    });
    await f.drop();
    await back.drop();
  });

  it("wavelength DC is Infinity", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await m.Frequency.fromF(new Float64Array([0.0, 1e9]), m.FrequencyUnit.Hz);
    const wl = await f.wavelength(m.WavelengthUnit.m, 1.0);
    expect(Number.isFinite(wl[0] as number)).toBe(false);
    expect(Number.isNaN(wl[0] as number)).toBe(false);
    await f.drop();
  });

  it("copy is independent and equal", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await m.Frequency.fromF(new Float64Array([1.0, 2.0]), m.FrequencyUnit.GHz);
    const c = await f.copy();
    expect(Array.from(await c.f)).toEqual([1e9, 2e9]);
    expect(await c.unit).toBe(m.FrequencyUnit.GHz);
    await f.drop();
    await c.drop();
  });

  it("async toString emits the display string", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await m.Frequency.fromF(new Float64Array([1.0, 2.0, 5.0]), m.FrequencyUnit.GHz);
    expect(await f.toString()).toBe("Frequency(1.0-5.0 GHz, 3 pts)");
    const empty = await m.Frequency.fromF(new Float64Array([]), m.FrequencyUnit.Hz);
    expect(await empty.toString()).toBe("Frequency([no freqs])");
    await f.drop();
    await empty.drop();
    expect(h.workerInstances()).toBe(1);
  });

  it("accessors reject after drop", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await m.Frequency.fromF(new Float64Array([1.0]), m.FrequencyUnit.GHz);
    await f.drop();
    await expect(f.f).rejects.toThrow();
    await expect(f.npoints()).rejects.toThrow();
  });
});
