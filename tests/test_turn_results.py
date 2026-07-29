"""Resolved-turn boundary: the engine returns domain actions and actor nodes own graph deltas."""

import pytest
from pydantic import TypeAdapter, ValidationError

from Agents.nodes.day import actors as day_actors
from Agents.nodes.night import healer as healer_node
from Agents.nodes.night import wolf as wolf_nodes
from Agents.schemas import DayChannel, DayVote, WolfChannel
from Agents.schemas.turn import (
    ResolvedDayDiscussion,
    ResolvedDayVote,
    ResolvedHealerTarget,
    ResolvedTurn,
    ResolvedWolfVote,
    TurnEffects,
)


def test_discriminated_union_roundtrips_and_rejects_wrong_entry_shape():
    adapter = TypeAdapter(ResolvedTurn)
    turn = adapter.validate_python({
        "kind": "day_vote",
        "entry": {"voter": "p1", "votee": "p2"},
        "effects": {},
    })
    assert isinstance(turn, ResolvedDayVote)

    with pytest.raises(ValidationError):
        adapter.validate_python({
            "kind": "day_vote",
            "entry": {"day": 1, "seq": 0, "player": "p1", "message": "hello"},
            "effects": {},
        })


def test_discuss_node_commits_one_entry_and_strategy(monkeypatch):
    entry = DayChannel(day=2, seq=0, player="p1", message="hello")
    monkeypatch.setattr(
        day_actors,
        "run_memory_informed_action",
        lambda *args, **kwargs: ResolvedDayDiscussion(
            entry=entry,
            effects=TurnEffects(strategy="press p2"),
        ),
    )

    update = day_actors.discuss(
        {"player_id": "p1", "player_role": "villager"},
        None,
        None,
    )

    assert update == {
        "day_channel": [entry],
        "agent_strategies": {"p1": "press p2"},
    }


def test_vote_node_commits_singleton_vote_list(monkeypatch):
    vote = DayVote(voter="p1", votee="p2")
    monkeypatch.setattr(
        day_actors,
        "run_memory_informed_action",
        lambda *args, **kwargs: ResolvedDayVote(entry=vote),
    )

    update = day_actors.vote(
        {"player_id": "p1", "player_role": "villager"},
        None,
        None,
    )

    assert update == {"day_votes": [vote]}


def test_single_actor_night_node_owns_target_channel(monkeypatch):
    monkeypatch.setattr(
        healer_node,
        "run_memory_informed_night_action",
        lambda *args, **kwargs: ResolvedHealerTarget(
            entry="p2",
            effects=TurnEffects(strategy="protect likely town"),
        ),
    )

    update = healer_node.healer_act({}, None, None)

    assert update == {
        "healer_target": "p2",
        "updated_strategy": "protect likely town",
    }


def test_wolf_vote_node_owns_wolf_channel_append(monkeypatch):
    entry = WolfChannel(day=2, round=3, wolf="w1", message="", vote="p2")
    monkeypatch.setattr(
        wolf_nodes,
        "run_memory_informed_night_action",
        lambda *args, **kwargs: ResolvedWolfVote(entry=entry),
    )

    update = wolf_nodes.wolf_night_vote({"player_id": "w1"}, None, None)

    assert update == {"wolf_channel": [entry]}
