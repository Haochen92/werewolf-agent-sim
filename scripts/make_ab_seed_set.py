"""Mint the paired memory-A/B shared seed set.

20 recovered baseline game_ids (from the frozen extraction set, with their recorded
baseline winner) + 10 fresh uuid4s. Pinning these game_ids across the A/B arms makes
every arm play identical role draws (verified 2026-06-11: a game_id reproduces its
role draw exactly), so the off/on outcomes pair for McNemar.

Run ONCE to freeze the set, then commit the artifacts. Outputs (under
evidence/memory_system/effectiveness/paired_ab/):
  seed_set.json           - full record: recovered (+baseline winner), fresh, all 30
  arms_game_ids.json      - {"game_ids":[30]} -> run_batch --game-ids-file for the 3 arms
  baseline_fresh_ids.json - {"game_ids":[10]} -> run_batch --game-ids-file for the 10 fresh baseline
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FROZEN = "evaluation/frozen_eval_sets/extraction/extraction_v5_0.jsonl"
OUT = Path("evidence/memory_system/effectiveness/paired_ab")
N_FRESH = 10


def main() -> int:
    recovered = [
        {"game_id": r["game_id"], "baseline_winner": r.get("game_outcome")}
        for r in (json.loads(line) for line in open(FROZEN))
    ]
    fresh = [str(uuid.uuid4()) for _ in range(N_FRESH)]
    all_ids = [r["game_id"] for r in recovered] + fresh
    assert len(set(all_ids)) == len(all_ids), "duplicate game_id in seed set"

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "seed_set.json").write_text(json.dumps({
        "description": (
            "Paired memory-A/B shared seed set. 20 recovered baseline game_ids "
            "(with recorded baseline winner) + 10 fresh. Pin across arms for McNemar."
        ),
        "recovered": recovered,
        "fresh_game_ids": fresh,
        "all_game_ids": all_ids,
    }, indent=2))
    (OUT / "arms_game_ids.json").write_text(json.dumps({"game_ids": all_ids}, indent=2))
    (OUT / "baseline_fresh_ids.json").write_text(json.dumps({"game_ids": fresh}, indent=2))

    print(f"recovered={len(recovered)} fresh={len(fresh)} total={len(all_ids)}")
    winners = {}
    for r in recovered:
        winners[r["baseline_winner"]] = winners.get(r["baseline_winner"], 0) + 1
    print(f"recovered baseline winners: {winners}")
    print(f"written to {OUT}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
