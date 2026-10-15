"""The timer job that gives up on games nobody ever came back to.

A game left waiting on a human question, waiting for its owner's API key after a
restart, or suspended because its solo player went away, with no human seat connected
costs nothing while it waits, but boot recovery would keep bringing it back forever.
This is its shelf life: once a solo game has waited an hour, or a game with several
humans a whole day, the sweeper marks it ``dropped`` and stores the reason, which is
what someone opening the game later sees. Running the sweep again is harmless, and it
never touches a game with a human seat connected (a spectator does not count), one that
is actually playing, or one that has already ended.

Waiting rooms have a shelf life too: a room nobody departed within ROOM_LIST_TTL_SECONDS
is closed on the same pass (``LiveGameRegistry.expire_rooms``).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from server.config import ServerSettings, server_settings
from server.game.live_game_registry import LiveGameRegistry
from server.game.game_session import GameSession

logger = logging.getLogger(__name__)


def _shelf_life(session: GameSession, settings: ServerSettings) -> timedelta:
    """An hour for a solo table, a day for one with several humans, so a group is not
    lost to one person's evening away. Both knobs are server settings."""
    multi = len(session._seat_tokens) > 1
    seconds = settings.MULTI_PARK_TTL_SECONDS if multi else settings.SOLO_PARK_TTL_SECONDS
    return timedelta(seconds=seconds)


def _waiting_since(session: GameSession) -> tuple[datetime, str] | None:
    """When the game began waiting for a human, and what to call that wait in the reason;
    None when it is not waiting. Parked on a question or on a key comes first; otherwise
    a solo game suspended because its player is away."""
    if session.parked_since is not None and (session.pending_requests or session.awaiting_key):
        return session.parked_since, "parked on a human turn with nobody connected"
    if session.suspended_since is not None:
        return session.suspended_since, "suspended with its player away"
    return None


def is_expired(session: GameSession, settings: ServerSettings,
               now: datetime | None = None) -> bool:
    """True when the game is waiting on a human (parked on a question or a key, or
    suspended with its solo player away), nobody is connected to watch it, and it has
    been in that state longer than its shelf life. The cheapest checks come first."""
    if session.error is not None or session.game_over or session.ended:
        return False
    waiting = _waiting_since(session)
    if waiting is None:
        return False
    if session.humans_present:
        return False
    now = now or datetime.now(timezone.utc)
    return now - waiting[0] >= _shelf_life(session, settings)


async def sweep_parked_games(registry: LiveGameRegistry,
                             settings: ServerSettings = server_settings,
                             now: datetime | None = None) -> list[str]:
    """One pass over every running game. Returns the ids of the games it dropped."""
    dropped: list[str] = []
    for session in registry.sessions:
        if not is_expired(session, settings, now):
            continue
        since, waiting = _waiting_since(session)  # type: ignore[misc]
        idle = datetime.now(timezone.utc) - since
        reason = f"abandoned: {waiting} for {int(idle.total_seconds() // 60)} min"
        try:
            await registry.drop(session.game_id, reason)
        except Exception:  # one bad game must not stop the rest of the sweep
            logger.exception("sweep: game %s could not be dropped", session.game_id)
            continue
        logger.info("sweep: game %s dropped (%s)", session.game_id, reason)
        dropped.append(session.game_id)
    return dropped


async def run_sweeper(registry: LiveGameRegistry,
                      settings: ServerSettings = server_settings) -> None:
    """The background loop the app starts at boot and cancels at shutdown. Each pass also
    closes the waiting rooms nobody departed within their shelf life."""
    while True:
        await asyncio.sleep(settings.SWEEP_INTERVAL_SECONDS)
        try:
            await sweep_parked_games(registry, settings)
            registry.expire_rooms(settings.ROOM_LIST_TTL_SECONDS)
        except Exception:
            logger.exception("sweep: pass failed")
