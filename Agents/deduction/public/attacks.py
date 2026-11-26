"""Catalogue rows B1–B12 and B33: what every announced death and save implies, for every seat.

Each announced attack type names who made it, and the morning's wording names how the player
survived or how its role was hidden. From that, for the attacked player X on night n:
- each attacker went to X, under its own name (B1, B3, B4, B5, B11), shown to any watch on X,
  except the wolf's kill on a victim the living Illusionist hid (B2, catalogue L4);
- an attack through a body names the Necromancer's one action that night (B6–B9, B12, L10);
- what X can still be, when its role is not public: not a wolf if the wolves attacked it, a wolf
  or the Vigilante if a sigil struck it, not the immune roles if it died or a protection saved it,
  and so on (B2, B7, B9–B12); the Fortune Teller if its own self-bet saved it (B33);
- a wolf a sigil struck carried the pack's kill, a Vigilante shot someone; and when no such
  attack was announced, its target was immune (B5, B10);
- a death means no protection went ahead on X; a revealed death through the Illusionist's body
  means its conceals are spent (B6); one hidden through it hides no visit (B7).
Only public data is read (Agents/deduction/public/known.py), so every seat gets the same items.
"""

from __future__ import annotations

from Agents.deduction.public import wording
from Agents.deduction.public.known import body_of, immune_on, public_possible, types_announced
from Agents.schemas.deduction import (
    ActedThroughBody,
    AttackedInOwnName,
    AttackOutcome,
    CarriedPackKill,
    DeductionItem,
    NoConcealsLeft,
    NoHiddenVisitTo,
    NoKillThroughBody,
    NotProtected,
    ProtectedBy,
    PublicRecord,
    RoleIn,
    SilentAttack,
    Source,
    Visited,
)
from Agents.schemas.game_events import AnnouncedDeath, AnnouncedSave, NightAnnouncement
from Agents.schemas.role_traits import (
    BODY_OF_ATTACK_TYPE,
    BODY_USER,
    OWN_ATTACK_TYPES,
    STRUCK_BY_SIGIL,
    WOLF_ROLES,
    announced_as,
    roles_acting,
    the_role,
)

VIGILANTE = the_role(attack_announced_as="vigilante")
NECROMANCER = BODY_USER
"""It cannot act on itself through a body."""
FORTUNE_TELLER = the_role(night_immune="self_bet")
HEALER = roles_acting("protect")[0]
ILLUSIONIST = roles_acting("conceal")[0]
SIGILS = frozenset({"sigilist", "reanimated_sigilist"})
OWN_NAME_ROLES = {kind: announced_as(kind) for kind in OWN_ATTACK_TYPES}
"""Who makes each attack type under their own name."""
BODY_OF_TYPE = BODY_OF_ATTACK_TYPE
"""The dead role whose body each reanimated attack type was made through."""
DEATH_ROW = {"wolves": "B1", "serial_killer": "B3", "vigilante": "B4", "sigilist": "B5",
             "reanimated_wolves": "B6", "reanimated_vigilante": "B8", "reanimated_sigilist": "B9"}


def attack_items(record: PublicRecord) -> list[DeductionItem]:
    """Every item the announced deaths and saves imply, morning by morning."""
    items: list[DeductionItem] = []
    for announcement in record.announcements:
        for death in announcement.deaths:
            items += _event_items(death, None, announcement, record)
        for save in announcement.saves:
            items += _event_items(None, save, announcement, record)
    return items


class _Event:
    """One announced death or save, with what every item about it shares."""

    def __init__(self, death: AnnouncedDeath | None, save: AnnouncedSave | None, announcement: NightAnnouncement):
        event = death or save
        self.death, self.save, self.night = death, save, announcement.night
        self.target = event.player
        self.types = list(event.attacker_types)
        self.source = Source("announcement", announcement.night, event.player)
        self.event = event
        if death is not None:
            hidden = {"illusionist": "B2", "reanimated_illusionist": "B7"}.get(death.hidden_by)
            self.row = hidden or DEATH_ROW[self.types[0]]
        else:
            self.row = {"healer": "B11", "reanimated_healer": "B12", "self_bet": "B33"}[save.saver]

    def item(self, row: str, text: str, *facts, about_the_night: bool = False) -> DeductionItem:
        return DeductionItem(row=row, subject=None if about_the_night else self.target, night=self.night,
                             conclusion=tuple(facts), text=text, sources=(self.source,), derivation=(self.event,))


def _event_items(death, save, announcement: NightAnnouncement, record: PublicRecord) -> list[DeductionItem]:
    event = _Event(death, save, announcement)
    items = _visits(event, record) + _bodies(event, record)
    role_item = _role(event, record)
    if role_item is not None:
        items.append(role_item)
    items += _struck_attacker(event, record)
    if death is not None:
        items.append(event.item(event.row, wording.no_protection(event.target, event.night),
                                NotProtected(event.target)))
    return items


# --- who went to the attacked player ----------------------------------------------------------

def _visits(event: _Event, record: PublicRecord) -> list[DeductionItem]:
    """B1–B5, B11: each attack type under its own name, and the living Healer's save, is a visit."""
    items = []
    hidden_by = event.death.hidden_by if event.death is not None else ""
    if hidden_by == "illusionist":
        items.append(event.item("B2", wording.killer_went_there_unseen(event.target, event.night),
                                Visited(WOLF_ROLES, event.target, shown=False)))
        items.append(event.item("B2", wording.illusionist_was_alive(event.target, event.night),
                                Visited(frozenset({ILLUSIONIST}), event.target, shown=None)))
    for kind in event.types:
        if kind not in OWN_NAME_ROLES or (kind == "wolves" and hidden_by == "illusionist"):
            continue
        row = DEATH_ROW[kind] if event.death is not None else event.row
        items.append(event.item(row, wording.went_there_and_was_shown(kind, event.target, event.night),
                                Visited(OWN_NAME_ROLES[kind], event.target)))
    if event.save is not None and event.save.saver == "healer":
        items.append(event.item("B11", wording.healer_went_there(event.target, event.night),
                                ProtectedBy(event.target, through_body=False),
                                Visited(frozenset({HEALER}), event.target)))
    if hidden_by == "reanimated_illusionist":
        items.append(event.item("B7", wording.reanimated_conceal_hides_no_visit(event.target, event.night),
                                NoHiddenVisitTo(event.target)))
    return items


# --- the Necromancer's one action through a body ----------------------------------------------

def _bodies(event: _Event, record: PublicRecord) -> list[DeductionItem]:
    """B6–B9, B12: a reanimated attack or save names the body and the Necromancer's whole night."""
    items = []
    for kind in event.types:
        if kind not in BODY_OF_TYPE:
            continue
        body = body_of(BODY_OF_TYPE[kind], event.night, record)
        if body is None:
            continue  # the body is always revealed before the night in a legal game
        revealed_death = event.death is not None and not event.death.hidden_by
        row = DEATH_ROW[kind] if revealed_death else event.row
        if kind == "reanimated_sigilist":
            items.append(event.item(row, wording.necromancer_sigil_through_body(event.target, event.night, body),
                                    ActedThroughBody(body, event.target), NoKillThroughBody()))
        else:
            text = wording.necromancer_attacked_through_body(event.target, event.night, body, BODY_OF_TYPE[kind])
            items.append(event.item(row, text, ActedThroughBody(body, event.target)))
        if kind == "reanimated_wolves" and event.death is not None and not event.death.hidden_by:
            items.append(event.item("B6", wording.conceals_used_up(event.target), NoConcealsLeft()))
    if event.save is not None and event.save.saver == "reanimated_healer":
        body = body_of(HEALER, event.night, record)
        if body is not None:
            items.append(event.item("B12", wording.necromancer_protected_through_body(event.target, event.night, body),
                                    ProtectedBy(event.target, through_body=True),
                                    ActedThroughBody(body, event.target), NoKillThroughBody()))
    return items


# --- what the attacked player can be ----------------------------------------------------------

def _role(event: _Event, record: PublicRecord) -> DeductionItem | None:
    """B2, B7, B9–B12, B33: what the attack and its outcome rule out, for a player whose role the
    morning did not reveal. One item, its reasons in order, its conclusion the remaining roles."""
    if event.death is not None and event.death.role:
        return None
    target, night = event.target, event.night
    if event.save is not None and event.save.saver == "self_bet":
        return event.item("B33", wording.survived_on_own_self_bet(target, night),
                          RoleIn(target, frozenset({FORTUNE_TELLER})), AttackOutcome(target, frozenset({"self_bet"})))

    possible = set(public_possible(target, record))
    sentences, rows = [], [event.row]
    immune = [role for role in immune_on(night, record) if role in possible]
    if immune:
        if event.death is not None:
            sentences.append(wording.killed_so_not_immune(target, immune))
        else:
            sentences.append(wording.saved_so_not_immune(target, immune))
        possible -= set(immune)
    if event.save is not None and event.save.saver == "healer" and HEALER in possible:
        sentences.append(wording.healer_cannot_protect_itself(target))
        possible.discard(HEALER)
    if "wolves" in event.types and possible & WOLF_ROLES:
        sentences.append(wording.attacked_by_wolves_so_not_a_wolf(target))
        possible -= WOLF_ROLES
    if "vigilante" in event.types and VIGILANTE in possible:
        sentences.append(wording.shot_by_vigilante_so_not_vigilante(target))
        possible.discard(VIGILANTE)
    through_body = any(kind in BODY_OF_TYPE for kind in event.types) or (
        event.save is not None and event.save.saver == "reanimated_healer")
    if through_body and NECROMANCER in possible:
        sentences.append(wording.acted_on_through_body_so_not_necromancer(target))
        possible.discard(NECROMANCER)
    if SIGILS & set(event.types):
        sentence = _sigil_sentence(target, possible, record)
        if sentence is None:
            return None  # no attacker left: cannot happen in a legal game
        sentences.append(sentence)
        possible &= STRUCK_BY_SIGIL
        rows.append("B10")
    if not sentences or not possible:
        return None
    return event.item("+".join(dict.fromkeys(rows)), " ".join(sentences), RoleIn(target, frozenset(possible)))


def _sigil_sentence(target: str, possible: set[str], record: PublicRecord) -> str | None:
    """A sigil struck `target`, so it attacked in its own name: a wolf carrying the kill or the
    Vigilante (never the Serial Killer, whom a sigil cannot harm). The reason a candidate is gone
    when the roster alone removed it is said."""
    wolf = bool(possible & WOLF_ROLES)
    vigilante = VIGILANTE in possible
    if not wolf and not vigilante:
        return None
    everyone = public_possible(target, record)
    dead = ""
    if not vigilante and VIGILANTE not in everyone:
        dead = "the Vigilante is dead"
    elif not wolf and not everyone & WOLF_ROLES:
        dead = "both wolves are dead"
    return wording.struck_by_sigil_so_attacker(target, wolf, vigilante, dead)


# --- the attacker a sigil struck --------------------------------------------------------------

def _struck_attacker(event: _Event, record: PublicRecord) -> list[DeductionItem]:
    """B5, B10: a sigil struck only an attacker under its own name. A wolf so struck carried the
    pack's kill, a Vigilante shot; with no such attack announced that night, its target was immune
    (every other outcome is announced, since R10)."""
    if not SIGILS & set(event.types):
        return []
    target, night = event.target, event.night
    if event.death is not None and event.death.role:
        possible = {event.death.role}
    else:
        possible = _attacker_roles(event, record)
    if event.death is not None:
        rows = ("B5" if "sigilist" in event.types else "B9") + "+B10"
    else:
        rows = event.row + "+B10"
    if possible and possible <= WOLF_ROLES:
        attacker_type, items = "wolves", [event.item(rows, wording.wolf_struck_by_sigil_carried(target, night),
                                                     CarriedPackKill(target))]
    elif possible == {VIGILANTE}:
        attacker_type, items = "vigilante", [event.item(rows, wording.vigilante_struck_by_sigil_shot(target, night),
                                                        AttackedInOwnName(target))]
    else:
        return []
    announced = types_announced(night, record) or set()
    immune = immune_on(night, record)
    if attacker_type not in announced and immune:
        items.append(event.item(rows, wording.attack_made_but_not_announced(attacker_type, night, immune),
                                SilentAttack(attacker_type, frozenset(immune)), about_the_night=True))
    return items


def _attacker_roles(event: _Event, record: PublicRecord) -> set[str]:
    """The roles a hidden or saved player struck by a sigil can hold: the role item's conclusion."""
    role_item = _role(event, record)
    if role_item is None:
        return set()
    return set(role_item.conclusion[0].roles)
