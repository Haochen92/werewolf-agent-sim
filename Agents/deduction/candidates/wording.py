"""Every sentence of the candidate-role level (catalogue F3, F7), in one place, so the same fact is
always worded the same way. The rules for the wording are in the catalogue (§0 "Form"): name players
and nights, plain verbs, end at the conclusion. Players are listed in seat order (hidden bodies in
death order), never by how much is known about them, and a list is always the full list.
"""

from __future__ import annotations

from Agents.deduction.wording import ROLE_TITLES


def _title(role: str) -> str:
    """"The Serial Killer", to open a sentence."""
    title = ROLE_TITLES[role]
    return title[0].upper() + title[1:]


def _joined(names: list[str], last: str) -> str:
    """"a, b and c" or "a, b or c"."""
    if len(names) == 1:
        return names[0]
    return f"{', '.join(names[:-1])} {last} {names[-1]}"


def _one_of(players: list[str]) -> str:
    return players[0] if len(players) == 1 else f"one of {_joined(players, 'and')}"


def _hidden_bodies(bodies: list[str]) -> str:
    if len(bodies) == 1:
        return f"{bodies[0]}'s hidden body"
    return "the hidden body of " + _joined(bodies, "or of")


# --- the census of the evil and neutral roles (F3) --------------------------------------------

def both_wolves_dead(players: list[str]) -> str:
    return f"Both wolves are dead: {_joined(players, 'and')}."


def both_wolves_alive(players: list[str]) -> str:
    if len(players) == 2:
        return f"Both wolves are alive: {players[0]} and {players[1]}."
    return f"Both wolves are alive and are two of {_joined(players, 'and')}."


def one_wolf_dead(player: str, role: str) -> str:
    return f"One wolf is dead: {player}, {ROLE_TITLES[role]}."


def role_dead(role: str, player: str) -> str:
    return f"{_title(role)} is dead: {player}."


def alive_and_one_of(role: str, players: list[str]) -> str:
    return f"{_title(role)} is alive and is {_one_of(players)}."


def alive_because(role: str, reason: str, players: list[str]) -> str:
    """When the role could have been a hidden body but acted after it died: the reason first."""
    return f"{_title(role)} is alive: {reason}. It is {_joined(players, 'or')}."


def dead_as_hidden_body(role: str, bodies: list[str]) -> str:
    return f"{_title(role)} is dead: it is {_hidden_bodies(bodies)}."


def alive_or_hidden_body(role: str, players: list[str], bodies: list[str]) -> str:
    return f"{_title(role)} is {_one_of(players)}, or is {_hidden_bodies(bodies)}."


DEEDS = {
    "killed_through_body": "it killed through a body on night {night}",
    "acted_through_body": "it acted through a body on night {night}",
    "roleblocked": "it roleblocked {target} on night {night}",
    "roleblocked_the_carrier": "it roleblocked the wolf carrying the kill on night {night}",
    "protected": "it protected {target} on night {night}",
    "went_to": "it went to {target} on night {night}",
    "attacked": "it attacked {target} on night {night}",
    "picked": "it picked a side on night {night}",
}
"""What the role did that night, as the reason it is alive: the deed and its night."""


def alive_reason(deed: str, night: int, target: str | None) -> str:
    return DEEDS[deed].format(night=night, target=target)


# --- what each player could still be (F7) -----------------------------------------------------

def _roles(roles: list[str]) -> str:
    return _joined([ROLE_TITLES[role] for role in roles], "or")


def can_only_be(player: str, roles: list[str]) -> str:
    if len(roles) == 1:
        return f"{player} is {ROLE_TITLES[roles[0]]}."
    return f"{player} can only be {_roles(roles)}."


def hidden_role_can_only_be(body: str, roles: list[str]) -> str:
    if len(roles) == 1:
        return f"{body}'s hidden role is {ROLE_TITLES[roles[0]]}."
    return f"{body}'s hidden role can only be {_roles(roles)}."
