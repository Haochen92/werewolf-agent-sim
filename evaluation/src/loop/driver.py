"""Compounding loop — the generational DRIVER. Wires c (extract, via run_batch) + a (credit) + b
(consolidate) into the on-policy loop, all toggleable via LoopConfig.

Per generation:
  1. run_batch seeded from + dumping to the run store (c: play N games, extract obs/SPs back to the store)
  2. credit_apply over the rolling window of batch records      (a)
  3. consolidate: prune/evict + credit-aware synthesis          (b)
  4. generation_score on this generation's records              (the slope proxy)

The store is run-specific (copied from a base or cold-empty) — canonical stores stay frozen. run_batch is
a subprocess so the model env-pin (cfg.env()) and seed=dump=store wiring are clean.

  poetry run python -m evaluation.src.loop.driver --run-dir <dir> --base-store memory_stores/v6_1 \
      --generations 1 --games-per-generation 5            # one-rotation gate
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from evaluation.src.loop.config import LoopConfig
from evaluation.src.loop.consolidate import consolidate
from evaluation.src.loop.credit import credit_apply
from evaluation.src.loop.measure import generation_score

REPO = Path(__file__).resolve().parents[3]


def _init_store(run_dir: Path, base_store: str | None) -> Path:
    store = run_dir / "store"
    store.mkdir(parents=True, exist_ok=True)
    if base_store:  # warm start: copy the baseline (canonical stays frozen)
        for f in ("observations.json", "strategy_points.json", "indexed_cache.pkl"):
            src = Path(base_store) / f
            if src.exists():
                shutil.copy2(src, store / f)
    else:  # cold start: empty store
        for f in ("observations.json", "strategy_points.json"):
            (store / f).write_text(json.dumps({"namespaces": {}, "schema_version": "loop.v1"}))
    return store


def _run_batch(store: Path, out_jsonl: Path, prefix: str, cfg: LoopConfig, configs: str) -> None:
    cmd = [
        "poetry", "run", "python", "scripts/run_batch.py",
        "--configs", configs,
        "--runs-per-config", str(cfg.games_per_generation),
        "--memory-store-dir", str(store),
        "--output", str(out_jsonl),
        "--session-prefix", prefix,
    ]
    env = {**os.environ, **cfg.env()}
    subprocess.run(cmd, cwd=REPO, env=env, check=True)


def run_loop(run_dir: str | Path, cfg: LoopConfig, *, base_store: str | None = "memory_stores/v6_1",
             configs: str = "all_enabled") -> list[dict]:
    run_dir = Path(run_dir)
    store = _init_store(run_dir, base_store)
    sp_path = store / "strategy_points.json"
    prev_obs_counts: dict = {}
    history: list[dict] = []

    for gen in range(1, cfg.generations + 1):
        out_jsonl = run_dir / f"gen{gen}.jsonl"
        print(f"\n=== generation {gen}/{cfg.generations} — run_batch ({cfg.games_per_generation} games, "
              f"{cfg.model}) ===", flush=True)
        _run_batch(store, out_jsonl, f"loop_{run_dir.name}_gen{gen}", cfg, configs)

        # rolling window of recent generations' records for credit
        w = cfg.window_generations or gen
        window = " ".join(str(run_dir / f"gen{g}.jsonl") for g in range(max(1, gen - w + 1), gen + 1))

        if cfg.credit:
            cstats = credit_apply(sp_path, window, discussion=cfg.discussion_credit)
            print(f"  credit: {cstats}", flush=True)
        cons = {}
        if cfg.prune or cfg.evict or cfg.synthesize:
            cons = consolidate(store, cfg, prev_obs_counts)
            prev_obs_counts = cons.get("obs_counts", prev_obs_counts)
            print(f"  consolidate: prune_evict={cons.get('prune_evict')} synth={cons.get('synth')}",
                  flush=True)
        score = generation_score(str(out_jsonl))
        print(f"  score: { {k: v for k, v in score.items() if not k.startswith('n_')} }", flush=True)
        history.append({"generation": gen, "score": score, "consolidate": cons})

    (run_dir / "loop_history.json").write_text(json.dumps(history, indent=2))
    print(f"\nloop history -> {run_dir / 'loop_history.json'}", flush=True)
    return history


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--base-store", default="memory_stores/v6_1", help="warm-start baseline ('' = cold)")
    ap.add_argument("--configs", default="all_enabled", help="run_batch config name (the arm)")
    ap.add_argument("--generations", type=int, default=1)
    ap.add_argument("--games-per-generation", type=int, default=5)
    ap.add_argument("--model", default="gemini-3.1-flash-lite")
    ap.add_argument("--no-synth", action="store_true")
    args = ap.parse_args()
    cfg = LoopConfig(generations=args.generations, games_per_generation=args.games_per_generation,
                     model=args.model, synthesize=not args.no_synth)
    run_loop(args.run_dir, cfg, base_store=args.base_store or None, configs=args.configs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
