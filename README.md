# netwave

_A frequency-domain scattering-matrix circuit solver for RF and photonics._

netwave is an S-parameter network engine: a Rust core computing on
`(nfreq, nports, nports)` interleaved complex f64 buffers, with thin
zero-copy bindings for Python (PyO3 + numpy), Node (napi-rs) and the
browser (wasm-bindgen). The bindings only move memory — every value is
computed once, in one place (`core/`).

The math is domain-agnostic: RF S-parameters and photonic S-parameters are
the same object (complex phasors on ports + a scattering matrix), so one
engine serves both. Reference impedance `z0` is a per-port attribute, not a
global constant — that is what lets RF algorithms be reused transparently in
optics.

Why this exists: pure-TypeScript stacks (e.g. `mathjs`-based
`RF-Touchstone`) drown in heap allocations and freeze on large Touchstone
files (>50 MB); netwave parses with `memmap2` + `rayon` (tens of
milliseconds for a 50 MB s4p) and shares one buffer across all three
language runtimes without copies. Byte layout is identical to scikit-rf
`Network.s` (complex128), so interop is a reinterpret, not a conversion.

Current stage: **scaffold** — the only public verb is `fill_pattern`, a
predictable-pattern allocator proving the zero-copy plumbing end to end. The
real `Network` / `SParameter` data model replaces it later.

Building from source or contributing? See
[CONTRIBUTING.md](CONTRIBUTING.md).

## License

Licensed under either of MIT or Apache-2.0, at your option. Full texts:
[LICENSE-MIT](LICENSE-MIT), [LICENSE-APACHE](LICENSE-APACHE). The software
is provided "as is", without warranty of any kind. `testdata/` has
separate terms — see [testdata/LICENSE-NOTES.md](testdata/LICENSE-NOTES.md).

Touchstone® is a registered trademark of Amphenol Corporation (formerly
Agilent Technologies).

## References

- scikit-rf (BSD-3-Clause) — <https://github.com/scikit-rf/scikit-rf>
- SignalIntegrity (GPL-3.0-or-later; algorithms referenced only, no code
  copied) — <https://github.com/Nubis-Communications/SignalIntegrity>
- Touchstone® File Format Specification v2.1 (IBIS Open Forum) —
  <https://ibis.org/touchstone_ver2.1/touchstone_ver2_1.pdf>
- P. J. Pupalaikis, _S-Parameters for Signal Integrity_, Cambridge
  University Press, 2020 — <https://doi.org/10.1017/9781108784863>
