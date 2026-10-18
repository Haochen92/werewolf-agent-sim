"""Catalogue C18, the game-continuation half: the game checks for a winner after every day and every
night, and a seat taking a turn knows it continued past every check so far. A role assignment that
would have ended the game at one of those checks is ruled out.

The living players' sides at a check are the dealt cast minus the sides of everyone dead by then, so
only the hidden bodies' roles are unknown in it: the rule narrows the hidden bodies (there are two at
most, catalogue L8) by trying every way of giving them their candidate roles. The day limit only
ever ends a game, so it never makes a continued game say more than this.
"""

from __future__ import annotations

from itertools import product

from Agents.schemas.game_events import DeathRecord
from Agents.schemas.roles import LONE_KILLER, NEUTRAL, TOWN, WOLVES, side_of

MOST_BODIES_TRIED = 4
"""Past this many hidden bodies (never in a legal game) the rule is skipped: it only narrows."""


def game_continues(side_counts: dict[str, int]) -> bool:
    """Whether a check with these living side counts lets the game go on: no winner and no draw
    (Agents/nodes/orchestrator.py `determine_winner`, `is_draw`)."""
    wolves, town = side_counts.get(WOLVES, 0), side_counts.get(TOWN, 0)
    killer, neutral = side_counts.get(LONE_KILLER, 0), side_counts.get(NEUTRAL, 0)
    if wolves == 0 and killer == 0:
        return False  # the town wins, or no side is left: a draw
    if killer == 1 and town + wolves + neutral <= 1:
        return False
    if killer == 0 and wolves > 0 and wolves >= town + neutral:
        return False
    return True


def _check_order(death: DeathRecord) -> tuple[int, int]:
    """Day n's lynch is checked before night n's deaths."""
    return death.day, 0 if death.phase == "day" else 1


def dead_at_each_check(dead_roster: list[DeathRecord]) -> list[list[DeathRecord]]:
    """Everyone dead at each check that changed who is alive, in game order."""
    checks = sorted({_check_order(death) for death in dead_roster})
    return [[death for death in dead_roster if _check_order(death) <= check] for check in checks]


def body_roles_that_continue(bodies: list[str], candidates: dict[str, frozenset[str]],
                             dead_roster: list[DeathRecord], copies: dict[str, int],
                             others_fixed: dict[str, int]) -> dict[str, set[str]] | None:
    """Each hidden body's candidate roles that some way of placing roles on all the bodies keeps
    the game going at every check; None to leave them as they are (too many bodies).
    `others_fixed`: copies of each role already certain on players who are not hidden bodies."""
    if len(bodies) > MOST_BODIES_TRIED:
        return None
    if any(not death.concealed and death.role not in copies for death in dead_roster):
        return None  # a death whose role the cast does not list: no side to count
    dealt_sides: dict[str, int] = {}
    for role, count in copies.items():
        dealt_sides[side_of(role)] = dealt_sides.get(side_of(role), 0) + count
    checks = dead_at_each_check(dead_roster)

    kept: dict[str, set[str]] = {body: set() for body in bodies}
    for placed in product(*(sorted(candidates[body]) for body in bodies)):
        if not _within_copies(placed, copies, others_fixed):
            continue
        body_role = dict(zip(bodies, placed))
        if all(game_continues(_living_sides(dead, body_role, dealt_sides)) for dead in checks):
            for body, role in body_role.items():
                kept[body].add(role)
    return kept


def _within_copies(placed: tuple[str, ...], copies: dict[str, int], others_fixed: dict[str, int]) -> bool:
    for role in set(placed):
        if placed.count(role) + others_fixed.get(role, 0) > copies.get(role, 0):
            return False
    return True


def _living_sides(dead: list[DeathRecord], body_role: dict[str, str], dealt_sides: dict[str, int]) -> dict[str, int]:
    living = dict(dealt_sides)
    for death in dead:
        role = body_role.get(death.player) if death.concealed else death.role
        living[side_of(role)] -= 1
    return living
