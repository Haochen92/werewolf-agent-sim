"""Logic tests for the whiff-conversion audit (synthetic fixtures, no LLM, no batch files).

Covers the pre-registered whiff detection (SK-whiff vs healed split, both attackers), the
dedup-by-(attacker, target) rule, the Layer-2 conversion join (accuse / vote / pre-baseline /
night re-target), the Layer-3 floor count, and the reasoning-scan keyword matcher.
"""

from __future__ import annotations

from evaluation.src.experiments.whiff_conversion_audit import (
    _field_matches,
    conversion_for_event,
    dedup_events,
    floor_for_event,
    target_survived_events,
)

ROLES = {
    "player_1": "wolf", "player_2": "wolf", "player_3": "serial_killer",
    "player_4": "villager", "player_5": "healer", "player_6": "investigator",
    "player_7": "vigilante", "player_8": "villager", "player_9": "villager",
}


def _nr(**kw):
    base = dict(day=1, wolves_target=None, wolf_target_role=None, healer_target=None,
                healer_saved=False, serial_killer_target=None, vigilante_target=None,
                vigilante_target_role=None, vigilante_kill_landed=False, deaths=[])
    base.update(kw)
    return base


def _msg(player, day, seq, targets=None, passed=False):
    return {"player": player, "day": day, "seq": seq, "passed": passed,
            "addressed_targets": targets or [], "firing_reason": {"tier": "proactive"}, "message": ""}


def _rec(nights, day_channel=None, day_resolutions=None):
    return {"status": "success", "roles": ROLES, "night_resolutions": nights,
            "day_channel": day_channel or [], "day_resolutions": day_resolutions or []}


# --------------------------------------------------------------------------- detection


def test_wolf_whiff_on_sk_detected():
    rec = _rec([_nr(day=1, wolves_target="player_3", wolf_target_role="serial_killer", deaths=[])])
    evs = target_survived_events(rec)
    assert len(evs) == 1
    assert evs[0]["attacker"] == "wolf" and evs[0]["ground_truth"] == "sk_whiff"
    assert evs[0]["target"] == "player_3" and evs[0]["night"] == 1


def test_wolf_healed_survival_detected():
    rec = _rec([_nr(day=1, wolves_target="player_4", wolf_target_role="villager",
                    healer_target="player_4", healer_saved=True, deaths=[])])
    evs = target_survived_events(rec)
    assert len(evs) == 1 and evs[0]["ground_truth"] == "healed" and evs[0]["target"] == "player_4"


def test_successful_kill_is_not_an_event():
    rec = _rec([_nr(day=1, wolves_target="player_4", wolf_target_role="villager", deaths=["player_4"])])
    assert target_survived_events(rec) == []


def test_sk_check_precedes_heal():
    # Wolf hits SK who is ALSO healed → still classified sk_whiff (immunity resolves first).
    rec = _rec([_nr(day=1, wolves_target="player_3", wolf_target_role="serial_killer",
                    healer_target="player_3", healer_saved=True, deaths=[])])
    assert target_survived_events(rec)[0]["ground_truth"] == "sk_whiff"


def test_vigilante_whiff_and_healed():
    rec = _rec([
        _nr(day=1, vigilante_target="player_3", vigilante_target_role="serial_killer",
            vigilante_kill_landed=False, deaths=[]),
        _nr(day=2, vigilante_target="player_4", vigilante_target_role="villager",
            healer_target="player_4", vigilante_kill_landed=False, deaths=[]),
    ])
    evs = target_survived_events(rec)
    kinds = {(e["attacker"], e["night"]): e["ground_truth"] for e in evs}
    assert kinds[("vigilante", 1)] == "sk_whiff"
    assert kinds[("vigilante", 2)] == "healed"


# --------------------------------------------------------------------------- dedup


def test_dedup_keeps_earliest_per_target():
    rec = _rec([
        _nr(day=2, wolves_target="player_3", wolf_target_role="serial_killer", deaths=[]),
        _nr(day=1, wolves_target="player_3", wolf_target_role="serial_killer", deaths=[]),
    ])
    deduped = dedup_events(target_survived_events(rec))
    assert len(deduped) == 1 and deduped[0]["night"] == 1


# --------------------------------------------------------------------------- conversion join


def _conversion_rec():
    nights = [
        _nr(day=1, wolves_target="player_3", wolf_target_role="serial_killer", deaths=[]),
        _nr(day=2, wolves_target="player_3", wolf_target_role="serial_killer", deaths=[]),  # re-target
    ]
    day_channel = [
        # pre-whiff day 1: wolf accuses an OTHER player, not the SK
        _msg("player_1", 1, 0, targets=[{"target": "player_8", "stance": "accusation"}]),
        # post-whiff day 2: wolf_1 accuses the SK
        _msg("player_1", 2, 0, targets=[{"target": "player_3", "stance": "accusation"}]),
    ]
    day_resolutions = [
        {"day": 2, "votes": [{"voter": "player_2", "votee": "player_3"}]},
    ]
    return _rec(nights, day_channel, day_resolutions)


def test_conversion_accuse_vote_retarget():
    rec = _conversion_rec()
    ev = dedup_events(target_survived_events(rec))[0]
    assert ev["night"] == 1
    conv = conversion_for_event(rec, ev, {2: rec["day_resolutions"][0]["votes"]})
    assert conv["converted"] is True
    assert conv["post_accused"] is True      # player_1 accused SK on day 2
    assert conv["post_voted"] is True        # player_2 voted SK on day 2
    assert conv["pre_target_directed"] is False  # no SK-directed action on day <= 1
    assert conv["post_accused_other"] is False   # day-2 (post) accusation was the SK only; player_8 was day 1 (pre)
    assert conv["night_retarget"] is True    # wolves hit SK again on night 2
    assert conv["kept_killing_others"] is False


def test_no_conversion_when_wolf_silent_on_target():
    nights = [_nr(day=1, wolves_target="player_3", wolf_target_role="serial_killer", deaths=[])]
    # wolf only accuses a different player after the whiff
    day_channel = [_msg("player_1", 2, 0, targets=[{"target": "player_8", "stance": "accusation"}])]
    rec = _rec(nights, day_channel, [{"day": 2, "votes": []}])
    ev = dedup_events(target_survived_events(rec))[0]
    conv = conversion_for_event(rec, ev, {2: []})
    assert conv["converted"] is False
    assert conv["post_accused_other"] is True  # accused someone, just not the SK


# --------------------------------------------------------------------------- floor


def test_floor_counts_nonpass_and_passes():
    nights = [_nr(day=1, wolves_target="player_3", wolf_target_role="serial_killer", deaths=[])]
    day_channel = [
        _msg("player_1", 2, 0),                 # real turn
        _msg("player_2", 2, 1, passed=True),    # declined offer
    ]
    rec = _rec(nights, day_channel)
    ev = dedup_events(target_survived_events(rec))[0]
    fl = floor_for_event(rec, ev)
    assert fl["nonpass_turns"] == 1 and fl["passes"] == 1 and fl["had_floor"] is True


# --------------------------------------------------------------------------- reasoning matcher


def test_field_matcher_requires_name_and_inference_token():
    assert _field_matches("player_3 seems immune to night kills", "player_3") is True
    assert _field_matches("no one died last night, player 3 is suspicious", "player_3") is True
    assert _field_matches("I will vote player_3 today", "player_3") is False   # no inference token
    assert _field_matches("player_5 survived the night", "player_3") is False  # wrong player
