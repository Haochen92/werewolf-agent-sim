"""Level 4 of the deduction engine (slice 10): conditionals (Agents/deduction/conditionals/; catalogue
Table F, F4 to F6, of evidence/reasoning_failures/deduction_catalogue.md).

- Constructed games through the real engine, with constructed claims: a watch that pins its visitor
  (AC2 constructed), a claim that only narrows (a check: "is a wolf"), the Vigilante at the Serial
  Killer's door (the immune-target branch), the Chanteuse's two visits, and where nothing may be said:
  a premise the seat knows cannot hold, a withdrawn claim, two claims for one role, the role claim
  alone, a claim the seat can check.
- The acceptance cases on their own frozen payloads: AC2 lines 4, 5 and 6 and AC4 line 4 as items,
  exactly; the blocks as rendered on a vote turn (the form of "AC2 folded") and on any other turn.
- Fold rule 3: F5 on most turns, its F6 on a vote turn (the form about the evil roles first).
- The leak boundary: hidden roles swapped and hidden state planted change nothing.
- The oracles. The truth oracle: random legal games with true and false claims, role claims and
  withdrawals: whenever a line's premise holds in the real game, its conclusion does too, and the
  role claims a line assumes are exactly the current ones. The brute-force oracle
  (tests/factories/role_assignments.py `add_premise`): every role a line states holds in every deal
  that agrees with the seat's view and the premise, the claimed visits read from the rules deal by deal.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path

from Agents.deduction import own_result_lines, seat_view_from_payload
from Agents.deduction.blocks import deduction_blocks
from Agents.deduction.conditionals import conditional_items, for_turn
from Agents.deduction.joins.known_visits import known_visits
from Agents.deduction.seat_view import public_record
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.schemas.deduction import HeldBy, RoleIn, SeatView
from Agents.schemas.game_events import DayChannel, DaySummary
from tests.engine.deduction.test_candidates import Table, _ac2, _ac4, _continuing_snapshots, _ne_sp, _sk_sp
from tests.factories.random_claims import random_claims, random_role_claims
from tests.factories.random_nights import _game_over, public_fact_holds, random_game
from tests.factories.role_assignments import add_premise, oracle_of


def _said(day: int, player: str, *actions: tuple, claim: str = "none", seq: int = 0) -> DayChannel:
    return DayChannel(day=day, seq=seq, player=player, message="(a claim)", claim=claim,
                      claimed_night_actions=[dict(zip(("night", "action", "target", "result", "seen"), a))
                                             for a in actions])


def _view(table: Table, seat: str, day: int, *lines: DayChannel, summaries=(), vote: bool = False) -> SeatView:
    return seat_view_from_payload({**table.payload(seat), "day_channel": list(lines), "day_summaries": list(summaries),
                                   "current_day": day, "vote_turn": vote})


def _lines(table: Table, seat: str, day: int, *lines: DayChannel, summaries=()) -> list[str]:
    return [item.text for item in conditional_items(_view(table, seat, day, *lines, summaries=summaries))]


# --- AC2 constructed: a watch that pins its visitor ---------------------------------------------------

AC2_LINE_4 = ("If player_2's watch is true, player_8 is the Healer: no other role still in play could have come to you "
              "on night 2.")
AC2_LINE_5 = "For player_8 not to be the Healer, player_2's watch must be false."
AC2_LINE_6 = "If the current role claims are true, the Serial Killer is player_6 or player_10."
AC2_VOTE = "player_8 can be the Serial Killer only if player_2's watch is false."
AC4_LINE_4 = "If player_9's claim is true, the Necromancer is player_3 or player_10."


def _ac2_claims() -> list[DayChannel]:
    """AC2's day-3 claims: player_2 the Sentinel (its night-2 watch on player_5 saw player_7 and player_8),
    player_4 the Sigilist (its sigil struck player_7), player_8 the Healer (it protected player_5)."""
    return [_said(3, "player_2", (2, "watch", "player_5", "not_said", ["player_7", "player_8"]), claim="sentinel"),
            _said(3, "player_4", (2, "sigil", "player_7", "died", []), claim="sigilist", seq=1),
            _said(3, "player_8", (2, "protect", "player_5", "no_attack", []), claim="healer", seq=2)]


def test_a_watch_pins_its_visitor_and_the_role_claims_narrow_the_serial_killer():
    """AC2 constructed. Under player_2's watch, player_8 came to player_5 on night 2: the Serial Killer's
    visit that night was to player_3, the sigil struck player_7, a Vigilante's shot on player_5 would
    have been announced (player_5, the seat, is not immune), the Speculator never visits, the seat is
    the Investigator, player_2 the Sentinel; the Trailseer, the Chanteuse and the Illusionist are
    revealed. Only the Healer is left."""
    items = conditional_items(_view(_ac2(), "player_5", 3, *_ac2_claims()))
    assert [(item.row, item.subject, item.vote_form, item.text) for item in items] == [
        ("F4", None, False, AC2_LINE_6),
        ("F5", "player_8", False, AC2_LINE_4),
        ("F6", "player_8", False, AC2_LINE_5),
        ("F6", "player_8", True, AC2_VOTE),
    ]
    f4, f5, f6, vote = items
    assert f4.conclusion == (HeldBy("serial_killer", ("player_6", "player_10")),)
    assert f5.conclusion == f6.conclusion == (RoleIn("player_8", frozenset({"healer"})),)
    assert f5.premises == f6.premises == vote.premises and all(item.grade == "follows_if_claims" for item in items)
    assert {fact.player for fact in f4.premises} == {"player_2", "player_4", "player_8"}


def test_the_role_claim_alone_says_nothing_and_a_watch_on_another_night_only_narrows():
    """player_2's role claim alone takes one player off the Serial Killer's list of five: no line. The
    same watch on night 1 does not pin player_8: on night 1 the sigil struck no one, so the Sigilist
    could have come too. The Serial Killer's list loses only player_8, which player_8's own line says."""
    assert _lines(_ac2(), "player_5", 3, _said(3, "player_2", claim="sentinel")) == []
    night_one = _said(3, "player_2", (1, "watch", "player_5", "not_said", ["player_8"]), claim="sentinel")
    assert _lines(_ac2(), "player_5", 3, night_one) == [
        "If player_2's watch is true, player_8 can only be the Sigilist or the Healer.",
        "player_8 can be the Serial Killer only if player_2's watch is false.",
    ]


# --- a claim that only narrows: a check -----------------------------------------------------------------

def _checked() -> Table:
    return Table(_sk_sp()).night(1, ("player_7", "kill", "player_10"), ("player_9", "kill", "player_5"),
                                 ("player_1", "investigate", "player_7"))


def test_a_claimed_check_makes_its_target_a_wolf_if_true():
    check = _said(2, "player_1", (1, "investigate", "player_7", "suspicious", []), claim="investigator")
    assert _lines(_checked(), "player_2", 2, check) == [
        "If player_1's check is true, player_7 is a wolf.",
        "For player_7 not to be a wolf, player_1's check must be false.",
    ]
    clear = _said(2, "player_1", (1, "investigate", "player_7", "not_suspicious", []), claim="investigator")
    assert _lines(_checked(), "player_2", 2, clear) == []  # "not a wolf" leaves six roles: too long a list


def test_a_suspicious_check_in_a_necromancer_cast_from_night_2_leaves_the_necromancer_open():
    """NE+SP. The Illusionist is voted out on day 2; on night 2 the Necromancer (player_9) kills through
    its body and the Investigator checks it: Suspicious. A wolf, or the Necromancer that killed through
    a body; the Illusionist is revealed, so the Chanteuse or the Necromancer (never "a wolf")."""
    table = Table(_ne_sp()).night(1, ("player_7", "kill", "player_3"), ("player_7", "block", "player_5"),
                                  ("player_6", "protect", "player_1"))
    table.lynch("player_8", 2)
    table.night(2, ("player_7", "kill", "player_5"), ("player_9", "kill", "player_6", "player_8"),
                ("player_1", "investigate", "player_9"))
    check = _said(3, "player_1", (2, "investigate", "player_9", "suspicious", []), claim="investigator")
    assert _lines(table, "player_2", 3, check) == [
        "If player_1's check is true, player_9 can only be the Chanteuse or the Necromancer."]


def test_on_a_vote_turn_a_wolf_line_reads_as_its_plain_contrapositive():
    check = _said(2, "player_1", (1, "investigate", "player_7", "suspicious", []), claim="investigator")
    items = conditional_items(_view(_checked(), "player_2", 2, check))
    assert [item.text for item in for_turn(items, vote=True)] == [
        "For player_7 not to be a wolf, player_1's check must be false."]
    assert [item.text for item in for_turn(items, vote=False)] == ["If player_1's check is true, player_7 is a wolf."]


# --- the visit rules on the real engine: the immune target, the Chanteuse's two visits --------------------

def _vigilante_at_the_killers_door() -> Table:
    """SK+SP. By night 3 the Trailseer, the Sigilist, both wolves and the Speculator are revealed. On
    night 3 the Serial Killer (player_9) attacks player_2 and the Healer saves it, the Vigilante
    (player_4) shoots player_9 (immune, in silence), and the Sentinel (player_2) watches player_9."""
    table = Table(_sk_sp())
    table.night(1, ("player_7", "kill", "player_3"), ("player_7", "block", "player_5"), ("player_9", "kill", "player_5"),
                ("player_6", "protect", "player_1"))
    table.lynch("player_7", 2)
    table.night(2, ("player_8", "kill", "player_10"), ("player_9", "kill", "player_1"), ("player_6", "protect", "player_1"))
    table.lynch("player_8", 3)
    table.night(3, ("player_9", "kill", "player_2"), ("player_6", "protect", "player_2"), ("player_4", "kill", "player_9"),
                ("player_2", "watch", "player_9"))
    return table


def test_a_visitor_to_a_player_who_could_be_immune_can_be_the_vigilante():
    """Only the Vigilante could have come to player_9: the Serial Killer's and the Healer's visits that
    night went to player_2, and a shot at player_9 is silent if player_9 is the Serial Killer."""
    watch = _said(4, "player_2", (3, "watch", "player_9", "not_said", ["player_4"]), claim="sentinel")
    assert _lines(_vigilante_at_the_killers_door(), "player_1", 4, watch) == [
        "If player_2's watch is true, player_4 is the Vigilante: no other role still in play could have come to "
        "player_9 on night 3.",
        "For player_4 not to be the Vigilante, player_2's watch must be false.",
        "player_4 can be the Serial Killer only if player_2's watch is false.",
    ]


def test_a_visit_no_role_in_play_could_have_made_gives_no_line():
    """The same visitor at the seat's own door: the seat is not immune, so a shot would have been
    announced, and no role in play could have come. The premise cannot hold: no line."""
    watch = _said(4, "player_2", (3, "watch", "player_1", "not_said", ["player_4"]), claim="sentinel")
    assert _lines(_vigilante_at_the_killers_door(), "player_1", 4, watch) == []


def _two_doors() -> Table:
    """The Chanteuse (player_7) carries the kill on player_10 and blocks player_6; the Sentinel
    (player_2) watches player_10 and sees her; the Trailseer (player_3) follows her."""
    return Table(_sk_sp()).night(1, ("player_7", "kill", "player_10"), ("player_7", "block", "player_6"),
                                 ("player_9", "kill", "player_5"), ("player_2", "watch", "player_10"),
                                 ("player_3", "follow", "player_7"), ("player_6", "protect", "player_1"))


def test_two_visits_on_one_night_are_the_chanteuses():
    """The seat's own watch saw player_7 at player_10's door; player_3's follow puts player_7 at player_6's
    too. Only the Chanteuse carrying the kill visits two players, and the pack's kill on player_10 does
    not place her block."""
    follow = _said(2, "player_3", (1, "follow", "player_7", "not_said", ["player_6"]), claim="trailseer")
    assert _lines(_two_doors(), "player_2", 2, follow) == [
        "If player_3's follow is true, the Chanteuse is player_7.",
        "For player_7 not to be the Chanteuse, player_3's follow must be false.",
    ]
    assert _lines(_two_doors(), "player_1", 2, follow) == []  # one visit known: anyone could have made it


# --- where nothing may be said ---------------------------------------------------------------------------

def test_two_claims_for_one_role_cannot_all_be_true_so_no_role_claims_line():
    claims = [_said(3, "player_2", claim="sentinel"), _said(3, "player_4", claim="sigilist", seq=1),
              _said(3, "player_8", claim="healer", seq=2), _said(3, "player_6", claim="healer", seq=3)]
    assert _lines(_ac2(), "player_5", 3, *claims) == []


def test_a_withdrawn_role_claim_is_not_among_the_current_role_claims():
    """player_6 claimed the Healer yesterday and withdrew it: the role claims are player_2's, player_4's and
    player_8's, as in AC2."""
    withdrawn = DaySummary(day=2, summary="(day 2)", structured={"role_claims": [
        {"player": "player_6", "claimed_role": "healer", "kind": "claimed"},
        {"player": "player_6", "claimed_role": "healer", "kind": "retracted"}]})
    claims = [_said(3, "player_2", claim="sentinel"), _said(3, "player_4", claim="sigilist", seq=1),
              _said(3, "player_8", claim="healer", seq=2)]
    items = conditional_items(_view(_ac2(), "player_5", 3, *claims, summaries=[withdrawn]))
    assert [item.text for item in items] == [AC2_LINE_6]
    assert {fact.player for fact in items[0].premises} == {"player_2", "player_4", "player_8"}


def test_a_role_claim_the_seat_can_check_is_left_out_and_named_as_such():
    """player_10 claims the Investigator, the seat's own role: the seat knows it is false, so the line
    assumes only the claims it cannot check."""
    claims = [_said(3, "player_2", claim="sentinel"), _said(3, "player_4", claim="sigilist", seq=1),
              _said(3, "player_8", claim="healer", seq=2), _said(3, "player_10", claim="investigator", seq=3)]
    assert _lines(_ac2(), "player_5", 3, *claims) == [
        "If every role claim you cannot check is true, the Serial Killer is player_6 or player_10."]


def test_a_visit_to_a_player_already_dead_or_by_the_seat_unrecorded_gives_no_line():
    dead = _said(3, "player_2", (2, "watch", "player_1", "not_said", ["player_8"]), claim="sentinel")
    assert _lines(_ac2(), "player_5", 3, dead) == []
    # player_6 says it watched player_4 on night 2 and saw the seat, who was roleblocked that night.
    seat = _said(3, "player_6", (2, "watch", "player_4", "not_said", ["player_5", "player_8"]), claim="sentinel")
    assert _lines(_ac2(), "player_5", 3, seat) == []


def test_a_visit_by_a_wolf_seat_its_role_could_not_have_made_gives_no_line():
    """A wolf's carrier visit is not in its records, but the Illusionist goes only to the pack's victim:
    on night 1 the pack's silent attack went to the immune Necromancer, not to player_1."""
    table = Table(_ne_sp()).night(1, ("player_7", "kill", "player_9"), ("player_7", "block", "player_3"))
    table.night(2, ("player_7", "kill", "player_1"))
    seen = _said(3, "player_2", (1, "watch", "player_1", "not_said", ["player_8", "player_5"]), claim="sentinel")
    assert _lines(table, "player_8", 3, seen) == []


# --- AC4 constructed, and the acceptance cases on their frozen payloads -------------------------------------

def test_the_one_role_claim_left_is_named_ac4_constructed():
    assert _lines(_ac4(), "player_2", 5, _said(5, "player_9", claim="sentinel")) == [AC4_LINE_4]


FROZEN = Path("evidence/reasoning_failures/data/haiku_effort_replay/vote_cases.jsonl")


def _frozen(case_id: str) -> dict:
    from evaluation.src.replay.hallucination_bench import turn_payload

    for line in FROZEN.read_text().splitlines():
        case = json.loads(line)
        if case["case_id"] == case_id:
            return turn_payload(case)
    raise KeyError(case_id)


def _seat_lines(payload: dict) -> list[str]:
    block = build_agent_prompt_input(payload)["deduction_seat_before_note"].strip()
    return [line.removeprefix("- ") for line in block.splitlines()[2:]]


def test_acceptance_case_2_lines_4_5_and_6_exactly_from_the_summary():
    """AC2 (2f19d908, the day-3 vote, player_5 the Investigator): the claims are in the day-3 summary."""
    payload = _frozen("9b827b695a61ece9")
    assert payload["vote_turn"] is True
    items = conditional_items(seat_view_from_payload(payload))
    assert [item.text for item in items] == [AC2_LINE_6, AC2_LINE_4, AC2_LINE_5, AC2_VOTE]


def test_acceptance_case_2_folded_on_its_vote_turn_and_line_4_on_any_other():
    """The vote turn shows "AC2 folded"'s form in player_8's entry; any other turn, line 4. Line 6 is the
    shared line after the census, both ways. Never "player_8 is the Healer" without the premise."""
    payload = _frozen("9b827b695a61ece9")
    lines = _seat_lines(payload)
    # Slice 11: player_8's entry goes on with the comparison of player_2's sighting and player_8's word (E1).
    assert lines[1] == AC2_LINE_6 and any(line.startswith(AC2_VOTE) for line in lines)
    assert not any(AC2_LINE_4 in line or AC2_LINE_5 in line for line in lines)
    other = _seat_lines({**payload, "vote_turn": False})
    assert other[1] == AC2_LINE_6 and any(line.startswith(AC2_LINE_4) for line in other)
    assert not any(AC2_VOTE in line or AC2_LINE_5 in line for line in other)
    for line in lines + other:
        assert "player_8 is the Healer" not in line or line.startswith(AC2_LINE_4)


def test_acceptance_case_4_line_4_exactly_from_the_summary_and_singles_out_none_of_the_three():
    payload = _frozen("5b11c9fd2f6b9b0e")
    items = conditional_items(seat_view_from_payload(payload))
    assert [(item.row, item.subject, item.text) for item in items] == [("F5", None, AC4_LINE_4)]
    assert _seat_lines(payload)[2] == AC4_LINE_4


# --- placement ------------------------------------------------------------------------------------------

def test_a_role_claims_line_is_shared_and_a_players_line_is_in_its_entry():
    view = _view(_ac2(), "player_5", 3, *_ac2_claims())
    blocks = deduction_blocks(view, own_result_lines(view), _ac2_claims(), 3)
    lines = [line.removeprefix("- ") for line in blocks.seat.text.splitlines()[2:]]
    assert lines[:2] == [
        "Both wolves are dead: player_9 and player_7. The Serial Killer is alive and is one of player_2, player_4, "
        "player_6, player_8 and player_10.",
        AC2_LINE_6,
    ]
    assert any(line.startswith(AC2_LINE_4) for line in lines)
    assert not any(AC2_LINE_5 in line or AC2_VOTE in line for line in lines)
    vote = deduction_blocks(view, own_result_lines(view), _ac2_claims(), 3, vote=True)
    assert AC2_VOTE in vote.seat.text and AC2_LINE_4 not in vote.seat.text
    assert not [item for item in blocks.public.shown if item.row in ("F4", "F5", "F6")]


# --- the leak boundary ----------------------------------------------------------------------------------

def test_hidden_roles_and_planted_state_change_nothing():
    swapped = _ac2(serial_killer="player_10", speculator="player_6")
    assert (conditional_items(_view(swapped, "player_5", 3, *_ac2_claims()))
            == conditional_items(_view(_ac2(), "player_5", 3, *_ac2_claims())))
    table = _ac2()
    payload = {**table.payload("player_5"), "day_channel": _ac2_claims(), "current_day": 3}
    planted = {**payload, "roles": table.roles, "all_night_actions": table.records, "night_choices": ["anything"]}
    assert conditional_items(seat_view_from_payload(planted)) == conditional_items(seat_view_from_payload(payload))


# --- the oracles ----------------------------------------------------------------------------------------

def _holds_in_every_deal(fact, support: dict[str, set[str]]) -> bool:
    if isinstance(fact, RoleIn):
        return support[fact.player] <= fact.roles
    if isinstance(fact, HeldBy):
        return all(role != fact.role or player in fact.players for player, roles in support.items() for role in roles)
    raise TypeError(fact)


def _brute_force(items, record, view: SeatView, true_roles: dict[str, str] | None = None) -> int:
    """Every role fact of every line, in every deal the view and the line's premise allow."""
    engine = [(visit.visitor, visit.target, visit.night) for visit in known_visits(view, public_record(view))]
    checked = 0
    for item in items:
        oracle = oracle_of(record, view)
        add_premise(oracle, item.premises, item.night, record,
                    [(visitor, target) for visitor, target, night in engine if night == item.night])
        support, deals = oracle.support()
        assert deals >= 1, item.text
        if true_roles is not None and all(_premise_true(fact, true_roles) for fact in item.premises):
            assert oracle.allows(true_roles), item.text
        for fact in item.conclusion:
            assert _holds_in_every_deal(fact, support), (item.text, fact, support)
        checked += 1
    return checked


def _premise_true(fact, roles: dict[str, str]) -> bool:
    return not isinstance(fact, RoleIn) or roles[fact.player] in fact.roles


def test_the_brute_force_oracle_on_the_constructed_lines():
    cases = [
        (_ac2(), "player_5", 3, _ac2_claims()),
        (_checked(), "player_2", 2, [_said(2, "player_1", (1, "investigate", "player_7", "suspicious", []),
                                           claim="investigator")]),
        (_vigilante_at_the_killers_door(), "player_1", 4,
         [_said(4, "player_2", (3, "watch", "player_9", "not_said", ["player_4"]), claim="sentinel")]),
        (_two_doors(), "player_2", 2, [_said(2, "player_3", (1, "follow", "player_7", "not_said", ["player_6"]),
                                              claim="trailseer")]),
        (_ac4(), "player_2", 5, [_said(5, "player_9", claim="sentinel")]),
    ]
    for table, seat, day, lines in cases:
        view = _view(table, seat, day, *lines)
        items = conditional_items(view)
        assert items
        assert _brute_force(items, table.public(), view, table.roles) == len(items)


FORMS = {
    "F4": r"^If (the current role claims are|every role claim you cannot check is) true",
    "F5 one role claim": r"^If player_\d+'s claim is true",
    "F5 a visit pins its visitor": r"no other role still in play could have come to",
    "F5 is a wolf": r"^If .* player_\d+ is a wolf\.$",
    "F5 a list": r"can only be",
    "F6 plain": r"^For player_\d+ not to be",
    "F6 vote": r"^player_\d+ can be .* only if",
}
"""The forms the random games must reach."""


def truth_oracle(nights: int, seed: int, seats_per_point: int = 2) -> dict[str, int]:
    """Random legal games with true and false claims (night actions, role claims, withdrawals), until
    `nights` nights: whenever a line's premise holds in the real game, so does its conclusion; and a
    role claims line assumes exactly the current, not withdrawn, role claims (of players whose role
    the seat does not know). Returns how often each form fired and how the premises fell."""
    rng = random.Random(seed)
    played = 0
    counts: dict[str, int] = {}
    while played < nights:
        game = random_game(rng)
        played += len(game.nights)
        for snapshot in game.snapshots:
            if _game_over(game.roles, snapshot.dead_roster) or not snapshot.announcements:
                continue
            lines, today = random_claims(rng, game, snapshot)
            roles_said, summaries, current = random_role_claims(rng, game, snapshot, today)
            current = _with_implied(current, lines + roles_said, summaries)
            for player in rng.sample(snapshot.living, min(seats_per_point, len(snapshot.living))):
                payload = {**game.payload_of(player, snapshot), "day_channel": lines + roles_said,
                           "day_summaries": summaries, "current_day": today}
                for item in conditional_items(seat_view_from_payload(payload)):
                    _check(item, game, current, counts)
    return counts


_IMPLIES = {"investigate": "investigator", "protect": "healer", "watch": "sentinel", "follow": "trailseer",
            "shoot": "vigilante", "sigil": "sigilist", "block": "chanteuse"}
_KEPT_IMPLIES = {"held_fire": "vigilante", "kept_check": "investigator", "kept_watch": "sentinel", "kept_sigil": "sigilist"}


def _with_implied(current: dict[str, str], lines, summaries) -> dict[str, str]:
    """The oracle's own account of the current role claims, with the implied ones (owner, 2026-10-18):
    a player with no current role claim whose latest claimed actions all name one role it has not
    withdrawn ("I held fire": the Vigilante). Read off the claim ledger's fold, with its own table."""
    from Agents.rules.claim_ledger import build_claim_ledger

    out = dict(current)
    for player, p in build_claim_ledger([s for s in summaries if s.source != "game_master"], lines).items():
        if player in out or p.current_role is not None:
            continue
        latest = [a for claim in p.actions.values() for a in (claim, *claim.also_claims)]
        named = {_KEPT_IMPLIES.get(a.result) if a.action == "no_action" else _IMPLIES.get(a.action) for a in latest}
        named.discard(None)
        withdrawn = {role for _, role, kind in p.roles if kind == "retracted"}
        if len(named) == 1 and not named & withdrawn:
            out[player] = named.pop()
    return out


def _check(item, game, current: dict[str, str], counts: dict[str, int]) -> None:
    for name, pattern in FORMS.items():
        if re.search(pattern, item.text):
            counts[name] = counts.get(name, 0) + 1
    assert item.grade == "follows_if_claims" and item.premises
    if item.row == "F4" or re.search(FORMS["F5 one role claim"], item.text):
        for fact in item.premises:
            assert isinstance(fact, RoleIn) and current.get(fact.player) in fact.roles, (item.text, fact, current)
    if not all(public_fact_holds(fact, item.night, game) for fact in item.premises):
        counts["premise false"] = counts.get("premise false", 0) + 1
        return
    counts["premise true"] = counts.get("premise true", 0) + 1
    for fact in item.conclusion:
        assert public_fact_holds(fact, item.night, game), (item.text, fact, game.roles)


def test_the_truth_oracle_on_random_games_with_true_and_false_claims():
    counts = truth_oracle(nights=4000, seed=20261022)
    assert set(FORMS) <= set(counts), counts
    assert counts["premise true"] > 1000 and counts["premise false"] > 100, counts


def test_a_seats_conditionals_on_random_games_do_not_change_with_planted_state():
    rng = random.Random(20261023)
    for game, snapshot in _continuing_snapshots(rng, 40):
        if not snapshot.announcements:
            continue
        lines, today = random_claims(rng, game, snapshot)
        roles_said, summaries, _ = random_role_claims(rng, game, snapshot, today)
        for player in snapshot.living:
            payload = {**game.payload_of(player, snapshot), "day_channel": lines + roles_said,
                       "day_summaries": summaries, "current_day": today}
            planted = {**payload, "roles": game.roles, "all_night_actions": game.records}
            assert conditional_items(seat_view_from_payload(planted)) == conditional_items(seat_view_from_payload(payload))


def test_the_brute_force_oracle_on_random_games():
    """Every line of a random game's view, in every deal the view and its premise allow; the true deal
    is among them whenever the premise's roles are true."""
    rng = random.Random(20261024)
    checked = 0
    for game, snapshot in _continuing_snapshots(rng, 120):
        if not snapshot.announcements:
            continue
        lines, today = random_claims(rng, game, snapshot)
        roles_said, summaries, _ = random_role_claims(rng, game, snapshot, today)
        player = rng.choice(snapshot.living)
        view = seat_view_from_payload({**game.payload_of(player, snapshot), "day_channel": lines + roles_said,
                                       "day_summaries": summaries, "current_day": today})
        items = conditional_items(view)
        checked += _brute_force(items, snapshot, view)
    assert checked >= 100, checked
