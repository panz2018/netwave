/** Touchstone node surface.
 *
 * Expected values are independent literals / closed-form (ironclad rule 2).
 * Same-machine RI round-trips are bit-exact; MA/DB compare within the
 * manifest core_tol (ironclad rule 3). */

import { existsSync, mkdtempSync } from "node:fs";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { describe, expect, it } from "vitest";
import { Frequency, Touchstone } from "../../src/index.node.ts";

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

describe("touchstone node factories", () => {
  it("fromText parses data and metadata", () => {
    const ts = Touchstone.fromText(S1P, 1, "/tmp/dir/filter.s1p");
    expect(ts.nports).toBe(1);
    expect(ts.name).toBe("filter");
    expect(ts.version).toBe("1.0");
    expect(ts.parameter).toBe("S");
    expect(ts.comments).toBe("comment one");
    expect(Array.from(ts.f)).toEqual([1e9, 2e9]);
    expect(Array.from(ts.z0)).toEqual([50.0]);
    // s: interleaved flat [re, im, ...].
    expect(Array.from(ts.s)).toEqual([1.0, 0.1, 0.9, -0.2]);
  });

  it("fromText infers nports from the path grammar", () => {
    const ts = Touchstone.fromText(S1P, undefined, "/x/a.s1p");
    expect(ts.nports).toBe(1);
  });

  it("fromText without nports or path throws", () => {
    expect(() => Touchstone.fromText(S1P)).toThrow(/nports/);
  });

  it("fromText without a # option line throws", () => {
    expect(() => Touchstone.fromText("1.0 0.1 0.2\n", 1)).toThrow(/option line/);
  });

  it("partial option line uses spec defaults GHz S MA R 50", () => {
    const ts = Touchstone.fromText("#\n1.0 0.5 -30\n", 1);
    expect(Array.from(ts.z0)).toEqual([50]);
    const s = Array.from(ts.s);
    expect(s[0]).toBeCloseTo(0.5 * Math.cos((-30 * Math.PI) / 180), 12);
    expect(s[1]).toBeCloseTo(0.5 * Math.sin((-30 * Math.PI) / 180), 12);
  });

  it("syntax error quotes the offending token", () => {
    expect(() => Touchstone.fromText("# GHZ S RI R 50\n1.0 abc 0.1\n", 1)).toThrow(/abc/);
  });

  it("duplicate frequency throws with the value", () => {
    const dup = "# GHZ S RI R 50\n1.0 1.0 0.1\n1.0 0.5 0.0\n";
    expect(() => Touchstone.fromText(dup, 1)).toThrow(/1/);
  });

  it("fromFile is async and parses", async () => {
    const dir = mkdtempSync(join(tmpdir(), "nw-"));
    const path = join(dir, "dut.s2p");
    await import("node:fs").then((fs) => fs.writeFileSync(path, Z2P));
    const ts = await Touchstone.fromFile(path);
    expect(ts.name).toBe("dut");
    expect(ts.nports).toBe(2);
    expect(ts.version).toBe("1.1");
    expect(Array.from(ts.z0)).toEqual([50.0, 45.0]);
  });

  it("constructor derives version from z0 values", () => {
    const f = Frequency.fromF([1.0], "GHz");
    const ts = new Touchstone(f, [10, 0, 20, 90, 30, -90, 40, 180], [50.0, 45.0], "Z");
    expect(ts.version).toBe("1.1");
    expect(ts.nports).toBe(2);
    // Z data converts to S at construction; parameter keeps the origin.
    expect(ts.parameter).toBe("Z");
  });

  it("constructor rejects a bad z0 shape", () => {
    const f = Frequency.fromF([1.0], "GHz");
    expect(() => new Touchstone(f, [1.0, 0.0], [50.0, 45.0], "S")).toThrow(/z0/);
  });
});

describe("touchstone node data plane", () => {
  it("data (S, RI) is the flat interleaved body", () => {
    const ts = Touchstone.fromText(S1P, 1);
    const d = ts.data("S", "RI");
    expect(d.shape).toEqual([2, 1, 1, 2]);
    expect(d.values.length).toBe(4);
    expect(Array.from(d.values)).toEqual([1.0, 0.1, 0.9, -0.2]);
  });

  it("data missing args throw", () => {
    // Both parameters are mandatory; no silent (S, RI) default.
    const ts = Touchstone.fromText(S1P, 1);
    expect(() => (ts as unknown as { data(): unknown }).data()).toThrow();
    expect(() => (ts as unknown as { data(p: string): unknown }).data("S")).toThrow();
  });

  it("data MA returns real pairs (mag, deg)", () => {
    const ts = Touchstone.fromText(S1P, 1);
    const ma = ts.data("S", "MA");
    expect(ma.shape).toEqual([2, 1, 1, 2]);
    expect(ma.values[0]).toBeCloseTo(Math.hypot(1.0, 0.1), 12);
    expect(ma.values[1]).toBeCloseTo((Math.atan2(0.1, 1.0) * 180) / Math.PI, 12);
  });

  it("flat index formula idx = ((f*n + r)*n + c)*2", () => {
    const ts = Touchstone.fromText(Z2P, 2);
    const z = ts.data("Z", "RI");
    expect(z.shape).toEqual([1, 2, 2, 2]);
    // z11 = 10 + 0j at flat index 0; z12 = 0 + 20j at index 2. MA→rect
    // is transcendental, so compare within the manifest core_tol (rule 3).
    const expected = [10, 0, 0, 20, 0, -30, -40, 0];
    expected.forEach((v, i) => {
      expect(z.values[i]).toBeCloseTo(v, 9);
    });
  });

  it("G/H require 2 ports", () => {
    const ts = Touchstone.fromText(S1P, 1);
    expect(() => ts.data("G", "RI")).toThrow(/2-port/);
  });
});

describe("touchstone node write", () => {
  it("writeTouchstone RI round-trips bit-exact", () => {
    const ts = Touchstone.fromText(Z2P, 2);
    const text = ts.writeTouchstone("S", "RI");
    const back = Touchstone.fromText(text, 2);
    expect(Array.from(back.s)).toEqual(Array.from(ts.s));
    expect(back.version).toBe(ts.version);
    expect(Array.from(back.z0)).toEqual(Array.from(ts.z0));
  });

  it("writeFile corrects the extension", async () => {
    const ts = Touchstone.fromText(S1P, 1, "/tmp/dir/filter.s1p");
    const dir = mkdtempSync(join(tmpdir(), "nw-"));
    await ts.writeFile(join(dir, "filter.s9p"), "S", "RI");
    expect(existsSync(join(dir, "filter.s1p"))).toBe(true);
    expect(existsSync(join(dir, "filter.s9p"))).toBe(false);
  });
});

describe("touchstone node fromUrl", () => {
  it("fetches and parses; HTTP errors propagate", async () => {
    const server = createServer((req, res) => {
      if (req.url?.startsWith("/data/")) {
        res.writeHead(200, { "content-type": "text/plain" });
        res.end(S1P);
      } else {
        res.writeHead(404);
        res.end();
      }
    });
    await new Promise<void>((r) => server.listen(0, "127.0.0.1", r));
    const port = (server.address() as { port: number }).port;
    try {
      const ts = await Touchstone.fromUrl(`http://127.0.0.1:${port}/data/filter.s1p`);
      expect(ts.name).toBe("filter");
      expect(ts.nports).toBe(1);
      expect(Array.from(ts.s)).toEqual([1.0, 0.1, 0.9, -0.2]);
      await expect(Touchstone.fromUrl(`http://127.0.0.1:${port}/missing.s1p`)).rejects.toThrow(
        /404/,
      );
    } finally {
      server.close();
    }
  });
});

describe("touchstone node lifecycle", () => {
  it("drop is idempotent; post-drop access throws", () => {
    const ts = Touchstone.fromText(S1P, 1);
    expect(ts.nports).toBe(1);
    ts.drop();
    expect(() => ts.nports).toThrow(/dropped/);
    expect(() => ts.s).toThrow(/dropped/);
    ts.drop(); // idempotent
  });
});

describe("touchstone node name pipeline", () => {
  it("static helpers match core grammar", () => {
    expect(Touchstone.filenameFromPath("/a/b/c.s2p")).toBe("c.s2p");
    expect(Touchstone.nameFromFilename("2026.10.09")).toBe("2026.10.09");
    expect(Touchstone.nameFromFilename("dut.s4p")).toBe("dut");
    expect(Touchstone.nportsFromFilename("dut.s4p")).toBe(4);
    expect(() => Touchstone.nportsFromFilename("no-ext")).toThrow(/nports/);
  });
});
