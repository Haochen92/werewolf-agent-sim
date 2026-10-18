"""The four acceptance cases end to end (catalogue "Acceptance cases" and "Build verification" item 4,
evidence/reasoning_failures/deduction_catalogue.md).

Each case's turn is built from its frozen payload exactly as the live pipeline builds it: the engine's
own payload builders (`turn_payload`, the replay bench's), `deduction_mode` "full", placement
"before_note", `build_agent_prompt_input`, and the production template of the turn (discussion or
vote) rendered whole, every message. Then every sentence the case lists is looked for verbatim in
the whole prompt, and where the fold put it is asserted (the record beside the seat's night
actions, the public block, or the seat block), and nothing on the case's "must not say" list is in
the prompt. AC1's and AC3's same-day claims are the hand-filled speaker fields of test_joins.py.

Where a listed sentence does not render verbatim, the test pins what does and why (the catalogue
records each, case by case):
- AC1 line 1: the proposition is the level-1 roleblock line (A6) as built in slice 1, which stands in
  for the record's own sentence; its wording differs from the case's (an owner's ruling).
- AC2 line 3: its last sentence names a claim of player_8's that the frozen payload does not carry
  (player_8 claimed only its night-2 protection), so the line ends at the block.
- AC2 lines 4 and 5: a vote turn reads F5 as its contrapositive's vote form (fold rule 3, "AC2
  folded"); line 4 renders on the same payload as a discussion turn, and line 5 is the F6 item the
  fold replaces.
- AC3 line 1: its first sentence is the record's own prose ("you checked player_6. player_6 reads
  Suspicious."), the A22 line follows it.
"""

from __future__ import annotations

import re

from Agents.deduction import seat_view_from_payload
from Agents.deduction.conditionals import conditional_items
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from tests.engine.deduction.test_joins import _ac1_case, _ac3_case, _case, _payload

AC2_ID, AC4_ID = "9b827b695a61ece9", "5b11c9fd2f6b9b0e"
VOTES = "haiku_effort_replay/vote_cases.jsonl"
PLACES = {"night_actions": "night record", "deduction_public_block": "public block",
          "deduction_seat_before_note": "seat block"}


def _turn(case: dict, **change) -> tuple[str, dict]:
    """The whole prompt of the case's turn, and its inputs, as the live pipeline builds them."""
    from evaluation.src.replay.hallucination_bench import turn_template

    payload = {**_payload(case), "deduction_mode": "full", "deduction_placement": "before_note", **change}
    template, _, _ = turn_template(case, payload)
    inputs = build_agent_prompt_input(payload)
    messages = template.invoke({name: inputs[name] for name in template.input_variables}).to_messages()
    return "\n\n".join(message.content for message in messages), inputs


def _where(sentence: str, prompt: str, inputs: dict) -> str:
    """Where the sentence is: present in the whole prompt, and in which engine-written part."""
    assert sentence in prompt, sentence
    places = [place for key, place in PLACES.items() if sentence in inputs[key]]
    assert len(places) == 1, (sentence, places)
    return places[0]


def _sentences(text: str) -> list[str]:
    return re.split(r"(?<=[.!?])\s+", text)


# --- AC1: 2f19d908, day 2, the Healer (player_8) ----------------------------------------------------

# Owner, 2026-10-18: A6 names the blocked action; the night comes from the record line's own "Night 1".
AC1_LINE_1 = ("Night 1 (last night): You were roleblocked: your protection of player_5 did not happen. Only the "
              "Chanteuse could roleblock that night, and a block is a visit, so the Chanteuse, a wolf, came to you "
              "that night.")
AC1_LINE_2 = ("player_3 says player_7 came to you on night 1, and player_7 agrees. If that is true, either player_7 is "
              "the Chanteuse, or player_7 and the Chanteuse both came to you.")


def test_acceptance_case_1_end_to_end():
    prompt, inputs = _turn(_ac1_case())
    assert _where(AC1_LINE_2, prompt, inputs) == "seat block"
    assert _where(AC1_LINE_1, prompt, inputs) == "night record"
    # Must not say: "player_7 is the Chanteuse", with or without the premise, but inside line 2's list.
    for sentence in _sentences(prompt):
        if "player_7 is the Chanteuse" in sentence:
            assert sentence == ("If that is true, either player_7 is the Chanteuse, or player_7 and the Chanteuse both "
                                "came to you."), sentence


# --- AC2: 2f19d908, the day-3 vote, the Investigator (player_5) -------------------------------------

AC2_LINES = {
    1: ("Both wolves are dead: player_9 and player_7. The Serial Killer is alive and is one of player_2, player_4, "
        "player_6, player_8 and player_10."),
    2: ("You were roleblocked on night 2, so the Chanteuse came to you, and player_7 was the Chanteuse. player_2's "
        "report that player_7 came to you that night is true. This does not show that player_2 is the Sentinel."),
    3: ("player_3's will shows player_7, the Chanteuse, went to player_8 on night 1. The pack's kill that night was on "
        "player_1, so that visit was her block on player_8."),
    4: ("If player_2's watch is true, player_8 is the Healer: no other role still in play could have come to you on "
        "night 2."),
    5: "For player_8 not to be the Healer, player_2's watch must be false.",
    6: "If the current role claims are true, the Serial Killer is player_6 or player_10.",
}
AC2_LINE_3_CLAIM = " It agrees with player_8's claim that it was roleblocked on night 1."
AC2_VOTE_FORM = "player_8 can be the Serial Killer only if player_2's watch is false."


def test_acceptance_case_2_end_to_end():
    case = _case(VOTES, AC2_ID)
    prompt, inputs = _turn(case)
    for line in (1, 2, 3, 6):
        assert _where(AC2_LINES[line], prompt, inputs) == "seat block", line
    assert AC2_LINES[3] + AC2_LINE_3_CLAIM not in prompt  # no such claim of player_8's in the payload
    # Lines 4 and 5 on this vote turn: the vote form (AC2 folded), in player_8's entry with line 3.
    assert AC2_LINES[4] not in prompt and AC2_LINES[5] not in prompt
    assert _where(AC2_VOTE_FORM, prompt, inputs) == "seat block"
    entry = next(line for line in inputs["deduction_seat_before_note"].splitlines() if AC2_VOTE_FORM in line)
    assert entry.startswith("- " + AC2_VOTE_FORM) and AC2_LINES[3] in entry
    # The same payload as a discussion turn shows line 4; line 5 is the item the fold replaced.
    discussion, discussion_inputs = _turn(case, vote_turn=False)
    assert _where(AC2_LINES[4], discussion, discussion_inputs) == "seat block"
    view = seat_view_from_payload({**_payload(case), "deduction_mode": "full"})
    assert AC2_LINES[5] in [item.text for item in conditional_items(view)]
    # Must not say: that player_8 is the Healer without the premise; that player_7's night-1 visit counts
    # against player_8 (the only sentences naming both and night 1 are the will itself and line 3).
    assert "player_8 is the Healer" not in prompt
    for sentence in _sentences(prompt):
        if "player_7" in sentence and "player_8" in sentence and "night 1" in sentence:
            assert sentence in ("The record of player_3, the trailseer: night 1, followed player_7; they visited "
                                "player_8.", _sentences(AC2_LINES[3])[0]), sentence


# --- AC3: 403f4dbc, day 3, the Investigator (player_4) ----------------------------------------------

AC3_LINES = {
    1: ("Your check read player_6 Suspicious on night 2. No one had died before that night, so the Necromancer had no "
        "body to kill through and could not read Suspicious: player_6 is a wolf."),
    2: ("player_9 says you came to player_6 on night 2. You did: you checked player_6 that night. This confirms that "
        "part of player_9's report, not that player_9 is the Sentinel."),
    3: ("player_6 says it visited no one on night 2. That is about where player_6 went. player_9's watch is about who "
        "came to player_6. The two do not conflict."),
}
AC3_RECORD = "Night 2 (last night): you checked player_6. player_6 reads Suspicious."


def test_acceptance_case_3_end_to_end():
    prompt, inputs = _turn(_ac3_case())
    first, second = AC3_LINES[1].split(". ", 1)
    assert _where(AC3_RECORD + " " + second, prompt, inputs) == "night record"  # line 1, after the record's own
    assert first + "." not in prompt
    for line in (2, 3):
        assert _where(AC3_LINES[line], prompt, inputs) == "seat block", line
    # Must not say: that player_6's statement and the watch conflict.
    for sentence in _sentences(prompt):
        if "player_6" in sentence:
            assert not re.search(r"conflict|contradict|cannot both be true|is false",
                                 sentence.replace("do not conflict", "")), sentence


# --- AC4: 403f4dbc, the day-5 vote, the Vigilante (player_2) ----------------------------------------

AC4_LINES = {
    1: ("Both wolves are dead: player_6 and player_1. The Necromancer is alive: it killed through a body on night 4. It "
        "is player_3, player_9 or player_10."),
    2: ("player_4's will shows player_4 checked player_6 on night 2, so player_4 went to player_6 that night, as "
        "player_9's watch reported. This confirms that part of the report, not that player_9 is the Sentinel."),
    3: "No one else claims the Sentinel. player_3 and player_10 have made no role claim.",
    4: "If player_9's claim is true, the Necromancer is player_3 or player_10.",
    5: ("player_9 says no one came to player_3 on night 4. That is about who came to player_3, not about whether "
        "player_3 acted."),
}


def test_acceptance_case_4_end_to_end():
    prompt, inputs = _turn(_case(VOTES, AC4_ID))
    for line, sentence in AC4_LINES.items():
        assert _where(sentence, prompt, inputs) == "seat block", line
    # Must not say: anything that singles out one of player_3, player_9 and player_10 (an engine line naming
    # some but not all of them is one of the case's own lines 2, 3 and 5).
    engine = inputs["deduction_public_block"] + inputs["deduction_seat_before_note"] + inputs["night_actions"]
    for line in engine.splitlines():
        named = [p for p in ("player_3", "player_9", "player_10") if re.search(rf"\b{p}\b", line)]
        assert named in ([], ["player_3", "player_9", "player_10"]) or line.removeprefix("- ") in (
            AC4_LINES[2], AC4_LINES[3], AC4_LINES[5]), line
