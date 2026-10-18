"""Which events today's discussion has raised (catalogue "Rendering", fold rule 5).

A working step (a public event's own line: a visit, a will's night, an absence) is shown on its own
only when it is raised in today's discussion. "Raised" is mechanical, so the same transcript always
raises the same events, whoever reads it:
- (b) a message today names both the player and the night: "player_7" and "night 1" (or "night
  one"; "last night" is the night before today);
- (a) a message today carries a structured claim on that night and player: a claimed night action
  (the speaker's own field, DayChannel.claimed_night_actions) raises its target and every player its
  sighting names, on its night. A night not said, or one that had not happened by today, raises
  nothing (the claim ledger reads it as not said).
The day summariser's accusations are not a source: they keep withdrawn accusations, and they are
written only after the discussion.
"""

from __future__ import annotations

import re
from typing import Iterable

from Agents.schemas.game_events import DayChannel

GAME_MASTER = "game_master"
"""The narrator's lines (the morning, the vote) name players and nights on every day; they raise
nothing."""

PLAYER = re.compile(r"\bplayer_(\d+)\b", re.IGNORECASE)
NIGHT_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
               "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
NIGHT = re.compile(r"\bnight[\s-]*(\d+|" + "|".join(NIGHT_WORDS) + r")\b", re.IGNORECASE)
LAST_NIGHT = re.compile(r"\blast night\b", re.IGNORECASE)


def nights_named(text: str, current_day: int) -> set[int]:
    """The nights a message names. Night n is the night after day n, so on day d "last night" is
    night d - 1."""
    nights = set()
    for match in NIGHT.finditer(text):
        word = match.group(1).lower()
        nights.add(int(word) if word.isdigit() else NIGHT_WORDS[word])
    if LAST_NIGHT.search(text) and current_day > 1:
        nights.add(current_day - 1)
    return nights


def players_named(text: str) -> set[str]:
    return {f"player_{number}" for number in PLAYER.findall(text)}


def raised_today(day_channel: Iterable[DayChannel], current_day: int) -> frozenset[tuple[str, int]]:
    """Every (player, night) that a message spoken today names together. A stored game carries the
    transcript as plain dicts, a live game as models."""
    raised = set()
    for message in day_channel:
        if isinstance(message, dict):
            message = DayChannel.model_validate(message)
        if message.day != current_day or message.passed or message.player == GAME_MASTER:
            continue
        for night in nights_named(message.message, current_day):
            for player in players_named(message.message):
                raised.add((player, night))
        raised |= _claimed(message, current_day)
    return frozenset(raised)


def _claimed(message: DayChannel, current_day: int) -> set[tuple[str, int]]:
    """Source (a): the (player, night) pairs of the message's claimed night actions."""
    raised = set()
    for action in message.claimed_night_actions:
        if not 1 <= action.night < current_day:
            continue
        for player in [action.target, *action.seen]:
            if player:
                raised.add((player, action.night))
    return raised
