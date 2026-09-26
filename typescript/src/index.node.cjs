// netwave node conditional shell (CJS twin of index.node.mjs): explicit
// named re-exports (no `export *`). Same async contract as the ESM shell.
// The generated binding index.node.generated.cjs is produced by `napi build`.
const {
  fillPattern: _napiFill,
  readElement: _napiRead,
} = require("../dist/index.node.generated.cjs");

/**
 * Allocate and fill an (nfreq, nports, nports) interleaved complex f64
 * buffer. @returns {Promise<{buffer: ArrayBuffer, byteOffset: number, length: number}>}
 */
async function fillPattern(nfreq, nports) {
  return _fillPattern(nfreq, nports);
}

/** Pass a view back into core and read an element. @returns {Promise<number>} */
async function readElement(buf, idx) {
  return _readElement(buf, idx);
}

/**
 * @internal Sync passthrough escape hatch; no stability guarantee.
 * napi returns an external Buffer (Uint8Array, byteOffset 0, underlying
 * ArrayBuffer exactly the same length). Convert to the contract shape.
 */
const _fillPattern = (nfreq, nports) => {
  const buf = _napiFill(nfreq, nports);
  return { buffer: buf.buffer, byteOffset: 0, length: buf.byteLength / 16 };
};

/** @internal Sync passthrough escape hatch. */
const _readElement = _napiRead;

module.exports = { fillPattern, readElement, _fillPattern, _readElement };
