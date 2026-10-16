"""Score the Haiku effort replay's votes by their target: no judge.

Record: evidence/reasoning_failures/experiment_log.md. A vote is right when it names the
actual threat (``vote_target`` is limited to the legal targets, so this is an exact match): in
403f4dbc as in haiku_vote_score.py, in 2f19d908 player_6 (the serial killer) on day 3. Cases come
from evaluation/experiments/haiku_effort_cases.py; the arms are thinking low (live) and medium.

  poetry run python evaluation/experiments/haiku_effort_score.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

RESULTS = Path("evaluation/eval_results/hallucination_bench/haiku_effort_votes")
CASES = Path("evidence/reasoning_failures/data/haiku_effort_replay/vote_cases.jsonl")
RIGHT = {("403f4dbc", 3): "player_6", ("403f4dbc", 4): "player_1", ("403f4dbc", 5): "player_3",
         ("403f4dbc", 6): "player_3", ("2f19d908", 3): "player_6"}
ARMS = ["haiku_low", "haiku_medium"]


def main() -> None:
    cases = {c["case_id"]: c for c in map(json.loads, CASES.read_text().splitlines())}
    for arm in ARMS:
        samples = [s for s in map(json.loads, (RESULTS / f"generations_{arm}.jsonl").read_text().splitlines())
                   if s["valid"]]
        print(f"== {arm} ({len(samples)} samples)")
        groups = Counter()
        for cid, c in cases.items():
            right_target = RIGHT[c["game_id"], c["day"]]
            votes = Counter(s["vote"] for s in samples if s["case_id"] == cid)
            right = votes.get(right_target, 0)
            group = (c["game_id"], c["slice"], c["kind"])
            groups[group, "right"] += right
            groups[group, "n"] += sum(votes.values())
            print(f"  {c['game_id']} [{c['slice']}] day {c['day']} {c['speaker']} ({c['role']}, {c['kind']}, "
                  f"voted {c['original'][0]}): right {right}/{sum(votes.values())}  {dict(votes)}")
        for group in sorted({g for g, _ in groups}):
            print(f"  {' '.join(group)}: right {groups[group, 'right']}/{groups[group, 'n']}")
        out = [s["usage"]["output"] for s in samples if s.get("usage")]
        print(f"  output tokens per vote: {sum(out) / len(out):.0f}")


if __name__ == "__main__":
    main()
