"""Exact-output goldens for the translator: the events it must produce, field for field.

Two chunk sequences, two golden files next to this module:

- ``translator_golden.jsonl``: every event from replaying the captured game
  (notebooks/fixtures/chunk_catalogue.jsonl). An AI-only game, so it never pauses.
- ``translator_golden_human.jsonl``: every event from ``human_path_chunks()``, a scripted
  sequence that starts from the captured game's real deal and then walks the paths only a
  human seat causes (interrupts, the uncached vote twins, re-run steps, cached re-streams)
  plus the night rows the captured game happened not to contain (deaths, a save, the
  vigilante's shot).

The property tests say the output is well-formed; these say it is unchanged. Regenerate
on purpose only, after a deliberate change to what ships::

    poetry run python -m tests.fixtures.translator_golden
"""

from __future__ import annotations

import json
import pathlib

from server.game.translate import Translator
from tests.fixtures.stream import load_fixture_chunks

HERE = pathlib.Path(__file__).resolve().parent
GOLDEN_FIXTURE = HERE / "translator_golden.jsonl"
GOLDEN_HUMAN = HERE / "translator_golden_human.jsonl"


def _updates(node: str, delta, ns: str | None = None, cached: bool = False) -> dict:
    data = {node: delta}
    if cached:
        data["__metadata__"] = {"cached": True}
    return {"type": "updates", "ns": [f"{ns}:task"] if ns else [], "data": data}


def _speech(day: int, seq: int, player: str, message: str) -> dict:
    return {"day": day, "seq": seq, "player": player, "message": message,
            "addressed_targets": [], "passed": False, "pass_reason": None,
            "firing_reason": None, "gated": False, "gated_candidate": ""}


def _interrupt(player: str, phase: str, day: int, targets: list[str]) -> dict:
    return {"value": {"player_id": player, "phase": phase, "day": day,
                      "valid_targets": targets, "surviving_players": targets,
                      "instruction": "", "can_pass": phase == "day_channel"},
            "id": f"int-{player}-{phase}"}


def human_path_chunks() -> list[dict]:
    """Day 1 to game over with player_6 (villager) and player_9 (wolf) as human seats.

    The deal is the captured game's real INITIALIZE_GAME chunk: player_1 vigilante,
    player_2 serial killer, player_3 investigator, player_4 and player_9 wolves, player_5
    healer, player_6 to player_8 villagers.
    """
    init = load_fixture_chunks()[0]
    day = "DAY_PHASE"
    wolf = "WOLF_NIGHT_PHASE"
    out: list[dict] = [init]

    # --- day 1: discussion, with the human's turn as an interrupt -------------------------
    out += [
        _updates("SCHEDULE", None, day),
        {"type": "custom", "ns": [f"{day}:task"],
         "data": {"event": "turn_started", "player": "player_3", "day": 1}},
        _updates("discuss", {"day_channel": [_speech(1, 0, "player_3", "I am the investigator.")],
                             "agent_strategies": {"player_3": "claim early"}}, day),
        _updates("discuss", {"day_channel": [{**_speech(1, 1, "player_4", ""), "passed": True,
                                              "pass_reason": "voluntary"}],
                             "agent_strategies": {"player_4": "lie low"}}, day),
        _updates("discuss", {"day_channel": [{**_speech(1, 2, "player_1", "player_4 is quiet."),
                                              "addressed_targets": [{"target": "player_4",
                                                                     "addressed_form": "mention",
                                                                     "stance": "accusation"}],
                                              "firing_reason": {"tier": "proactive", "owes": []}}],
                             "agent_strategies": {"player_1": "watch player_4"}}, day),
        # the human's turn: the interrupt streams under the subgraph, then at root
        _updates("__interrupt__", [_interrupt("player_6", "day_channel", 1, [])], day),
        _updates("__interrupt__", [_interrupt("player_6", "day_channel", 1, [])]),
        # resume: the discuss step re-runs and re-delivers the earlier entry (dropped)
        _updates("discuss", {"day_channel": [_speech(1, 2, "player_1", "player_4 is quiet.")],
                             "agent_strategies": {"player_1": "watch player_4"}}, day),
        _updates("discuss", {"day_channel": [_speech(1, 3, "player_6", "Agreed, player_4.")],
                             "agent_strategies": {}}, day),
        _updates("SUMMARIZE_DAY_DISCUSSION",
                 {"day_summaries": [{"day": 1, "summary": "Suspicion on player_4.",
                                     "structured": {}}]}, day),
        _updates("START_VOTING", None, day),
    ]
    # --- day 1 vote: AI ballots stream, the human interrupt aborts the step, all re-run ---
    first = [("player_1", "player_4"), ("player_2", "abstain"), ("player_3", "player_4")]
    rerun = [("player_1", "player_4"), ("player_2", "player_4"), ("player_3", "player_4"),
             ("player_4", "player_1"), ("player_5", "player_4"), ("player_7", "player_4"),
             ("player_8", "abstain")]
    for voter, votee in first:
        out.append(_updates("vote", {"day_votes": [{"voter": voter, "votee": votee}],
                                     "agent_strategies": {}}, day))
    out += [
        _updates("__interrupt__", [_interrupt("player_6", "day_votes", 1, ["player_4"]),
                                   _interrupt("player_9", "day_votes", 1, ["player_4"])], day),
        _updates("__interrupt__", [_interrupt("player_6", "day_votes", 1, ["player_4"]),
                                   _interrupt("player_9", "day_votes", 1, ["player_4"])]),
    ]
    for voter, votee in rerun:
        out.append(_updates("vote", {"day_votes": [{"voter": voter, "votee": votee}],
                                     "agent_strategies": {}}, day))
    out += [
        _updates("vote_human", {"day_votes": [{"voter": "player_6", "votee": "player_4"}],
                                "agent_strategies": {}}, day),
        _updates("vote_human", {"day_votes": [{"voter": "player_9", "votee": "player_1"}],
                                "agent_strategies": {}}, day),
        _updates("COLLECT_VOTES", None, day),
        _updates("DAY_PHASE", {"day_channel": [], "day_votes": [], "day_summaries": [],
                               "agent_strategies": {}}),
        _updates("DAY_RESOLUTION", {
            "day_channel": [_speech(1, 4, "game_master", "player_4 was lynched. They were a wolf.")],
            "day_summaries": [], "voted_player": "player_4", "no_lynch_streak": 0,
            "dead_roster": [{"player": "player_4", "role": "wolf", "day": 1, "phase": "day"}],
            "surviving_wolves": ["player_9"],
            "surviving_villagers": ["player_1", "player_2", "player_3", "player_5",
                                    "player_6", "player_7", "player_8"],
            "healer_player": "player_5", "investigator_player": "player_3",
            "serial_killer_player": "player_2", "vigilante_player": "player_1",
        }),
        _updates("NIGHT_START", None),
    ]
    # --- night 1: a lone human wolf, the special roles, then resolution -----------------
    out += [
        _updates("PREPARE_WOLF_NIGHT", {"current_round": 1}, wolf),
        _updates("__interrupt__", [_interrupt("player_9", "wolf_channel", 1, [])], wolf),
        _updates("__interrupt__", [_interrupt("player_9", "wolf_channel", 1, [])]),
        _updates("WOLF_NIGHT_DISCUSS", {"wolf_channel": [
            {"day": 1, "round": 1, "wolf": "player_9", "message": "player_6 tonight.",
             "vote": "", "passed": False}], "agent_strategies": {}}, wolf),
        _updates("PREPARE_WOLF_NIGHT", {"current_round": 2}, wolf),
        _updates("START_WOLF_VOTE", None, wolf),
        _updates("__interrupt__", [_interrupt("player_9", "wolf_vote", 1, ["player_6"])], wolf),
        _updates("__interrupt__", [_interrupt("player_9", "wolf_vote", 1, ["player_6"])]),
        _updates("WOLF_NIGHT_VOTE_HUMAN", {"wolf_channel": [
            {"day": 1, "round": 2, "wolf": "player_9", "message": "", "vote": "player_6",
             "passed": False}], "agent_strategies": {}}, wolf),
        _updates("COLLECT_WOLF_VOTES", {"wolves_kill_target": "player_6"}, wolf),
        _updates("WOLF_NIGHT_PHASE", {"wolf_channel": [], "wolves_kill_target": "player_6",
                                      "agent_strategies": {}}),
        _updates("healer_act", {"healer_target": "player_6", "updated_strategy": "guard the loud"},
                 "HEALER_NIGHT_PHASE"),
        _updates("HEALER_NIGHT_PHASE", {"healer_target": "player_6", "agent_strategies": {}}),
        _updates("investigator_act", {"investigator_target": "player_9", "updated_strategy": ""},
                 "INVESTIGATOR_NIGHT_PHASE"),
        _updates("INVESTIGATOR_NIGHT_PHASE", {"investigator_target": "player_9",
                                              "agent_strategies": {}}),
        _updates("serial_killer_act", {"serial_killer_target": "player_7", "updated_strategy": "thin the herd"},
                 "SERIAL_KILLER_NIGHT_PHASE"),
        _updates("SERIAL_KILLER_NIGHT_PHASE", {"serial_killer_target": "player_7",
                                               "agent_strategies": {}}),
        _updates("vigilante_act", {"vigilante_target": "player_8", "updated_strategy": "shoot"},
                 "VIGILANTE_NIGHT_PHASE"),
        _updates("VIGILANTE_NIGHT_PHASE", {"vigilante_target": "player_8", "agent_strategies": {}}),
        _updates("NIGHT_RESOLUTION", {
            "day_channel": [_speech(1, 5, "game_master",
                                    "Night of day 1: player_6 was saved; player_7 and player_8 died.")],
            "day_summaries": [], "dead_roster": [
                {"player": "player_7", "role": "villager", "day": 1, "phase": "night"},
                {"player": "player_8", "role": "villager", "day": 1, "phase": "night"}],
            "wolf_channel": [{"day": 1, "round": 3, "wolf": "game_master",
                              "message": "Your target was saved.", "vote": "", "passed": False}],
            "investigator_results": [{"day": 1, "player_investigated": "player_9",
                                      "role_revealed": "wolf"}],
            "vigilante_results": [{"day": 1, "target": "player_8"}],
            "vigilante_bullets": 1,
            "surviving_wolves": ["player_9"],
            "surviving_villagers": ["player_1", "player_2", "player_3", "player_5", "player_6"],
            "healer_player": "player_5", "investigator_player": "player_3",
            "serial_killer_player": "player_2", "vigilante_player": "player_1",
        }),
        _updates("ONE_MORE_DAY", {"current_day": 2, "day_votes": [], "voted_player": None,
                                  "wolves_kill_target": None, "healer_target": None,
                                  "investigator_target": None, "serial_killer_target": None,
                                  "vigilante_target": None}),
    ]
    # --- day 2: a restart re-streams the committed step tagged cached, then the end -------
    out += [
        _updates("SCHEDULE", None, day, cached=True),
        _updates("discuss", {"day_channel": [_speech(2, 0, "player_3", "player_9 is a wolf.")],
                             "agent_strategies": {"player_3": "claim early"}}, day, cached=True),
        _updates("discuss", {"day_channel": [_speech(2, 0, "player_3", "player_9 is a wolf.")],
                             "agent_strategies": {"player_3": "claim early"}}, day),
        _updates("END_GAME", {"winner": "villagers",
                              "day_channel": [_speech(2, 1, "game_master", "Game over! The villagers have won!")]}),
        _updates("POST_GAME_ANALYSIS", None),
    ]
    return out


def events_of(chunks: list[dict]) -> list[dict]:
    """Every event the translator produces for the sequence, as JSON-shaped dicts."""
    translator = Translator()
    deadlines = {"player_6": "2026-01-01T00:01:00Z", "player_9": "2026-01-01T00:01:00Z"}
    return [e.model_dump(mode="json")
            for chunk in chunks for e in translator.translate(chunk, deadlines=deadlines)]


def load_golden(path: pathlib.Path) -> list[dict]:
    with path.open() as f:
        return [json.loads(line) for line in f]


def write_goldens() -> None:
    for path, chunks in ((GOLDEN_FIXTURE, load_fixture_chunks()),
                         (GOLDEN_HUMAN, human_path_chunks())):
        with path.open("w") as f:
            for event in events_of(chunks):
                f.write(json.dumps(event, sort_keys=True) + "\n")
        print(f"wrote {path.name}: {sum(1 for _ in path.open())} events")


if __name__ == "__main__":
    write_goldens()
