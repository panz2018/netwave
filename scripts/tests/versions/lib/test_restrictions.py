"""Unit tests for lib.restrictions — loading and contract validation.

Contract (change add-version-restrictions, spec「限制记录读取的错误语义」):
missing file = no records; a file that exists but breaks the contract raises
RestrictionFormatError (never silently skipped)."""

import json

import pytest
from lib.restrictions import RestrictionFormatError, load_restrictions

DATA = {
    "restrictions": [
        {
            "reason": "tsdown dts 管线与 TS7 初版不兼容",
            "combos": [{"npm:typescript": "7.0.0", "npm:tsdown": "0.23.0"}],
        }
    ]
}


def _write(root, doc):
    path = root / "scripts" / "versions" / "restrictions.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


class TestLoadMissingFile:
    def test_missing_file_is_no_records_not_an_error(self, tmp_path):
        assert load_restrictions(tmp_path) == []


class TestLoadValidFile:
    def test_returns_reason_and_combos(self, tmp_path):
        _write(tmp_path, DATA)
        assert load_restrictions(tmp_path) == DATA["restrictions"]

    def test_empty_list_is_valid(self, tmp_path):
        _write(tmp_path, {"restrictions": []})
        assert load_restrictions(tmp_path) == []

    def test_single_package_combo_allowed(self, tmp_path):
        doc = {"restrictions": [{"reason": "自身 bug", "combos": [{"cargo:foo": "1.2.3"}]}]}
        _write(tmp_path, doc)
        assert load_restrictions(tmp_path) == doc["restrictions"]


class TestLoadFormatErrors:
    def test_invalid_json_raises(self, tmp_path):
        path = _write(tmp_path, DATA)
        path.write_text("{not json", encoding="utf-8")
        with pytest.raises(RestrictionFormatError):
            load_restrictions(tmp_path)

    def test_missing_restrictions_key_raises(self, tmp_path):
        _write(tmp_path, {"wrongs": []})
        with pytest.raises(RestrictionFormatError):
            load_restrictions(tmp_path)

    def test_missing_reason_raises(self, tmp_path):
        _write(tmp_path, {"restrictions": [{"combos": [{"npm:a": "1.0.0"}]}]})
        with pytest.raises(RestrictionFormatError):
            load_restrictions(tmp_path)

    def test_record_that_is_not_an_object_raises(self, tmp_path):
        _write(tmp_path, {"restrictions": ["just a string"]})
        with pytest.raises(RestrictionFormatError):
            load_restrictions(tmp_path)

    def test_top_level_that_is_not_an_object_raises(self, tmp_path):
        _write(tmp_path, [{"reason": "x", "combos": [{"npm:a": "1.0.0"}]}])
        with pytest.raises(RestrictionFormatError):
            load_restrictions(tmp_path)

    def test_missing_combos_raises(self, tmp_path):
        _write(tmp_path, {"restrictions": [{"reason": "x"}]})
        with pytest.raises(RestrictionFormatError):
            load_restrictions(tmp_path)

    def test_package_without_ecosystem_prefix_raises(self, tmp_path):
        _write(tmp_path, {"restrictions": [{"reason": "x", "combos": [{"typescript": "7.0.0"}]}]})
        with pytest.raises(RestrictionFormatError):
            load_restrictions(tmp_path)

    def test_empty_combo_raises(self, tmp_path):
        _write(tmp_path, {"restrictions": [{"reason": "x", "combos": [{}]}]})
        with pytest.raises(RestrictionFormatError):
            load_restrictions(tmp_path)

    def test_version_that_is_not_a_plain_number_raises(self, tmp_path):
        _write(tmp_path, {"restrictions": [{"reason": "x", "combos": [{"npm:a": ">=1.0.0"}]}]})
        with pytest.raises(RestrictionFormatError):
            load_restrictions(tmp_path)

    def test_error_message_names_the_offending_file(self, tmp_path):
        _write(tmp_path, {"restrictions": [{"reason": "x"}]})
        with pytest.raises(RestrictionFormatError, match="restrictions.json"):
            load_restrictions(tmp_path)
