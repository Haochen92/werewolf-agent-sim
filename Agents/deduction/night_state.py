"""Public facts about a given night that every level of the engine needs: who was already dead
when it began, and who could have been immune to an attack that night.

Every rule here uses the state of the night in question, not today's: all night actions are
simultaneous, so a player revealed dead this morning still acted last night (catalogue §0,
"Use the state of night n").
"""

from __future__ import annotations

from Agents.schemas.game_events import DeathRecord

ALWAYS_IMMUNE = "serial_killer"
"""The serial killer cannot be killed at night, on any night."""
IMMUNE_ON_NIGHT_ONE = "necromancer"
"""The necromancer cannot be killed on night 1 only."""
IMMUNE_WHEN_SELF_BETTING = "fortune_teller"
"""The fortune teller cannot be killed on a night it bets on itself."""


def revealed_before_night(dead_roster: list[DeathRecord], night: int) -> dict[str, str]:
    """Players whose role was publicly revealed before night `night` began, with that role.

    That is a night death on an earlier night, or a lynch on day `night` or before (a day-n lynch
    happens before night n). A concealed body is not revealed.
    """
    revealed: dict[str, str] = {}
    for death in dead_roster:
        if death.concealed or not death.role:
            continue
        died_on_an_earlier_night = death.phase == "night" and death.day < night
        lynched_before_this_night = death.phase == "day" and death.day <= night
        if died_on_an_earlier_night or lynched_before_this_night:
            revealed[death.player] = death.role
    return revealed


def role_revealed_on_others(role: str, player: str, dead_roster: list[DeathRecord],
                            cast_role_counts: dict[str, int]) -> bool:
    """Whether every dealt copy of `role` has been publicly revealed on players other than
    `player`, at any time. Then `player` cannot hold it. (A role revealed on `player` itself
    rules nothing out: an immune player lynched the next day is still the one who was immune.)"""
    holders_other_than_player = 0
    for death in dead_roster:
        if death.role == role and not death.concealed and death.player != player:
            holders_other_than_player += 1
    return holders_other_than_player >= cast_role_counts.get(role, 0)


def roles_always_immune(night: int, cast_role_counts: dict[str, int]) -> set[str]:
    """The roles in this cast that cannot be killed on `night` whatever they choose: the serial
    killer, and the necromancer on night 1. (The fortune teller only on a self-bet night.)"""
    roles = set()
    if cast_role_counts.get(ALWAYS_IMMUNE):
        roles.add(ALWAYS_IMMUNE)
    if cast_role_counts.get(IMMUNE_ON_NIGHT_ONE) and night == 1:
        roles.add(IMMUNE_ON_NIGHT_ONE)
    return roles


def immune_candidates(target: str, night: int, own_role: str, cast_role_counts: dict[str, int],
                      dead_roster: list[DeathRecord]) -> list[str]:
    """The roles `target` could hold that would make it unkillable on `night` (catalogue L1, per
    cast). "fortune_teller" stands for a fortune teller betting on itself that night.

    Ruled out: the seat's own role (it is not the target), and a role publicly revealed on
    someone else.
    """
    candidates = sorted(roles_always_immune(night, cast_role_counts))
    if cast_role_counts.get(IMMUNE_WHEN_SELF_BETTING):
        candidates.append(IMMUNE_WHEN_SELF_BETTING)

    possible = []
    for role in candidates:
        if role == own_role:
            continue
        if role_revealed_on_others(role, target, dead_roster, cast_role_counts):
            continue
        possible.append(role)
    return possible
