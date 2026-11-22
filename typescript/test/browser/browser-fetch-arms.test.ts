/** Real-browser-only: core's `fetch_text` error arms. The shared wasm suite
 * only drives the success and non-OK paths; the text-await failure and the
 * non-utf8 body arms need a fetch whose `Response.text()` misbehaves, which
 * only the worker realm can provide (wasm reads `fetch` off its own global at
 * call time). A `stubFetch` control message installs such a fetch in the
 * worker, then `fromUrl` drives the arm. Cannot run under Node (the node
 * harness's fakeSelf never reaches these web_sys arms). */
import { beforeAll, describe, expect, it } from "vitest";
import { installResidentWorkerHarness } from "../wasm/harness.ts";

beforeAll(async () => {
  await installResidentWorkerHarness();
});

/** Ask the resident worker to install a fetch stub and await its ack. */
async function stubWorkerFetch(mode: "textthrow" | "reject" | "nonstring"): Promise<void> {
  const w = (globalThis as unknown as { __netwaveWorker?: Worker }).__netwaveWorker;
  if (!w) throw new Error("shell did not register the singleton worker");
  await new Promise<void>((resolve) => {
    const onMessage = (ev: MessageEvent) => {
      const data = ev.data as { id: number; stubbed?: boolean };
      if (data.id === 0 && "stubbed" in data) {
        w.removeEventListener("message", onMessage);
        resolve();
      }
    };
    w.addEventListener("message", onMessage);
    w.postMessage({ control: "stubFetch", mode });
  });
}

describe("real browser: fetch error arms", () => {
  it("a Response whose text() throws synchronously surfaces the failure", async () => {
    const m = await import("../../src/index.browser.ts");
    await stubWorkerFetch("textthrow");
    const url = new URL("/test/fixtures/filter.s1p", location.href).href;
    await expect(m.Touchstone.fromUrl(url)).rejects.toThrow(/fetch failed/);
  });

  it("a Response whose text() rejects surfaces the failure verbatim", async () => {
    const m = await import("../../src/index.browser.ts");
    await stubWorkerFetch("reject");
    const url = new URL("/test/fixtures/filter.s1p", location.href).href;
    await expect(m.Touchstone.fromUrl(url)).rejects.toThrow(/fetch failed/);
  });

  it("a non-string text() body is rejected as non-utf8", async () => {
    const m = await import("../../src/index.browser.ts");
    await stubWorkerFetch("nonstring");
    const url = new URL("/test/fixtures/filter.s1p", location.href).href;
    await expect(m.Touchstone.fromUrl(url)).rejects.toThrow(/fetch failed/);
  });
});
