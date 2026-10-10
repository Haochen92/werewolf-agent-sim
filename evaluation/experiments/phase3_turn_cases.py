"""Freeze the Phase 3 reasoning failures as hallucination-bench cases, without playing new games.

Each case is one discussion turn from a captured ten-seat game (evidence/game_play_enhancement/
data/phase3_*), frozen as the game state the engine held just before the speaker spoke: the
transcript up to that line, the earlier summaries, the dead roster, the night records, the pack's
chat, the uses left, the speaker's strategy note. The state is rebuilt from the game's record and
its stream of chunks, and written in the bench's case format, so the bench's replay
(``evaluation/src/replay/hallucination_bench.py``) rebuilds the turn with today's builders and
prompts, and its golden judge reads every sample against the case's hand-written expectation.

The turns were found by reading five games by hand (phase3_reads/README.md). Positives are lines
that broke the expectation; controls are lines on the same evidence that kept it. A round turn
(opening, closing) is replayed as a sweep turn: the bench rebuilds discussion turns only.

  poetry run python evaluation/experiments/phase3_turn_cases.py
  poetry run eval-hallucination-bench --config evaluation/config/hallucination_bench_phase3_turns.json
"""

from __future__ import annotations

import json
from pathlib import Path

from evaluation.src.data.builders.hallucination_bench import _case_id, _facts

MAIN = Path(__file__).resolve().parents[2]
DATA = MAIN / "evidence/game_play_enhancement/data"
OUT = DATA / "phase3_turn_replay/cases.jsonl"

_WATCH_ONLY = ("A sentinel's watch shows only who visited the watched player. It cannot show what a visitor did "
               "there, what role the visitor holds, or whether a visitor's claimed result is true.")
_EMPTY_HOUSE = ("player_10 (sentinel) watched player_8 last night and saw no one visit them. A watch shows only who "
                "came to player_8. It says nothing about whether player_8 stayed home or went out.")

TURNS = [
    {"game": "phase3_balance_4/e04", "day": 2, "speaker": "player_3", "kind": "positive",
     "starts": "Player_1's watch confirms player_10 was physically",
     "golden": _WATCH_ONLY + " On this turn player_1 watched player_5 on night 1 and saw player_4 and player_10 "
               "visit; player_10 claims to be the investigator and player_8 counter-claims investigator. Violates: "
               "treating player_1's watch as support for player_10's investigator claim, or as evidence that "
               "player_8's counter-claim is false or rushed. Meets: keeping the visit and the role claim apart."},
    {"game": "phase3_balance_4/e04", "day": 2, "speaker": "player_1", "kind": "control",
     "starts": "I can confirm player_10 actually was at player_5",
     "golden": _WATCH_ONLY + " On this turn player_1 watched player_5 on night 1 and saw player_4 and player_10 "
               "visit; player_10 claims to be the investigator and player_8 counter-claims investigator. Violates: "
               "treating player_1's watch as support for player_10's investigator claim, or as evidence that "
               "player_8's counter-claim is false or rushed. Meets: keeping the visit and the role claim apart."},
    {"game": "phase3_balance_3/d03", "day": 3, "speaker": "player_9", "kind": "positive",
     "starts": "My investigation on Player 2 was completed",
     "golden": "player_9 claims investigator. player_1 (sentinel) saw player_3 and player_6 visit player_9, and "
               "player_3 (claimed healer) says they protected player_9. A watch and a protection show only who "
               "came to player_9 and that an attack on player_9 was stopped; neither can show what player_9's "
               "investigation returned. Violates: saying the watch or the protection proves, verifies or "
               "corroborates player_9's investigation results."},
    {"game": "phase3_balance/b02", "day": 4, "speaker": "player_10", "kind": "positive",
     "starts": "Player_8, a wolf carrier leaves home to make the kill, which means my watch",
     "golden": _EMPTY_HOUSE + " Violates: saying the watch shows player_8's house was empty, that player_8 left "
               "home, or that player_8 stayed home."},
    {"game": "phase3_balance/b02", "day": 4, "speaker": "player_9", "kind": "positive",
     "starts": "Player_10, your watch on player_8's empty house",
     "golden": _EMPTY_HOUSE + " Violates: saying the watch shows player_8's house was empty, that player_8 left "
               "home, or that player_8 stayed home."},
    {"game": "phase3_balance/b02", "day": 4, "speaker": "player_9", "kind": "positive",
     "starts": "Establishing player_3's lack of visits",
     "golden": "player_9 (trailseer) followed player_3 last night and saw player_3 visit no one. A fortune "
               "teller's bet, a speculator's pick and a declined action are not visits, so an empty trail does "
               "not show that player_3 used no night ability. Violates: saying the empty trail rules out, or "
               "shows, that player_3 used no night ability or did nothing at night."},
    {"game": "phase3_balance_4/e04", "day": 3, "speaker": "player_7", "kind": "positive",
     "starts": "Since player_10 died on night two",
     "golden": "player_10 (revealed chanteuse) was alive during night 2 and was shot that night; all night "
               "actions happen at once, so the block on player_3 on night 2 can be player_10's own. A necromancer "
               "can only act through a player who died on an earlier night. Violates: saying the night-2 block "
               "shows, or means, that a necromancer is using player_10's body."},
    {"game": "phase3_balance_4/e04", "day": 3, "speaker": "player_1", "kind": "control",
     "starts": "Player_7, player_10 was still alive to block player_3",
     "golden": "player_10 (revealed chanteuse) was alive during night 2 and was shot that night; all night "
               "actions happen at once, so the block on player_3 on night 2 can be player_10's own. A necromancer "
               "can only act through a player who died on an earlier night. Violates: saying the night-2 block "
               "shows, or means, that a necromancer is using player_10's body."},
    {"game": "phase3_balance_4/e06", "day": 3, "speaker": "player_3", "kind": "positive",
     "starts": "Player_2 claimed chanteuse on day two",
     "golden": "On day 2 player_2 said only: \"I was roleblocked last night, which confirms we have an active "
               "Chanteuse in play.\" player_2 never claimed or bluffed chanteuse, on any day. Today (day 3) "
               "player_2 has claimed investigator, and saying so is correct. Violates: saying or implying that "
               "player_2 claimed, bluffed or admitted to chanteuse."},
    {"game": "phase3_balance_4/e06", "day": 3, "speaker": "player_2", "kind": "positive",
     "starts": "I claimed chanteuse yesterday",
     "golden": "On day 2 player_2 said only: \"I was roleblocked last night, which confirms we have an active "
               "Chanteuse in play.\" player_2 never claimed or bluffed chanteuse, on any day, and player_2's own "
               "night record says they were roleblocked on night 1. Today (day 3) player_2 has claimed "
               "investigator, and saying so is correct. Violates: player_2 saying or accepting that they claimed, "
               "bluffed or admitted to chanteuse."},
]

# The f02 rule cases (2026-10-10): four players asserted that an illusionist's visit to hide a body
# is always seen, and voted out the real trailseer, whose empty trail on the illusionist was right (it
# had carried its own kill). The rule was then unstated; these cases test the sentence that states it.
_ILLUSIONIST_CARRIER = (
    "On night 2 player_2 was killed and concealed, and player_3 (claiming trailseer) says player_10 "
    "visited no one that night. Under the rules, an illusionist that carries the pack's kill itself and "
    "conceals that victim leaves no trace at that door: a trailseer following it sees no visit. So "
    "player_3's empty trail on player_10 is consistent with player_10 being that illusionist. Violates: "
    "saying an illusionist's visit to hide a body is always or never-hidden seen by a trailseer, or that "
    "player_3's empty trail on player_10 shows player_3 is lying. Meets: anything that allows the "
    "carrier exception or does not rest on that rule.")
TURNS += [
    {"game": "phase3_flash_games/f02", "day": 4, "speaker": "player_1", "kind": "positive", "slice": "f02_rule",
     "starts": "player_3, your claim has a major contradiction", "golden": _ILLUSIONIST_CARRIER},
    {"game": "phase3_flash_games/f02", "day": 4, "speaker": "player_7", "kind": "positive", "slice": "f02_rule",
     "starts": "player_9, player_1 and player_5 are entirely right", "golden": _ILLUSIONIST_CARRIER},
    {"game": "phase3_flash_games/f02", "day": 4, "speaker": "player_9", "kind": "positive", "slice": "f02_rule",
     "starts": "player_3, calling the rules 'textbook assumptions'", "golden": _ILLUSIONIST_CARRIER},
    {"game": "phase3_flash_games/f02", "day": 4, "speaker": "player_3", "kind": "control", "slice": "f02_rule",
     "starts": "player_7, you're joining this dogpile", "golden": _ILLUSIONIST_CARRIER},
]

# The sentinel's own visit (2026-10-10, the Luna games): the engine leaves a sentinel out of its own visitor
# list, the card said only "Watching is a visit", and the real sentinel conceded it should appear.
_SENTINEL_SELF = (
    "A sentinel is not among the visitors it is told of: its own watch never appears in its result, so a "
    "result that lists other visitors, or no one, and not the sentinel itself is exactly what a real "
    "sentinel gets. Violates: saying the sentinel should have appeared in its own visitor list, or that its "
    "result is incomplete, impossible or suspect for leaving the sentinel out.")
TURNS += [
    {"game": "phase3_luna_games/l01", "day": 2, "speaker": "player_1", "kind": "positive", "slice": "sentinel_rule",
     "starts": "player_3, was player_5 the full list", "golden": _SENTINEL_SELF},
    {"game": "phase3_luna_games/l01", "day": 2, "speaker": "player_3", "kind": "positive", "slice": "sentinel_rule",
     "starts": "I only saw player_5 listed", "golden": _SENTINEL_SELF},
    {"game": "phase3_luna_games/l04", "day": 2, "speaker": "player_5", "kind": "positive", "slice": "sentinel_rule",
     "starts": "There’s a direct issue with player_10’s Sentinel claim", "golden": _SENTINEL_SELF},
    {"game": "phase3_luna_games/l04", "day": 2, "speaker": "player_10", "kind": "positive", "slice": "sentinel_rule",
     "starts": "You’re right: watching is a visit", "golden": _SENTINEL_SELF},
]

_KEEP = ("agent_strategies", "uses_left", "speculator_pick", "fortune_points", "surviving_wolves",
         "surviving_villagers")


def _state_before(game: str, day: int, starts: str) -> tuple[dict, dict, dict]:
    """(state, the original entry, the record): the game state just before the line that starts with
    ``starts`` was spoken on ``day``."""
    record = json.load(open(DATA / f"{game}.record.json"))
    entry = next(m for m in record["day_channel"] if m["day"] == day and m["message"].startswith(starts))
    latest: dict = {"agent_strategies": {}}
    wolf_channel, summaries, dead = [], [], []
    seen_wolf, seen_summary, seen_dead = set(), set(), set()
    for line in open(DATA / f"{game}.chunks.jsonl"):
        chunk = json.loads(line)
        if chunk["type"] != "updates":
            continue
        reached = False
        for delta in (chunk["data"] or {}).values():
            if not isinstance(delta, dict):
                continue
            spoken = [*(delta.get("day_channel") or []),
                      *(c.get("entry") or {} for c in delta.get("round_candidates") or [])]
            if any(e.get("day") == day and (e.get("message") or "").startswith(starts) for e in spoken):
                reached = True
                break
            for key in _KEEP:
                if key == "agent_strategies" and delta.get(key):
                    latest[key].update(delta[key])
                elif key in delta and key != "agent_strategies":
                    latest[key] = delta[key]
            for e in delta.get("wolf_channel") or []:
                k = (e["day"], e["round"], e["wolf"], e.get("message"), e.get("vote"))
                if k not in seen_wolf:
                    seen_wolf.add(k); wolf_channel.append(e)
            for e in delta.get("day_summaries") or []:
                k = (e["day"], e.get("source"), e["summary"])
                if k not in seen_summary:
                    seen_summary.add(k); summaries.append(e)
            for e in delta.get("dead_roster") or []:
                if e["player"] not in seen_dead:
                    seen_dead.add(e["player"]); dead.append(e)
        if reached:
            break
    state = {
        "roles": record["roles"], "lineup": record["lineup"], "current_day": day, "current_round": 0,
        "human_players": [],
        "day_channel": [m for m in record["day_channel"]
                        if m["day"] < day or (m["day"] == day and m["seq"] < entry["seq"])],
        "day_summaries": [s for s in summaries if s["day"] < day],
        "dead_roster": dead,
        "night_actions": [a for a in record["night_actions"] if a["day"] < day],
        "wolf_channel": [e for e in wolf_channel if e["day"] < day],
        **{k: latest[k] for k in _KEEP if k in latest},
    }
    return state, entry, record


def main() -> None:
    cases = []
    for t in TURNS:
        state, entry, record = _state_before(t["game"], t["day"], t["starts"])
        label = t["game"].split("/")[1]
        firing = entry.get("firing_reason") or {"tier": "proactive", "owes": []}
        cases.append({
            "case_id": _case_id("phase3", label, t["day"], t["speaker"], entry["seq"]),
            "source": "phase3_capture", "kind": t["kind"],
            "slice": t.get("slice") or ("control" if t["kind"] == "control" else "pinned"),
            "game_id": label, "game_arm": "phase3", "phase": "day_discussion", "day": t["day"],
            "speaker": t["speaker"], "role": record["roles"][t["speaker"]],
            "state": state, "firing_reason": firing,
            "memory": {"observations": [], "strategy_points": []},
            "facts": _facts(record), "golden": t["golden"],
            "original": [entry["message"]], "original_round": entry.get("day_round", "discussion"),
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(c) for c in cases) + "\n")
    print(f"{len(cases)} cases -> {OUT}")


if __name__ == "__main__":
    main()
