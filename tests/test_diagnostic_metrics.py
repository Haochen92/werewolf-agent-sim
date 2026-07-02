"""Diagnostic-tier per-game proxies adopted from the 2026-07-02 metrics audit
(evidence/metrics/metrics_audit/proxy_discovery_log.md §3): wolf_power_kill_rate,
town_accusation_precision, investigator_find_next_round_convergence. Definitions mirror the audit
runners (evaluation/src/experiments/{accusation_metrics,claim_conversion}.py); these synthetic-record
tests pin that the production computation matches those definitions. Deterministic, no LLM."""

from Agents.compute_metrics import (
    DIAGNOSTIC_METRICS,
    _metric_tier,
    compute_game_metrics,
)
from Agents.schemas.game_events import AddressedTarget, DayChannel
from Agents.schemas.metrics import (
    DayResolutionMetric,
    Metrics,
    NightResolutionMetric,
)

ROLES = {
    "inv": "investigator",
    "v1": "villager",
    "v2": "villager",
    "w1": "wolf",
    "w2": "wolf",
    "sk": "serial_killer",
    "healer": "healer",
}


def _msg(day, seq, player, targets=(), passed=False, message="msg"):
    return DayChannel(
        day=day,
        seq=seq,
        player=player,
        message="" if passed else message,
        passed=passed,
        addressed_targets=[
            AddressedTarget(target=t, addressed_form="mention", stance=s) for t, s in targets
        ],
    )


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


def _night(day, investigator_target=None, investigator_target_role=None,
           wolves_target=None, wolf_target_role=None, kill_successful=False):
    return NightResolutionMetric(
        day=day,
        wolves_target=wolves_target,
        wolf_target_role=wolf_target_role,
        healer_target=None,
        investigator_target=investigator_target,
        investigator_target_role=investigator_target_role,
        kill_successful=kill_successful,
        healer_saved=False,
    )


def _result(day_channel, winner="villagers", current_day=3):
    return {
        "roles": ROLES,
        "surviving_wolves": [],
        "surviving_villagers": [],
        "winner": winner,
        "current_day": current_day,
        "day_channel": day_channel,
    }


def _compute(day_channel, day_res=None, night_res=None):
    return compute_game_metrics(
        _result(day_channel),
        Metrics(day_resolutions=day_res or [], night_resolutions=night_res or []),
    )


# --------------------------------------------------------------------------- town_accusation_precision


def test_town_accusation_precision_counts_only_town_accusers_on_threats():
    # Town accusations: v1->w1 (threat), v2->v1 (town), inv->sk (threat). Wolf w1->v2 is NOT a town
    # accusation (excluded from denominator). Self-accusation and passes ignored.
    dc = [
        _msg(1, 0, "v1", [("w1", "accusation")]),
        _msg(1, 1, "v2", [("v1", "accusation")]),
        _msg(1, 2, "inv", [("sk", "accusation")]),
        _msg(1, 3, "w1", [("v2", "accusation")]),        # wolf accuser -> not counted
        _msg(1, 4, "v1", [("v1", "accusation")]),        # self-accusation -> skipped
        _msg(1, 5, "v2", passed=True),                    # pass -> skipped
    ]
    m = _compute(dc)
    assert m.town_accusations_total == 3
    assert m.town_accusations_on_threat == 2
    assert abs(m.town_accusation_precision - 2 / 3) < 1e-9


def test_town_accusation_precision_none_when_no_town_accusations():
    m = _compute([_msg(1, 0, "w1", [("v1", "accusation")])])  # only a wolf accuses
    assert m.town_accusations_total == 0
    assert m.town_accusation_precision is None


def test_town_accusation_precision_only_accusation_stance():
    dc = [
        _msg(1, 0, "v1", [("w1", "defense")]),      # not an accusation
        _msg(1, 1, "v2", [("w2", "agreement")]),    # not an accusation
    ]
    m = _compute(dc)
    assert m.town_accusations_total == 0
    assert m.town_accusation_precision is None


# --------------------------------------------------------------------------- convergence


def test_find_next_round_convergence_mean_over_finds():
    # Wolf w1 found on night 1 -> actionable day 2. Day-2 town votes: inv->w1, v1->w1, v2->w2.
    # w2 found on night 2 -> actionable day 3. Day-3 town votes: inv->v1 (0 on w2).
    night_res = [
        _night(1, investigator_target="w1", investigator_target_role="wolf"),
        _night(2, investigator_target="w2", investigator_target_role="wolf"),
    ]
    day_res = [
        _day(2, [("inv", "w1"), ("v1", "w1"), ("v2", "w2"), ("w1", "v1")], "w1", "wolf"),
        _day(3, [("inv", "v1")], "v1", "villager"),
    ]
    m = _compute([], day_res=day_res, night_res=night_res)
    # day2: 2 of 3 town votes on w1 = 2/3 ; day3: 0 of 1 on w2 = 0 ; mean = 1/3
    assert abs(m.investigator_find_next_round_convergence - (2 / 3 + 0) / 2) < 1e-9


def test_find_next_round_convergence_none_without_finds():
    day_res = [_day(2, [("inv", "w1")], "w1", "wolf")]
    m = _compute([], day_res=day_res, night_res=[_night(1)])
    assert m.investigator_find_next_round_convergence is None


def test_find_next_round_convergence_skips_find_with_no_next_round_town_votes():
    # Find on night 2, but there is no day-3 resolution -> skipped -> None.
    night_res = [_night(2, investigator_target="w1", investigator_target_role="wolf")]
    day_res = [_day(2, [("inv", "w1")], "w1", "wolf")]
    m = _compute([], day_res=day_res, night_res=night_res)
    assert m.investigator_find_next_round_convergence is None


# --------------------------------------------------------------------------- wolf_power_kill_rate


def test_wolf_power_kill_rate_is_kills_over_power_alive_nights():
    # Two nights, a power role (healer/inv/vig) alive both. Night 1 the wolves kill the healer.
    night_res = [
        _night(1, wolves_target="healer", wolf_target_role="healer", kill_successful=True),
        _night(2, wolves_target="v1", wolf_target_role="villager", kill_successful=True),
    ]
    day_res = [_day(1, [("v1", "w1")], None, None)]
    m = _compute([], day_res=day_res, night_res=night_res)
    assert m.power_roles_killed_by_wolves == 1
    assert m.power_role_alive_nights == 2
    assert abs(m.wolf_power_kill_rate - 0.5) < 1e-9


def test_wolf_power_kill_rate_none_without_power_alive_nights():
    m = _compute([], day_res=[], night_res=[])
    assert m.wolf_power_kill_rate is None


# --------------------------------------------------------------------------- tiering


def test_diagnostic_metrics_are_tiered_diagnostic_and_present_on_dump():
    m = _compute([_msg(1, 0, "v1", [("w1", "accusation")])])
    dump = m.model_dump()
    for name in DIAGNOSTIC_METRICS:
        assert name in dump, name
        assert _metric_tier(name) == "diagnostic", name
    # And they are NOT mislabeled into the trusted tiers.
    from Agents.compute_metrics import DO_NOT_USE_METRICS, VALIDATED_BASKET_METRICS
    assert not (DIAGNOSTIC_METRICS & VALIDATED_BASKET_METRICS)
    assert not (DIAGNOSTIC_METRICS & DO_NOT_USE_METRICS)
