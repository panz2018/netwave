/** Browser Touchstone surface.
 *
 * Runs under Node (fake worker harness) AND a real browser unchanged.
 * Expected values are independent literals / closed-form (ironclad rule 2);
 * MA→rect is transcendental so those legs compare within core_tol
 * (ironclad rule 3). */
import { beforeAll, describe, expect, it } from "vitest";
import { installResidentWorkerHarness } from "./harness.ts";

beforeAll(async () => {
  await installResidentWorkerHarness();
});

const S1P = `! comment one
# GHZ S RI R 50
1.0 1.0 0.1
2.0 0.9 -0.2
`;

// 2-port Z, v1.1 per-port R, MA: z11=10∠0 z12=20∠90 z21=30∠-90 z22=40∠180.
// v1.x 2-port files use legacy order (z11, z21, z12, z22).
const Z2P = `# GHZ Z MA R 50 45
1.0 10 0 30 -90
20 90 40 180
`;

describe("browser touchstone factories", () => {
  it("fromText routes through the touchstone namespace", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText(S1P, 1, "/tmp/dir/filter.s1p");
    expect(await ts.nports()).toBe(1);
    expect(await ts.name()).toBe("filter");
    expect(await ts.version()).toBe("1.0");
    expect(await ts.parameter()).toBe("S");
    expect(await ts.comments()).toBe("comment one");
    expect(Array.from(await ts.f)).toEqual([1e9, 2e9]);
    expect(Array.from(await ts.z0)).toEqual([50.0]);
    expect(Array.from(await ts.s)).toEqual([1.0, 0.1, 0.9, -0.2]);
    await ts.drop();
  });

  it("fromText infers nports from the path grammar", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText(S1P, undefined, "/x/a.s1p");
    expect(await ts.nports()).toBe(1);
    await ts.drop();
  });

  it("parse errors reject quoting the offending token", async () => {
    const m = await import("../../src/index.browser.ts");
    await expect(m.Touchstone.fromText("# GHZ S RI R 50\n1.0 abc 0.1\n", 1)).rejects.toThrow(/abc/);
  });

  it("fromFile transfers the bytes (buffer detached afterwards)", async () => {
    const m = await import("../../src/index.browser.ts");
    const bytes = new TextEncoder().encode(Z2P);
    const buf = bytes.buffer as ArrayBuffer;
    const ts = await m.Touchstone.fromFile({
      name: "dut.s2p",
      arrayBuffer: () => Promise.resolve(buf),
    } as unknown as File);
    // Transfer: the caller's ArrayBuffer is detached (byteLength 0) — the
    // bytes moved into the worker (single ownership, ironclad rule 8).
    expect(buf.byteLength).toBe(0);
    expect(await ts.name()).toBe("dut");
    expect(await ts.nports()).toBe(2);
    expect(await ts.version()).toBe("1.1");
    expect(Array.from(await ts.z0)).toEqual([50.0, 45.0]);
    await ts.drop();
  });

  it("fromUrl resolves a Promise", async () => {
    const m = await import("../../src/index.browser.ts");
    // The harness worker forwards to core; a fetch to an unreachable host
    // must reject verbatim (no swallow, no retry).
    await expect(m.Touchstone.fromUrl("http://127.0.0.1:1/none.s1p")).rejects.toThrow();
  });
});

describe("browser touchstone data plane", () => {
  it("data (S, RI) is the flat interleaved body", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText(S1P, 1);
    const d = await ts.data("S", "RI");
    expect(d.shape).toEqual([2, 1, 1, 2]);
    expect(d.values.length).toBe(4);
    expect(Array.from(d.values)).toEqual([1.0, 0.1, 0.9, -0.2]);
    await ts.drop();
  });

  it("data missing args reject", async () => {
    // Both parameters are mandatory; no silent (S, RI) default.
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText(S1P, 1);
    await expect((ts as unknown as { data(): Promise<unknown> }).data()).rejects.toThrow();
    await expect(
      (ts as unknown as { data(p: string): Promise<unknown> }).data("S"),
    ).rejects.toThrow();
    await ts.drop();
  });

  it("data MA returns real pairs (mag, deg)", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText(S1P, 1);
    const ma = await ts.data("S", "MA");
    expect(ma.shape).toEqual([2, 1, 1, 2]);
    expect(ma.values[0]).toBeCloseTo(Math.hypot(1.0, 0.1), 9);
    expect(ma.values[1]).toBeCloseTo((Math.atan2(0.1, 1.0) * 180) / Math.PI, 9);
    await ts.drop();
  });

  it("G on a 1-port network rejects", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText(S1P, 1);
    await expect(ts.data("G", "RI")).rejects.toThrow(/2-port/);
    await ts.drop();
  });

  it("z/y/g/h shortcut getters return their domains", async () => {
    // The four computed shortcut getters forward to core's s_to_domain; a
    // 2-port object must resolve all of them (shortcut properties, not just
    // data()). Each domain is distinct, so the four results differ pairwise.
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText(Z2P, 2);
    const zv = await ts.z;
    const yv = await ts.y;
    const gv = await ts.g;
    const hv = await ts.h;
    // 2×2 complex → 8 interleaved re/im for every domain.
    expect(zv.length).toBe(8);
    expect(yv.length).toBe(8);
    expect(gv.length).toBe(8);
    expect(hv.length).toBe(8);
    // z round-trips the parsed Z2P domain (row-major z11,z12,z21,z22);
    // MA→rect→S→Z is transcendental, so compare within tolerance.
    expect(zv[0]).toBeCloseTo(10, 9);
    expect(zv[1]).toBeCloseTo(0, 9);
    expect(Array.from(zv)).not.toEqual(Array.from(yv));
    expect(Array.from(gv)).not.toEqual(Array.from(hv));
    await ts.drop();
  });
});

describe("browser touchstone write", () => {
  it("toText renders text in core", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText(Z2P, 2);
    const text = await ts.toText("S", "RI");
    const back = await m.Touchstone.fromText(text, 2);
    expect(Array.from(await back.s)).toEqual(Array.from(await ts.s));
    expect(await back.version()).toBe(await ts.version());
    await back.drop();
    await ts.drop();
  });

  it("writeFile downloads under the core-corrected filename", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText(S1P, 1, "/tmp/dir/filter.s1p");
    // Platform-glue stubs: the shell's Blob + <a download> is the only DOM
    // it touches; the filename decision is core's (write_path). Stubbed
    // unconditionally so the same test runs under Node and a real browser.
    const clicks: string[] = [];
    let blobs = 0;
    const g = globalThis as unknown as Record<string, unknown>;
    // `document` is getter-only on Window (browser) and absent on Node:
    // install a minimal scope either way, stubbing createElement.
    const origDoc = g.document;
    const fakeDoc = {
      createElement: (_tag: string) => {
        const attrs: Record<string, string> = {};
        return {
          set href(v: string) {
            attrs.href = v;
          },
          set download(v: string) {
            attrs.download = v;
          },
          click() {
            clicks.push(String(attrs.download));
          },
        };
      },
    };
    if (origDoc) {
      // Browser: `document` exists (getter-only) — patch createElement on it.
      (origDoc as { createElement: unknown }).createElement = fakeDoc.createElement;
    } else {
      Object.defineProperty(g, "document", { value: fakeDoc, configurable: true });
    }
    if (!g.URL) Object.defineProperty(g, "URL", { value: {}, configurable: true });
    const origCreate = URL.createObjectURL as unknown;
    const origRevoke = URL.revokeObjectURL as unknown;
    URL.createObjectURL = (() => {
      blobs++;
      return "blob:stub";
    }) as unknown as typeof URL.createObjectURL;
    URL.revokeObjectURL = (() => {}) as unknown as typeof URL.revokeObjectURL;
    try {
      await ts.writeFile("filter.s9p", "S", "RI");
      // No path (browser-optional): core write_path falls back to name +
      // correct extension; exercises the `path ?? null` branch.
      await ts.writeFile(undefined, "S", "RI");
    } finally {
      if (!origDoc) delete g.document;
      URL.createObjectURL = origCreate as typeof URL.createObjectURL;
      URL.revokeObjectURL = origRevoke as typeof URL.revokeObjectURL;
    }
    // The wrong extension is mechanically impossible: core write_path
    // rebuilt it from the written parameter + real nports. The path-less
    // call falls back to the stored name (also filter.s1p).
    expect(clicks).toEqual(["filter.s1p", "filter.s1p"]);
    expect(blobs).toBe(2);
    await ts.drop();
  });
});

// Byte boundary (fromBytes / toBytes) through the resident worker. ASCII
// body; the µ comment marker is injected at the byte level so tests control
// the exact encoding bytes (ironclad rule 2).
const BODY_1P = new TextEncoder().encode("# GHZ S RI R 50\n1.0 1.0 0.1\n2.0 0.9 -0.2\n");
const LATIN1 = Uint8Array.from([0x21, 0x20, 0xb5, 0x0a, ...BODY_1P]); // µ = single byte B5

describe("browser touchstone bytes", () => {
  it("fromBytes guesses latin-1 through the worker", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromBytes(Uint8Array.from(LATIN1), 1);
    expect(await ts.comments()).toBe("\u00b5");
    expect(Array.from(await ts.s)).toEqual([1.0, 0.1, 0.9, -0.2]);
    await ts.drop();
  });

  it("fromBytes infers nports from the path grammar", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromBytes(Uint8Array.from(LATIN1), undefined, "dut.s1p");
    expect(await ts.nports()).toBe(1);
    expect(await ts.name()).toBe("dut");
    await ts.drop();
  });

  it("fromBytes transfers the bytes (buffer detached afterwards)", async () => {
    const m = await import("../../src/index.browser.ts");
    const buf = Uint8Array.from(LATIN1).buffer as ArrayBuffer;
    const ts = await m.Touchstone.fromBytes(new Uint8Array(buf), 1);
    expect(buf.byteLength).toBe(0); // moved into the worker (ironclad rule 8)
    expect(await ts.comments()).toBe("\u00b5");
    await ts.drop();
  });

  it("fromBytes explicit UTF-8 on latin-1 rejects", async () => {
    const m = await import("../../src/index.browser.ts");
    await expect(
      m.Touchstone.fromBytes(Uint8Array.from(LATIN1), 1, undefined, "UTF-8"),
    ).rejects.toThrow(/UTF-8/);
  });

  it("toBytes returns a Uint8Array (default UTF-8, explicit latin-1)", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromBytes(Uint8Array.from(LATIN1), 1);
    const utf8 = await ts.toBytes("S", "RI");
    expect(utf8).toBeInstanceOf(Uint8Array);
    expect(Array.from(utf8.slice(0, 4))).toEqual([0x21, 0x20, 0xc2, 0xb5]);
    const latin = await ts.toBytes("S", "RI", "ISO-8859-1");
    expect(Array.from(latin.slice(0, 3))).toEqual([0x21, 0x20, 0xb5]);
    await ts.drop();
  });

  it("bytes round-trip bit-exact at the same encoding", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromBytes(Uint8Array.from(LATIN1), 1, undefined, "ISO-8859-1");
    const written = await ts.toBytes("S", "RI", "ISO-8859-1");
    const back = await m.Touchstone.fromBytes(written, 1, undefined, "ISO-8859-1");
    expect(Array.from(await back.s)).toEqual(Array.from(await ts.s));
    expect(await back.comments()).toBe(await ts.comments());
    await back.drop();
    await ts.drop();
  });
});

describe("browser touchstone name pipeline", () => {
  it("static helpers route through the namespace", async () => {
    const m = await import("../../src/index.browser.ts");
    expect(await m.Touchstone.filenameFromPath("/a/b/c.s2p")).toBe("c.s2p");
    expect(await m.Touchstone.nameFromFilename("2026.10.09")).toBe("2026.10.09");
    expect(await m.Touchstone.nameFromFilename("dut.s4p")).toBe("dut");
    expect(await m.Touchstone.nportsFromFilename("dut.s4p")).toBe(4);
    await expect(m.Touchstone.nportsFromFilename("no-ext")).rejects.toThrow(/nports/);
  });
});

describe("browser touchstone lifecycle", () => {
  it("drop frees the core resource; post-drop access rejects", async () => {
    const m = await import("../../src/index.browser.ts");
    const ts = await m.Touchstone.fromText(S1P, 1);
    await ts.drop();
    await expect(ts.nports()).rejects.toThrow(/handle/);
    // Idempotent: a second drop resolves.
    await ts.drop();
  });
});
