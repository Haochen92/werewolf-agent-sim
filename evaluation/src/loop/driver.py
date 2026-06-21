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
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from evaluation.src.experiments.credit_backfill import compute_base_rates
from evaluation.src.loop.config import LoopConfig
from evaluation.src.loop.consolidate import consolidate
from evaluation.src.loop.credit import credit_apply, credit_distribution
from evaluation.src.loop.measure import generation_score
from evaluation.src.loop.merge import merge_new_obs

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


def _stamp_obs_generations(store: Path, gen: int, sidecar: Path) -> dict:
    """First-seen generation per obs record `key`, persisted in a run sidecar. The loop clock is
    GENERATION, not wall-clock: each re-extraction stamps a fresh created_at, so timestamps can't be the
    decay key — but the record key is stable across dedup merges (the survivor keeps its key), so a
    reinforced obs keeps its original age while its observation_count grows. New obs this gen get `gen`;
    existing keep their stamp. Returns the full key -> first-seen-gen map for observation decay."""
    gen_map = json.loads(sidecar.read_text()) if sidecar.exists() else {}
    obs = json.loads((store / "observations.json").read_text())
    for recs in obs.get("namespaces", {}).values():
        for r in recs:
            gen_map.setdefault(r.get("key"), gen)
    sidecar.write_text(json.dumps(gen_map, indent=2))
    return gen_map


def _run_one_game(out_jsonl: Path, prefix: str, cfg: LoopConfig, configs: str,
                  seed: Path | None = None, dump: Path | None = None, extra: tuple = ()) -> None:
    """One game via run_batch (--runs-per-config 1). Separate seed/dump dirs let parallel games share a
    read-only snapshot seed while each dumps to its own store (no shared-store write race)."""
    cmd = [
        "poetry", "run", "python", "scripts/run_batch.py",
        "--configs", configs, "--runs-per-config", "1",
        "--output", str(out_jsonl), "--session-prefix", prefix,
    ]
    if seed is not None:
        cmd += ["--seed-store-dir", str(seed)]
    if dump is not None:
        cmd += ["--dump-store-dir", str(dump)]
    cmd += list(extra)
    subprocess.run(cmd, cwd=REPO, env={**os.environ, **cfg.env()}, check=True)


def _run_games_parallel(run_dir: Path, out_jsonl: Path, prefix: str, cfg: LoopConfig, configs: str,
                        seed: Path | None = None, dump_each: bool = False, extra: tuple = ()) -> list:
    """Play games_per_generation games CONCURRENTLY (cap = game_concurrency), then concatenate the
    per-game batch records into out_jsonl. With dump_each, each game dumps to its own per-game store and
    the dirs are returned (for the freeze-old merge). Games are the wall-clock bottleneck; the only writer
    to the shared store is the post-merge, so this is race-free by construction."""
    stem = out_jsonl.stem

    def _one(k: int):
        out_k = run_dir / f"{stem}_g{k}.jsonl"
        dump_k = None
        if dump_each:
            dump_k = run_dir / f"{stem}_store_g{k}"
            dump_k.mkdir(parents=True, exist_ok=True)
        _run_one_game(out_k, f"{prefix}_g{k}", cfg, configs, seed=seed, dump=dump_k, extra=extra)
        return out_k, dump_k

    outs: list = []
    dumps: list = []
    with ThreadPoolExecutor(max_workers=max(1, cfg.game_concurrency)) as pool:
        for out_k, dump_k in pool.map(_one, range(cfg.games_per_generation)):
            outs.append(out_k)
            if dump_k is not None:
                dumps.append(dump_k)
    with open(out_jsonl, "w") as f:                       # concat per-game records into the gen record
        for o in outs:
            if o.exists():
                f.write(o.read_text())
            o.unlink(missing_ok=True)                     # the per-game record is now redundant
    return dumps


def run_loop(run_dir: str | Path, cfg: LoopConfig, *, base_store: str | None = "memory_stores/v6_1",
             configs: str = "all_enabled") -> list[dict]:
    run_dir = Path(run_dir)
    store = _init_store(run_dir, base_store)
    sp_path = store / "strategy_points.json"
    obs_sidecar = run_dir / "obs_generations.json"
    _stamp_obs_generations(store, 0, obs_sidecar)  # warm-start obs = generation 0 (oldest)
    prev_obs_counts: dict = {}
    history: list[dict] = []

    for gen in range(1, cfg.generations + 1):
        on_jsonl = run_dir / f"gen{gen}_on.jsonl"
        print(f"\n=== generation {gen}/{cfg.generations} — ON arm ({cfg.games_per_generation} games "
              f"x{cfg.game_concurrency} parallel, {cfg.model}) ===", flush=True)
        # Freeze the gen-start store as a read-only SNAPSHOT; every parallel game seeds from it and dumps
        # to its own per-game store (no shared-store write race). Then ONE freeze-old merge folds the new
        # obs in (cross-game dups collapse to observation_count; the snapshot is frozen).
        snapshot = run_dir / f"gen{gen}_snapshot"
        if snapshot.exists():
            shutil.rmtree(snapshot)
        shutil.copytree(store, snapshot)
        dump_dirs = _run_games_parallel(run_dir, on_jsonl, f"loop_{run_dir.name}_gen{gen}_on",
                                        cfg, configs, seed=snapshot, dump_each=True)
        mstats = merge_new_obs(store, snapshot, dump_dirs)
        print(f"  merge: {mstats}", flush=True)
        shutil.rmtree(snapshot, ignore_errors=True)      # cleanup snapshot + per-game temp stores
        for d in dump_dirs:
            shutil.rmtree(d, ignore_errors=True)

        if cfg.off_baseline:                 # memory-OFF flat baseline — NO seed/dump (never touches store)
            print(f"=== generation {gen} — OFF baseline (all_disabled, no seed/dump) ===", flush=True)
            _run_games_parallel(run_dir, run_dir / f"gen{gen}_off.jsonl",
                                f"loop_{run_dir.name}_gen{gen}_off", cfg, "all_disabled",
                                seed=None, dump_each=False, extra=("--no-memory-seed", "--no-memory-dump"))

        # credit runs over the ON arm window (rolling). The de-luck BASELINE comes from the clean,
        # same-epoch OFF arm (consolidation_design §3), NOT the incidental memory-off decisions inside the
        # ON games (thin + biased toward retrieval-skipped/early boards). The off arm is the comparison AND
        # calibrates the baseline. When off_baseline is disabled, credit_apply falls back to the ON glob.
        w = cfg.window_generations or gen
        gens = range(max(1, gen - w + 1), gen + 1)
        window = " ".join(str(run_dir / f"gen{g}_on.jsonl") for g in gens)
        cstats, cdist = {}, {}
        if cfg.credit:
            base_rates = None
            if cfg.off_baseline:
                off_window = " ".join(str(run_dir / f"gen{g}_off.jsonl") for g in gens)
                base_rates = compute_base_rates(off_window)
            cstats = credit_apply(sp_path, window, base_rates=base_rates,
                                  discussion=cfg.discussion_credit, discussion_mode=cfg.discussion_mode,
                                  tags_dir=str(run_dir / "tags"))  # persist tags per game_id (no re-tag)
            cdist = credit_distribution(sp_path, min_follow=cfg.prune_min_follow)  # did credit ENGAGE?
            print(f"  credit: {cstats}\n  credit_dist: {cdist}", flush=True)
        cons = {}
        if cfg.prune or cfg.evict or cfg.synthesize or cfg.evict_observations:
            obs_gen_map = _stamp_obs_generations(store, gen, obs_sidecar)  # new obs this gen -> `gen`
            cons = consolidate(store, cfg, prev_obs_counts, obs_gen_map=obs_gen_map, current_gen=gen)
            prev_obs_counts = cons.get("obs_counts", prev_obs_counts)
            print(f"  consolidate: prune_evict={cons.get('prune_evict')} "
                  f"obs_evict={cons.get('obs_evict')} synth={cons.get('synth')}", flush=True)
        score = generation_score(str(run_dir / f"gen{gen}_*.jsonl"))   # on + off arms
        print(f"  score: { {k: v for k, v in score.items() if not k.startswith('n_')} }", flush=True)
        history.append({"generation": gen, "score": score, "credit": cstats,
                        "credit_dist": cdist, "consolidate": cons})

    (run_dir / "loop_history.json").write_text(json.dumps(history, indent=2))
    print(f"\nloop history -> {run_dir / 'loop_history.json'}", flush=True)
    return history


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--base-store", default="memory_stores/v6_1", help="warm-start baseline ('' = cold)")
    ap.add_argument("--configs", default="all_enabled", help="run_batch config name (the arm)")
    ap.add_argument("--generations", type=int, default=10)
    ap.add_argument("--games-per-generation", type=int, default=5)
    ap.add_argument("--window-generations", type=int, default=6, help="credit de-luck lookback (gens)")
    ap.add_argument("--game-concurrency", type=int, default=5, help="parallel games within a generation")
    ap.add_argument("--model", default="gemini-3.1-flash-lite")
    ap.add_argument("--no-synth", action="store_true")
    args = ap.parse_args()
    cfg = LoopConfig(generations=args.generations, games_per_generation=args.games_per_generation,
                     window_generations=args.window_generations, game_concurrency=args.game_concurrency,
                     model=args.model, synthesize=not args.no_synth)
    run_loop(args.run_dir, cfg, base_store=args.base_store or None, configs=args.configs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
