"""A human's vote or night action is announced from the routing edge, before its step ends.

The agents' siblings run in the same parallel step, and an interrupt surfaces only when the
step is done, so the prompt used to arrive after the agents had acted (2026-10-06). The
announcement carries the targets the node will offer; the interrupt still takes the answer.
"""
from __future__ import annotations

from Agents.game_config import GameConfig
from Agents.nodes import orchestrator
from Agents.nodes.day import flow
from Agents.schemas.roles import lineup
from Agents.turn import human_turn

LINEUP = lineup("serial_killer", "speculator")


def _capture(monkeypatch, module):
    written: list[dict] = []
    monkeypatch.setattr(human_turn, "get_stream_writer", lambda: written.append)
    return written


def _day_state(human: str | None) -> dict:
    return {
        "current_day": 2, "current_round": 0, "day_channel": [], "day_summaries": [],
        "wolf_channel": [], "agent_strategies": {}, "night_actions": [],
        "uses_left": {"vigilante": 0}, "no_lynch_streak": 0,
        "roles": {"player_1": "sentinel", "player_2": "chanteuse", "player_3": "healer"},
        "lineup": LINEUP,
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
        "current_day": 3, "human_players": [], "uses_left": {"vigilante": 1},
        "lineup": LINEUP,
        "roles": {"player_1": "sentinel", "player_2": "illusionist", "player_3": "investigator",
                  "player_6": "chanteuse", "player_8": "healer", "player_9": "vigilante"},
        "surviving_wolves": ["player_6", "player_2"],
        "surviving_villagers": ["player_1", "player_3", "player_8", "player_9"],
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


def test_a_human_round_turn_is_announced_with_its_round(monkeypatch):
    written = _capture(monkeypatch, flow)
    state = _day_state(human="player_3")
    state["day_round"] = "opening"
    state["round_players"] = ["player_1", "player_2", "player_3"]

    sends = flow.fan_out_round(state, {})

    nodes = []
    for send in sends:
        nodes.append(send.node)
    assert nodes == ["round_turn", "round_turn", "round_turn_human"]
    (announcement,) = written
    assert announcement["event"] == "human_turn_opened"
    assert announcement["player"] == "player_3"
    assert announcement["phase"] == "day_channel"
    assert announcement["day_round"] == "opening"

    state["day_round"] = "closing"
    state["round_players"] = ["player_3"]
    flow.fan_out_round(state, {})
    assert written[1]["day_round"] == "closing"


def test_a_human_vote_announcement_carries_no_round(monkeypatch):
    monkeypatch.setattr(flow, "game_config_from_runnable", lambda config: GameConfig())
    written = _capture(monkeypatch, flow)

    flow.fan_out_vote(_day_state(human="player_3"), {})

    assert written[0]["day_round"] is None


def test_a_human_necromancers_announcement_carries_its_bodies(monkeypatch):
    from Agents.schemas.game_events import DeathRecord
    written = _capture(monkeypatch, orchestrator)
    state = _night_state(
        lineup=lineup("necromancer", "speculator"), human_players=["player_7"],
        roles={"player_1": "sentinel", "player_2": "illusionist", "player_6": "chanteuse",
               "player_7": "necromancer", "player_8": "healer"},
        surviving_villagers=["player_1", "player_7", "player_8"],
        dead_roster=[DeathRecord(player="player_9", role="vigilante", day=2, phase="night")],
    )
    orchestrator.route_night_actors(state)
    (ann,) = [a for a in written if a["player"] == "player_7"]
    assert ann["phase"] == "necromancer_target" and ann["bodies"] == ["player_9"]
    assert ann["valid_targets"][-1] == "stay_put"


def test_a_human_fortune_teller_is_offered_itself_only_while_a_self_bet_is_left(monkeypatch):
    written = _capture(monkeypatch, orchestrator)
    base = dict(lineup=lineup("serial_killer", "fortune_teller"), human_players=["player_4"],
                roles={"player_1": "sentinel", "player_2": "illusionist", "player_4": "fortune_teller",
                       "player_6": "chanteuse"},
                surviving_villagers=["player_1", "player_4"])
    orchestrator.route_night_actors(_night_state(**base, uses_left={"fortune_teller": 1}))
    orchestrator.route_night_actors(_night_state(**base, uses_left={"fortune_teller": 0}))
    first, second = [a["valid_targets"] for a in written if a["player"] == "player_4"]
    assert "player_4" in first and "player_4" not in second
