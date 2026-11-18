"""The ten-seat game's rules that random play cannot be relied on to reach, with no model.

A borrowed kill, a self-bet, a pick, the uses spent once per night and the like are pinned on
the night layer, the night routing and the resolution node, each on a state built by hand. The
whole games on the real graph are in `test_whole_game.py`.
"""
from __future__ import annotations

from types import SimpleNamespace

from Agents.nodes.night.resolution import night_resolution
from Agents.nodes.orchestrator import acts_tonight, initialize_game, route_night_actors
from Agents.rules.night import resolve_night, usable_bodies
from Agents.rules.night_record import night_action_records
from Agents.schemas.game_events import DeathRecord
from Agents.schemas.metrics import Metrics
from Agents.schemas.night import NightChoice
from Agents.schemas.roles import ALL_LINEUPS
from Agents.turn.resolve import RETRY, night_choice


# --- the rules random play cannot be relied on to reach ----------------------------------------

def _state(game: dict, day: int = 2) -> dict:
    st = initialize_game({}, {"configurable": {"game_id": "rules", "game_config": game}})
    st.update({"current_day": day, "dead_roster": [], "agent_strategies": {}})
    return st


def _holders(st: dict) -> dict[str, str]:
    return {role: player for player, role in st["roles"].items()}


def test_a_borrowed_kill_shows_the_body_and_reads_as_the_body_would():
    st = _state({"lone_killer": "necromancer", "neutral": "speculator"})
    h = _holders(st)
    body = h["illusionist"]
    st["dead_roster"] = [DeathRecord(player=body, role="illusionist", day=1, phase="night")]
    st["surviving_wolves"] = [w for w in st["surviving_wolves"] if w != body]
    assert usable_bodies(st["dead_roster"]) == [body]
    assert acts_tonight(st, "necromancer")
    assert "NECROMANCER_NIGHT_PHASE" in route_night_actors(st)
    choices = [
        NightChoice(h["necromancer"], "necromancer", "kill", h["healer"], via=body),
        NightChoice(h["sentinel"], "sentinel", "watch", h["healer"]),
        NightChoice(h["sigilist"], "sigilist", "sigil", h["necromancer"]),
        NightChoice(h["investigator"], "investigator", "investigate", h["necromancer"]),
    ]
    outcome = resolve_night(choices, st["roles"], 2)
    assert outcome.deaths == [h["healer"]]
    assert outcome.attacks_on[h["healer"]][0].attacker_type == "reanimated_wolves"  # owner 2026-10-10
    assert (body, h["healer"]) in outcome.visits and h["necromancer"] not in outcome.attackers
    assert h["necromancer"] in outcome.suspicious
    records = {r.actor: r for r in night_action_records(choices, outcome, st["roles"])}
    assert records[h["sentinel"]].seen == [body]
    assert records[h["sigilist"]].result == "miss"
    assert records[h["investigator"]].result == "suspicious"
    assert records[h["necromancer"]].seen[0] == body and records[h["necromancer"]].outcome.startswith("Through")


def test_the_necromancer_sits_out_night_one_and_needs_a_body():
    st = _state({"lone_killer": "necromancer", "neutral": "speculator"}, day=1)
    assert not acts_tonight(st, "necromancer")
    st["current_day"] = 2
    assert not acts_tonight(st, "necromancer")  # no body yet
    h = _holders(st)
    st["dead_roster"] = [DeathRecord(player=h["speculator"], role="speculator", day=1, phase="night")]
    assert not acts_tonight(st, "necromancer")  # a neutral's body gives nothing


def test_night_choice_rejects_a_body_not_on_offer():
    st = _state({"lone_killer": "necromancer", "neutral": "speculator"})
    h = _holders(st)
    payload = {"bodies": [h["healer"]], "dead_roster": [DeathRecord(player=h["healer"], role="healer", day=1, phase="night")]}
    valid = [h["sentinel"], "stay_put"]
    good = SimpleNamespace(necromancer_target=h["sentinel"], body=h["healer"])
    choice = night_choice("necromancer", h["necromancer"], good, payload, valid)
    assert choice.kind == "protect" and choice.via == h["healer"]
    bad = SimpleNamespace(necromancer_target=h["sentinel"], body="nobody")
    assert night_choice("necromancer", h["necromancer"], bad, payload, valid) is RETRY
    stay = SimpleNamespace(necromancer_target="stay_put", body="none")
    assert night_choice("necromancer", h["necromancer"], stay, payload, valid) is None


def test_a_self_bet_is_immune_and_scores_nothing_and_a_bet_scores_by_death_and_role():
    st = _state({"lone_killer": "serial_killer", "neutral": "fortune_teller"})
    h = _holders(st)
    choices = [
        NightChoice(h["serial_killer"], "serial_killer", "kill", h["fortune_teller"]),
        NightChoice(h["fortune_teller"], "fortune_teller", "bet", h["fortune_teller"]),
    ]
    outcome = resolve_night(choices, st["roles"], 2)
    assert outcome.verdicts[h["fortune_teller"]] == "immune" and not outcome.bets
    choices = [
        NightChoice(h["chanteuse"], "chanteuse", "kill", h["healer"]),
        NightChoice(h["fortune_teller"], "fortune_teller", "bet", h["healer"], role_named="healer"),
    ]
    outcome = resolve_night(choices, st["roles"], 2)
    assert outcome.bets[0].points == 2
    st["night_choices"] = choices
    runtime = SimpleNamespace(context={"metrics": Metrics()})
    update = night_resolution(st, runtime)
    assert update["fortune_points"] == 2
    assert update["uses_left"]["fortune_teller"] == 2  # a bet on another is not a self-bet
    record = next(r for r in update["night_actions"] if r.actor == h["fortune_teller"])
    assert record.result == "scored_2"


def test_the_pick_is_announced_without_the_seat_and_spent_once():
    st = _state({"lone_killer": "serial_killer", "neutral": "speculator"})
    h = _holders(st)
    assert acts_tonight(st, "speculator")
    st["night_choices"] = [NightChoice(h["speculator"], "speculator", "pick", "wolves")]
    update = night_resolution(st, SimpleNamespace(context={"metrics": Metrics()}))
    assert update["speculator_pick"] == "wolves" and update["uses_left"]["speculator"] == 0
    assert update["night_report"].pick == "wolves"
    message = update["day_channel"][0].message
    assert "The Speculator has picked the Wolves." in message and h["speculator"] not in message
    st.update({"speculator_pick": "wolves", "uses_left": update["uses_left"]})
    assert not acts_tonight(st, "speculator")


def test_uses_are_spent_in_the_resolution_once_per_night_and_a_decline_spends_nothing():
    st = _state({"lone_killer": "serial_killer", "neutral": "speculator"})
    h = _holders(st)
    st["night_choices"] = [
        NightChoice(h["vigilante"], "vigilante", "kill", h["speculator"]),
        NightChoice(h["sigilist"], "sigilist", "sigil", h["healer"]),       # a miss is still spent
        NightChoice(h["illusionist"], "illusionist", "conceal", None),      # no pack kill: kept
    ]
    runtime = SimpleNamespace(context={"metrics": Metrics()})
    once = night_resolution(st, runtime)["uses_left"]
    again = night_resolution(st, runtime)["uses_left"]  # a re-run of the same night
    assert once == again == {"investigator": 2, "sentinel": 2, "vigilante": 1, "sigilist": 1, "illusionist": 2, "speculator": 1}
    st["night_choices"] = [NightChoice(h["vigilante"], "vigilante", "hold_fire", None)]
    held = night_resolution(st, runtime)
    assert held["uses_left"]["vigilante"] == 2
    assert [r.result for r in held["night_actions"] if r.actor == h["vigilante"]] == ["held"]
    # A blocked shot was never fired: the bullet stays (seen in the second live game).
    st["night_choices"] = [
        NightChoice(h["chanteuse"], "chanteuse", "block", h["vigilante"]),
        NightChoice(h["vigilante"], "vigilante", "kill", h["speculator"]),
    ]
    blocked = night_resolution(st, runtime)
    assert blocked["uses_left"]["vigilante"] == 2
    assert [r.result for r in blocked["night_actions"] if r.actor == h["vigilante"]] == ["roleblocked"]


def test_the_night_metric_keeps_what_the_night_decided_and_every_actors_record():
    st = _state({"lone_killer": "serial_killer", "neutral": "speculator"})
    h = _holders(st)
    st["night_choices"] = [
        NightChoice(h["chanteuse"], "chanteuse", "block", h["vigilante"]),
        NightChoice(h["vigilante"], "vigilante", "kill", h["speculator"]),
        NightChoice(h["serial_killer"], "serial_killer", "kill", h["sentinel"]),
        NightChoice(h["sentinel"], "sentinel", "watch", h["healer"]),
    ]
    runtime = SimpleNamespace(context={"metrics": Metrics()})
    night_resolution(st, runtime)
    metric = runtime.context["metrics"].night_resolutions[-1]
    assert metric.outcome["blocked"] == [h["vigilante"]]
    assert metric.outcome["deaths"] == [h["sentinel"]]
    results = {r["actor"]: r["result"] for r in metric.records}
    assert results[h["vigilante"]] == "roleblocked"
    # The sentinel died tonight and is never told its watch, but the record keeps it.
    assert h["sentinel"] in results
    assert metric.model_dump(mode="json")["outcome"]["blocked"] == [h["vigilante"]]


def test_a_dead_player_gets_no_record_of_its_last_night():
    st = _state({"lone_killer": "serial_killer", "neutral": "speculator"})
    h = _holders(st)
    st["night_choices"] = [
        NightChoice(h["serial_killer"], "serial_killer", "kill", h["sentinel"]),
        NightChoice(h["sentinel"], "sentinel", "watch", h["healer"]),
    ]
    update = night_resolution(st, SimpleNamespace(context={"metrics": Metrics()}))
    assert update["dead_roster"][0].player == h["sentinel"]
    assert all(r.actor != h["sentinel"] for r in update["night_actions"])


def test_every_lineup_routes_every_dealt_solo_role_on_night_two():
    for cast in ALL_LINEUPS:
        st = _state({"lone_killer": cast[-2], "neutral": cast[-1]})
        h = _holders(st)
        if "necromancer" in cast:
            st["dead_roster"] = [DeathRecord(player=h["trailseer"], role="trailseer", day=1, phase="night")]
            st["surviving_villagers"] = [p for p in st["surviving_villagers"] if p != h["trailseer"]]
        phases = route_night_actors(st)
        for role in cast:
            if role in ("chanteuse", "illusionist", "trailseer") and "necromancer" in cast and role == "trailseer":
                continue
            if role in ("chanteuse", "illusionist"):
                assert "PACK_NIGHT_PHASE" in phases
            else:
                assert f"{role.upper()}_NIGHT_PHASE" in phases, (cast, role)


# ---- the review of 2026-10-09: what the first wiring got wrong -------------------------------

def test_a_self_bet_is_spent_and_not_offered_once_spent_but_the_bet_goes_on():
    from Agents.turn.action_space import valid_targets_for_action
    st = _state({"lone_killer": "serial_killer", "neutral": "fortune_teller"})
    h = _holders(st)
    st["night_choices"] = [NightChoice(h["fortune_teller"], "fortune_teller", "bet", h["fortune_teller"])]
    update = night_resolution(st, SimpleNamespace(context={"metrics": Metrics()}))
    assert update["uses_left"]["fortune_teller"] == 1
    offered = valid_targets_for_action(
        {"player_id": h["fortune_teller"], "surviving_players": [h["healer"], h["fortune_teller"]], "uses_left": 1},
        "bet_target")
    assert h["fortune_teller"] in offered
    spent = valid_targets_for_action(
        {"player_id": h["fortune_teller"], "surviving_players": [h["healer"], h["fortune_teller"]], "uses_left": 0},
        "bet_target")
    assert spent == [h["healer"]]
    st["uses_left"]["fortune_teller"] = 0
    assert acts_tonight(st, "fortune_teller")  # the ordinary bet is every night


def test_carrying_the_packs_kill_spends_no_conceal():
    st = _state({"lone_killer": "serial_killer", "neutral": "speculator"})
    h = _holders(st)
    runtime = SimpleNamespace(context={"metrics": Metrics()})
    st["night_choices"] = [NightChoice(h["illusionist"], "illusionist", "kill", h["healer"])]
    assert night_resolution(st, runtime)["uses_left"]["illusionist"] == 2
    st["night_choices"] = [
        NightChoice(h["illusionist"], "illusionist", "kill", h["healer"]),
        NightChoice(h["illusionist"], "illusionist", "conceal", None),
    ]
    assert night_resolution(st, runtime)["uses_left"]["illusionist"] == 1


def test_the_conceal_is_a_visit_to_the_packs_victim():
    from Agents.rules.night import visitors_of
    st = _state({"lone_killer": "serial_killer", "neutral": "speculator"})
    h = _holders(st)
    choices = [
        NightChoice(h["chanteuse"], "chanteuse", "kill", h["healer"]),
        NightChoice(h["illusionist"], "illusionist", "conceal", None),
        NightChoice(h["sentinel"], "sentinel", "watch", h["healer"]),
        NightChoice(h["trailseer"], "trailseer", "follow", h["illusionist"]),
    ]
    outcome = resolve_night(choices, st["roles"], 2)
    # The victim died and was concealed: the carrier's visit is hidden, the illusionist's is not.
    assert outcome.concealed == [h["healer"]]
    assert visitors_of(outcome, h["healer"]) == sorted([h["illusionist"], h["sentinel"]],
                                                       key=lambda p: int(p.split("_")[1]))
    records = {r.actor: r for r in night_action_records(choices, outcome, st["roles"])}
    assert records[h["sentinel"]].seen == [h["illusionist"]]
    assert records[h["trailseer"]].seen == [h["healer"]]
    # Saved, nothing is concealed and the carrier's visit is seen as before.
    saved = resolve_night(choices + [NightChoice(h["healer"], "healer", "protect", h["healer"])], st["roles"], 2)
    assert not saved.concealed and h["chanteuse"] in visitors_of(saved, h["healer"])
    # The carrier's other visit stays visible: a trailseer on the carrier sees its block.
    carrier_blocks = [NightChoice(h["chanteuse"], "chanteuse", "kill", h["healer"]),
                      NightChoice(h["chanteuse"], "chanteuse", "block", h["vigilante"]),
                      NightChoice(h["illusionist"], "illusionist", "conceal", None),
                      NightChoice(h["trailseer"], "trailseer", "follow", h["chanteuse"])]
    traced = resolve_night(carrier_blocks, st["roles"], 2)
    trail = next(r for r in night_action_records(carrier_blocks, traced, st["roles"]) if r.actor == h["trailseer"])
    assert trail.seen == [h["vigilante"]]
    # Blocked, the illusionist went nowhere.
    choices.append(NightChoice(h["chanteuse"], "chanteuse", "block", h["illusionist"]))
    assert h["illusionist"] not in visitors_of(resolve_night(choices, st["roles"], 2), h["healer"])


def test_the_whole_pack_learns_the_role_the_illusionist_hid():
    # Owner, 2026-10-17: the pack's record (every wolf's) names the concealed role.
    st = _state({"lone_killer": "serial_killer", "neutral": "speculator"})
    h = _holders(st)
    choices = [
        NightChoice(h["chanteuse"], "chanteuse", "kill", h["healer"]),
        NightChoice(h["illusionist"], "illusionist", "conceal", None),
    ]
    pack = next(r for r in night_action_records(choices, resolve_night(choices, st["roles"], 2), st["roles"])
                if r.actor == "wolves")
    assert pack.result == "killed" and pack.seen == ["healer"]
    assert pack.outcome == f"{h['healer']} died, and the illusionist hid their role: they were a healer."
    # No conceal: the role is public, and the record says it as before.
    plain = night_action_records(choices[:1], resolve_night(choices[:1], st["roles"], 2), st["roles"])[0]
    assert plain.seen == [] and plain.outcome == f"{h['healer']} died. They were a healer."


def test_a_clean_through_the_illusionists_body_is_not_told_to_the_pack():
    st = _state({"lone_killer": "necromancer", "neutral": "speculator"}, day=3)
    h = _holders(st)
    choices = [
        NightChoice(h["chanteuse"], "chanteuse", "kill", h["healer"]),
        NightChoice(h["necromancer"], "necromancer", "kill", h["healer"], via=h["illusionist"]),
    ]
    outcome = resolve_night(choices, st["roles"], 3, body_conceals=1)
    assert outcome.concealed == [h["healer"]]
    pack = next(r for r in night_action_records(choices, outcome, st["roles"]) if r.actor == "wolves")
    assert pack.seen == [] and pack.outcome == f"{h['healer']} died. Their role was concealed."


def test_a_wolfs_skill_turn_is_stamped_with_its_own_round():
    from Agents.nodes.night.pack import CARRIER_ROUND, SKILL_ROUND, pack_fan_out_skills
    st = _state({"lone_killer": "serial_killer", "neutral": "speculator"})
    pack = {**st, "current_round": CARRIER_ROUND, "carrier": st["surviving_wolves"][0],
            "wolves_target": st["surviving_villagers"][0], "wolf_channel": [], "human_players": []}
    sends = pack_fan_out_skills(pack)
    assert SKILL_ROUND != CARRIER_ROUND
    assert [s.arg["current_round"] for s in sends] == [SKILL_ROUND, SKILL_ROUND]


def test_a_sigil_on_an_immune_attacker_reads_as_a_miss_and_is_spent():
    st = _state({"lone_killer": "serial_killer", "neutral": "speculator"})
    h = _holders(st)
    choices = [
        NightChoice(h["serial_killer"], "serial_killer", "kill", h["healer"]),
        NightChoice(h["sigilist"], "sigilist", "sigil", h["serial_killer"]),
    ]
    outcome = resolve_night(choices, st["roles"], 2)
    assert outcome.verdicts[h["serial_killer"]] == "immune"
    record = next(r for r in night_action_records(choices, outcome, st["roles"]) if r.actor == h["sigilist"])
    assert (record.result, record.outcome) == ("miss", "Your sigil had no effect.")
    quiet = resolve_night(choices[1:], st["roles"], 2)  # the same words as a night nobody attacked
    quiet_record = next(r for r in night_action_records(choices[1:], quiet, st["roles"]))
    assert (quiet_record.result, quiet_record.outcome) == (record.result, record.outcome)
    st["night_choices"] = choices
    update = night_resolution(st, SimpleNamespace(context={"metrics": Metrics()}))
    assert update["uses_left"]["sigilist"] == 1
    assert h["serial_killer"] not in update["day_channel"][0].message  # nothing public either


def test_checks_and_watches_are_capped_and_a_kept_one_spends_nothing():
    from Agents.turn.action_space import valid_targets_for_action
    st = _state({"lone_killer": "serial_killer", "neutral": "speculator"})
    h = _holders(st)
    assert st["uses_left"]["investigator"] == 2 and st["uses_left"]["sentinel"] == 2
    assert valid_targets_for_action({"player_id": h["investigator"], "surviving_players": [h["healer"]]},
                                    "investigator_target")[-1] == "no_check"
    runtime = SimpleNamespace(context={"metrics": Metrics()})
    st["night_choices"] = [
        NightChoice(h["investigator"], "investigator", "investigate", h["chanteuse"]),
        NightChoice(h["sentinel"], "sentinel", "watch", h["healer"]),
    ]
    update = night_resolution(st, runtime)
    assert update["uses_left"]["investigator"] == 1 and update["uses_left"]["sentinel"] == 1
    assert night_choice("investigator", h["investigator"], SimpleNamespace(investigator_target="no_check", body=None, bet_role="none"),
                        {"player_id": h["investigator"]}, [h["healer"], "no_check"]) is None
    st["uses_left"].update({"investigator": 0, "sentinel": 0})
    assert not acts_tonight(st, "investigator") and not acts_tonight(st, "sentinel")


def test_the_necromancer_may_use_the_same_body_night_after_night():
    st = _state({"lone_killer": "necromancer", "neutral": "speculator"}, day=3)
    h = _holders(st)
    body = DeathRecord(player=h["illusionist"], role="illusionist", day=1, phase="night")
    assert usable_bodies([body]) == [h["illusionist"]]
    st["dead_roster"] = [body]
    st["night_choices"] = [NightChoice(h["necromancer"], "necromancer", "kill", h["healer"], via=h["illusionist"])]
    update = night_resolution(st, SimpleNamespace(context={"metrics": Metrics()}))
    assert "last_body" not in update
    st.update({"current_day": 4, "dead_roster": st["dead_roster"] + update["dead_roster"]})
    assert acts_tonight(st, "necromancer") and h["illusionist"] in usable_bodies(st["dead_roster"])


def test_a_borrowed_kill_on_the_packs_victim_names_the_wolves_and_a_reanimated_corpse():
    st = _state({"lone_killer": "necromancer", "neutral": "speculator"}, day=3)
    h = _holders(st)
    st["dead_roster"] = [DeathRecord(player=h["illusionist"], role="illusionist", day=1, phase="night")]
    st["night_choices"] = [
        NightChoice(h["chanteuse"], "chanteuse", "kill", h["healer"]),
        NightChoice(h["necromancer"], "necromancer", "kill", h["healer"], via=h["illusionist"]),
    ]
    update = night_resolution(st, SimpleNamespace(context={"metrics": Metrics()}))
    message = update["day_channel"][0].message
    assert f"{h['healer']} was attacked by the wolves and a reanimated wolf last night." in message
    assert update["night_report"].deaths == [(h["healer"], "", ["wolves", "reanimated_wolves"])]  # cleaned
    # alone, with the illusionist's conceals spent, a borrowed kill is a reanimated wolf's
    st["night_choices"] = st["night_choices"][1:]
    st["uses_left"]["illusionist"] = 0
    alone = night_resolution(st, SimpleNamespace(context={"metrics": Metrics()}))
    assert f"{h['healer']} was killed by a reanimated wolf last night. They were a healer." in alone["day_channel"][0].message


def test_a_kill_through_the_illusionists_body_cleans_and_the_necromancer_learns_the_role():
    st = _state({"lone_killer": "necromancer", "neutral": "speculator"}, day=3)
    h = _holders(st)
    st["dead_roster"] = [DeathRecord(player=h["illusionist"], role="illusionist", day=1, phase="night")]
    st["uses_left"]["illusionist"] = 1
    st["night_choices"] = [NightChoice(h["necromancer"], "necromancer", "kill", h["healer"], via=h["illusionist"])]
    update = night_resolution(st, SimpleNamespace(context={"metrics": Metrics()}))
    assert (f"{h['healer']} was killed by a reanimated wolf last night. Their role is hidden by a reanimated "
            "illusionist.") in update["day_channel"][0].message
    assert update["dead_roster"][0].concealed and update["uses_left"]["illusionist"] == 0
    record = next(r for r in update["night_actions"] if r.actor == h["necromancer"])
    assert record.outcome.endswith(f"{h['healer']} died, and you hid their role: they were a healer.")
    # a vigilante's body gives a plain shot, named as the vigilante's, reanimated
    st.update({"dead_roster": [DeathRecord(player=h["vigilante"], role="vigilante", day=1, phase="night")],
               "night_choices": [NightChoice(h["necromancer"], "necromancer", "kill", h["healer"], via=h["vigilante"])]})
    shot = night_resolution(st, SimpleNamespace(context={"metrics": Metrics()}))
    assert f"{h['healer']} was shot by a reanimated vigilante last night. They were a healer." in shot["day_channel"][0].message


def test_an_illusionist_that_carries_and_conceals_leaves_no_trace_at_that_door():
    from Agents.rules.night import visitors_of
    st = _state({"lone_killer": "serial_killer", "neutral": "speculator"})
    h = _holders(st)
    choices = [
        NightChoice(h["illusionist"], "illusionist", "kill", h["investigator"]),
        NightChoice(h["illusionist"], "illusionist", "conceal", None),
        NightChoice(h["sentinel"], "sentinel", "watch", h["investigator"]),
        NightChoice(h["trailseer"], "trailseer", "follow", h["illusionist"]),
    ]
    outcome = resolve_night(choices, st["roles"], 2)
    assert outcome.concealed == [h["investigator"]]
    assert h["illusionist"] not in visitors_of(outcome, h["investigator"])
    records = {r.actor: r for r in night_action_records(choices, outcome, st["roles"])}
    assert records[h["sentinel"]].seen == [] and records[h["trailseer"]].seen == []
    # saved, nothing is concealed, so the carrier is seen as usual
    saved = resolve_night(choices + [NightChoice(h["healer"], "healer", "protect", h["investigator"])], st["roles"], 2)
    assert h["illusionist"] in visitors_of(saved, h["investigator"])


def test_a_save_through_the_healers_body_is_announced_as_a_reanimated_healer():
    # Owner, 2026-10-16: there is one healer, so once it is dead a save is the necromancer's, and the
    # morning names it as it names a reanimated attack.
    st = _state({"lone_killer": "necromancer", "neutral": "speculator"}, day=3)
    h = _holders(st)
    st["dead_roster"] = [DeathRecord(player=h["healer"], role="healer", day=1, phase="night")]
    st["night_choices"] = [
        NightChoice(h["chanteuse"], "chanteuse", "kill", h["sentinel"]),
        NightChoice(h["necromancer"], "necromancer", "protect", h["sentinel"], via=h["healer"]),
        NightChoice(h["vigilante"], "vigilante", "kill", h["sentinel"]),
    ]
    update = night_resolution(st, SimpleNamespace(context={"metrics": Metrics()}))
    message = update["day_channel"][0].message
    assert f"{h['sentinel']} was attacked by the wolves and the vigilante but was saved by a reanimated healer!" in message
    assert "saved by the healer" not in message
    assert update["night_report"].reanimated_saves == [h["sentinel"]]
    shot = next(r for r in update["night_actions"] if r.actor == h["vigilante"])
    assert shot.outcome == f"{h['sentinel']} survived: a reanimated healer saved them."


def test_a_living_healers_save_still_names_the_healer():
    st = _state({"lone_killer": "serial_killer", "neutral": "speculator"})
    h = _holders(st)
    st["night_choices"] = [
        NightChoice(h["chanteuse"], "chanteuse", "kill", h["sentinel"]),
        NightChoice(h["healer"], "healer", "protect", h["sentinel"]),
    ]
    update = night_resolution(st, SimpleNamespace(context={"metrics": Metrics()}))
    assert f"{h['sentinel']} was attacked by the wolves but was saved by the healer!" in update["day_channel"][0].message
    assert update["night_report"].reanimated_saves == []


# ---- R10 (owner, 2026-10-17): an attack the fortune teller's self-bet stopped is announced ----

def test_an_attack_a_self_bet_stopped_is_announced_and_every_record_says_so():
    st = _state({"lone_killer": "serial_killer", "neutral": "fortune_teller"})
    h = _holders(st)
    ft = h["fortune_teller"]
    st["night_choices"] = [
        NightChoice(h["chanteuse"], "chanteuse", "kill", ft),
        NightChoice(h["serial_killer"], "serial_killer", "kill", ft),
        NightChoice(ft, "fortune_teller", "bet", ft),
        NightChoice(h["healer"], "healer", "protect", ft),
    ]
    update = night_resolution(st, SimpleNamespace(context={"metrics": Metrics()}))
    assert update["day_channel"][0].message == (
        f"Night of day 2: {ft} was attacked by the wolves and the serial killer but survived: the fortune "
        f"teller's self-bet saved them.")
    report = update["night_report"]
    assert report.saves == [(ft, ["wolves", "serial_killer"])] and report.deaths == []
    assert report.self_bet_saves == [ft] and report.reanimated_saves == []
    records = {r.actor: r for r in update["night_actions"]}
    assert (records["wolves"].result, records["wolves"].outcome) == (
        "self_bet_saved", f"{ft} survived: the fortune teller's self-bet saved them.")
    assert records[h["serial_killer"]].result == "self_bet_saved"
    assert (records[h["healer"]].result, records[h["healer"]].outcome) == (
        "self_bet_saved", f"{ft} was attacked by the wolves and the serial killer and survived: the fortune "
                          f"teller's self-bet saved them, not your protection.")
    assert (records[ft].result, records[ft].outcome) == (
        "self_bet", "You bet on yourself and were attacked by the wolves and the serial killer: your self-bet "
                    "saved you, and the morning announces it.")
    assert update["uses_left"]["fortune_teller"] == 1


def test_a_self_bet_with_no_attack_on_it_is_silent():
    st = _state({"lone_killer": "serial_killer", "neutral": "fortune_teller"})
    h = _holders(st)
    ft = h["fortune_teller"]
    st["night_choices"] = [NightChoice(ft, "fortune_teller", "bet", ft),
                           NightChoice(h["healer"], "healer", "protect", ft)]
    update = night_resolution(st, SimpleNamespace(context={"metrics": Metrics()}))
    assert update["day_channel"][0].message == "Night of day 2: No one died last night."
    assert update["night_report"].saves == [] and update["night_report"].self_bet_saves == []
    records = {r.actor: r for r in update["night_actions"]}
    assert (records[ft].result, records[ft].outcome) == (
        "self_bet", "You bet on yourself. No one attacked you tonight, and nothing is scored.")
    assert (records[h["healer"]].result, records[h["healer"]].outcome) == (
        "no_attack", f"No attack on {ft} was announced.")


def test_the_serial_killers_immunity_stays_silent_beside_a_self_bet():
    st = _state({"lone_killer": "serial_killer", "neutral": "fortune_teller"})
    h = _holders(st)
    ft, killer = h["fortune_teller"], h["serial_killer"]
    st["night_choices"] = [
        NightChoice(h["vigilante"], "vigilante", "kill", killer),
        NightChoice(ft, "fortune_teller", "bet", ft),
        NightChoice(killer, "serial_killer", "kill", h["healer"]),
    ]
    update = night_resolution(st, SimpleNamespace(context={"metrics": Metrics()}))
    message = update["day_channel"][0].message
    assert killer not in message and "self-bet" not in message
    assert update["night_report"].self_bet_saves == []
    shot = next(r for r in update["night_actions"] if r.actor == h["vigilante"])
    assert (shot.result, shot.outcome) == (
        "immune", f"{killer} was unharmed: immune to night kills tonight. The public was told nothing about "
                  "this attack.")


def test_a_reanimated_attack_on_a_self_betting_fortune_teller_is_announced_too():
    st = _state({"lone_killer": "necromancer", "neutral": "fortune_teller"}, day=3)
    h = _holders(st)
    ft, body = h["fortune_teller"], h["illusionist"]
    st["dead_roster"] = [DeathRecord(player=body, role="illusionist", day=1, phase="night")]
    st["surviving_wolves"] = [w for w in st["surviving_wolves"] if w != body]
    st["night_choices"] = [
        NightChoice(h["necromancer"], "necromancer", "kill", ft, via=body),
        NightChoice(ft, "fortune_teller", "bet", ft),
    ]
    update = night_resolution(st, SimpleNamespace(context={"metrics": Metrics()}))
    assert (f"{ft} was attacked by a reanimated wolf but survived: the fortune teller's self-bet saved them."
            in update["day_channel"][0].message)
    record = next(r for r in update["night_actions"] if r.actor == h["necromancer"])
    assert (record.result, record.outcome) == (
        "self_bet_saved", f"Through {body}'s body: {ft} survived: the fortune teller's self-bet saved them.")


def test_a_protection_through_the_healers_body_on_a_self_betting_fortune_teller_is_not_a_reanimated_save():
    st = _state({"lone_killer": "necromancer", "neutral": "fortune_teller"}, day=3)
    h = _holders(st)
    ft = h["fortune_teller"]
    st["dead_roster"] = [DeathRecord(player=h["healer"], role="healer", day=1, phase="night")]
    st["night_choices"] = [
        NightChoice(h["chanteuse"], "chanteuse", "kill", ft),
        NightChoice(ft, "fortune_teller", "bet", ft),
        NightChoice(h["necromancer"], "necromancer", "protect", ft, via=h["healer"]),
    ]
    update = night_resolution(st, SimpleNamespace(context={"metrics": Metrics()}))
    message = update["day_channel"][0].message
    assert "reanimated healer" not in message and "the fortune teller's self-bet saved them" in message
    assert update["night_report"].self_bet_saves == [ft] and update["night_report"].reanimated_saves == []
    record = next(r for r in update["night_actions"] if r.actor == h["necromancer"])
    assert record.result == "self_bet_saved" and record.outcome.endswith("not your protection.")


def test_the_will_tells_a_self_bet_save_in_its_own_words():
    from Agents.rules.night_record import disclosure
    st = _state({"lone_killer": "serial_killer", "neutral": "fortune_teller"})
    h = _holders(st)
    ft = h["fortune_teller"]
    choices = [NightChoice(h["vigilante"], "vigilante", "kill", ft),
               NightChoice(ft, "fortune_teller", "bet", ft),
               NightChoice(h["healer"], "healer", "protect", ft)]
    records = night_action_records(choices, resolve_night(choices, st["roles"], 2), st["roles"])
    assert disclosure(h["vigilante"], "vigilante", records) == (
        f"The record of {h['vigilante']}, the vigilante: night 2, shot {ft}, who was saved by the fortune "
        "teller's self-bet.")
    assert disclosure(h["healer"], "healer", records) == (
        f"The record of {h['healer']}, the healer: night 2, protected {ft}, who was attacked and saved by the "
        "fortune teller's self-bet.")


def test_a_clean_through_the_illusionists_body_leaves_the_carriers_visit_seen():
    # Owner, 2026-10-16: only the living illusionist's conceal hides the pack carrier's visit.
    from Agents.rules.night import visitors_of
    st = _state({"lone_killer": "necromancer", "neutral": "speculator"}, day=3)
    h = _holders(st)
    choices = [
        NightChoice(h["chanteuse"], "chanteuse", "kill", h["healer"]),
        NightChoice(h["necromancer"], "necromancer", "kill", h["healer"], via=h["illusionist"]),
        NightChoice(h["sentinel"], "sentinel", "watch", h["healer"]),
    ]
    outcome = resolve_night(choices, st["roles"], 3, body_conceals=1)
    assert outcome.concealed == [h["healer"]]
    assert set(visitors_of(outcome, h["healer"])) >= {h["chanteuse"], h["illusionist"]}
    records = {r.actor: r for r in night_action_records(choices, outcome, st["roles"])}
    assert h["chanteuse"] in records[h["sentinel"]].seen
