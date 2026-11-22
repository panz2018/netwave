// Coverage-chain dump helper, imported by the resident worker. Lives in its
// own module (outside the v8 coverage `include`) for the same reason as
// test/wasm/coverage-dump.ts: the dump arms only ever execute against an
// instrumented instance, which production v8 runs never load — keeping them
// out of the TS coverage denominator keeps that threshold honest.

/** The dump entry points the instrumented glue exports (absent on a
 * production instance). */
export interface CoverageInstance {
  __cov_dump: () => void;
  __cov_ptr: () => number;
  __cov_len: () => number;
  __cov_signature: () => bigint;
  memory: WebAssembly.Memory;
}

/** Drain the instrumented instance's coverage counters. Returns null when
 * the loaded instance is not instrumented (production build: no dump
 * exports, nothing to drain). The buffer view MUST be built after the dump
 * call: capture_coverage may grow (reallocate) linear memory and detach any
 * earlier view. */
export function dumpCoverage(
  instance: Record<string, unknown> | undefined,
): { profraw: Uint8Array; signature: string } | null {
  if (!instance || typeof instance.__cov_dump !== "function") return null;
  const wasm = instance as unknown as CoverageInstance;
  const signature = wasm.__cov_signature().toString();
  wasm.__cov_dump();
  // Re-read the buffer after dump: capture_coverage may have grown (reallocated)
  // linear memory, detaching any earlier typed-array view.
  const bytes = new Uint8Array(wasm.memory.buffer, wasm.__cov_ptr(), wasm.__cov_len());
  return { profraw: bytes.slice(), signature };
}

/** @internal Install a fetch stub on the worker's own global so a later
 * `fromUrl` drives core's fetch error arms. web_sys looks up `fetch` on the
 * global at call time (`arg0.fetch(...)` in the glue), so replacing it here is
 * observed by wasm. `reject` makes `Response.text()` reject (the text-await
 * error arm); `nonstring` resolves it to a number (the non-utf8 arm — Rust's
 * `as_string()` yields None). Coverage-chain only: production never calls it. */
export function installFetchStub(mode: "textthrow" | "reject" | "nonstring"): void {
  const scope = globalThis as unknown as { fetch: typeof fetch };
  // web_sys maps a synchronous throw from `text()` to Rust `Err` (the
  // `resp.text().map_err` arm); a rejected Promise maps to the await error
  // arm; a non-string resolve makes Rust `as_string()` yield None (non-utf8).
  const text = () => {
    if (mode === "textthrow") throw new Error("stub text throw");
    if (mode === "reject") return Promise.reject(new Error("stub text reject"));
    return Promise.resolve(12345);
  };
  scope.fetch = (() => Promise.resolve({ ok: true, status: 200, text })) as unknown as typeof fetch;
}
