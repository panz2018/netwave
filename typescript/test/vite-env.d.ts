// Ambient declaration for vite's `?raw` import suffix (used by the worker
// source sentinel in test/wasm/worker.test.ts): the imported module's
// default export is the file's raw text. Vite resolves it at build/test
// time in both the Node and browser vitest realms; tsc only needs the type.
declare module "*?raw" {
  const src: string;
  export default src;
}
