// vitest setupFile for the node-driven wasm suite: registers an `afterAll`
// that runs in the SAME worker context as the tests, so it can reach the live
// wasm instance the worker stashed on globalThis and drain its coverage
// counters. minicov has no atexit, so the dump MUST be called explicitly from
// here (globalSetup runs in the main process and cannot see worker memory).
//
// No-op unless NETWAVE_WASM_DIR is set — i.e. only under the rust coverage
// chain. Production and browser runs import this file but do nothing, so the
// TS-only v8 coverage path is untouched.
import { afterAll } from "vitest";

afterAll(async () => {
  const covDir = process.env.NETWAVE_WASM_DIR;
  const outDir = process.env.NETWAVE_COV_OUT;
  if (!covDir || !outDir) return; // not the coverage chain: nothing to drain

  const slot = (
    globalThis as unknown as { __netwaveWasmInstance?: { current?: Record<string, unknown> } }
  ).__netwaveWasmInstance;
  const wasm = slot?.current;
  if (!wasm) return; // worker never inited (no test exercised it): nothing to drain

  const dump = wasm.__cov_dump as () => void;
  const ptr = wasm.__cov_ptr as () => number;
  const len = wasm.__cov_len as () => number;
  // u64 crosses the boundary as a BigInt.
  const signature = wasm.__cov_signature as () => bigint;
  const memory = wasm.memory as WebAssembly.Memory;

  dump();
  // Re-read the buffer after dump: capture_coverage may have grown (reallocated)
  // linear memory, detaching any earlier typed-array view.
  const bytes = new Uint8Array(memory.buffer, ptr(), len());
  const { writeFile, mkdir } = await import("node:fs/promises");
  await mkdir(outDir, { recursive: true });
  // Name by module_signature so concurrent workers never overwrite one another
  // before `llvm-profdata merge` (signature is unique per load module).
  await writeFile(`${outDir}/default-${signature()}-${process.pid}.profraw`, bytes);
});
