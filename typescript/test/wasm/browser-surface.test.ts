/** Browser entry surface tests (ironclad rule 8): the browser entry MUST
 * NOT export any `_`-prefixed sync compute function — the main thread has
 * no wasm, so sync compute has nowhere to run. Node keeps `_` (in-process
 * napi core); that asymmetry is pinned here and in test/native. */
import { beforeAll, describe, expect, it } from "vitest";
import { installResidentWorkerHarness } from "./harness.ts";

beforeAll(async () => {
  await installResidentWorkerHarness();
});

describe("browser entry surface", () => {
  it("exports no `_`-prefixed sync compute escape hatches", async () => {
    const m = await import("../../src/index.browser.ts");
    const syncHatches = Object.keys(m).filter((k) => k.startsWith("_"));
    expect(syncHatches).toEqual([]);
  });

  it("exports the async class surface + vocabulary", async () => {
    const m = await import("../../src/index.browser.ts");
    expect(Object.keys(m).sort()).toEqual([
      "Frequency",
      "FrequencyUnit",
      "Network",
      "SPEED_OF_LIGHT",
      "WavelengthUnit",
      "frequencyUnits",
      "liveCount",
    ]);
  });
});
