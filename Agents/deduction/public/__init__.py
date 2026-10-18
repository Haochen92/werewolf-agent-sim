"""Level 5 of the deduction engine: public events and what they imply (catalogue Table B).

The items here are the same for every seat: they read only the public record (PublicRecord: the
cast, the dead roster, the mornings and the read-out wills), never a seat's role, records or pack,
so they can sit in the prompt's shared, cached prefix. Not rendered yet (slice 8 renders items).
- attacks.py: B1–B12, B33 (each announced death and save);
- absences.py: B13, B14 (an attack not announced, "No one died");
- wills.py: B15–B24, B32 (each read-out will, through the level-1 rows);
- roster.py: B25–B27 (a lynched body, the Speculator's pick).
B28–B30 give no line, and B31 (the game-over lines) has no reader: no seat takes a turn after it.
"""

from __future__ import annotations

from Agents.deduction.public.absences import absence_items
from Agents.deduction.public.attacks import attack_items
from Agents.deduction.public.roster import roster_items
from Agents.deduction.public.wills import will_items
from Agents.schemas.deduction import DeductionItem, PublicRecord


def public_items(record: PublicRecord) -> list[DeductionItem]:
    """Every public item, morning by morning, then the wills and the roster. A proposition two
    rows reach (a sigil-struck wolf's silent attack and B13's) is kept once, the first time."""
    items = []
    seen = set()
    for item in attack_items(record) + absence_items(record) + will_items(record) + roster_items(record):
        key = (item.night, item.conclusion)
        if key in seen:
            continue
        seen.add(key)
        items.append(item)
    return items


__all__ = ["public_items"]
