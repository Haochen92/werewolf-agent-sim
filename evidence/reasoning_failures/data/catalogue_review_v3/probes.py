"""Third catalogue review: deterministic probes, no model calls.

Run from repository root:
    PYTHONPATH=. poetry run python evidence/reasoning_failures/data/catalogue_review_v3/probes.py

These isolate legal night interactions; they do not simulate complete game histories.
Assertions document the reviewed working tree, including one remaining ledger bug.
"""
import json

from Agents.nodes.night.resolution import _spent
from Agents.rules.claim_ledger import action_text, build_claim_ledger
from Agents.rules.night import resolve_night
from Agents.rules.night_record import disclosure, night_action_records
from Agents.schemas.game_events import DaySummary
from Agents.schemas.night import NightChoice as C
from Agents.schemas.output import ClaimedNightAction
from Agents.schemas.roles import lineup


mapping = {f"p{i}": role for i, role in enumerate(lineup("necromancer", "speculator"), 1)}
results = {}

# Vigilante is already revealed dead; the necromancer shoots through that body.
choices = [C("p9", "necromancer", "kill", "p1", via="p4")]
outcome = resolve_night(choices, mapping, 2)
assert outcome.verdicts["p1"] == "killed" and not outcome.blocked
types = [a.attacker_type for a in outcome.attacks_on["p1"]]
assert types == ["reanimated_vigilante"]
results["E8a_borrowed_shot"] = {"attack_types": types, "verdict": outcome.verdicts["p1"]}

# Illusionist is already revealed dead with two conceals remaining.
choices = [C("p9", "necromancer", "kill", "p1", via="p8")]
outcome = resolve_night(choices, mapping, 2, body_conceals=2)
uses = _spent({"roles": mapping, "uses_left": {"illusionist": 2}}, choices, outcome)
assert outcome.concealed == ["p1"] and uses["illusionist"] == 1
results["C20_borrowed_action_spends_conceal"] = uses

# Night 1's carrier is p7. Its block fails on the speculator, yet BOTH visits
# to that same concealed victim disappear from a follow.
choices = [C("p7", "chanteuse", "kill", "p10"),
           C("p7", "chanteuse", "block", "p10"),
           C("p8", "illusionist", "conceal", None),
           C("p3", "trailseer", "follow", "p7")]
outcome = resolve_night(choices, mapping, 1)
records = {r.actor: r for r in night_action_records(choices, outcome, mapping)}
assert outcome.blocks_without_effect == ["p10"] and not outcome.blocked
assert outcome.concealed == ["p10"] and records["p3"].seen == []
results["A35_invisible_failed_block"] = records["p3"].outcome

# Missing clauses in a COMPLETE town disclosure exclude completed uses on
# nights the holder survived. N1 was declined (no choice), N2 was a quiet sigil.
choices = [C("p5", "sigilist", "sigil", "p1")]
outcome = resolve_night(choices, mapping, 2)
records = night_action_records(choices, outcome, mapping)
will = disclosure("p5", "sigilist", records)
assert "night 1" not in will and "night 2" in will and "no effect" in will
uses = _spent({"roles": mapping, "uses_left": {"sigilist": 2}}, choices, outcome)
assert uses["sigilist"] == 1
results["L11_complete_will_accounts_for_quiet_uses"] = will


def claim_day(day, night, seen):
    action = ClaimedNightAction(night=night, action="watch", target="p5", result="not_said",
                               seen=seen, reason="").model_dump()
    return DaySummary(day=day, summary="", structured={"role_claims": [
        {"player": "p2", "claimed_role": "sentinel", "kind": "claimed", "night_actions": [action]}
    ]})


# The two specifically reported OQ16 cases are now fixed.
claims = build_claim_ledger([claim_day(2, 1, ["p7"]), claim_day(3, 1, ["p8"])])["p2"]
action = claims.actions[(1, "watch")]
assert action.seen == ["p8"] and len(action.earlier) == 1
results["OQ16_named_correction_fixed"] = {"current": action_text(action), "earlier": action.earlier}

# A different path still loses information: date an undated sighting without
# restating its visitor. The code merges the entries but drops the sighting.
claims = build_claim_ledger([claim_day(2, 0, ["p7"]), claim_day(3, 1, [])])["p2"]
assert len(claims.actions) == 1
action = claims.actions[(1, "watch")]
assert action.seen == [] and action.earlier == []
results["OQ16_dating_loses_sighting"] = action_text(action)

# A borrowed watch's raw seen list contains body metadata, not just visitors.
choices = [C("p9", "necromancer", "watch", "p1", via="p2")]
outcome = resolve_night(choices, mapping, 2)
record = night_action_records(choices, outcome, mapping)[0]
assert record.seen == ["p2"] and "No one visited" in record.outcome
results["L12_borrowed_watch_needs_normalization"] = {"raw_seen": record.seen, "text": record.outcome}

print(json.dumps(results, indent=2))
