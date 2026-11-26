# netwave-browser

The browser binding: the wasm binary runs only inside the resident worker and is
consumed privately by the published `netwave` shell (the `typescript/` package).
This package owns and builds every browser artifact — the worker shell, the
standalone build, the wasm binary and its wasm-bindgen glue, the generated
constants, and the type declarations.

## Commands (run from the repo root)

| Command                      | What it does                                                                                                                                                       |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `pnpm -C browser build`      | Build every browser artifact: generate constants, `wasm-pack build --target web`, bundle the shells, publish shell                                                 |
| `pnpm -C browser test`       | Full browser test chain: toolchain probes, build, node-driven unit suite, instrumented real-browser rust coverage chain, real-browser e2e suite                    |
| `pnpm -C browser test:unit`  | vitest unit suite (v8 coverage)                                                                                                                                    |
| `pnpm -C browser test:e2e`   | vitest real-browser (playwright chromium) suite (v8 coverage)                                                                                                      |
| `pnpm -C browser dump <dir>` | browser-end cross-binding dump: real-browser harness (playwright chromium, static server over `dist/` + `oracle/samples/`) writing `<dir>/browser/*` answer sheets |
| `pnpm -C browser typecheck`  | `tsc --noEmit` type gate                                                                                                                                           |

## Local toolchain installers

The full `pnpm -C browser test` chain needs two tools that are not on the public
npm/cargo path. `browser/scripts/test.sh` only probes for them and prints the
matching command below when one is missing — it never installs anything itself.

| Script                                        | Purpose                                                                                                                                                                                                                                   | Usage (from repo root)                             |
| --------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `browser/scripts/install_wasi_sdk.sh`         | installs the **latest** wasi-sdk into `~/.local/opt/wasi-sdk` (official GitHub tarballs, no sudo); its stock clang compiles the wasm32 C runtime for the wasm rust coverage chain (gcc has no wasm32 backend)                             | `bash browser/scripts/install_wasi_sdk.sh`         |
| `browser/scripts/install_wasm_bindgen_cli.sh` | installs the `wasm-bindgen` CLI **matching the crate version** into `~/.local/bin` (glue and crate must be the same version or the runtime aborts); turns the instrumented `.wasm` into web-target JS glue that `wasm-pack` cannot expose | `bash browser/scripts/install_wasm_bindgen_cli.sh` |
