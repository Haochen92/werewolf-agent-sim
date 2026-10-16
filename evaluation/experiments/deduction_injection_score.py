"""Score case R1's replay: does the healer reason through once its night record states the roleblock's
certain consequence?

Record: evidence/reasoning_failures/experiment_log.md (case R1). The measures were fixed before the
run, per arm, variant (as_played / injected) and turn:

- spoke: the turn produced a public message (the game's healer passed all three);
- claimed healer: the structured claim field;
- read player_7 as chanteuse: the structured read's suspected role;
- named player_7: the message mentions player_7 together with a block or the chanteuse. This is a
  mention count to find the messages; every message is printed, and the record's verdict on them is
  a hand read.

The silence test (healer_silence: the healer's note as played or neutral, by the healer card as is or
without its survival sentence) is scored the same way.

  poetry run python evaluation/experiments/deduction_injection_score.py [--run healer_silence] [--messages]
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

RESULTS = Path("evaluation/eval_results/hallucination_bench")
DATA = Path("evidence/reasoning_failures/data/deduction_injection")
RUNS = {  # run label -> (its cases, its arms)
    "deduction_injection": (DATA / "cases.jsonl", ["haiku_low", "haiku_medium"]),
    "healer_silence": (DATA / "silence_cases.jsonl", ["card_as_is", "card_no_survival"]),
}
_NAMED = re.compile(r"player_7\b[^.]*\b(block|chanteuse)|\b(block|chanteuse)[^.]*player_7\b", re.I)


def _unit(sample: dict, name: str) -> str:
    return next((u["text"] for u in sample["units"] if u["unit"] == name), "")


def main(run: str, show: bool) -> None:
    cases_path, arms = RUNS[run]
    cases = {c["case_id"]: c for c in map(json.loads, cases_path.read_text().splitlines())}
    for arm in arms:
        path = RESULTS / run / f"generations_{arm}.jsonl"
        if not path.exists():
            continue
        rows = defaultdict(list)
        for s in map(json.loads, path.read_text().splitlines()):
            if s["valid"]:
                c = cases[s["case_id"]]
                rows[c["context"][:40], c["slice"]].append(s)
        print(f"== {arm}")
        for (context, variant), samples in sorted(rows.items()):
            n = len(samples)
            spoke = [s for s in samples if _unit(s, "message")]
            claimed = sum(s.get("claim") == "healer" for s in samples)
            read7 = sum(bool(re.search(r"^player_7: chanteuse", _unit(s, "reads"), re.M)) for s in samples)
            named = sum(bool(_NAMED.search(_unit(s, "message"))) for s in samples)
            print(f"  [{variant:14}] {context}: spoke {len(spoke)}/{n}, claimed healer {claimed}/{n}, "
                  f"read player_7 chanteuse {read7}/{n}, message names player_7 as blocker {named}/{n}")
            if show:
                for s in spoke:
                    print(f"      - {_unit(s, 'message')}")


if __name__ == "__main__":
    args = sys.argv[1:]
    main(args[args.index("--run") + 1] if "--run" in args else "deduction_injection", "--messages" in args)
