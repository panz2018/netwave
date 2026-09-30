// netwave/standalone — zero-build single-file ESM entry for plain HTML
// (fetches the wasm via the web-target glue's async init). Same async
// contract as the main entry; zero Node.js.
// Usage: <script type="module">
//   import { fillPattern } from "./standalone.js";
// </script>
// `.ts` specifier is legal under noEmit; publish_shell.mjs rewrites it to
// "./index.browser.mjs" in the dist output.
export {
  _fillPattern,
  _readElement,
  fillPattern,
  readElement,
} from "./index.browser.ts";
