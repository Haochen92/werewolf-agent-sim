"""Which roles could have made a visit (catalogue Table F, F5: "no other role still in play could have
come to you on night 2"). A claim taken as true says a visit went ahead: a visitor went to a target on
a night. These rules turn that into a constraint on the visitor's role, from that night's morning and
the rules alone (sound, not complete: a role is left out only when no legal night that agrees with the
morning lets it make the visit).

- A living name is not the Necromancer (its visits show a body's name) and not a neutral, which never
  visits (C10). A name already dead when the night began is a body: the Necromancer acted through it.
- Each role makes at most one visit a night, except the Chanteuse carrying the pack's kill (her kill
  and her block). An announced attack places its maker's visit: the Serial Killer's and the
  Vigilante's at their victim, the Sigilist's at the player its sigil struck; a save the morning
  credits to the Healer places the Healer's; a wolves' attack places the Illusionist's, since its
  conceal and its kill both go to the pack's victim.
- Every visit of the Serial Killer, the Vigilante and the Illusionist is an attack (or the conceal
  beside the pack's attack), and an attack that went ahead is announced unless its target was
  silently immune that night (the Serial Killer; the Necromancer on night 1; a fortune teller's
  self-bet is announced, R10). So they went to the target only if that attack on it was announced,
  or the target could have been silently immune.
- No wolf visits a player who can only be a wolf: the pack kills and the Chanteuse blocks non-wolves.
- Two visits by one living name on one night: that player is the Chanteuse.
"""

from __future__ import annotations

from collections.abc import Iterable

from Agents.deduction.candidates.constraints import NEVER_VISIT_UNDER_OWN_NAME, WOLF_ROLES
from Agents.deduction.morning import placed_visits
from Agents.deduction.night_state import roles_always_immune
from Agents.schemas.game_events import NightAnnouncement
from Agents.schemas.role_traits import VISITS_TWO, roles_acting, roles_with

CHANTEUSE = VISITS_TWO
TWO_VISITS = frozenset(roles_with(visits_two=True))
"""The one role that can visit two players on one night: the Chanteuse carrying the pack's kill, who
also blocks (catalogue L4, A34)."""
VISIT_IS_AN_ATTACK = frozenset(roles_acting("kill") + roles_acting("conceal"))
"""The roles whose every visit is an announced attack unless its target was silently immune: those
whose own action is a kill, and the conceal (a visit to the pack's victim)."""


def roles_that_could_visit(target: str, night: int, announcement: NightAnnouncement | None, dealt: frozenset[str],
                           target_roles: frozenset[str], cast_role_counts: dict[str, int]) -> frozenset[str]:
    """The roles a living player could hold and still have gone to `target` on `night`, with an
    action that went ahead. `target_roles`: the roles the target can hold, as the seat knows (to
    tell whether it could have been silently immune, or can only be a wolf). Without the morning of
    that night, only C10."""
    allowed = set(dealt) - NEVER_VISIT_UNDER_OWN_NAME
    if announcement is None:
        return frozenset(allowed)
    placed = placed_visits(announcement)
    for role, players in placed.items():
        if target not in players and role not in TWO_VISITS:
            allowed.discard(role)
    silently_immune = bool(target_roles & roles_always_immune(night, cast_role_counts))
    for role in VISIT_IS_AN_ATTACK:
        if target not in placed.get(role, set()) and not silently_immune:
            allowed.discard(role)
    if target_roles <= WOLF_ROLES:
        allowed -= WOLF_ROLES
    return frozenset(allowed)


def visited_twice(visits: Iterable[tuple[str, str]]) -> list[str]:
    """The visitors with two different targets among `visits` (visitor, target) of one night."""
    targets: dict[str, set[str]] = {}
    for visitor, target in visits:
        targets.setdefault(visitor, set()).add(target)
    return [visitor for visitor, where in targets.items() if len(where) > 1]
