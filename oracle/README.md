# oracle

Numeric reference and grading for netwave cross-validation. All cross-end
comparison happens here; each binding (core/python/node/wasm) only dumps its
own computed results into `tmp/` (gitignored).

## Layout

- `manifest.json` — cross-end grading tolerance contract (single source)
- `samples/` — shared Touchstone samples (`dut.s1p` / `dut.s2p` / `dut.s4p`)
- `LICENSE-NOTES.md` — provenance and licenses of borrowed samples
- `compare_cross.py` — horizontal-axis grader (four ends vs each other)
- `tmp/` — answer sheets dumped by the four ends (gitignored, layered
  `<end>/<sample>/<field>.bin`)

## Run

From the repo root:

```sh
pnpm check:cross
```

Or grade an existing dump directory directly (dumps must already exist):

```sh
python3 oracle/compare_cross.py oracle/tmp
```

Comparison tiers and tolerance layering are defined in the governance spec
([project-governance spec](../openspec/specs/project-governance/spec.md)) —
this README only points there, never restates.
