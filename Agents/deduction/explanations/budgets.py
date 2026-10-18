"""Catalogue F9 (level 7): limited abilities the public counts exactly, across nights (C17, C20).

Only what the mornings fix exactly is said, and only once a budget is used up:
- the Fortune Teller's self-bets: every self-bet that stopped an attack is announced (R10), on a
  different night each, and each spends one of its two; after two it has none, so an attack on it
  from then on kills it unless a protection saves it (B33, C17);
- the Illusionist's conceals: every conceal hides exactly one death, from one pool of two for the
  Illusionist and its body, and a conceal that hid nothing spends nothing (L8, C20); after two hidden
  deaths no death is hidden again. B6 says the same when a kill through its body was not hidden: then
  this line is left to it.
Not built: a self-bet with no attack on it is never announced, so fewer than two announced saves
leave the count open; the other budgets (checks, watches, sigils) count only through the wills of the
dead and the claims, and bullets are not public (R7). A claimed use beyond the limit is E11's.
"""

from __future__ import annotations

from Agents.deduction.explanations import wording
from Agents.schemas.deduction import DeductionItem, NoConcealsLeft, NoUsesLeft, PublicRecord, RoleIn, Source
from Agents.schemas.role_traits import BODY_USER, roles_acting, the_role

FORTUNE_TELLER = the_role(night_immune="self_bet")
ILLUSIONIST = roles_acting("conceal")[0]
HEALER = roles_acting("protect")[0]
NECROMANCER = BODY_USER


def budget_items(record: PublicRecord, events: list[DeductionItem]) -> list[DeductionItem]:
    """The used-up budgets, from the public record alone (the same for every seat); `events` are the
    public items, so a line B6 already says is not said twice."""
    from Agents.config.game import GameConfig  # the config package imports the prompts, which import this

    uses = GameConfig().starting_uses()
    return _self_bets(record, uses[FORTUNE_TELLER]) + _conceals(record, uses[ILLUSIONIST], events)


def _self_bets(record: PublicRecord, limit: int) -> list[DeductionItem]:
    if not record.cast_role_counts.get(FORTUNE_TELLER) or limit <= 0:
        return []
    nights: dict[str, list[int]] = {}
    for announcement in record.announcements:
        for save in announcement.saves:
            if save.saver == "self_bet":
                nights.setdefault(save.player, []).append(announcement.night)
    dead = {death.player for death in record.dead_roster}
    items = []
    for player, saved in nights.items():
        if len(saved) < limit or player in dead:
            continue
        text = wording.self_bets_used_up(player, len(saved), _savers(record))
        sources = tuple(Source("announcement", night, player) for night in saved)
        items.append(DeductionItem(row="F9", subject=player, night=saved[-1],
                                   conclusion=(RoleIn(player, frozenset({FORTUNE_TELLER})), NoUsesLeft(FORTUNE_TELLER)),
                                   text=text, sources=sources,
                                   derivation=tuple(a for a in record.announcements if a.night in saved)))
    return items


def _savers(record: PublicRecord) -> list[str]:
    """Who could still save a player from an attack (A1, B12): the living Healer while it is not
    revealed dead, and in a Necromancer cast the Necromancer through the Healer's body, while the
    Necromancer is not revealed dead (the body is usable once the Healer is revealed dead)."""
    revealed = {death.role for death in record.dead_roster if death.role and not death.concealed}
    savers = []
    if record.cast_role_counts.get(HEALER) and HEALER not in revealed:
        savers.append(wording.HEALER_SAVES)
    if record.cast_role_counts.get(HEALER) and record.cast_role_counts.get(NECROMANCER) and NECROMANCER not in revealed:
        savers.append(wording.REANIMATED_SAVES)
    return savers


def _conceals(record: PublicRecord, limit: int, events: list[DeductionItem]) -> list[DeductionItem]:
    if not record.cast_role_counts.get(ILLUSIONIST) or limit <= 0:
        return []
    if any(isinstance(fact, NoConcealsLeft) for item in events for fact in item.conclusion):
        return []  # B6 says it
    hidden = [(death.player, announcement.night) for announcement in record.announcements
              for death in announcement.deaths if death.hidden_by]
    if len(hidden) < limit:
        return []
    night = hidden[-1][1]
    return [DeductionItem(row="F9", subject=None, night=night, conclusion=(NoUsesLeft(ILLUSIONIST),),
                          text=wording.conceals_used_up(hidden),
                          sources=tuple(Source("announcement", n, player) for player, n in hidden),
                          derivation=tuple(a for a in record.announcements if any(d.hidden_by for d in a.deaths)))]
