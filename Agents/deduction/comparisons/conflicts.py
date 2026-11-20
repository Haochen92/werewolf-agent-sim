"""A visit stated against a whole account that leaves it out (catalogue E2b, E2c, E3a, E3b, E6b, E12,
and the seat's own movements against a sighting of it).

Statement and account on the same night (statements.py), the account leaving the visit out:
- "to" (a watch on the target): no name the statement allows is on the list, and none is the watcher
  (a watch never lists its own visit); the statement is one a watch could see;
- "by" (a follow, or the seat's own movements): the target is not on the list; the statement is one a
  watch could see (a follow sees no more);
- "none_by" (I visited no one; I was roleblocked): the visitor is the player;
- "not_to" (I did not go to X): the visitor and the target are the player and X.
Then, by source:
- an engine source against a claim: the claim is false (certain);
- two claims: they cannot both be true, never which (Table E);
- two engine sources never disagree, and a claim is never set against its own claimant's.
An engine watch on the night's concealed victim, and an engine follow on a night the living
Illusionist hid a death, are not whole for what their wording says ("everyone who came"), so they are
not read. Each false claim gets one line (the first account that shows it), each pair of claims one.
"""

from __future__ import annotations

from Agents.deduction.comparisons import wording
from Agents.deduction.comparisons.statements import concealed_victim
from Agents.schemas.deduction import (
    DeductionItem,
    NotAllTrue,
    SeatView,
    Source,
    VisitList,
    VisitStatement,
)


def conflict_items(view: SeatView, statements: list[VisitStatement], lists: list[VisitList]) -> list[DeductionItem]:
    n = wording.Names(view.player_id)
    living = set(view.living)
    items = []
    said: set = set()
    for account in lists:
        if not _whole(view, account):
            continue
        for statement in statements:
            if statement.night != account.night or not _leaves_out(statement, account):
                continue
            item = _item(view, n, statement, account, living)
            if item is None:
                continue
            key = _key(statement, account)
            if key in said:
                continue
            said.add(key)
            items.append(item)
    return items


def _whole(view: SeatView, account: VisitList) -> bool:
    if account.source == "claim" or account.record is None:
        return True
    if account.kind == "to":
        return concealed_victim(view, account.night) != account.subject
    return concealed_victim(view, account.night) is None


def _leaves_out(statement: VisitStatement, account: VisitList) -> bool:
    one = statement.visitors[0] if len(statement.visitors) == 1 else None
    if account.kind == "to":
        allowed = {*account.names, account.watcher}
        return statement.shown and statement.target == account.subject and not allowed & set(statement.visitors)
    if one is None or one != account.subject:
        return False
    if account.kind == "by":
        return statement.shown and statement.target not in account.names
    if account.kind == "none_by":
        return True
    return statement.target == account.names[0]  # not_to


def _key(statement: VisitStatement, account: VisitList) -> tuple:
    if statement.source == "claim" and account.source == "claim":
        return ("pair", statement.claim, account.claim)
    false = statement.claim if statement.source == "claim" else account.claim
    return ("false", false, statement.night)


def _item(view: SeatView, n: wording.Names, statement: VisitStatement, account: VisitList,
          living: set[str]) -> DeductionItem | None:
    engine_statement, engine_account = statement.source != "claim", account.source != "claim"
    if engine_statement and engine_account:
        return None
    if statement.claim is not None and account.claim is not None and statement.claim.claimant == account.claim.claimant:
        return None
    night = statement.night
    sources = _sources(statement, account)
    derivation = tuple(x for x in (statement.claim or (statement.known.record if statement.known else None),
                                   account.claim or account.record) if x is not None)
    only = _only_blocker(n, statement, account)
    if engine_account:
        subject = statement.claim.claimant
        text = wording.is_false(_statement_clause(n, statement, night, True),
                                _account_evidence(n, statement, account) + only,
                                "report" if _is_sighting(statement) else "claim")
        conclusion = NotAllTrue(statement.facts)
        grade_premises = ()
    elif engine_statement:
        subject = account.claim.claimant
        text = wording.is_false(_account_clause(n, account, night, True), _statement_evidence(n, statement) + only,
                                _account_kind(account))
        conclusion = NotAllTrue(account.facts)
        grade_premises = ()
    else:
        subject = _pair_subject(statement, account, living)
        if subject is None:
            return None
        reason = None
        if account.kind == "none_by" and account.claim.blocked:
            reason = wording.blocked_goes_nowhere()
        elif statement.block:
            reason = "A roleblock is a visit." if not only else wording.only_blocker_sentence(n, statement.visitors[0])
        text = wording.cannot_both(_statement_clause(n, statement, night, True), _account_clause(n, account, night, False),
                                   reason)
        conclusion = NotAllTrue((*statement.facts, *account.facts))
        grade_premises = ()
    if subject not in living:
        return None
    row = _row(statement, account)
    return DeductionItem(row=row, subject=subject, night=night, conclusion=(conclusion,), text=text,
                         premises=grade_premises, sources=sources, derivation=derivation, receiver=view.player_id)


def _only_blocker(n: wording.Names, statement: VisitStatement, account: VisitList) -> str:
    """A roleblock set against one player's movements rests on that player being the only one who
    could have made it: said on the line."""
    if not statement.block or account.kind == "to":
        return ""
    return wording.only_blocker(n, statement.visitors[0])


def _pair_subject(statement: VisitStatement, account: VisitList, living: set[str]) -> str | None:
    """The player whose own movements are in question, when one of the two claims is its own; else
    the claimant of the whole account. A living one."""
    first = account.claim.claimant
    if account.kind in ("to", "by") and statement.claim.claimant in statement.visitors:
        first = statement.claim.claimant
    for player in (first, statement.claim.claimant, account.claim.claimant):
        if player in living:
            return player
    return None


def _row(statement: VisitStatement, account: VisitList) -> str:
    if statement.block or (account.kind == "none_by" and account.claim is not None and account.claim.blocked):
        return "E6b"
    if account.kind == "none_by":
        return "E2c"
    if account.kind == "not_to":
        return "E2b"
    if account.source == "will" or statement.source == "will":
        return "E12"
    return "E3a" if account.kind == "to" else "E3b"


def _sources(statement: VisitStatement, account: VisitList) -> tuple[Source, ...]:
    out = []
    holder_of_statement = statement.known.holder if statement.known else (statement.target if statement.block else None)
    for source, claim, holder in ((statement.source, statement.claim, holder_of_statement),
                                  (account.source, account.claim, account.holder)):
        if source == "claim":
            out.append(Source("claim", statement.night, claim.claimant))
        elif source == "will":
            out.append(Source("will", statement.night, holder))
        else:
            out.append(Source("own_record", statement.night))
    return tuple(out)


def _is_sighting(statement: VisitStatement) -> bool:
    return statement.claim is not None and statement.claim.action in ("watch", "follow") and not statement.block \
        and statement.visitors[0] != statement.claim.claimant


# --- the clauses --------------------------------------------------------------------------------

def _statement_clause(n: wording.Names, statement: VisitStatement, night: int, first: bool) -> str:
    claim = statement.claim
    words = wording.when(night, first)
    if statement.block:
        return wording.roleblocked(claim.claimant, words)
    if _is_sighting(statement):
        return wording.sighting(n, claim.claimant, claim.action, statement.visitors[0], statement.target, words)
    return wording.own_visit(n, claim.claimant, claim.action, statement.target, words)


def _account_clause(n: wording.Names, account: VisitList, night: int, first: bool) -> str:
    claim = account.claim
    words = wording.when(night, first)
    if account.kind == "to":
        return wording.saw_no_one_come(n, claim.claimant, account.subject, words)
    if account.kind == "by":
        return wording.saw_visit_no_one(n, claim.claimant, account.subject, words)
    if account.kind == "not_to":
        return wording.did_not_go_to(n, claim.claimant, account.names[0], words)
    if claim.blocked:
        return wording.roleblocked(claim.claimant, words)
    return wording.visited_no_one(claim.claimant, words)


def _account_kind(account: VisitList) -> str:
    if account.kind in ("to", "by"):
        return "report"
    return "claim" if account.claim.blocked else "statement"


def _statement_evidence(n: wording.Names, statement: VisitStatement) -> str:
    if statement.block:
        holder = None if statement.source == "own_record" else statement.target
        return wording.you_were_blocked(holder)
    known = statement.known
    if known.how == "own_action":
        return wording.you_did(n, known.holder, known.action, known.target)
    return wording.you_saw(n, known.holder, known.how, known.visitor, known.target)


def _account_evidence(n: wording.Names, statement: VisitStatement, account: VisitList) -> str:
    if account.kind == "to":
        missing = wording.no_blocker_among() if statement.block else wording.not_among(n, statement.visitors[0])
        return wording.watch_saw_everyone(n, account.holder, account.subject, missing)
    if account.record is not None:
        return wording.follow_saw_everywhere(n, account.holder, account.subject, wording.not_among(n, statement.target))
    return wording.you_did_not_go(n, statement.target)
