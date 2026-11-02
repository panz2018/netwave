# scripts/versions — version consistency gate & freshness check

Version pins live in the files that carry them (`rust-toolchain.toml`,
`.python-version`, `pyproject.toml`, `package.json`,
`.github/workflows/ci.yml`, lockfiles) — those files are the single source
of truth; prose docs point at paths instead of copying numbers. This domain
holds the two tools that police those pins: an offline rule gate and a
networked freshness report. Spec:
[dependency-upgrade](../../openspec/specs/dependency-upgrade/spec.md).

## Layout

| Path                | Role                                                                                                                         |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `check_versions.py` | Offline rule gate (four laws: MSRV, Python project, packageManager, CI matrix coverage). Wired into `pnpm check:meta`        |
| `check_outdated.py` | Networked freshness report (manual, never a CI gate): latest LTS/stable versions vs pins. Entry point: `pnpm check:outdated` |

## Usage (from repo root)

```bash
uv run python scripts/versions/check_versions.py   # offline gate (also: pnpm check:meta)
uv run python scripts/versions/check_outdated.py   # networked freshness (also: pnpm check:outdated)
```

Both run in the root uv tooling project (`pyproject.toml` / `uv.lock` at the
repo root); no global Python packages required.
