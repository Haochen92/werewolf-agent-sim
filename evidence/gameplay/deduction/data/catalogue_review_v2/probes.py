"""Reproduce second-review findings without model calls or production changes.

From repository root:
    PYTHONPATH=. poetry run python evidence/reasoning_failures/data/catalogue_review_v2/probes.py

Night inputs isolate legal action interactions; they are not full generated game histories.
Assertions describe current engine behaviour, not assertions that the catalogue is correct.
"""
import json

from pydantic import ValidationError

from Agents.nodes.night.resolution import _spent
from Agents.nodes.orchestrator import _max_days_winner, determine_winner
from Agents.rules.claim_ledger import action_text, build_claim_ledger
from Agents.rules.night import resolve_night
from Agents.rules.night_record import disclosure, night_action_records
from Agents.schemas.game_events import DaySummary
from Agents.schemas.night import NightChoice as C
from Agents.schemas.output import ClaimedNightAction
from Agents.schemas.roles import lineup


def roles(killer="necromancer", neutral="speculator"):
    return {f"p{i}": role for i, role in enumerate(lineup(killer, neutral), 1)}


def records(choices, mapping, night=1, **kwargs):
    outcome = resolve_night(choices, mapping, night, **kwargs)
    return outcome, {r.actor: r for r in night_action_records(choices, outcome, mapping)}


results = {}
mapping = roles()

# E3: the followed person is the watcher; self-exclusion explains the omission.
o, r = records([C("p2", "sentinel", "watch", "p1"),
                C("p3", "trailseer", "follow", "p2")], mapping)
assert r["p2"].seen == [] and r["p3"].seen == ["p1"]
results["E3_self_exclusion"] = {k: v.seen for k, v in r.items()}

# E3: live conceal suppresses the carrier's destination for BOTH observers.
o, r = records([C("p7", "chanteuse", "kill", "p1"),
                C("p7", "chanteuse", "block", "p10"),
                C("p8", "illusionist", "conceal", None),
                C("p2", "sentinel", "watch", "p1"),
                C("p3", "trailseer", "follow", "p7")], mapping)
assert "p7" not in r["p2"].seen and "p1" not in r["p3"].seen
results["E3_hidden_from_both"] = {k: r[k].seen for k in ("p2", "p3")}

# A34: two destinations identify Chanteuse, but the block can fail on the neutral.
o, r = records([C("p7", "chanteuse", "kill", "p1"),
                C("p7", "chanteuse", "block", "p10"),
                C("p3", "trailseer", "follow", "p7")], mapping)
assert len(r["p3"].seen) == 2 and o.blocked == [] and "p10" in o.blocks_without_effect
results["A34_block_need_not_take"] = {"destinations": r["p3"].seen, "blocked": o.blocked}

# E5: a living necromancer really can claim the reanimated protection it performed.
o, r = records([C("p7", "chanteuse", "kill", "p1"),
                C("p9", "necromancer", "protect", "p1", via="p6")], mapping, night=2)
assert r["p9"].result == "saved" and o.protected_through_body == ["p1"]
results["E5_living_protector"] = r["p9"].outcome

# C20: an unannounced failed sigil still becomes public via a later town will.
choices = [C("p5", "sigilist", "sigil", "p1")]
o, r = records(choices, mapping)
remaining = _spent({"roles": mapping, "uses_left": {"sigilist": 2}}, choices, o)
will = disclosure("p5", "sigilist", list(r.values()))
assert remaining["sigilist"] == 1 and not o.attacks_on and "it had no effect" in will
results["C20_silent_use_later_public"] = will

# C20/C17: published immune shots establish FT self-bets in NE+FT after night 1.
mapping_ft = roles(neutral="fortune_teller")
shots = []
for night in (2, 3):
    o, r = records([C("p4", "vigilante", "kill", "p10"),
                    C("p10", "fortune_teller", "bet", "p10")], mapping_ft, night=night)
    assert r["p4"].result == "immune" and not o.deaths
    shots.append(r["p4"])
results["C20_public_FT_uses"] = disclosure("p4", "vigilante", shots)

# C20: only successful conceals spend; the public hidden-body count is exact.
for protected in (False, True):
    choices = [C("p8", "illusionist", "kill", "p1"), C("p8", "illusionist", "conceal", None)]
    if protected:
        choices.append(C("p6", "healer", "protect", "p1"))
    o, r = records(choices, mapping, night=2)
    remaining = _spent({"roles": mapping, "uses_left": {"illusionist": 2}}, choices, o)
    assert remaining["illusionist"] == 2 - len(o.concealed)
results["C20_conceal_accounting"] = "Exact: remaining = 2 - concealed deaths."


def claim_day(day, result, seen):
    action = ClaimedNightAction(night=1, action="watch", target="p5", result=result,
                               seen=seen, reason="").model_dump()
    return DaySummary(day=day, summary="", structured={"role_claims": [
        {"player": "p2", "claimed_role": "sentinel", "kind": "claimed", "night_actions": [action]}
    ]})


# OQ16: schema-valid positive sightings use not_said, not the illegal token seen.
a = build_claim_ledger([claim_day(2, "not_said", ["p7"]),
                        claim_day(3, "not_said", ["p8"])])["p2"].actions[(1, "watch")]
assert a.seen == ["p8"] and a.earlier == []
results["OQ16_history_still_lost"] = {"seen": a.seen, "earlier": a.earlier}
a = build_claim_ledger([claim_day(2, "no_visitors", []),
                        claim_day(3, "not_said", ["p8"])])["p2"].actions[(1, "watch")]
assert a.result == "no_visitors" and a.seen == ["p8"] and "p8" not in action_text(a)
results["OQ16_empty_to_positive_stale"] = action_text(a)
try:
    claim_day(2, "seen", ["p7"])
except ValidationError:
    results["OQ16_existing_test_result_token"] = "seen is not permitted by ClaimedNightAction"
else:
    raise AssertionError("The schema now allows seen; revisit this finding.")

# B31: the day-limit tiebreak can select a winner before its ordinary condition holds.
state = {"roles": mapping, "lineup": list(mapping.values()),
         "surviving_wolves": ["p7", "p8"],
         "surviving_villagers": [p for p in mapping if p not in ("p7", "p8")]}
assert determine_winner(state) is None and _max_days_winner(state) == "villagers"
results["B31_day_limit"] = {"ordinary_winner": None, "day_limit_winner": "villagers"}
print(json.dumps(results, indent=2))
