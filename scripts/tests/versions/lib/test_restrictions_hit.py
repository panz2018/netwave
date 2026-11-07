"""Unit tests for lib.restrictions.is_restricted — combo hit semantics.

A recorded combo hits only when every package in it matches the current
locked version (design D2). Combos within one record are OR'd; untested
cross products must stay unrestricted."""

from lib.restrictions import is_restricted

RECORDS = [
    {
        "reason": "tsdown dts 管线与 TS7 初版不兼容",
        "combos": [
            {"npm:typescript": "7.0.0", "npm:tsdown": "0.23.0"},
            {"npm:typescript": "7.0.1", "npm:tsdown": "0.23.1"},
        ],
    }
]


class TestExactMatch:
    def test_full_match_hits(self):
        assert is_restricted({"npm:typescript": "7.0.0", "npm:tsdown": "0.23.0"}, RECORDS)

    def test_second_combo_hits(self):
        assert is_restricted({"npm:typescript": "7.0.1", "npm:tsdown": "0.23.1"}, RECORDS)

    def test_untested_cross_product_is_not_restricted(self):
        assert not is_restricted({"npm:typescript": "7.0.0", "npm:tsdown": "0.23.1"}, RECORDS)
        assert not is_restricted({"npm:typescript": "7.0.1", "npm:tsdown": "0.23.0"}, RECORDS)

    def test_one_package_off_by_patch_is_not_restricted(self):
        assert not is_restricted({"npm:typescript": "7.0.0", "npm:tsdown": "0.23.2"}, RECORDS)

    def test_extra_current_packages_do_not_block_a_hit(self):
        combo = {"npm:typescript": "7.0.0", "npm:tsdown": "0.23.0", "npm:tsdown-examples": "1.0.0"}
        assert is_restricted(combo, RECORDS)


class TestSinglePackageRecord:
    def test_single_package_bug_hits(self):
        records = [{"reason": "自身 bug", "combos": [{"cargo:foo": "1.2.3"}]}]
        assert is_restricted({"cargo:foo": "1.2.3"}, records)

    def test_other_version_of_same_package_passes(self):
        records = [{"reason": "自身 bug", "combos": [{"cargo:foo": "1.2.3"}]}]
        assert not is_restricted({"cargo:foo": "1.2.4"}, records)


class TestMissingPackage:
    def test_record_package_absent_from_current_combo_is_not_a_hit(self):
        assert not is_restricted({"npm:typescript": "7.0.0"}, RECORDS)

    def test_no_records_never_hits(self):
        assert not is_restricted({"npm:typescript": "7.0.0"}, [])
