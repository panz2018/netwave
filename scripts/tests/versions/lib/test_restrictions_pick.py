"""Unit tests for lib.restrictions.pick_unrestricted — target selection.

The helper answers "which version should the freshness report advertise as the
target for this package, given what the rest of the repo is locked to?".
Direction is not preset: the newest candidate wins whenever it is not part of
a recorded bad combo (design D4)."""

from lib.restrictions import pick_unrestricted

RECORDS = [
    {
        "reason": "tsdown dts 管线与 TS7 初版不兼容",
        "combos": [
            {"npm:typescript": "7.0.0", "npm:tsdown": "0.23.0"},
            {"npm:typescript": "7.0.1", "npm:tsdown": "0.23.1"},
        ],
    }
]


class TestNewestWinsWhenUnrestricted:
    def test_latest_candidate_returned_when_nothing_hits(self):
        peers = {"npm:tsdown": "0.22.0"}
        assert pick_unrestricted("npm:tsdown", ["0.23.0", "0.22.0"], peers, RECORDS) == "0.23.0"

    def test_no_records_at_all_returns_newest(self):
        assert pick_unrestricted("npm:tsdown", ["0.23.1", "0.23.0"], {}, []) == "0.23.1"

    def test_candidates_need_not_be_pre_sorted(self):
        peers = {"npm:tsdown": "0.22.0"}
        assert pick_unrestricted("npm:tsdown", ["0.22.0", "0.23.0"], peers, RECORDS) == "0.23.0"


class TestSkipsRecordedCombos:
    def test_restricted_newest_falls_back_to_next_unrestricted(self):
        peers = {"npm:typescript": "7.0.0"}
        assert pick_unrestricted("npm:tsdown", ["0.23.0", "0.23.1"], peers, RECORDS) == "0.23.1"

    def test_falls_back_past_several_restricted_versions(self):
        records = [
            {
                "reason": "r",
                "combos": [
                    {"npm:a": "9.0.0", "npm:b": "3.0.0"},
                    {"npm:a": "9.0.0", "npm:b": "2.0.0"},
                ],
            }
        ]
        peers = {"npm:a": "9.0.0"}
        candidates = ["3.0.0", "2.0.0", "1.0.0"]
        assert pick_unrestricted("npm:b", candidates, peers, records) == "1.0.0"

    def test_untested_cross_product_still_newest(self):
        peers = {"npm:typescript": "7.0.0"}
        assert pick_unrestricted("npm:tsdown", ["0.23.1", "0.23.0"], peers, RECORDS) == "0.23.1"


class TestNoUsableCandidate:
    def test_all_candidates_restricted_returns_none(self):
        peers = {"npm:typescript": "7.0.0"}
        assert pick_unrestricted("npm:tsdown", ["0.23.0"], peers, RECORDS) is None

    def test_empty_candidates_returns_none(self):
        assert pick_unrestricted("npm:tsdown", [], {}, RECORDS) is None
