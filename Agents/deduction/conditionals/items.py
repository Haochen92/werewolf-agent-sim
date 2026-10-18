"""Catalogue F4, F5 and F6 as items (grade "follows_if_claims"): what a premise adds to the seat's
candidate roles, said only where it narrows them.

Each premise reruns the seat's propagation with it added (premises.py). A premise the propagation
finds impossible gives no line. Compared with the seat's own candidates (or, for a claimed action,
with its claimant's role alone, so the action's line says only what the action adds):
- the evil roles (the wolves, the lone killer) whose possible holders narrow, in one line for the
  premise: "If the current role claims are true, the Serial Killer is player_6 or player_10." For a
  claimed action, a holder lost by a player the premise pins, or by a player with its own line, is no
  news (that player's line says it). A line is shown only when three holders or fewer are left (four
  for the wolves): a longer list takes a claimant or two off the census, a long way to say little.
- each player the premise narrows, beyond losing the roles it pins on others: one role, a wolf, or a
  list of at most three roles. An evil role on one player is the role's line. "If player_2's watch is
  true, player_8 is the Healer: no other role still in play could have come to you on night 2."
  The reason is given when the claimed visit is what pins the player.
- F6, for a living player's line: the contrapositive, as its own item with the same premise. Plain,
  for one role or a wolf ("For player_8 not to be the Healer, player_2's watch must be false"), and
  worded about the evil roles the premise takes from the player when it takes them all ("player_8
  can be the Serial Killer only if player_2's watch is false": the vote-turn form).
Placement: the role lines of the role claims are shared (subject None); a claimed action's role line
goes in its claimant's entry, or, when it puts an evil role on one living player, in that player's
entry with its F6; a player's line and its F6 in that player's entry.
"""

from __future__ import annotations

from Agents.deduction.candidates import seat_constraints, solve_seat
from Agents.deduction.candidates.constraints import WOLF_ROLES
from Agents.deduction.conditionals import wording
from Agents.deduction.conditionals.premises import (
    action_premises,
    premise_constraints,
    role_claims_premise,
    visit_roles,
)
from Agents.deduction.joins.known_visits import known_visits
from Agents.deduction.night_state import deaths_before_night
from Agents.deduction.seat_view import public_record
from Agents.schemas.deduction import (
    Candidates,
    DeductionItem,
    HeldBy,
    KnownVisit,
    OnlyRoles,
    Premise,
    RoleConstraint,
    RoleIn,
    SeatView,
    Source,
    VisitAsClaimed,
)
from Agents.schemas.roles import LONE_KILLER, ROLE_SPECS, WOLVES

EVIL = frozenset(role for role, spec in ROLE_SPECS.items() if spec.side in (WOLVES, LONE_KILLER) and not spec.retired)
MOST_ROLES_LISTED = 3
"""A player's conditional list of roles is shown only this short: a longer one says little."""
MOST_HOLDERS_LISTED = 3
"""A line on an evil role is shown only when this few holders are left (one more for a wolf while
neither wolf is known: both wolves among four players)."""


class _Run:
    """One seat's propagation, solved once without a premise and then with each."""

    def __init__(self, view: SeatView):
        self.view = view
        self.known, self.constraints = seat_constraints(view)
        self.base = solve_seat(view, self.known, self.constraints)
        self.engine_visits: list[KnownVisit] = known_visits(view, public_record(view)) if self.base else []

    def under(self, premise: Premise) -> Candidates | None:
        extra = premise_constraints(premise, self.view, self.base, self.engine_visits)
        if extra is None:
            return None
        return solve_seat(self.view, self.known, self.constraints + extra)

    def under_role(self, premise: Premise) -> Candidates | None:
        """The claimant's role alone: what an action's line is compared with."""
        extra: list[RoleConstraint] = [OnlyRoles(player, frozenset({role}), "premise") for player, role in premise.roles]
        return solve_seat(self.view, self.known, self.constraints + extra) if extra else self.base


def conditional_items(view: SeatView) -> list[DeductionItem]:
    """F4 or the one role claim (F5), then each claimed action's F5 and F6, in the claims' order."""
    if not view.claims or not view.living:
        return []
    run = _Run(view)
    if run.base is None:
        return []
    items: list[DeductionItem] = []
    premise = role_claims_premise(view, run.base)
    if premise is not None:
        under = run.under(premise)
        if under is not None:
            items += _items(run, premise, under, run.base, wording.Wording(premise))
    for premise in action_premises(view, run.engine_visits):
        under = run.under(premise)
        ref = run.under_role(premise) if under is not None else None
        if under is None or ref is None:
            continue
        items += _items(run, premise, under, ref, wording.Wording(premise, _same_kind_nights(view, premise)))
    return items


def _same_kind_nights(view: SeatView, premise: Premise) -> int:
    """How many nights the claimant claims an action of this kind for (a line then names the night)."""
    claim = premise.claim
    for player in view.claims:
        if player.player == claim.claimant:
            return len({c.night for c in player.actions if c.latest and c.action == claim.action and c.night > 0})
    return 1


def _items(run: _Run, premise: Premise, under: Candidates, ref: Candidates, words: wording.Wording) -> list[DeductionItem]:
    view, base = run.view, run.base
    assumed = {player for player, _ in premise.roles}
    pinned = {player: next(iter(roles)) for player, roles in under.roles.items() if len(roles) == 1}
    players = [*under.living, *under.hidden_bodies]
    row = "F4" if premise.kind == "role_claims" else "F5"
    night = premise.night or _last_night(view)
    sources = tuple(Source("claim", premise.night, player) for player in
                    ([premise.claimant] if premise.claimant else sorted(assumed)))
    derivation = (premise.claim,) if premise.claim else ()

    def item(row_: str, subject: str | None, conclusion, text: str, vote_form: bool = False) -> DeductionItem:
        return DeductionItem(row=row_, subject=subject, night=night, conclusion=tuple(conclusion), text=text,
                             grade="follows_if_claims", premises=premise.facts, sources=sources,
                             derivation=derivation, receiver=view.player_id, vote_form=vote_form)

    lines = _player_lines(premise, base, under, ref, pinned, players)
    items = []
    explained = {player for player, _, _, _ in lines} | set(pinned)
    held = _role_lines(premise, base, under, ref, explained, players)
    if held:
        conclusion = [HeldBy(role, tuple(holders)) for role, holders in held]
        one = held[0][1][0] if len(held) == 1 and len(held[0][1]) == 1 else None
        if premise.kind != "action":
            items.append(item(row, None, conclusion, wording.conditional(words, _role_clauses(held, under))))
        elif one is not None and one in under.living:
            # An evil role on one living player: a line about that player, in its entry, with its F6.
            items.append(item(row, one, conclusion, wording.conditional(words, _role_clauses(held, under))))
            items.append(item("F6", one, conclusion, wording.contrapositive(words, one, [held[0][0]], False)))
        else:
            items.append(item(row, premise.claimant, conclusion, wording.conditional(words, _role_clauses(held, under))))
    for player, now, hidden, wolf in lines:
        in_order = [role for role in ROLE_SPECS if role in now]
        reason = _reason(run, premise, player, now) if len(now) == 1 and not hidden else None
        clause = wording.player_is(player, in_order, hidden, wolf)
        items.append(item(row, player, [RoleIn(player, now)], wording.conditional(words, [clause], reason)))
        if hidden:
            continue
        if len(now) == 1 or wolf:
            items.append(item("F6", player, [RoleIn(player, now)],
                              wording.contrapositive(words, player, in_order, wolf)))
        taken = base.roles[player] & EVIL
        if taken and not now & EVIL:
            evil = [role for role in ROLE_SPECS if role in taken]
            dealt_wolves = frozenset(role for role in WOLF_ROLES if view.cast_role_counts.get(role))
            items.append(item("F6", player, [RoleIn(player, frozenset(base.roles[player] - EVIL))],
                              wording.only_if_false(words, player, wording.evil_roles(evil, dealt_wolves)),
                              vote_form=True))
    return items


def _player_lines(premise: Premise, base: Candidates, under: Candidates, ref: Candidates, pinned: dict[str, str],
                  players: list[str]) -> list[tuple[str, frozenset[str], bool, bool]]:
    """(player, its roles under the premise, a hidden body, a wolf) for each player the premise narrows
    beyond the roles it pins on others, in a form short enough to show."""
    assumed = {player for player, _ in premise.roles}
    lines = []
    for player in players:
        if player in base.known or player in assumed:
            continue
        now = under.roles[player]
        before = ref.roles[player] - {role for other, role in pinned.items() if other != player}
        if not now < before:
            continue
        hidden = player in under.hidden_bodies
        wolf = not hidden and now == WOLF_ROLES
        if len(now) == 1 and now <= EVIL:
            continue  # the role's own line names its holder
        if len(now) == 1 or wolf or len(now) <= MOST_ROLES_LISTED:
            lines.append((player, now, hidden, wolf))
    return lines


def _role_lines(premise: Premise, base: Candidates, under: Candidates, ref: Candidates, explained: set[str],
                players: list[str]) -> list[tuple[str, list[str]]]:
    """(role, its possible holders under the premise) for each evil role the premise narrows. For a
    claimed action, a holder lost by a player with its own line (or pinned) is that line's news."""
    assumed_roles = {role for _, role in premise.roles}
    known_roles = {next(iter(base.roles[player])) for player in base.known}
    held = []
    for role in ROLE_SPECS:
        if role not in EVIL or role not in base.census or role in assumed_roles or role in known_roles:
            continue
        now = [player for player in players if role in under.roles[player]]
        before = [player for player in players if role in ref.roles[player]]
        if premise.kind == "action":
            before = [player for player in before if player not in explained or role in under.roles[player]]
        both_wolves = role in WOLF_ROLES and WOLF_ROLES <= base.census and not WOLF_ROLES & known_roles
        if len(now) > MOST_HOLDERS_LISTED + (1 if both_wolves else 0):
            continue
        if set(now) < set(before):
            held.append((role, now))
    return held


def _role_clauses(held: list[tuple[str, list[str]]], under: Candidates) -> list[str]:
    """One clause per role; both wolves in one when they have the same living holders."""
    holders = dict(held)
    wolves = [role for role in holders if role in WOLF_ROLES]
    clauses = []
    together = (len(wolves) == 2 and holders[wolves[0]] == holders[wolves[1]]
                and not set(holders[wolves[0]]) & set(under.hidden_bodies))
    if together:
        clauses.append(wording.wolves_are(holders[wolves[0]]))
    for role, players in held:
        if together and role in wolves:
            continue
        living = [player for player in players if player in under.living]
        bodies = [player for player in players if player in under.hidden_bodies]
        clauses.append(wording.role_is(role, living, bodies))
    return clauses


def _reason(run: _Run, premise: Premise, player: str, now: frozenset[str]) -> str | None:
    """"no other role still in play could have come to you on night 2": when `player` is a living
    visitor the premise claims, and without that visit the premise leaves it roles of which only
    `now` could have made it."""
    if premise.kind != "action":
        return None
    dead_before = {death.player for death in deaths_before_night(run.view.dead_roster, premise.night)}
    for fact in premise.facts:
        if not isinstance(fact, VisitAsClaimed) or fact.visitor != player or player in dead_before:
            continue
        without = Premise(kind=premise.kind, claimant=premise.claimant, roles=premise.roles, claim=premise.claim,
                          visits=premise.visits, facts=tuple(f for f in premise.facts if f != fact),
                          night=premise.night)
        loose = run.under(without)
        if loose is None or loose.roles[player] == now:
            continue
        if loose.roles[player] & visit_roles(fact, premise.night, run.view, run.base) == now:
            whom = "you" if fact.target == run.view.player_id else fact.target
            return wording.no_other_visitor(whom, premise.night)
    return None


def _last_night(view: SeatView) -> int:
    nights = [announcement.night for announcement in view.announcements]
    nights += [death.day if death.phase == "night" else death.day - 1 for death in view.dead_roster]
    return max(nights, default=0)
