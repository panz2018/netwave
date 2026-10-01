// netwave/standalone — zero-build single-file ESM entry for plain HTML
// (ironclad rule 8: the entry self-hosts the resident worker; the main
// thread never touches wasm). Same async contract as the browser shell;
// zero Node.js, zero `_` sync surface.
// Usage: <script type="module">
//   import { upload, readElement, release } from "./standalone.js";
// </script>
// `.ts` specifier is legal under noEmit; publish_shell.mjs rewrites it to
// "./index.browser.mjs" in the dist output (same-origin Pages deploy: the
// worker URL resolves relative to this module, no configuration needed).
export { fillPattern, readElement, release, upload } from "./index.browser.ts";
