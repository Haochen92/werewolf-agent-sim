"""What the public knows, in the forms the public rows read it.

The public rows reuse the level-1 helpers (who can still hold which role, the immune roles of a
night), which read a SeatView. Here that view is built from the public record alone: no seat's role,
records or pack. For a read-out will it is the view of the dead holder, whose role and records are
public from the reveal on (catalogue L11), so the level-1 rows run on a will exactly as on a seat's
own record.
"""

from __future__ import annotations

from Agents.deduction.morning import attack_types
from Agents.deduction.night_state import revealed_before_night, roles_always_immune
from Agents.deduction.self_knowledge import possible_roles
from Agents.schemas.deduction import PublicRecord, SeatView
from Agents.schemas.game_events import NightActionRecord, ReadOutWill, WillClause
from Agents.schemas.role_traits import WOLF_ROLES
from Agents.schemas.roles import ROLE_SPECS


def public_view(record: PublicRecord) -> SeatView:
    """The view of a seat that knows only the public record."""
    return SeatView(player_id="", role="", cast_role_counts=record.cast_role_counts,
                    dead_roster=record.dead_roster, night_records=[], announcements=record.announcements,
                    wills=record.wills)


def will_record(will: ReadOutWill, clause: WillClause) -> NightActionRecord:
    """A will's night as the record it was read from, with only what the will said. A roleblocked
    night does not say what was tried: the role's own action stands in, which no roleblock row
    reads."""
    action = clause.action or ROLE_SPECS[will.role].night_action
    return NightActionRecord(day=clause.night, actor=will.holder, action=action, target=clause.target,
                             outcome="", result=clause.result, seen=list(clause.seen))


def holder_view(record: PublicRecord, will: ReadOutWill) -> SeatView:
    """The dead holder's view, from its read-out will: its role and its records, as public now."""
    return SeatView(player_id=will.holder, role=will.role, cast_role_counts=record.cast_role_counts,
                    dead_roster=record.dead_roster,
                    night_records=[will_record(will, clause) for clause in will.clauses],
                    announcements=record.announcements, wills=record.wills)


def public_possible(player: str, record: PublicRecord) -> frozenset[str]:
    """The dealt roles `player` can still hold, as far as the public roster shows."""
    return possible_roles(player, public_view(record))


def body_of(role: str, night: int, record: PublicRecord) -> str | None:
    """The player revealed dead before night `night` as `role`: the body the Necromancer used."""
    for player, revealed_role in revealed_before_night(record.dead_roster, night).items():
        if revealed_role == role:
            return player
    return None


def immune_on(night: int, record: PublicRecord) -> list[str]:
    """The roles that could fail an attack in silence on `night` (catalogue L1, since R10): the
    Serial Killer, or the Necromancer on night 1, unless revealed dead before that night."""
    gone = set(revealed_before_night(record.dead_roster, night).values())
    return sorted(roles_always_immune(night, record.cast_role_counts) - gone)


def types_announced(night: int, record: PublicRecord) -> set[str] | None:
    """Every attack type the morning after `night` named; None when the payload has no such
    morning (an absence then proves nothing)."""
    for announcement in record.announcements:
        if announcement.night == night:
            return attack_types(announcement)
    return None


def wolf_alive_at_start(night: int, record: PublicRecord) -> bool:
    """Whether a wolf was certainly alive when `night` began. A body hidden by the living
    Illusionist is never a wolf; one hidden through its body may be (catalogue L8), and so may one
    whose morning the payload lacks."""
    wolves_dealt = sum(record.cast_role_counts.get(role, 0) for role in WOLF_ROLES)
    revealed = revealed_before_night(record.dead_roster, night)
    wolves_dead = sum(1 for role in revealed.values() if role in WOLF_ROLES)
    hidden_may_be_wolves = 0
    for death in record.dead_roster:
        died_before = (death.phase == "night" and death.day < night) or (death.phase == "day" and death.day <= night)
        if died_before and death.concealed and _hidden_by(death.player, death.day, record) != "illusionist":
            hidden_may_be_wolves += 1
    return wolves_dealt - wolves_dead - hidden_may_be_wolves >= 1


def _hidden_by(player: str, night: int, record: PublicRecord) -> str | None:
    for announcement in record.announcements:
        if announcement.night == night:
            for death in announcement.deaths:
                if death.player == player:
                    return death.hidden_by
    return None
