// netwave browser conditional shell: explicit named re-exports (no
// `export *`, preserves tree-shaking). Backed by the wasm-pack `web`
// target glue (dist/wasm-web), which exposes an async `init` that fetches
// the .wasm. Worker offload arrives in phase 3; for now calls resolve
// immediately after init.
import wasmInit, {
  fill_pattern as _wasmFill,
  read_element as _wasmRead,
} from "../dist/wasm-web/netwave_wasm.js";

let ready = null;
// Record the live linear memory so the worker can avoid transferring it
// (transferring wasm memory would detach the instance's memory).
const ensureReady = () =>
  (ready ??= (async () => {
    const exports = await wasmInit({ module_or_path: await wasmSource() });
    // wasm-bindgen init resolves to the instance exports object.
    globalThis.__netwaveWasmMemory = exports.memory;
    return exports;
  })());

// In browsers the web-target glue fetches the .wasm itself (default);
// under Node (vitest) fetch has no file: support, so read the bytes with
// node:fs. The node: import is dynamic and browser-invisible.
/* v8 ignore next 1 -- environment probe; Node-only in this test suite */
const isNode = typeof process !== "undefined" && !!process.versions.node;
const wasmSource = async () => {
  /* v8 ignore start -- browser-only path; exercised in real-browser tests (phase 3) */
  if (!isNode) return undefined; // glue default: fetch relative to its own URL
  /* v8 ignore stop */
  const { readFile } = await import("node:fs/promises");
  const { fileURLToPath } = await import("node:url");
  return readFile(fileURLToPath(new URL("../dist/wasm-web/netwave_wasm_bg.wasm", import.meta.url)));
};

/**
 * Allocate and fill an interleaved complex f64 buffer, returning a
 * descriptor from which a view can be rebuilt.
 * @returns {Promise<{buffer: ArrayBuffer, byteOffset: number, length: number}>}
 */
export async function fillPattern(nfreq, nports) {
  await ensureReady();
  return _fillPattern(nfreq, nports);
}

/** Pass a view back into core and read an element. @returns {Promise<number>} */
export async function readElement(view, idx) {
  await ensureReady();
  return _readElement(view, idx);
}

/**
 * @internal Sync passthrough escape hatch; no stability guarantee. Only
 * usable after init has completed (await fillPattern once, or use the
 * async surface). wasm returns a linear-memory view descriptor
 * {buffer, byteOffset, length}; buffer is the whole linear memory (may
 * grow), so views must be cut at the offset.
 */
export const _fillPattern = (nfreq, nports) => _wasmFill(nfreq, nports);
/** @internal Sync passthrough escape hatch. */
export const _readElement = (view, idx) => _wasmRead(view, idx);
