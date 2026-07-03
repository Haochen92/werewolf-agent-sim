"""Aggregation-math + config tests for the canonical tagger runner (cli_runner/discussion_tagger_eval.py).

$0: ``tag_game`` (the only paid path — flash-lite) is stubbed with canned DayTags-shaped dicts, so
every mode's aggregation is exercised on tiny synthetic records without a real tagging pass. The
deluck/credit path (``_decision_credit``) is deterministic (pure roles lookup), so it runs for real.
"""

from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from evaluation.src.core.config_schema import TaggerEvalConfig
from evaluation.src.cli_runner import discussion_tagger_eval as te


def _cfg(mode: str, **kw) -> TaggerEvalConfig:
    kw.setdefault("pro_model", None)  # don't touch env in tests
    return TaggerEvalConfig(mode=mode, **kw)


def _tag(verdict="positive", framing="none", credibility="medium", role_reveal="none"):
    return {"verdict": verdict, "framing": framing, "credibility": credibility, "role_reveal": role_reveal}


def _write_sidecar(cases: list[dict]) -> str:
    d = tempfile.mkdtemp()
    p = Path(d) / "cases.jsonl"
    p.write_text("\n".join(json.dumps({"kind": "agent_action_eval", "output": {"eval_case": c}}) for c in cases))
    return str(p)


# ---------------------------------------------------------------------------


class ConfigTests(unittest.TestCase):
    def test_mode_default_glob_filled(self) -> None:
        self.assertEqual(_cfg("accuracy").batch_glob,
                         "batch_results/v6ab_baseline.jsonl batch_results/v6ab_skboth.jsonl")
        self.assertEqual(_cfg("skill").batch_glob, "evidence/v7_final/v2_full/gen*_on.jsonl")
        self.assertEqual(_cfg("deleak").batch_glob, "evidence/v7_final/v2_full/gen*_on.jsonl")

    def test_explicit_glob_preserved(self) -> None:
        self.assertEqual(_cfg("skill", batch_glob="foo/*.jsonl").batch_glob, "foo/*.jsonl")

    def test_json_round_trip(self) -> None:
        cfg = TaggerEvalConfig.model_validate_json(json.dumps(
            {"mode": "deleak", "n_games": 8, "tags_cache_dir": "x/y", "pro_model": None}))
        self.assertEqual(cfg.mode, "deleak")
        self.assertEqual(cfg.n_games, 8)
        self.assertEqual(str(cfg.tags_cache_dir), "x/y")


class TagCacheTests(unittest.TestCase):
    """`tagged` caches the immutable per-game tags so a paid re-run over the same dumps is free."""

    def test_cache_miss_then_hit(self) -> None:
        rec = {"game_id": "g1", "session_id": "s1", "trace_id": "t1"}
        ret = ({(2, "p3"): _tag("negative")}, {(2, "p3"): {"verdict": "neutral"}})
        with tempfile.TemporaryDirectory() as d:
            cfg = _cfg("skill", tags_cache_dir=Path(d))
            with patch.object(te, "tag_game", return_value=ret) as m:
                disc1, night1 = te.tagged(rec, cfg, show_outcome=False, speakers_only=False)
                disc2, night2 = te.tagged(rec, cfg, show_outcome=False, speakers_only=False)
            m.assert_called_once()                    # tagged once; second call hit the cache
            self.assertEqual(disc1, disc2)
            self.assertEqual(list(disc2.keys()), [(2, "p3")])   # (int day, str player) restored

    def test_outcome_axis_is_separate_cache_key(self) -> None:
        rec = {"game_id": "g1", "session_id": "s1", "trace_id": "t1"}
        with tempfile.TemporaryDirectory() as d:
            cfg = _cfg("skill", tags_cache_dir=Path(d))
            with patch.object(te, "tag_game", return_value=({(1, "p1"): _tag()}, {})) as m:
                te.tagged(rec, cfg, show_outcome=True, speakers_only=False)
                te.tagged(rec, cfg, show_outcome=False, speakers_only=False)  # different outcome -> re-tag
            self.assertEqual(m.call_count, 2)


class AccuracyModeTests(unittest.TestCase):
    def _record(self) -> dict:
        return {
            "game_id": "g1",
            "roles": {"p1": "investigator", "p2": "wolf", "p3": "serial_killer", "p4": "villager"},
            "day_channel": [
                {"day": 1, "player": "p1", "message": "I am the investigator, I investigated p2"},
                {"day": 1, "player": "p4", "message": "As the healer I saved p1"},  # explicit claim
                {"day": 1, "player": "p2", "message": "p1 is lying"},
            ],
            "day_summaries": [
                {"day": 1, "summary": "Role claims: p1 -> investigator"},
                {"day": 2, "summary": "Role claims: none"},
            ],
        }

    def test_accuracy_cross_tabs(self) -> None:
        disc = {
            (1, "p1"): _tag("positive", "legitimate", "high", "own_role_claim"),   # confirmed (detector agrees)
            (1, "p2"): _tag("negative", "manipulative", "low", "none"),
            (1, "p3"): _tag("neutral", "none", "medium", "none"),
            (1, "p4"): _tag("neutral", "none", "medium", "none"),                  # detector saw a claim -> MISSED
            (2, "p2"): _tag("positive", "manipulative", "medium", "own_role_claim"),  # no detector match -> tagger_only
        }
        with patch.object(te, "tag_game", return_value=(disc, {})):
            res = te.run_accuracy([self._record()], _cfg("accuracy"))
        rr = res["role_reveal"]
        self.assertEqual(rr["distribution"], {"own_role_claim": 2, "none": 3})
        self.assertEqual(rr["confirmed"], 1)
        self.assertEqual(rr["tagger_only"], 1)
        self.assertEqual(rr["missed_by_tagger"], 1)
        self.assertEqual(rr["detector_explicit_claims"], 2)
        self.assertEqual(rr["recall"], 0.5)
        self.assertEqual(res["framing_by_faction"]["town"], {"legitimate": 1, "none": 1})
        self.assertEqual(res["framing_by_faction"]["wolf"], {"manipulative": 2})
        self.assertEqual(res["framing_by_faction"]["serial_killer"], {"none": 1})
        self.assertEqual(res["credibility_by_faction"]["town"], {"high": 1, "medium": 1})


class SkillModeTests(unittest.TestCase):
    def _game(self, gid: str, winner: str) -> dict:
        roles = {"p1": "villager", "p2": "wolf", "p3": "serial_killer", "p4": "villager"}
        sidecar = _write_sidecar([
            {"action_phase": "day_vote", "player_role": "villager", "day": 1, "agent_vote": {"votee": "p2"}},
            {"action_phase": "day_vote", "player_role": "wolf", "day": 1, "agent_vote": {"votee": "p1"}},
            {"action_phase": "day_vote", "player_role": "serial_killer", "day": 1, "agent_vote": {"votee": "p1"}},
        ])
        return {
            "game_id": gid, "winner": winner, "roles": roles, "eval_cases_path": sidecar,
            "day_resolutions": [], "day_channel": [
                {"day": 1, "player": "p1", "message": "hi"},
                {"day": 1, "player": "p2", "message": "hello there friend"},
            ],
        }

    def test_skill_columns_and_partial_r(self) -> None:
        games = [self._game(f"g{i}", "villagers" if i % 2 else "wolves") for i in range(4)]

        def stub(record, *, show_outcome, speakers_only, strict):
            v = "positive" if show_outcome else "neutral"
            disc = {(1, "p1"): _tag(v), (1, "p4"): _tag(v), (1, "p2"): _tag("negative"), (1, "p3"): _tag("neutral")}
            return disc, {}

        with patch.object(te, "tag_game", side_effect=stub):
            res = te.run_skill(games, _cfg("skill"))
        town = res["factions"]["town"]
        self.assertEqual(town["n"], 4)
        self.assertEqual(town["columns"]["din"], [1.0, 1.0, 1.0, 1.0])    # positive (outcome-in)
        self.assertEqual(town["columns"]["dout"], [0.0, 0.0, 0.0, 0.0])   # neutral (blinded)
        self.assertEqual(town["columns"]["won"], [0.0, 1.0, 0.0, 1.0])    # villagers won on odd i
        self.assertEqual(town["columns"]["deluck"], [1.0, 1.0, 1.0, 1.0])  # villager voted the wolf -> positive
        for key in ("A_in_given_deluck", "B_out_given_deluck", "C_out_given_deluck_verbosity"):
            self.assertEqual(set(town[key]), {"r", "p", "n"})
            self.assertEqual(town[key]["n"], 4)
        self.assertEqual(res["factions"]["wolf"]["n"], 4)
        self.assertEqual(res["factions"]["wolf"]["columns"]["din"], [-1.0] * 4)


class DeleakUnitTests(unittest.TestCase):
    def test_favor(self) -> None:
        self.assertEqual(te._favor("town", "wolf"), 1)
        self.assertEqual(te._favor("town", "villager"), -1)
        self.assertEqual(te._favor("wolf", "wolf"), -1)
        self.assertEqual(te._favor("wolf", "villager"), 1)
        self.assertEqual(te._favor("serial_killer", "serial_killer"), -1)
        self.assertEqual(te._favor("town", None), 0)

    def test_coupling_matches_pearson_and_speaker_filter(self) -> None:
        from evaluation.src.core.stats import pearson
        # rows: (verdict, credibility, favor, spoke). 4 rows, one silent.
        rows = {"town": [(1.0, 2, 1, True), (-1.0, 0, -1, True), (1.0, 1, 1, False), (-1.0, 0, -1, True)]}
        out = te._coupling(rows, speakers_only=False)
        exp_r, _ = pearson([1.0, -1.0, 1.0, -1.0], [1, -1, 1, -1])
        self.assertAlmostEqual(out["town"]["disc_verdict"], exp_r)
        self.assertEqual(out["town"]["n"], 4)
        spk = te._coupling(rows, speakers_only=True)
        self.assertEqual(spk["town"]["n"], 3)  # the silent row dropped


class DeleakModeTests(unittest.TestCase):
    def _game(self, gid: str, lynch_role: str) -> dict:
        return {
            "game_id": gid,
            "roles": {"p1": "villager", "p4": "villager", "p5": "investigator", "p2": "wolf", "p3": "serial_killer"},
            "day_resolutions": [{"day": 1, "voted_player_role": lynch_role}],
            "day_channel": [
                {"day": 1, "player": "p1", "message": "a"},
                {"day": 1, "player": "p4", "message": "b"},
                {"day": 1, "player": "p5", "message": "c"},
                {"day": 1, "player": "p2", "message": "d"},
            ],  # p3 is silent -> exercises the all/speakers contrast
        }

    def test_deleak_cells_and_contrasts(self) -> None:
        games = [self._game("gA", "wolf"), self._game("gB", "villager"), self._game("gC", "serial_killer")]

        def stub(record, *, show_outcome, speakers_only, strict):
            base = "positive" if record["day_resolutions"][0]["voted_player_role"] == "wolf" else "negative"
            v = base if show_outcome else "neutral"          # outcome axis shifts the verdict
            disc = {(1, p): _tag(v, credibility="high") for p in record["roles"]}
            return disc, {}

        with patch.object(te, "tag_game", side_effect=stub):
            res = te.run_deleak(games, _cfg("deleak"))
        # 3 town players x 3 games = 9 town rows in the all cell; 1 SK silent per game.
        self.assertEqual(res["coupling"]["town"]["in/all"]["n"], 9)
        self.assertEqual(res["coupling"]["serial_killer"]["in/all"]["n"], 3)
        self.assertEqual(res["coupling"]["serial_killer"]["in/speakers"]["n"], 0)  # SK never spoke
        for f in te.FACTIONS:
            con = res["contrasts"][f]
            self.assertIn("mechanical_silent_player_effect", con)
            self.assertIn("outcome_leak_all_players", con)


class LoadRecordsTests(unittest.TestCase):
    """load_records reads via REPO_ROOT.glob; point REPO_ROOT at a tmp tree to exercise the caps."""

    def _write(self, root: Path, name: str, recs: list[dict]) -> None:
        (root / name).write_text("\n".join(json.dumps(r) for r in recs))

    def test_accuracy_per_source_cap(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            self._write(root, "a.jsonl", [{"roles": {"p1": "villager"}, "game_id": f"a{i}"} for i in range(5)])
            self._write(root, "b.jsonl", [{"roles": {"p1": "wolf"}, "game_id": f"b{i}"} for i in range(5)])
            with patch.object(te, "REPO_ROOT", root):
                recs, srcs = te.load_records(_cfg("accuracy", batch_glob="a.jsonl b.jsonl", max_games_per_source=2))
            self.assertEqual(len(recs), 4)   # first 2 of each file
            self.assertEqual(len(srcs), 2)

    def test_deleak_stride_subsample_needs_eval_cases(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            sc = _write_sidecar([])
            self._write(root, "g.jsonl",
                        [{"roles": {"p1": "villager"}, "game_id": f"g{i}", "eval_cases_path": sc} for i in range(6)])
            with patch.object(te, "REPO_ROOT", root):
                recs, _ = te.load_records(_cfg("deleak", batch_glob="g.jsonl", n_games=3))
            self.assertEqual(len(recs), 3)


if __name__ == "__main__":
    unittest.main()
