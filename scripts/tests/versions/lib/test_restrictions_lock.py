"""Unit tests for lib.restrictions.locked_versions — ecosystem prefix to lockfile.

`npm:` reads pnpm-lock.yaml (regex on the `name@version:` keys, no YAML
dependency), `cargo:` reads Cargo.lock, `pypi:` reads every uv.lock found in
the repo (design D3). A package the repo does not lock is simply absent from
the result, so its record never hits and is kept (spec「限制记录读取的错误语义」).
"""

from lib.restrictions import is_restricted, locked_versions

RECORDS = [{"reason": "r", "combos": [{"npm:tsdown": "0.23.0", "cargo:numpy": "0.29.0"}]}]


def _npm_lock(root, *keys):
    body = "".join(f"  {k}:\n    resolution: x\n" for k in keys)
    text = f"lockfileVersion: '9.0'\n\npackages:\n{body}"
    (root / "pnpm-lock.yaml").write_text(text, encoding="utf-8")


def _cargo_lock(root, *pairs):
    body = "\n".join(f'[[package]]\nname = "{n}"\nversion = "{v}"\n' for n, v in pairs)
    (root / "Cargo.lock").write_text(body, encoding="utf-8")


def _uv_lock(root, subdir, *pairs):
    path = root / subdir
    path.mkdir(parents=True, exist_ok=True)
    body = "\n".join(f'[[package]]\nname = "{n}"\nversion = "{v}"\n' for n, v in pairs)
    (path / "uv.lock").write_text(body, encoding="utf-8")


class TestNpm:
    def test_plain_key(self, tmp_path):
        _npm_lock(tmp_path, "tsdown@0.23.0")
        assert locked_versions(tmp_path, ["npm:tsdown"]) == {"npm:tsdown": "0.23.0"}

    def test_scoped_package_key_quoted_as_pnpm_writes_it(self, tmp_path):
        (tmp_path / "pnpm-lock.yaml").write_text(
            "lockfileVersion: '9.0'\n\npackages:\n  '@types/node@24.0.0':\n    resolution: x\n",
            encoding="utf-8",
        )
        assert locked_versions(tmp_path, ["npm:@types/node"]) == {"npm:@types/node": "24.0.0"}

    def test_peer_suffixed_key_does_not_shadow_plain_key(self, tmp_path):
        _npm_lock(tmp_path, "tsdown@0.23.0", "tsdown@0.23.0(typescript@7.0.2)")
        assert locked_versions(tmp_path, ["npm:tsdown"]) == {"npm:tsdown": "0.23.0"}


class TestCargo:
    def test_package_table(self, tmp_path):
        _cargo_lock(tmp_path, ("numpy", "0.29.0"), ("serde", "1.0.200"))
        assert locked_versions(tmp_path, ["cargo:numpy"]) == {"cargo:numpy": "0.29.0"}


class TestPypi:
    def test_reads_every_uv_lock(self, tmp_path):
        _uv_lock(tmp_path, "python", ("numpy", "2.1.0"))
        _uv_lock(tmp_path, ".", ("pyyaml", "6.0.2"))
        got = locked_versions(tmp_path, ["pypi:numpy", "pypi:pyyaml"])
        assert got == {"pypi:numpy": "2.1.0", "pypi:pyyaml": "6.0.2"}

    def test_same_name_in_two_locks_agrees(self, tmp_path):
        _uv_lock(tmp_path, "python", ("numpy", "2.1.0"))
        _uv_lock(tmp_path, ".", ("numpy", "2.1.0"))
        assert locked_versions(tmp_path, ["pypi:numpy"]) == {"pypi:numpy": "2.1.0"}


class TestMultipleLockedVersions:
    def test_highest_locked_version_wins(self, tmp_path):
        # a transitive dep can pin an older line next to the direct one; the
        # version a fresh resolve lands on is the highest
        _npm_lock(tmp_path, "typescript@6.0.3", "typescript@7.0.2")
        assert locked_versions(tmp_path, ["npm:typescript"]) == {"npm:typescript": "7.0.2"}

    def test_highest_across_entries(self, tmp_path):
        _uv_lock(tmp_path, "python", ("numpy", "2.1.0"), ("numpy", "2.2.0"))
        assert locked_versions(tmp_path, ["pypi:numpy"]) == {"pypi:numpy": "2.2.0"}


class TestMissingThings:
    def test_unrequested_package_is_absent_and_record_does_not_hit(self, tmp_path):
        _npm_lock(tmp_path, "tsdown@0.23.1")
        combo = locked_versions(tmp_path, ["npm:tsdown", "cargo:numpy"])
        assert combo == {"npm:tsdown": "0.23.1"}
        assert not is_restricted(combo, RECORDS)

    def test_missing_lockfile_is_not_an_error(self, tmp_path):
        assert locked_versions(tmp_path, ["npm:tsdown", "cargo:numpy", "pypi:numpy"]) == {}

    def test_no_names_requested_reads_nothing(self, tmp_path):
        _npm_lock(tmp_path, "tsdown@0.23.0")
        assert locked_versions(tmp_path, []) == {}

    def test_unknown_ecosystem_prefix_is_absent(self, tmp_path):
        _npm_lock(tmp_path, "tsdown@0.23.0")
        assert locked_versions(tmp_path, ["nuget:tsdown"]) == {}
