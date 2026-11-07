"""Unit tests for lib.repository — discovery with skip dirs, pin extraction."""

from lib.repository import (
    SKIP_DIRS,
    ci_python_cells,
    find_ci_workflows,
    find_files,
    find_package_managers,
    find_python_versions,
    is_python_project,
    rust_versions,
    toolchain_channel,
    workspace_members,
)


def test_skip_dirs_cover_build_outputs():
    # regression for the drift fix: the outdated script used to miss these
    assert {"target", "target-wasm", "node_modules", ".venv", ".git", "dist", "coverage"} <= set(
        SKIP_DIRS
    )


def test_find_files_skips_excluded_dirs(tmp_path):
    (tmp_path / "keep").mkdir()
    (tmp_path / "keep" / ".python-version").write_text("3.14\n")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / ".python-version").write_text("3.9\n")
    (tmp_path / "target-wasm").mkdir()
    (tmp_path / "target-wasm" / ".python-version").write_text("3.9\n")
    found = find_files(tmp_path, ".python-version")
    assert found == {"keep/.python-version"}


def test_find_python_versions_reads_values(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / ".python-version").write_text("3.14\n")
    assert find_python_versions(tmp_path) == {"a/.python-version": "3.14"}


def test_workspace_members_from_root_manifest(tmp_path):
    (tmp_path / "Cargo.toml").write_text('[workspace]\nmembers = ["core", "python"]\n')
    assert workspace_members(tmp_path) == ["core/Cargo.toml", "python/Cargo.toml"]


def test_rust_versions_maps_pins_and_omits_missing(tmp_path):
    (tmp_path / "Cargo.toml").write_text('[workspace]\nmembers = ["a", "b", "ghost"]\n')
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "Cargo.toml").write_text('[package]\nrust-version = "1.90"\n')
    (tmp_path / "b").mkdir()
    (tmp_path / "b" / "Cargo.toml").write_text('[package]\nname = "b"\n')
    # "ghost" has no directory at all — rust_versions skips it (the law
    # reports it via workspace_members, not here)
    assert rust_versions(tmp_path) == {"a/Cargo.toml": "1.90"}


def test_toolchain_channel_reads_value(tmp_path):
    (tmp_path / "rust-toolchain.toml").write_text('[toolchain]\nchannel = "1.95.1"\n')
    assert toolchain_channel(tmp_path) == "1.95.1"


def test_find_ci_workflows_sorted(tmp_path):
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "b.yml").write_text("a: 1\n")
    (tmp_path / ".github" / "workflows" / "a.yml").write_text("a: 1\n")
    (tmp_path / ".github" / "workflows" / "c.yaml").write_text("a: 1\n")
    found = find_ci_workflows(tmp_path)
    assert [p.name for p in found] == ["a.yml", "b.yml"]


def test_find_ci_workflows_missing_dir_returns_empty(tmp_path):
    assert find_ci_workflows(tmp_path) == []


def test_ci_python_cells_include_list_and_inline_quoted_and_bare(tmp_path):
    (tmp_path / ".github" / "workflows").mkdir(parents=True)
    (tmp_path / ".github" / "workflows" / "ci.yml").write_text(
        "jobs:\n"
        "  t:\n"
        "    strategy:\n"
        "      matrix:\n"
        "        include:\n"
        '          - python-version: "3.10"\n'
        "          - python-version: 3.11\n"
        "  u:\n"
        "    steps:\n"
        "      - uses: actions/setup-python@v5\n"
        "        with:\n"
        '          python-version: "3.12"\n'
        "      - run: echo ${{ matrix.python-version }}\n"
    )
    # include-style matrix items (key on each item line, quoted or bare) and
    # inline step inputs are extracted; ${{ matrix... }} refs are not versions
    assert ci_python_cells(tmp_path) == {"3.10", "3.11", "3.12"}


def test_ci_python_cells_skips_excluded_dirs(tmp_path):
    (tmp_path / "node_modules" / "pkg").mkdir(parents=True)
    (tmp_path / "node_modules" / "pkg" / "ci.yml").write_text('python-version: "3.9"\n')
    assert ci_python_cells(tmp_path) == set()


def test_find_package_managers_only_files_carrying_field(tmp_path):
    (tmp_path / "package.json").write_text('{"packageManager": "pnpm@12.5.1"}\n')
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "package.json").write_text('{"name": "no-pm-field"}\n')
    found = find_package_managers(tmp_path)
    assert found == {"package.json": "pnpm@12.5.1"}


def test_is_python_project_parses_toml_not_substring():
    assert is_python_project('[project]\nname = "p"\n')
    assert not is_python_project("# [project] is only a comment\n")
    assert not is_python_project("[tool.uv]\npackage = false\n")
    assert not is_python_project("[project broken toml\n")
