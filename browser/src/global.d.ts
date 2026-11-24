// Compile-time flag injected by the bundler's `define` (tsdown publish build
// fills `false`; both vitest configs fill `true`). Guarding coverage-chain
// code with `if (__NETWAVE_COVERAGE__)` lets dce-only + tree-shaking strip it
// from the published worker bundle. Declared here so `tsc --noEmit` resolves
// the bare identifier (mirrors Vue/React `__DEV__`).
declare const __NETWAVE_COVERAGE__: boolean;
