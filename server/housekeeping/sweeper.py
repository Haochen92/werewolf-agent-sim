"""The timer job that gives up on games nobody ever came back to.

A game left waiting on a human question with nobody connected costs nothing while it
waits, but boot recovery would keep bringing it back forever. This is its shelf life:
once a solo game has waited an hour, or a game with several humans a whole day, the
sweeper marks it ``dropped`` and stores the reason, which is what someone opening the
game later sees. Running the sweep again is harmless, and it never touches a game
somebody is watching, one that is actually playing, or one that has already ended.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from server.config import ServerSettings, server_settings
from server.game.registry import GameRegistry
from server.game.runtime import GameSession

logger = logging.getLogger(__name__)


def _shelf_life(session: GameSession, settings: ServerSettings) -> timedelta:
    multi = len(session._seat_tokens) > 1
    seconds = settings.MULTI_PARK_TTL_SECONDS if multi else settings.SOLO_PARK_TTL_SECONDS
    return timedelta(seconds=seconds)


def is_expired(session: GameSession, settings: ServerSettings,
               now: datetime | None = None) -> bool:
    """True when the game is waiting on a human, nobody is connected to watch it, and it
    has been in that state longer than its shelf life. The cheapest checks come first."""
    if session.error is not None or session.game_over or session._finished.is_set():
        return False
    if not session.pending_requests or session.parked_since is None:
        return False
    if session.humans_present():
        return False
    now = now or datetime.now(timezone.utc)
    return now - session.parked_since >= _shelf_life(session, settings)


async def sweep_parked_games(registry: GameRegistry,
                             settings: ServerSettings = server_settings,
                             now: datetime | None = None) -> list[str]:
    """One pass over every running game. Returns the ids of the games it dropped."""
    dropped: list[str] = []
    for session in registry.sessions():
        if not is_expired(session, settings, now):
            continue
        idle = datetime.now(timezone.utc) - session.parked_since  # type: ignore[operator]
        reason = (f"abandoned: parked on a human turn with nobody connected for "
                  f"{int(idle.total_seconds() // 60)} min")
        try:
            await registry.drop(session.game_id, reason)
        except Exception:  # one bad game must not stop the rest of the sweep
            logger.exception("sweep: game %s could not be dropped", session.game_id)
            continue
        logger.info("sweep: game %s dropped (%s)", session.game_id, reason)
        dropped.append(session.game_id)
    return dropped


async def run_sweeper(registry: GameRegistry,
                      settings: ServerSettings = server_settings) -> None:
    """The background loop the app starts at boot and cancels at shutdown."""
    while True:
        await asyncio.sleep(settings.SWEEP_INTERVAL_SECONDS)
        try:
            await sweep_parked_games(registry, settings)
        except Exception:
            logger.exception("sweep: pass failed")
