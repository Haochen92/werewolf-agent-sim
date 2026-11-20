"""Level 4 of the deduction engine (slice 10): conditionals (catalogue Table F, F4 to F6; "Rendering",
level 4 and fold rule 3).

A conditional line holds in every legal game that agrees with what the seat knows and in which the
named claims are true (catalogue §0, grade 2). The engine reruns the seat's own propagation (the
candidate roles, Agents/deduction/candidates/) with the premise added for that run only:
- premises.py: which claims are premises (the current role claims; one claimed night action with its
  claimant's role), and what each adds as role constraints;
- visits.py: which roles could have made a claimed visit, from that night's morning and the rules;
- items.py: the lines, F4 and F5, and F6 (the contrapositive) as its own item;
- wording.py: the sentences.
Claims change with every message, so every item goes in the seat block. One fact is shown in one
form a turn (fold rule 3, `for_turn`): F5 on most turns, its F6 on a vote turn.

Not built: F9 across nights (a premise here is one claimed action, about one night, or roles, which
hold on every night; budgets over several nights need the use counts, C20); two named claims together.
"""

from __future__ import annotations

from collections.abc import Sequence

from Agents.deduction.conditionals.items import conditional_items
from Agents.schemas.deduction import DeductionItem


def for_turn(items: Sequence[DeductionItem], vote: bool) -> list[DeductionItem]:
    """Fold rule 3 for a fact read both ways: on a vote turn, a player's contrapositive (F6) in place
    of its F4 or F5 line, the form about the evil roles first; on any other turn, no F6."""
    if not vote:
        return [item for item in items if item.row != "F6"]
    chosen: dict[tuple, DeductionItem] = {}
    for item in items:
        key = (item.subject, item.premises)
        if item.row == "F6" and (key not in chosen or item.vote_form):
            chosen[key] = item
    kept = []
    for item in items:
        key = (item.subject, item.premises)
        if item.row == "F6" and chosen[key] is not item:
            continue
        if item.row in ("F4", "F5") and item.subject is not None and key in chosen:
            continue
        kept.append(item)
    return kept


__all__ = ["conditional_items", "for_turn"]
