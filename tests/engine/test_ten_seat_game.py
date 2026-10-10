"""The ten-seat game, end to end and rule by rule, with no model.

A whole game runs on the real parent graph with a scripted model that fills whatever schema it
is bound to, streamed through the server's translator and the pacing units, for both drawn
lineups. The rules the random play cannot be relied on to reach (a borrowed kill, a self-bet, a
pick, the uses spent once per night) are pinned on the night layer and the resolution node.
"""
from __future__ import annotations

import random
import typing
from types import SimpleNamespace

import pytest
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel
from pydantic_core import to_jsonable_python

from Agents.config import RunConfig, build_runnable_config, normalize_run_config
from Agents.graphs.parent import parent_graph_compiled
from Agents.nodes.day import flow
from Agents.nodes.night.resolution import night_resolution
from Agents.nodes.orchestrator import acts_tonight, initialize_game, route_night_actors
from Agents.rules.night import resolve_night, usable_bodies
from Agents.rules.night_record import night_action_records
from Agents.schemas.game_events import DeathRecord
from Agents.schemas.metrics import Metrics
from Agents.schemas.night import NightChoice
from Agents.schemas.roles import ALL_LINEUPS, lineup
from Agents.state import fresh_game_state
from Agents.turn import agent_player, resolve
from Agents.turn.resolve import RETRY, night_choice
from server.game.pacing import BRANCH_UNITS
from server.game.translate import Translator


# --- a scripted model -------------------------------------------------------------------------

def _fill(schema: type[BaseModel], rng: random.Random) -> BaseModel:
    """Any schema, filled: a Literal gets one of its values, so a target is always legal."""
    values = {}
    for name, field in schema.model_fields.items():
        ann, origin = field.annotation, typing.get_origin(field.annotation)
        if origin is typing.Literal:
            values[name] = rng.choice(typing.get_args(ann))
        elif ann is bool:
            values[name] = False
        elif ann is str:
            values[name] = "a line" if name == "message" else ("none" if name == "bet_role" else "x")
        elif ann is int:
            values[name] = 1
        elif origin is list or ann is list:
            item = typing.get_args(ann)[0] if typing.get_args(ann) else None
            # One read, built from the lineup's own read class, so the effects must accept it.
            values[name] = [_fill(item, rng).model_dump()] if name == "reads" and item is not None else []
        else:
            values[name] = None
    if "pass_turn" in values and rng.random() < 0.6:
        values["pass_turn"], values["message"] = True, ""
    return schema.model_validate(values)


class _FakeLLM:
    model = "fake"

    def __init__(self, rng):
        self.rng = rng

    def with_structured_output(self, schema, **kwargs):
        return RunnableLambda(lambda prompt: _fill(schema, self.rng))


def _play(monkeypatch, game: dict, seed: int) -> tuple[dict, list, set[str]]:
    rng = random.Random(seed)
    monkeypatch.setattr(agent_player, "get_llm", lambda: _FakeLLM(rng))
    monkeypatch.setattr(agent_player, "get_llm_game_fallback", lambda: None)
    monkeypatch.setattr(flow, "run_day_summary_agent", lambda day, messages, max_retries=1, **kw: ("summary", "fake", {}))
    monkeypatch.setattr(flow, "filter_openings", lambda entries: entries)
    monkeypatch.setattr(resolve, "line_echo_of", lambda message, player, earlier: "")
    # One thread per game: the checkpointer keys on the game id, and a second game under the same
    # id resumes on top of the first's final state (the add-reduced lists accumulate).
    game_id = f"offline-{game['lone_killer']}-{game['neutral']}-{seed}"
    run = normalize_run_config(RunConfig(game_id=game_id, game=game, memory_persistence={"dump_enabled": False}))
    config = build_runnable_config(run)
    context = {"metrics": Metrics(), "eval_sink": None}
    translator, events, units = Translator(), [], set()
    for part in parent_graph_compiled.stream(fresh_game_state(), config=config, context=context,
                                             stream_mode=["updates", "custom"], subgraphs=True, version="v2"):
        chunk = {"type": part["type"], "ns": list(part["ns"]), "data": to_jsonable_python(part["data"])}
        events.extend(translator.translate(chunk))
        if chunk["type"] == "updates" and not chunk["ns"]:
            units |= {BRANCH_UNITS[n] for n in chunk["data"] if n in BRANCH_UNITS}
    return parent_graph_compiled.get_state(config).values, events, units


@pytest.mark.parametrize("game", [
    {"lone_killer": "serial_killer", "neutral": "speculator"},
    {"lone_killer": "necromancer", "neutral": "fortune_teller"},
])
def test_a_whole_game_runs_on_the_real_graph_and_the_wire_accepts_every_chunk(monkeypatch, game):
    result, events, units = _play(monkeypatch, game, seed=3)
    assert result["lineup"] == lineup(game["lone_killer"], game["neutral"])
    assert result["winner"] in ("villagers", "wolves", "serial_killer", "necromancer", None)
    assert result["neutral_result"] is not None
    types = {e.type for e in events}
    assert {"game_started", "role_assigned", "night_result", "night_record", "wolf_kill_decided",
            "night_action", "uses_remaining", "game_over"} <= types
    assert "wolf_vote" not in types
    assert "wolves" in units and len(units) >= 5
    started = next(e for e in events if e.type == "game_started")
    assert started.lineup == result["lineup"] and len(started.seats) == 10
    over = next(e for e in events if e.type == "game_over")
    assert over.winner == result["winner"] and over.neutral_result == result["neutral_result"]
    # No night record goes to a seat that died that night; the pack's goes to the wolves.
    for e in events:
        if e.type == "night_record" and e.actor == "wolves":
            assert result["roles"][e.player] in ("chanteuse", "illusionist")


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


def test_a_dead_player_gets_no_record_of_its_last_night():
    st = _state({"lone_killer": "serial_killer", "neutral": "speculator"})
    h = _holders(st)
    st["night_choices"] = [
        NightChoice(h["serial_killer"], "serial_killer", "kill", h["sentinel"]),
        NightChoice(h["sentinel"], "sentinel", "watch", h["healer"]),
    ]
    update = night_resolution(st, SimpleNamespace(context={"metrics": Metrics()}))
    assert h["sentinel"] in update["dead_roster"][0].player
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
