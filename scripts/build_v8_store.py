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

from langgraph.store.memory import InMemoryStore

from Agents.memory.store import store as indexed_store
from Agents.schemas.memory import cell_observation_schema_for


def _games(paths: list[str]) -> list[tuple[str, list]]:
    """(game id, observations as cell models) per extracted game, human-seat games left out."""
    games = []
    for path in paths:
        for line in Path(path).read_text().splitlines():
            case = json.loads(line)["output"]["extraction_case"]
            if case.get("human_players"):
                continue
            observations = [cell_observation_schema_for(o["perspective"], o["action_phase"]).model_validate(o)
                            for o in case["observations"]]
            games.append((case["game_id"], observations))
    return games


def build(paths: list[str], out: Path) -> dict:
    from Agents.memory.deduplication import run_downstream_observation_dedup
    from Agents.memory.persistence.config import memory_store_paths
    from Agents.memory.persistence.dump import dump_memory_to_json_files

    target = InMemoryStore(index=indexed_store.index_config)
    stats = {"games": 0, "observations": 0, "kept": 0, "discarded": 0, "failed": 0}
    for i, (game_id, observations) in enumerate(_games(paths), 1):
        s = run_downstream_observation_dedup(target, observations, game_id)
        stats["games"] += 1
        stats["observations"] += len(observations)
        for k in ("kept", "discarded", "failed"):
            stats[k] += getattr(s, k)
        print(f"{i:3} {game_id[:8]}: {len(observations)} observations, kept {s.kept}, discarded {s.discarded}")
    out.mkdir(parents=True, exist_ok=True)
    obs_path, sp_path = memory_store_paths(out)
    dump_memory_to_json_files(obs_path, sp_path, target_store=target)
    return stats


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
