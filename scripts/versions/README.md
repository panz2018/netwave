# scripts/versions — version consistency gate & freshness check

Version pins live in the files that carry them (`rust-toolchain.toml`,
`.python-version`, `pyproject.toml`, `package.json`,
`.github/workflows/ci.yml`, lockfiles) — those files are the single source
of truth; prose docs point at paths instead of copying numbers. This domain
holds the two tools that police those pins: an offline rule gate and a
networked freshness report. Spec:
[dependency-upgrade](../../openspec/specs/dependency-upgrade/spec.md).

## Layout

| Path                  | Role                                                                                                                                                                                                                                                                                                  |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `check_versions.py`   | Offline rule gate facade (four laws: rust-version, Python project, packageManager, CI python matrix coverage). Wired into `pnpm check:meta`                                                                                                                                                           |
| `check_outdated.py`   | Networked freshness report facade (manual, never a CI gate): latest LTS/stable versions vs pins. Entry point: `pnpm check:outdated`                                                                                                                                                                   |
| `lib/version.py`      | Version parsing/comparison: `parse_version` (zero-padded triple), `is_exact`, `is_exact_patch`, `is_major_only`, `is_outdated`                                                                                                                                                                        |
| `lib/repository.py`   | Repo scanning & pin extraction: `ROOT`, `SKIP_DIRS` (single source), `find_files`, `find_python_versions`, `find_ci_workflows`, `workspace_members`, `rust_versions`, `toolchain_channel`, `ci_python_cells`, `find_package_managers`, `is_python_project`                                            |
| `lib/rules.py`        | The four laws: `check_rust_version`, `check_python_projects`, `check_package_manager`, `check_ci_python_versions` (each returns error strings); plus `all_laws` / `summary`                                                                                                                           |
| `lib/latest.py`       | Networked probes (only `check_outdated.py` consumes them): `fetch_json`, `run_cmd`, `first_line`, `latest_version`, `package_versions`, `refine_node_lts`, `find_uv_projects`, `action_refs`, `is_version_tag`                                                                                        |
| `lib/restrictions.py` | Bad-version records (`restrictions.json`): `load_restrictions` (contract check, raises `RestrictionFormatError`), `is_restricted` (exact combo match), `pick_unrestricted` (highest candidate forming no recorded combo), `locked_versions` (ecosystem prefix → lockfile). Pure functions, no network |

Facades only assemble inputs, select checks, and aggregate the exit code;
judgement lives in `lib/`. Unit tests: `scripts/tests/versions/` (offline
fixtures plus swapped-out network/subprocess helpers — tests never reach the
network; an autouse guard in `scripts/tests/conftest.py` enforces this;
wired into `pnpm check:py`, which CI runs via `pnpm check`; discovery is
`testpaths` in root `pyproject.toml`). This domain's line coverage is held
at a 100% floor by `check:py`'s `--cov-fail-under` (threshold value defined
only in root `package.json`).

## Exit codes

- `check_versions.py`: 0 = all laws hold, 1 = violations (each printed as
  `::error::` on stderr).
- `check_outdated.py`: SKIP vs FAILED layering (spec「过期体检命令」).
  An unreachable source retries once, then its lines print `SKIP <source>`
  and the exit code is unaffected (network luck is not a failure).
  FAILED (non-zero exit, `FAILED:` names them) stays reserved for real
  errors: a local probe command that cannot run (`WARN`), or
  `restrictions.json` breaking its contract (the report aborts — a
  misleading judgement baseline must never drive upgrades). Informational
  report, never a gate — but a real failure is never hidden.

## Usage (from repo root)

```bash
uv run python scripts/versions/check_versions.py   # offline gate (also: pnpm check:meta)
uv run python scripts/versions/check_outdated.py   # networked freshness (also: pnpm check:outdated)
```

Both run in the root uv tooling project (`pyproject.toml` / `uv.lock` at the
repo root); no global Python packages required.

`check:outdated` runs automatically as the last task of every OpenSpec
apply (wired in `openspec/config.yaml`); the LAGs it reports are
pre-authorized upgrades per the dependency-upgrade spec. It can also be
run by hand any time.

## Registering a version restriction

`restrictions.json` (this directory) is the single carrier of bad-version
facts: which exact versions are unusable, and why. It is consumed by
`check_outdated.py` only — never by a CI gate; correctness stays with the
builds and tests that catch an unregistered bad version.

Register only what you have actually run and seen fail. An untested version
or combination MUST NOT be recorded (a record is a measurement, not a guess),
and records are append-only — never delete one, even after the upstream fix.

1. Reproduce the failure and keep the command + exit code, e.g.
   `pnpm -C typescript build:shells` → rc 1 with `typescript@X` and
   `tsdown@Y` installed.
2. Append a record to `scripts/versions/restrictions.json`:

   ```json
   {
     "restrictions": [
       {
         "reason": "one sentence: what breaks and where",
         "combos": [{ "npm:typescript": "7.0.2", "npm:tsdown": "0.23.0" }]
       }
     ]
   }
   ```

   - `reason` — one sentence, shared by every combo listed under it.
   - `combos` — every combination you actually tested and saw fail under that
     reason. One package per combo is fine (a package's own bug); N packages
     is the same shape (a pairing bug). Combos within a record are OR'd; the
     packages inside one combo are AND'd, so untested cross products stay
     allowed.
   - Package names carry an ecosystem prefix — `npm:` / `cargo:` / `pypi:` —
     because names collide across ecosystems (`numpy` is both a PyPI package
     and a Rust crate).
   - Runtime/tool pins join combos under prefixed names too
     (`pypi:python`, `cargo:rustc`), at the pin's own granularity (CPython
     minor): write every party of a measured runtime×library incompatibility
     into one combo, e.g.
     `{ "pypi:python": "3.16", "pypi:numpy": "2.3.0" }`.
   - Versions are the exact ones you tested. Ranges (`^`, `>=`, `*`) are
     rejected by the loader.

3. Tighten the pin in the manifest that carries it, same round: raise the
   lower bound of the existing range and keep its style (`^0.23.0` →
   `^0.23.2`). Never switch to `>=` and never add an upper bound the range
   did not have — that would widen the untested surface.
4. Verify: `pnpm check:outdated` prints a `SKIP <reason>` line for the
   package and advertises a target below the recorded version; the failing
   combination is gone from `pnpm install` output.
