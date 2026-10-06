"""A human's vote or night action is announced from the routing edge, before its step ends.

The agents' siblings run in the same parallel step, and an interrupt surfaces only when the
step is done, so the prompt used to arrive after the agents had acted (2026-10-06). The
announcement carries the targets the node will offer; the interrupt still takes the answer.
"""
from __future__ import annotations

from Agents.game_config import GameConfig
from Agents.nodes import orchestrator
from Agents.nodes.day import flow
from Agents.turn import human_turn


def _capture(monkeypatch, module):
    written: list[dict] = []
    monkeypatch.setattr(human_turn, "get_stream_writer", lambda: written.append)
    return written


def _day_state(human: str | None) -> dict:
    return {
        "current_day": 2, "current_round": 0, "day_channel": [], "day_summaries": [],
        "wolf_channel": [], "agent_strategies": {}, "investigator_results": [],
        "vigilante_results": [], "vigilante_bullets": 0, "no_lynch_streak": 0,
        "roles": {"player_1": "villager", "player_2": "wolf", "player_3": "healer"},
        "surviving_villagers": ["player_1", "player_3"], "surviving_wolves": ["player_2"],
        "human_players": [human] if human else [],
    }


def test_a_human_vote_is_announced_with_its_candidates(monkeypatch):
    monkeypatch.setattr(flow, "game_config_from_runnable", lambda config: GameConfig())
    written = _capture(monkeypatch, flow)
    sends = flow.fan_out_vote(_day_state(human="player_3"), {})
    assert [s.node for s in sends] == ["vote", "vote", "vote_human"]
    [ann] = written
    assert ann["event"] == "human_turn_opened"
    assert (ann["player"], ann["role"], ann["phase"], ann["day"]) == ("player_3", "healer", "day_votes", 2)
    assert ann["valid_targets"] == ["player_1", "player_2"] + (["abstain"] if GameConfig().abstain_enabled else [])
    assert flow.fan_out_vote(_day_state(human=None), {}) and len(written) == 1  # no human: nothing


def _night_state(**over) -> dict:
    s = {
        "current_day": 3, "human_players": [], "vigilante_bullets": 1,
        "surviving_wolves": ["player_6", "player_2"],
        "surviving_villagers": ["player_1", "player_3", "player_8", "player_9"],
        "healer_player": "player_8", "investigator_player": "player_3",
        "serial_killer_player": None, "vigilante_player": "player_9",
    }
    s.update(over)
    return s


def test_a_human_solo_night_actor_is_announced_with_every_other_survivor(monkeypatch):
    written = _capture(monkeypatch, orchestrator)
    phases = orchestrator.route_night_actors(_night_state(human_players=["player_8", "player_9"]))
    assert "HEALER_NIGHT_PHASE" in phases and "VIGILANTE_NIGHT_PHASE" in phases
    by_player = {a["player"]: a for a in written}
    assert by_player["player_8"]["phase"] == "healer_target"
    assert by_player["player_8"]["valid_targets"] == ["player_1", "player_2", "player_3", "player_6", "player_9"]
    assert by_player["player_9"]["valid_targets"][-1] == "hold_fire"
    assert by_player["player_9"]["day"] == 3


def test_a_human_wolf_is_not_announced_the_pack_prompts_at_the_turn(monkeypatch):
    written = _capture(monkeypatch, orchestrator)
    orchestrator.route_night_actors(_night_state(human_players=["player_2"]))
    assert written == []
