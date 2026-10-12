"""The v8 gate's stage-filter replay: the 96 read lookups searched again, with lessons from another
stage of the game left out.

Record: evidence/memory_system/v8/experiment_log.md (the gate). The relevance read found one lesson in
seven fit, mostly because the search matched the role and not the stage. Each lesson stores the board
it was learned on, and the seat's own board is exact, so a lesson is left out when the two differ on:

- the alive bucket (early 8+, mid 5-7, late 4 or fewer);
- whether the pack has lost a partner (``ally_revealed``), where both carry it;
- whether the limited ability has any use left (``uses_left`` or ``bullets_left``, some vs none)
(``dimension_gating.stage_mismatch``, the live filter's own test).

Every lesson in the seat's cell is scored against the situation the seat wrote at the time (one
embedding call per lookup; the store's vectors come from its cache), then the top three are kept as
live retrieval keeps them (``RETRIEVAL_KEEP_PER_SITUATION``). The unfiltered top three reproduce what
the seat was shown, a check on the replay. Writes ``data/gate/stage_filter/``: ``replay.jsonl`` (per
lookup: both lesson sets, the read's verdict where the lesson was read) and ``to_read.md`` (the kept
lessons the read has not judged, for a reader with the same rubric).

  poetry run python evaluation/experiments/v8_stage_filter_replay.py
"""

from __future__ import annotations

import json
from collections import Counter

from Agents.memory.persistence.seed import seed_memory_from_config
from Agents.memory.retrieval.accessors import RETRIEVAL_KEEP_PER_SITUATION
from Agents.memory.retrieval.dimension_gating import stage_mismatch
from Agents.memory.store import store
from evaluation.experiments.v8_gate_lookups import OUT as GATE, PARTS, sample

STORE_DIR = "memory_stores/ten_seat_v1"
OUT = GATE / "stage_filter"


def _verdicts() -> dict[tuple[int, str], dict]:
    """The read's verdict on each lesson, by (lookup number, lesson key)."""
    read = {}
    for part in range(1, PARTS + 1):
        for line in (GATE / "read" / f"part_{part}.jsonl").read_text().splitlines():
            row = json.loads(line)
            read[row["lookup"]] = {les["n"]: les for les in row["lessons"]}
    return read


def main() -> None:
    rows = [json.loads(line) for line in (GATE / "lookups.jsonl").read_text().splitlines()]
    picked = sample(rows)
    target = store
    seed_memory_from_config({"seed_enabled": True, "seed_store_dir": STORE_DIR}, target_store=target)
    read = _verdicts()
    verdict_by_key: dict[tuple[int, str], dict] = {}
    for n, r in picked.items():
        for i, les in enumerate(r["lessons"], 1):
            verdict_by_key[(n, les["key"])] = read[n][i]

    out_rows, tally, to_read = [], Counter(), []
    for n, r in sorted(picked.items()):
        query = r["query_dims"]
        cell = target.search(("strategy_points", r["role"], r["phase"]), query=r["situations"][0], limit=50)
        scored = sorted(cell, key=lambda it: it.score or 0.0, reverse=True)
        before = [it.key for it in scored[:RETRIEVAL_KEEP_PER_SITUATION]]
        tally["reproduced" if before == [les["key"] for les in r["lessons"]] else "not reproduced"] += 1
        kept = [it for it in scored if not stage_mismatch(query, it.value.get("dimensions") or {})]
        after = kept[:RETRIEVAL_KEEP_PER_SITUATION]
        lessons = []
        for it in scored:
            v = verdict_by_key.get((n, it.key))
            entry = {"key": it.key, "score": round(it.score or 0.0, 3), "shown": it.key in before,
                     "kept": it in after, "mismatch": stage_mismatch(query, it.value.get("dimensions") or {}),
                     "fit": v["fit"] if v else None, "why": v["why"] if v else None,
                     "situation": it.value["situation"], "action": it.value["action"]}
            lessons.append(entry)
            if entry["kept"] and v is None:
                to_read.append((n, r, entry))
        out_rows.append({"lookup": n, "model": r["model"], "role": r["role"], "phase": r["phase"],
                         "day": r["day"], "query_dims": query, "cell_size": len(scored), "lessons": lessons})

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "replay.jsonl").write_text("".join(json.dumps(r) + "\n" for r in out_rows))
    (OUT / "to_read.md").write_text(_render_to_read(to_read))
    print(dict(tally), f"{len(to_read)} kept lessons unread -> {OUT}")


def _render_to_read(items: list[tuple[int, dict, dict]]) -> str:
    """The unread kept lessons, grouped by lookup, in the read's format (situation, true roles)."""
    blocks, last = [], None
    for n, r, les in items:
        if n != last:
            roles = ", ".join(f"{p} {role}" for p, role in sorted(r["true_roles"].items(),
                                                                  key=lambda x: int(x[0].split("_")[1])))
            blocks.append(f"\n## Lookup {n}: {r['model']} game {r['game_id']}, {r['player_id']} the {r['role']}, "
                          f"{r['phase']}, day {r['day']}\nTrue roles (the reader's ground truth, not known to "
                          f"the seat): {roles}\n\n**Situation the seat wrote:** {r['situations'][0]}\n\n"
                          f"**Lessons to judge:**")
            last = n
        blocks.append(f"- key {les['key']} (score {les['score']}) *When:* {les['situation']}\n"
                      f"  *Do:* {les['action']}")
    return "\n".join(blocks).lstrip() + "\n"


if __name__ == "__main__":
    main()
