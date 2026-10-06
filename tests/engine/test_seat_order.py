"""A turn's survivor list is in seat order, whatever bucket a player came from.

The engine keeps the wolves and everyone else in two lists and joined them as they were, so
every prompt's "Surviving players" line and the human seat's candidate chips named one faction
before the other (2026-10-06: the vote chips read 3, 4, 5, 7, 9, then 2, 6, the two wolves).
"""
from __future__ import annotations

from types import SimpleNamespace

from Agents.graphs import parent
from Agents.nodes.day.flow import build_speaker_send, fan_out_day
from Agents.rules.seats import seat_number, seat_order
from Agents.schemas import FiringReason


def _state(**over) -> dict:
    s = {
        "current_day": 2, "current_round": 0, "human_players": [], "day_channel": [],
        "day_summaries": [], "wolf_channel": [], "agent_strategies": {},
        "investigator_results": [], "vigilante_results": [], "vigilante_bullets": 0,
        "roles": {f"player_{i}": "villager" for i in range(1, 10)} | {"player_2": "wolf", "player_6": "wolf",
                                                                     "player_8": "healer"},
        "surviving_villagers": ["player_1", "player_3", "player_4", "player_5", "player_7", "player_8", "player_9"],
        "surviving_wolves": ["player_2", "player_6"],
        "healer_player": "player_8",
    }
    s.update(over)
    return s


SEATED = [f"player_{i}" for i in range(1, 10)]


def test_seat_order_sorts_by_seat_number_and_names_without_one_last():
    assert seat_order(["player_10", "player_2", "player_1"]) == ["player_1", "player_2", "player_10"]
    assert seat_order(["w1", "t0", "inv", "w0"]) == ["t0", "w0", "w1", "inv"]
    assert (seat_number("player_7"), seat_number("inv")) == (7, None)


def test_day_payloads_list_survivors_in_seat_order():
    send = build_speaker_send(_state(), "player_3", "villager", FiringReason(tier="proactive", owes=[]))
    assert send.arg["surviving_players"] == SEATED
    for send in fan_out_day(_state(), "vote", allow_abstain=True):
        assert send.arg["surviving_players"] == SEATED


def test_night_payloads_list_targets_in_seat_order(monkeypatch):
    seen = {}
    monkeypatch.setattr(parent, "healer_graph_compiled",
                        SimpleNamespace(invoke=lambda payload, **_: seen.update(payload) or {}))
    monkeypatch.setattr(parent, "child_runnable_config", lambda config: config)
    parent.healer_night_phase(_state(), {}, SimpleNamespace(context=None))
    assert seen["surviving_players"] == [p for p in SEATED if p != "player_8"]
