"""Resolved-turn boundary: the engine returns domain actions and actor nodes own graph deltas."""

import pytest
from pydantic import TypeAdapter, ValidationError

from Agents.nodes.day import actors as day_actors
from Agents.nodes.night import pack as pack_nodes
from Agents.nodes.night import solo as solo_nodes
from Agents.schemas import DayChannel, DayVote, WolfChannel
from Agents.schemas.lineup_output import night_output
from Agents.schemas.night import NightChoice
from Agents.schemas.roles import lineup
from Agents.schemas.turn import (
    ResolvedDayDiscussion,
    ResolvedDayVote,
    ResolvedNightChoice,
    ResolvedTurn,
    ResolvedWolfDiscussion,
    TurnEffects,
)
from Agents.turn.resolve import _turn_effects, extract_agent_reasoning

LINEUP = lineup("serial_killer", "speculator")


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
        {"player_id": "p1", "player_role": "healer", "lineup": LINEUP},
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
        {"player_id": "p1", "player_role": "healer", "lineup": LINEUP},
        None,
        None,
    )

    assert update == {"day_votes": [vote]}


def test_solo_night_node_commits_its_choice_and_strategy(monkeypatch):
    choice = NightChoice("p1", "healer", "protect", "p2")
    monkeypatch.setattr(
        solo_nodes,
        "run_memory_informed_night_action",
        lambda *args, **kwargs: ResolvedNightChoice(
            entry=choice,
            effects=TurnEffects(strategy="protect likely town"),
        ),
    )
    state = {"roles": {"p1": "healer", "p2": "sentinel", "w1": "chanteuse"}, "lineup": LINEUP,
             "surviving_wolves": ["w1"], "surviving_villagers": ["p1", "p2"], "current_day": 1}

    update = solo_nodes.solo_night_phase("healer")(state, None, None)

    assert update == {
        "night_choices": [choice],
        "agent_strategies": {"p1": "protect likely town"},
    }


def test_a_declined_night_action_commits_no_choice(monkeypatch):
    monkeypatch.setattr(
        solo_nodes,
        "run_memory_informed_night_action",
        lambda *args, **kwargs: ResolvedNightChoice(entry=None),
    )
    state = {"roles": {"p1": "sigilist", "w1": "chanteuse"}, "lineup": LINEUP, "uses_left": {"sigilist": 2},
             "surviving_wolves": ["w1"], "surviving_villagers": ["p1"], "current_day": 2}

    assert solo_nodes.solo_night_phase("sigilist")(state, None, None) == {}


def test_carrier_node_commits_the_kill_as_a_choice_and_a_channel_entry(monkeypatch):
    kill = NightChoice("w1", "chanteuse", "kill", "p2")
    monkeypatch.setattr(
        pack_nodes,
        "run_memory_informed_night_action",
        lambda *args, **kwargs: ResolvedNightChoice(entry=kill),
    )

    update = pack_nodes.carrier_kill(
        {"player_id": "w1", "player_role": "chanteuse", "lineup": LINEUP, "current_day": 2}, None, None)

    assert update == {
        "night_choices": [kill],
        "wolves_target": "p2",
        "wolf_channel": [WolfChannel(day=2, round=pack_nodes.CARRIER_ROUND, wolf="w1", message="", vote="p2")],
    }


def test_pack_chat_node_owns_wolf_channel_append(monkeypatch):
    entry = WolfChannel(day=2, round=1, wolf="w1", message="take p2", vote="")
    monkeypatch.setattr(
        pack_nodes,
        "run_memory_informed_night_action",
        lambda *args, **kwargs: ResolvedWolfDiscussion(entry=entry),
    )

    update = pack_nodes.pack_chat({"player_id": "w1", "player_role": "chanteuse", "lineup": LINEUP}, None, None)

    assert update == {"wolf_channel": [entry]}


def test_pack_skill_node_commits_the_skill_or_nothing(monkeypatch):
    block = NightChoice("w1", "chanteuse", "block", "p3")
    payload = {"player_id": "w1", "player_role": "chanteuse", "lineup": LINEUP}
    monkeypatch.setattr(pack_nodes, "run_memory_informed_night_action",
                        lambda *args, **kwargs: ResolvedNightChoice(entry=block))
    assert pack_nodes.pack_skill(payload, None, None) == {"night_choices": [block]}

    monkeypatch.setattr(pack_nodes, "run_memory_informed_night_action",
                        lambda *args, **kwargs: ResolvedNightChoice(entry=None))  # no_conceal
    assert pack_nodes.pack_skill({**payload, "player_role": "illusionist"}, None, None) is None


def test_a_lineup_schemas_reads_resolve_into_turn_effects():
    # The reads come back as the lineup schema's own PlayerRead class; the turn's effects keep them.
    result = night_output("healer", LINEUP)(
        reads=[{"player": "p2", "why": "quiet", "suspected_role": "sentinel", "confidence": "low"}],
        updated_strategy="note", healer_target="p2",
    )
    effects = _turn_effects(extract_agent_reasoning(result))
    assert [read.player for read in effects.reads] == ["p2"]
