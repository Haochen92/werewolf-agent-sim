"""The turn-cache key must be VALUE-stable across a checkpoint round-trip.

The cache's only job is to catch the re-executed superstep after a human resume — and
those re-run payloads are checkpoint-round-tripped stored Sends. LangGraph's default
pickle key differs there (pydantic __pydantic_fields_set__ changes), missing exactly
when it matters; turn_cache_key hashes canonical JSON values instead.
"""

from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

from Agents.config.langgraph import turn_cache_key
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
