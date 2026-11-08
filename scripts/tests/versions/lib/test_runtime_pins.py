"""Unit tests for lib.repository.runtime_pins — runtime and tool pins as
combo peers (design D2: `locked_versions ∪ runtime_pins`).

Python pins normalise to the minor line (the granularity the freshness
report compares at); rustc and CI action pins keep their pinned value.
The hit/miss fixtures prove a `pypi:python × pypi:numpy` record becomes
reachable once the python pin joins the peers map."""

from pathlib import Path

from lib.repository import runtime_pins
from lib.restrictions import is_restricted

RECORDS = [
    {
        "reason": "numpy 2.3.0 wheels missing for python 3.16",
        "combos": [{"pypi:python": "3.16", "pypi:numpy": "2.3.0"}],
    }
]


def _repo(tmp_path: Path) -> Path:
    (tmp_path / ".python-version").write_text("3.15\n", encoding="utf-8")
    (tmp_path / "rust-toolchain.toml").write_text(
        '[toolchain]\nchannel = "1.99.1"\n', encoding="utf-8"
    )
    wf = tmp_path / ".github" / "workflows"
    wf.mkdir(parents=True)
    (wf / "ci.yml").write_text(
        "jobs:\n  t:\n    steps:\n      - uses: actions/checkout@v4\n"
        "      - uses: dtolnay/rust-toolchain@stable\n",
        encoding="utf-8",
    )
    return tmp_path


class TestRuntimePins:
    def test_python_pin_normalised_to_minor(self, tmp_path):
        assert runtime_pins(_repo(tmp_path))["pypi:python"] == "3.15"

    def test_python_patch_pin_normalised_to_minor(self, tmp_path):
        (tmp_path / ".python-version").write_text("3.15.2\n", encoding="utf-8")
        assert runtime_pins(_repo(tmp_path))["pypi:python"] == "3.15"

    def test_rustc_pin_from_toolchain_channel(self, tmp_path):
        assert runtime_pins(_repo(tmp_path))["cargo:rustc"] == "1.99.1"

    def test_pnpm_pin_from_package_manager(self, tmp_path):
        # corepack takes pnpm from packageManager, so the repo field — not the
        # machine's global — is pnpm's real version
        (tmp_path / "package.json").write_text(
            '{"packageManager": "pnpm@12.18.0"}', encoding="utf-8"
        )
        assert runtime_pins(_repo(tmp_path))["npm:pnpm"] == "12.18.0"

    def test_action_pin_keyed_by_repo(self, tmp_path):
        assert runtime_pins(_repo(tmp_path))["github:actions/checkout"] == "v4"

    def test_moving_ref_action_kept_verbatim(self, tmp_path):
        assert runtime_pins(_repo(tmp_path))["github:dtolnay/rust-toolchain"] == "stable"

    def test_missing_files_omit_keys(self, tmp_path):
        assert runtime_pins(tmp_path) == {}

    def test_nvmrc_is_not_a_pin(self, tmp_path):
        # .nvmrc is a passive declaration — nvm does not auto-apply it, so it
        # cannot guarantee a machine's active node version and must never join
        # the peers map as if it did (a fake pin is worse than no pin)
        (tmp_path / ".nvmrc").write_text("26.13.0\n", encoding="utf-8")
        assert "npm:node" not in runtime_pins(_repo(tmp_path))

    def test_package_manager_absent_omits_pnpm_key(self, tmp_path):
        pins = runtime_pins(_repo(tmp_path))
        assert "npm:pnpm" not in pins


class TestRuntimePinJoinsCombos:
    def test_recorded_python_times_numpy_combo_hits(self, tmp_path):
        peers = {**runtime_pins(_repo(tmp_path)), "pypi:numpy": "2.3.0"}
        # the python bump the report would advertise (3.15 -> 3.16) hits the
        # recorded pairing, so the target must be adjusted instead
        assert is_restricted({**peers, "pypi:python": "3.16"}, RECORDS)

    def test_numpy_off_the_combo_line_misses(self, tmp_path):
        peers = {**runtime_pins(_repo(tmp_path)), "pypi:numpy": "2.4.0"}
        assert not is_restricted({**peers, "pypi:python": "3.16"}, RECORDS)
