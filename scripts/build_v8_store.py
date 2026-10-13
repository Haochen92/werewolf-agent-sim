"""Build a v8 store from the offline extraction job's output (decisions §11), then synthesize its lessons.

Live games no longer write the store: the job's ``extracted.jsonl`` files hold each game's observations
(de-haloed). This writes them into a fresh store the way the post-game node did (each game's
observations deduplicated against the store as they go in, then dumped), and with ``--synthesize``
runs ``consolidate()`` on a copy as the ten_seat_v1 synthesis did (credit, prune and eviction off; a
Claude model as one Message Batch). A game with a human seat never teaches the store.

  poetry run python scripts/build_v8_store.py --extracted batch_results/extraction_runs/*/extracted.jsonl \\
      --out memory_stores/v8_reextract --synthesize --synth-out memory_stores/v8_reextract_synth
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


def synthesize(store_dir: Path, synth_dir: Path, model: str) -> dict:
    from Agents.memory.consolidation.config import TickConfig
    from Agents.memory.consolidation.store_ops import consolidate

    if synth_dir.exists():
        raise SystemExit(f"{synth_dir} exists; synthesis writes a fresh copy")
    shutil.copytree(store_dir, synth_dir, ignore=shutil.ignore_patterns("indexed_cache.pkl"))
    cfg = TickConfig(model=model, batch=model.startswith("claude"), credit=False, prune=False, evict=False,
                     evict_observations=False)
    result = consolidate(synth_dir, cfg)
    return {k: v for k, v in result.items() if k != "obs_counts"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--extracted", nargs="+", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--synthesize", action="store_true")
    parser.add_argument("--synth-out", type=Path)
    parser.add_argument("--model", default="claude-sonnet-5-5")
    args = parser.parse_args()
    started = time.time()
    summary = {"build": build(args.extracted, args.out)}
    if args.synthesize:
        from Agents.llm_factory.providers import anthropic as claude_structured

        summary["synthesis"] = synthesize(args.out, args.synth_out or args.out.with_name(args.out.name + "_synth"),
                                          args.model)
        summary["synthesis_cost_usd"] = claude_structured.usage_cost_usd()
    summary["minutes"] = round((time.time() - started) / 60, 1)
    (args.out / "build_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps(summary, indent=2, default=str)[:3000])


if __name__ == "__main__":
    main()
