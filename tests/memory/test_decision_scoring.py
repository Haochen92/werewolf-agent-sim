"""The vote scorer's threat set, read from the role registry: a ten-seat pack or lone-killer role is
a threat hit, a neutral is not, and a nine-seat record scores as it did when the set was literal."""

from __future__ import annotations

import pytest

from Agents.memory.consolidation.decision_scoring import THREAT_ROLES, score_vote

NINE_SEAT = {"p1": "wolf", "p2": "serial_killer", "p3": "villager", "p4": "healer",
             "p5": "investigator", "p6": "vigilante"}
TEN_SEAT = {"p1": "chanteuse", "p2": "illusionist", "p3": "serial_killer", "p4": "necromancer",
            "p5": "speculator", "p6": "fortune_teller", "p7": "sentinel", "p8": "healer"}


def test_nine_seat_threats_are_unchanged():
    assert THREAT_ROLES & set(NINE_SEAT.values()) == {"wolf", "serial_killer"}


@pytest.mark.parametrize("votee,hit", [("p1", True), ("p2", True), ("p3", False), ("p4", False),
                                       ("p5", False), ("p6", False)])
def test_nine_seat_vote(votee, hit):
    out = score_vote(votee, NINE_SEAT)
    assert out.hit_threat is hit and out.is_town_mislynch is (not hit)


@pytest.mark.parametrize("votee", ["p1", "p2", "p3", "p4"])
def test_ten_seat_pack_and_lone_killer_are_threats(votee):
    out = score_vote(votee, TEN_SEAT)
    assert out.hit_threat and not out.is_town_mislynch


@pytest.mark.parametrize("votee", ["p5", "p6", "p7", "p8"])
def test_ten_seat_neutral_and_town_are_mislynches(votee):
    """Town wins with the neutral alive, so lynching it does not advance town."""
    out = score_vote(votee, TEN_SEAT)
    assert not out.hit_threat and out.is_town_mislynch


def test_abstain_is_its_own_bucket():
    out = score_vote("abstain", TEN_SEAT)
    assert out.is_abstain and not out.hit_threat and not out.is_town_mislynch
