"""Whole games of ten seats on the real game graph, with the scripted model in place of every model.

Each test plays a game to its end, or through a pause for a human seat and its resume, on a
graph with its own checkpoint store (the `game_graph` fixture). Nothing outside the process is
needed. The games run for both drawn lineups; the server's translator and the pacing units take
every chunk. One game pauses a human Vigilante at its night turn and resumes it, to check the
bullet is spent once. The seeds were chosen by hand and also seed the deal: change one and a
different game is played.
"""
from __future__ import annotations

import pytest
from langgraph.types import Command

from Agents.config import RunConfig, build_runnable_config, normalize_run_config
from Agents.nodes.orchestrator import initialize_game
from Agents.observability.case_sink import EvalCaseSink
from Agents.schemas.metrics import Metrics
from Agents.schemas.roles import lineup
from Agents.state import fresh_game_state
from tests.factories.whole_game import play_game


@pytest.mark.parametrize("game", [
    {"lone_killer": "serial_killer", "neutral": "speculator"},
    {"lone_killer": "necromancer", "neutral": "fortune_teller"},
])
def test_a_whole_game_runs_on_the_real_graph_and_the_wire_accepts_every_chunk(scripted_model, game_graph,
                                                                              game):
    # Arrange
    scripted_model(seed=3)

    # Act
    result, events, units = play_game(game_graph, game, seed=3)

    # Assert
    assert result["lineup"] == lineup(game["lone_killer"], game["neutral"])
    assert result["winner"] in ("villagers", "wolves", "serial_killer", "necromancer", None)
    assert result["neutral_result"] is not None
    types = {e.type for e in events}
    assert {"game_started", "role_assigned", "night_result", "night_record", "wolf_kill_decided",
            "night_action", "uses_remaining", "game_over"} <= types
    assert "wolf_vote" not in types
    assert "PACK_NIGHT_PHASE" in units and len(units) >= 5
    started = next(e for e in events if e.type == "game_started")
    assert started.lineup == result["lineup"] and len(started.seats) == 10
    over = next(e for e in events if e.type == "game_over")
    assert over.winner == result["winner"] and over.neutral_result == result["neutral_result"]
    # No night record goes to a seat that died that night; the pack's goes to the wolves.
    for e in events:
        if e.type == "night_record" and e.actor == "wolves":
            assert result["roles"][e.player] in ("chanteuse", "illusionist")


def test_every_day_turn_reaches_the_replay_and_every_wolf_turn_says_what_it_decided(scripted_model,
                                                                                    game_graph):
    # Arrange
    sink = EvalCaseSink()
    scripted_model(seed=11)

    # Act
    result, events, _ = play_game(game_graph, {"lone_killer": "serial_killer", "neutral": "speculator"},
                                  seed=11, sink=sink)

    # Assert
    # The translator sends one reads event per (player, day, round, phase): a player's later
    # discussion turns of a day must not share its first turn's round, or they are dropped.
    rounds: dict[tuple[str, int], list[int]] = {}
    for e in events:
        if e.type == "player_reads" and e.action_phase == "day_discussion":
            rounds.setdefault((e.player, e.day), []).append(e.round)
    assert any(len(r) > 1 for r in rounds.values())
    assert all(len(r) == len(set(r)) for r in rounds.values())
    # The night_action phase tag is shared by the pack's chat, kill and skill turns.
    kinds = {}
    for record in sink.records:
        case = record["output"].get("eval_case") or {}
        action = case.get("agent_night_action")
        if action and action["role"] in ("chanteuse", "illusionist"):
            kinds.setdefault(action["role"], set()).add(action["kind"])
    assert {"chat", "kill"} <= kinds["chanteuse"] | kinds["illusionist"]
    assert kinds["chanteuse"] <= {"chat", "kill", "block"}
    assert kinds["illusionist"] <= {"chat", "kill", "conceal", "declined"}


def _shots_fired(state: dict, vigilante: str) -> int:
    """The vigilante's shots that went ahead: a blocked shot was never fired."""
    return sum(1 for r in state.get("night_actions", [])
               if r.actor == vigilante and r.action == "shoot" and r.result != "roleblocked")


def test_a_human_vigilantes_shot_is_spent_once_across_the_pause_and_resume(scripted_model, game_graph):
    # The night's turns pause for the human and are re-run on resume; the bullet is spent only
    # in NIGHT_RESOLUTION, the barrier after every night turn, so the pause always comes first.

    # Arrange
    game = {"lone_killer": "serial_killer", "neutral": "speculator"}
    run = normalize_run_config(RunConfig(game_id="offline-human-vigilante-5", game=game, human_player=1,
                                         human_role="vigilante", memory_persistence={"dump_enabled": False}))
    config = build_runnable_config(run)
    # No scripted player targets the Vigilante, so its first shot always goes ahead and is kept on
    # record: a seat that dies that night gets no record, and the scripted players share one random
    # generator across threads, so without this the game played (and the count) varied by thread order.
    scripted_model(seed=5, spare=frozenset(initialize_game({}, config)["human_players"]))
    context = {"metrics": Metrics()}

    # Act: play the game, answering each pause for the human
    result = game_graph.invoke(fresh_game_state(), config=config, context=context)
    shot_turns = 0
    while "__interrupt__" in result:
        request = result["__interrupt__"][0].value
        state = game_graph.get_state(config).values
        if request["phase"] != "vigilante_target":
            answer = {"delegate": True}
        elif _shots_fired(state, request["player_id"]) == 0:
            # One shot only: a second could hide a double spend behind the count's floor of zero.
            answer = {"target": next(t for t in request["valid_targets"] if t.startswith("player_"))}
            shot_turns += 1
        else:
            answer = {"target": "hold_fire"}
        result = game_graph.invoke(Command(resume=answer), config=config, context=context)

    # Assert
    final = game_graph.get_state(config).values
    vigilante = final["human_players"][0]
    assert final["roles"][vigilante] == "vigilante"
    assert shot_turns >= 1 and _shots_fired(final, vigilante) == 1
    assert final["uses_left"]["vigilante"] == 1


def test_a_finished_game_saves_its_extraction_input_and_extracts_nothing(scripted_model, game_graph):
    # Extraction is an offline batch (decisions §11): the game keeps only what it can teach.

    # Arrange
    sink = EvalCaseSink()
    scripted_model(seed=5)

    # Act
    result, events, _ = play_game(game_graph, {"lone_killer": "necromancer", "neutral": "fortune_teller"},
                                  seed=5, sink=sink)

    # Assert
    [record] = [r for r in sink.records if r["kind"] == "extraction_input"]
    case = record["output"]["extraction_case"]
    assert case["roles"] == result["roles"] and case["lineup"] == result["lineup"]
    assert case["game_outcome"] == result["winner"] and case["human_players"] == []
    assert "=== Night Actions (exact, from the game engine) ===" in case["formatted_discussions"]
    assert case["observations"] == [] and case["strategy_points"] == []
    assert not any(r["kind"] in ("postgame_extraction", "dehalo") for r in sink.records)
    assert "memory_extracted" not in {e.type for e in events}
