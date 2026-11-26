"""Catalogue rows A28–A31: a watch read with the morning, the Sentinel's own or the Necromancer's
through the dead Sentinel's body.

Every attack is a visit, and so is the living Healer's save. A watch lists every visitor but the
watcher, except the visit of the wolf who made the kill when the living Illusionist hid the
victim's role (catalogue L4, L12). So when the morning names attacks on (or a save of) the watched
player, each attacker and the Healer is among the living players the watch saw:
- an attacker or the Healer is named when only one of them can be it; when the possible players
  are exactly as many as the attackers and savers left, each is one of them, without saying which
  (A28, A29: "one is a wolf and the other the Healer" must not say which);
- a victim the living Illusionist hid: its killer's visit is hidden, and the Illusionist's conceal
  is a visit, so the Illusionist made the kill itself unless it is one of the players seen (A30);
- a victim hidden through the Illusionist's body: no visit is hidden (A31; R5).
An attack through a body shows the body's name, which A27 already explains.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from Agents.deduction import wording
from Agents.deduction.morning import announcement_of, death_of, save_of
from Agents.deduction.night_state import revealed_before_night
from Agents.deduction.self_knowledge import possible_roles
from Agents.schemas.deduction import CarriedOrAmong, Fact, MadeBy, ReadRecord, RoleIn, SeatView, VisitorsAmong
from Agents.schemas.role_traits import OWN_ATTACK_TYPES, announced_as, roles_acting

DOER_ROLES = {
    **{kind: announced_as(kind) for kind in OWN_ATTACK_TYPES},
    "healer": frozenset(roles_acting("protect")),
}
"""Who can make each announced attack (by its type) under their own name, or the living Healer's
save. An attack through a body is not here: it shows the body's name."""
ILLUSIONIST = roles_acting("conceal")[0]
"""The role whose conceal hides the pack's victim (and is itself a visit to it)."""


@dataclass
class DoorReading:
    """What the morning adds to a watch: its sentences, their facts and the rows they implement."""

    sentences: list[str] = field(default_factory=list)
    facts: list[Fact] = field(default_factory=list)
    rows: list[str] = field(default_factory=list)
    possible: bool = False
    """True when a sentence lists explanations ("either … or")."""
    holder: str | None = None
    """The dead watcher whose read-out record this is (worded by name); None for the seat's own."""


def door_reading(record: ReadRecord, view: SeatView, holder: str | None = None) -> DoorReading | None:
    """What the morning's attacks on, or save of, the watched player add to the watch; None when
    the morning named neither, or the payload has no morning. `holder`: the watch is a dead
    player's, read out in its will (catalogue B19), and the lines name it instead of "you"."""
    morning = announcement_of(view, record.night)
    if morning is None:
        return None
    target = record.target
    death = death_of(morning, target)
    save = save_of(morning, target)
    if death is None and save is None:
        return None

    attack_types = (death or save).attacker_types
    hidden_by_the_living_illusionist = death is not None and death.hidden_by == "illusionist"
    doers = [kind for kind in attack_types if kind in DOER_ROLES
             and not (kind == "wolves" and hidden_by_the_living_illusionist)]
    if save is not None and save.saver == "healer":
        doers.append("healer")

    bodies = revealed_before_night(view.dead_roster, record.night)
    seen_alive = [name for name in record.observed if name not in bodies]
    reading = DoorReading(holder=holder)

    if hidden_by_the_living_illusionist:
        _the_hidden_killer(target, seen_alive, view, reading)
        if doers:
            reading.sentences.append(wording.other_attacks_were_seen(target, holder))
    else:
        if death is not None and death.hidden_by == "reanimated_illusionist":
            reading.sentences.append(wording.reanimated_conceal_hides_no_visit(target, holder))
            reading.rows.append("A31")
        elif doers:
            reading.sentences.append(wording.every_attack_was_a_visit(target, "healer" in doers, holder))
        watcher = record.body or view.player_id
        reading.facts.append(VisitorsAmong(target, (*record.observed, watcher)))

    if doers:
        _who_was_at_the_door(target, doers, seen_alive, view, reading)
    if not reading.sentences:
        return None
    return reading


def _the_hidden_killer(target: str, seen_alive: list[str], view: SeatView, reading: DoorReading) -> None:
    """A30: the killer's visit is hidden; the Illusionist's conceal is not, unless it made the kill."""
    reading.rows.append("A30")
    reading.sentences.append(wording.living_conceal_hides_the_killer(target, reading.holder))
    could_be_illusionist = [name for name in seen_alive if ILLUSIONIST in possible_roles(name, view)]
    if could_be_illusionist:
        reading.sentences.append(wording.illusionist_made_the_kill_or_was_seen(target, could_be_illusionist))
        reading.possible = True
    else:
        reading.sentences.append(wording.illusionist_made_the_kill(target, reading.holder))
    reading.facts.append(CarriedOrAmong(ILLUSIONIST, tuple(could_be_illusionist)))


def _who_was_at_the_door(target: str, doers: list[str], seen_alive: list[str], view: SeatView,
                         reading: DoorReading) -> None:
    """A28, A29: each attacker and the Healer is a different player among those seen. Every way of
    placing them on the players seen is tried; only what holds in all of them is said."""
    placements = _placements(doers, seen_alive, view)
    if not placements:
        return  # cannot happen in a legal game
    if any(doer != "healer" for doer in doers):
        reading.rows.append("A28")
    if "healer" in doers:
        reading.rows.append("A29")

    open_doers = []
    for doer in doers:
        players = sorted({placement[doer] for placement in placements}, key=seen_alive.index)
        reading.facts.append(MadeBy(target, doer, tuple(players)))
        if len(players) == 1:
            player = players[0]
            reading.sentences.append(wording.only_one_seen_can_be(doer, target, player, reading.holder))
            reading.facts.append(RoleIn(player, possible_roles(player, view) & DOER_ROLES[doer]))
        else:
            open_doers.append(doer)
    if not open_doers:
        return

    open_players = sorted({placement[doer] for placement in placements for doer in open_doers},
                          key=seen_alive.index)
    if len(open_players) == len(open_doers):
        # As many players as attackers and savers left: each of them is one, but not which.
        reading.sentences.append(wording.seen_are_one_each(open_players, open_doers, reading.holder))
        their_roles = frozenset().union(*(DOER_ROLES[doer] for doer in open_doers))
        for player in open_players:
            reading.facts.append(RoleIn(player, possible_roles(player, view) & their_roles))
        return
    for doer in open_doers:
        players = sorted({placement[doer] for placement in placements}, key=seen_alive.index)
        reading.sentences.append(wording.doer_is_one_of(doer, target, players))


def _placements(doers: list[str], seen_alive: list[str], view: SeatView) -> list[dict[str, str]]:
    """Every way to give each doer a different player seen who can hold its role."""
    candidates = {doer: [name for name in seen_alive if possible_roles(name, view) & DOER_ROLES[doer]]
                  for doer in doers}
    placements: list[dict[str, str]] = []

    def place(index: int, placed: dict[str, str]) -> None:
        if index == len(doers):
            placements.append(dict(placed))
            return
        doer = doers[index]
        for name in candidates[doer]:
            if name in placed.values():
                continue
            placed[doer] = name
            place(index + 1, placed)
            del placed[doer]

    place(0, {})
    return placements
