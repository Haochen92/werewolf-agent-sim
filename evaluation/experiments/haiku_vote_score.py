"""Score the replayed votes of game 403f4dbc by their outcome: no judge.

Record: evidence/game_play_enhancement/discussion_evidence.md §8.7. The vote is a structured field
(``vote_target``, limited to the legal targets), so a vote is right when it names the actual threat:
player_6 (illusionist) on day 3, player_1 (chanteuse) on day 4, player_3 (the Necromancer) on days 5
and 6. Beside it, a regex count over the free-text reads of the evidence each vote rests on (a mention
count, not a judgment of soundness).

  poetry run python evaluation/experiments/haiku_vote_score.py [arm ...]
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

RESULTS = Path("evaluation/eval_results/hallucination_bench/haiku_vote_compare")
CASES = Path("evidence/game_play_enhancement/data/haiku_vote_replay/cases.jsonl")
RIGHT = {3: "player_6", 4: "player_1", 5: "player_3", 6: "player_3"}
ARMS = ["haiku_pre_fixes", "haiku_layout_baseline", "haiku_current", "haiku_read_compare", "haiku_ballot_tag"]

# What a vote can rest on, per (day, voter or None for every voter): the read of whom, and the pattern.
CITES = {
    "d4: player_1's read cites its vote on the investigator": (4, None, "player_1", r"player_4"),
    "d5 vigilante: player_3's read cites its day-4 abstain": (5, "player_2", "player_3", r"abstain"),
    "d5 vigilante: player_3's read says nothing separates it": (
        5, "player_2", "player_3", r"(not|nothing|no evidence)[^.;]*(separat|distinguish)|no distinguishing"),
    "d5 vigilante: player_3's read says it voted out player_4 (false)": (
        5, "player_2", "player_3", r"(eliminate|voted)[^.;]*player_4"),
    "d6 vigilante: player_3's read cites the sentinel's vote on it": (
        6, "player_2", "player_3", r"(player_9|sentinel)[^.;]*vot|vot[^.;]*(player_9|sentinel)"),
}


def _read_of(sample: dict, player: str) -> str:
    reads = next((u["text"] for u in sample["units"] if u["unit"] == "reads"), "")
    return next((line for line in reads.split("\n") if line.startswith(player + ":")), "")


def main(arms: list[str]) -> None:
    cases = {c["case_id"]: c for c in map(json.loads, CASES.read_text().splitlines())}
    for arm in arms:
        path = RESULTS / f"generations_{arm}.jsonl"
        if not path.exists():
            continue
        samples = [s for s in map(json.loads, path.read_text().splitlines()) if s["valid"]]
        print(f"== {arm} ({len(samples)} samples)")
        for cid, c in cases.items():
            votes = Counter(s["vote"] for s in samples if s["case_id"] == cid)
            right = votes.get(RIGHT[c["day"]], 0)
            print(f"  day {c['day']} {c['speaker']} ({c['role']}, voted {c['original'][0]}): "
                  f"right {right}/{sum(votes.values())}  {dict(votes)}")
        by_day = Counter()
        for s in samples:
            day = cases[s["case_id"]]["day"]
            by_day[day, "n"] += 1
            by_day[day, "right"] += s["vote"] == RIGHT[day]
        print("  right by day: " + ", ".join(f"day {d} {by_day[d, 'right']}/{by_day[d, 'n']}" for d in (3, 4, 5, 6)))
        for label, (day, voter, about, pattern) in CITES.items():
            pool = [s for s in samples if cases[s["case_id"]]["day"] == day
                    and (voter is None or cases[s["case_id"]]["speaker"] == voter)]
            hits = sum(bool(re.search(pattern, _read_of(s, about), re.I)) for s in pool)
            print(f"  {label}: {hits}/{len(pool)}")
        out = [s["usage"]["output"] for s in samples if s.get("usage")]
        print(f"  output tokens per vote: {sum(out) / len(out):.0f}")


if __name__ == "__main__":
    main(sys.argv[1:] or ARMS)
