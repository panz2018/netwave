/** Shared harness for resident-worker tests ("same test code" rule: runs
 * unmodified under Node (vitest node env) AND in a real browser (vitest
 * browser mode)).
 *
 * Node: installs a fake `self` (worker side, importing the real worker
 * with the real wasm glue) and a fake `Worker` class (shell side), wired
 * together. `postMessage` uses `structuredClone(msg, {transfer})` so
 * detach/transfer semantics are REAL, not stubbed.
 * Browser: wraps the native Worker to count instances/posts and observe
 * module); the real worker is loaded by URL by the shell itself in a
 * browser (vite resolves ./netwave.worker.js -> src/netwave.worker.ts).
 *
 * Both paths expose identical counters so the assertions are shared.
 */
import type { WorkerRequest, WorkerResponse } from "../../src/types.ts";

export interface Harness {
  /** Replies observed from the worker (cloned, post-transfer). */
  posted: { msg: WorkerResponse; transfer: ArrayBuffer[] | undefined }[];
  /** Count of postMessage calls made by the shell. */
  shellPosts(): number;
  /** Count of Worker instances constructed. */
  workerInstances(): number;
  /** The shell's singleton worker (globalThis registry). Available after
   * the shell's first await. */
  singleton(): { postMessage: (m: WorkerRequest, t?: ArrayBuffer[]) => void } | undefined;
  /** Subscribe to worker replies (all of them); returns unsubscribe. */
  onReply(fn: (res: WorkerResponse) => void): () => void;
}

export async function installResidentWorkerHarness(): Promise<Harness> {
  const posted: Harness["posted"] = [];
  const replyFns = new Set<(res: WorkerResponse) => void>();
  let instances = 0;
  let posts = 0;

  if (typeof Worker === "undefined") {
    // ---- Node: fake both scopes, real modules, real structuredClone. ----
    const shellListeners = new Set<(ev: MessageEvent<WorkerResponse>) => void>();
    const fakeSelf = {
      onmessage: null as ((ev: MessageEvent<WorkerRequest>) => Promise<void>) | null,
      postMessage: (msg: WorkerResponse, transfer?: ArrayBuffer[]) => {
        const cloned = structuredClone(msg, { transfer: transfer ?? [] });
        posted.push({ msg: cloned, transfer });
        const ev = { data: cloned } as MessageEvent<WorkerResponse>;
        for (const fn of shellListeners) fn(ev);
        for (const fn of replyFns) fn(cloned);
      },
    };
    Object.defineProperty(globalThis, "self", {
      value: fakeSelf,
      writable: true,
      configurable: true,
    });
    await import("../../src/netwave.worker.ts");
    if (!fakeSelf.onmessage) throw new Error("worker did not register onmessage");
    const onmessage = fakeSelf.onmessage;
    class FakeWorker {
      onmessage: ((ev: MessageEvent<WorkerResponse>) => void) | null = null;
      constructor() {
        instances++;
      }
      addEventListener(_type: string, fn: (ev: MessageEvent<WorkerResponse>) => void) {
        shellListeners.add(fn);
      }
      postMessage(msg: WorkerRequest, options?: StructuredSerializeOptions) {
        posts++;
        const cloned = structuredClone(msg, options ?? {});
        void onmessage({ data: cloned } as unknown as MessageEvent<WorkerRequest>);
      }
    }
    Object.defineProperty(globalThis, "Worker", {
      value: FakeWorker,
      writable: true,
      configurable: true,
    });
  } else {
    // ---- Real browser: wrap native Worker to count + observe. ----
    const NativeWorker = Worker;
    class WrappedWorker extends NativeWorker {
      constructor(url: string | URL, options?: WorkerOptions) {
        super(url, options);
        instances++;
        this.addEventListener("message", (ev: MessageEvent<WorkerResponse>) => {
          posted.push({ msg: ev.data, transfer: undefined });
          for (const fn of replyFns) fn(ev.data);
        });
      }
      postMessage(
        msg: WorkerRequest,
        transfer?: StructuredSerializeOptions | Transferable[],
      ): void {
        posts++;
        const options: StructuredSerializeOptions = Array.isArray(transfer)
          ? { transfer }
          : (transfer ?? {});
        super.postMessage(msg, options);
      }
    }
    Object.defineProperty(globalThis, "Worker", {
      value: WrappedWorker,
      writable: true,
      configurable: true,
    });
  }

  return {
    posted,
    shellPosts: () => posts,
    workerInstances: () => instances,
    singleton: () =>
      (
        globalThis as unknown as {
          __netwaveWorker?: { postMessage: (m: WorkerRequest, t?: ArrayBuffer[]) => void };
        }
      ).__netwaveWorker,
    onReply: (fn) => {
      replyFns.add(fn);
      return () => replyFns.delete(fn);
    },
  };
}
