"""The v8 gate's relevance read: every memory lookup from the memory-on gate games, and a sample to read.

Record: evidence/memory_system/v8/experiment_log.md (the gate). Reads the games' local decision records
(run_batch's eval-case sidecars) and writes:

- ``lookups.jsonl``: one row per lookup (a seat's situation and the lessons it fetched), with every
  decision that was shown those lessons (a lookup is reused within a day's discussion and a night) and
  the seat's verdict on each lesson;
- ``sample/part_N.md``: a sample stratified by model, role and phase, for a reader (a Sonnet subagent,
  then the owner) to judge whether the lessons fit the situation, whether the situation states the board
  correctly, and whether anything leaks (a concealed role stated as fact, a player id in a lesson).

  poetry run python evaluation/experiments/v8_gate_lookups.py
"""

from __future__ import annotations

import glob
import json
import random
from collections import defaultdict
from pathlib import Path

MAIN = Path(__file__).resolve().parents[2]
GAMES = {"haiku": "batch_results/v8_gate_haiku/games_*.jsonl",
         "luna": "batch_results/v8_luna_memory/run2/game_*.jsonl"}
OUT = MAIN / "evidence/memory_system/v8/data/gate"
PER_CELL = 2      # lookups per (model, role, phase) in the sample
PARTS = 4         # files the sample is split into, one per reader
SEED = 20261012


def _cases_path(game: dict, batch_file: Path) -> Path:
    """The game's eval-case sidecar, copied beside its batch file (the run's worktree is gone)."""
    rel = Path(game["eval_cases_path"])
    return batch_file.parent / rel.relative_to("batch_results")


def _decision(case: dict) -> dict:
    act = case.get("agent_night_action") or case.get("agent_vote") or case.get("agent_message")
    return {"day": case["day"], "round": case.get("round"), "decision": act,
            "verdicts": case.get("strategy_verdicts") or []}


def collect() -> list[dict]:
    lookups: dict[tuple, dict] = {}
    for model, pattern in GAMES.items():
        for batch_file in map(Path, sorted(glob.glob(str(MAIN / pattern)))):
            for line in batch_file.read_text().splitlines():
                game = json.loads(line)
                if game.get("status") != "success":
                    continue
                for raw in _cases_path(game, batch_file).read_text().splitlines():
                    rec = json.loads(raw)
                    if rec["kind"] != "agent_action_eval":
                        continue
                    case = next(iter(rec["output"].values()))
                    if not case.get("retrieved_strategy_points"):
                        continue
                    key = (game["game_id"], case["player_id"], case["action_phase"], tuple(case["situations"]))
                    row = lookups.get(key)
                    if row is None:
                        row = lookups[key] = {
                            "model": model, "game_id": game["game_id"][:8], "lineup": game["lineup"],
                            "true_roles": game["roles"], "player_id": case["player_id"],
                            "role": case["player_role"], "phase": case["action_phase"], "day": case["day"],
                            "situations": case["situations"],
                            "query_dims": (case.get("situation_dimensions") or [{}])[0],
                            "lessons": [{"key": sp.get("key"), "score": round(sp.get("score") or 0, 3),
                                         "dimensions": sp["strategy_point"].get("dimensions") or {},
                                         "situation": sp["strategy_point"]["situation"],
                                         "action": sp["strategy_point"]["action"]}
                                        for sp in case["retrieved_strategy_points"]],
                            "decisions": [],
                        }
                    row["decisions"].append(_decision(case))
    return list(lookups.values())


def _render(i: int, row: dict) -> str:
    lines = [f"## Lookup {i}: {row['model']} game {row['game_id']}, {row['player_id']} the {row['role']}, "
             f"{row['phase']}, day {row['day']}",
             f"True roles (the reader's ground truth, not known to the seat): "
             + ", ".join(f"{p} {r}" for p, r in sorted(row["true_roles"].items(), key=lambda x: int(x[0].split('_')[1]))),
             "", "**Situation(s) the seat wrote:**"]
    lines += [f"{n}. {s}" for n, s in enumerate(row["situations"], 1)]
    lines += ["", "**Lessons fetched:**"]
    for n, les in enumerate(row["lessons"], 1):
        lines += [f"{n}. (score {les['score']}) *When:* {les['situation']}", f"   *Do:* {les['action']}"]
    lines += ["", "**Decisions shown these lessons, with the seat's verdicts:**"]
    for d in row["decisions"]:
        verdicts = "; ".join(f"#{v.get('strategy_index')} {v.get('verdict')}: {v.get('why', '')}" for v in d["verdicts"])
        lines.append(f"- day {d['day']} round {d['round']}: {json.dumps(d['decision'])[:300]} | {verdicts or 'no verdicts'}")
    return "\n".join(lines) + "\n"


def sample(rows: list[dict]) -> dict[int, dict]:
    """The read sample by lookup number (part N numbers from (N-1)*1000+1): PER_CELL lookups per
    (model, role, phase), shuffled and dealt into PARTS."""
    by_cell: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        by_cell[(r["model"], r["role"], r["phase"])].append(r)
    rng = random.Random(SEED)
    picked = [r for cell in sorted(by_cell) for r in rng.sample(by_cell[cell], min(PER_CELL, len(by_cell[cell])))]
    rng.shuffle(picked)
    return {part * 1000 + 1 + i: r for part in range(PARTS) for i, r in enumerate(picked[part::PARTS])}


def main() -> None:
    rows = collect()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "lookups.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    picked = sample(rows)
    (OUT / "sample").mkdir(exist_ok=True)
    for part in range(PARTS):
        chunk = [(n, r) for n, r in picked.items() if (n - 1) // 1000 == part]
        (OUT / "sample" / f"part_{part + 1}.md").write_text("\n".join(_render(n, r) for n, r in chunk))
    print(f"{len(rows)} lookups ({sum(len(r['decisions']) for r in rows)} decisions); "
          f"sample {len(picked)} in {PARTS} parts -> {OUT}")


if __name__ == "__main__":
    main()
