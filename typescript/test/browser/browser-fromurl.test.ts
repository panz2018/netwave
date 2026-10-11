/** Real-browser-only: `fromUrl` SUCCESS path. The shared wasm suite only
 * witnesses rejection (an unreachable host rejects before the worker ever
 * resolves), so the shell's `.then((handle) => new Touchstone(handle))`
 * success callback is exercised only here — a same-origin fixture served by
 * the vitest browser server makes the worker's `web_sys::fetch` resolve.
 * Cannot run under Node (no vite browser server). */
import { beforeAll, describe, expect, it } from "vitest";
import { installResidentWorkerHarness } from "../wasm/harness.ts";

beforeAll(async () => {
  await installResidentWorkerHarness();
});

describe("real browser: fromUrl resolves", () => {
  it("fetches a same-origin fixture and parses it", async () => {
    const m = await import("../../src/index.browser.ts");
    // vitest browser mode serves the project root over http; the worker's
    // fetch runs same-origin (no CORS). The name pipeline takes the last
    // path segment (filter.s1p -> name "filter", nports 1).
    const url = new URL("/test/fixtures/filter.s1p", location.href).href;
    const ts = await m.Touchstone.fromUrl(url);
    expect(await ts.name()).toBe("filter");
    expect(await ts.nports()).toBe(1);
    expect(await ts.parameter()).toBe("S");
    expect(Array.from(await ts.f)).toEqual([1e9, 2e9]);
    expect(Array.from(await ts.s)).toEqual([0.5, 0.1, 0.4, -0.2]);
    await ts.drop();
  });
});
