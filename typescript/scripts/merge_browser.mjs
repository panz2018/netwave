// Build step (runs after tsdown, before publish_shell): copy the browser
// package's already-built dist artifacts into this package's dist/ so the
// published `netwave` package is self-contained (single npm package, exports
// conditions select node vs browser). The browser package owns and builds every
// browser artifact (shell, standalone, worker, wasm binary + glue, constants,
// dts); this step only copies — it never rebuilds or rewrites them. The public
// dts hubs (index.d.ts / index.d.mts) are emitted by publish_shell, so the
// browser package's own index.d.ts hub is not copied here.
import { cpSync, existsSync, rmSync } from "node:fs";
import { join, resolve } from "node:path";

const browserDist = resolve("..", "browser", "dist");
if (!existsSync(browserDist)) {
  console.error(`browser dist not found at ${browserDist} — build it first: pnpm -C browser build`);
  process.exit(1);
}

// Files the browser package produces that this package re-publishes. The
// index.d.ts hub is excluded (publish_shell emits the node/browser hubs).
const files = [
  "index.browser.mjs",
  "index.browser.d.mts",
  "standalone.js",
  "netwave.worker.js",
  "constants.generated.mjs",
  "constants.generated.d.mts",
];

for (const name of files) {
  cpSync(join(browserDist, name), join("dist", name));
}

// The wasm directory (binary + wasm-bindgen glue + its package.json). Replace
// wholesale so a stale artifact from a prior crate name never lingers.
rmSync(join("dist", "wasm"), { recursive: true, force: true });
cpSync(join(browserDist, "wasm"), join("dist", "wasm"), { recursive: true });

for (const name of [...files, "wasm"]) {
  console.log(`merged ${resolve(join("dist", name))}`);
}
