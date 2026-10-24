"""Freeze the day votes of the owner's first Haiku 5.5 game as hallucination-bench cases.

Record: evidence/game_play_enhancement/discussion_evidence.md §8.7. Game 403f4dbc's day-5 vigilante
voted out the real sentinel because its claim was "unverified" (data/haiku_sentinel_vote/), and on
day 6 the Necromancer's late, uncontested sigilist claim carried the vote onto the town's speculator.
These cases test a read that compares the candidates against each other: the two day-5 ballots that
went wrong, the two day-6 ballots the bluff won, and controls (the day-5 sentinel, and three town seats
on each of days 3 and 4, whose votes were right).

Each case is the state the engine held just before the day's vote fan-out, read from the game's
LangGraph checkpoints (``haiku_game_turn_cases.day_states``, read-only). The bench scores the vote
target per sample (``vote``); the goldens guard the facts and name the reasoning errors in the reads
and the strategy note.

  poetry run python evaluation/experiments/haiku_vote_cases.py
  poetry run eval-hallucination-bench --config evaluation/config/hallucination_bench_haiku_vote_compare.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evaluation.experiments.haiku_game_turn_cases import GAME, _D3_FACTS, day_states  # noqa: E402
from evaluation.src.data.builders.hallucination_bench import _case_id  # noqa: E402

OUT = Path("evidence/game_play_enhancement/data/haiku_vote_replay/cases.jsonl")

_D4_VOTE = (
    "Facts on this turn: on day 3 player_1 and player_6 voted to eliminate player_4, and the other seven voted "
    "player_6, who was eliminated and was the illusionist. On night 3 player_4 (investigator) was killed by the "
    "wolves, and player_5 was killed by a reanimated wolf with the role hidden. player_9 (claiming sentinel) says "
    "it was roleblocked on night 3. Violates: misstating any of these votes, deaths or claims. Meets: anything "
    "else.")
_D5_VOTE = (
    "Facts on this turn: both wolves are dead (player_6 the illusionist, player_1 the chanteuse), so the living "
    "killer is the necromancer. player_9 claims sentinel; its night 2 watch on player_6 saw player_4 and player_8, "
    "which fits player_4's Suspicious check on player_6, and player_4 died as the investigator and player_6 as "
    "the illusionist. No one has counterclaimed sentinel. player_3 and player_10 have made no role claim. "
    "player_8 and player_5 died with their roles hidden. player_9 says its night 4 watch on player_3 saw no one "
    "come to player_3; a watch shows only who came to the watched player. Violates: calling player_9 the "
    "necromancer or the leading suspect on the ground that its claim is unverified or self-reported, without "
    "naming evidence that tells player_9 apart from player_3 and player_10; or treating the empty watch as "
    "evidence that player_3 did not act. Meets: anything else, including suspecting player_9 for a stated "
    "reason that distinguishes it, or saying the evidence does not distinguish them.")
_D6_VOTE = (
    "Facts on this turn: three players live, player_2, player_3 and player_10; the necromancer is one of them. "
    "On day 5 player_9 was eliminated and was the sentinel (player_2 and player_10 voted player_9, player_9 "
    "voted player_3, player_3 abstained). Today player_3 claimed sigilist for the first time, saying it placed a "
    "sigil on player_2 on night 2; a sigil only acts if its target attacks, and the sigilist's results are "
    "private, so no one can confirm the claim; player_5 died on night 3 with its role hidden, so the sigilist "
    "may be dead. player_10 says it has no night action. A watch shows only who came to the watched player. "
    "Violates: treating player_3's sigilist claim as confirmed or as clearing player_3; or treating player_9's "
    "empty watch on player_3 as evidence that player_3 did not act. Meets: anything else.")

# (day, voter, kind, golden): the vote the original seat cast is read from the checkpoint.
VOTES = [
    (5, "player_2", "positive", _D5_VOTE),   # voted player_9, the real sentinel
    (5, "player_10", "positive", _D5_VOTE),  # the speculator (picked Town): voted player_9 too
    (5, "player_9", "control", _D5_VOTE),    # the sentinel: voted player_3, the necromancer
    (6, "player_2", "positive", _D6_VOTE),   # voted player_10 after player_3's sigilist claim
    (6, "player_10", "positive", _D6_VOTE),  # voted player_2
    (3, "player_2", "control", _D3_FACTS),   # day 3: seven town votes on player_6, the illusionist
    (3, "player_7", "control", _D3_FACTS),
    (3, "player_9", "control", _D3_FACTS),
    (4, "player_2", "control", _D4_VOTE),    # day 4: four town votes on player_1, the chanteuse
    (4, "player_7", "control", _D4_VOTE),
    (4, "player_9", "control", _D4_VOTE),
]


def pre_vote_state(states: list[dict], day: int) -> tuple[dict, dict]:
    """(state, the day's ballots): the day's state at the vote fan-out (its full discussion, no ballot
    yet, without the ballot key), and the ballots a later checkpoint of the same discussion recorded."""
    today = [s for s in states if s.get("current_day") == day and s.get("surviving_villagers")]
    longest = max(len(s.get("day_channel", [])) for s in today)
    at_vote = [s for s in today if len(s.get("day_channel", [])) == longest]
    before = next(s for s in at_vote if not s.get("day_votes"))
    ballots = next(s["day_votes"] for s in at_vote if s.get("day_votes"))
    return {k: v for k, v in before.items() if k != "day_votes"}, {b["voter"]: b["votee"] for b in ballots}


def main() -> None:
    import evaluation.experiments.haiku_game_turn_cases as turns

    turns._KEEP = turns._KEEP + ("day_votes",)  # the ballots, to tell the pre-vote checkpoint apart
    states = day_states()
    cases = []
    for day, voter, kind, golden in VOTES:
        state, ballots = pre_vote_state(states, day)
        cases.append({
            "case_id": _case_id("haiku_vote", GAME[:8], day, voter, -1),
            "source": "live_checkpoint", "kind": kind, "slice": "vote_compare", "context": f"day{day}",
            "game_id": GAME[:8], "game_arm": "haiku_live", "phase": "day_vote", "day": day,
            "speaker": voter, "role": state["roles"][voter], "state": state,
            "memory": {"observations": [], "strategy_points": []},
            "facts": {}, "golden": golden, "original": [ballots[voter]], "original_round": "vote",
        })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(c) for c in cases) + "\n")
    print(f"{len(cases)} cases -> {OUT}")
    for c in cases:
        print(f"  day {c['day']} {c['speaker']} ({c['role']}): voted {c['original'][0]}")


if __name__ == "__main__":
    main()
