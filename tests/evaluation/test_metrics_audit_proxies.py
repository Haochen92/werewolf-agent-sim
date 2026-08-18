"""Unit tests for the metrics-audit Workstream-1 parsing/join logic (Ideas A/B/C).

Covers the deterministic event parsing + joins only (not the correlations, which are data-dependent):
accusation-graph parsing/precision/credit/conversion (Idea B), the investigator find->next-round
convergence join (Idea C), the power-role-alive-nights denominator (Idea A), the role_claim coverage
probe (Idea C), and the partial_correlation / pearson helpers added to core.stats.
"""

from __future__ import annotations

import math

from evaluation.src.core.stats import partial_correlation, pearson
from evaluation.src.instrument_validation.proxies.accusation_metrics import accusations, game_metrics
from evaluation.src.instrument_validation.proxies.claim_conversion import (
    find_next_round_convergence,
    role_claim_coverage,
)
from evaluation.src.instrument_validation.proxies.proxy_rescue import _power_role_alive_nights

# p1,p2 town villagers; p3 wolf; p4 SK; p5 investigator; p6 vigilante
ROLES = {"p1": "villager", "p2": "villager", "p3": "wolf", "p4": "serial_killer",
         "p5": "investigator", "p6": "vigilante"}


def _msg(day, seq, player, targets, passed=False, message="msg"):
    return {"day": day, "seq": seq, "player": player, "passed": passed, "message": message,
            "addressed_targets": [{"stance": st, "target": tg} for tg, st in targets]}


def _accusation_record():
    return {
        "game_id": "g", "winner": "villagers", "roles": ROLES,
        "day_channel": [
            _msg(1, 1, "p1", [("p3", "accusation")]),               # town->threat, 1st accuser
            _msg(1, 2, "p2", [("p3", "accusation")]),               # town->threat, 2nd accuser (early)
            _msg(1, 3, "p1", [("p2", "accusation"), ("p9", "neutral")]),  # town->town (non-threat)
            _msg(1, 4, "p3", [("p1", "accusation")]),               # wolf->town
            _msg(1, 5, "p2", [("p2", "accusation")], passed=True),  # passed -> skipped
            _msg(1, 6, "p1", [("p1", "accusation")]),               # self -> skipped
            _msg(2, 1, "p5", [("p4", "accusation")]),               # investigator->SK, 1st accuser
        ],
        "day_resolutions": [
            {"day": 1, "votes": [{"voter": "p1", "votee": "p3"}, {"voter": "p2", "votee": "p3"},
                                 {"voter": "p5", "votee": "p1"}]},
            {"day": 2, "votes": [{"voter": "p5", "votee": "p4"}]},
        ],
        "night_resolutions": [],
    }


def test_accusations_parsing_orders_and_filters():
    evs = accusations(_accusation_record())
    # passed + self-accusation dropped; neutral stance dropped; ordered by (day, seq)
    got = [(e["day"], e["seq"], e["accuser"], e["target"]) for e in evs]
    assert got == [(1, 1, "p1", "p3"), (1, 2, "p2", "p3"), (1, 3, "p1", "p2"),
                   (1, 4, "p3", "p1"), (2, 1, "p5", "p4")]


def test_town_accusation_metrics():
    m = game_metrics(_accusation_record())
    # town accusations: p1->p3, p2->p3, p1->p2, p5->p4  => 4; on-threat = 3 (all but p1->p2)
    assert m["town_accusation_precision"] == 0.75
    # early credit: p1->p3 (rank1), p2->p3 (rank2), p5->p4 (rank1) are on-threat & rank<=2 => 3/4
    assert m["town_first_accuser_credit_rate"] == 0.75
    # conversion: p1->p3 (voted p3 d1), p2->p3 (voted p3 d1), p5->p4 (voted p4 d2) => 3/4
    assert m["town_accusation_to_vote_conversion"] == 0.75


def test_wolf_accusation_on_town_rate():
    m = game_metrics(_accusation_record())
    # only wolf accusation is p3->p1 (town) => 1/1
    assert m["wolf_accusation_on_town_rate"] == 1.0


def test_first_accuser_credit_excludes_late_accuser():
    rec = {
        "game_id": "g", "winner": "villagers", "roles": ROLES,
        "day_channel": [
            _msg(1, 1, "p1", [("p3", "accusation")]),  # rank1
            _msg(1, 2, "p2", [("p3", "accusation")]),  # rank2
            _msg(1, 3, "p6", [("p3", "accusation")]),  # rank3 -> NOT early
        ],
        "day_resolutions": [], "night_resolutions": [],
    }
    m = game_metrics(rec)
    assert m["town_accusation_precision"] == 1.0            # all 3 on the wolf
    assert m["town_first_accuser_credit_rate"] == 2 / 3     # 3rd accuser excluded


def test_find_next_round_convergence():
    rec = {
        "roles": ROLES,
        "night_resolutions": [
            {"day": 1, "investigator_target": "p3", "investigator_target_role": "wolf"},
        ],
        "day_resolutions": [
            {"day": 1, "votes": []},
            # next round (day 2): town voters p1,p2,p5,p6; 3 of 4 land on the found wolf p3
            {"day": 2, "votes": [{"voter": "p1", "votee": "p3"}, {"voter": "p2", "votee": "p3"},
                                 {"voter": "p5", "votee": "p4"}, {"voter": "p6", "votee": "p3"}]},
        ],
    }
    assert find_next_round_convergence(rec) == 0.75


def test_find_next_round_convergence_none_when_no_following_round():
    rec = {"roles": ROLES,
           "night_resolutions": [{"day": 3, "investigator_target": "p3",
                                  "investigator_target_role": "wolf"}],
           "day_resolutions": [{"day": 3, "votes": [{"voter": "p1", "votee": "p3"}]}]}
    assert find_next_round_convergence(rec) is None


def test_power_role_alive_nights():
    # p1 healer, p2 investigator, p3 vigilante are the power roles
    rec = {
        "roles": {"p1": "healer", "p2": "investigator", "p3": "vigilante",
                  "p4": "villager", "p5": "wolf"},
        "day_resolutions": [{"day": 1, "voted_player": "p2"}],  # investigator lynched day 1
        "night_resolutions": [
            {"day": 1, "deaths": ["p1"]},  # entering: p2 dead, p1/p3 alive -> counts; then p1 dies
            {"day": 2, "deaths": ["p3"]},  # entering: p3 alive -> counts; then p3 dies
            {"day": 3, "deaths": []},      # entering: no power role alive -> not counted
        ],
    }
    assert _power_role_alive_nights(rec) == 2


def test_role_claim_coverage_counts():
    absent = {"day_summaries": [{"day": 1, "structured": {}}]}
    present = {"day_summaries": [{"day": 1, "structured": {
        "role_claims": [{"player": "p1", "claimed_role": "healer"}]}}]}
    cov = role_claim_coverage([absent, present])
    assert cov == {"n_games": 2, "games_with_role_claims": 1, "total_role_claims": 1}


def test_pearson_basic():
    r, p = pearson([1, 2, 3, 4, 5], [2, 4, 6, 8, 10])
    assert math.isclose(r, 1.0, abs_tol=1e-9)


def test_partial_correlation_removes_common_driver():
    # x and y are both driven by z plus small independent wiggles -> high raw corr, low partial|z
    z = [1, 2, 3, 4, 5, 6, 7, 8]
    a = [0.3, -0.3, 0.3, -0.3, 0.3, -0.3, 0.3, -0.3]   # orthogonal to b
    b = [0.3, 0.3, -0.3, -0.3, 0.3, 0.3, -0.3, -0.3]
    x = [zi + ai for zi, ai in zip(z, a)]
    y = [zi + bi for zi, bi in zip(z, b)]
    raw, _ = pearson(x, y)
    pr, _, n = partial_correlation(x, y, [z])
    assert raw > 0.9
    assert abs(pr) < 0.5      # the shared z driver is partialled out
    assert n == 8


def test_partial_correlation_degenerate_returns_nan():
    r, p, n = partial_correlation([1, 1, 1], [1, 2, 3], [[1, 2, 3]])
    assert math.isnan(r) and n == 3
