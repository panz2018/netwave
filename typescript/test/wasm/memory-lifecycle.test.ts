/** Memory-lifecycle tripwire (memory-lifecycle spec). Runs unmodified under
 * Node (fake scopes, real wasm glue, `--expose-gc`) and in a real browser
 * (native Worker, chromium `--expose-gc`) via the shared harness — the same
 * three assertions witness Rust `Drop` on both realms.
 *
 * The witness is the core `live_count()`: it proves the Rust `Drop` actually
 * ran, not merely that a JS Map entry vanished. `--expose-gc` is injected by
 * `vitest.wasm.config.ts` / `vitest.browser.config.ts`; the fail-fast probe
 * below distinguishes "env missing expose-gc" from "mechanism broken".
 */
// These tests assign a wrapper to a variable and then null it on purpose:
// the variable's ONLY job is to be a GC root (write-only by design), so the
// linter's "unused" is a false positive here — the reference is the test.
/** biome-ignore-all lint/correctness/noUnusedVariables: GC-root variable, write-only by design */
import { beforeAll, describe, expect, it } from "vitest";
// FrequencyUnit is a plain numeric-constant object in the glue; importing it
// never instantiates wasm and never touches Worker (ironclad rule 8), so it
// is safe at module-eval time — unlike the shell, whose top level builds the
// worker (imported dynamically below, after the harness installs a fake).
import { FrequencyUnit } from "../../dist/wasm-web/netwave_wasm.js";
import type { Frequency } from "../../src/index.browser.ts";
import { type Harness, installResidentWorkerHarness } from "./harness.ts";

let h: Harness;

beforeAll(async () => {
  h = await installResidentWorkerHarness();
});

const shell = async () => await import("../../src/index.browser.ts");

// Force a major GC and let the FinalizationRegistry callback drain: the
// callback is queued during gc() but delivered on a later task, so yield.
const collect = async (): Promise<void> => {
  for (let i = 0; i < 50; i++) {
    (globalThis as unknown as { gc: () => void }).gc();
    await new Promise((r) => setTimeout(r, 0));
  }
};

const liveCount = async (): Promise<number> => (await shell()).liveCount();

describe("memory lifecycle (browser double-realm)", () => {
  it("env exposes gc (fail-fast: env vs mechanism)", () => {
    expect(typeof (globalThis as unknown as { gc?: unknown }).gc).toBe("function");
  });

  it("registry drives free: dropping the last ref runs Rust Drop", async () => {
    const m = await shell();
    const base = await liveCount();
    let shellRef: Frequency | null = await m.Frequency.fromF(
      new Float64Array([1e9, 2e9]),
      FrequencyUnit.GHz,
    );
    expect(await liveCount()).toBe(base + 1);
    shellRef = null; // drop the only main-thread reference
    await collect();
    expect(await liveCount()).toBe(base); // Drop ran via registry -> worker drop
  });

  it("shared ownership: not freed until ALL refs are gone", async () => {
    const m = await shell();
    const base = await liveCount();
    let a: Frequency | null = await m.Frequency.fromF(new Float64Array([3e9]), FrequencyUnit.GHz);
    let b: Frequency | null = a; // second reference to the same shell
    a = null;
    await collect();
    expect(await liveCount()).toBe(base + 1); // b still holds it
    b = null;
    await collect();
    expect(await liveCount()).toBe(base); // last ref gone -> Drop
  });

  it("explicit drop(): immediate, no GC needed", async () => {
    const m = await shell();
    const base = await liveCount();
    const f = await m.Frequency.fromF(new Float64Array([4e9]), FrequencyUnit.GHz);
    expect(await liveCount()).toBe(base + 1);
    await f.drop(); // deterministic release, no gc() call
    expect(await liveCount()).toBe(base);
  });

  it("double drop is idempotent (no double-free)", async () => {
    const m = await shell();
    const base = await liveCount();
    const f = await m.Frequency.fromF(new Float64Array([5e9]), FrequencyUnit.GHz);
    await f.drop();
    await f.drop(); // second drop: no-op, no throw
    expect(await liveCount()).toBe(base); // Drop ran exactly once
    await expect(f.npoints()).rejects.toThrow(/dropped/); // post-drop access
  });
});
