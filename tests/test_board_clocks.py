"""The public-census criticality math (Agents/board_clocks.py): the census subtraction, the three
faction clocks, and the invariant that made the 2026-07-11 promotion sound — the census-derived
criticality must equal the true-role-map criticality (deaths reveal roles truthfully, so the two
count paths cannot diverge). No LLM, pure fixtures."""

from Agents.board_clocks import (
    alive_role_counts,
    criticality_from_census,
    criticality_from_counts,
)
from evaluation.src.loop.decision_scoring import query_criticality


def test_alive_role_counts_subtracts_revealed_dead():
    cast = {"wolf": 2, "serial_killer": 1, "villager": 3, "healer": 1, "investigator": 1, "vigilante": 1}
    roster = [{"role": "wolf"}, {"role": "villager"}]
    remaining = alive_role_counts(cast, roster)
    assert remaining["wolf"] == 1 and remaining["villager"] == 2 and remaining["serial_killer"] == 1


def test_alive_role_counts_accepts_object_records():
    class Dead:
        role = "healer"

    remaining = alive_role_counts({"healer": 1, "villager": 2}, [Dead()])
    assert remaining["healer"] == 0


def test_criticality_from_counts_matches_ruled_boards():
    # SK endgame (wolves swept, SK + 2 town): SK clock 1 -> dist 1, swing.
    assert criticality_from_counts(wolves=0, sk=1, town=2) == (3, 1, True)
    # Near town win (1 wolf, 3 town, no SK): evil clock 2, town clock 1 -> swing.
    assert criticality_from_counts(wolves=1, sk=0, town=3) == (4, 2, True)
    # Early board (2 wolves, 6 town, SK): all clocks far -> not swing.
    assert criticality_from_counts(wolves=2, sk=1, town=6) == (9, 5, False)


def test_census_criticality_equals_role_map_criticality():
    # The promotion invariant: census-derived == omniscient on the same board.
    cast = {"wolf": 2, "serial_killer": 1, "villager": 3, "healer": 1, "investigator": 1, "vigilante": 1}
    roster = [{"role": "wolf"}, {"role": "villager"}, {"role": "vigilante"}]
    roles = {"w2": "wolf", "sk": "serial_killer", "v2": "villager", "v3": "villager",
             "h": "healer", "inv": "investigator"}
    assert criticality_from_census(cast, roster) == query_criticality(list(roles), roles)


def test_census_criticality_none_without_census():
    assert criticality_from_census({}, []) is None
    assert criticality_from_census(None, None) is None
