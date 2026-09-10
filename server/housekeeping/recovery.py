"""Boot recovery: rebuild the registry from persisted facts after a restart.

The counterpart of "persistence writes facts down": at boot, every waiting/running row
is handed to ``GameRegistry.revive``, which re-creates the living entry from the row,
the event log and the checkpoint. Per-row failure policy: recovery of one game must
never take the server down or block the others — a row that fails to revive is marked
dropped with the reason and skipped.
"""

from __future__ import annotations

import logging

from server.database_models.game import DROPPED
from server.game.registry import GameRegistry
from server.storage.game_repository import GameRepository

logger = logging.getLogger(__name__)


async def recover_registry(registry: GameRegistry, repository: GameRepository) -> None:
    """Fill the fresh registry from every waiting/running row. Called by the lifespan
    after the graph runtime starts; a no-op when Postgres is unconfigured."""
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
