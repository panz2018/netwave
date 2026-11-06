"""Unit tests for lib.rules — the four version laws, run against tmp fixture
repos (the gate's positive/negative fixtures from the dependency-upgrade
spec, made regression-testable)."""

from pathlib import Path

from lib.rules import (
    check_ci_python_versions,
    check_package_manager,
    check_python_projects,
    check_rust_version,
)


def make_repo(root: Path) -> None:
    """Minimal repo satisfying all four laws: one workspace member pinned
    1.99 against toolchain 1.99.1, one python project, exact packageManager,
    python matrix cell covering the pin."""
    (root / "Cargo.toml").write_text('[workspace]\nmembers = ["core"]\n')
    (root / "core").mkdir()
    (root / "core" / "Cargo.toml").write_text('[package]\nname = "core"\nrust-version = "1.99"\n')
    (root / "rust-toolchain.toml").write_text('[toolchain]\nchannel = "1.99.1"\n')
    (root / "pyproject.toml").write_text('[project]\nname = "p"\nrequires-python = ">=3.10"\n')
    (root / ".python-version").write_text("3.14\n")
    (root / "package.json").write_text('{"packageManager": "pnpm@12.5.1"}\n')
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / ".github" / "workflows" / "ci.yml").write_text(
        "jobs:\n"
        "  t:\n"
        "    strategy:\n"
        "      matrix:\n"
        "        include:\n"
        '          - python-version: "3.10"\n'
        '          - python-version: "3.14"\n'
    )


class TestRustVersionLaw:
    def test_clean_repo_passes(self, tmp_path):
        make_repo(tmp_path)
        assert check_rust_version(tmp_path) == []

    def test_missing_rust_version_fails(self, tmp_path):
        make_repo(tmp_path)
        (tmp_path / "core" / "Cargo.toml").write_text('[package]\nname = "core"\n')
        errors = check_rust_version(tmp_path)
        assert any(
            "core/Cargo.toml: workspace member missing rust-version pin" in e for e in errors
        )

    def test_drift_fails(self, tmp_path):
        make_repo(tmp_path)
        (tmp_path / "Cargo.toml").write_text('[workspace]\nmembers = ["core", "extra"]\n')
        (tmp_path / "extra").mkdir()
        (tmp_path / "extra" / "Cargo.toml").write_text(
            '[package]\nname = "extra"\nrust-version = "1.98"\n'
        )
        errors = check_rust_version(tmp_path)
        assert any("rust-version drift" in e for e in errors)

    def test_above_pin_fails(self, tmp_path):
        make_repo(tmp_path)
        (tmp_path / "core" / "Cargo.toml").write_text(
            '[package]\nname = "core"\nrust-version = "2.0"\n'
        )
        errors = check_rust_version(tmp_path)
        assert any("above rust-toolchain pin 1.99.1" in e for e in errors)

    def test_inexact_channel_fails(self, tmp_path):
        make_repo(tmp_path)
        (tmp_path / "rust-toolchain.toml").write_text('[toolchain]\nchannel = "stable"\n')
        errors = check_rust_version(tmp_path)
        assert any("is not an exact pin" in e for e in errors)

    def test_member_without_manifest_fails(self, tmp_path):
        make_repo(tmp_path)
        (tmp_path / "Cargo.toml").write_text('[workspace]\nmembers = ["ghost"]\n')
        errors = check_rust_version(tmp_path)
        assert any("ghost/Cargo.toml: workspace member has no Cargo.toml" in e for e in errors)


class TestPythonProjectLaw:
    def test_clean_repo_passes(self, tmp_path):
        make_repo(tmp_path)
        assert check_python_projects(tmp_path) == []

    def test_missing_requires_python_fails(self, tmp_path):
        make_repo(tmp_path)
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "p"\n')
        errors = check_python_projects(tmp_path)
        assert any("missing requires-python declaration" in e for e in errors)

    def test_missing_python_version_fails(self, tmp_path):
        make_repo(tmp_path)
        (tmp_path / ".python-version").unlink()
        errors = check_python_projects(tmp_path)
        assert any("no sibling .python-version pin" in e for e in errors)

    def test_comment_mentioning_project_not_counted(self, tmp_path):
        make_repo(tmp_path)
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "pyproject.toml").write_text("# [project] is only a comment\n")
        assert check_python_projects(tmp_path) == []


class TestPackageManagerLaw:
    def test_clean_repo_passes(self, tmp_path):
        make_repo(tmp_path)
        assert check_package_manager(tmp_path) == []

    def test_inexact_package_manager_fails(self, tmp_path):
        make_repo(tmp_path)
        (tmp_path / "package.json").write_text('{"packageManager": "pnpm@12"}\n')
        errors = check_package_manager(tmp_path)
        assert any("is not an exact pnpm version" in e for e in errors)

    def test_two_component_package_manager_fails(self, tmp_path):
        # the law requires a full major.minor.patch pin
        make_repo(tmp_path)
        (tmp_path / "package.json").write_text('{"packageManager": "pnpm@12.5"}\n')
        errors = check_package_manager(tmp_path)
        assert any("is not an exact pnpm version" in e for e in errors)

    def test_drift_fails(self, tmp_path):
        make_repo(tmp_path)
        (tmp_path / "sub").mkdir()
        (tmp_path / "sub" / "package.json").write_text('{"packageManager": "pnpm@9.0.0"}\n')
        errors = check_package_manager(tmp_path)
        assert any("packageManager drift" in e for e in errors)


class TestCiPythonVersionsLaw:
    def test_clean_repo_passes(self, tmp_path):
        make_repo(tmp_path)
        assert check_ci_python_versions(tmp_path) == []

    def test_uncovered_pin_fails(self, tmp_path):
        make_repo(tmp_path)
        (tmp_path / ".python-version").write_text("3.13\n")
        errors = check_ci_python_versions(tmp_path)
        assert any("not among ci python matrix cells" in e for e in errors)

    def test_no_ci_cells_skips_check(self, tmp_path):
        make_repo(tmp_path)
        (tmp_path / ".github" / "workflows" / "ci.yml").unlink()
        assert check_ci_python_versions(tmp_path) == []
