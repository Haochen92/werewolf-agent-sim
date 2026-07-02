"""Guard the deterministic truth-computation fns of the v6 dimension audit — they recompute each
gated dimension from a case's OWN frozen board, and the epistemic-split verdict rides on them being
exactly right. Pure, no LLM, synthetic fixtures."""

from Agents.schemas.evaluation import EvalCase, EvalPrivateContext
from evaluation.src.audits.dimension_audit import (
    ally_revealed_true_absent,
    ally_revealed_true_lynched,
    bullets_left_true,
    players_alive_true,
    rows_for_case,
)
from evaluation.src.loop.decision_scoring import query_criticality


def _case(role="wolf", pid="player_1", day=3, phase="day_vote", situation_dimensions=None, **pc):
    return EvalCase(player_id=pid, player_role=role, day=day, round=0, action_phase=phase,
                    memory_enabled=True, situation_dimensions=situation_dimensions or [],
                    private_context=EvalPrivateContext(**pc))


def test_players_alive_true_counts_roster():
    c = _case(surviving_players=["player_1", "player_2", "player_3"])
    assert players_alive_true(c) == 3


def test_query_criticality_town_lens():
    # 5 alive, 2 wolves -> others=3, dist=3-2=1 -> swing
    roles = {"p1": "wolf", "p2": "wolf", "p3": "villager", "p4": "villager", "p5": "serial_killer"}
    assert query_criticality(["p1", "p2", "p3", "p4", "p5"], roles) == (5, 1, True)
    # 9 alive, 2 wolves -> others=7, dist=5 -> not swing
    roles9 = {f"p{i}": "villager" for i in range(1, 10)}
    roles9["p1"] = roles9["p2"] = "wolf"
    assert query_criticality(list(roles9), roles9) == (9, 5, False)


def test_bullets_left_true_counts_prior_night_shots():
    # loadout 2; a shot on night 1 only (night 2 null); a day-3 decision sees nights 1 and 2.
    nr = [
        {"day": 1, "vigilante_target": "player_5"},
        {"day": 2, "vigilante_target": None},
        {"day": 3, "vigilante_target": "player_6"},  # night 3 is AFTER the day-3 decision -> excluded
    ]
    assert bullets_left_true(3, nr, loadout=2) == 1  # one prior shot (night 1)
    assert bullets_left_true(1, nr, loadout=2) == 2  # no nights before day 1
    assert bullets_left_true(2, nr, loadout=2) == 1  # night 1 only


def test_bullets_left_true_floors_at_zero():
    nr = [{"day": 1, "vigilante_target": "a"}, {"day": 2, "vigilante_target": "b"},
          {"day": 3, "vigilante_target": "c"}]
    assert bullets_left_true(9, nr, loadout=2) == 0  # spent both, never negative


def test_ally_revealed_absent_variant():
    roles = {"player_1": "wolf", "player_2": "wolf", "player_3": "villager"}
    # partner (player_2) still alive -> not revealed
    c_alive = _case(pid="player_1", surviving_wolves=["player_1", "player_2"])
    assert ally_revealed_true_absent(c_alive, roles) is False
    # partner gone from surviving_wolves -> revealed
    c_dead = _case(pid="player_1", surviving_wolves=["player_1"])
    assert ally_revealed_true_absent(c_dead, roles) is True


def test_ally_revealed_lynched_variant():
    roles = {"player_1": "wolf", "player_2": "wolf", "player_3": "villager"}
    dr = [{"day": 1, "voted_player": "player_2", "voted_player_role": "wolf"}]
    c = _case(pid="player_1", day=3)
    assert ally_revealed_true_lynched(c, roles, dr) is True
    # a townie lynch does not count, and a same/future-day lynch is excluded
    dr_town = [{"day": 1, "voted_player": "player_3", "voted_player_role": "villager"}]
    assert ally_revealed_true_lynched(c, roles, dr_town) is False
    dr_future = [{"day": 3, "voted_player": "player_2", "voted_player_role": "wolf"}]
    assert ally_revealed_true_lynched(c, roles, dr_future) is False


def test_rows_for_case_scores_fill_vs_truth():
    # 9 alive, 2 wolves; wolf agent fills players_alive right but distance/is_swing wrong.
    roles = {f"player_{i}": "villager" for i in range(1, 10)}
    roles["player_1"] = roles["player_2"] = "wolf"
    dims = [{"players_alive": 9, "distance_to_parity": 3, "is_swing": False, "ally_revealed": False}]
    c = _case(role="wolf", pid="player_1", day=2, surviving_players=list(roles),
              surviving_wolves=["player_1", "player_2"], situation_dimensions=dims)
    rec = {"roles": roles, "night_resolutions": [], "day_resolutions": []}
    rows, _ = rows_for_case(c, rec, "run", loadout=2)
    by_dim = {r["dim"]: r for r in rows}
    assert by_dim["players_alive"]["match"] is True and by_dim["players_alive"]["abs_err"] == 0
    # true dist = others(7) - wolves(2) = 5; filled 3 -> mismatch, abs_err 2, tagged true_fill (wolf)
    assert by_dim["distance_to_parity"]["true"] == 5
    assert by_dim["distance_to_parity"]["match"] is False
    assert by_dim["distance_to_parity"]["abs_err"] == 2
    assert by_dim["distance_to_parity"]["epistemic"] == "true_fill"
    assert by_dim["ally_revealed"]["match"] is True


def test_rows_for_case_town_role_tagged_vs_omniscient():
    roles = {f"player_{i}": "villager" for i in range(1, 6)}
    roles["player_1"] = "wolf"
    dims = [{"players_alive": 5, "distance_to_parity": 2, "is_swing": False}]
    c = _case(role="villager", pid="player_3", day=2, surviving_players=list(roles),
              situation_dimensions=dims)
    rec = {"roles": roles, "night_resolutions": [], "day_resolutions": []}
    rows, _ = rows_for_case(c, rec, "run", loadout=2)
    dist = next(r for r in rows if r["dim"] == "distance_to_parity")
    assert dist["epistemic"] == "vs_omniscient"  # a villager can't know the wolf count
