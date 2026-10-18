"""Every sentence of the joins with claims (slice 9b: catalogue Table F, F1 and F2), in one place, so
the same join is always worded the same way. The rules are the catalogue's (§0 "Form", fold rule 2):
a certain line confirms only the part of a claim the seat's record shows, and keeps on the same line
what it does not confirm; a line that rests on a claim opens with it ("If that is true, …").
"""

from __future__ import annotations

from Agents.deduction.wording import ROLE_TITLES

DEED = {
    "investigate": "checked",
    "protect": "protected",
    "watch": "watched",
    "follow": "followed",
    "shoot": "shot at",
    "kill": "attacked",
    "sigil": "set a sigil on",
    "block": "blocked",
    "visit": "went to",
}
"""What a record or a claim says was done to its target, as a verb in the past."""

ACTION_NOUN = {
    "investigate": "a check",
    "protect": "a protection",
    "watch": "a watch",
    "follow": "a follow",
    "shoot": "a shot",
    "kill": "an attack",
    "sigil": "a sigil",
    "block": "a block",
}

SIGHTING_VERB = {"watch": "came to", "follow": "went to"}
"""A watch sees who came to its target; a follow sees where its target went."""


def _whom(holder: str | None) -> str:
    return "you" if holder is None else holder


def _role(role: str) -> str:
    return ROLE_TITLES[role]


# --- F1: the seat's own record (or a will) confirms part of a claim --------------------------------

def you_did_as_reported(claimant: str, sighting: str, target: str, night: int, action: str, role: str) -> str:
    """The seat's own action, seen by the claimant's watch on the target or follow of the seat."""
    said = "came to" if sighting == "watch" else "went to"
    return (f"{claimant} says you {said} {target} on night {night}. You did: you {DEED[action]} {target} that "
            f"night. This confirms that part of {claimant}'s report, not that {claimant} is {_role(role)}.")


def holder_did_as_reported(holder: str, target: str, night: int, action: str, claimant: str, sighting: str,
                           role: str) -> str:
    """A will's own action, seen by the claimant's watch or follow."""
    return (f"{holder}'s will shows {holder} {DEED[action]} {target} on night {night}, so {holder} went to "
            f"{target} that night, as {claimant}'s {sighting} reported. This confirms that part of the report, "
            f"not that {claimant} is {_role(role)}.")


def seen_by_you(how: str, visitor: str, target: str, holder: str | None = None) -> str:
    """What the seat's (or a will's) watch or follow saw, as the evidence of a line."""
    whose = "Your" if holder is None else f"{holder}'s will shows {holder}'s"
    if how == "watch":
        return f"{whose} watch saw {visitor} come to {target} that night."
    return f"{whose} follow saw {visitor} go to {target} that night."


def sighting_as_reported(claimant: str, sighting: str, visitor: str, target: str, night: int, evidence: str,
                         role: str) -> str:
    """Another player's sighting of a visit the seat's watch or follow (or a will's) also saw."""
    return (f"{claimant} says {visitor} {SIGHTING_VERB[sighting]} {target} on night {night}. {evidence} This "
            f"confirms that part of {claimant}'s report, not that {claimant} is {_role(role)}.")


def own_claim_as_reported(visitor: str, action: str, target: str, night: int, evidence: str,
                          role: str | None) -> str:
    """The visitor's own claimed action, its visit seen by the seat's watch or follow (or a will's):
    the visit is confirmed, never the action or the role (catalogue E13)."""
    if action == "visit":
        hedge = f"not which action {visitor} took"
        if role:
            hedge += f" or that {visitor} is {_role(role)}"
    elif role:
        hedge = f"not that {visitor} is {_role(role)} or that the visit was {ACTION_NOUN[action]}"
    else:
        hedge = f"not that the visit was {ACTION_NOUN[action]}"
    return (f"{visitor} says it {DEED[action]} {target} on night {night}. {evidence} This confirms that "
            f"{visitor} went to {target}, {hedge}.")


def chanteuse_as_reported(claimant: str, chanteuse: str, night: int, dead: bool, role: str,
                          holder: str | None = None) -> str:
    """A roleblock (the seat's own, or a will's) with the Chanteuse known: a sighting of her at the
    blocked player's door is true (catalogue AC2, line 2)."""
    whom = _whom(holder)
    opening = "You were" if holder is None else f"{holder} was"
    return (f"{opening} roleblocked on night {night}, so the Chanteuse came to {whom}, and {chanteuse} "
            f"{'was' if dead else 'is'} the Chanteuse. {claimant}'s report that {chanteuse} came to {whom} that "
            f"night is true. This does not show that {claimant} is {_role(role)}.")


def body_as_reported(claimant: str, body: str, night: int, role: str, holder: str | None = None) -> str:
    """A roleblock through the dead Chanteuse's body: a sighting of her name at the door is true in
    name only, since the Necromancer made the visit."""
    whom = _whom(holder)
    opening = "You were" if holder is None else f"{holder} was"
    return (f"{opening} roleblocked on night {night} through the dead Chanteuse's body, so a watch on {whom} "
            f"would have shown {body}. {claimant}'s report that {body} came to {whom} that night is true in "
            f"name: the Necromancer, not {body}, made that visit. This does not show that {claimant} is "
            f"{_role(role)}.")


# --- F2: a roleblock and a claimed visitor: the explanations, if the claim is true ------------------

def claimed_visitor(reporters: list[str], visitor: str, agrees: bool, night: int, holder: str | None = None) -> str:
    """The premise: who says `visitor` came to the blocked player (one or two named claims)."""
    whom = _whom(holder)
    if not reporters:
        return f"{visitor} says it came to {whom} on night {night}."
    said = f"{reporters[0]} says" if len(reporters) == 1 else f"{reporters[0]} and {reporters[1]} say"
    agreement = f", and {visitor} agrees" if agrees else ""
    return f"{said} {visitor} came to {whom} on night {night}{agreement}."


def chanteuse_or_both(premise: str, visitor: str, holder: str | None = None) -> str:
    """Catalogue AC1, line 2: never "the visitor is the Chanteuse", since a second visitor is possible."""
    return (f"{premise} If that is true, either {visitor} is the Chanteuse, or {visitor} and the Chanteuse both "
            f"came to {_whom(holder)}.")
