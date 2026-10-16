"""Freeze the bench cases for the Haiku effort replay: thinking low (live) against medium, on the
failures of both Haiku 5.5 games.

Record: evidence/reasoning_failures/experiment_log.md. The turns and votes of 403f4dbc
(§8.6, §8.7) are taken as frozen. Added here from 2f19d908 (2026-10-14, Haiku in all ten seats,
memory on, town won day 3), whose day 3 turned on the healer (seat 8):

- claim_read: seat 4 listed seat 8 among the "unclaimed" after seat 8 had called its night-2 visit
  protection, and argued the protection was pointless because its target was roleblocked;
- visit: the trailseer called seat 8 "worth watching" because the chanteuse had visited seat 8;
- self_reference: seat 8 said "I'm not voting player_8";
- votes: the investigator voted the healer who protected it, citing "accused by three players" from
  the moderator's closing line (one of the three had withdrawn, one was a question). The day-3
  votes are frozen twice: as played, and with the closing line the engine now writes (no accusers
  named, 2026-10-16), so the replay also measures that fix.

  poetry run python evaluation/experiments/haiku_effort_cases.py
  poetry run eval-hallucination-bench --config evaluation/config/hallucination_bench_haiku_effort_turns.json
  poetry run eval-hallucination-bench --config evaluation/config/hallucination_bench_haiku_effort_votes.json
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import evaluation.experiments.haiku_game_turn_cases as turns  # noqa: E402
from evaluation.experiments.haiku_vote_cases import pre_vote_state  # noqa: E402
from evaluation.src.data.builders.hallucination_bench import _case_id  # noqa: E402

GAME = "2f19d908-a6b3-4faf-8f16-c2a009bb0428"
OUT = Path("evidence/reasoning_failures/data/haiku_effort_replay")
FROZEN_403F = {
    "turn_cases.jsonl": Path("evidence/game_play_enhancement/data/haiku_turn_replay/cases.jsonl"),
    "vote_cases.jsonl": Path("evidence/game_play_enhancement/data/haiku_vote_replay/cases.jsonl"),
}
CLOSING_NOW = "Before the vote: player_8 gets a last word."

_ONLY_MESSAGE = (" This expectation is about the public chat message only: a private strategy note or a read "
                 "meets it whatever it says.")

_D3_CLAIMS = (
    "Facts on this turn: in entry 8 player_8 said its night 2 visit to player_5 was protection, a healer's "
    "action, and player_2 (claiming sentinel) watched player_5 on night 2 and saw player_7 and player_8 come to "
    "it, so the visit is confirmed. player_5 (claiming investigator) says it was roleblocked on night 2; "
    "player_7, dead as the chanteuse (a roleblocker), visited it. A roleblock stops the blocked player's own "
    "action, not an attack on that player, so protecting a roleblocked player is not pointless. Violates: "
    "listing player_8 among the players who have made no claim or given no account of their night, or arguing "
    "that player_8's protection was pointless, impossible or a lie because player_5 was blocked. Meets: anything "
    "else, including suspecting player_8 on other stated grounds." + _ONLY_MESSAGE)
_D2_FOLLOW = (
    "player_3 (trailseer) followed player_7 on night 1 and saw player_7 go to player_8. A follow shows where "
    "player_7 went: player_8 is the player visited, not the one who acted, so the follow is no evidence that "
    "player_8 is evil. Violates: presenting player_8 as suspicious, worth watching or a suspect because player_7 "
    "visited them. Meets: anything else, including suspecting player_7 or reporting the follow plainly."
    + _ONLY_MESSAGE)
_D3_SELF = (
    "The speaker is player_8, the healer. Night 1 it tried to protect player_5 and was roleblocked; night 2 it "
    "protected player_5 and was not blocked, and no attack on player_5 was announced. player_4 has just said it "
    "would vote player_8. Violates: speaking of player_8 as a different player (for example \"I'm not voting "
    "player_8\" or \"player_8 should explain\"), or claiming a night action or result other than these. Meets: "
    "anything else." + _ONLY_MESSAGE)
_D3_VOTE = (
    "Facts on this turn: both wolves are dead (player_9 the illusionist, voted out on day 2; player_7 the "
    "chanteuse, struck by a sigil on night 2), so the serial killer is the evil player left. Claims, none "
    "contested: player_2 sentinel (night 2 watch on player_5 saw player_7 and player_8), player_4 sigilist (its "
    "night 2 sigil struck player_7), player_5 investigator (night 1 Suspicious on player_9, borne out by the "
    "illusionist reveal; roleblocked on night 2), player_8 healer (protected player_5 on night 2; the sentinel's "
    "watch confirms the visit). player_6 and player_10 have made no role claim. On night 1 the trailseer "
    "(dead) saw player_7, the chanteuse, go to player_8. Violates: misstating these facts; saying player_8 made "
    "no claim; calling player_8's healer claim unverified or unsupported without naming evidence that tells it "
    "apart from the other claims; or treating player_7's night 1 visit to player_8 as evidence against player_8. "
    "Meets: anything else.")

# (day, entry seq, speaker, kind, slice, context, golden)
TURNS = [
    (3, 12, "player_4", "positive", "claim_read", "origin", _D3_CLAIMS),
    (3, 10, "player_10", "control", "claim_read", "origin", _D3_CLAIMS),
    (3, 11, "player_2", "control", "claim_read", "origin", _D3_CLAIMS),
    (2, 10, "player_3", "positive", "visit", "origin", _D2_FOLLOW),
    (3, 13, "player_8", "positive", "self_reference", "origin", _D3_SELF),
]
# (voter, kind): day 3; the right vote is player_6, the serial killer.
VOTES = [("player_5", "positive"), ("player_2", "control"), ("player_4", "control"),
         ("player_10", "control"), ("player_8", "control")]


def _turn_cases(states: list[dict]) -> list[dict]:
    cases = []
    for day, seq, speaker, kind, slice_, context, golden in TURNS:
        state, entry = turns.state_before(states, day, seq)
        assert entry["player"] == speaker, (day, seq, entry["player"])
        cases.append({
            "case_id": _case_id(f"haiku_{slice_}", GAME[:8], day, speaker, seq),
            "source": "live_checkpoint", "kind": kind, "slice": slice_, "context": context,
            "game_id": GAME[:8], "game_arm": "haiku_live", "phase": "day_discussion", "day": day,
            "speaker": speaker, "role": state["roles"][speaker], "state": state,
            "firing_reason": entry.get("firing_reason") or {"tier": "proactive", "owes": []},
            "memory": {"observations": [], "strategy_points": []},
            "facts": {}, "golden": golden,
            "original": [entry.get("message") or "(passed)"], "original_round": entry["day_round"],
        })
    return cases


def _vote_cases(states: list[dict]) -> list[dict]:
    played, ballots = pre_vote_state(states, 3)
    now = copy.deepcopy(played)
    (closing,) = [m for m in now["day_channel"]
                  if m["day"] == 3 and m["player"] == "game_master" and m["message"].startswith("Before the vote")]
    closing["message"] = CLOSING_NOW
    cases = []
    for variant, state in (("vote", played), ("vote_closing_now", now)):
        for voter, kind in VOTES:
            cases.append({
                "case_id": _case_id(f"haiku_{variant}", GAME[:8], 3, voter, -1),
                "source": "live_checkpoint", "kind": kind, "slice": variant, "context": "day3",
                "game_id": GAME[:8], "game_arm": "haiku_live", "phase": "day_vote", "day": 3,
                "speaker": voter, "role": state["roles"][voter], "state": state,
                "memory": {"observations": [], "strategy_points": []},
                "facts": {}, "golden": _D3_VOTE, "original": [ballots[voter]], "original_round": "vote",
            })
    return cases


def main() -> None:
    turns._KEEP = turns._KEEP + ("day_votes",)  # the ballots, to tell the pre-vote checkpoint apart
    states = turns.day_states(GAME)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, new in (("turn_cases.jsonl", _turn_cases(states)), ("vote_cases.jsonl", _vote_cases(states))):
        frozen = [line for line in FROZEN_403F[name].read_text().splitlines() if line.strip()]
        (OUT / name).write_text("\n".join(frozen + [json.dumps(c) for c in new]) + "\n")
        print(f"{name}: {len(frozen)} from 403f4dbc + {len(new)} from 2f19d908")
        for c in new:
            print(f"  [{c['slice']}] day {c['day']} {c['speaker']} ({c['role']}): {c['original'][0][:90]}")


if __name__ == "__main__":
    main()
