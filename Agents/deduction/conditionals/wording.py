"""Every sentence of the conditionals (slice 10: catalogue Table F, F4 to F6), in one place, so the same
premise and the same conclusion are always worded the same way. The rules are the catalogue's (§0,
grade 2; "Rendering", fold rule 3): the premise opens the line and names the claims it assumes (never
"if X is lying"); the contrapositive keeps the same premise; no line is worded as advice. Players are
listed in seat order (hidden bodies in death order), and a list of roles is always the full list.
"""

from __future__ import annotations

from Agents.deduction.wording import ROLE_TITLES
from Agents.schemas.deduction import Premise

DONE = {"investigate": "checked", "protect": "protected", "shoot": "shot at", "kill": "attacked",
        "sigil": "set a sigil on", "block": "blocked", "visit": "gone to", "watch": "watched", "follow": "followed"}
"""What a claim says was done to its target, after "to have"."""
NAMED_BY_NOUN = {"watch": "watch", "follow": "follow", "investigate": "check"}
"""Claimed actions a line names by their noun ("player_2's watch"); the others by what they say."""


def _joined(names: list[str], last: str) -> str:
    """"a, b and c" or "a, b or c"."""
    if len(names) == 1:
        return names[0]
    return f"{', '.join(names[:-1])} {last} {names[-1]}"


class Wording:
    """How one premise is named: in the opening ("If player_2's watch is true"), and when false."""

    def __init__(self, premise: Premise, same_kind_nights: int = 1):
        claim = premise.claim
        self.plural = premise.kind == "role_claims" and not premise.unchecked_only
        if premise.kind == "role_claims":
            self.noun = ("every role claim you cannot check" if premise.unchecked_only
                         else "the current role claims")
            self.one_false = ("one of the role claims you cannot check" if premise.unchecked_only
                              else "one of the current role claims")
        elif premise.kind == "role_claim" or claim is None:
            self.noun = self.one_false = f"{premise.claimant}'s claim"
        elif claim.blocked:
            self.noun = self.one_false = f"{claim.claimant}'s claim to have been roleblocked on night {claim.night}"
        elif claim.action in NAMED_BY_NOUN:
            when = f" on night {claim.night}" if same_kind_nights > 1 else ""
            self.noun = self.one_false = f"{claim.claimant}'s {NAMED_BY_NOUN[claim.action]}{when}"
        else:
            self.noun = self.one_false = (f"{claim.claimant}'s claim to have {DONE[claim.action]} {claim.target} "
                                          f"on night {claim.night}")

    def opening(self) -> str:
        return f"If {self.noun} {'are' if self.plural else 'is'} true"

    def must_be_false(self) -> str:
        return f"{self.one_false} must be false"

    def is_false(self) -> str:
        return f"{self.one_false} is false"


# --- the conclusions -------------------------------------------------------------------------------

def holders(players: list[str], bodies: list[str]) -> str:
    """Who holds a role: "player_6 or player_10", "…, or is player_1's hidden body"."""
    hidden = [f"{body}'s hidden body" for body in bodies]
    if players and hidden:
        return f"{_joined(players, 'or')}, or is {_joined(hidden, 'or')}"
    return _joined(players or hidden, "or")


def role_is(role: str, players: list[str], bodies: list[str]) -> str:
    """"the Serial Killer is player_6 or player_10"."""
    return f"{ROLE_TITLES[role]} is {holders(players, bodies)}"


def wolves_are(players: list[str]) -> str:
    """Both wolves among the same players (no hidden body)."""
    if len(players) == 2:
        return f"the wolves are {players[0]} and {players[1]}"
    return f"both wolves are two of {_joined(players, 'and')}"


def player_is(player: str, roles: list[str], hidden: bool, wolf: bool) -> str:
    """What a living player (or a hidden body's role) can be: one role, a wolf (a living player
    only), or the full list."""
    subject = f"{player}'s hidden role" if hidden else player
    if wolf:
        return f"{subject} is a wolf"
    if len(roles) == 1:
        return f"{subject} is {ROLE_TITLES[roles[0]]}"
    return f"{subject} can only be {_joined([ROLE_TITLES[role] for role in roles], 'or')}"


def no_other_visitor(whom: str, night: int) -> str:
    """The reason a visit pins its visitor (catalogue AC2, line 4)."""
    return f"no other role still in play could have come to {whom} on night {night}"


def conditional(wording: Wording, clauses: list[str], reason: str | None = None) -> str:
    """F4, F5: "If player_2's watch is true, player_8 is the Healer: …"."""
    joined = clauses[0] if len(clauses) == 1 else f"{', '.join(clauses[:-1])}, and {clauses[-1]}"
    text = f"{wording.opening()}, {joined}"
    return f"{text}: {reason}." if reason else f"{text}."


def what_it_is(roles: list[str], wolf: bool) -> str:
    """"the Healer", "a wolf"."""
    return "a wolf" if wolf else ROLE_TITLES[roles[0]]


def contrapositive(wording: Wording, player: str, roles: list[str], wolf: bool) -> str:
    """F6 (catalogue AC2, line 5): "For player_8 not to be the Healer, player_2's watch must be false"."""
    return f"For {player} not to be {what_it_is(roles, wolf)}, {wording.must_be_false()}."


def evil_roles(roles: list[str], wolves: frozenset[str]) -> str:
    """"a wolf or the Serial Killer": both wolves read as "a wolf"."""
    named = []
    if wolves and wolves <= set(roles):
        named.append("a wolf")
    named += [ROLE_TITLES[role] for role in roles if not (role in wolves and wolves <= set(roles))]
    return _joined(named, "or")


def only_if_false(wording: Wording, player: str, evil: str) -> str:
    """F6 on a vote turn (catalogue "AC2 folded"): "player_8 can be the Serial Killer only if
    player_2's watch is false"."""
    return f"{player} can be {evil} only if {wording.is_false()}."
