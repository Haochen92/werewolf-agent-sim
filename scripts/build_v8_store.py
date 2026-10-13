"""Build a v8 store from the offline extraction job's output (decisions §11), then synthesize its lessons.

Live games no longer write the store: the job's ``extracted.jsonl`` files hold each game's observations
(de-haloed). This writes them into a fresh store the way the post-game node did (each game's
observations deduplicated against the store as they go in, then dumped), and with ``--synthesize``
runs ``consolidate()`` on a copy as the ten_seat_v1 synthesis did (credit, prune and eviction off; a
Claude model as one Message Batch). A game with a human seat never teaches the store.

  poetry run python scripts/build_v8_store.py --extracted batch_results/extraction_runs/*/extracted.jsonl \\
      --out memory_stores/v8_reextract --synthesize --synth-out memory_stores/v8_reextract_synth

The grade variant (decisions §13) starts from the same observations, copied rather than rebuilt, with
each observation's decision tag and grade written on, and synthesizes from the grades:

  poetry run python scripts/build_v8_store.py --from-store memory_stores/v8_reextract \\
      --annotate batch_results/extraction_runs/flash_seed_gate_2026-10-12 batch_results/extraction_runs/sonnet_rest_2026-10-12 \\
      --out memory_stores/v8_reextract_graded --synthesize --synth-outcome grade --synth-out memory_stores/v8_grade_synth
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path


def build(paths: list[str], out: Path) -> dict:
    from Agents.memory.extraction.offline import write_extracted_store

    return write_extracted_store(paths, out)


def annotate_decisions(store_dir: Path, runs: list[str]) -> dict:
    """Write each stored observation's decision tag and grade (decision_day, pack_turn, decision_grade)
    from the runs' decisions.jsonl and grades.jsonl (scripts/tag_observation_decisions.py,
    scripts/grade_observations.py), matched by game, role, phase and approach. Returns match counts."""
    by_obs = {}
    for run in runs:
        cases = [json.loads(line)["output"]["extraction_case"] for line in open(Path(run) / "extracted.jsonl")]
        tags = {(t["game_id"], t["index"]): t for t in map(json.loads, open(Path(run) / "decisions.jsonl"))}
        grades = {(g["game_id"], g["index"]): g for g in map(json.loads, open(Path(run) / "grades.jsonl"))}
        for case in cases:
            for i, o in enumerate(case["observations"], 1):
                t, g = tags.get((case["game_id"], i)), grades.get((case["game_id"], i))
                if t:
                    by_obs[(case["game_id"], o["perspective"], o["action_phase"], o.get("approach", ""))] = {
                        "decision_day": t["decision_day"], "pack_turn": t["pack_turn"],
                        "decision_grade": g["decision_grade"] if g else None}
    path = store_dir / "observations.json"
    store = json.loads(path.read_text())
    matched = total = 0
    for recs in store["namespaces"].values():
        for r in recs:
            v = r["value"]
            dims = v.get("dimensions") or {}
            fields = by_obs.get((v.get("game_id"), dims.get("perspective"), dims.get("action_phase"), v.get("approach", "")))
            total += 1
            if fields:
                v.update(fields)
                matched += 1
    path.write_text(json.dumps(store, indent=2))
    return {"observations": total, "annotated": matched}


def synthesize(store_dir: Path, synth_dir: Path, model: str, outcome: str = "verdict") -> dict:
    from Agents.memory.consolidation.config import TickConfig
    from Agents.memory.consolidation.store_ops import consolidate

    if synth_dir.exists():
        raise SystemExit(f"{synth_dir} exists; synthesis writes a fresh copy")
    shutil.copytree(store_dir, synth_dir, ignore=shutil.ignore_patterns("indexed_cache.pkl"))
    cfg = TickConfig(model=model, batch=model.startswith("claude"), credit=False, prune=False, evict=False,
                     evict_observations=False, synth_outcome=outcome)
    result = consolidate(synth_dir, cfg)
    return {k: v for k, v in result.items() if k != "obs_counts"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--extracted", nargs="+", help="the job's extracted.jsonl files to build from")
    parser.add_argument("--from-store", type=Path, help="copy this built store instead of building one")
    parser.add_argument("--annotate", nargs="+", default=[],
                        help="extraction run folders whose decisions.jsonl and grades.jsonl to write on")
    parser.add_argument("--synth-outcome", choices=("verdict", "grade"), default="verdict")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--synthesize", action="store_true")
    parser.add_argument("--synth-out", type=Path)
    parser.add_argument("--model", default="claude-sonnet-5-5")
    args = parser.parse_args()
    if not (args.extracted or args.from_store):
        parser.error("--extracted or --from-store")
    started = time.time()
    if args.from_store:
        if args.out.exists():
            raise SystemExit(f"{args.out} exists; the copy goes to a fresh folder")
        shutil.copytree(args.from_store, args.out, ignore=shutil.ignore_patterns("indexed_cache.pkl", "build_summary.json"))
        summary = {"copied_from": str(args.from_store)}
    else:
        summary = {"build": build(args.extracted, args.out)}
    if args.annotate:
        summary["annotated"] = annotate_decisions(args.out, args.annotate)
    if args.synthesize:
        from Agents.llm_factory.providers import anthropic as claude_structured

        summary["synthesis"] = synthesize(args.out, args.synth_out or args.out.with_name(args.out.name + "_synth"),
                                          args.model, args.synth_outcome)
        summary["synthesis_cost_usd"] = claude_structured.usage_cost_usd()
    summary["minutes"] = round((time.time() - started) / 60, 1)
    (args.out / "build_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str)[:3000])


if __name__ == "__main__":
    main()
