# scripts/versions — version consistency gate & freshness check

Version pins live in the files that carry them (`rust-toolchain.toml`,
`.python-version`, `pyproject.toml`, `package.json`,
`.github/workflows/ci.yml`, lockfiles) — those files are the single source
of truth; prose docs point at paths instead of copying numbers. This domain
holds the two tools that police those pins: an offline rule gate and a
networked freshness report. Spec:
[dependency-upgrade](../../openspec/specs/dependency-upgrade/spec.md).

## Layout

| Path                | Role                                                                                                                                                                                                                                                       |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `check_versions.py` | Offline rule gate facade (four laws: rust-version, Python project, packageManager, CI python matrix coverage). Wired into `pnpm check:meta`                                                                                                                |
| `check_outdated.py` | Networked freshness report facade (manual, never a CI gate): latest LTS/stable versions vs pins. Entry point: `pnpm check:outdated`                                                                                                                        |
| `lib/version.py`    | Version parsing/comparison: `parse_version` (zero-padded triple), `is_exact`, `is_exact_patch`, `is_major_only`, `is_outdated`                                                                                                                             |
| `lib/repository.py` | Repo scanning & pin extraction: `ROOT`, `SKIP_DIRS` (single source), `find_files`, `find_python_versions`, `find_ci_workflows`, `workspace_members`, `rust_versions`, `toolchain_channel`, `ci_python_cells`, `find_package_managers`, `is_python_project` |
| `lib/rules.py`      | The four laws: `check_rust_version`, `check_python_projects`, `check_package_manager`, `check_ci_python_versions` (each returns error strings); plus `all_laws` / `summary`                                                                                |
| `lib/latest.py`     | Networked probes (only `check_outdated.py` consumes them): `fetch_json`, `run_cmd`, `first_line`, `latest_version`, `refine_node_lts`, `find_uv_projects`, `action_refs`, `is_version_tag`                                                                 |

Facades only assemble inputs, select checks, and aggregate the exit code;
judgement lives in `lib/`. Unit tests: `scripts/tests/` (pure logic,
fixtures only, offline — wired into `pnpm check:py` and the CI lint job).

## Exit codes

- `check_versions.py`: 0 = all laws hold, 1 = violations (each printed as
  `::error::` on stderr).
- `check_outdated.py`: always 0 — informational report, never a gate; a
  failing probe degrades to `WARN` and never aborts the rest.

## Usage (from repo root)

```bash
uv run python scripts/versions/check_versions.py   # offline gate (also: pnpm check:meta)
uv run python scripts/versions/check_outdated.py   # networked freshness (also: pnpm check:outdated)
```

Both run in the root uv tooling project (`pyproject.toml` / `uv.lock` at the
repo root); no global Python packages required.
