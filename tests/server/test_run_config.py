"""The served game's engine config: the memory switch reaches every role, nothing is seeded
into the process (the graph is compiled over the database's store), and a served game never
writes the store back."""
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


def test_a_served_game_never_dumps_and_never_seeds_a_file_store():
    for memory in (True, False):
        persistence = game_run_config(memory=memory, human_player=0).memory_persistence
        assert persistence.dump_enabled is False
        assert persistence.seed_enabled is False
        # The store's name on the game's retrieval metadata: the runtime's database store.
        assert str(persistence.seed_store_dir) == "postgres"


def test_a_room_carries_the_hosts_choice_into_its_config():
    room = GameLobby(memory=True)
    run = room.run_config()
    assert run.game_id == room.game_id  # the room link survives the swap
    assert all(run.memory_config.values())
    assert not any(GameLobby().run_config().memory_config.values())
