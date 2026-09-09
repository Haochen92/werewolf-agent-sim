"""Retention for parked games (seat_continuity.md §7).

A game parked on a human question with nobody connected costs nothing while it waits,
but boot recovery would revive it forever. This sweeper is the shelf life: past the
window it marks the game ``dropped`` — the existing terminal status, reused — with the
reason as the epitaph viewers see. Idempotent, and never touches a game a human is
watching, a game that is running, or one that already ended.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from server.config import ServerSettings, server_settings
from server.database_models.game import DROPPED
from server.game_repository import GameRepository
from server.runtime import GameSession

logger = logging.getLogger(__name__)


def _shelf_life(session: GameSession, settings: ServerSettings) -> timedelta:
    multi = len(session._seat_tokens) > 1
    seconds = settings.MULTI_PARK_TTL_SECONDS if multi else settings.SOLO_PARK_TTL_SECONDS
    return timedelta(seconds=seconds)


def is_expired(session: GameSession, settings: ServerSettings,
               now: datetime | None = None) -> bool:
    """Parked, unwatched, and past its shelf life — the three conditions, in order of
    how cheaply each rules a game out."""
    if session.error is not None or session.game_over or session._finished.is_set():
        return False
    if not session.pending_requests or session.parked_since is None:
        return False
    if session.humans_present():
        return False
    now = now or datetime.now(timezone.utc)
    return now - session.parked_since >= _shelf_life(session, settings)


async def sweep_parked_games(games: dict, repository: GameRepository | None,
                             settings: ServerSettings = server_settings,
                             now: datetime | None = None) -> list[str]:
    """One pass over the registry. Returns the game ids dropped."""
    dropped: list[str] = []
    for game_id, entry in list(games.items()):
        if not isinstance(entry, GameSession) or not is_expired(entry, settings, now):
            continue
        idle = datetime.now(timezone.utc) - entry.parked_since  # type: ignore[operator]
        reason = (f"abandoned: parked on a human turn with nobody connected for "
                  f"{int(idle.total_seconds() // 60)} min")
        try:
            await entry.abandon(reason)
            if repository is not None:
                await repository.upsert_game(game_id, status=DROPPED, error=reason)
        except Exception:  # one bad row must not stop the sweep
            logger.exception("sweep: game %s could not be dropped", game_id)
            continue
        logger.info("sweep: game %s dropped (%s)", game_id, reason)
        dropped.append(game_id)
    return dropped


async def run_sweeper(games: dict, repository: GameRepository | None,
                      settings: ServerSettings = server_settings) -> None:
    """The lifespan's background loop; cancelled at shutdown."""
    while True:
        await asyncio.sleep(settings.SWEEP_INTERVAL_SECONDS)
        try:
            await sweep_parked_games(games, repository, settings)
        except Exception:
            logger.exception("sweep: pass failed")
