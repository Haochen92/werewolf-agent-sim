"""Who gets a last word before the vote, and the moderator's line that calls them.

When the discussion would end, the one or two players accused by the most different players
today get one closing turn (discussion_evidence.md §7.2 S2). The accused are picked from the
accusation tags each speaker puts on its own message, and only from them: the agents' private
suspicion reads would leak what they secretly think, and a model-written case summary in the
moderator's voice would turn any mistake into a "fact". Counting the tags costs nothing and
cannot misstate anything; it can miss an accuser the tags missed, which the census (§7.1) puts at
about one message in eight.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from Agents.schemas.game_events import DayChannel

# A player is "on trial" with this many different accusers, and at most this many players
# get a closing turn.
MIN_ACCUSERS = 2
MAX_ACCUSED = 2


@dataclass(frozen=True)
class Accused:
    player: str
    accusers: tuple[str, ...]
    """The different players who accused them today, in the order they first did."""
    latest_seq: int
    """The transcript position of the latest accusation against them (the tie-breaker)."""


def closing_speakers(
    day_channel: Iterable[DayChannel], current_day: int, surviving_players: Iterable[str]
) -> list[Accused]:
    """The players who get a last word today, most accused first.

    Over today's spoken, non-moderator entries, every accusation tag against a living player
    other than the speaker counts its speaker as one accuser (a player accusing twice counts
    once). A pass counts nothing, a held line included: the table never heard it, and naming its
    author as an accuser announced accusations nobody had seen (owner, 2026-10-07, after the step 8
    games: four of six named accusers in one closing had been held). Players with at least
    MIN_ACCUSERS accusers qualify; the most accusers first, then the more recently accused, then
    the player id so the order is fixed; at most MAX_ACCUSED.
    Empty when nobody qualifies, and the day goes straight to its summary.
    """
    alive = set(surviving_players)
    # The tally: accused player -> the different players who accused them, in the order they
    # first did. Scratch state for this loop only; the result is the Accused list below.
    accusers_of: dict[str, list[str]] = {}
    # accused player -> transcript position of the latest accusation against them.
    latest_seq: dict[str, int] = {}

    for entry in day_channel:
        if entry.day != current_day or entry.player == "game_master":
            continue
        # A pass has no accusation the table heard, a held line included.
        if entry.passed:
            continue
        for tag in entry.addressed_targets:
            if tag.stance != "accusation":
                continue
            accused = tag.target
            if accused == entry.player or accused not in alive:
                continue
            accusers = accusers_of.setdefault(accused, [])
            if entry.player not in accusers:
                accusers.append(entry.player)
            latest_seq[accused] = entry.seq

    on_trial: list[Accused] = []
    for accused, accusers in accusers_of.items():
        if len(accusers) >= MIN_ACCUSERS:
            on_trial.append(Accused(accused, tuple(accusers), latest_seq[accused]))
    # Most accusers first; among equals the more recently accused; then the id, so ties are fixed.
    on_trial.sort(key=lambda a: (-len(a.accusers), -a.latest_seq, a.player))
    return on_trial[:MAX_ACCUSED]


def closing_announcement(accused: list[Accused]) -> str:
    """The moderator's call, written by code: who is on trial and who is pressing, e.g.
    "Before the vote: player_5 has been accused by player_2, player_4 and player_7; player_8 by
    player_1 and player_3. Each gets a last word." The reasons are already in the transcript."""
    if not accused:
        raise ValueError("no closing announcement without an accused player")

    clauses: list[str] = []
    for position, trial in enumerate(accused):
        who_accused = _names(trial.accusers)
        if position == 0:
            clauses.append(f"{trial.player} has been accused by {who_accused}")
        else:
            clauses.append(f"{trial.player} by {who_accused}")
    charges = "; ".join(clauses)

    if len(accused) == 1:
        last_word = f"{accused[0].player} gets a last word."
    else:
        last_word = "Each gets a last word."

    return f"Before the vote: {charges}. {last_word}"


def _names(players: tuple[str, ...]) -> str:
    """Player ids as a spoken list: "player_2", "player_2 and player_4",
    "player_2, player_4 and player_7"."""
    if len(players) == 1:
        return players[0]
    all_but_last = ", ".join(players[:-1])
    last = players[-1]
    return f"{all_but_last} and {last}"
