"""The served game's engine config: the memory switch reaches every role, the store the
deployment names is the one seeded, and a served game never writes the store back."""
from __future__ import annotations

from Agents.schemas.roles import roles
from server.game.lobby import GameLobby
from server.game.run_config import game_run_config


def test_the_switch_sets_every_role_at_once():
    on = game_run_config(memory=True, human_player=0)
    off = game_run_config(memory=False, human_player=1, human_role="wolf")
    assert on.memory_config == {role: True for role in roles}
    assert off.memory_config == {role: False for role in roles}
    assert off.human_player == 1 and off.human_role == "wolf"


def test_a_served_game_retrieves_strategy_points_only():
    # The town half of the store has no observations; both factions get the same kind of memory.
    for memory in (True, False):
        run = game_run_config(memory=memory, human_player=0)
        assert run.retrieval_types_config == {"observations": False, "strategy_points": True}


def test_a_served_game_never_dumps_and_seeds_from_the_named_store(monkeypatch):
    from server.config import server_settings

    on = game_run_config(memory=True, human_player=0).memory_persistence
    assert on.dump_enabled is False
    # Memory-on games extract what they taught for the replay, still without writing.
    assert on.extraction.extract_without_dump is True
    assert game_run_config(memory=False, human_player=0).memory_persistence.extraction.extract_without_dump is False

    monkeypatch.setattr(server_settings, "WW_MEMORY_STORE_DIR", "memory_stores/demo_gen1")
    run = game_run_config(memory=True, human_player=0)
    assert str(run.memory_persistence.seed_store_dir) == "memory_stores/demo_gen1"
    assert run.memory_persistence.dump_enabled is False


def test_a_room_carries_the_hosts_choice_into_its_config():
    room = GameLobby(memory=True)
    run = room.run_config()
    assert run.game_id == room.game_id  # the room link survives the swap
    assert all(run.memory_config.values())
    assert not any(GameLobby().run_config().memory_config.values())
