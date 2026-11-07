"""Unit tests for lib.latest — pure helpers run offline; networked helpers
(`fetch_json`, `latest_version`, `refine_node_lts`) run against a swapped-out
`urlopen`/`fetch_json` so the tests assert call shapes (URLs, headers,
parsing, fallbacks) without touching the network. `run_cmd` runs real local
commands (echo / a missing binary) — subprocesses are not sockets."""

import json
import urllib.error
import urllib.request

import pytest
from lib import latest
from lib.latest import (
    action_refs,
    clean_version,
    fetch_json,
    find_uv_projects,
    first_line,
    is_version_tag,
    latest_version,
    package_versions,
    refine_node_lts,
    run_cmd,
)


class TestFirstLine:
    def test_banner_returns_first_non_empty(self):
        out = "\nrustup 1.28.1 (q: 1)\ncommit-hash: abc\n"
        assert first_line(out) == "rustup 1.28.1 (q: 1)"

    def test_blank_everywhere_returns_question(self):
        assert first_line("\n  \n") == "?"


class TestIsVersionTag:
    @pytest.mark.parametrize("tag", ["v1", "v1.2", "1.2.3", "7", "v0.0.11"])
    def test_version_shapes_are_tags(self, tag):
        assert is_version_tag(tag)

    @pytest.mark.parametrize("tag", ["stable", "main", "v3-stable", "nightly", ""])
    def test_branch_refs_are_not_tags(self, tag):
        assert not is_version_tag(tag)


class TestFindUvProjects:
    def test_sorted_by_lockfile_path_and_skips_excluded(self, tmp_path, monkeypatch):
        # regression: sort by lockfile path so `python/uv.lock` precedes
        # the root `uv.lock` — sorting by project dir would put root "."
        # first, which is the trap this avoids
        (tmp_path / "uv.lock").write_text("")
        (tmp_path / "python").mkdir()
        (tmp_path / "python" / "uv.lock").write_text("")
        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "x").mkdir()
        (tmp_path / "node_modules" / "x" / "uv.lock").write_text("")
        monkeypatch.setattr(latest, "ROOT", tmp_path)
        assert find_uv_projects() == ["python", "."]


class TestActionRefs:
    def test_collects_uses_refs_and_excludes_docker(self, tmp_path, monkeypatch):
        wf = tmp_path / ".github" / "workflows"
        wf.mkdir(parents=True)
        (wf / "ci.yml").write_text(
            "jobs:\n"
            "  a:\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "      - uses: docker://alpine:3.19\n"
            "      - uses: dtolnay/rust-toolchain@stable\n"
            "      - uses: owner/repo/sub@v1.2.3\n"
            "      - uses: no-at-sign-here\n"
        )
        monkeypatch.setattr(latest, "ROOT", tmp_path)
        assert action_refs() == {
            ("actions/checkout", "v4"),
            ("dtolnay/rust-toolchain", "stable"),
            ("owner/repo/sub", "v1.2.3"),
        }


def _capture_urlopen(payload, calls):
    """Fake urlopen returning `payload` (parsed as JSON by fetch_json) and
    recording the Request it was called with."""

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return json.dumps(payload).encode()

    def fake(req, timeout=None):
        calls.append(req)
        return _Resp()

    return fake


class TestFetchJson:
    def test_github_token_attached_for_github_api(self, monkeypatch):
        calls = []
        monkeypatch.setattr(urllib.request, "urlopen", _capture_urlopen({}, calls))
        monkeypatch.setenv("GITHUB_TOKEN", "tok123")
        fetch_json("https://api.github.com/repos/x/y/releases/latest")
        req = calls[0]
        assert req.get_header("Authorization") == "Bearer tok123"
        assert req.get_header("User-agent") == "netwave-check-outdated"

    def test_no_token_header_without_env(self, monkeypatch):
        calls = []
        monkeypatch.setattr(urllib.request, "urlopen", _capture_urlopen({}, calls))
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        fetch_json("https://api.github.com/repos/x/y")
        assert calls[0].get_header("Authorization") is None

    def test_token_never_leaks_to_non_github_hosts(self, monkeypatch):
        calls = []
        monkeypatch.setattr(urllib.request, "urlopen", _capture_urlopen({}, calls))
        monkeypatch.setenv("GITHUB_TOKEN", "tok123")
        fetch_json("https://registry.npmjs.org/pnpm")
        assert calls[0].get_header("Authorization") is None


class TestLatestVersion:
    def test_npm_dist_tag(self, monkeypatch):
        monkeypatch.setattr(latest, "fetch_json", lambda url: {"dist-tags": {"latest": "12.5.1"}})
        assert latest_version(("npm", "pnpm")) == "12.5.1"

    def test_github_release_tag(self, monkeypatch):
        monkeypatch.setattr(latest, "fetch_json", lambda url: {"tag_name": "v1.2.3"})
        assert latest_version(("github", "astral-sh/uv")) == "v1.2.3"

    def test_github_tags_first_entry(self, monkeypatch):
        monkeypatch.setattr(latest, "fetch_json", lambda url: [{"name": "v1.28.1"}])
        assert latest_version(("github-tags", "rust-lang/rustup")) == "v1.28.1"

    def test_github_tags_empty_returns_question(self, monkeypatch):
        monkeypatch.setattr(latest, "fetch_json", lambda url: [])
        assert latest_version(("github-tags", "some/repo")) == "?"

    def test_endoflife_lts_skips_non_lts_cycles(self, monkeypatch):
        monkeypatch.setattr(
            latest,
            "fetch_json",
            lambda url: [
                {"cycle": "27", "lts": False},
                {"cycle": "26", "lts": True},
                {"cycle": "24", "lts": True},
            ],
        )
        assert latest_version(("endoflife", "nodejs", "lts")) == "26"

    def test_endoflife_lts_none_available_returns_question(self, monkeypatch):
        monkeypatch.setattr(latest, "fetch_json", lambda url: [{"cycle": "27"}])
        assert latest_version(("endoflife", "nodejs", "lts")) == "?"

    def test_endoflife_stable_takes_first_cycle(self, monkeypatch):
        monkeypatch.setattr(latest, "fetch_json", lambda url: [{"cycle": "1.95"}])
        assert latest_version(("endoflife", "rust", "stable")) == "1.95"

    def test_unknown_endoflife_kind_raises(self, monkeypatch):
        monkeypatch.setattr(latest, "fetch_json", lambda url: [])
        with pytest.raises(ValueError, match="'eol'"):
            latest_version(("endoflife", "nodejs", "eol"))

    def test_unknown_source_kind_raises(self):
        with pytest.raises(ValueError, match="'gitlab'"):
            latest_version(("gitlab", "x/y"))


class TestPackageVersions:
    def test_npm_lists_stable_versions_sorted(self, monkeypatch):
        calls = []

        def fake(url):
            calls.append(url)
            return {"versions": {"0.23.1": {}, "0.23.10": {}, "0.23.2": {}, "1.0.0-rc.1": {}}}

        monkeypatch.setattr(latest, "fetch_json", fake)
        assert package_versions("npm", "tsdown") == ["0.23.1", "0.23.2", "0.23.10"]
        assert calls == ["https://registry.npmjs.org/tsdown"]

    def test_cargo_skips_yanked(self, monkeypatch):
        calls = []

        def fake(url):
            calls.append(url)
            return {"versions": [{"num": "0.30.0"}, {"num": "0.29.0", "yanked": True}]}

        monkeypatch.setattr(latest, "fetch_json", fake)
        assert package_versions("cargo", "numpy") == ["0.30.0"]
        assert calls == ["https://crates.io/api/v1/crates/numpy"]

    def test_pypi_skips_empty_releases(self, monkeypatch):
        calls = []

        def fake(url):
            calls.append(url)
            return {
                "releases": {
                    "2.1.0": [{"filename": "x"}],
                    "2.2.0": [],
                    "2.2.1": [{"filename": "y"}],
                }
            }

        monkeypatch.setattr(latest, "fetch_json", fake)
        assert package_versions("pypi", "numpy") == ["2.1.0", "2.2.1"]
        assert calls == ["https://pypi.org/pypi/numpy/json"]

    def test_unknown_ecosystem_raises(self):
        with pytest.raises(ValueError, match="'nuget'"):
            package_versions("nuget", "x")


class TestRefineNodeLts:
    def test_picks_newest_patch_on_lts_line(self, monkeypatch):
        monkeypatch.setattr(
            latest,
            "fetch_json",
            lambda url: [
                {"version": "v27.0.1"},
                {"version": "v26.12.1"},
                {"version": "v26.11.0"},
            ],
        )
        assert refine_node_lts("26") == "26.12.1"

    def test_no_match_falls_back_to_line(self, monkeypatch):
        monkeypatch.setattr(latest, "fetch_json", lambda url: [{"version": "v27.0.1"}])
        assert refine_node_lts("26") == "26"


class TestCleanVersion:
    # strip tool-name prefixes, `v` prefixes and parenthesized suffixes so
    # installed-vs-latest compares pure semver
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("uv 0.13.5 (aarch64-unknown-linux-gnu)", "0.13.5"),
            ("rustc 1.99.1 (58cf8f9c3 2026-10-13)", "1.99.1"),
            ("rustup 1.29.2 (d8c92c676 2026-10-21)", "1.29.2"),
            ("wasm-pack 0.15.0", "0.15.0"),
            ("wasm-opt version 133 (version_133)", "133"),
            ("markdownlint-cli2 v0.24.0 (markdownlint v0.42.0)", "0.24.0"),
            ("v26.12.1", "26.12.1"),
            ("12.5.1", "12.5.1"),
        ],
    )
    def test_strips_to_pure_version(self, raw, expected):
        assert clean_version(raw) == expected

    @pytest.mark.parametrize("raw", ["?", "stable", "not a version", ""])
    def test_unparseable_returns_none(self, raw):
        assert clean_version(raw) is None


class TestRunCmd:
    def test_success_returns_zero_and_stdout(self):
        rc, out = run_cmd("echo hello")
        assert rc == 0
        assert out == "hello"

    def test_missing_command_fails_without_raising(self):
        rc, out = run_cmd("netwave-no-such-cmd-xyz")
        assert rc != 0
        # shell error text lands on stderr and must be captured into out
        assert "not found" in out

    def test_internal_error_degrades_to_rc_125(self, monkeypatch):
        def boom(*args, **kwargs):
            raise OSError("fork failed")

        monkeypatch.setattr(latest.subprocess, "run", boom)
        rc, out = run_cmd("anything")
        assert rc == 125
        assert "fork failed" in out


def test_urlopen_failure_propagates_as_error_for_callers(monkeypatch):
    # callers rely on fetch_json raising so their WARN branches fire;
    # verify the raise path end-to-end through a failing fake
    def fail(req, timeout=None):
        raise urllib.error.URLError("rate limited")

    monkeypatch.setattr(urllib.request, "urlopen", fail)
    with pytest.raises(urllib.error.URLError, match="rate limited"):
        fetch_json("https://api.github.com/repos/x/y")
