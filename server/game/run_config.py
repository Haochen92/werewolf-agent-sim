"""The one place a served game's engine config is built.

Three doors start a game — the solo door, a room's host, and recovery after a restart —
and they must agree on the same rules: the memory system follows the player's choice for
every role at once, lessons are read from the store the deployment names, and a game
played over the server is never mined into that store. Building the config here keeps a
game that is rebuilt after a restart identical to the one that was started.
"""

from __future__ import annotations

from Agents.config import RunConfig
from Agents.schemas.roles import roles
from server.config import server_settings


def game_run_config(*, memory: bool, human_player: int, human_role: str | None = None,
                    game_id: str | None = None) -> RunConfig:
    """Build the config a served game runs on.

    ``memory`` is the player's switch: on, every AI seat retrieves lessons from past
    games before each decision, and at the end the game's own lessons are extracted for
    the replay to show; off, neither happens. Either way those lessons are never written
    back into the live store."""
    persistence: dict = {"dump_enabled": False, "extraction": {"extract_without_dump": memory}}
    if server_settings.WW_MEMORY_STORE_DIR:
        persistence["seed_store_dir"] = server_settings.WW_MEMORY_STORE_DIR
    return RunConfig(
        game_id=game_id,
        human_player=human_player,
        human_role=human_role,
        memory_config={role: memory for role in roles},
        memory_persistence=persistence,
    )
