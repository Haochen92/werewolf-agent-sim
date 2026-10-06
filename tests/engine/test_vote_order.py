"""The seated humans vote before the agents.

One superstep used to fan every survivor out at once, and an interrupt only surfaces when its
superstep ends, so the seat's vote prompt arrived after the agents' ballots had dropped into
the jar (2026-10-06). Now START_VOTING fans the humans out first; VOTE_AGENTS fans the agents
out once their ballots are in; with no human seated the agents vote at once from START_VOTING.
"""
from __future__ import annotations

from langgraph.types import Send

from Agents.game_config import GameConfig
from Agents.graphs.day import build_day_graph
from Agents.nodes.day import flow
from Agents.nodes.day.flow import fan_out_agent_votes, fan_out_vote


def _state(human: str | None) -> dict:
    return {
        "current_day": 2, "current_round": 0, "day_channel": [], "day_summaries": [],
        "wolf_channel": [], "agent_strategies": {}, "investigator_results": [],
        "vigilante_results": [], "vigilante_bullets": 0, "no_lynch_streak": 0,
        "roles": {"player_1": "villager", "player_2": "wolf", "player_3": "healer"},
        "surviving_villagers": ["player_1", "player_3"], "surviving_wolves": ["player_2"],
        "human_players": [human] if human else [],
    }


def _nodes(sends) -> list[tuple[str, str]]:
    assert all(isinstance(s, Send) for s in sends)
    return [(s.node, s.arg["player_id"]) for s in sends]


def test_the_humans_vote_first_and_the_agents_after(monkeypatch):
    monkeypatch.setattr(flow, "game_config_from_runnable", lambda config: GameConfig())
    state = _state(human="player_3")
    assert _nodes(fan_out_vote(state, {})) == [("vote_human", "player_3")]
    assert _nodes(fan_out_agent_votes(state, {})) == [("vote", "player_1"), ("vote", "player_2")]


def test_with_no_human_seated_the_agents_vote_at_once(monkeypatch):
    monkeypatch.setattr(flow, "game_config_from_runnable", lambda config: GameConfig())
    sends = fan_out_vote(_state(human=None), {})
    assert _nodes(sends) == [("vote", "player_1"), ("vote", "player_2"), ("vote", "player_3")]
    assert all(s.arg["allow_abstain"] == GameConfig().abstain_enabled for s in sends)


def test_the_day_graph_routes_the_humans_ballots_through_the_agents_barrier():
    graph = build_day_graph()
    assert "VOTE_AGENTS" in graph.nodes
    assert ("vote_human", "VOTE_AGENTS") in {(e[0], e[1]) for e in graph.edges}
    assert ("vote", "COLLECT_VOTES") in {(e[0], e[1]) for e in graph.edges}
