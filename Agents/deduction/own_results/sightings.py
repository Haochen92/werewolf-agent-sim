"""Catalogue rows A26, A27 and A32–A35: what a watch or a follow implies, the seat's own or the
Necromancer's through the dead Sentinel's or Trailseer's body. Every list here is the normalized
one (Agents/deduction/records.py, catalogue L14).

- A watch's visitor acted on the target that night. A visitor under its own name is not the
  Necromancer (its visits show a dead player's name) and not the neutral (it never visits) (A26).
- A visitor who was already dead is a body the Necromancer used, with that body's ability (A27).
- An empty watch on a player who survived is complete: only a victim the living Illusionist hid
  can have a hidden visit, and that victim died. So no one else went there (A32).
- A follow that shows one player is a visit by the followed player (A33); two players means the
  Chanteuse carried the kill and also blocked someone (A34); no one rules out the roles that must
  always visit and can never be hidden (A35).
- A watch on a player the morning names as attacked or saved also shows who among those seen made
  the attack or the save (A28–A31, at_the_door.py).
"""

from __future__ import annotations

from Agents.deduction import wording
from Agents.deduction.night_state import revealed_before_night
from Agents.deduction.own_results.at_the_door import DoorReading, door_reading
from Agents.deduction.self_knowledge import possible_roles
from Agents.schemas.deduction import (
    ActedThroughBody,
    CarriedPackKill,
    NotRoleUnlessBlocked,
    NoVisitTo,
    OwnResultLine,
    ReadRecord,
    RoleIn,
    SeatView,
    WentTo,
)
from Agents.schemas.role_traits import BLOCKER, BODY_USER, NEVER_VISIT_UNDER_OWN_NAME, VISITS_TWO, roles_acting, the_role
from Agents.schemas.roles import BORROWED_ABILITY

ALWAYS_VISITS = the_role(must_act=True, blockable=False, visits="own_name")
"""Must attack every night, cannot be blocked, and its visit is never hidden."""
MUST_PROTECT = roles_acting("protect")[0]
"""Must protect another player every night, and its visit is never hidden; only a block stops it."""


def sighting_line(record: ReadRecord, view: SeatView, holder: str | None = None) -> OwnResultLine | None:
    """What a watch's visitors or a follow's destinations imply. `holder`: a dead player's watch
    read out in its will (catalogue B19), worded with its name instead of "you"."""
    if record.action == "watch":
        return _watch_line(record, view, holder)
    return _follow_line(record, view)


# --- the watch (A26, A27, A32) ----------------------------------------------------------------

def _died_that_night(player: str, night: int, view: SeatView) -> bool:
    return any(death.player == player and death.phase == "night" and death.day == night
               for death in view.dead_roster)


def _watch_line(record: ReadRecord, view: SeatView, holder: str | None = None) -> OwnResultLine | None:
    """The watch's own lines (A26, A27, A32), then what the morning adds to them (A28–A31)."""
    if record.observed:
        line = _who_was_seen(record, view)
    else:
        line = _no_one_visited(record, view)
    return _with_the_morning(line, door_reading(record, view, holder))


def _with_the_morning(line: OwnResultLine | None, door: DoorReading | None) -> OwnResultLine | None:
    if door is None:
        return line
    if line is None:
        return OwnResultLine(text=" ".join(door.sentences), row="+".join(door.rows),
                             grade="possible" if door.possible else "certain", facts=tuple(door.facts))
    possible = door.possible or line.grade == "possible"
    return OwnResultLine(
        text=" ".join([line.text, *door.sentences]),
        row="+".join([line.row, *door.rows]),
        grade="possible" if possible else "certain",
        facts=line.facts + tuple(door.facts),
    )


def _who_was_seen(record: ReadRecord, view: SeatView) -> OwnResultLine | None:
    """A26, A27: what each name on the watch's list did, as far as a visit shows."""
    target = record.target
    bodies = revealed_before_night(view.dead_roster, record.night)
    visitors = [name for name in record.observed if name not in bodies]
    body_visitors = [name for name in record.observed if bodies.get(name) in BORROWED_ABILITY]

    sentences = []
    facts = []
    if visitors:
        sentences.append(wording.visit_does_not_show_the_action())
        exclusion = _never_visit_exclusion(visitors, view)
        if exclusion:
            sentences.append(exclusion)
        for visitor in visitors:
            facts.append(WentTo(visitor, target))
            facts.append(_not_a_role_that_never_visits(visitor, view))
    for body in body_visitors:
        sentences.append(wording.acted_through_body(body, bodies[body], target))
        facts.append(ActedThroughBody(body, target))

    if not sentences:
        return None
    return OwnResultLine(text=" ".join(sentences), row="A27" if body_visitors else "A26", facts=tuple(facts))


def _no_one_visited(record: ReadRecord, view: SeatView) -> OwnResultLine | None:
    """A32. If the target died that night, a hidden carrier's visit is possible (A30, read with the
    morning in at_the_door.py)."""
    target = record.target
    if _died_that_night(target, record.night, view):
        return None
    watcher_name = record.body or view.player_id
    return OwnResultLine(
        text=wording.no_one_else_visited(target),
        row="A32",
        facts=(NoVisitTo(target, watcher_name),),
    )


# --- the follow (A33, A34, A35) ---------------------------------------------------------------

def _follow_line(record: ReadRecord, view: SeatView) -> OwnResultLine | None:
    target = record.target
    destinations = list(record.observed)
    if len(destinations) == 1:
        sentences = [wording.visit_does_not_show_the_action()]
        exclusion = _never_visit_exclusion([target], view)
        if exclusion:
            sentences.append(exclusion)
        return OwnResultLine(
            text=" ".join(sentences),
            row="A33",
            facts=(WentTo(target, destinations[0]), _not_a_role_that_never_visits(target, view)),
        )
    if len(destinations) == 2:
        return OwnResultLine(
            text=wording.visited_two_so_chanteuse(target, destinations),
            row="A34",
            facts=(RoleIn(target, frozenset({VISITS_TWO})), CarriedPackKill(target),
                   WentTo(target, destinations[0]), WentTo(target, destinations[1])),
        )
    if not destinations:
        return _visited_no_one(record, view)
    return None


def _visited_no_one(record: ReadRecord, view: SeatView) -> OwnResultLine | None:
    """A35: the Serial Killer always visits; the Healer does unless it was blocked. The Trailseer
    must visit too, but every follow is the Trailseer's own, its revealed body's or its will, and a
    game deals one, so the followed player is never it."""
    target = record.target
    possible = possible_roles(target, view)
    not_serial_killer = ALWAYS_VISITS in possible

    healer = ""
    if MUST_PROTECT in possible:
        healer = "unless_blocked" if _a_block_was_possible(record, view) else "certain"
    if not not_serial_killer and not healer:
        return None

    ruled_out = {ALWAYS_VISITS}
    facts = []
    if healer == "certain":
        ruled_out.add(MUST_PROTECT)
    elif healer == "unless_blocked":
        facts.append(NotRoleUnlessBlocked(target, MUST_PROTECT))
    facts.append(RoleIn(target, possible - ruled_out))
    return OwnResultLine(
        text=wording.visited_no_one(target, not_serial_killer, healer),
        row="A35",
        facts=tuple(facts),
    )


def _a_block_was_possible(record: ReadRecord, view: SeatView) -> bool:
    """Whether anyone could have roleblocked that night: the Chanteuse, unless she was revealed
    dead before it; or the Necromancer through her body, unless it is this seat (it followed)."""
    revealed = set(revealed_before_night(view.dead_roster, record.night).values())
    if BLOCKER not in revealed:
        return True
    necromancer_could_block = (bool(view.cast_role_counts.get(BODY_USER))
                               and view.role != BODY_USER and BODY_USER not in revealed)
    return necromancer_could_block


# --- shared -----------------------------------------------------------------------------------

def _never_visit_exclusion(names: list[str], view: SeatView) -> str:
    """The roles that never show their own name on a visit, among those one of `names` could
    otherwise hold; "" when there are none."""
    roles = [role for role in NEVER_VISIT_UNDER_OWN_NAME
             if any(role in possible_roles(name, view) for name in names)]
    if not roles:
        return ""
    return wording.not_roles_that_never_visit_in_own_name(names, roles)


def _not_a_role_that_never_visits(player: str, view: SeatView) -> RoleIn:
    return RoleIn(player, possible_roles(player, view) - set(NEVER_VISIT_UNDER_OWN_NAME))
