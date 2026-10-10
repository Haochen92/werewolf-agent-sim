"""The claim ledger and the agents' view of previous days (day summary v4; discussion_evidence.md §6.6).

The summariser only transcribes claims; code folds them across days and checks them against the
engine's record. Pins the fold (repeats merge, changes keep history, retractions show), every check
(each states a fact, and none fires where the record fits more than one reading), that the ledger
is recomputed from the current record, and the compact view agents read.
"""
from __future__ import annotations

from Agents.nodes.day.summary_agent import summary_context
from Agents.prompts.prompt_formatters import format_day_summaries
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.prompts.day_discuss import day_discuss_template
from Agents.rules.claim_ledger import format_claim_ledger
from Agents.schemas.game_events import DaySummary, DeathRecord
from Agents.schemas.roles import lineup

CAST = {role: 1 for role in lineup("serial_killer", "speculator")}


def _day(day, claims=(), accusations=()):
    return DaySummary(day=day, summary="(text)",
                      structured={"accusations": list(accusations), "role_claims": list(claims)})


def _claim(player, role, *actions, kind="claimed"):
    return {"player": player, "claimed_role": role, "kind": kind,
            "night_actions": [dict(zip(("night", "action", "target", "result"), a)) for a in actions]}


def _gm(text, day):
    return DaySummary(day=day, summary=text, source="game_master")


def _ledger(*summaries, dead=(), cast=CAST):
    return format_claim_ledger(list(summaries), list(dead), cast)


# --- the fold ---------------------------------------------------------------------

def test_a_repeated_claim_merges_and_a_change_keeps_the_earlier_one():
    text = _ledger(
        _day(2, [_claim("p3", "investigator", (1, "investigate", "p1", "vigilante"))]),
        _day(3, [_claim("p3", "investigator", (1, "investigate", "p1", "vigilante"))]),
        _day(4, [_claim("p3", "investigator", (1, "investigate", "p1", "healer"))]),
    )
    assert text.splitlines() == [
        "p3: claimed investigator (day 2).",
        "  Night 1: checked p1, result: healer (changed on day 4; earlier: Night 1: checked p1, "
        "result: vigilante).",
    ]


def test_role_changes_and_retractions_read_as_history():
    text = _ledger(_day(2, [_claim("p3", "investigator"), _claim("p6", "vigilante")]),
                   _day(4, [_claim("p3", "healer")]),
                   _day(5, [_claim("p6", "vigilante", kind="retracted")]))
    assert "p3: claimed investigator (day 2), then claimed healer (day 4)." in text
    assert "p6: claimed vigilante (day 2), retracted vigilante (day 5)." in text


def test_filling_in_a_result_later_is_not_a_change():
    text = _ledger(_day(2, [_claim("p5", "healer", (1, "protect", "p1", "not_said"))]),
                   _day(3, [_claim("p5", "healer", (1, "protect", "p1", "saved_from_attack"))]))
    assert "changed" not in text and "says they saved them from an attack" in text


def test_two_targets_named_for_one_night_on_the_same_day_break_the_rules():
    # game 140610ad day 3: "I checked player_2 and got nothing useful ... the one I actually confirmed is player_9"
    claims = [(2, "investigate", "p2", "not_said"), (2, "investigate", "p9", "healer")]
    text = _ledger(_day(3, [_claim("p6", "investigator", *claims)]))
    assert text.splitlines()[1] == ("  Night 2: checked p9, result: healer (on day 3 also named: Night 2: "
                                    "checked p2). Rules: one check a night.")
    # named on different days, it is a change, not a second action
    text = _ledger(_day(3, [_claim("p6", "investigator", claims[0])]),
                   _day(4, [_claim("p6", "investigator", claims[1])]))
    assert "changed on day 4; earlier: Night 2: checked p2" in text and "Rules" not in text


def _planning(player, role, *plans, actions=()):
    claim = _claim(player, role, *actions)
    claim["planned_actions"] = [{"action": a, "target": t} for a, t in plans]
    return claim


def test_a_plan_is_set_beside_what_the_player_later_says_they_did():
    kept = _ledger(_day(2, [_planning("p6", "investigator", ("investigate", "p2"))]),
                   _day(3, [_claim("p6", "investigator", (2, "investigate", "p2", "not_suspicious"))]))
    assert kept.splitlines()[1] == "  Night 2: checked p2, says they read Not suspicious (planned on day 2)."
    switched = _ledger(_day(2, [_planning("p6", "investigator", ("investigate", "p2"))]),
                       _day(3, [_claim("p6", "investigator", (2, "investigate", "p9", "healer"))]))
    assert switched.splitlines()[1] == ("  Night 2: checked p9, result: healer. "
                                        "On day 2 said they planned to check p2.")
    # the player's own reason travels with it; the line states facts, never a broken promise
    reasoned = _claim("p6", "investigator", (2, "investigate", "p9", "healer"))
    reasoned["night_actions"][0]["reason"] = "they named p2 as a decoy."
    text = _ledger(_day(2, [_planning("p6", "investigator", ("investigate", "p2"))]), _day(3, [reasoned]))
    assert text.endswith("On day 2 said they planned to check p2; reason given on day 3: they named p2 as a decoy.")
    assert not any(word in text for word in ("promise", "broke", "instead"))


def test_a_plan_never_reported_on_stands_alone_and_a_protected_death_is_checked():
    text = _ledger(_day(2, [_planning("p5", "healer", ("protect", "p1"))]),
                   _gm("Night of day 2: p1 was killed by the wolves last night. They were a sentinel.", 2),
                   dead=[DeathRecord(player="p1", role="sentinel", day=2, phase="night")])
    assert text.splitlines()[1] == "  Night 2: on day 2 said they planned to protect p1. Record: p1 died that night."


def test_agents_are_told_a_day_plan_binds_no_one():
    text = format_day_summaries([_day(2, [_planning("p6", "investigator", ("investigate", "p2"))])], before_day=3)
    assert "a plan said in the day binds no one" in text


def test_older_summaries_still_read_into_the_ledger():
    v3 = DaySummary(day=2, summary="(text)", structured={"role_claims": [
        {"player": "p3", "claimed_role": "investigator", "status": "new", "evidence": "unverified",
         "claimed_results": [{"night": 1, "target": "p7", "result": "is a wolf"}]}]})
    v1 = DaySummary(day=3, summary="(text)", structured={"role_claims": [
        {"player": "p5", "claimed_role": "healer", "evidence": "unverified"}]})
    text = _ledger(v3, v1, dead=[DeathRecord(player="p7", role="sentinel", day=2, phase="night")])
    assert "p3: claimed investigator (day 2).\n  Night 1: p7 is a wolf." in text  # free text, never checked
    assert "p5: claimed healer (day 3)." in text


# --- the checks ----------------------------------------------------------------------

def test_an_investigation_result_is_checked_against_a_revealed_role():
    # The investigator's reads (Suspicious / Not suspicious) and a claimed role are both checked.
    claims = _day(2, [_claim("p3", "investigator", (1, "investigate", "p7", "suspicious"),
                             (2, "investigate", "p8", "not_suspicious"), (3, "investigate", "p9", "healer"))])
    dead = [DeathRecord(player="p7", role="chanteuse", day=3, phase="day"),
            DeathRecord(player="p8", role="illusionist", day=3, phase="night"),
            DeathRecord(player="p9", role="healer", day=3, phase="night")]
    text = _ledger(claims, dead=dead)
    assert "checked p7, says they read Suspicious. Record: p7 was revealed as chanteuse, as claimed." in text
    assert "checked p8, says they read Not suspicious. Record: p8 was revealed as illusionist." in text
    assert "checked p9, result: healer. Record: p9 was revealed as healer, as claimed." in text


def test_an_unverified_private_result_stays_unverified():
    # nothing in the record bears on a living player's role: no note either way
    text = _ledger(_day(2, [_claim("p3", "investigator", (1, "investigate", "p7", "suspicious"))]))
    assert text == "p3: claimed investigator (day 2).\n  Night 1: checked p7, says they read Suspicious."


def test_a_healer_protecting_themselves_breaks_the_rules():
    text = _ledger(_day(3, [_claim("p5", "healer", (2, "protect", "p5", "not_said"))]))
    assert "Night 2: protected p5. Rules: the healer cannot protect themselves." in text


def test_a_claimed_save_is_checked_against_the_announcements():
    night1 = _gm("Night of day 1: p1 was attacked by the wolves but was saved by the healer!", 1)
    night2 = _gm("Night of day 2: No one died last night.", 2)
    text = _ledger(night1, night2, _day(3, [_claim("p5", "healer", (1, "protect", "p1", "saved_from_attack"),
                                                   (2, "protect", "p4", "saved_from_attack"))]))
    assert "Night 1: protected p1, says they saved them from an attack. Record: p1 was attacked and saved by the healer that night." in text
    assert "Night 2: protected p4, says they saved them from an attack. Record: no save of p4 was announced that night." in text


def test_a_night_not_yet_announced_is_not_checked():
    text = _ledger(_day(2, [_claim("p5", "healer", (2, "protect", "p4", "saved_from_attack"))]))
    assert "Record" not in text


def test_a_shot_is_checked_against_deaths_but_a_survivor_is_left_alone():
    gm = [_gm("Night of day 1: p4 was shot by the vigilante last night. They were a sentinel.", 1),
          _gm("Night of day 2: No one died last night.", 2)]
    dead = [DeathRecord(player="p4", role="sentinel", day=1, phase="night")]
    text = _ledger(*gm, _day(3, [_claim("p9", "vigilante", (1, "shoot", "p4", "died"), (2, "shoot", "p2", "died"))]),
                   dead=dead)
    assert "Night 1: shot p4, says they died. Record: p4 died that night." in text
    assert "Night 2: shot p2, says they died. Record: p2 did not die that night." in text
    # a shot that "missed" may have hit the immune serial killer, whose survival is silent: no note
    quiet = _ledger(*gm, _day(3, [_claim("p9", "vigilante", (2, "shoot", "p2", "survived"))]), dead=dead)
    assert "Record" not in quiet


def test_counterclaims_and_revealed_holders_of_a_one_off_role():
    dead = [DeathRecord(player="p3", role="investigator", day=2, phase="night")]
    text = _ledger(_day(2, [_claim("p3", "investigator"), _claim("p6", "investigator")]),
                   _day(3, [_claim("p7", "investigator")]), dead=dead)
    assert "p3: claimed investigator (day 2). Record: revealed as investigator when they died on night 2, as claimed." in text
    assert ("p6: claimed investigator (day 2). Record: the game has 1 investigator, and p7 also claims it and "
            "p3 was revealed as investigator.") in text


def test_a_dead_claimant_is_checked_against_their_revealed_role():
    dead = [DeathRecord(player="p8", role="chanteuse", day=3, phase="day")]
    text = _ledger(_day(2, [_claim("p8", "healer")]), dead=dead)
    assert "p8: claimed healer (day 2). Record: revealed as chanteuse when they were voted out on day 3, not healer." in text


def test_the_ledger_is_recomputed_from_the_current_record():
    claims = _day(2, [_claim("p3", "investigator", (1, "investigate", "p7", "suspicious"))])
    assert "Record" not in _ledger(claims)
    later = _ledger(claims, dead=[DeathRecord(player="p7", role="chanteuse", day=3, phase="day")])
    assert "Record: p7 was revealed as chanteuse, as claimed." in later


def test_the_next_summariser_sees_the_checks():
    # the check the summariser's v3 verdict used to carry (and the old ledger dropped) now reaches it
    _, claims = summary_context([_day(3, [_claim("p5", "healer", (2, "protect", "p5", "not_said"))])])
    assert "Rules: the healer cannot protect themselves." in claims


# --- the view agents read ---------------------------------------------------------------

def test_accusations_tag_revealed_players_and_drop_the_retold_sections():
    old = DaySummary(day=3, summary="Key accusations and defenses: ...\nVillage dynamics: a story.", structured={
        "accusations": [{"accusers": ["p8", "p1"], "target": "p2", "reasoning": "p8 argued p2 survived an attack.",
                         "evidence_type": "concrete_claim", "defense": "p2 denied it.",
                         "disputed_by": "p6 disagreed.", "record_check": "No attack on p2 was announced."}],
        "role_claims": [], "alliances": [{"players": ["p8", "p1"], "basis": "pushing p2"}],
        "village_dynamics": {"information_landscape": "a story", "consensus": "b", "drivers": "c"}})
    text = format_day_summaries([old], before_day=4,
                                dead_roster=[DeathRecord(player="p8", role="chanteuse", day=3, phase="day")])
    assert ("[Day 3] p8 (revealed chanteuse, voted out day 3), p1 → p2: p8 argued p2 survived an attack. "
            "Defense: p2 denied it. Disputed: p6 disagreed. Summariser's check against the record: "
            "No attack on p2 was announced.") in text
    assert "a story" not in text and "pushing p2" not in text and "concrete_claim" not in text
    assert "Claims made in the day discussion" not in text  # nobody claimed: no block


def test_a_day_stored_only_as_text_is_shown_as_written():
    fallback = DaySummary(day=2, summary="p1: hello\np2: hi", structured={})
    assert "[Day 2]\np1: hello\np2: hi" in format_day_summaries([fallback], before_day=3)


def test_the_role_claims_line_is_not_repeated_beside_the_ledger():
    text = format_day_summaries([DaySummary(day=2, summary="Key accusations and defenses: None.\nRole claims: p3 claimed investigator",
                                            structured={"accusations": [], "role_claims": [_claim("p3", "investigator")]})],
                                before_day=3)
    assert text.count("investigator") == 1


def test_memory_instructions_appear_only_with_memories():
    base = {"player_id": "p1", "player_role": "healer", "current_day": 2, "day_channel": [], "day_summaries": [],
            "surviving_players": ["p1", "p2"], "lineup": lineup("serial_killer", "speculator")}
    template = day_discuss_template("healer")
    off = "\n".join(m.content for m in template.format_messages(**build_agent_prompt_input(base)))
    assert "Relevant observations" not in off and "Dynamic strategy points" not in off
    assert "Adaptive Strategic thinking" in off  # the private note is not memory: it stays
    on = "\n".join(m.content for m in template.format_messages(**build_agent_prompt_input(
        {**base, "retrieved_observations": "1. Situation: x", "strategy_points": "[1] y → Action: z"})))
    assert "Relevant observations" in on and "1. Situation: x" in on
    assert "Dynamic strategy points" in on and "[1] y → Action: z" in on and "cross-check" in on


def test_a_claim_repeated_without_its_night_merges_into_the_dated_one():
    text = _ledger(_day(2, [_claim("p5", "investigator", (1, "investigate", "p1", "suspicious"))]),
                   _day(4, [_claim("p5", "investigator", (0, "investigate", "p1", "suspicious"))]))
    assert text.count("checked p1") == 1 and "Night not stated" not in text
    # and the other way round: an undated claim that is later dated becomes the dated entry
    text = _ledger(_day(2, [_claim("p5", "investigator", (0, "investigate", "p1", "suspicious"))]),
                   _day(3, [_claim("p5", "investigator", (1, "investigate", "p1", "not_said"))]))
    assert text.splitlines()[1:] == ["  Night 1: checked p1, says they read Suspicious."]


# --- the speaker's own claim field (role_sheet.md, formal claims; 2026-10-09) ----------------

from Agents.schemas.game_events import DayChannel


def _said(day, seq, player, claim="none", passed=False):
    return DayChannel(day=day, seq=seq, player=player, message="" if passed else "a line",
                      claim=claim, passed=passed)


def test_the_role_line_comes_from_the_speakers_claim_field():
    text = format_claim_ledger([_day(2)], [], CAST, [_said(2, 1, "p3", "investigator")])
    assert text.splitlines() == ["p3: claimed investigator (day 2)."]


def test_the_summarisers_role_is_dropped_where_the_speaker_claimed_otherwise_that_day():
    text = format_claim_ledger(
        [_day(2, [_claim("p3", "healer", (1, "protect", "p1", "no_attack"))])], [], CAST,
        [_said(2, 1, "p3", "investigator")])
    assert text.splitlines() == [
        "p3: claimed investigator (day 2).",
        "  Night 1: protected p1, says there was no attack.",  # the transcribed action still counts
    ]


def test_the_summarisers_role_fills_in_for_a_player_who_set_no_claim_that_day():
    # a human's line has no field; the field also misses a repeat said on a later day
    text = format_claim_ledger(
        [_day(2, [_claim("p3", "investigator")]), _day(3, [_claim("p3", "investigator", kind="retracted")])],
        [], CAST, [_said(2, 1, "p5", "healer")])
    assert text.splitlines() == [
        "p5: claimed healer (day 2).",
        "p3: claimed investigator (day 2), retracted investigator (day 3).",
    ]


def test_a_held_or_passed_line_claims_nothing_and_a_repeat_merges():
    text = format_claim_ledger([], [], CAST, [
        _said(2, 1, "p3", "investigator", passed=True),
        _said(2, 2, "p3", "investigator"),
        _said(3, 1, "p3", "investigator"),
        _said(3, 2, "p3", "none"),
    ])
    assert text.splitlines() == ["p3: claimed investigator (day 2)."]


def test_agents_read_only_the_claims_of_earlier_days():
    text = format_day_summaries([_day(2)], before_day=3, cast_role_counts=CAST,
                                messages=[_said(2, 1, "p3", "investigator"), _said(3, 1, "p5", "healer")])
    assert "p3: claimed investigator (day 2)." in text and "p5" not in text


def test_a_claimed_sighting_is_the_claimants_word_and_says_what_it_does_not_establish():
    watch = {"player": "p3", "claimed_role": "sentinel", "kind": "claimed",
             "night_actions": [{"night": 1, "action": "watch", "target": "p5", "result": "not_said", "seen": ["p4", "p7"]}]}
    follow = {"player": "p6", "claimed_role": "trailseer", "kind": "claimed",
              "night_actions": [{"night": 1, "action": "follow", "target": "p4", "result": "not_said", "seen": ["p5"]}]}
    quiet = {"player": "p8", "claimed_role": "sentinel", "kind": "claimed",
             "night_actions": [{"night": 1, "action": "watch", "target": "p9", "result": "not_said", "seen": []}]}
    text = _ledger(_day(2, [watch, follow, quiet]))
    assert ("  Night 1: watched p5; says p4 and p7 visited them (a visit alone does not establish a "
            "visitor's role or what they did).") in text.splitlines()
    assert "  Night 1: followed p4; says they visited p5 (a visit alone does not establish what they did there)." in text
    assert "  Night 1: watched p9." in text  # saw no one: no names, no line
    # a repeat on a later day keeps the names
    later = _ledger(_day(2, [watch]), _day(3, [{**watch, "night_actions": [{**watch["night_actions"][0], "seen": []}]}]))
    assert "says p4 and p7 visited them" in later


def test_an_action_done_to_the_speaker_is_not_their_claim():
    # e06, 2026-10-10: "I was roleblocked last night" was transcribed as a chanteuse claim.
    invented = {"player": "p2", "claimed_role": "chanteuse", "kind": "claimed",
                "night_actions": [{"night": 1, "action": "block", "target": "p2", "result": "not_said"}]}
    assert _ledger(_day(2, [invented])) == ""
    # a real claim on the same day keeps its role; only the self-targeted action goes
    text = format_claim_ledger([_day(2, [invented])], [], CAST, [_said(2, 1, "p2", "investigator")])
    assert text.splitlines() == ["p2: claimed investigator (day 2)."]
    # the fortune teller's self-bet is the one action a role takes on itself
    bet = {"player": "p4", "claimed_role": "fortune_teller", "kind": "claimed",
           "night_actions": [{"night": 1, "action": "bet", "target": "p4", "result": "not_said"}]}
    assert "p4: claimed fortune teller (day 2)." in _ledger(_day(2, [bet]))


def test_a_true_role_keeps_its_claim_when_a_held_fire_is_written_as_a_self_shot():
    # replay 2026-10-10 (e02 day 3): "I was roleblocked on night 1 and held my fire last night"
    held = {"player": "p9", "claimed_role": "vigilante", "kind": "claimed",
            "night_actions": [{"night": 1, "action": "shoot", "target": "p9", "result": "not_said"},
                              {"night": 2, "action": "shoot", "target": "p9", "result": "not_said"}]}
    assert _ledger(_day(3, [held])).splitlines() == ["p9: claimed vigilante (day 3)."]
