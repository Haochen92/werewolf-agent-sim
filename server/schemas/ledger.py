"""The claim ledger's wire shape: what the agents read each morning about the claims made in
earlier day discussions, with the game master's checks (server/game/ledger.py builds it)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class LedgerCheck(BaseModel, frozen=True):
    text: str
    """The check as the agents read it, starting "Record:" or "Rules:"."""
    fits: bool | None
    """True: the record agrees with the claim; False: it disagrees, or the claim breaks a rule;
    None: a fact beside the claim that is neither."""


class LedgerRole(BaseModel, frozen=True):
    day: int
    role: str
    kind: Literal["claimed", "retracted"]


class LedgerEntryView(BaseModel, frozen=True):
    """One claimed night action, or a plan the player never said they carried out."""

    night: int
    """The night it is about; 0 when the player did not say."""
    action: str
    """investigate / protect / shoot / kill; "" for an older game's free-text result."""
    target: str
    result: str
    """The result word the player gave (e.g. wolf, not_a_wolf, saved_from_attack, not_said);
    "" for an unreported plan."""
    said_on_day: int
    reported: bool
    """False for a plan the player never said they carried out."""
    earlier: list[str]
    """What the player said about the same night before changing it, oldest first, as text."""
    also: list[str]
    """Other targets the player named for the same action and night on the same day, as text."""
    planned: str | None
    """The target the player said, on that night's day, they would act on; None if no plan."""
    reason: str
    """The player's reason for doing something other than what they planned, if given."""
    text: str
    """The whole line as the agents read it, without its checks."""
    checks: list[LedgerCheck]


class LedgerPlayerView(BaseModel, frozen=True):
    player: str
    history: str
    """The role history as the agents read it, e.g. "claimed investigator (day 2)"."""
    roles: list[LedgerRole]
    checks: list[LedgerCheck]
    entries: list[LedgerEntryView]


class LedgerDay(BaseModel, frozen=True):
    day: int
    """The morning this ledger was read on."""
    players: list[LedgerPlayerView]
