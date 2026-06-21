"""Guard tests for the tagger's structured inputs (A4 reasoning carrier + role_claims persist):
  - DaySummary.structured persists the in-game DaySummaryOutput (gameplay-neutral, for the tagger);
  - _role_claims_by_day reads it (empty for pre-A4 records);
  - _reasoning_by_day splits the agent's own updated_strategy into night vs discussion (attribution only).
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from Agents.schemas.game_events import DaySummary
from evaluation.src.loop import discussion_tagger as dt
from evaluation.src.loop.discussion_tagger import _reasoning_by_day, _role_claims_by_day


class DaySummaryStructuredTests(unittest.TestCase):
    def test_structured_roundtrips_and_defaults_empty(self) -> None:
        d = DaySummary(day=2, summary="prose",
                       structured={"role_claims": [{"player": "p5", "claimed_role": "investigator"}]})
        dump = d.model_dump()
        self.assertEqual(dump["structured"]["role_claims"][0]["claimed_role"], "investigator")
        self.assertEqual(DaySummary(day=1, summary="x").model_dump()["structured"], {})


class RoleClaimsByDayTests(unittest.TestCase):
    def test_reads_structured_role_claims(self) -> None:
        rec = {"day_summaries": [
            {"day": 2, "summary": "x", "structured": {"role_claims": [
                {"player": "p5", "claimed_role": "investigator", "evidence": "unverified"},
                {"player": "p1", "claimed_role": "healer", "evidence": "unverified"}]}},
            {"day": 3, "summary": "y", "structured": {"role_claims": []}},
        ]}
        out = _role_claims_by_day(rec)
        self.assertEqual(sorted(out[2]), [("p1", "healer"), ("p5", "investigator")])
        self.assertNotIn(3, out)  # empty claims -> no entry

    def test_empty_for_pre_a4_records(self) -> None:
        # old dumps have no structured field -> tagger falls back to judging from messages
        self.assertEqual(dict(_role_claims_by_day({"day_summaries": [{"day": 1, "summary": "x"}]})), {})
        self.assertEqual(dict(_role_claims_by_day({})), {})


class ReasoningByDayTests(unittest.TestCase):
    def _record(self, cases):
        d = tempfile.mkdtemp()
        p = Path(d) / "ec.jsonl"
        p.write_text("\n".join(json.dumps({"output": {"eval_case": c}}) for c in cases))
        return {"eval_cases_path": str(p)}

    def test_splits_night_vs_discussion(self) -> None:
        rec = self._record([
            {"action_phase": "night_action", "player_id": "p3", "day": 1, "updated_strategy": "kill the loud one"},
            {"action_phase": "day_discussion", "player_id": "p3", "day": 2, "updated_strategy": "lie low"},
            {"action_phase": "day_vote", "player_id": "p3", "day": 2, "updated_strategy": "ignored"},
            {"action_phase": "day_discussion", "player_id": "p7", "day": 2, "updated_strategy": ""},  # empty skipped
        ])
        night, disc = _reasoning_by_day(rec)
        self.assertEqual(night, {(1, "p3"): "kill the loud one"})
        self.assertEqual(disc, {(2, "p3"): "lie low"})  # day_vote excluded, empty skipped

    def test_missing_eval_path_is_empty(self) -> None:
        self.assertEqual(_reasoning_by_day({}), ({}, {}))
        self.assertEqual(_reasoning_by_day({"eval_cases_path": "/nonexistent.jsonl"}), ({}, {}))


class TagCacheTests(unittest.TestCase):
    def test_no_dir_tags_fresh(self) -> None:
        with patch.object(dt, "tag_game", return_value=({(1, "p1"): {"v": 1}}, {})) as m:
            disc, _ = dt.tag_game_cached({"game_id": "g1"}, None)
        m.assert_called_once()
        self.assertEqual(disc, {(1, "p1"): {"v": 1}})

    def test_persists_and_reuses_by_game_id(self) -> None:
        rec = {"game_id": "g1"}
        ret = ({(2, "p3"): {"verdict": "positive"}}, {(2, "p3"): {"verdict": "neutral"}})
        with tempfile.TemporaryDirectory() as d:
            with patch.object(dt, "tag_game", return_value=ret) as m:
                disc1, night1 = dt.tag_game_cached(rec, d)   # miss -> tag + write
                disc2, night2 = dt.tag_game_cached(rec, d)   # hit  -> read, no re-tag
            m.assert_called_once()                           # tagged exactly once
            self.assertEqual(disc1, disc2)
            self.assertEqual(night1, night2)
            self.assertEqual(list(disc2.keys()), [(2, "p3")])  # (int day, str player) restored

    def test_version_bump_invalidates(self) -> None:
        rec = {"game_id": "g1"}
        with tempfile.TemporaryDirectory() as d:
            with patch.object(dt, "tag_game", return_value=({(1, "p1"): {"v": 1}}, {})) as m:
                dt.tag_game_cached(rec, d, version="v1")
                dt.tag_game_cached(rec, d, version="v2")   # different version -> re-tag
            self.assertEqual(m.call_count, 2)


if __name__ == "__main__":
    unittest.main()
