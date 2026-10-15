"""Publish a v8 store: the working store's points marked by the reads, the published copy without them.

The reads' rule flags (a point stating a rule the game does not have) and duplicate groups (the same
move in the same situation; one point kept) are written onto the points of the working store, so
nothing is lost and a flag can be reviewed, then the store is copied to ``--out`` without the flagged
and duplicate points (as ten_seat_v1 was published, 2026-10-12). The copy has no vector cache: a
server embeds its points on first load.

  poetry run python scripts/publish_v8_store.py --working memory_stores/v8_reextract_synth \\
      --reads evidence/memory_system/v8/data/reextract/points --out memory_stores/ten_seat_v2 \\
      --description "..."
"""

from __future__ import annotations

import argparse
import glob
import json
import shutil
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--working", type=Path, required=True)
    parser.add_argument("--reads", type=Path, required=True, help="folder of rules_part_*.jsonl and dups_part_*.jsonl")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--description", required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit(f"{args.out} exists")

    rules = {r["key"]: r for f in sorted(glob.glob(str(args.reads / "rules_part_*.jsonl")))
             for r in map(json.loads, Path(f).read_text().splitlines())}
    duplicate_of = {k: g for f in sorted(glob.glob(str(args.reads / "dups_part_*.jsonl")))
                    for g in map(json.loads, Path(f).read_text().splitlines()) for k in g["keys"] if k != g["keep"]}
    source = f"{args.reads.relative_to(Path.cwd()) if args.reads.is_absolute() else args.reads}"

    sp_path = args.working / "strategy_points.json"
    store = json.loads(sp_path.read_text())
    for items in store["namespaces"].values():
        for it in items:
            value = it["value"]
            if it["key"] in rules:
                r = rules[it["key"]]
                value["rule_flag"] = {"screen": source, "confidence": r["confidence"], "claim": r["claim"], "rule": r["rule"]}
            if it["key"] in duplicate_of:
                g = duplicate_of[it["key"]]
                value["duplicate_of"] = {"screen": source, "keep": g["keep"], "why": g["why"]}
    sp_path.write_text(json.dumps(store, indent=2))

    args.out.mkdir(parents=True)
    shutil.copy(args.working / "observations.json", args.out / "observations.json")
    if (args.working / "synthesis_log.jsonl").exists():
        shutil.copy(args.working / "synthesis_log.jsonl", args.out / "synthesis_log.jsonl")
    published = {**store, "description": args.description, "namespaces": {
        ns: [it for it in items if "rule_flag" not in it["value"] and "duplicate_of" not in it["value"]]
        for ns, items in store["namespaces"].items()}}
    (args.out / "strategy_points.json").write_text(json.dumps(published, indent=2))
    before = sum(len(v) for v in store["namespaces"].values())
    after = sum(len(v) for v in published["namespaces"].values())
    smallest = min((len(v), ns.split("/", 1)[1]) for ns, v in published["namespaces"].items())
    print(f"{before} points, {len(rules)} rule-flagged, {len(duplicate_of)} duplicates -> {after} published "
          f"in {len(published['namespaces'])} cells (smallest: {smallest[1]}, {smallest[0]}) -> {args.out}")


if __name__ == "__main__":
    main()
