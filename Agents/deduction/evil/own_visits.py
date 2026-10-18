"""An evil seat's own nights against the claims it might make about them (owner, 2026-10-17: evil
seats build no fake claims; they get the certain facts, never advice). From the seat's own records
and the public mornings, on the two most recent nights:

- a protection of a player its own visit went to and who died that night (E4b);
- an action on a player already dead when the night began (E14): the players who died just before
  it (killed the night before, or voted out that day), the deaths a night's number is mixed up with;
  last night only (the commonest and wordiest of these lines);
- the Chanteuse who carried the pack's kill and blocked someone else made two visits; when the
  living Illusionist's conceal hid neither (L4), a follow of her or a watch on each shows two
  visits, which only the Chanteuse makes (E2a's rule).
The first two are Table E's comparisons (record.py `claim_items`) run on the claim the seat could
make: a line only where that comparison calls the claim false.

The seat's visits: its own actions that went ahead on a player (a wolf's skill, the Serial Killer's
kill), the Illusionist's conceal (a visit to the pack's victim whenever the pack's kill went ahead),
and the pack's kill when the seat carried it. The carrier rotates through the wolves alive that
night in seat order (Agents/rules/night.py `pack_carrier`); it is known only when the seat knows
every wolf dealt (its living pack and the revealed dead). The Necromancer is left out: its visits
are under the bodies' names, never its own.

Two nights: claims are about last night or the one before far more often than older nights, and an
older night's lines would lengthen the block for the rest of the game.
"""

from __future__ import annotations

from Agents.deduction.comparisons import wording
from Agents.deduction.comparisons.record import claim_items
from Agents.deduction.comparisons.statements import Possible, concealed_victim
from Agents.deduction.joins.known_visits import VISITING_ACTIONS
from Agents.deduction.morning import announcement_of
from Agents.deduction.night_state import deaths_before_night
from Agents.rules.night import pack_carrier
from Agents.rules.night_record import PACK_ACTOR
from Agents.rules.seats import seat_order
from Agents.schemas.deduction import (
    ActionClaim,
    CarriedPackKill,
    DeductionItem,
    NotProtected,
    NoVisitTo,
    RoleIn,
    SeatView,
    Source,
    VisitAsClaimed,
    WentTo,
)
from Agents.schemas.role_traits import BODY_USER, VISITS_TWO
from Agents.schemas.roles import LONE_KILLER, ROLE_SPECS, WOLVES

RECENT_NIGHTS = 2
"""The nights the lines cover, counting back from last night."""
CHANTEUSE = VISITS_TWO
NECROMANCER = BODY_USER
"""Its visits are under the bodies' names: no own-visit line."""
DEAD_TARGET_ACTIONS = ("investigate", "watch", "follow", "protect")
"""The claims the dead-target line names (any action on the dead is false; these are the ones said)."""


def own_visit_items(view: SeatView, today: int, possible: Possible) -> list[DeductionItem]:
    """The seat's lines, night by night, oldest first: two visits, a protection, the dead. Night n
    follows day n, so on day (or night) `today` the nights before it are resolved."""
    spec = ROLE_SPECS.get(view.role)
    if (spec is None or spec.side not in (WOLVES, LONE_KILLER) or view.role == NECROMANCER
            or view.player_id not in view.living):
        return []
    items = []
    for night in range(max(1, today - RECENT_NIGHTS), today):
        visits = _visits(view, night)
        items += _two_visits(view, night, visits)
        items += _protections(view, night, visits, today, possible)
        if night == today - 1:  # last night only (coordinator, 2026-10-18): the commonest, wordiest line
            items += _dead_targets(view, night, today, possible)
    return items


# --- the seat's own visits ----------------------------------------------------------------------

def _visits(view: SeatView, night: int) -> dict[str, bool]:
    """Every player the seat went to that night, each with whether a watch or a follow shows it:
    only a carrier's visits to the victim the living Illusionist concealed are hidden (L4)."""
    pack = next((own for own in view.night_records
                 if own.actor == PACK_ACTOR and own.day == night and own.action == "kill"), None)
    victim = pack.target if pack is not None and pack.result != "roleblocked" else None
    carried = victim is not None and _carrier(view, night) == view.player_id
    hidden = concealed_victim(view, night) if carried else None
    targets = []
    for own in view.night_records:
        if own.day != night or own.actor != view.player_id or own.result == "roleblocked":
            continue
        if own.action == "conceal" and victim:
            targets.append(victim)
        elif own.action in VISITING_ACTIONS and own.target:
            targets.append(own.target)
    if carried:
        targets.append(victim)
    return {target: target != hidden for target in seat_order(set(targets))}


def _carrier(view: SeatView, night: int) -> str | None:
    """The wolf who carried the pack's kill that night, when the seat knows every wolf dealt."""
    dealt = sum(count for role, count in view.cast_role_counts.items() if role in ROLE_SPECS and ROLE_SPECS[role].pack)
    wolves = {view.player_id, *view.pack_roles}
    wolves |= {death.player for death in view.dead_roster
               if not death.concealed and death.role in ROLE_SPECS and ROLE_SPECS[death.role].pack}
    if len(wolves) != dealt:
        return None
    gone = {death.player for death in deaths_before_night(view.dead_roster, night)}
    return pack_carrier([wolf for wolf in wolves if wolf not in gone], night)


def _as_claim(view: SeatView, night: int, action: str, target: str, today: int) -> ActionClaim:
    """The claim the seat could make today that its `action` on `target` went ahead that night."""
    return ActionClaim(claimant=view.player_id, day=today, night=night, action=action, target=target,
                       result="no_attack" if action == "protect" else "not_said", seen=(), latest=True,
                       blocked=False, completed=True, seen_complete=False, source="speaker")


def _item(view: SeatView, row: str, night: int, text: str, conclusion: tuple, derivation: tuple = (),
          kind: str = "dead_roster") -> DeductionItem:
    return DeductionItem(row=row, subject=None, night=night, conclusion=conclusion, text=text,
                         sources=(Source("own_record", night, view.player_id), Source(kind, night)),
                         derivation=derivation, receiver=view.player_id)


# --- the lines ----------------------------------------------------------------------------------

def _two_visits(view: SeatView, night: int, visits: dict[str, bool]) -> list[DeductionItem]:
    if view.role != CHANTEUSE or len(visits) != 2 or not all(visits.values()) or announcement_of(view, night) is None:
        return []
    first, second = visits
    facts = (RoleIn(view.player_id, frozenset({CHANTEUSE})), CarriedPackKill(view.player_id),
             VisitAsClaimed(view.player_id, view.player_id, first, shown=True),
             VisitAsClaimed(view.player_id, view.player_id, second, shown=True))
    return [_item(view, "E2a+own", night, wording.own_two_visits(first, second, night), facts, kind="announcement")]


def _protections(view: SeatView, night: int, visits: dict[str, bool], today: int,
                 possible: Possible) -> list[DeductionItem]:
    items = []
    for target in visits:
        claim = _as_claim(view, night, "protect", target, today)
        if any(item.row == "E4b" for item in claim_items(view, claim, today, possible)):
            items.append(_item(view, "E4b+own", night, wording.own_protection_false(target, night),
                               (WentTo(view.player_id, target), NotProtected(target)), (claim,)))
    return items


def _dead_targets(view: SeatView, night: int, today: int, possible: Possible) -> list[DeductionItem]:
    """The players who died just before the night: the night before, or voted out on its day."""
    recent = [death for death in deaths_before_night(view.dead_roster, night)
              if (death.phase == "night" and death.day == night - 1) or (death.phase == "day" and death.day == night)]
    order = seat_order(death.player for death in recent)
    dead, claims = [], []
    for death in sorted(recent, key=lambda death: order.index(death.player)):
        said = [_as_claim(view, night, action, death.player, today) for action in DEAD_TARGET_ACTIONS]
        if all(any(item.row == "E14" for item in claim_items(view, claim, today, possible)) for claim in said):
            dead.append((death.player, wording.death_words(death.phase, death.day)))
            claims += said
    if not dead:
        return []
    facts = tuple(NoVisitTo(player, "") for player, _ in dead)
    return [_item(view, "E14+own", night, wording.own_dead_targets(dead, night), facts, tuple(claims))]
