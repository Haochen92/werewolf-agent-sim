"""Filling the registry back up at boot from what the database remembers.

A restart empties the process, but every game is still written down. At startup each row
still marked waiting or running is handed to ``LiveGameRegistry.revive``, which rebuilds the
game from that row, the stored events and the engine checkpoint. One broken game must
never take the server down or hold up the others, so a row that cannot be rebuilt is
marked dropped, with the reason, and skipped.
"""

from __future__ import annotations

import logging

from server.database_models.game import DROPPED
from server.game.live_game_registry import LiveGameRegistry
from server.storage.game_repository import GameRepository

logger = logging.getLogger(__name__)


async def recover_registry(registry: LiveGameRegistry, repository: GameRepository) -> None:
    """Fill a fresh registry from every waiting or running row. Called at startup once
    the graph runtime is up, and does nothing when Postgres is not configured."""
    if not registry.durable:
        return
    rows = await repository.load_recoverable_games()
    revived = 0
    for row in rows:
        try:
            if await registry.revive(row) is not None:
                revived += 1
        except Exception:
            logger.exception("game %s: recovery failed; marking dropped", row.game_id)
            await repository.upsert_game(
                row.game_id, status=DROPPED, error="recovery failed on restart")
    if rows:
        logger.info("recovery: %d open row(s) processed, %d revived", len(rows), revived)
