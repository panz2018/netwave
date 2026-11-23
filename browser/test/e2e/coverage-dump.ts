// vitest setupFile for the REAL-BROWSER rust coverage chain. Registers an
// `afterAll` that runs in the test (main-thread) context: it asks the resident
// worker to drain its instrumented instance's profraw (only the worker realm
// can read wasm memory), then ships the bytes to node through a vitest browser
// command so `llvm-profdata merge` can read them.
//
// No-op unless the chain is active — the config only loads this file when
// NETWAVE_WASM_DIR is set, so production browser runs never register the hook.
//
// The bytes cross the worker boundary as a raw Uint8Array (structuredClone),
// but the vitest browser-command transport degrades Uint8Array to a plain
// Object, so they are base64-encoded here for the command leg (spike-verified
// byte-for-byte). The minicov module signature is a property of the binary, so
// every test file loading the SAME instrumented wasm shares one signature — a
// bare signature filename would let each file's afterAll overwrite the last.
// A per-dump UUID suffix keeps every file's counters as its own profraw so
// `llvm-profdata merge -sparse` unions them (a line hit in any file counts).
import { afterAll } from "vitest";
import { commands } from "vitest/browser";

// The chain's custom command (registered in vitest.browser.config.ts). Vitest
// types BrowserCommands as a fixed table; the custom command is added at
// runtime, so it is cast here rather than augmenting the global type (this
// file is coverage-chain-only and never ships).
const writeProfraw = (
  commands as unknown as { writeProfraw: (b64: string, signature: string) => Promise<number> }
).writeProfraw;

afterAll(async () => {
  const worker = (globalThis as unknown as { __netwaveWorker?: Worker }).__netwaveWorker;
  if (!worker) return; // no worker was ever constructed: nothing to drain

  // Drive core's defensive arms (dropped guards, dispatch error arms) in the
  // worker realm first — JS dispatch never reaches them, so without this their
  // counters stay zero and they show as gaps. No-op on a production instance.
  await new Promise<void>((resolve) => {
    const onDrive = (ev: MessageEvent) => {
      const data = ev.data as { id: number; drove?: boolean };
      if (data.id === 0 && "drove" in data) {
        worker.removeEventListener("message", onDrive);
        resolve();
      }
    };
    worker.addEventListener("message", onDrive);
    worker.postMessage({ control: "driveCoverage" });
  });

  const dump = await new Promise<{ profraw: Uint8Array; signature: string } | null>((resolve) => {
    const onMessage = (ev: MessageEvent) => {
      const data = ev.data as { id: number; coverage?: typeof dump };
      if (data.id === 0 && "coverage" in data) {
        worker.removeEventListener("message", onMessage);
        resolve(data.coverage ?? null);
      }
    };
    worker.addEventListener("message", onMessage);
    worker.postMessage({ control: "dumpCoverage" });
  });
  if (!dump) return; // production instance (no dump exports): nothing to write

  const chunk = 8192;
  let bin = "";
  for (let i = 0; i < dump.profraw.length; i += chunk) {
    bin += String.fromCharCode(...dump.profraw.subarray(i, i + chunk));
  }
  // Unique per dump so concurrent test files sharing one module signature never
  // overwrite each other's profraw before merge.
  await writeProfraw(btoa(bin), `${dump.signature}-${crypto.randomUUID()}`);
});
