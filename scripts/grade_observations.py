"""Grade every tagged observation's decision deterministically (decisions §13; plan §9.6 item 11).

Reads the tags (``decisions.jsonl`` beside each ``extracted.jsonl``, from
scripts/tag_observation_decisions.py) and each game's record: the batch runner's record where the game
was played in a batch, else rebuilt from the server's event log (read only). Writes ``grades.jsonl``
beside the tags: one row per observation with its decision's grade (positive / neutral / negative, or
null when it names no single decision or the decision is unscored), and prints the grade mix by phase.

  poetry run python scripts/grade_observations.py --runs batch_results/extraction_runs/flash_seed_gate_2026-10-12 \\
      batch_results/extraction_runs/sonnet_rest_2026-10-12
"""

from __future__ import annotations

import argparse
import collections
import glob
import json
from pathlib import Path

BATCH_RECORDS = "batch_results/**/*.jsonl"


def batch_records(game_ids: set[str]) -> dict[str, dict]:
    """The batch runner's record of each game it played, by id."""
    found = {}
    for path in glob.glob(BATCH_RECORDS, recursive=True):
        if "eval_cases" in path or "extraction" in path:
            continue
        try:
            for line in open(path):
                g = json.loads(line)
                if isinstance(g, dict) and g.get("game_id") in game_ids and g.get("night_resolutions"):
                    found.setdefault(g["game_id"], g)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
    return found


def server_records(game_ids: set[str]) -> dict[str, dict]:
    """Records rebuilt from the server's event log, read only."""
    import psycopg
    from dotenv import dotenv_values
    from psycopg.rows import dict_row

    from Agents.memory.consolidation.sources import record_from_event_log

    out = {}
    with psycopg.connect(dotenv_values(".env")["WW_POSTGRES_DSN"], autocommit=True, row_factory=dict_row,
                         options="-c default_transaction_read_only=on") as conn:
        for gid in sorted(game_ids):
            events = [r["payload"] for r in conn.execute(
                "select payload from events where game_id = %s order by seq", (gid,)).fetchall()]
            if events:
                out[gid] = record_from_event_log(gid, events)
    return out


def main() -> None:
    from Agents.memory.consolidation.grading import GameView

    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--runs", nargs="+", required=True, help="extraction run folders holding decisions.jsonl")
    args = ap.parse_args()
    tags = {run: [json.loads(line) for line in open(Path(run) / "decisions.jsonl")] for run in args.runs}
    ids = {r["game_id"] for rows in tags.values() for r in rows}
    records = batch_records(ids)
    source = {gid: "batch" for gid in records}
    rebuilt = server_records(ids - set(records))
    records.update(rebuilt)
    source.update({gid: "server" for gid in rebuilt})
    views = {gid: GameView(g) for gid, g in records.items()}
    mix: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for run, rows in tags.items():
        out = []
        for r in rows:
            view = views.get(r["game_id"])
            grade = view.observation_grade(r["perspective"], r["action_phase"], r["decision_day"],
                                           r["pack_turn"] or "none") if view and r["decision_day"] is not None else None
            out.append({"game_id": r["game_id"], "index": r["index"], "decision_grade": grade,
                        "record": source.get(r["game_id"])})
            mix[r["action_phase"]][grade or "not graded"] += 1
        (Path(run) / "grades.jsonl").write_text("".join(json.dumps(x) + "\n" for x in out))
    print(json.dumps({"games": len(records), "batch": sum(s == "batch" for s in source.values()),
                      "server": len(rebuilt), "missing": sorted(ids - set(records)),
                      "mix": {k: dict(v) for k, v in mix.items()}}, indent=2))


if __name__ == "__main__":
    main()
