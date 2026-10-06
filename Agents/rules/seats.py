"""Seat order for a list of players: seat 1, seat 2, ... whichever bucket each came from.

The engine keeps the survivors in two buckets (the wolves, everyone else) and a turn's
``surviving_players`` list joins them. Joined as they were, the list named one faction before
the other, in every prompt and in the human seat's chips: a reader who noticed could tell the
wolves by their place in the line (seen 2026-10-06 in the vote chips: 3, 4, 5, 7, 9, then 2, 6).
"""

from __future__ import annotations

import re
from collections.abc import Iterable

_TRAILING_NUMBER = re.compile(r"(\d+)$")


def seat_number(player: str) -> int | None:
    """The number at the end of a player id ("player_7" -> 7), or None if it has none."""
    m = _TRAILING_NUMBER.search(player)
    return int(m.group(1)) if m else None


def seat_order(players: Iterable[str]) -> list[str]:
    """The players by seat number, then by name (ids with no number go last, by name)."""
    return sorted(players, key=lambda p: (seat_number(p) is None, seat_number(p) or 0, p))
