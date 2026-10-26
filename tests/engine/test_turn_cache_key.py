"""The turn-cache key must be VALUE-stable across a checkpoint round-trip, and separate games.

The cache's only job is to catch the re-executed superstep after a human resume — and
those re-run payloads are checkpoint-round-tripped stored Sends. LangGraph's default
pickle key differs there (pydantic __pydantic_fields_set__ changes), missing exactly
when it matters; turn_cache_key hashes canonical JSON values instead.
"""

from types import SimpleNamespace

import pytest
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from Agents.config.langgraph import build_runnable_config, turn_cache_key
from Agents.config.run import RunConfig
from Agents.nodes.day.flow import fan_out_round, start_opening
from Agents.nodes.night.pack import _pack_payload
from Agents.nodes.orchestrator import initialize_game
from Agents.memory.checkpointer import _STATE_MODEL_ALLOWLIST
from Agents.schemas.game_events import DayChannel


def _payload(**over):
    payload = {
        "human_player": False, "player_id": "player_2", "player_role": "villager",
        "day_channel": [DayChannel(day=1, seq=0, player="player_3", message="hi")],
        "current_day": 2, "allow_abstain": True,
        "surviving_players": ["player_2", "player_3"],
    }
    payload.update(over)
    return payload


def test_key_survives_a_checkpoint_round_trip():
    serde = JsonPlusSerializer(allowed_msgpack_modules=_STATE_MODEL_ALLOWLIST)
    original = _payload()
    roundtripped = serde.loads_typed(serde.dumps_typed(original))
    assert turn_cache_key(original) == turn_cache_key(roundtripped)


def test_key_separates_different_turns():
    assert turn_cache_key(_payload()) != turn_cache_key(_payload(player_id="player_3"))
    assert turn_cache_key(_payload()) != turn_cache_key(_payload(current_day=3))


def test_key_separates_games():
    assert turn_cache_key(_payload(game_id="game-a")) != turn_cache_key(_payload(game_id="game-b"))


class _StopAtInvoke(Exception):
    """Raised by the fake subgraphs once they have captured the wrapper's input."""


class _CapturingSubgraph:
    """Stands in for a compiled subgraph: records the input the wrapper built, then stops."""

    def __init__(self, captured: dict, name: str):
        self.captured = captured
        self.name = name

    def invoke(self, payload, **kwargs):
        self.captured[self.name] = payload
        raise _StopAtInvoke


def _wrapper_inputs(monkeypatch, game_id: str) -> dict:
    """The day and pack subgraph inputs the parent's wrappers build for a freshly dealt game."""
    import Agents.graphs.parent as parent

    captured: dict = {}
    monkeypatch.setattr(parent, "day_graph_compiled", _CapturingSubgraph(captured, "day"))
    monkeypatch.setattr(parent, "pack_night_graph_compiled", _CapturingSubgraph(captured, "pack"))
    config = build_runnable_config(RunConfig(game_id=game_id))
    state = initialize_game({}, config)
    runtime = SimpleNamespace(context=None)
    for wrapper in (parent.day_phase, parent.pack_night_phase):
        with pytest.raises(_StopAtInvoke):
            wrapper(state, config, runtime)
    return captured


def test_the_subgraph_wrappers_and_payload_builders_carry_the_game_id(monkeypatch):
    captured = _wrapper_inputs(monkeypatch, "game-a")
    assert captured["day"]["game_id"] == "game-a"
    assert captured["pack"]["game_id"] == "game-a"

    pack = captured["pack"]
    assert _pack_payload(pack, pack["surviving_wolves"][0])["game_id"] == "game-a"


def test_two_games_never_share_a_day_one_opening_key(monkeypatch):
    """Found 2026-10-26: without the game id, 8 seat pairs among 12 games keyed alike, so a later
    game's opening at the same seat, role and lineup was served an earlier game's line."""
    keys_by_game = {}
    for number in range(12):
        day = _wrapper_inputs(monkeypatch, f"game-{number}")["day"]
        day.update(start_opening(day))
        sends = fan_out_round(day, build_runnable_config(RunConfig(game_id=f"game-{number}")))
        keys_by_game[number] = {turn_cache_key(send.arg) for send in sends}

    games = sorted(keys_by_game)
    for first in games:
        for second in games[first + 1:]:
            assert not keys_by_game[first] & keys_by_game[second]
