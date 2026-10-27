# scripts/versions — version governance domain

Every version pin in this repo, in one machine-readable registry, plus the
two tools that read it. The registry is the single source of truth for
"where versions are pinned"; prose docs link to it instead of copying
numbers. Spec: [dependency-upgrade](../../openspec/specs/dependency-upgrade/spec.md).

## Layout

| Path                | Role                                                                                                                                        |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `lib/registry.json` | The pin registry: every pin's location, category, upgrade method, pairings, known-bad (`blocked`) versions                                  |
| `check_versions.py` | Offline reconciliation gate: registry ↔ real files, two-way, plus consistency rules. Wired into `pnpm check:meta`                           |
| `check_outdated.py` | Networked freshness report (manual, never a CI gate): latest versions vs pins, with `blocked` fallbacks. Entry point: `pnpm check:outdated` |

## Usage (from repo root)

```bash
uv run python scripts/versions/check_versions.py   # offline gate (also: pnpm check:meta)
uv run python scripts/versions/check_outdated.py   # networked freshness (also: pnpm check:outdated)
```

Both run in the root uv tooling project (`pyproject.toml` / `uv.lock` at the
repo root); no global Python packages required.
