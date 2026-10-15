"""Freeze the turns that went wrong in the owner's first Haiku 5.5 game as hallucination-bench cases.

Record: evidence/game_play_enhancement/discussion_evidence.md §8.6. Game 403f4dbc (2026-10-12, live
site, Claude Haiku 5.5 in every AI seat, the owner as the Necromancer) showed three discussion faults:

- visit: a visit read the wrong way round ("I visited nobody" answered as "no one visited you"; a
  watch that saw no one taken to mean the watched player did nothing);
- repeat: replies that restate a result already given that day, and questions asked again after
  they were answered (a three-way exchange on day 3);
- vote_reason: town seats passing on the open floor and then voting a player out without having said
  why (10 of 21 votes for a player came from seats silent that day).

Each case is one turn, frozen as the state the engine held just before it, read from the game's
LangGraph checkpoint on the server's Postgres (read-only), in the bench's case format; the bench's
replay (``evaluation/src/replay/hallucination_bench.py``) rebuilds it with the checked-out builders and
prompts. The goldens are hand-written. An opening-round turn is replayed as a sweep turn (the bench
rebuilds discussion turns only), with today's channel empty as it was. The vote_reason cases are read
for the pass rate and the spoken reasons; their golden only guards the facts.

Each turn is also labelled by its context: ``origin`` when no visit misreading is yet in the speaker's
transcript (the rule is what is tested), ``cascade`` when other players have already made it (resistance
to a peer's error is what is tested), reported apart (discussion_evidence.md §8.6).

  poetry run python evaluation/experiments/haiku_game_turn_cases.py
  poetry run eval-hallucination-bench --config evaluation/config/hallucination_bench_haiku_game.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evaluation.src.data.builders.hallucination_bench import _case_id  # noqa: E402

GAME = "403f4dbc-4a16-45fc-bb22-1c5e67bd5936"
OUT = Path("evidence/game_play_enhancement/data/haiku_turn_replay/cases.jsonl")

_ONLY_MESSAGE = (" This expectation is about the public chat message only: a private strategy note or a read "
                 "meets it whatever it says.")

_D3_DIRECTION = (
    "On night 2 player_9 (claiming sentinel) watched player_6 and saw player_4 and player_8 come to player_6. "
    "player_6 says it visited nobody on night 2: a statement about where player_6 went. A watch shows only who "
    "came to the watched player, never where that player went, so the watch neither contradicts nor supports "
    "player_6's statement. Violates: treating player_6's statement as a claim that no one visited player_6, or "
    "saying the watch (two visitors at player_6's door) contradicts or disproves player_6's statement that it "
    "visited nobody. Meets: anything that keeps the two directions apart, including doubting player_6 on other "
    "grounds.")
_N4_EMPTY_WATCH = (
    "player_9 (claiming sentinel) watched player_3 on night 4 and saw no one come to player_3. A watch shows only "
    "who came to player_3; it says nothing about where player_3 went or whether player_3 acted. The night 4 kill "
    "on player_7 was made by a reanimated wolf, through a dead player's body. Violates: treating the empty watch "
    "as evidence that player_3 did nothing, stayed home or did not act on night 4, or as a reason player_3 is "
    "unlikely to be the necromancer. Meets: anything else.")

_D3_FACTS = (
    "Facts on this turn: player_4 claims investigator with a Suspicious result on player_6 (night 2); player_9 "
    "claims sentinel and saw player_4 and player_8 come to player_6 on night 2; player_6 says it visited no one "
    "on night 2; on day 2 player_6 was the only player to vote for anyone (player_2), everyone else abstained. "
    "A watch shows only who came to the watched player. Violates: misstating any of these facts, or saying the "
    "watch contradicts player_6's statement that it visited no one. Meets: anything else, including passing.")
_D4_FACTS = (
    "Facts on this turn: on day 3 player_1 and player_6 voted to eliminate player_4, and the other seven voted "
    "player_6, who was eliminated and was the illusionist. On night 3 player_4 (investigator) was killed by the "
    "wolves, and player_5 was killed by a reanimated wolf with the role hidden. player_9 (claiming sentinel) says "
    "it was roleblocked on night 3. Violates: misstating any of these votes, deaths or claims. Meets: anything "
    "else, including passing.")
_D5_FACTS = (
    "Facts on this turn: on day 4 player_1 was eliminated and was the chanteuse (player_2, player_7, player_9 and "
    "player_10 voted player_1; player_1 voted player_3; player_3 abstained). On night 4 player_7 (healer) was "
    "killed by a reanimated wolf. player_9 (claiming sentinel) said this morning that its night 4 watch on "
    "player_3 saw no one come to player_3. A watch shows only who came to the watched player. Violates: "
    "misstating these facts, or treating player_9's empty watch as evidence that player_3 did not act. Meets: "
    "anything else, including passing.")

TURNS = [
    # visit: the direction of a visit
    {"day": 3, "seq": 14, "context": "origin", "speaker": "player_4", "kind": "positive", "slice": "visit", "golden": _D3_DIRECTION},
    {"day": 3, "seq": 18, "context": "cascade", "speaker": "player_4", "kind": "positive", "slice": "visit", "golden": _D3_DIRECTION},
    {"day": 3, "seq": 19, "context": "cascade", "speaker": "player_9", "kind": "positive", "slice": "visit", "golden": _D3_DIRECTION},
    {"day": 3, "seq": 15, "context": "cascade", "speaker": "player_9", "kind": "control", "slice": "visit", "golden": _D3_DIRECTION},
    {"day": 5, "seq": 2, "context": "origin", "speaker": "player_9", "kind": "positive", "slice": "visit", "golden": _N4_EMPTY_WATCH},
    {"day": 6, "seq": 3, "context": "origin", "speaker": "player_2", "kind": "positive", "slice": "visit", "golden": _N4_EMPTY_WATCH},
    {"day": 6, "seq": 5, "context": "cascade", "speaker": "player_10", "kind": "control", "slice": "visit", "golden": _N4_EMPTY_WATCH},
    # repeat: restating what one already said, asking again what was answered
    {"day": 3, "seq": 15, "context": "cascade", "speaker": "player_9", "kind": "positive", "slice": "repeat", "golden": (
        "Earlier today player_9 already gave its whole record twice (entries 7 and 13): night 1 it watched nobody; "
        "night 2 its watch on player_6 saw player_4 and player_8. It has already answered player_1's question about "
        "night 1. Violates: restating the night 1 or night 2 result again in full or re-explaining it. Meets: a "
        "brief pointer back (\"as I said\"), answering only something not yet answered, or saying it was already "
        "answered." + _ONLY_MESSAGE)},
    {"day": 3, "seq": 19, "context": "cascade", "speaker": "player_9", "kind": "positive", "slice": "repeat", "golden": (
        "Earlier today player_9 already gave its whole record three times (entries 7, 13 and 15): night 1 it watched "
        "nobody; night 2 its watch on player_6 saw player_4 and player_8. player_6 has just asked again what the "
        "night 1 watch showed, which player_9 already answered. Violates: restating the night 1 or night 2 result "
        "again in full or re-explaining it. Meets: a brief pointer back (\"as I said, nothing on night 1\"), "
        "something new, or saying it was already answered." + _ONLY_MESSAGE)},
    {"day": 3, "seq": 18, "context": "cascade", "speaker": "player_4", "kind": "positive", "slice": "repeat", "golden": (
        "Earlier today player_4 already said three times (entries 3, 11 and 14) that its only check was player_6 on "
        "night 2 and it read Suspicious, and that player_9's watch puts it at player_6's door. player_6 has just "
        "asked it to say plainly whether it checked anyone on night 1. Violates: restating the Suspicious result or "
        "the watch at length again. Meets: answering the night 1 question plainly, with at most a brief pointer "
        "back to the rest." + _ONLY_MESSAGE)},
    {"day": 3, "seq": 12, "context": "origin", "speaker": "player_6", "kind": "positive", "slice": "repeat", "golden": (
        "player_6 asked player_4 and player_9 (entry 9) what they checked or watched on night 1. player_4 has "
        "already answered (entry 11): its only check so far was player_6 on night 2, so it checked no one on night "
        "1. player_9 has not answered yet. Violates: asking player_4 again what it checked on night 1. Meets: "
        "anything else, including asking player_9 about night 1." + _ONLY_MESSAGE)},
    {"day": 3, "seq": 17, "context": "cascade", "speaker": "player_6", "kind": "positive", "slice": "repeat", "golden": (
        "Both have answered player_6's night 1 question: player_4 (entries 11 and 14) that its only check was "
        "player_6 on night 2, and player_9 (entries 13 and 15) that it watched nobody on night 1. Violates: asking "
        "player_4 or player_9 again what they did on night 1. Meets: anything else." + _ONLY_MESSAGE)},
    {"day": 6, "seq": 9, "context": "cascade", "speaker": "player_10", "kind": "positive", "slice": "repeat", "golden": (
        "Earlier today player_10 already said (entries 5 and 7) that it has no night action and visited nobody on "
        "nights 4 and 5, and that a watch on player_3 shows only who came to player_3. player_2 has just asked who "
        "player_10 thinks the necromancer is. Violates: restating those points again in full. Meets: answering "
        "player_2's question, with at most a brief pointer back." + _ONLY_MESSAGE)},
    # vote_reason: a town seat on the open floor of a voting day (it passed, then voted a player out)
    {"day": 3, "seq": 21, "context": "cascade", "speaker": "player_5", "kind": "positive", "slice": "vote_reason", "golden": _D3_FACTS},
    {"day": 3, "seq": 22, "context": "cascade", "speaker": "player_7", "kind": "positive", "slice": "vote_reason", "golden": _D3_FACTS},
    {"day": 4, "seq": 8, "context": "origin", "speaker": "player_2", "kind": "positive", "slice": "vote_reason", "golden": _D4_FACTS},
    {"day": 4, "seq": 10, "context": "origin", "speaker": "player_7", "kind": "positive", "slice": "vote_reason", "golden": _D4_FACTS},
    {"day": 5, "seq": 4, "context": "cascade", "speaker": "player_2", "kind": "positive", "slice": "vote_reason", "golden": _D5_FACTS},
]


# The state keys a discussion turn is built from (as phase3_turn_cases.py keeps them); the rest of a
# checkpoint (pending sends, scheduler scratch) is not part of a turn's input.
_KEEP = ("roles", "lineup", "current_day", "current_round", "human_players", "day_channel", "day_summaries",
         "dead_roster", "night_actions", "wolf_channel", "agent_strategies", "uses_left", "speculator_pick",
         "fortune_points", "surviving_wolves", "surviving_villagers")


def _plain(value):
    """A checkpoint value as JSON: pydantic models dumped, containers walked."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    return value


def day_states() -> list[dict]:
    """Every day-phase checkpoint of the game, as JSON states."""
    import psycopg
    from dotenv import dotenv_values
    from langgraph.checkpoint.postgres import PostgresSaver
    from psycopg.rows import dict_row

    from Agents.memory.checkpointer import durable_serde

    dsn = dotenv_values(".env")["WW_POSTGRES_DSN"]
    states = []
    with psycopg.connect(dsn, autocommit=True, row_factory=dict_row,
                         options="-c default_transaction_read_only=on") as conn:
        saver = PostgresSaver(conn, serde=durable_serde())
        namespaces = [r["checkpoint_ns"] for r in conn.execute(
            "select distinct checkpoint_ns from checkpoints where thread_id=%s "
            "and checkpoint_ns like 'DAY_PHASE:%%'", (GAME,)).fetchall()]
        for ns in namespaces:
            for t in saver.list({"configurable": {"thread_id": GAME, "checkpoint_ns": ns}}):
                values = t.checkpoint["channel_values"]
                states.append({k: _plain(values[k]) for k in _KEEP if k in values})
    return states


def state_before(states: list[dict], day: int, seq: int) -> tuple[dict, dict]:
    """(state, the original entry): the day's state just before entry ``seq``. An opening-round turn
    saw none of the day's lines, so its state is the one with today's channel empty."""
    full = max((s for s in states if s.get("current_day") == day), key=lambda s: len(s.get("day_channel", [])))
    entry = next(m for m in full["day_channel"] if m["day"] == day and m["seq"] == seq)
    upto = -1 if entry["day_round"] == "opening" else seq - 1
    for s in states:
        today = [m["seq"] for m in s.get("day_channel", []) if m["day"] == day]
        if s.get("current_day") == day and (max(today) if today else -1) == upto and s.get("surviving_villagers"):
            return s, entry
    sys.exit(f"no checkpoint just before day {day} entry {seq}")


def main() -> None:
    states = day_states()
    cases = []
    for t in TURNS:
        state, entry = state_before(states, t["day"], t["seq"])
        assert entry["player"] == t["speaker"], (t, entry["player"])
        firing = entry.get("firing_reason") or {"tier": "proactive", "owes": []}
        cases.append({
            "case_id": _case_id(f"haiku_{t['slice']}", GAME[:8], t["day"], t["speaker"], t["seq"]),
            "source": "live_checkpoint", "kind": t["kind"], "slice": t["slice"], "context": t["context"],
            "game_id": GAME[:8], "game_arm": "haiku_live", "phase": "day_discussion", "day": t["day"],
            "speaker": t["speaker"], "role": state["roles"][t["speaker"]],
            "state": state, "firing_reason": firing,
            "memory": {"observations": [], "strategy_points": []},
            "facts": {}, "golden": t["golden"],
            "original": [entry.get("message") or "(passed)"], "original_round": entry["day_round"],
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(c) for c in cases) + "\n")
    print(f"{len(cases)} cases -> {OUT}")


if __name__ == "__main__":
    main()
