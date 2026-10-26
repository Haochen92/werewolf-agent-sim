"""Slice 8: the deduction blocks (Agents/deduction/render.py, blocks.py, raised.py; catalogue
"Rendering: what the seat reads" of evidence/gameplay/deduction/deduction_catalogue.md).

- The fold rules, one at a time, on constructed items and on constructed nights through the real
  engine (the Illusionist's A45 beside the pack's A13 or A11 on the same target).
- "Raised today", from the transcript alone.
- Placement: the public block before the cache boundary and the same for every seat, in a whole game
  on the real graph; the seat block after it, always before the strategy note (since 2026-10-24); the
  modes "off" and "record" and a human seat get no block.
- The log: every shown line's derivation goes with the prompt capture, never into the text.
- The acceptance cases AC2 and AC4, on their own frozen payloads: the exact blocks, the census and
  level-1 lines the cases list, and nothing from their "must not say" lists.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from Agents.deduction import (
    deduction_blocks,
    deduction_log,
    fold_own_lines,
    own_result_lines,
    seat_view_from_payload,
)
from Agents.deduction.candidates import public_candidate_items, seat_candidate_items
from Agents.deduction.raised import raised_today
from Agents.deduction.render import (
    PUBLIC_HEADING,
    SEAT_HEADING,
    render_public,
    render_seat,
)
from Agents.prompts.prompt_formatters import format_night_actions
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.schemas.deduction import (
    AttackOutcome,
    DeductionItem,
    HeldBy,
    NoConcealsLeft,
    NotProtected,
    OwnResultLine,
    ProtectedBy,
    RenderedBlock,
    RoleIn,
    Source,
)
from Agents.schemas.game_events import DayChannel
from tests.engine.deduction.test_candidates import Table, _sk_sp

LIVING = ["player_2", "player_4", "player_6"]
DEAD = ["player_9", "player_1"]


def _item(row: str, subject: str | None, text: str, *facts, night: int = 1, premises=(), receiver=None,
          sources=()) -> DeductionItem:
    return DeductionItem(row=row, subject=subject, night=night, conclusion=tuple(facts), text=text,
                         premises=tuple(premises), sources=tuple(sources), receiver=receiver)


def _lines(block: RenderedBlock) -> list[str]:
    return [line.removeprefix("- ") for line in block.text.splitlines()[2:]]


# --- rule 3: one proposition, once ---------------------------------------------------------------

def test_the_same_proposition_under_the_same_premises_is_shown_once_compared_as_facts_not_text():
    one = _item("F7", "player_4", "player_4 can only be the Healer or the Sentinel.",
                RoleIn("player_4", frozenset({"healer", "sentinel"})))
    reworded = _item("B11", "player_4", "Worded differently.", RoleIn("player_4", frozenset({"healer", "sentinel"})),
                     night=2)
    assert render_public([one, reworded], LIVING, DEAD).shown == (one,)  # a role holds on every night


def test_a_census_line_naming_one_holder_is_the_same_proposition_as_that_players_role():
    census = _item("F3", None, "The Fortune Teller is alive and is player_6.",
                   HeldBy("fortune_teller", ("player_6",)))
    pinned = _item("F7", "player_6", "player_6 is the Fortune Teller.", RoleIn("player_6", frozenset({"fortune_teller"})))
    assert render_public([census, pinned], LIVING, DEAD).shown == (census,)


def test_lines_that_sound_alike_but_state_different_facts_both_stay():
    one = _item("F7", "player_4", "player_4 can only be the Healer or the Sentinel.",
                RoleIn("player_4", frozenset({"healer", "sentinel"})))
    same_text = _item("F7", "player_6", "player_4 can only be the Healer or the Sentinel.",
                      RoleIn("player_6", frozenset({"healer", "sentinel"})))
    assert len(render_public([one, same_text], LIVING, DEAD).shown) == 2


def test_a_premise_keeps_a_line_apart_from_the_same_conclusion_without_it():
    plain = _item("F7", "player_4", "player_4 is the Healer.", RoleIn("player_4", frozenset({"healer"})))
    assumed = _item("F5", "player_4", "If player_2's watch is true, player_4 is the Healer.",
                    RoleIn("player_4", frozenset({"healer"})), premises=[NotProtected("player_9")])
    assert render_public([plain, assumed], LIVING, DEAD).shown == (plain, assumed)


def test_a_fact_about_a_night_is_not_the_same_fact_on_another_night():
    first = _item("F7", "player_4", "Night 1.", AttackOutcome("player_4", frozenset()), night=1)
    second = _item("F7", "player_4", "Night 2.", AttackOutcome("player_4", frozenset()), night=2)
    assert len(render_public([first, second], LIVING, DEAD).shown) == 2


def test_the_seat_block_leaves_out_what_the_public_block_or_its_own_record_lines_already_state():
    census = HeldBy("serial_killer", ("player_2", "player_4"))
    public = render_public([_item("F3", None, "The public census.", census)], LIVING, DEAD)
    seat_census = _item("F3", None, "The seat's census.", census, receiver="player_6")
    pinned = _item("F7", "player_4", "player_4 is the Serial Killer.",
                   RoleIn("player_4", frozenset({"serial_killer"})), receiver="player_6")
    own = [(1, OwnResultLine(text="Only the Serial Killer could survive that attack, so player_4 is the Serial Killer.",
                             row="A13", facts=(AttackOutcome("player_4", frozenset({"serial_killer"})),
                                               RoleIn("player_4", frozenset({"serial_killer"})))))]
    seat = render_seat([seat_census, pinned], [], frozenset(), LIVING, DEAD, public, own)
    assert seat.shown == () and seat.text == ""


def test_the_illusionist_reads_the_pack_targets_immunity_once():
    """The pack attacked the Serial Killer and the conceal found no body: A13 on the pack's record
    and A45 on the conceal state the same facts. The first stays; the conceal keeps its own prose."""
    table = Table(_sk_sp()).night(1, ("player_7", "kill", "player_9"), ("player_8", "conceal", None),
                                  ("player_9", "kill", "player_1"), ("player_6", "protect", "player_2"))
    view = table.seat("player_8")
    lines = own_result_lines(view)
    assert [line.row for line in lines] == ["A13", "A45"]
    folded = fold_own_lines(view.night_records, lines)
    assert [line and line.row for line in folded] == ["A13", None]
    assert format_night_actions(view.night_records, 2, folded).splitlines()[1] == (
        "Night 1 (last night): The pack's victim did not die, so no body was concealed.")


def test_the_illusionist_reads_the_save_of_the_pack_target_once():
    """The Healer saved the pack's target: A45's protection is one of the facts of the pack record's
    A11, so A45 goes and A11 stays whole."""
    table = Table(_sk_sp()).night(1, ("player_7", "kill", "player_2"), ("player_8", "conceal", None),
                                  ("player_9", "kill", "player_1"), ("player_6", "protect", "player_2"))
    view = table.seat("player_8")
    lines = own_result_lines(view)
    assert [line.row for line in lines] == ["A11", "A45"]
    assert ProtectedBy("player_2", through_body=False) in lines[0].facts
    assert [line and line.row for line in fold_own_lines(view.night_records, lines)] == ["A11", None]


def test_a_roleblock_line_which_stands_in_for_its_record_is_never_folded():
    blocked = OwnResultLine(text="You were roleblocked.", row="A6", replaces_outcome=True,
                            facts=(NotProtected("player_2"),))
    wider = OwnResultLine(text="Wider.", row="A1", facts=(NotProtected("player_2"), NoConcealsLeft()))
    records = Table(_sk_sp()).night(1, ("player_7", "kill", "player_2"), ("player_6", "protect", "player_2"),
                                    ("player_9", "kill", "player_1")).seat("player_6").night_records
    record = records[0]
    assert fold_own_lines([record, record], [blocked, wider]) == [blocked, wider]


# --- the census: nothing that names every unknown player, nothing the public block has ------------

def test_a_census_clause_naming_every_unknown_player_is_left_out():
    """Day 1, no one dead: "Both wolves are alive and are two of" everyone says nothing (rule 1),
    in the public's view and in a seat's; the full items are still computed."""
    table = Table(_sk_sp())
    assert public_candidate_items(table.public(), informative=True) == []
    assert seat_candidate_items(table.seat("player_1"), informative=True) == []
    assert [item.row for item in public_candidate_items(table.public())] == ["F3", "F3"]


def test_a_list_that_leaves_out_one_unknown_player_or_a_hidden_body_stays():
    """The pack killed player_2 under the living conceal: its body is neither a wolf nor the Serial
    Killer (L8), so those clauses narrow and stay; the Speculator's, which names every living player
    and the body, goes."""
    table = Table(_sk_sp()).night(1, ("player_7", "kill", "player_2"), ("player_8", "conceal", None),
                                  ("player_9", "kill", "player_1"))
    living = "player_3, player_4, player_5, player_6, player_7, player_8, player_9 and player_10"
    texts = [item.text for item in public_candidate_items(table.public(), informative=True) if item.row == "F3"]
    assert texts == [f"Both wolves are alive and are two of {living}. The Serial Killer is alive and is one of {living}."]


def test_the_census_is_the_seats_alone_and_an_f7_line_that_is_the_publics_less_the_seat_is_left_out():
    """The pack's attack on player_3 was saved; the Investigator's private check reads player_2 Not
    suspicious. The census is in the seat block only, with the seat left out: the wolves' clause
    narrows (player_3 attacked, player_2 checked), and so does the Serial Killer's (player_3 was
    saved); the Speculator's names every unknown player and goes. The Healer's F7 line on player_3 is the public's less the
    Healer, so only the public block has it."""
    table = Table(_sk_sp()).night(1, ("player_7", "kill", "player_3"), ("player_6", "protect", "player_3"),
                                  ("player_9", "kill", "player_5"), ("player_1", "investigate", "player_2"))
    view = table.seat("player_1")
    blocks = deduction_blocks(view, own_result_lines(view), [], 2)
    assert [item.row for item in blocks.public.shown] == ["F7"]
    assert [item.text for item in blocks.seat.shown if item.row == "F3"] == [
        "Both wolves are alive and are two of player_4, player_6, player_7, player_8, player_9 and player_10. "
        "The Serial Killer is alive and is one of player_2, player_4, player_6, player_7, player_8, player_9 and "
        "player_10."]
    healer = table.seat("player_6")
    assert [item.row for item in seat_candidate_items(healer, informative=True)] == ["F3"]


# --- rule 4: the order of the block ---------------------------------------------------------------

def test_shared_lines_first_then_the_living_in_seat_order_then_the_dead_in_death_order():
    items = [
        _item("F7", "player_1", "Dead one.", RoleIn("player_1", frozenset({"healer", "sentinel"}))),
        _item("F7", "player_6", "Six.", RoleIn("player_6", frozenset({"healer", "sentinel"}))),
        _item("F3", None, "Census.", HeldBy("serial_killer", ("player_2", "player_6"))),
        _item("F7", "player_2", "Two.", RoleIn("player_2", frozenset({"healer", "sentinel"}))),
        _item("B6", "player_9", "Dead nine.", NoConcealsLeft()),
    ]
    assert _lines(render_public(items, LIVING, DEAD)) == ["Census.", "Two.", "Six.", "Dead nine.", "Dead one."]


def test_an_entry_is_a_conclusion_and_two_supporting_sentences_then_a_second_entry():
    raised = frozenset({("player_4", 1)})
    steps = [_item("B1", "player_4", f"Step {n}.", NotProtected(f"player_{n}")) for n in range(1, 5)]
    pinned = _item("F7", "player_4", "player_4 can only be the Healer or the Sentinel.",
                   RoleIn("player_4", frozenset({"healer", "sentinel"})), receiver="player_6")
    seat = render_seat([pinned], steps, raised, LIVING, DEAD, RenderedBlock(""), [])
    assert _lines(seat) == ["player_4 can only be the Healer or the Sentinel. Step 1. Step 2.", "Step 3. Step 4."]


def test_a_block_with_nothing_to_show_is_empty():
    assert render_public([], LIVING, DEAD) == RenderedBlock("")


# --- rule 5: working steps only when raised today --------------------------------------------------

def _said(player: str, message: str, day: int = 3, **kw) -> DayChannel:
    return DayChannel(day=day, seq=0, player=player, message=message, **kw)


def test_raised_today_is_a_player_and_a_night_named_in_one_message_spoken_today():
    channel = [
        _said("player_2", "On night 2 I watched player_5 and saw player_7."),
        _said("player_4", "player_8, what did you do last night?"),
        _said("player_6", "Night one: player_3 was quiet."),
        _said("player_6", "player_10 and night 1 were yesterday.", day=2),
        _said("game_master", "Night 1: player_1 died."),
        _said("player_9", "", passed=True),
        _said("player_10", "player_1 is odd."),
    ]
    assert raised_today(channel, 3) == {("player_5", 2), ("player_7", 2), ("player_8", 2), ("player_3", 1)}
    assert raised_today(channel, 1) == frozenset()


def test_a_working_step_is_never_in_the_public_block_and_in_the_seat_block_only_when_raised():
    step = _item("B1", "player_4", "A wolf went to player_4 on night 1.", NotProtected("player_4"),
                 sources=[Source("announcement", 1, "player_4")])
    will = _item("B19+A26", "player_6", "player_9's will shows that on night 1 player_9 watched player_6.",
                 NotProtected("player_6"), sources=[Source("will", 1, "player_9")])
    assert render_public([step, will], LIVING, DEAD).shown == ()
    assert render_seat([], [step, will], frozenset(), LIVING, DEAD, RenderedBlock(""), []).shown == ()
    raised = frozenset({("player_4", 1), ("player_9", 1)})  # the will's holder raises its night too
    assert render_seat([], [step, will], raised, LIVING, DEAD, RenderedBlock(""), []).shown == (step, will)
    assert render_seat([], [step], frozenset({("player_4", 2)}), LIVING, DEAD, RenderedBlock(""), []).shown == ()


# --- placement: where each block sits in every turn kind ----------------------------------------------

def _rendered(template, inputs: dict) -> str:
    values = {v: inputs.get(v, f"<{v}>") for v in template.input_variables}
    return template.invoke(values).to_messages()[1].content


def _templates(role: str) -> dict:
    from Agents.prompts.day_discuss import day_discuss_template
    from Agents.prompts.day_vote import day_vote_template
    from Agents.prompts.night import carrier_template, night_template, wolf_chat_template

    out = {"discuss": day_discuss_template(role), "vote": day_vote_template(role)}
    if role in ("chanteuse", "illusionist"):
        out |= {"wolf_chat": wolf_chat_template(role), "carrier": carrier_template(role)}
    out["night"] = night_template(role)
    return out


@pytest.mark.parametrize("role", ["healer", "illusionist"])
def test_the_public_block_is_before_the_boundary_and_the_seat_block_after_it_before_the_note(role):
    """On AC2's frozen turn (both blocks have lines), rendered through every turn kind's template."""
    from Agents.llm_factory.providers.common import TRANSCRIPT_RULE

    inputs = build_agent_prompt_input(_frozen("9b827b695a61ece9"))
    for kind, template in _templates(role).items():
        text = _rendered(template, inputs)
        boundary = TRANSCRIPT_RULE.search(text).start()
        public, seat = text.index(PUBLIC_HEADING), text.index(SEAT_HEADING)
        note = text.index("Adaptive Strategic thinking:")
        assert public < boundary < seat, kind
        assert text.count(PUBLIC_HEADING) == 1 and text.count(SEAT_HEADING) == 1, kind
        assert seat < note, kind


def test_level_two_keeps_the_record_and_leaves_out_every_claim_line():
    """Mode "public" (difficulty level 2): the same public block, and a seat block of only the census
    and the seat's candidate roles: no line from the claims (the status, joins, conditionals, Table E)."""
    from Agents.schemas.game_events import DayChannel
    from tests.fixtures.day_discuss_prompt_golden import speaker_payload

    payload = speaker_payload("healer")
    day = payload["current_day"]
    claims = [DayChannel(day=day, seq=k, player=p, message="(a role)", claim="investigator")
              for k, p in enumerate(("player_1", "player_2"))]
    payload = {**payload, "day_channel": [*payload.get("day_channel", []), *claims]}
    full = build_agent_prompt_input({**payload, "deduction_mode": "full"})
    public = build_agent_prompt_input({**payload, "deduction_mode": "public"})
    assert "both claim the Investigator" in full["deduction_seat_before_note"]
    assert public["deduction_public_block"] == full["deduction_public_block"]
    assert {entry["row"] for entry in public["deduction_log"] if entry["block"] == "seat"} <= {"F3", "F7"}
    seat = public["deduction_seat_before_note"]
    assert "from the public record and your own night results." in seat and "claim" not in seat


@pytest.mark.parametrize("change", [{"deduction_mode": "off"}, {"deduction_mode": "record"}, {"human_player": True}])
def test_no_block_outside_full_mode_or_for_a_human_seat(change):
    from Agents.prompts.day_discuss import day_discuss_template
    from tests.fixtures.day_discuss_prompt_golden import speaker_payload

    inputs = build_agent_prompt_input({**speaker_payload("healer"), **change})
    assert inputs["deduction_public_block"] == inputs["deduction_seat_before_note"] == ""
    assert inputs["deduction_log"] == []
    text = _rendered(day_discuss_template("healer"), inputs)
    assert PUBLIC_HEADING not in text and SEAT_HEADING not in text


@pytest.mark.parametrize("game", [
    {"lone_killer": "serial_killer", "neutral": "speculator"},
    {"lone_killer": "necromancer", "neutral": "fortune_teller"},
])
def test_in_a_whole_game_every_seat_and_turn_kind_gets_the_same_public_block(monkeypatch, game):
    """On the real graph: every AI turn (discussion, vote, night, the wolf chat and the carrier) with
    the same day and dead roster has byte-identical public blocks; the block grows as the game does."""
    from Agents.turn.eval import TURN_CAPTURE, TurnCapture
    from tests.engine.test_ten_seat_game import _play

    capture = TurnCapture()
    token = TURN_CAPTURE.set(capture)
    try:
        _play(monkeypatch, game, seed=13)  # not 11: test_ten_seat_game plays that game id, and the checkpointer is shared
    finally:
        TURN_CAPTURE.reset(token)
    blocks: dict[tuple, set[str]] = {}
    kinds = set()
    for entry in capture.prompts:
        inputs = entry["prompt_input"]
        blocks.setdefault((entry["day"], inputs["dead_roster"]), set()).add(inputs["deduction_public_block"])
        kinds.add(entry["output_key"])
    assert {"day_channel", "day_votes", "wolf_channel", "kill_target"} <= kinds
    assert all(len(seen) == 1 for seen in blocks.values()), blocks
    # No "the block is non-empty" check here: which path this scripted game takes depends on set order
    # (PYTHONHASHSEED), and on some paths no public line appears. The AC4 golden pins a non-empty block.


# --- the log ---------------------------------------------------------------------------------------

def test_every_shown_line_is_logged_with_its_derivation_and_no_derivation_reaches_the_text():
    view = Table(_sk_sp()).night(1, ("player_7", "kill", "player_2"), ("player_8", "conceal", None),
                                 ("player_9", "kill", "player_1"), ("player_6", "protect", "player_3")).seat("player_6")
    channel = [_said("player_3", "player_1 died on night 1.", day=2)]
    blocks = deduction_blocks(view, own_result_lines(view), channel, 2)
    log = deduction_log(blocks)
    assert [entry["text"] for entry in log] == [item.text for item in blocks.public.shown + blocks.seat.shown]
    assert any(entry["derivation"] for entry in log) and json.loads(json.dumps(log)) == log
    assert {entry["block"] for entry in log} == {"public", "seat"}
    for text in (blocks.public.text, blocks.seat.text):
        assert "derivation" not in text and "night_announcements" not in text


def test_the_prompt_capture_carries_the_log():
    from Agents.turn.eval import TurnCapture, TURN_CAPTURE, log_prompt

    payload = _frozen("9b827b695a61ece9")
    capture = TurnCapture()
    token = TURN_CAPTURE.set(capture)
    try:
        log_prompt(payload, "day_channel", build_agent_prompt_input(payload))
    finally:
        TURN_CAPTURE.reset(token)
    logged = capture.prompts[0]["prompt_input"]["deduction_log"]
    assert logged and {entry["block"] for entry in logged} == {"public", "seat"}


# --- the leak boundary: the public block reads only the public record --------------------------------

def test_the_public_block_does_not_change_with_anything_private():
    table = Table(_sk_sp()).night(1, ("player_7", "kill", "player_2"), ("player_8", "conceal", None),
                                  ("player_9", "kill", "player_1"), ("player_6", "protect", "player_2"),
                                  ("player_1", "investigate", "player_7"))
    texts = set()
    for player in table.living():
        view = table.seat(player)
        texts.add(deduction_blocks(view, own_result_lines(view), [], 2).public.text)
    assert len(texts) == 1 and next(iter(texts))


# --- the acceptance cases, on their own frozen payloads -----------------------------------------------

FROZEN = Path("evidence/gameplay/deduction/data/haiku_effort_replay/vote_cases.jsonl")


def _frozen(case_id: str) -> dict:
    from evaluation.src.replay.hallucination_bench import turn_payload

    for line in FROZEN.read_text().splitlines():
        case = json.loads(line)
        if case["case_id"] == case_id:
            return turn_payload(case)
    raise KeyError(case_id)


AC2_PUBLIC = """\
== Worked out from the public record ==
The game computed these lines from the announcements, the dead roster and the wills. Each line is certain unless it names what it assumes.
- player_1's hidden role can only be the Investigator, the Sentinel, the Vigilante, the Healer or the Speculator."""

AC2_SEAT = """\
== Worked out for you ==
The game computed these lines from the public record, your own night results and what players say they did. Each line is certain unless it names what it assumes.
- Both wolves are dead: player_9 and player_7. The Serial Killer is alive and is one of player_2, player_4, player_6, player_8 and player_10.
- If the current role claims are true, the Serial Killer is player_6 or player_10.
- No one else claims the Investigator, the Sentinel, the Sigilist or the Healer. player_6 and player_10 have made no role claim.
- You were roleblocked on night 2, so the Chanteuse came to you, and player_7 was the Chanteuse. player_2's report that player_7 came to you that night is true. This does not show that player_2 is the Sentinel.
- player_8 can be the Serial Killer only if player_2's watch is false. player_2 says player_8 came to you on night 2, and player_8 says it protected you that night. These agree; the sighting does not show which action player_8 took. player_3's will shows player_7, the Chanteuse, went to player_8 on night 1. The pack's kill that night was on player_1, so that visit was her block on player_8.
- The Sigilist went to player_7 on night 2 to set a sigil on them, and a watch on player_7 that night would have shown that visit. A wolf is struck by a sigil only when it carries the pack's kill, so player_7 carried the pack's kill on night 2. No protection went ahead on player_7 on night 2: one would have saved player_7."""

AC2_LINE_1 = ("Both wolves are dead: player_9 and player_7. The Serial Killer is alive and is one of player_2, "
              "player_4, player_6, player_8 and player_10.")
AC2_LINE_2 = ("You were roleblocked on night 2, so the Chanteuse came to you, and player_7 was the Chanteuse. player_2's "
              "report that player_7 came to you that night is true. This does not show that player_2 is the Sentinel.")


def test_acceptance_case_2_the_blocks_exactly():
    """AC2 (2f19d908, the day-3 vote, player_5 the Investigator). Line 1 (F3) is the seat block's first
    line, exactly: the census is the seat's alone. Its Speculator clause names every unknown player
    and player_1's body, so it is left out. Line 6 (F4, slice 10) is the shared line after it. Line 2
    (F1, slice 9b) is player_2's entry, exactly: the day-3 summary carries player_2's watch. On this
    vote turn lines 4 and 5 (F5, F6) read as "AC2 folded" has them, in player_8's entry
    (test_conditionals.py has them on another turn). Slice 11 adds the role claims' status after line
    6, and, in player_8's entry, that player_2's sighting and player_8's own word agree (E1). Slice 12
    adds line 3 there, ending at the block (no claim of player_8's that it was roleblocked on night 1
    is in the payload: the catalogue's line corrected). Today player_2 named player_7 on night 2,
    which raises the sigil's events."""
    payload = _frozen("9b827b695a61ece9")
    inputs = build_agent_prompt_input(payload)
    assert inputs["deduction_public_block"] == AC2_PUBLIC + "\n\n"
    assert inputs["deduction_seat_before_note"] == "\n" + AC2_SEAT + "\n"
    assert _lines(RenderedBlock(AC2_SEAT))[:4] == [
        AC2_LINE_1, "If the current role claims are true, the Serial Killer is player_6 or player_10.",
        "No one else claims the Investigator, the Sentinel, the Sigilist or the Healer. player_6 and player_10 have "
        "made no role claim.", AC2_LINE_2]
    assert "Both wolves" not in AC2_PUBLIC
    # Level 1, beside the records: the night-2 roleblock (A6) and the night-1 check.
    assert inputs["night_actions"] == (
        "Night 1: you checked player_9. player_9 reads Suspicious. Only a wolf reads Suspicious in this game, "
        "so player_9 is a wolf.\n"
        "Night 2 (last night): You were roleblocked: your check on player_3 did not happen. Only the Chanteuse could "
        "roleblock that night, and a block is a visit, so the Chanteuse, a wolf, came to you that night.")


def test_acceptance_case_2_must_not_say():
    """Not that player_8 is the Healer without the premise (on this vote turn not even with it: the
    line reads as its contrapositive); nothing of player_7's night-1 visit to player_8 but line 3, that
    it was her block (no line about player_8 but the census and its entry, which opens with the
    conditional on player_2's watch)."""
    blocks = AC2_PUBLIC + "\n" + AC2_SEAT
    status = "No one else claims the Investigator, the Sentinel, the Sigilist or the Healer."
    assert "player_8 is" not in blocks
    assert "Healer" not in blocks.replace("the Healer or the Speculator", "").replace(status, "")
    for line in blocks.splitlines():
        if "player_8" in line:
            assert (line.startswith("- Both wolves are dead") or line.startswith("- The Speculator is one of")
                    or line.startswith("- player_8 can be the Serial Killer only if player_2's watch is false."))


AC4_PUBLIC = """\
== Worked out from the public record ==
The game computed these lines from the announcements, the dead roster and the wills. Each line is certain unless it names what it assumes.
- The Speculator picked Town on night 3, so it was alive at the start of that night, and it will not pick again.
- player_8's hidden role can only be the Sentinel, the Trailseer, the Vigilante or the Sigilist.
- player_6 was voted out on day 3 as the Illusionist, so from night 3 on the Necromancer can use player_6's body to attack someone.
- player_5's hidden role can only be the Sentinel, the Trailseer, the Vigilante, the Sigilist or the Speculator.
- player_1 was voted out on day 4 as the Chanteuse, so from night 4 on the Necromancer can use player_1's body to block someone.
- player_7 was killed through the dead Illusionist's body and their role was not hidden, so the Illusionist's conceals are used up: no death will be hidden again."""

AC4_SEAT = """\
== Worked out for you ==
The game computed these lines from the public record, your own night results and what players say they did. Each line is certain unless it names what it assumes.
- Both wolves are dead: player_6 and player_1. The Necromancer is alive and is one of player_3, player_9 and player_10.
- The Speculator is one of player_3, player_9 and player_10, or is player_5's hidden body.
- If player_9's claim is true, the Necromancer is player_3 or player_10.
- No one else claims the Sentinel. player_3 and player_10 have made no role claim.
- player_9 says no one came to player_3 on night 4. That is about who came to player_3, not about whether player_3 acted.
- player_4's will shows player_4 checked player_6 on night 2, so player_4 went to player_6 that night, as player_9's watch reported. This confirms that part of the report, not that player_9 is the Sentinel.
- The Necromancer attacked player_7 on night 4 through player_6's body (the Illusionist): it was alive that night, and a kill through a body makes it read Suspicious that night. It acts once a night, so it did nothing else. No protection went ahead on player_7 on night 4: one would have saved player_7."""

AC4_LINE_1 = ("Both wolves are dead: player_6 and player_1. The Necromancer is alive and is one of player_3, player_9 "
              "and player_10.")
AC4_LINE_2 = ("player_4's will shows player_4 checked player_6 on night 2, so player_4 went to player_6 that night, as "
              "player_9's watch reported. This confirms that part of the report, not that player_9 is the Sentinel.")


AC4_LINE_3 = "No one else claims the Sentinel. player_3 and player_10 have made no role claim."
AC4_LINE_5 = ("player_9 says no one came to player_3 on night 4. That is about who came to player_3, not about whether "
              "player_3 acted.")


def test_acceptance_case_4_the_blocks_exactly():
    """AC4 (403f4dbc, the day-5 vote, player_2 the Vigilante). Line 1 (F3) is the seat block's first
    line, exactly. The seat's F7 lines on player_8 and player_5 are the public's less the Vigilante,
    so only the public block has them. Line 2 (F1 through a will, slice 9b) is player_9's entry, exactly:
    the day-3 summary carries player_9's watch, player_4's will was read out the morning after night 3.
    Line 4 (F5, slice 10) is a shared line after the census. Line 3 (the role claims' status, slice 11)
    is the shared line after it, and line 5 (E17, slice 11) is player_3's entry, exactly."""
    payload = _frozen("5b11c9fd2f6b9b0e")
    inputs = build_agent_prompt_input(payload)
    assert inputs["deduction_public_block"] == AC4_PUBLIC + "\n\n"
    assert inputs["deduction_seat_before_note"] == "\n" + AC4_SEAT + "\n"
    assert _lines(RenderedBlock(AC4_SEAT))[0] == AC4_LINE_1
    assert AC4_LINE_2 in _lines(RenderedBlock(AC4_SEAT))
    assert _lines(RenderedBlock(AC4_SEAT))[3:5] == [AC4_LINE_3, AC4_LINE_5]
    assert "Both wolves" not in AC4_PUBLIC


def test_acceptance_case_4_singles_out_none_of_the_three():
    """Nothing certain separates player_3, player_9 and player_10: they are named together, in the
    census, and fewer only in the case's own lines: line 2, which confirms a visit in player_9's report
    and says that it does not show player_9's role; line 3, the claims' status; line 5, which says
    that player_9's watch says nothing of whether player_3 acted."""
    payload = _frozen("5b11c9fd2f6b9b0e")
    view = seat_view_from_payload(payload)
    blocks = deduction_blocks(view, own_result_lines(view), payload["day_channel"], payload["current_day"])
    for item in blocks.public.shown + blocks.seat.shown:
        assert item.subject != "player_10"
        assert item.subject != "player_3" or (item.row == "E17" and item.text == AC4_LINE_5)
        assert item.subject != "player_9" or (item.row == "F1" and item.text == AC4_LINE_2)
    for line in (AC4_PUBLIC + "\n" + AC4_SEAT).splitlines():
        named = [p for p in ("player_3", "player_9", "player_10") if p in line]
        assert (named in ([], ["player_3", "player_9", "player_10"])
                or line in (f"- {AC4_LINE_2}", f"- {AC4_LINE_3}", f"- {AC4_LINE_5}")), line
