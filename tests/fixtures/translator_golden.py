"""Exact-output goldens for the translator: the events it must produce, field for field.

Two chunk sequences, two golden files next to this module:

- ``translator_golden.jsonl``: every event from replaying the captured ten-seat game of
  2026-10 (notebooks/fixtures/chunk_catalogue_phase3.jsonl): the opening round, the sweep and
  the vote; the pack's chat, carrier and skills; the solo night nodes; the night report with
  a sigil's kill and a concealed body; a neutral's result at game over. An AI-only game, so
  it never pauses.
- ``translator_golden_human.jsonl``: every event from ``human_path_chunks()``, a scripted
  sequence that starts from the captured game's real deal and then walks the paths only a
  human seat causes (a human in the opening round: the early announcement, the interrupt,
  the cached siblings' re-stream and the uncached twin; a solo night turn announced from
  NIGHT_START; a human wolf's passed chat turn, the human carrier and a human skill turn;
  the vote's uncached twin; cached re-streams) plus a night report with a death, a save and
  a pick.

(The nine-seat captures had a golden each, translator_golden.jsonl and
translator_golden_phase2.jsonl; the ten-seat capture has the rounds too, so one golden
covers both.)

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
    candidate = {"day": entry["day"], "day_round": entry["day_round"], "entry": entry}
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
        "observations": [{"perspective": "chanteuse", "action_phase": "day_discussion",
                          "situation": "The investigator claimed on day 1 with a wolf result.",
                          "approach": "The wolves stayed silent instead of counter-claiming.",
                          "outcome": "The claim went unchallenged and the wolf was lynched.",
                          "net_verdict": "negative"}],
        "strategy_points": [{"perspective": "chanteuse", "action_phase": "day_discussion",
                             "situation": "When an investigator claims a wolf result on you",
                             "action": "Counter-claim at once; silence reads as guilt."}]}}


def _interrupt(player: str, phase: str, day: int, targets: list[str],
               day_round: str | None = None) -> dict:
    return {"value": {"player_id": player, "phase": phase, "day": day,
                      "day_round": day_round,
                      "valid_targets": targets, "surviving_players": targets,
                      "instruction": "", "can_pass": phase in ("day_channel", "wolf_channel")},
            "id": f"int-{player}-{phase}"}


def _night_turn_opened(player: str, role: str, phase: str, day: int,
                       targets: list[str]) -> dict:
    """A human solo actor's night turn, announced by route_night_actors (a root edge) as the
    night fans out, before the slowest branch has ended."""
    return {"type": "custom", "ns": [],
            "data": {"event": "human_turn_opened", "player": player, "role": role,
                     "phase": phase, "day": day, "valid_targets": targets, "day_round": None}}


def _vote_opened(player: str, role: str, day: int, targets: list[str]) -> dict:
    """A human's ballot, announced by fan_out_vote as the agents start voting."""
    return {"type": "custom", "ns": ["DAY_PHASE:task"],
            "data": {"event": "human_turn_opened", "player": player, "role": role,
                     "phase": "day_votes", "day": day, "valid_targets": targets,
                     "day_round": None}}


def _choice(actor: str, role: str, kind: str, target: str | None) -> dict:
    """One NightChoice as a night node commits it."""
    return {"actor": actor, "role": role, "kind": kind, "target": target, "via": None,
            "role_named": None}


def _solo(role: str, choice: dict | None, strategy: str) -> dict:
    """A solo role's root night node: its choice (none for a declined action) and its note."""
    delta = {"night_choices": [choice] if choice else [],
             "agent_strategies": {choice["actor"]: strategy} if choice and strategy else {}}
    return _updates(f"{role.upper()}_NIGHT_PHASE", delta)


def _wolf_line(day: int, round_: int, wolf: str, message: str = "", vote: str = "") -> dict:
    passed = not message and not vote
    return {"day": day, "round": round_, "wolf": wolf, "message": message, "vote": vote,
            "passed": passed, "pass_reason": "voluntary" if passed else None}


def _record(actor: str, action: str, target: str | None, result: str, outcome: str,
            seen: list[str] | None = None) -> dict:
    """One NightActionRecord as NIGHT_RESOLUTION commits it."""
    return {"day": 1, "actor": actor, "action": action, "target": target, "result": result,
            "outcome": outcome, "seen": seen or []}


def human_path_chunks() -> list[dict]:
    """Day 1 to game over with player_4 (sigilist) and player_5 (chanteuse) as human seats.

    The deal is the captured game's real INITIALIZE_GAME chunk: player_1 vigilante, player_2
    healer, player_3 trailseer, player_4 sigilist, player_5 chanteuse and player_6
    illusionist (the pack), player_7 investigator, player_8 fortune teller, player_9
    sentinel, player_10 serial killer. The game is scripted to a day limit of two days, so it
    ends after day 2's lynch with the largest side winning. Night 1's outcome is what
    Agents/rules/night.py resolves for the choices below.
    """
    init = load_fixture_chunks()[0]
    day, pack = "DAY_PHASE", "PACK_NIGHT_PHASE"
    out: list[dict] = [init]
    seats = list(init["data"]["INITIALIZE_GAME"]["roles"])
    humans = ("player_4", "player_5")

    # --- day 1: the opening round, with the two humans' turns as interrupts ----------------
    # The round's entry node lists its players; the router announces each human's turn as the
    # round starts, so their prompts open before the agents have finished.
    out += [
        _updates("START_OPENING", {"day_round": "opening", "round_players": seats}, day),
        _human_turn_opened("player_4", "sigilist", 1, "opening"),
        _human_turn_opened("player_5", "chanteuse", 1, "opening"),
    ]
    # The agents' turns land first, in the order they finish. The investigator's reads stream
    # from inside its node; streamed again (a re-run), they are sent once.
    openings = {
        "player_7": ("I am the investigator. Nothing to report before the first night.",
                     "claim", "claim early"),
        "player_1": ("", "other", "hide the gun"),
        "player_10": ("", "other", "blend in"),
    }
    agents = [p for p in seats if p not in humans]
    out.append(_player_reads("player_7", "investigator", 1))
    out.append(_player_reads("player_7", "investigator", 1))

    def opening_turn(player: str, cached: bool = False) -> dict:
        message, kind, strategy = openings.get(player, ("Nothing yet.", "other", ""))
        entry = _opening(player, message, kind)
        if message == "":
            entry["passed"] = True
            entry["pass_reason"] = "voluntary"
        return _round_turn(entry, strategy, cached=cached)

    out += [opening_turn(p) for p in agents]
    # The humans' turns: the interrupt streams under the subgraph, then at the root; the
    # announcement already sent the prompts, so these send nothing.
    asks = [_interrupt(p, "day_channel", 1, [], "opening") for p in humans]
    out += [_updates("__interrupt__", asks, day), _updates("__interrupt__", asks)]
    # Resume: the agents' turns come back from the cache (dropped whole), the humans' lines
    # arrive through the uncached twin.
    out += [opening_turn(p, cached=True) for p in agents]
    out += [
        _updates("round_turn_human", {"round_candidates": [{
            "day": 1, "day_round": "opening",
            "entry": _opening("player_4", "Glad to have an investigator. Stay safe.", "other")}],
            "agent_strategies": {}}, day),
        _updates("round_turn_human", {"round_candidates": [{
            "day": 1, "day_round": "opening",
            "entry": {**_opening("player_5", "", "other"), "passed": True,
                      "pass_reason": "voluntary"}}],
            "agent_strategies": {}}, day),
    ]
    # COLLECT_ROUND plays the lines in seat order, numbered, after the opening's filter: the
    # agents' "Nothing yet." lines are held as opening_filtered passes with the text kept.
    collected = []
    for seq, player in enumerate(seats):
        if player == "player_7":
            collected.append({**_speech(1, seq, player, openings[player][0], "opening"),
                              "opening_kind": "claim"})
        elif player == "player_4":
            collected.append({**_speech(1, seq, player, "Glad to have an investigator. Stay safe.",
                                        "opening"),
                              "opening_kind": "other",
                              "addressed_targets": [{"target": "player_7",
                                                     "addressed_form": "mention",
                                                     "stance": "agreement"}]})
        elif player in ("player_1", "player_5", "player_10"):
            collected.append({**_speech(1, seq, player, "", "opening"), "opening_kind": "other",
                              "passed": True, "pass_reason": "voluntary"})
        else:
            collected.append({**_speech(1, seq, player, "", "opening"), "opening_kind": "other",
                              "passed": True, "pass_reason": "opening_filtered",
                              "gated": True, "gated_candidate": "Nothing yet."})
    # Day 1 is the opening and the summary only: no sweep, no vote.
    no_vote = "\nThere is no vote on day 1, so no one voted and no one is eliminated."
    out += [
        _updates("COLLECT_ROUND", {"day_channel": collected}, day),
        _updates("SUMMARIZE_DAY_DISCUSSION", {"day_summaries": [{
            "day": 1, "summary": "Role claims: player_7 claimed investigator.",
            "source": "discussion",
            "structured": {"accusations": [], "role_claims": [
                {"player": "player_7", "role": "investigator"}]}}]}, day),
        _updates("DAY_PHASE", {"day_channel": [], "day_votes": [], "day_summaries": [],
                               "agent_strategies": {}}),
        _updates("DAY_RESOLUTION", {
            "voted_player": None, "no_lynch_streak": 1,
            "day_channel": [_speech(1, 10, "game_master", no_vote)],
            "day_summaries": [{"day": 1, "summary": no_vote, "source": "game_master",
                               "structured": {}}],
        }),
        _updates("NIGHT_START", None),
    ]

    # --- night 1: the human sigilist's solo turn, the human chanteuse carrying the kill -----
    # route_night_actors announces the sigilist's turn as the night fans out: every other
    # survivor in seat order, and the word that keeps the sigil.
    sigil_targets = [p for p in seats if p != "player_4"] + ["keep_sigil"]
    out.append(_night_turn_opened("player_4", "sigilist", "sigil_target", 1, sigil_targets))
    # The agents' solo turns commit as they finish. The healer weighed a lesson first (a
    # memory-on game); its node streamed the consultation twice, which is sent once.
    out += [
        _solo("sentinel", _choice("player_9", "sentinel", "watch", "player_7"), "watch the claimant"),
        _solo("investigator", _choice("player_7", "investigator", "investigate", "player_6"), ""),
        _solo("serial_killer", _choice("player_10", "serial_killer", "kill", "player_3"), "thin the herd"),
        _solo("fortune_teller", _choice("player_8", "fortune_teller", "bet", "player_3"), ""),
        _solo("trailseer", _choice("player_3", "trailseer", "follow", "player_5"), ""),
        _memory_consulted("player_2", "healer", 1),
        _memory_consulted("player_2", "healer", 1),
        _solo("healer", _choice("player_2", "healer", "protect", "player_7"), "guard the claimant"),
        _solo("vigilante", _choice("player_1", "vigilante", "kill", "player_6"), "shoot the quiet one"),
    ]
    # The pack: player_5 carries tonight (pack_carrier rotates in seat order), so speaks first.
    # The chat turn is not a cached node: the human's interrupt streams under the pack's
    # subgraph and at the root, where it shares the step's interrupt list with the sigilist's
    # (whose prompt is already open, so only the chat turn is asked).
    chat_ask = _interrupt("player_5", "wolf_channel", 1, [])
    sigil_ask = _interrupt("player_4", "sigil_target", 1, sigil_targets)
    out += [
        _updates("PREPARE_PACK_NIGHT", {"current_round": 1}, pack),
        _updates("__interrupt__", [chat_ask], pack),
        _updates("__interrupt__", [sigil_ask, chat_ask]),
        # resume: the human passed the chat round, then the illusionist passed too, which
        # ends the chat early; the sigilist's answer commits through its own node
        _updates("PACK_CHAT", {"wolf_channel": [_wolf_line(1, 1, "player_5")],
                               "agent_strategies": {}}, pack),
        _updates("SIGILIST_NIGHT_PHASE", {"night_choices": [
            _choice("player_4", "sigilist", "sigil", "player_10")], "agent_strategies": {}}),
        _updates("PREPARE_PACK_NIGHT", {"current_round": 1}, pack),
        _updates("PACK_CHAT", {"wolf_channel": [_wolf_line(1, 1, "player_6")],
                               "agent_strategies": {"player_6": "let player_5 lead"}}, pack),
        _updates("PREPARE_PACK_NIGHT", {"current_round": 4}, pack),
        _updates("START_CARRIER", None, pack),
    ]
    # The human carrier goes through the uncached twin; wolf_kill_decided names the carrier.
    alive = [p for p in seats if p != "player_5"]
    kill_ask = _interrupt("player_5", "kill_target", 1, alive)
    out += [
        _updates("__interrupt__", [kill_ask], pack),
        _updates("__interrupt__", [kill_ask]),
        _updates("CARRIER_KILL_HUMAN", {
            "night_choices": [_choice("player_5", "chanteuse", "kill", "player_7")],
            "wolves_target": "player_7",
            "wolf_channel": [_wolf_line(1, 4, "player_5", vote="player_7")],
            "agent_strategies": {}}, pack),
    ]
    # The skills in parallel: the illusionist's turn (cached) declines to conceal and lands
    # first; the human chanteuse's block pauses the step; on resume the illusionist's turn
    # re-streams from the cache (dropped whole) and the block arrives through the twin.
    illusionist_skill = {"agent_strategies": {"player_6": "save the conceals"}}
    block_ask = _interrupt("player_5", "block_target", 1, alive)
    out += [
        _updates("PACK_SKILL", illusionist_skill, pack),
        _updates("__interrupt__", [block_ask], pack),
        _updates("__interrupt__", [block_ask]),
        _updates("PACK_SKILL", illusionist_skill, pack, cached=True),
        _updates("PACK_SKILL_HUMAN", {"night_choices": [
            _choice("player_5", "chanteuse", "block", "player_1")], "agent_strategies": {}}, pack),
        _updates("COLLECT_PACK", None, pack),
        _updates("PACK_NIGHT_PHASE", {"wolf_channel": [], "night_choices": [],
                                      "agent_strategies": {}}),
    ]
    # The resolution: the serial killer's stab kills the trailseer, the healer saves the
    # investigator from the pack, the sigil finds the serial killer immune, the chanteuse's
    # block cancels the vigilante's shot. The records go to each actor, the pack's kill to
    # both wolves. The report's pick is set by hand: this deal has a fortune teller, not a
    # speculator, so the engine would commit None; it is here only to pin the field.
    dawn = ("Night of day 1: player_3 was stabbed by the serial killer last night. They were "
            "a trailseer. player_7 was attacked by the wolves but was saved by the healer!")
    out += [
        _updates("NIGHT_RESOLUTION", {
            "uses_left": {"vigilante": 2, "sigilist": 1, "illusionist": 2, "fortune_teller": 2},
            "night_actions": [
                _record("player_9", "watch", "player_7", "seen",
                        "Tonight player_7 was visited by player_2 and player_5.",
                        ["player_2", "player_5"]),
                _record("player_7", "investigate", "player_6", "suspicious",
                        "player_6 reads Suspicious.", ["player_6"]),
                _record("player_10", "kill", "player_3", "killed",
                        "player_3 died. They were a trailseer."),
                _record("player_4", "sigil", "player_10", "miss",  # the serial killer: reads as a miss
                        "Your sigil had no effect."),
                _record("player_8", "bet", "player_3", "scored_1", "player_3 died: one point."),
                _record("player_2", "protect", "player_7", "saved",
                        "player_7 was attacked by the wolves, and your protection saved them."),
                _record("player_1", "shoot", "player_6", "roleblocked",
                        "You were roleblocked: your action was not carried out and you "
                        "learned nothing tonight."),
                _record("wolves", "kill", "player_7", "saved",
                        "player_7 survived: the healer saved them."),
                _record("player_5", "block", "player_1", "blocked",
                        "player_1 was roleblocked tonight."),
            ],
            "fortune_points": 1,
            "last_body": None,
            "dead_roster": [{"player": "player_3", "role": "trailseer", "day": 1,
                             "phase": "night", "concealed": False}],
            "surviving_wolves": ["player_5", "player_6"],
            "surviving_villagers": ["player_1", "player_2", "player_4", "player_7", "player_8",
                                    "player_9", "player_10"],
            "day_channel": [_speech(1, 11, "game_master", dawn)],
            "day_summaries": [{"day": 1, "summary": dawn, "source": "game_master",
                               "structured": {}}],
            "night_report": {"night": 1, "deaths": [["player_3", "trailseer", ["serial_killer"]]],
                             "saves": [["player_7", ["wolves"]]], "pick": "town"},
        }),
        _updates("ONE_MORE_DAY", {"current_day": 2, "day_votes": [], "night_choices": None,
                                  "night_report": None, "voted_player": None}),
    ]

    # --- day 2: a restart mid-opening, the sweep, the vote, the end -----------------------
    # The server restarted during the opening: its committed steps re-stream tagged cached
    # (their events went out before the restart), then the round is collected.
    survivors = [p for p in seats if p != "player_3"]
    accusation = {**_opening("player_7", "player_6 reads Suspicious."), "day": 2,
                  "addressed_targets": [{"target": "player_6", "addressed_form": "mention",
                                         "stance": "accusation"}]}
    out += [
        _updates("START_OPENING", {"day_round": "opening", "round_players": survivors}, day,
                 cached=True),
        _round_turn(accusation, "claim the check", cached=True),
    ]
    collected = []
    for seq, player in enumerate(survivors):
        if player == "player_7":
            collected.append({**accusation, "seq": seq})
        else:
            collected.append({**_speech(2, seq, player, "", "opening"), "opening_kind": "other",
                              "passed": True, "pass_reason": "voluntary"})
    # The accused answers the claim: the reactive chain fires one speaker at a time (the only
    # turns that announce "X is thinking").
    defence = {**_speech(2, 9, "player_6", "The check is wrong, player_7. I am a sentinel."),
               "addressed_targets": [{"target": "player_7", "addressed_form": "response",
                                      "stance": "defense"}],
               "firing_reason": {"tier": "reactive", "owes": ["player_7"]}}
    out += [
        _updates("COLLECT_ROUND", {"day_channel": collected}, day),
        {"type": "custom", "ns": [f"{day}:task"],
         "data": {"event": "turn_started", "player": "player_6", "day": 2}},
        _updates("SCHEDULE", None, day),
        _updates("discuss", {"day_channel": [defence],
                             "agent_strategies": {"player_6": "counterclaim"}}, day),
        _updates("SCHEDULE", None, day),
        _updates("SUMMARIZE_DAY_DISCUSSION", {"day_summaries": [{
            "day": 2, "summary": "player_7 claimed investigator and named player_6.",
            "source": "discussion", "structured": {}}]}, day),
        _updates("START_VOTING", None, day),
    ]
    # --- day 2 vote: the humans' ballots open as the vote starts; the agents' ballots
    # stream; the humans' interrupt ends the step; on resume the agents' ballots re-stream
    # from the cache (no events, but they refill the buffer) and the humans' arrive through
    # the uncached twin; COLLECT_VOTES releases the batch.
    vote_targets = [*survivors, "abstain"]
    out += [_vote_opened("player_4", "sigilist", 2,
                         [p for p in vote_targets if p != "player_4"]),
            _vote_opened("player_5", "chanteuse", 2,
                         [p for p in vote_targets if p != "player_5"])]
    ballots = [("player_1", "player_6"), ("player_2", "player_6"), ("player_6", "player_7"),
               ("player_7", "player_6"), ("player_8", "abstain"), ("player_9", "player_6"),
               ("player_10", "player_6")]

    def vote_chunk(voter: str, votee: str, cached: bool = False) -> dict:
        return _updates("vote", {"day_votes": [{"voter": voter, "votee": votee}],
                                 "agent_strategies": {}}, day, cached=cached)

    out += [vote_chunk(v, t) for v, t in ballots]
    asks = [_interrupt(p, "day_votes", 2, [t for t in vote_targets if t != p]) for p in humans]
    out += [_updates("__interrupt__", asks, day), _updates("__interrupt__", asks)]
    out += [vote_chunk(v, t, cached=True) for v, t in ballots]
    lynch = ("\nHere's the vote result for day 2:\n"
             "  player_1 voted to eliminate player_6\n  player_2 voted to eliminate player_6\n"
             "  player_4 voted to eliminate player_6\n  player_5 voted to eliminate player_7\n"
             "  player_6 voted to eliminate player_7\n  player_7 voted to eliminate player_6\n"
             "  player_8 voted to abstain\n  player_9 voted to eliminate player_6\n"
             "  player_10 voted to eliminate player_6\n"
             "Player player_6 has been voted out and was a illusionist.\n")
    end = "Game over! The town has won! The fortune teller lost (1 points)."
    out += [
        _updates("vote_human", {"day_votes": [{"voter": "player_4", "votee": "player_6"}],
                                "agent_strategies": {}}, day),
        _updates("vote_human", {"day_votes": [{"voter": "player_5", "votee": "player_7"}],
                                "agent_strategies": {}}, day),
        _updates("COLLECT_VOTES", None, day),
        _updates("DAY_PHASE", {"day_channel": [], "day_votes": [], "day_summaries": [],
                               "agent_strategies": {}}),
        _updates("DAY_RESOLUTION", {
            "voted_player": "player_6", "no_lynch_streak": 0,
            "day_channel": [_speech(2, 10, "game_master", lynch)],
            "day_summaries": [{"day": 2, "summary": lynch, "source": "game_master",
                               "structured": {}}],
            "dead_roster": [{"player": "player_6", "role": "illusionist", "day": 2,
                             "phase": "day", "concealed": False}],
            "surviving_wolves": ["player_5"],
            "surviving_villagers": ["player_1", "player_2", "player_4", "player_7", "player_8",
                                    "player_9", "player_10"],
        }),
        # the day limit: the largest side wins, the fortune teller short of its two points
        _updates("END_GAME", {"winner": "villagers", "neutral_result": "lost (1 points)",
                              "day_channel": [_speech(2, 11, "game_master", end)]}),
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
    deadlines = {"player_4": "2026-01-01T00:01:00Z", "player_5": "2026-01-01T00:01:00Z"}
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
