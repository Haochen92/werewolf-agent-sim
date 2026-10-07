"""Exact-output goldens for the translator: the events it must produce, field for field.

Three chunk sequences, three golden files next to this module:

- ``translator_golden.jsonl``: every event from replaying the captured game of 2026-08
  (notebooks/fixtures/chunk_catalogue.jsonl), the sequential day before the rounds. An
  AI-only game, so it never pauses.
- ``translator_golden_phase2.jsonl``: every event from replaying the captured game of
  2026-10 (notebooks/fixtures/chunk_catalogue_phase2.jsonl), the day with rounds: the
  opening, the proactive rounds, the closing (discussion_evidence.md §7). AI-only too.
- ``translator_golden_human.jsonl``: every event from ``human_path_chunks()``, a scripted
  sequence that starts from the first captured game's real deal and then walks the paths
  only a human seat causes (a human in the opening round: the early announcement, the
  interrupt, the cached siblings' re-stream and the uncached twin; the uncached vote twins;
  re-run steps; cached re-streams) plus the night rows the captured game happened not to
  contain (deaths, a save, the vigilante's shot).

The property tests say the output is well-formed; these say it is unchanged. Regenerate
on purpose only, after a deliberate change to what ships::

    poetry run python -m tests.fixtures.translator_golden
"""

from __future__ import annotations

import json
import pathlib

from server.game.translate import Translator
from tests.fixtures.stream import FIXTURE_PHASE2, load_fixture_chunks

HERE = pathlib.Path(__file__).resolve().parent
GOLDEN_FIXTURE = HERE / "translator_golden.jsonl"
GOLDEN_PHASE2 = HERE / "translator_golden_phase2.jsonl"
GOLDEN_HUMAN = HERE / "translator_golden_human.jsonl"


def _updates(node: str, delta, ns: str | None = None, cached: bool = False) -> dict:
    data = {node: delta}
    if cached:
        data["__metadata__"] = {"cached": True}
    return {"type": "updates", "ns": [f"{ns}:task"] if ns else [], "data": data}


def _speech(day: int, seq: int, player: str, message: str,
            day_round: str = "discussion") -> dict:
    return {"day": day, "seq": seq, "player": player, "message": message,
            "addressed_targets": [], "passed": False, "pass_reason": None,
            "firing_reason": None, "gated": False, "gated_candidate": "",
            "day_round": day_round, "opening_kind": ""}


def _opening(player: str, message: str, kind: str = "claim") -> dict:
    """An opening-round line as round_turn holds it: no seq yet (COLLECT_ROUND numbers it)."""
    entry = _speech(1, 0, player, message, day_round="opening")
    entry["opening_kind"] = kind
    return entry


def _round_turn(entry: dict, strategy: str, cached: bool = False) -> dict:
    """One round turn's chunk: the line held as a RoundCandidate, plus the strategy note."""
    candidate = {"day": entry["day"], "day_round": entry["day_round"], "round_no": 0,
                 "entry": entry}
    delta = {"round_candidates": [candidate],
             "agent_strategies": {entry["player"]: strategy} if strategy else {}}
    return _updates("round_turn", delta, "DAY_PHASE", cached=cached)


def _human_turn_opened(player: str, role: str, day: int, day_round: str) -> dict:
    return {"type": "custom", "ns": ["DAY_PHASE:task"],
            "data": {"event": "human_turn_opened", "player": player, "role": role,
                     "phase": "day_channel", "day": day, "valid_targets": [],
                     "day_round": day_round}}


def _player_reads(player: str, role: str, day: int, phase: str = "day_discussion") -> dict:
    return {"type": "custom", "ns": ["DAY_PHASE:task"], "data": {
        "event": "player_reads", "player": player, "role": role, "day": day, "round": 0,
        "action_phase": phase,
        "reads": [{"player": "player_4", "why": "passed on day 1 with nothing to say",
                   "suspected_role": "wolf", "confidence": "low"}]}}


def _memory_consulted(player: str, role: str, day: int) -> dict:
    return {"type": "custom", "ns": [f"{role.upper()}_NIGHT_PHASE:task"], "data": {
        "event": "memory_consulted", "player": player, "role": role, "day": day, "round": 0,
        "action_phase": "night_action",
        "lessons": [{"index": 1, "key": "sp-1", "situation": "When a claimed investigator is loud",
                     "action": "Protect the claimant, not the accuser."}],
        "verdicts": [{"strategy_index": 1, "verdict": "follow", "why": "player_3 claimed today"}],
        "observations": [], "applicability": []}}


def _memory_extracted(day: int) -> dict:
    return {"type": "custom", "ns": [], "data": {
        "event": "memory_extracted", "day": day,
        "observations": [{"perspective": "wolf", "action_phase": "day_discussion",
                          "situation": "The investigator claimed on day 1 with a wolf result.",
                          "approach": "The wolves stayed silent instead of counter-claiming.",
                          "outcome": "The claim went unchallenged and the wolf was lynched.",
                          "net_verdict": "negative"}],
        "strategy_points": [{"perspective": "wolf", "action_phase": "day_discussion",
                             "situation": "When an investigator claims a wolf result on you",
                             "action": "Counter-claim at once; silence reads as guilt."}]}}


def _interrupt(player: str, phase: str, day: int, targets: list[str],
               day_round: str | None = None) -> dict:
    return {"value": {"player_id": player, "phase": phase, "day": day,
                      "day_round": day_round,
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
    seats = [f"player_{n}" for n in range(1, 10)]

    # --- day 1: the opening round, with the two humans' turns as interrupts ----------------
    # The round's entry node lists its players; the router announces each human's turn as the
    # round starts, so their prompts open before the agents have finished.
    out += [
        _updates("START_OPENING", {"day_round": "opening", "round_players": seats}, day),
        _human_turn_opened("player_6", "villager", 1, "opening"),
        _human_turn_opened("player_9", "wolf", 1, "opening"),
    ]
    # The agents' turns land first; the vigilante's suspicions stream from inside its node,
    # and its re-run streams them again, which is sent once.
    openings = [
        ("player_3", "I am the investigator.", "claim", "claim early"),
        ("player_4", "", "other", "lie low"),
        ("player_1", "player_4 is quiet.", "challenge", "watch player_4"),
        ("player_2", "Nothing yet.", "other", ""),
        ("player_5", "Nothing yet.", "other", ""),
        ("player_7", "Nothing yet.", "other", ""),
        ("player_8", "Nothing yet.", "other", ""),
    ]
    out.append(_player_reads("player_1", "vigilante", 1))
    out.append(_player_reads("player_1", "vigilante", 1))
    for player, message, kind, strategy in openings:
        entry = _opening(player, message, kind)
        if message == "":
            entry["passed"] = True
            entry["pass_reason"] = "voluntary"
        out.append(_round_turn(entry, strategy))
    out += [
        # the humans' turns: each interrupt streams under the subgraph, then at root; the
        # announcement already sent the prompts, so these send nothing
        _updates("__interrupt__", [_interrupt("player_6", "day_channel", 1, [], "opening"),
                                   _interrupt("player_9", "day_channel", 1, [], "opening")], day),
        _updates("__interrupt__", [_interrupt("player_6", "day_channel", 1, [], "opening"),
                                   _interrupt("player_9", "day_channel", 1, [], "opening")]),
    ]
    # resume: the agents' turns come back from the cache (dropped whole), the humans' lines
    # arrive through the uncached twin
    for player, message, kind, strategy in openings:
        entry = _opening(player, message, kind)
        if message == "":
            entry["passed"] = True
            entry["pass_reason"] = "voluntary"
        out.append(_round_turn(entry, strategy, cached=True))
    out += [
        _updates("round_turn_human",
                 {"round_candidates": [{"day": 1, "day_round": "opening", "round_no": 0,
                                        "entry": _opening("player_6", "Agreed, player_4.", "challenge")}],
                  "agent_strategies": {}}, day),
        _updates("round_turn_human",
                 {"round_candidates": [{"day": 1, "day_round": "opening", "round_no": 0,
                                        "entry": _opening("player_9", "", "other")}],
                  "agent_strategies": {}}, day),
    ]
    # COLLECT_ROUND plays the lines in seat order, numbered, after the opening's filter: the
    # agents' empty "nothing yet" lines are held as opening_filtered passes with the text kept
    collected = []
    for seq, player in enumerate(seats):
        if player == "player_3":
            collected.append({**_speech(1, seq, player, "I am the investigator.", "opening"),
                              "opening_kind": "claim"})
        elif player == "player_1":
            collected.append({**_speech(1, seq, player, "player_4 is quiet.", "opening"),
                              "opening_kind": "challenge",
                              "addressed_targets": [{"target": "player_4",
                                                     "addressed_form": "mention",
                                                     "stance": "accusation"}]})
        elif player == "player_6":
            collected.append({**_speech(1, seq, player, "Agreed, player_4.", "opening"),
                              "opening_kind": "challenge"})
        elif player in ("player_4", "player_9"):
            collected.append({**_speech(1, seq, player, "", "opening"), "opening_kind": "other",
                              "passed": True, "pass_reason": "voluntary"})
        else:
            collected.append({**_speech(1, seq, player, "", "opening"), "opening_kind": "other",
                              "passed": True, "pass_reason": "opening_filtered",
                              "gated": True, "gated_candidate": "Nothing yet."})
    # then the reactive chain: player_4 owes player_1 and player_6 an answer, which the
    # scheduler fires one speaker at a time (the only turns that announce "X is thinking")
    out += [
        _updates("COLLECT_ROUND", {"day_channel": collected}, day),
        _updates("SCHEDULE", None, day),
        {"type": "custom", "ns": [f"{day}:task"],
         "data": {"event": "turn_started", "player": "player_4", "day": 1}},
        _updates("discuss", {"day_channel": [{**_speech(1, 9, "player_4", "I had nothing to say, player_1. That is not a tell."),
                                              "addressed_targets": [{"target": "player_1",
                                                                     "addressed_form": "response",
                                                                     "stance": "defense"}],
                                              "firing_reason": {"tier": "reactive",
                                                                "owes": ["player_1", "player_6"]}}],
                             "agent_strategies": {"player_4": "lie low"}}, day),
        _updates("SCHEDULE", None, day),
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
        # the healer weighed a lesson first (a memory-on game); its node re-ran and streamed
        # the same consultation again, which is sent once
        _memory_consulted("player_5", "healer", 1),
        _memory_consulted("player_5", "healer", 1),
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
    # --- day 2: a restart re-streams the committed steps tagged cached, then the end ------
    alive = ["player_1", "player_2", "player_3", "player_5", "player_6", "player_9"]
    accusation = {**_opening("player_3", "player_9 is a wolf."), "day": 2,
                  "addressed_targets": [{"target": "player_9", "addressed_form": "mention",
                                         "stance": "accusation"}]}
    out += [
        _updates("START_OPENING", {"day_round": "opening", "round_players": alive}, day, cached=True),
        _round_turn(accusation, "claim early", cached=True),
        _updates("COLLECT_ROUND", {"day_channel": [{**accusation, "seq": 0}]}, day),
        _updates("END_GAME", {"winner": "villagers",
                              "day_channel": [_speech(2, 1, "game_master", "Game over! The villagers have won!")]}),
        # what the game taught (a memory-on game), streamed from inside the post-game
        # node; a re-run streams it again and it is sent once
        _memory_extracted(2),
        _memory_extracted(2),
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
                         (GOLDEN_PHASE2, load_fixture_chunks(FIXTURE_PHASE2)),
                         (GOLDEN_HUMAN, human_path_chunks())):
        with path.open("w") as f:
            for event in events_of(chunks):
                f.write(json.dumps(event, sort_keys=True) + "\n")
        print(f"wrote {path.name}: {sum(1 for _ in path.open())} events")


if __name__ == "__main__":
    write_goldens()
