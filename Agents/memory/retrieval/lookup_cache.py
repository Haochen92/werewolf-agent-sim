"""A seat's memory lookup, reused within a day or a night (v8 plan D4; owner's ruling 2026-10-12).

A lookup (the situation call and the search) ran on every decision: about 60 in the owner's first
ten-seat game, 27 of them discussion turns. Now a seat's day discussion reuses its first lookup of the
day until someone makes a new role claim that day, and every night decision of a seat (the pack's chat
rounds, its kill, its ability) reuses the night's first lookup; a vote always looks up afresh. After
review the same day, a wolf's night is two lookups: one for the pack's chat, one for its kill and its
ability, since the talk moves from candidate targets to a plan the first lookup could not anticipate.

What is kept is the lessons the lookup selected and its record, never the payload or a verdict: each
decision still records its own verdicts. The cache lives in the process, so a server restart only
means a fresh lookup. A payload with no game id (a bare test, a bench replay) is never cached.
"""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Any

REUSED_PHASES = frozenset({"day_discussion", "night_action"})
_MAX_ENTRIES = 1024  # a few games' worth on a long-running server; the oldest go first

_cache: OrderedDict[tuple, dict[str, Any]] = OrderedDict()
_lock = threading.Lock()


def claims_today(payload: dict[str, Any]) -> frozenset[tuple[str, str]]:
    """The (player, role) claims made in today's discussion. A claimant repeating its claim adds
    nothing, so only a new claim refreshes a seat's lookup."""
    day = payload["current_day"]
    claims = set()
    for entry in payload.get("day_channel") or []:
        get = entry.get if isinstance(entry, dict) else lambda k, e=entry: getattr(e, k, None)
        if get("day") == day and (get("claim") or "none") != "none":
            claims.add((get("player"), get("claim")))
    return frozenset(claims)


def lookup_key(game_id: str, payload: dict[str, Any], action_phase: str, store_dir: str,
               scope: str = "") -> tuple | None:
    """The key a lookup is kept under, or None when this decision always looks up afresh. ``scope``
    splits a night: the pack's chat ("chat") and its kill and ability ("act") each keep their own."""
    if action_phase not in REUSED_PHASES or not game_id:
        return None
    return (game_id, payload["player_id"], payload["current_day"], action_phase, store_dir, scope)


def get(key: tuple, payload: dict[str, Any]) -> dict[str, Any] | None:
    """The kept lookup for this decision, or None if there is none or a new claim has outdated it."""
    with _lock:
        entry = _cache.get(key)
    if entry is None or not claims_today(payload) <= entry["claims"]:
        return None
    return entry


def put(key: tuple, payload: dict[str, Any], lookup: dict[str, Any]) -> None:
    with _lock:
        _cache[key] = {**lookup, "claims": claims_today(payload)}
        _cache.move_to_end(key)
        while len(_cache) > _MAX_ENTRIES:
            _cache.popitem(last=False)


def clear() -> None:
    with _lock:
        _cache.clear()
