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
from unittest.mock import MagicMock, patch

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


class TagCacheProvenanceTests(unittest.TestCase):
    """The (game_id, version) key once collided across a paired A/B (same game_id, different
    play). session_id/trace_id now partition the filename AND provenance is asserted on read."""

    def test_different_arms_do_not_collide(self) -> None:
        # Same game_id pinned across arms, but each arm has its own trace/session -> the two
        # must NOT share a cache file (the cross-arm "scored OFF with ON tags" bug).
        off = {"game_id": "g1", "session_id": "s_off", "trace_id": "t_off"}
        on = {"game_id": "g1", "session_id": "s_on", "trace_id": "t_on"}
        with tempfile.TemporaryDirectory() as d:
            with patch.object(dt, "tag_game", return_value=({(1, "p1"): {"v": "off"}}, {})) as m:
                dt.tag_game_cached(off, d)
            with patch.object(dt, "tag_game", return_value=({(1, "p1"): {"v": "on"}}, {})) as m2:
                disc_on, _ = dt.tag_game_cached(on, d)   # different arm -> tags fresh, no hit
                m2.assert_called_once()
            self.assertEqual(disc_on, {(1, "p1"): {"v": "on"}})
            self.assertEqual(len(list(Path(d).glob("g1.*.json"))), 2)  # two distinct files

    def test_present_but_mismatched_provenance_retags(self) -> None:
        rec = {"game_id": "g1", "session_id": "s1", "trace_id": "t1"}
        slug = dt._provenance_slug(rec)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / f"g1.{slug}.v2.json"
            # A file at the exact path but belonging to a DIFFERENT trace -> must not be trusted.
            path.write_text(json.dumps({
                "provenance": {"game_id": "g1", "session_id": "s1", "trace_id": "OTHER", "version": "v2"},
                "disc": {"1|p1": {"v": "foreign"}}, "night": {},
            }))
            with patch.object(dt, "tag_game", return_value=({(1, "p1"): {"v": "fresh"}}, {})) as m:
                disc, _ = dt.tag_game_cached(rec, d)
            m.assert_called_once()                          # mismatch -> re-tag, not foreign tags
            self.assertEqual(disc, {(1, "p1"): {"v": "fresh"}})

    def test_matching_provenance_hits(self) -> None:
        rec = {"game_id": "g1", "session_id": "s1", "trace_id": "t1"}
        with tempfile.TemporaryDirectory() as d:
            with patch.object(dt, "tag_game", return_value=({(2, "p3"): {"v": 1}}, {})) as m:
                dt.tag_game_cached(rec, d)                  # miss -> write with provenance
                dt.tag_game_cached(rec, d)                  # same play -> hit, no re-tag
            m.assert_called_once()


class TaggerFailureCounterTests(unittest.TestCase):
    """A swallowed per-day tag = silent credit degradation, so it must be LOUD (summary ERROR)
    and strict=True must re-raise."""

    def _record(self) -> dict:
        return {
            "game_id": "g1",
            "roles": {"p1": "villager"},
            "day_channel": [{"day": 1, "player": "p1", "message": "hi"}],
            "day_resolutions": [],
            "night_resolutions": [],
        }

    def _boom_llm(self):
        boom = MagicMock()
        boom.invoke.side_effect = RuntimeError("forced tag failure")
        structured = MagicMock()
        structured.with_structured_output.return_value = boom
        return structured

    def test_failure_logs_summary_error_and_returns_empty(self) -> None:
        with patch.object(dt, "get_llm_pro", return_value=self._boom_llm()):
            with self.assertLogs("evaluation.src.loop.discussion_tagger", level="ERROR") as cm:
                disc, night = dt.tag_game(self._record())
        self.assertEqual((disc, night), ({}, {}))           # degraded to empty, not a crash
        self.assertTrue(any("days produced EMPTY tags" in line for line in cm.output))

    def test_strict_reraises(self) -> None:
        with patch.object(dt, "get_llm_pro", return_value=self._boom_llm()):
            with self.assertRaises(RuntimeError):
                dt.tag_game(self._record(), strict=True)


if __name__ == "__main__":
    unittest.main()
