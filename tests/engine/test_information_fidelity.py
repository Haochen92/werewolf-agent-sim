"""The information-fidelity pass (audit 2026-10-03; discussion_evidence.md §6.4).

Pins what each agent is now told and how: the private night record (what each night actor did and
may know, gated to its owner), a held-back draft shown to its author only, the previous days split
by authority (the game master's record, the claims on record, the discussion summaries), the vote
turn seeing the note it replaces, the vote wording, and the summariser's v4 output.
"""
from __future__ import annotations

from Agents.nodes.day.flow import build_speaker_send, fan_out_day
from Agents.nodes.day.summary_agent import _serialize_day_summary, summary_context
from Agents.nodes.night.resolution import night_resolution
from Agents.nodes.orchestrator import day_resolution
from Agents.prompts.day_discuss import VIGILANTE_DAY_DISCUSS
from Agents.prompts.day_vote import HEALER_DAY_VOTE
from Agents.prompts.night import WOLF_NIGHT_VOTE
from Agents.prompts.prompt_formatters import format_day_channel, format_day_summaries
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.rules.night_record import night_action_records, own_night_actions
from Agents.rules.resolution import collect_attacks, resolve_attacks
from Agents.schemas import DaySummaryOutputV4
from Agents.schemas.game_events import (
    DayChannel,
    DaySummary,
    DayVote,
    DiscussionPassReason,
    FiringReason,
    NightActionRecord,
)
from tests.factories.builders import night_runtime as _runtime

ROLES = {"w0": "wolf", "w1": "wolf", "sk": "serial_killer", "h": "healer", "v": "vigilante",
         "inv": "investigator", "t0": "villager"}


def _records(wolves=None, healer=None, sk=None, vig=None, held=False):
    attacks = collect_attacks(wolves, sk, vig)
    return night_action_records(
        1, wolves_target=wolves, healer_target=healer, serial_killer_target=sk, vigilante_target=vig,
        attacks_on=attacks, verdicts=resolve_attacks(attacks, healer, "sk"), roles=ROLES,
        healer="h", serial_killer="sk", vigilante="v", vigilante_held_fire=held)


def _by(records, actor):
    return [r for r in records if r.actor == actor]


# --- the private night record ---------------------------------------------------

def test_healer_learns_a_save_and_otherwise_only_what_the_public_does():
    saved = _by(_records(wolves="t0", healer="t0"), "h")[0]
    assert saved.outcome == "t0 was attacked by the wolves, and your protection saved them."
    quiet = _by(_records(wolves="inv", healer="t0"), "h")[0]
    assert quiet.outcome == "No attack on t0 was announced."
    # protecting the serial killer while the wolves hit it: the attack is silent, so no leak
    on_sk = _by(_records(wolves="sk", healer="sk"), "h")[0]
    assert on_sk.outcome == "No attack on sk was announced."


def test_killers_learn_their_result_and_only_the_attackers_learn_the_silent_immunity():
    recs = _records(wolves="sk", vig="t0", sk="inv", healer="inv")
    assert "confirms sk is the serial killer" in _by(recs, "wolves")[0].outcome
    assert _by(recs, "v")[0].outcome == "t0 died. They were a villager."
    assert _by(recs, "sk")[0].outcome == "inv survived: the healer saved them."
    # the healer hears the (public) save, never the wolves' silent failed attack on sk
    assert "immune" not in _by(recs, "h")[0].outcome and "sk" not in _by(recs, "h")[0].outcome


def test_vigilante_holding_fire_is_recorded():
    assert [(r.action, r.target) for r in _by(_records(held=True), "v")] == [("hold_fire", None)]
    assert _by(_records(), "v") == []  # not asked (no bullets / dead): nothing


def test_each_player_sees_only_its_own_record_and_every_wolf_sees_the_packs():
    recs = _records(wolves="t0", healer="inv", sk="v", vig="w1")
    assert {r.actor for r in own_night_actions(recs, "h", "healer")} == {"h"}
    assert {r.actor for r in own_night_actions(recs, "w0", "wolf")} == {"wolves"}
    assert own_night_actions(recs, "t0", "villager") == []


def test_night_resolution_writes_the_record():
    state = {"current_day": 1, "roles": ROLES, "surviving_wolves": ["w0", "w1"],
             "surviving_villagers": ["sk", "h", "v", "inv", "t0"], "serial_killer_player": "sk",
             "healer_player": "h", "investigator_player": "inv", "vigilante_player": "v",
             "vigilante_bullets": 2, "day_channel": [], "wolves_kill_target": "t0",
             "healer_target": "t0", "serial_killer_target": None, "vigilante_target": None}
    update = night_resolution(state, _runtime())
    assert {(r.actor, r.action) for r in update["night_actions"]} == {
        ("h", "protect"), ("wolves", "kill"), ("v", "hold_fire")}
    assert update["day_summaries"][0].source == "game_master"


def _day_state(records):
    return {"current_day": 2, "current_round": 0, "roles": ROLES, "human_players": [],
            "day_channel": [], "day_summaries": [], "wolf_channel": [],
            "surviving_wolves": ["w0", "w1"], "surviving_villagers": ["sk", "h", "v", "inv", "t0"],
            "agent_strategies": {}, "investigator_results": [], "vigilante_results": [],
            "vigilante_bullets": 1, "night_actions": records}


def test_day_payloads_carry_only_the_speakers_own_record():
    recs = _records(wolves="t0", healer="inv", sk="v", vig="w1")
    fr = FiringReason(tier="proactive", owes=[])
    for player in ROLES:
        role = ROLES[player]
        send = build_speaker_send(_day_state(recs), player, role, fr)
        want = own_night_actions(recs, player, role)
        assert send.arg.get("night_actions", []) == want, player
    for send in fan_out_day(_day_state(recs), "vote"):
        p = send.arg["player_id"]
        assert send.arg.get("night_actions", []) == own_night_actions(recs, p, ROLES[p]), p


# --- what the prompts render ------------------------------------------------------

def test_the_vigilante_day_prompt_shows_bullets_and_its_record():
    rec = NightActionRecord(day=1, actor="v", action="shoot", target="t0", outcome="t0 died. They were a villager.")
    payload = build_speaker_send(_day_state([rec]), "v", "vigilante", FiringReason(tier="proactive", owes=[])).arg
    text = "\n".join(m.content for m in VIGILANTE_DAY_DISCUSS.format_messages(**build_agent_prompt_input(payload)))
    assert "Bullets left: 1" in text
    assert "Night 1 (last night): you shot t0. t0 died. They were a villager." in text


def test_the_vote_prompt_shows_the_note_it_replaces():
    payload = {**_day_state([]), "player_id": "h", "player_role": "healer",
               "surviving_players": list(ROLES), "previous_strategy": "SENTINEL-NOTE", "allow_abstain": True}
    text = "\n".join(m.content for m in HEALER_DAY_VOTE.format_messages(**build_agent_prompt_input(payload)))
    assert "SENTINEL-NOTE" in text


def test_the_wolf_night_vote_gets_the_census_and_the_packs_record():
    rec = NightActionRecord(day=1, actor="wolves", action="kill", target="sk",
                            outcome="sk was unharmed: immune to night kills.")
    payload = {"current_day": 2, "current_round": 3, "player_id": "w0", "player_role": "wolf",
               "day_channel": [], "day_summaries": [], "wolf_channel": [], "surviving_wolves": ["w0", "w1"],
               "surviving_villagers": ["sk", "t0"], "dead_roster": [], "cast_role_counts": {"wolf": 2},
               "night_actions": [rec], "previous_strategy": "", "strategy_points": ""}
    text = "\n".join(m.content for m in WOLF_NIGHT_VOTE.format_messages(**build_agent_prompt_input(payload)))
    assert "== Dead so far (public) ==" in text and "your pack attacked sk" in text
    assert "Surviving non-wolf players" in text


def test_a_held_back_draft_is_shown_to_its_author_and_nobody_else():
    channel = [
        DayChannel(day=2, seq=0, player="t0", message="I think w1 is lying."),
        DayChannel(day=2, seq=1, player="h", message="", passed=True, gated=True,
                   pass_reason=DiscussionPassReason.NOVELTY_GATED, gated_candidate="I revealed my role."),
    ]
    assert "I revealed my role." not in format_day_channel(channel)
    assert "I revealed my role." not in format_day_channel(channel, viewer="t0")
    mine = format_day_channel(channel, viewer="h")
    assert "held back" in mine and "no one else saw it" in mine and "I revealed my role." in mine


def test_previous_days_put_the_game_masters_record_above_claims_and_accusations():
    summaries = [
        DaySummary(day=2, summary="(text)", structured={
            "accusations": [{"accusers": ["player_8"], "target": "player_2",
                             "reasoning": "player_8 claimed player_2 survived an attack."}],
            "role_claims": [{"player": "inv", "claimed_role": "investigator", "kind": "claimed",
                             "night_actions": [{"night": 1, "action": "investigate", "target": "w0", "result": "wolf"}]}]}),
        DaySummary(day=2, summary="Night of day 2: t0 was stabbed by the serial killer last night.", source="game_master"),
    ]
    text = format_day_summaries(summaries, before_day=3)
    record, claims, accusations = (text.index("game master's record"), text.index("Claims made in the day discussion"),
                                   text.index("Accusations in the day discussion"))
    assert record < claims < accusations
    assert text.index("t0 was stabbed") < claims < text.index("player_8 claimed")
    assert "inv: claimed investigator (day 2)." in text
    assert "Night 1: investigated w0, result: wolf." in text


def test_votes_are_written_as_eliminate_or_abstain():
    state = {"current_day": 2, "roles": ROLES, "surviving_wolves": ["w0", "w1"],
             "surviving_villagers": ["sk", "h", "v", "inv", "t0"], "day_channel": [], "no_lynch_streak": 0,
             "day_votes": [DayVote(voter="h", votee="w0"), DayVote(voter="t0", votee="w0"),
                           DayVote(voter="inv", votee="abstain")]}
    message = day_resolution(state, _runtime())["day_channel"][0].message
    assert "h voted to eliminate w0" in message and "inv voted to abstain" in message
    assert "voted for" not in message


# --- the v4 day summary -------------------------------------------------------------

def test_the_summariser_gets_the_record_and_the_claim_ledger():
    record, claims = summary_context([
        DaySummary(day=1, summary="Night of day 1: No one died last night.", source="game_master"),
        DaySummary(day=1, summary="...", structured={"role_claims": [{"player": "h", "claimed_role": "healer"}]}),
    ])
    assert record == "[Day 1] Night of day 1: No one died last night."
    assert claims == "h: claimed healer (day 1)."


def test_the_v4_summary_writes_two_headings_and_transcribes_claims_in_fixed_words():
    out = DaySummaryOutputV4.model_validate({
        "accusations": [{"accusers": ["player_8"], "target": "player_2",
                         "reasoning": "player_8 argued that player_2 survived an attack.",
                         "evidence_type": "concrete_claim", "defense": "player_2 denied being attacked.",
                         "disputed_by": "player_6 said survival proves nothing.",
                         "record_check": "No attack on player_2 was ever announced."}],
        "role_claims": [{"player": "player_3", "claimed_role": "investigator", "kind": "claimed",
                         "night_actions": [{"night": 1, "action": "investigate", "target": "player_1", "result": "vigilante",
                                            "reason": ""}],
                         "planned_actions": [{"action": "investigate", "target": "player_5"}]},
                        {"player": "player_4", "claimed_role": "healer", "kind": "retracted", "night_actions": []}],
    })
    text = _serialize_day_summary(out)
    assert [line.split(":")[0] for line in text.splitlines()] == ["Key accusations and defenses", "Role claims"]
    assert "Disputed: player_6" in text and "Against the record: No attack on player_2" in text
    assert ("player_3 claimed investigator — Night 1: investigated player_1, result: vigilante, "
            "plans to investigate player_5 tonight") in text
    assert "player_4 retracted healer" in text
    assert set(out.model_dump()) == {"accusations", "role_claims"}
