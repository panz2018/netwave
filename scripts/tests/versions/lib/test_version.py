"""Unit tests for lib.version — version parsing and comparison."""

from lib.version import is_exact, is_exact_patch, is_major_only, is_outdated, parse_version


class TestParseVersion:
    def test_pads_missing_patch_to_zero(self):
        assert parse_version("1.85") == (1, 85, 0)

    def test_full_triple(self):
        assert parse_version("1.85.2") == (1, 85, 2)

    def test_strips_v_prefix(self):
        assert parse_version("v2.3.4") == (2, 3, 4)

    def test_major_only_pads(self):
        assert parse_version("v7") == (7, 0, 0)

    def test_two_and_three_equal(self):
        assert parse_version("1.85") == parse_version("1.85.0")


class TestIsExact:
    def test_exact_major_minor(self):
        assert is_exact("1.99")

    def test_exact_triple(self):
        assert is_exact("1.99.1")

    def test_rejects_major_only(self):
        assert not is_exact("1")

    def test_rejects_range_and_words(self):
        assert not is_exact(">=1.99")
        assert not is_exact("stable")
        assert not is_exact("")


class TestIsExactPatch:
    def test_full_triple(self):
        assert is_exact_patch("12.5.1")

    def test_rejects_two_component(self):
        # packageManager pins require all three components
        assert not is_exact_patch("12.5")
        assert not is_exact_patch("pnpm")


class TestIsMajorOnly:
    def test_v7_is_major_only(self):
        assert is_major_only("v7")

    def test_bare_major(self):
        assert is_major_only("3")

    def test_full_tag_not_major_only(self):
        assert not is_major_only("v10.2.0")
        assert not is_major_only("v0.0.11")


class TestIsOutdated:
    def test_lag_on_minor(self):
        assert is_outdated("1.85.0", "1.99.1")

    def test_not_outdated_when_equal(self):
        assert not is_outdated("1.99.1", "1.99.1")

    def test_not_outdated_when_ahead(self):
        assert not is_outdated("2.0.0", "1.99.1")

    def test_padded_compare(self):
        assert not is_outdated("1.85", "1.85.0")

    def test_major_only_compares_major(self):
        assert is_outdated("v6", "v7.1.0", major_only=True)
        assert not is_outdated("v7.1.0", "v7.9.9", major_only=True)
