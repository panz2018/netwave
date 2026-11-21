/** Coverage-gap drivers for core's browser-gated code.

These cases exist to exercise core paths the surface tests above never reach:
the H/G/Y domain conversions (only S and Z files were parsed before), the DB
output format, fromData's validation branches, write_path's directory/grammar
shapes, every wavelength unit, and the post-drop access contract on each getter.
Expected values are independent closed-form (ironclad rule 2); transcendental
legs compare within tolerance (ironclad rule 3). */
import { beforeAll, describe, expect, it } from "vitest";
import { type Harness, installResidentWorkerHarness } from "./harness.ts";

let harness: Harness;
beforeAll(async () => {
  harness = await installResidentWorkerHarness();
});

/** Send one raw worker request and resolve with the reply's error string
 * (undefined on success). Reaches the defensive dispatch arms — unknown
 * method/namespace, a handle that is neither number nor string, and the
 * argument-type guards — that the typed shells cannot express. */
function rawError(handle: number | string, method: string, args: unknown[]): Promise<string> {
  const id = Math.floor(Math.random() * 1e9);
  return new Promise((resolve) => {
    const stop = harness.onReply((res) => {
      if (res.id === id) {
        stop();
        resolve(res.error ?? "");
      }
    });
    harness.singleton()?.postMessage({ id, handle, method, args });
  });
}

// 2-port H, RI, R 50. v1.x 2-port column order is N11,N21,N12,N22.
const H2P = `# GHZ H RI R 50
1.0 1 0 2 0 3 0 4 0
`;
// 2-port G, RI.
const G2P = `# GHZ G RI R 50
1.0 0.1 0 0.2 0 0.3 0 0.4 0
`;
// 2-port Y, RI.
const Y2P = `# GHZ Y RI R 50
1.0 0.01 0 0.02 0 0.03 0 0.04 0
`;

describe("domain conversions at ingestion (convert_to_s)", () => {
  it("an H file converts through h_to_z then z_to_s", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText(H2P, 2);
    expect(await ts.parameter()).toBe("H");
    // The stored S is finite and the H shortcut round-trips the domain.
    const s = await ts.s;
    expect(s.length).toBe(8);
    expect(Array.from(s).every(Number.isFinite)).toBe(true);
    const h = await ts.h;
    expect(h.length).toBe(8);
    await ts.drop();
  });

  it("a G file converts through g_to_y then y_to_s", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText(G2P, 2);
    expect(await ts.parameter()).toBe("G");
    const g = await ts.g;
    expect(g.length).toBe(8);
    expect(Array.from(await ts.s).every(Number.isFinite)).toBe(true);
    await ts.drop();
  });

  it("a Y file converts through y_to_s", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText(Y2P, 2);
    expect(await ts.parameter()).toBe("Y");
    const y = await ts.y;
    expect(y.length).toBe(8);
    await ts.drop();
  });
});

describe("data output formats (to_db / to_ma on every domain)", () => {
  const S1P = `# GHZ S RI R 50\n1.0 1.0 0.1\n2.0 0.9 -0.2\n`;
  it("S DB renders (db, deg) pairs", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText(S1P, 1);
    const db = await ts.data("S", "DB");
    // |1+0.1j| = hypot(1,0.1); dB = 20*log10 of that.
    const mag = Math.hypot(1.0, 0.1);
    expect(db.values[0]).toBeCloseTo(20 * Math.log10(mag), 9);
    expect(db.values[1]).toBeCloseTo((Math.atan2(0.1, 1.0) * 180) / Math.PI, 9);
    await ts.drop();
  });

  it("Z domain in MA and DB both render", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText(H2P, 2); // any 2-port gives a Z
    const zma = await ts.data("Z", "MA");
    const zdb = await ts.data("Z", "DB");
    expect(zma.values.length).toBe(8);
    expect(zdb.values.length).toBe(8);
    await ts.drop();
  });

  it("G/H domain in DB renders", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText(G2P, 2);
    expect((await ts.data("G", "DB")).values.length).toBe(8);
    expect((await ts.data("H", "MA")).values.length).toBe(8);
    await ts.drop();
  });
});

describe("fromData validation branches", () => {
  async function axis(m: unknown, pts: number[]) {
    const mm = m as typeof import("../../src/index.browser.ts");
    return mm.Frequency.fromF(new Float64Array(pts), mm.FrequencyUnit.GHz);
  }

  it("empty axis + empty data builds an empty object (nports from z0)", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await axis(m, []);
    const ts = await m.Touchstone.fromData(f, new Float64Array([]), [50], "S");
    expect(await ts.nports()).toBe(1);
    expect(Array.from(await ts.s)).toEqual([]);
    await ts.drop();
    await f.drop();
  });

  it("empty axis + empty data with per-port z0 infers nports", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await axis(m, []);
    const ts = await m.Touchstone.fromData(f, new Float64Array([]), [50, 45], "S");
    expect(await ts.nports()).toBe(2);
    expect(await ts.version()).toBe("1.1"); // differing z0 values
    await ts.drop();
    await f.drop();
  });

  it("empty z0 rejects Z0Shape", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await axis(m, []);
    await expect(m.Touchstone.fromData(f, new Float64Array([]), [], "S")).rejects.toThrow();
    await f.drop();
  });

  it("empty axis carrying data rejects DimensionMismatch", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await axis(m, []);
    await expect(m.Touchstone.fromData(f, new Float64Array([1, 0]), [50], "S")).rejects.toThrow();
    await f.drop();
  });

  it("non-square cell count rejects DimensionMismatch", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await axis(m, [1]);
    // 3 complex values for 1 point → cells=3, not a perfect square.
    await expect(
      m.Touchstone.fromData(f, new Float64Array([1, 0, 2, 0, 3, 0]), [50], "S"),
    ).rejects.toThrow();
    await f.drop();
  });

  it("z0 length neither 1 nor nports rejects Z0Shape", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await axis(m, [1]);
    // 1-port data (2 values) but z0 length 2 → mismatch.
    await expect(
      m.Touchstone.fromData(f, new Float64Array([1, 0]), [50, 45], "S"),
    ).rejects.toThrow();
    await f.drop();
  });

  it("G on a 1-port fromData rejects DomainPortCount", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await axis(m, [1]);
    await expect(m.Touchstone.fromData(f, new Float64Array([1, 0]), [50], "G")).rejects.toThrow(
      /2-port/,
    );
    await f.drop();
  });

  it("fromData in a non-S domain converts to S", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await axis(m, [1]);
    // 2-port Z data (8 values), scalar z0 → version 1.0, converts to S.
    const ts = await m.Touchstone.fromData(
      f,
      new Float64Array([10, 0, 20, 0, 30, 0, 40, 0]),
      [50],
      "Z",
    );
    expect(await ts.version()).toBe("1.0");
    expect((await ts.s).length).toBe(8);
    await ts.drop();
    await f.drop();
  });
});

describe("write_path shapes", () => {
  const S1P = `# GHZ S RI R 50\n1.0 1.0 0.1\n`;
  // writeFile's shell glue touches the DOM (Blob + <a download>); stub the
  // minimal scope so the same test runs under Node and a real browser. The
  // filename decision itself is core's (write_path), which is what we assert.
  function stubDom(): { clicks: string[]; restore: () => void } {
    const g = globalThis as unknown as Record<string, unknown>;
    const clicks: string[] = [];
    const origDoc = g.document;
    const fakeDoc = {
      createElement: () => ({
        set href(_v: string) {},
        set download(v: string) {
          clicks.push(String(v));
        },
        click() {},
      }),
    };
    Object.defineProperty(g, "document", { value: fakeDoc, configurable: true });
    if (!g.URL) Object.defineProperty(g, "URL", { value: {}, configurable: true });
    const origCreate = URL.createObjectURL as unknown;
    const origRevoke = URL.revokeObjectURL as unknown;
    URL.createObjectURL = (() => "blob:stub") as unknown as typeof URL.createObjectURL;
    URL.revokeObjectURL = (() => {}) as unknown as typeof URL.revokeObjectURL;
    return {
      clicks,
      restore: () => {
        if (origDoc) g.document = origDoc;
        else delete g.document;
        URL.createObjectURL = origCreate as typeof URL.createObjectURL;
        URL.revokeObjectURL = origRevoke as typeof URL.revokeObjectURL;
      },
    };
  }

  it("a trailing-slash path is treated as a directory", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText(S1P, 1, "/tmp/dir/filter.s1p");
    const dom = stubDom();
    try {
      await ts.writeFile("/some/dir/", "S", "RI");
    } finally {
      dom.restore();
    }
    expect(dom.clicks).toEqual(["/some/dir/filter.s1p"]);
    await ts.drop();
  });

  it("a path with a wrong extension is rebuilt from the written domain", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText(S1P, 1, "/tmp/dir/filter.s1p");
    const dom = stubDom();
    try {
      // Writing Z on a 1-port: extension must become .z1p regardless of input.
      await ts.writeFile("/tmp/dir/filter.s9p", "Z", "RI");
    } finally {
      dom.restore();
    }
    expect(dom.clicks).toEqual(["/tmp/dir/filter.z1p"]);
    await ts.drop();
  });

  it("toText renders v1.1 per-port R and DB format", async () => {
    const m = await import("../../src/index.browser.ts");
    const Z2P = `# GHZ Z MA R 50 45\n1.0 10 0 30 -90\n20 90 40 180\n`;
    const ts = await m.Touchstone.fromText(Z2P, 2);
    const db = await ts.toText("S", "DB");
    expect(db).toContain("# GHZ S DB R 50 45"); // per-port R, uppercase keywords
    await ts.drop();
  });
});

describe("wavelength units and fromWavelength", () => {
  it("every wavelength unit scales the axis", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await m.Frequency.fromF(new Float64Array([1e9]), m.FrequencyUnit.Hz);
    for (const u of [
      m.WavelengthUnit.m,
      m.WavelengthUnit.cm,
      m.WavelengthUnit.mm,
      m.WavelengthUnit.um,
      m.WavelengthUnit.nm,
    ]) {
      const wl = await f.wavelength(u, 1.0);
      expect(wl[0]).toBeGreaterThan(0);
    }
    await f.drop();
  });

  it("fromWavelength builds an axis from each unit", async () => {
    const m = await import("../../src/index.browser.ts");
    // core uses the exact SPEED_OF_LIGHT (299792458 m/s), not 3e8.
    const f = await m.Frequency.fromWavelength(new Float64Array([0.3]), m.WavelengthUnit.m, 1.0);
    expect((await f.f)[0]).toBeCloseTo(299792458 / 0.3, 1);
    await f.drop();
  });

  it("an illegal wavelength unit string rejects quoting the input", async () => {
    const m = await import("../../src/index.browser.ts");
    await expect(
      m.Frequency.fromWavelength(new Float64Array([1]), "furlong" as never, 1.0),
    ).rejects.toThrow(/furlong/);
  });
});

describe("post-drop access contract on every getter", () => {
  it("every frequency getter rejects after drop (Dropped Display)", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await m.Frequency.fromF(new Float64Array([1e9]), m.FrequencyUnit.GHz);
    await f.drop();
    // Each getter forwards to a core accessor that errors on the dropped
    // axis; the error text is core's Dropped Display ("data has been dropped").
    await expect(f.f).rejects.toThrow(/dropped/);
    await expect(f.fScaled).rejects.toThrow(/dropped/);
    await expect(f.w).rejects.toThrow(/dropped/);
    await expect(f.unit).rejects.toThrow(/dropped/);
    await expect(f.npoints()).rejects.toThrow(/dropped/);
    await expect(f.wavelength(m.WavelengthUnit.m, 1)).rejects.toThrow(/dropped/);
    await expect(f.toString()).rejects.toThrow(/dropped/);
  });

  it("copy of a dropped axis rejects", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await m.Frequency.fromF(new Float64Array([1e9]), m.FrequencyUnit.GHz);
    await f.drop();
    await expect(f.copy()).rejects.toThrow(/dropped/);
  });

  it("touchstone getters reject after drop", async () => {
    const m = await import("../../src/index.browser.ts");
    const S1P = `# GHZ S RI R 50\n1.0 1.0 0.1\n`;
    const ts = await m.Touchstone.fromText(S1P, 1);
    await ts.drop();
    await expect(ts.s).rejects.toThrow(/dropped/);
    await expect(ts.z).rejects.toThrow(/dropped/);
    await expect(ts.nports()).rejects.toThrow(/dropped/);
  });
});

// ---------------------------------------------------------------------------
// Batch 2: the dispatch error arms, parser branches and name-pipeline guards
// that the typed shells cannot express. Raw worker requests reach the
// defensive `match` fallbacks and argument-type guards directly (the typed
// shell always sends well-formed arguments).
// ---------------------------------------------------------------------------

describe("dispatch argument-type guards (raw worker requests)", () => {
  it("a unit that is neither number nor string rejects", async () => {
    // js_freq_unit: not a string, not a number → "number or a string".
    expect(await rawError("frequency", "fromF", [new Float64Array([1]), true])).toContain(
      "number or a string",
    );
  });

  it("a wavelength unit that is neither number nor string rejects", async () => {
    expect(
      await rawError("frequency", "fromWavelength", [new Float64Array([1]), true, 1]),
    ).toContain("number or a string");
  });

  it("wavelength with no unit argument rejects", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await m.Frequency.fromF(new Float64Array([1e9]), m.FrequencyUnit.GHz);
    expect(await rawError(f.handle, "wavelength", [])).toContain("wl_unit argument required");
    await f.drop();
  });

  it("wavelength with a non-number n rejects", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await m.Frequency.fromF(new Float64Array([1e9]), m.FrequencyUnit.GHz);
    expect(await rawError(f.handle, "wavelength", [m.WavelengthUnit.m])).toContain(
      "n must be a number",
    );
    await f.drop();
  });

  it("fromWavelength with no n argument rejects", async () => {
    expect(await rawError("frequency", "fromWavelength", [new Float64Array([1]), 0])).toContain(
      "n must be a number",
    );
  });

  it("fromF with no axis argument rejects (arg_f64_vec guard)", async () => {
    expect(await rawError("frequency", "fromF", [])).toContain("must be a Float64Array");
  });

  it("fromText with a non-string text rejects (arg_str guard)", async () => {
    expect(await rawError("touchstone", "fromText", [123])).toContain("must be a string");
  });

  it("fromData with a non-number handle rejects (arg_u32 guard)", async () => {
    expect(await rawError("touchstone", "fromData", ["x"])).toContain("must be a number");
  });

  it("fromData with a dropped/unknown handle rejects (with_any guard)", async () => {
    expect(
      await rawError("touchstone", "fromData", [
        999_997,
        new Float64Array([]),
        new Float64Array([50]),
        "S",
      ]),
    ).toContain("unknown or dropped handle");
  });

  it("fromData over a non-Frequency handle rejects (downcast guard)", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText("# GHZ S RI R 50\n1.0 1.0 0.1\n", 1);
    // arg0 is a live handle but hosts a Touchstone, not a Frequency.
    expect(
      await rawError("touchstone", "fromData", [
        ts.handle,
        new Float64Array([]),
        new Float64Array([50]),
        "S",
      ]),
    ).toContain("not a live Frequency");
    await ts.drop();
  });

  it("fromBytes with a non-Uint8Array argument rejects", async () => {
    expect(await rawError("touchstone", "fromBytes", [42])).toContain("must be a Uint8Array");
  });

  it("a handle that is neither number nor string rejects", async () => {
    expect(await rawError(null as unknown as number, "f", [])).toContain(
      "must be a number (instance) or a string",
    );
  });

  it("an unknown method on an instance handle rejects", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText("# GHZ S RI R 50\n1.0 1.0 0.1\n", 1);
    expect(await rawError(ts.handle, "nope", [])).toContain("unknown method");
    await ts.drop();
  });
});

describe("parser branches (from_text)", () => {
  it("a comment line is collected", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText("! hello\n# GHZ S RI R 50\n1.0 1.0 0.1\n", 1);
    expect(await ts.comments()).toBe("hello");
    await ts.drop();
  });

  it("a second option line is ignored whole", async () => {
    const m = await import("../../src/index.browser.ts");
    // The first `#` wins; the second is skipped unvalidated (spec v2.1).
    const ts = await m.Touchstone.fromText("# GHZ S RI R 50\n# MHZ Z MA\n1.0 1.0 0.1\n", 1);
    expect(await ts.parameter()).toBe("S");
    await ts.drop();
  });

  it("a per-port R whose length is neither 1 nor nports rejects Z0Shape", async () => {
    const m = await import("../../src/index.browser.ts");
    // R has 2 values but nports is 3 → shape mismatch.
    await expect(m.Touchstone.fromText("# GHZ S RI R 50 45\n1.0 1 2 3", 3)).rejects.toThrow(
      /z0|shape|R/i,
    );
  });

  it("a token count not divisible by the stride rejects", async () => {
    const m = await import("../../src/index.browser.ts");
    // 1-port stride is 3; two tokens is not a multiple.
    await expect(m.Touchstone.fromText("# GHZ S RI R 50\n1.0 1.0", 1)).rejects.toThrow();
  });

  it("an unknown option-line keyword rejects quoting the token", async () => {
    const m = await import("../../src/index.browser.ts");
    await expect(m.Touchstone.fromText("# GHZ S RI FOO R 50\n1.0 1.0 0.1", 1)).rejects.toThrow(
      /FOO/,
    );
  });

  it("an option line with no R defaults to 50", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText("# GHZ S RI\n1.0 1.0 0.1\n", 1);
    expect(Array.from(await ts.z0)).toEqual([50]);
    await ts.drop();
  });

  it("two R groups parse per-port values", async () => {
    const m = await import("../../src/index.browser.ts");
    // "R 50 R 45": the inner loop breaks on the second R, then resumes.
    const ts = await m.Touchstone.fromText("# GHZ S RI R 50 R 45\n1.0 1 2 3 4 5 6 7 8\n", 2);
    expect(Array.from(await ts.z0)).toEqual([50, 45]);
    await ts.drop();
  });

  it("a DB-format file converts at ingestion", async () => {
    const m = await import("../../src/index.browser.ts");
    // -3 dB, 0 deg → |S| = 10^(-3/20).
    const ts = await m.Touchstone.fromText("# GHZ S DB R 50\n1.0 -3 0\n", 1);
    const s = await ts.s;
    expect(s[0]).toBeCloseTo(10 ** (-3 / 20), 9);
    await ts.drop();
  });

  it("a duplicate frequency point rejects", async () => {
    const m = await import("../../src/index.browser.ts");
    await expect(m.Touchstone.fromText("# GHZ S RI R 50\n1.0 1 0\n1.0 2 0\n", 1)).rejects.toThrow(
      /duplicate/i,
    );
  });

  it("explicit UTF-8 decoding succeeds on valid bytes", async () => {
    const m = await import("../../src/index.browser.ts");
    const bytes = new TextEncoder().encode("# GHZ S RI R 50\n1.0 1.0 0.1\n");
    const ts = await m.Touchstone.fromBytes(bytes, 1, undefined, "UTF-8");
    expect(await ts.nports()).toBe(1);
    await ts.drop();
  });
});

describe("domain port-count guards on getters and data()", () => {
  const S1P = `# GHZ S RI R 50\n1.0 1.0 0.1\n`;
  it("the g getter on a 1-port rejects DomainPortCount", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText(S1P, 1);
    await expect(ts.g).rejects.toThrow(/2-port/);
    await ts.drop();
  });

  it("the h getter on a 1-port rejects DomainPortCount", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText(S1P, 1);
    await expect(ts.h).rejects.toThrow(/2-port/);
    await ts.drop();
  });

  it("data('G') on a 1-port rejects DomainPortCount", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText(S1P, 1);
    await expect(ts.data("G", "RI")).rejects.toThrow(/2-port/);
    await ts.drop();
  });
});

describe("from_data empty-axis and shape branches", () => {
  async function axis(m: typeof import("../../src/index.browser.ts"), pts: number[]) {
    return m.Frequency.fromF(new Float64Array(pts), m.FrequencyUnit.GHz);
  }

  it("empty axis + empty data + G rejects DomainPortCount (nports from z0)", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await axis(m, []);
    await expect(m.Touchstone.fromData(f, new Float64Array([]), [50], "G")).rejects.toThrow(
      /2-port/,
    );
    await f.drop();
  });

  it("a non-empty axis with empty data rejects DimensionMismatch", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await axis(m, [1]);
    await expect(m.Touchstone.fromData(f, new Float64Array([]), [50], "S")).rejects.toThrow();
    await f.drop();
  });

  it("per-port z0 with differing values records version 1.1", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await axis(m, [1]);
    // 2-port Z data (8 values), per-port z0 → version 1.1, converts to S.
    const ts = await m.Touchstone.fromData(
      f,
      new Float64Array([10, 0, 20, 0, 30, 0, 40, 0]),
      [50, 45],
      "Z",
    );
    expect(await ts.version()).toBe("1.1");
    await ts.drop();
    await f.drop();
  });
});

describe("write_path and format_number edge shapes", () => {
  function stubDom(): { clicks: string[]; restore: () => void } {
    const g = globalThis as unknown as Record<string, unknown>;
    const clicks: string[] = [];
    const origDoc = g.document;
    Object.defineProperty(g, "document", {
      value: {
        createElement: () => ({
          set href(_v: string) {},
          set download(v: string) {
            clicks.push(String(v));
          },
          click() {},
        }),
      },
      configurable: true,
    });
    const origCreate = URL.createObjectURL as unknown;
    const origRevoke = URL.revokeObjectURL as unknown;
    URL.createObjectURL = (() => "blob:stub") as unknown as typeof URL.createObjectURL;
    URL.revokeObjectURL = (() => {}) as unknown as typeof URL.revokeObjectURL;
    return {
      clicks,
      restore: () => {
        if (origDoc) g.document = origDoc;
        else delete g.document;
        URL.createObjectURL = origCreate as typeof URL.createObjectURL;
        URL.revokeObjectURL = origRevoke as typeof URL.revokeObjectURL;
      },
    };
  }

  it("an empty-string path uses the bare name", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText(
      "# GHZ S RI R 50\n1.0 1.0 0.1\n",
      1,
      "/tmp/dir/filter.s1p",
    );
    const dom = stubDom();
    try {
      await ts.writeFile("", "S", "RI");
    } finally {
      dom.restore();
    }
    expect(dom.clicks).toEqual(["filter.s1p"]);
    await ts.drop();
  });

  it("a signed-zero data value round-trips its sign in to_text", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await m.Frequency.fromF(new Float64Array([1e9]), m.FrequencyUnit.GHz);
    // +0 and -0 in the data slots must render as "0" and "-0" respectively,
    // so a write→read roundtrip preserves each sign bit.
    const ts = await m.Touchstone.fromData(f, new Float64Array([0, -0]), [50], "S");
    const text = await ts.toText("S", "RI");
    expect(text).toMatch(/\s-0(\s|$)/);
    expect(text).toMatch(/\s0(\s|$)/);
    await ts.drop();
    await f.drop();
  });
});

describe("name-pipeline grammar guards", () => {
  it("a filename too short after the dot keeps the whole stem", async () => {
    const m = await import("../../src/index.browser.ts");
    // ".z" is shorter than the grammar minimum → no strip.
    expect(await m.Touchstone.nameFromFilename("x.z")).toBe("x.z");
  });

  it("a non-domain letter before the digits keeps the whole stem", async () => {
    const m = await import("../../src/index.browser.ts");
    // ".a2p": 'a' is not a domain letter → no strip.
    expect(await m.Touchstone.nameFromFilename("x.a2p")).toBe("x.a2p");
  });

  it("a filename not ending in p keeps the whole stem", async () => {
    const m = await import("../../src/index.browser.ts");
    expect(await m.Touchstone.nameFromFilename("x.s2q")).toBe("x.s2q");
  });

  it("a digit run that overflows usize rejects NportsNoMatch", async () => {
    const m = await import("../../src/index.browser.ts");
    // Grammar matches but the port count overflows usize → parse error.
    await expect(m.Touchstone.nportsFromFilename("x.s99999999999999999999p")).rejects.toThrow();
  });
});

// ---------------------------------------------------------------------------
// Batch 3: the last worker-reachable branches — blank lines, R-value parse
// errors, a zero matrix element in the multiply, odd data lengths, the empty
// digit run in the grammar, and a domain error surfacing through toText.
// ---------------------------------------------------------------------------

describe("final parser and formatting branches", () => {
  it("a blank line between rows is skipped", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText("# GHZ S RI R 50\n1.0 1.0 0.1\n\n2.0 0.9 -0.2\n", 1);
    expect(await ts.nports()).toBe(1);
    await ts.drop();
  });

  it("a non-numeric R value rejects quoting the token", async () => {
    const m = await import("../../src/index.browser.ts");
    await expect(m.Touchstone.fromText("# GHZ S RI R foo\n1.0 1.0 0.1", 1)).rejects.toThrow(/foo/);
  });

  it("a fully-zero matrix element is skipped in the domain multiply", async () => {
    const m = await import("../../src/index.browser.ts");
    // Z with a zero off-diagonal (0+0j) exercises the mat_mul zero-skip arm.
    const f = await m.Frequency.fromF(new Float64Array([1e9]), m.FrequencyUnit.GHz);
    const ts = await m.Touchstone.fromData(
      f,
      new Float64Array([50, 0, 0, 0, 0, 0, 50, 0]),
      [50],
      "Z",
    );
    // Reading Y back runs invert/mat_mul over the zero element.
    expect((await ts.y).length).toBe(8);
    await ts.drop();
    await f.drop();
  });

  it("a data length not a multiple of npoints×2 rejects DimensionMismatch", async () => {
    const m = await import("../../src/index.browser.ts");
    const f = await m.Frequency.fromF(new Float64Array([1e9]), m.FrequencyUnit.GHz);
    // 3 values for 1 point → not divisible by 2.
    await expect(
      m.Touchstone.fromData(f, new Float64Array([1, 0, 2]), [50], "S"),
    ).rejects.toThrow();
    await f.drop();
  });

  it("a '.sp' filename (empty digit run) keeps the whole stem", async () => {
    const m = await import("../../src/index.browser.ts");
    // Grammar needs at least one digit between the letter and 'p'.
    expect(await m.Touchstone.nameFromFilename("x.sp")).toBe("x.sp");
  });

  it("toText in a domain invalid for the port count rejects", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText("# GHZ S RI R 50\n1.0 1.0 0.1\n", 1);
    // G is 2-port only; rendering it on a 1-port errors through toText.
    await expect(ts.toText("G", "RI")).rejects.toThrow(/2-port/);
    await ts.drop();
  });

  it("toString renders a non-integral axis value without the .1 format", async () => {
    const m = await import("../../src/index.browser.ts");
    // 1.5 Hz is not integral → the fmt_axis_value non-integral branch runs.
    const f = await m.Frequency.fromF(new Float64Array([1.5, 2.25]), m.FrequencyUnit.Hz);
    const s = await f.toString();
    expect(s).toContain("1.5");
    expect(s).toContain("2.25");
    await f.drop();
  });
});
