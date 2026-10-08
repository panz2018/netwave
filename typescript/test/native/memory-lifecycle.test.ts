/** Node napi memory-lifecycle tripwire: the napi finalizer must run `Drop`
 * automatically. Drives the generated glue directly: the napi class
 * is internalized (the shell does NOT re-export it), but the glue build
 * artifact is the real object under test — the same three assertions as the
 * browser line, witnessed by the same core `live_count`. `--expose-gc` comes
 * from `vitest.native.config.ts`. */
// These tests assign a wrapper to a variable and then null it on purpose:
// the variable's ONLY job is to be a GC root (write-only by design), so the
// linter's "unused" is a false positive here — the reference is the test.
/** biome-ignore-all lint/correctness/noUnusedVariables: GC-root variable, write-only by design */
import { describe, expect, it } from "vitest";
import { Frequency, FrequencyUnit, liveCount } from "../../dist/index.node.generated.mjs";

// Force a major GC and let the napi cleanup finalizer drain: the finalizer
// runs during GC cleanup, delivered on a later task, so yield.
const collect = async (): Promise<void> => {
  for (let i = 0; i < 50; i++) {
    (globalThis as unknown as { gc: () => void }).gc();
    await new Promise((r) => setTimeout(r, 0));
  }
};

describe("native memory lifecycle (napi finalizer)", () => {
  it("env exposes gc (fail-fast: env vs mechanism)", () => {
    expect(typeof (globalThis as unknown as { gc?: unknown }).gc).toBe("function");
  });

  it("napi finalizer runs Rust Drop on GC", async () => {
    const base = liveCount();
    let f: Frequency | null = Frequency.fromF([1e9, 2e9], FrequencyUnit.GHz);
    expect(liveCount()).toBe(base + 1);
    f = null; // drop the only reference
    await collect();
    expect(liveCount()).toBe(base); // finalizer -> Drop ran
  });

  it("shared ownership: not freed until ALL refs are gone", async () => {
    const base = liveCount();
    let a: Frequency | null = Frequency.fromF([3e9], FrequencyUnit.GHz);
    let b: Frequency | null = a; // second reference to the same object
    a = null;
    await collect();
    expect(liveCount()).toBe(base + 1); // b still holds it
    b = null;
    await collect();
    expect(liveCount()).toBe(base); // last ref gone -> Drop
  });

  it("explicit drop(): immediate, no GC needed", async () => {
    const base = liveCount();
    const f = Frequency.fromF([4e9], FrequencyUnit.GHz);
    expect(liveCount()).toBe(base + 1);
    f.drop(); // deterministic reclamation, no gc() call (the unified verb)
    expect(liveCount()).toBe(base);
  });
});
