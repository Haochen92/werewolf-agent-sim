"""The ten-seat grading table (plan §9.6 item 10) and the credit rules built on it.

One test per row of the table where the row has a case of its own, on hand-built night records in
the engine's shape (``night_resolutions[*].records/choices/outcome``), plus the credit ledger's
once-per-scope count, the unscored baseline, adoption counts and the prune list.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from Agents.memory.consolidation.config import TickConfig
from Agents.memory.consolidation.credit import credit_apply, sp_lift
from Agents.memory.consolidation.grading import GameView
from Agents.memory.consolidation.store_ops import prune_and_evict
from tests.factories.builders import eval_case_part, strategy_point

ROLES = {"p1": "investigator", "p2": "sentinel", "p3": "trailseer", "p4": "vigilante", "p5": "sigilist",
         "p6": "healer", "p7": "chanteuse", "p8": "illusionist", "p9": "serial_killer", "p10": "speculator"}


def rec(actor, action, target, result, seen=()):
    return {"actor": actor, "action": action, "target": target, "result": result, "seen": list(seen)}


def night(day, records, choices=(), deaths=(), **outcome):
    base = {"attackers": [], "attacks_on": {}, "concealed": [], "visits": []}
    base.update(outcome)
    return {"day": day, "records": list(records), "choices": list(choices), "deaths": list(deaths),
            "outcome": base}


def kill_choice(actor, target, role="chanteuse"):
    return {"actor": actor, "kind": "kill", "role": role, "target": target}


def view(*nights, roles=ROLES, days=(), **extra):
    return GameView({"roles": roles, "night_resolutions": list(nights), "day_resolutions": list(days), **extra})


def night_case(player, day, kind, target=None):
    return {"action_phase": "night_action", "player_id": player, "player_role": ROLES[player], "day": day,
            "agent_night_action": {"kind": kind, "target": target}}


def pack_night(result, victim="p1", extra=(), **outcome):
    return night(2, [rec("wolves", "kill", victim, result), *extra], [kill_choice("p7", victim)], **outcome)


# --- the pack's kill, and its chat ---

@pytest.mark.parametrize("result, victim, grade", [
    ("killed", "p1", "positive"),   # a town role
    ("killed", "p10", "neutral"),   # a neutral
    ("saved", "p1", "negative"),    # a target the healer covered
    ("immune", "p9", "negative"),   # the serial killer
])
def test_pack_kill(result, victim, grade):
    v = view(pack_night(result, victim))
    assert v.night_grade(night_case("p7", 2, "kill", victim)) == grade
    assert v.night_grade(night_case("p8", 2, "chat")) == grade  # the chat takes the night's kill grade


def test_pack_kill_seen_is_negative_and_a_sigil_on_the_carrier_is_not_counted():
    watched = pack_night("killed", extra=[rec("p2", "watch", "p1", "seen", ["p7"])])
    followed = pack_night("killed", extra=[rec("p3", "follow", "p7", "seen", ["p1"])])
    sigiled = pack_night("killed", extra=[rec("p5", "sigil", "p7", "hit")])
    assert view(watched).pack_kill_grade(2) == "negative"
    assert view(followed).pack_kill_grade(2) == "negative"
    assert view(sigiled).pack_kill_grade(2) == "positive"


# --- the lone killer ---

@pytest.mark.parametrize("result, victim, extra, grade", [
    ("killed", "p1", (), "positive"),
    ("killed", "p10", (), "neutral"),
    ("saved", "p1", (), "negative"),
    ("killed", "p1", (rec("p2", "watch", "p1", "seen", ["p9"]),), "negative"),
])
def test_serial_killer(result, victim, extra, grade):
    v = view(night(2, [rec("p9", "kill", victim, result), *extra]))
    assert v.night_grade(night_case("p9", 2, "kill", victim)) == grade


def test_necromancer_nights_are_unscored():
    roles = {**ROLES, "p9": "necromancer"}
    v = view(night(2, [rec("p9", "kill", "p1", "killed", ["p4"])]), roles=roles)
    assert v.night_grade({**night_case("p9", 2, "kill", "p1"), "player_role": "necromancer"}) is None


# --- the wolves' skills ---

def test_chanteuse_blocks():
    healer_on_victim = {"actor": "p6", "kind": "protect", "role": "healer", "target": "p1"}
    held = {"actor": "p4", "kind": "hold_fire", "role": "vigilante", "target": None}
    trail = {"actor": "p3", "kind": "follow", "role": "trailseer", "target": "p2"}
    base = [rec("wolves", "kill", "p1", "killed")]

    def grade(block, choice):
        n = night(2, [*base, block], [kill_choice("p8", "p1", "illusionist"), choice])
        return view(n).night_grade(night_case("p7", 2, "block", block["target"]))

    assert grade(rec("p7", "block", "p6", "blocked"), healer_on_victim) == "positive"  # critical
    assert grade(rec("p7", "block", "p3", "blocked"), trail) == "neutral"              # cancelled, harmless
    assert grade(rec("p7", "block", "p4", "blocked"), held) == "negative"              # nothing to cancel
    assert grade(rec("p7", "block", "p9", "no_effect"), held) == "neutral"             # did not take


def test_illusionist_conceals():
    earlier = night(1, [rec("p1", "investigate", "p7", "suspicious", ["p7"])])
    concealed = night(2, [rec("wolves", "kill", "p1", "killed"), rec("p8", "conceal", None, "concealed")],
                      deaths=["p1"], concealed=["p1"])
    assert view(earlier, concealed).night_grade(night_case("p8", 2, "conceal")) == "positive"
    assert view(concealed).night_grade(night_case("p8", 2, "conceal")) == "negative"  # no record to hide
    no_body = night(2, [rec("wolves", "kill", "p1", "saved"), rec("p8", "conceal", None, "no_body")])
    assert view(no_body).night_grade(night_case("p8", 2, "conceal")) == "neutral"
    landed = night(2, [rec("wolves", "kill", "p1", "killed")], deaths=["p1"])
    assert view(earlier, landed).night_grade(night_case("p8", 2, "declined")) == "negative"  # will names a wolf
    assert view(landed).night_grade(night_case("p8", 2, "declined")) == "neutral"


# --- town ---

@pytest.mark.parametrize("record, grade", [
    (rec("p1", "investigate", "p7", "suspicious"), "positive"),
    (rec("p1", "investigate", "p2", "not_suspicious"), "neutral"),
    (rec("p1", "investigate", "p9", "not_suspicious"), "negative"),  # a false clear on the serial killer
    (rec("p1", "investigate", "p7", "roleblocked"), "neutral"),
])
def test_investigator(record, grade):
    assert view(night(2, [record])).night_grade(night_case("p1", 2, "investigate", record["target"])) == grade


def test_declined_uses_are_neutral():
    assert view(night(2, [])).night_grade(night_case("p1", 2, "declined")) == "neutral"
    assert view(night(2, [])).night_grade(night_case("p4", 2, "hold_fire")) == "neutral"


def test_sentinel():
    def grade(seen, *earlier):
        return view(*earlier, night(2, [rec("p2", "watch", "p6", "seen", seen)])).night_grade(
            night_case("p2", 2, "watch", "p6"))

    assert grade(["p7"]) == "positive"
    assert grade(["p4"]) == "neutral"
    assert grade([]) == "negative"  # a watch spent on a door no one came to
    dead_p4 = night(1, [], deaths=["p4"])
    assert grade(["p4"], dead_p4) == "positive"  # a dead name at the door: the necromancer's body


@pytest.mark.parametrize("target, seen, grade", [("p7", ["p1"], "positive"), ("p4", ["p1"], "neutral"),
                                                 ("p4", [], "negative")])
def test_trailseer(target, seen, grade):
    v = view(night(2, [rec("p3", "follow", target, "seen", seen)]))
    assert v.night_grade(night_case("p3", 2, "follow", target)) == grade


@pytest.mark.parametrize("target, result, grade", [("p1", "saved", "positive"), ("p7", "saved", "negative"),
                                                   ("p1", "no_attack", "neutral")])
def test_healer(target, result, grade):
    v = view(night(2, [rec("p6", "protect", target, result)]))
    assert v.night_grade(night_case("p6", 2, "protect", target)) == grade


@pytest.mark.parametrize("target, result, grade", [("p9", "immune", "positive"), ("p7", "saved", "positive"),
                                                   ("p1", "killed", "negative"), ("p10", "killed", "neutral")])
def test_vigilante(target, result, grade):
    v = view(night(2, [rec("p4", "shoot", target, result)]))
    assert v.night_grade(night_case("p4", 2, "kill", target)) == grade


@pytest.mark.parametrize("target, result, attackers, grade", [
    ("p7", "hit", ["p7"], "positive"),
    ("p9", "miss", ["p9"], "positive"),   # the immune serial killer: the right choice, read as a miss
    ("p4", "hit", ["p4"], "negative"),    # the vigilante, who shot
    ("p1", "miss", ["p7"], "negative"),   # a sigil on someone who did not attack
])
def test_sigilist(target, result, attackers, grade):
    v = view(night(2, [rec("p5", "sigil", target, result)], attackers=attackers))
    assert v.night_grade(night_case("p5", 2, "sigil", target)) == grade


# --- the neutrals ---

def test_speculator_pick_and_dying_unpicked():
    picked = night(2, [rec("p10", "pick", "town", "picked", ["town"])])
    assert view(picked, neutral_result="won").night_grade(night_case("p10", 2, "pick", "town")) == "positive"
    assert view(picked, neutral_result="lost").night_grade(night_case("p10", 2, "pick", "town")) == "negative"
    died = night(2, [], deaths=["p10"])
    v = view(night(1, []), died)
    assert v.night_grade(night_case("p10", 2, "declined")) == "negative"  # its last night, unpicked
    assert v.night_grade(night_case("p10", 1, "declined")) == "neutral"


def test_fortune_teller():
    roles = {**ROLES, "p10": "fortune_teller"}

    def grade(record, **outcome):
        v = view(night(2, [record], **outcome), roles=roles)
        return v.night_grade({**night_case("p10", 2, "bet", record["target"]), "player_role": "fortune_teller"})

    assert grade(rec("p10", "bet", "p1", "scored_1")) == "positive"
    assert grade(rec("p10", "bet", "p1", "missed")) == "negative"
    assert grade(rec("p10", "bet", "p10", "self_bet"), attacks_on={"p10": [{"attacker": "p9"}]}) == "positive"
    assert grade(rec("p10", "bet", "p10", "self_bet")) == "negative"


# --- day ---

def test_votes_by_side():
    lynch_p7 = {"day": 2, "voted_player": "p7", "vote_counts": {"p7": 5, "p1": 2}}
    no_lynch = {"day": 2, "no_vote": True, "voted_player": None, "vote_counts": {"abstain": 4}}
    v = view(night(1, [rec("p10", "pick", "wolves", "picked", ["wolves"])]), days=[lynch_p7])

    def vote(player, votee, day_res=lynch_p7):
        return v.vote_grade(player, ROLES[player], 2, votee, majority=max(day_res["vote_counts"],
                            key=day_res["vote_counts"].get), day_res=day_res)

    assert vote("p1", "p7") == "positive"                 # town on a wolf
    assert vote("p1", "p10") == "negative"                # town on a neutral
    assert vote("p1", "abstain", no_lynch) == "negative"  # a town abstain that fed a deadlock
    assert vote("p8", "p7") == "positive"                 # the pack blends with the room
    assert vote("p8", "p1") == "negative"
    assert vote("p9", "p7") == "positive"                 # the lone killer: any lynch but its own
    assert vote("p10", "p7") == "positive"                # the speculator after picking the wolves: blends
    assert v.vote_grade("p10", "speculator", 1, "p7") is None  # before its pick


def test_discussion_grade():
    v = view(days=[{"day": 2, "voted_player": "p1"}, {"day": 3, "voted_player": "p7"}])
    assert v.discussion_grade("p7", "chanteuse", 3, set()) == "negative"   # its own lynch
    assert v.discussion_grade("p8", "illusionist", 2, {"p1"}) == "positive"  # a landed push
    assert v.discussion_grade("p8", "illusionist", 3, set()) == "negative"  # a packmate lynched


# --- the credit ledger ---

def _window(tmp: Path, cases: list, record: dict) -> str:
    cases_path = tmp / "cases" / "g1.jsonl"
    cases_path.parent.mkdir(parents=True)
    cases_path.write_text("\n".join(json.dumps(eval_case_part(c)) for c in cases))
    dump = tmp / "games.jsonl"
    dump.write_text(json.dumps({**record, "game_id": "g1", "roles": ROLES,
                                "eval_cases_path": "somewhere/else/g1.jsonl"}))  # stale: found by name
    return str(dump)


def _followed(case: dict, key: str, verdict: str = "follow") -> dict:
    return {**case, "memory_enabled": True, "strategy_index_to_key": {"1": key},
            "strategy_verdicts": [{"strategy_index": 1, "verdict": verdict}]}


def test_one_verdict_per_lesson_per_scope_and_unscored_without_a_base(tmp_path):
    chat = [_followed(night_case("p7", 2, "chat"), "k_chat") for _ in range(3)]
    record = {"night_resolutions": [pack_night("killed")], "day_resolutions": []}
    on = _window(tmp_path, chat, record)
    sp = tmp_path / "strategy_points.json"
    sp.write_text(json.dumps({"namespaces": {"strategy_points/chanteuse/night_action": [
        strategy_point("k_chat", cell="chanteuse/night_action")]}}))

    credit_apply(sp, on, base_rates={"chanteuse/night_action/chat": [0.2, 10]})
    v = json.loads(sp.read_text())["namespaces"]["strategy_points/chanteuse/night_action"][0]["value"]
    assert (v["follow_count"], v["positive_count"], v["retrieved_count"]) == (1, 1, 1)  # three turns, one chat
    assert v["credit_base"] == 0.2

    credit_apply(sp, on, base_rates={})  # no memory-off data for the channel
    v = json.loads(sp.read_text())["namespaces"]["strategy_points/chanteuse/night_action"][0]["value"]
    assert v["follow_count"] == 1 and v["credit_base"] is None and sp_lift(v, v["credit_base"]) is None


def test_adoption_counts_take_the_strongest_verdict_of_a_scope(tmp_path):
    turns = [_followed(night_case("p7", 2, "chat"), "k", "not_relevant"),
             _followed(night_case("p7", 2, "chat"), "k", "override")]
    on = _window(tmp_path, turns, {"night_resolutions": [pack_night("killed")], "day_resolutions": []})
    sp = tmp_path / "strategy_points.json"
    sp.write_text(json.dumps({"namespaces": {"strategy_points/chanteuse/night_action": [
        strategy_point("k", cell="chanteuse/night_action")]}}))
    credit_apply(sp, on, base_rates={})
    v = json.loads(sp.read_text())["namespaces"]["strategy_points/chanteuse/night_action"][0]["value"]
    assert (v["retrieved_count"], v["override_count"], v["not_relevant_count"]) == (1, 1, 0)


def test_prune_and_evict_list_their_changes_and_never_prune_an_unscored_point():
    cell = "chanteuse/night_action"
    ns = {f"strategy_points/{cell}": [
        strategy_point("bad", cell=cell, follow_count=10, negative_count=10, credit_base=0.0),
        strategy_point("unscored", cell=cell, follow_count=10, negative_count=10, credit_base=None),
        strategy_point("rejected", cell=cell, retrieved_count=9, override_count=5, not_relevant_count=1),
        strategy_point("good", cell=cell, follow_count=3, positive_count=3, credit_base=0.0),
    ]}
    stats = prune_and_evict(ns, {}, TickConfig())
    assert {c["key"]: c["change"] for c in stats["changes"]} == {"bad": "pruned", "rejected": "evicted",
                                                                 "good": "proven"}
    assert [r["key"] for r in ns[f"strategy_points/{cell}"]] == ["unscored", "good"]


# --- a tagged observation's grade, and a served game's record rebuilt from its events ---

def test_observation_grade_finds_the_named_decision():
    lynch = {"day": 2, "voted_player": "p7", "vote_counts": {"p7": 5}, "votes": [{"voter": "p1", "votee": "p7"}]}
    v = view(pack_night("killed", extra=[rec("p7", "block", "p4", "blocked"), rec("p1", "investigate", "p7", "suspicious")]),
             days=[lynch])
    assert v.observation_grade("investigator", "night_action", 2) == "positive"
    assert v.observation_grade("chanteuse", "night_action", 2, "kill") == "positive"
    assert v.observation_grade("chanteuse", "night_action", 2, "several") is None  # no single decision
    assert v.observation_grade("illusionist", "night_action", 2, "skill") == "neutral"  # declined: no will
    assert v.observation_grade("sentinel", "night_action", 2) == "neutral"  # no record: a declined watch
    assert v.observation_grade("investigator", "day_vote", 2) == "positive"
    assert v.observation_grade("investigator", "day_vote", 0) is None
    assert v.observation_grade("investigator", "day_vote", -1) is None  # not tagged


def test_record_from_event_log_rebuilds_what_the_grader_reads():
    from Agents.memory.extraction.offline import record_from_event_log

    roles = {"p1": "investigator", "p6": "healer", "p7": "chanteuse", "p8": "illusionist", "p9": "serial_killer"}
    events = [
        {"seq": 1, "day": 1, "type": "roles_assigned", "roles": roles},
        {"seq": 2, "day": 1, "type": "night_action", "actor": "p6", "role": "healer", "target": "p1"},
        {"seq": 3, "day": 1, "type": "night_action", "actor": "p1", "role": "investigator", "target": "p7"},
        {"seq": 4, "day": 1, "type": "wolf_kill_decided", "carrier": "p8", "target": "p6"},
        {"seq": 5, "day": 1, "type": "night_record", "actor": "wolves", "action": "kill", "target": "p6", "result": "killed"},
        {"seq": 6, "day": 1, "type": "night_record", "actor": "p9", "action": "kill", "target": "p1", "result": "saved"},
        {"seq": 7, "day": 1, "type": "night_record", "actor": "p1", "action": "investigate", "target": "p7",
         "result": "suspicious", "seen": ["p7"]},
        {"seq": 8, "day": 1, "type": "night_result", "deaths": [{"player": "p6", "concealed": False}],
         "saves": [{"player": "p1"}]},
        {"seq": 9, "day": 2, "type": "addressed_targets", "player": "p7", "targets": [{"stance": "accusation", "target": "p1"}]},
        {"seq": 10, "day": 2, "type": "vote_cast", "voter": "p7", "votee": "p1"},
        {"seq": 11, "day": 2, "type": "lynch_result", "player": "p1", "outcome": "lynched", "vote_counts": {"p1": 4}},
        {"seq": 12, "day": 2, "type": "game_over", "winner": "wolves", "neutral_result": None},
    ]
    g = record_from_event_log("g1", events)
    n = g["night_resolutions"][0]
    assert {"actor": "p8", "kind": "kill", "role": "illusionist", "target": "p6"} in n["choices"]
    assert sorted(n["outcome"]["attackers"]) == ["p8", "p9"]
    healer = next(r for r in n["records"] if r["actor"] == "p6")  # killed that night, so never told
    assert healer["untold"] and healer["result"] == "saved"
    v = GameView(g)
    assert v.observation_grade("healer", "night_action", 1) == "positive"
    assert v.observation_grade("chanteuse", "day_discussion", 2) == "positive"  # a landed push
    assert v.observation_grade("chanteuse", "day_vote", 2) == "positive"  # blended with the room
