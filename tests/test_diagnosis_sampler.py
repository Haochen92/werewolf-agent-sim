"""Diagnosis case sampler: the outcome-halo guard, deterministic outlier + cohort selection, the
computed (not LLM-filled) leverage anchor, the uncalibrated-judge flag, and the verdict record."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from Agents.schemas import DayVote
from Agents.schemas.evaluation import EvalCase, EvalPrivateContext, NightAction
from evaluation.src.diagnosis.sampler import (
    ReviewVerdict,
    append_verdict,
    assert_outcome_blind,
    build_scored_cases,
    decision_score,
    leverage_anchor,
    load_verdicts,
    select_review_cases,
    verdict_for,
)

# A 9-player 3-faction board (the standard casting).
ROLES = {
    "p1": "wolf", "p2": "villager", "p3": "villager", "p4": "investigator",
    "p5": "healer", "p6": "serial_killer", "p7": "wolf", "p8": "vigilante", "p9": "villager",
}
GAME_INDEX = {"g1": {"roles": ROLES, "game_id": "g1"}}
GAME_LENGTHS = {"g1": 5}


def _vote_case(obs_id: str, role: str, votee: str, *, day: int = 3,
               roster: list[str] | None = None, mem: bool = True) -> EvalCase:
    return EvalCase(
        trace_id="g1",
        observation_id=obs_id,
        span_name=f"span_{obs_id}",
        player_id="p2",
        player_role=role,
        day=day,
        round=0,
        action_phase="day_vote",
        memory_enabled=mem,
        agent_vote=DayVote(voter="p2", votee=votee),
        private_context=EvalPrivateContext(
            surviving_players=roster if roster is not None else list(ROLES)
        ),
    )


class OutcomeHaloGuardTests(unittest.TestCase):
    def test_outcome_signal_raises(self) -> None:
        for bad in ("winner", "won", "faction_won", "role_faction_won", "game_outcome", "who_won"):
            with self.assertRaises(ValueError, msg=bad):
                assert_outcome_blind(bad)

    def test_structural_signals_pass(self) -> None:
        for ok in ("decision_score", "is_swing", "distance_to_parity", "town_vote_accuracy"):
            assert_outcome_blind(ok)  # must not raise

    def test_select_refuses_outcome_source(self) -> None:
        with self.assertRaises(ValueError):
            select_review_cases([], GAME_INDEX, GAME_LENGTHS, outlier_source="winner")


class DecisionScoreTests(unittest.TestCase):
    def test_town_lens(self) -> None:
        self.assertEqual(decision_score(_vote_case("a", "villager", "p1"), ROLES), (1.0, "hit_threat"))
        self.assertEqual(decision_score(_vote_case("b", "villager", "p3"), ROLES), (-1.0, "mislynch"))
        self.assertEqual(decision_score(_vote_case("c", "villager", "abstain"), ROLES), (0.0, "abstain"))

    def test_deceiver_lens_is_own_win_condition(self) -> None:
        # a wolf driving a town mislynch is faction-CORRECT (+1), not a town hit.
        self.assertEqual(decision_score(_vote_case("d", "wolf", "p3"), ROLES), (1.0, "induced_mislynch"))

    def test_night_and_discussion(self) -> None:
        vig = EvalCase(trace_id="g1", observation_id="n", player_id="p8", player_role="vigilante",
                       day=2, round=0, action_phase="night_action", memory_enabled=True,
                       agent_night_action=NightAction(role="vigilante", target="p1"))
        self.assertEqual(decision_score(vig, ROLES), (1.0, "hit_threat"))
        disc = _vote_case("x", "villager", "p1")
        disc = disc.model_copy(update={"action_phase": "day_discussion", "agent_vote": None})
        self.assertIsNone(decision_score(disc, ROLES))


class LeverageAnchorTests(unittest.TestCase):
    def test_computed_from_board_not_fill(self) -> None:
        # 3 alive (1 wolf, 2 others) -> distance_to_parity = 1 -> is_swing True. A bogus
        # situation_dimensions fill must NOT be consulted (Phase-1: the fill is worse than a constant).
        case = _vote_case("s", "villager", "p2", roster=["p1", "p2", "p3"])
        case.situation_dimensions = [{"is_swing": False, "distance_to_parity": 99}]
        lev = leverage_anchor(case, ROLES)
        assert lev == {"players_alive": 3, "distance_to_parity": 1, "is_swing": True}

    def test_no_roster_returns_none(self) -> None:
        case = _vote_case("e", "wolf", "p2", roster=[])
        self.assertIsNone(leverage_anchor(case, ROLES))


class SelectionTests(unittest.TestCase):
    def _cases(self) -> list[EvalCase]:
        # full roster (not swing) so the outlier channel is isolated from leverage.
        return [
            _vote_case("hit", "villager", "p1"),       # +1 hit_threat  (outlier)
            _vote_case("miss", "villager", "p3"),      # -1 mislynch    (outlier)
            _vote_case("abs1", "villager", "abstain"),  # 0
            _vote_case("abs2", "healer", "abstain"),    # 0
        ]

    def test_outlier_selection_picks_extremes(self) -> None:
        selected = select_review_cases(
            self._cases(), GAME_INDEX, GAME_LENGTHS,
            n_outliers=2, n_leverage=0, cohort_per_bucket=0,
        )
        keys = {sc.key for sc in selected}
        self.assertEqual(keys, {"hit", "miss"})
        for sc in selected:
            self.assertIn("outlier:decision_score", sc.reasons)

    def test_deterministic_same_seed(self) -> None:
        kw = dict(n_outliers=1, n_leverage=0, cohort_per_bucket=1, cohort_max=2, seed=7)
        a = select_review_cases(self._cases(), GAME_INDEX, GAME_LENGTHS, **kw)
        b = select_review_cases(self._cases(), GAME_INDEX, GAME_LENGTHS, **kw)
        self.assertEqual([sc.key for sc in a], [sc.key for sc in b])

    def test_leverage_channel_flags_swing(self) -> None:
        swing = _vote_case("sw", "villager", "p2", roster=["p1", "p2", "p3"])
        selected = select_review_cases(
            [swing], GAME_INDEX, GAME_LENGTHS, n_outliers=0, n_leverage=1, cohort_per_bucket=0,
        )
        self.assertEqual(selected[0].reasons, ["leverage:is_swing"])

    def test_judge_source_flagged_uncalibrated(self) -> None:
        cases = self._cases()
        scores = {"hit": 5.0, "miss": 1.0, "abs1": 3.0, "abs2": 3.0}
        scored = build_scored_cases(
            cases, GAME_INDEX, outlier_source="app_judge_effectiveness", judge_scores=scores
        )
        self.assertTrue(all(sc.outlier_uncalibrated for sc in scored))
        selected = select_review_cases(
            cases, GAME_INDEX, GAME_LENGTHS,
            outlier_source="app_judge_effectiveness", judge_scores=scores,
            n_outliers=2, n_leverage=0, cohort_per_bucket=0,
        )
        # tails = deviations from median (3.0): hit (+2) and miss (-2).
        self.assertEqual({sc.key for sc in selected}, {"hit", "miss"})
        for sc in selected:
            self.assertTrue(any("uncalibrated" in r for r in sc.reasons))

    def test_memory_off_dropped(self) -> None:
        off = _vote_case("off", "villager", "p1", mem=False)
        scored = build_scored_cases([off], GAME_INDEX)
        self.assertEqual(scored, [])


class VerdictRecordTests(unittest.TestCase):
    def test_roundtrip(self) -> None:
        selected = select_review_cases(
            [_vote_case("hit", "villager", "p1")], GAME_INDEX, GAME_LENGTHS,
            n_outliers=1, n_leverage=0, cohort_per_bucket=0,
        )
        v = verdict_for(selected[0], reviewer="human", question="reads right?", verdict="good",
                        notes="clean threat hit")
        self.assertIsInstance(v, ReviewVerdict)
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "verdicts.jsonl"
            append_verdict(path, v)
            append_verdict(path, verdict_for(selected[0], reviewer="model:x", question="q", verdict="bad"))
            loaded = load_verdicts(path)
        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0].verdict, "good")
        self.assertEqual(loaded[0].observation_id, "hit")
        self.assertEqual(loaded[0].selection_reasons, ["outlier:decision_score"])
        self.assertEqual(loaded[1].reviewer, "model:x")


if __name__ == "__main__":
    unittest.main()
