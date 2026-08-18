"""Unconditioned wolf blending (the validated day-camouflage proxy) is computed over ALL
lynch days, excludes the wolf being lynched, and is distinct from the disaster-conditioned
wolf_blending_rate (which only samples wolf-elimination days). See
evidence/memory_system/effectiveness/paired_ab/experiment_log.md (blending follow-up)."""

from Agents.compute_metrics import compute_game_metrics
from Agents.schemas.metrics import DayResolutionMetric, Metrics


ROLES = {"w1": "wolf", "w2": "wolf", "t1": "villager", "t2": "villager", "t3": "villager"}


def _day(day, votes, voted_player, voted_player_role):
    return DayResolutionMetric(
        day=day,
        votes=[{"voter": a, "votee": b} for a, b in votes],
        voted_player=voted_player,
        voted_player_role=voted_player_role,
        vote_counts={},
        tied_players=[],
        no_vote=False,
    )


def _result(winner="villagers", current_day=2):
    return {
        "roles": ROLES,
        "surviving_wolves": [],
        "surviving_villagers": [],
        "winner": winner,
        "current_day": current_day,
    }


def _compute(day_resolutions):
    return compute_game_metrics(_result(), Metrics(day_resolutions=day_resolutions))


def test_unconditioned_blending_counts_all_lynch_days_and_excludes_self():
    # Day 1 (town lynched): w1 aligns with the lynch, w2 dissents -> 1/2.
    # Day 2 (wolf w1 lynched): w2 blends (votes w1), w1 is the target so his vote is excluded
    #   -> 1/1. Total across both days = 2 aligned / 3 votes.
    m = _compute([
        _day(1, [("w1", "t1"), ("w2", "t2"), ("t1", "t1")], "t1", "villager"),
        _day(2, [("w2", "w1"), ("w1", "w2"), ("t2", "w1")], "w1", "wolf"),
    ])
    assert m.wolf_blend_votes_aligned == 2
    assert m.wolf_blend_votes_total == 3
    assert abs(m.wolf_unconditioned_blending_rate - 2 / 3) < 1e-9


def test_distinct_from_conditioned_blending_rate():
    # The conditioned metric only sees the wolf-elim day (day 2): w2 blended -> 1.0.
    # The unconditioned metric also counts day 1's dissent -> 2/3. They must differ.
    m = _compute([
        _day(1, [("w1", "t1"), ("w2", "t2")], "t1", "villager"),
        _day(2, [("w2", "w1"), ("w1", "w2")], "w1", "wolf"),
    ])
    assert m.wolf_blending_rate == 1.0
    assert abs(m.wolf_unconditioned_blending_rate - 2 / 3) < 1e-9


def test_none_when_no_wolf_votes_on_lynch_days():
    # A lynch day with no surviving wolf voters -> denominator 0 -> None (absence != zero).
    m = _compute([_day(1, [("t1", "t2"), ("t2", "t2")], "t2", "villager")])
    assert m.wolf_blend_votes_total == 0
    assert m.wolf_unconditioned_blending_rate is None


def test_no_vote_day_contributes_nothing():
    # A day with no lynch (voted_player None) is skipped entirely.
    m = _compute([_day(1, [("w1", "t1")], None, None)])
    assert m.wolf_blend_votes_total == 0
    assert m.wolf_unconditioned_blending_rate is None
