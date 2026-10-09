"""Composes the rules block every prompt opens with, from the dealt cast.

A role the game does not have must never appear in the rules: an agent reads a rule about a role
and starts claiming things about it. So the block is built at game start from the cast: the
template in ``game_rules.py`` is the text, and the three functions below fill its slots from the
role cards in ``roles/`` and the sides table. The composed text for a cast is pinned as a golden
under ``goldens/``, so what is reviewed is the English the model reads.
"""

from __future__ import annotations

import textwrap
from collections import Counter

from Agents.prompts.game_rules import RULES_TEMPLATE, SIDES
from Agents.prompts.roles import card
from Agents.schemas.role_card import RoleCard

_WIDTH = 104
"""Line width of the rendered block; bullets wrap with a four-space hanging indent."""

_NUMBER_WORDS = {0: "no", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}


def _card(name: str) -> RoleCard:
    """The card of a role."""
    return card(name)


def _has_card(name: str) -> bool:
    """Whether a role has a card: the retired roles of the nine-seat game (in old records) do not,
    and are left out of the block rather than composed."""
    try:
        card(name)
    except ModuleNotFoundError:
        return False
    return True


def _bullet(text: str) -> str:
    """One "- " bullet, wrapped to the block's width with a hanging indent."""
    return textwrap.fill(text.strip(), width=_WIDTH, initial_indent="- ", subsequent_indent="    ")


def _dealt(cast: list[str]) -> tuple[list[str], list[str]]:
    """The roles in cast order, each once, and the sides they fall on, in lineup order."""
    roles: list[str] = []
    for role in cast:
        if role not in roles and _has_card(role):
            roles.append(role)
    sides: list[str] = []
    for side in SIDES:
        for role in roles:
            if _card(role).side == side and side not in sides:
                sides.append(side)
    return roles, sides


def _lineup(cast: list[str]) -> str:
    """The "Team composition" header and one line per role, grouped by side."""
    counts = Counter(cast)
    roles, sides = _dealt(cast)
    lines = [f"Team composition ({len(cast)} players, {_NUMBER_WORDS[len(sides)]} sides):"]
    for side in sides:
        lines.append(SIDES[side]["heading"])
        for role in roles:
            card = _card(role)
            if card.side == side:
                lines.append(_bullet(f"{counts[role]} {card.name}: {card.lineup.strip()}"))
    return "\n".join(lines)


def _roles(cast: list[str]) -> str:
    """One paragraph per dealt side (a team's shared rules) and role, in lineup order."""
    roles, sides = _dealt(cast)
    lines: list[str] = []
    for side in sides:
        if "rules" in SIDES[side]:
            lines.append(_bullet(f"The {side}: {SIDES[side]['rules']}"))
        for role in roles:
            card = _card(role)
            if card.side == side:
                lines.append(_bullet(f"{card.name}: {card.rules.strip()}"))
    return "\n".join(lines)


def _wins(cast: list[str]) -> str:
    """One line per team, from the sides table, and per seat of one, from its card."""
    roles, sides = _dealt(cast)
    lines: list[str] = []
    for side in sides:
        if "win" in SIDES[side]:
            lines.append(_bullet(SIDES[side]["win"]))
        for role in roles:
            card = _card(role)
            if card.side == side and card.win:
                lines.append(_bullet(card.win))
    return "\n".join(lines)


def rules_block(cast: list[str]) -> str:
    """The rules block for one cast."""
    return RULES_TEMPLATE.format(lineup=_lineup(cast), roles=_roles(cast), wins=_wins(cast))


def preamble(cast: list[str]) -> str:
    """The rules block with the second-person opening every play prompt starts with."""
    return (
        f"You are playing a game of Werewolf with {len(cast)} players. The role line-up below is\n"
        "public knowledge — everyone knows these roles are in the game, but not who holds them.\n\n"
        + rules_block(cast)
        + "\n"
    )
