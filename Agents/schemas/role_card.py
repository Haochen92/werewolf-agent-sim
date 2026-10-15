"""A role's words, one card per role in ``Agents/prompts/roles/<role>.py``: the public half (lineup,
rules, win) goes into the rules block everyone reads; the private half (playstyle, and the three
turn blocks) only into the holder's own prompts. A turn block holds the role-specific words of one
turn's template; the scaffold around them (preamble, tone, transcript, memory context, the JSON
boilerplate) lives in the turn's module under ``Agents/prompts/``."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DiscussWords:
    """The role's words in its day-discussion template."""

    framing: str
    """The identity line and how this role speaks."""
    context: str
    """The info lines: the surviving players, then the private ones (past results, uses left, the
    pack's record)."""
    trailer: str = ""
    """A reminder after the transcript (the wolves' cover note); "" for none."""


@dataclass(frozen=True)
class VoteWords:
    """The role's words in its day-vote template."""

    framing: str
    """The identity line and how this role votes."""
    context: str
    """The info lines: the surviving players, then the private ones."""
    closing: str
    """The last line: what the vote is for."""
    guidance: str = ""
    """Voting rules in the system block in place of the shared ones (the wolves, a lone killer);
    "" takes the shared block."""


@dataclass(frozen=True)
class NightWords:
    """The role's words in its night template."""

    ability: str
    """The identity line, the choice the turn asks for with the no-action word if any, and how
    this role chooses."""
    context: str
    """The info lines: the players the action can target, uses left, past results."""
    closing: str
    """The last line: the choice to make."""
    target_field: str
    """The JSON field the choice goes in: "investigator_target"."""
    no_action: str = ""
    """The word that declines the action ("hold_fire", "keep_sigil"); "" when the role must act."""
    lot: bool = False
    """Whether night 1 offers the default drawn by lot (prompt_inputs.night_one_lot)."""


@dataclass(frozen=True)
class RoleCard:
    """What a role card says; one per role in ``Agents/prompts/roles/<role>.py`` as ``CARD``."""

    side: str
    """The role's side: town, wolves, lone_killer or neutral."""
    name: str
    """The name as printed: "Sigilist"."""
    lineup: str
    """The one-line ability, after the count in the lineup."""
    rules: str
    """The paragraph with everything about the role."""
    playstyle: str = ""
    """PRIVATE to the holder, read on every turn: who it is and what winning means, in the second
    person. The turn-by-turn considerations are on the turn blocks below."""
    win: str | None = None
    """The win condition, for a seat of one (a team's is in SIDES)."""
    day_discuss: DiscussWords | None = None
    """PRIVATE: the role's words in the day-discussion template."""
    day_vote: VoteWords | None = None
    """PRIVATE: the role's words in the day-vote template."""
    night: NightWords | None = None
    """PRIVATE: the role's words in the night template; None for a role that does not act at night."""
