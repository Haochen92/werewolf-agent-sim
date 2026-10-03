"""The puppet cast: which plush character stands at each seat.

The characters are the theatre's puppets; the frontend holds their sprites, filed under
each one's id. They are dealt independently of roles, so a costume never says anything
about what a player is. A player in a room, or at the solo door, may pick their own
puppet. The house draws the rest at random when the engine deals the seats, and the cast
is then written down with the game, so a replay shows the same puppets the live game did.

A character's id is its slug (``polarBear``): the name its sprites are filed under, and
stable for the life of the record. The display name is what people read and may change
freely (``shade`` is the songbird). Adding a character means a row in ``CATALOGUE``, a
migration that seeds it into the ``characters`` table, and its sprites in the frontend.
Retiring one keeps its row, since old games still name it, and takes it out of the draw.
"""

from __future__ import annotations

import random
from typing import Mapping, NamedTuple, Sequence


class Character(NamedTuple):
    id: str
    display_name: str
    retired: bool = False


CATALOGUE: tuple[Character, ...] = (
    Character("owl", "Owl"),
    Character("hare", "Hare"),
    Character("cat", "Cat"),
    Character("badger", "Badger"),
    Character("cyclops", "Cyclops"),
    Character("threeEyes", "Three-Eyes"),
    Character("dragon", "Dragon"),
    Character("onion", "Onion"),
    Character("whale", "Whale"),
    Character("polarBear", "Polar Bear"),
    Character("shade", "Songbird"),
)

CHARACTER_IDS: frozenset[str] = frozenset(c.id for c in CATALOGUE)
"""Every id ever issued, retired ones included: what a stored cast may name."""

DRAW_POOL: tuple[str, ...] = tuple(c.id for c in CATALOGUE if not c.retired)
"""The ids a player may pick and the house may draw."""


def is_pickable(character_id: str) -> bool:
    return character_id in DRAW_POOL


class CastSeat(NamedTuple):
    """One seat's puppet: the engine seat (``player_3``), the character, and whether a
    player chose it (``chosen``) or the house drew it."""

    seat: str
    character: str
    chosen: bool


def draw_cast(seats: Sequence[str], picks: Mapping[str, str] = {},
              rng: random.Random | None = None) -> list[CastSeat]:
    """Deal a puppet to every seat: the picks as given, the rest drawn at random from
    the pool, no character twice. ``picks`` maps an engine seat to its chosen character;
    it is trusted to be valid and distinct, which the pick endpoints guarantee.
    Raises ValueError when the pool cannot cover the seats."""
    draw = rng or random
    remaining = [c for c in DRAW_POOL if c not in picks.values()]
    open_seats = [s for s in seats if s not in picks]
    if len(remaining) < len(open_seats):
        raise ValueError(f"{len(seats)} seats but only {len(DRAW_POOL)} characters")
    drawn = iter(draw.sample(remaining, len(open_seats)))
    return [CastSeat(seat, picks[seat], True) if seat in picks
            else CastSeat(seat, next(drawn), False) for seat in seats]


def seat_number(seat: str) -> int:
    """``player_7`` → 7, the order a cast is listed in."""
    return int(seat.rsplit("_", 1)[-1])
