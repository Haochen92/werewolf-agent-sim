"""The consolidation TICK — the batch ops entry that advances the live store one generation.

One tick = one learning step over a window of accumulated agent-only games (triggered by the ops
timer on N-games-or-max-age, never per-game): fold the window's new observations into the store,
recompute fixed-rule credit against the paired OFF base stream, run the
consolidation store-ops (decay / synth / dedup / prune), persist to Postgres, and export the
frozen ``demo_gen{k}`` snapshot the read path and the frontend changelog serve from.

Baseline coherence in production (load-bearing): the OFF window MUST be memory-off, agent-only
games graded by the same fixed rule — mode-1 traffic (+ the self-play trickle) is that stream. The
human-seat poisoning guard lives in ``credit_rules._iter_game_records``, so human-involved games
are inert here even if a glob accidentally includes them; per-game extraction dump dirs for
human games must still be excluded by the caller (extraction has no record-level guard). The
offline extraction job's output (``--extracted``) skips its human-seat games itself.

Ten-seat since 2026-10-13: the store bootstraps from ``ten_seat_v2`` and its snapshots go to their own
folder (the nine-seat ``demo_snapshots`` are left as they are).

    poetry run python -m Agents.memory.consolidation.tick \
        --on-dumps "batch_results/demo_on/games_*.jsonl" --off-dumps "batch_results/v8_seed_*/games/*.jsonl" \
        --extracted "batch_results/extraction_runs/demo_on_*/extracted.jsonl"
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path

import Agents.memory.consolidation.db as db
from Agents.memory.consolidation.config import TickConfig
from Agents.memory.consolidation.credit import credit_apply, credit_distribution
from Agents.memory.consolidation.credit_rules import compute_base_rates
from Agents.memory.consolidation.obs_fold import merge_new_obs
from Agents.memory.consolidation.store_ops import consolidate

DEFAULT_BOOTSTRAP_STORE = "memory_stores/ten_seat_v2"
DEFAULT_SNAPSHOT_ROOT = "memory_stores/ten_seat_snapshots"


def _stamp_obs_generations(scratch: Path, gen: int, first_seen: dict, reinforced: dict,
                           counts: dict) -> None:
    """Advance the decay clocks in place: a new key is first-seen (and reinforced) THIS gen; a
    RISE in observation_count for a tracked key = reinforced this gen (the fold's dedup bumps the
    survivor's count instead of adding a record)."""
    obs = json.loads((scratch / "observations.json").read_text())
    for recs in obs.get("namespaces", {}).values():
        for r in recs:
            key = r.get("key")
            count = r["value"].get("observation_count", 1)
            if not key:
                continue
            if key not in first_seen:
                first_seen[key] = reinforced[key] = gen
            elif count > counts.get(key, 0):
                reinforced[key] = gen
            counts[key] = count


def run_tick(on_dumps: str, off_dumps: str, game_store_dirs: list[str] | None = None,
             snapshot_root: str | Path = DEFAULT_SNAPSHOT_ROOT,
             bootstrap_store: str | Path = DEFAULT_BOOTSTRAP_STORE,
             cfg: TickConfig | None = None, dsn: str | None = None,
             extracted: list[str] | None = None) -> dict:
    """One generation. ``extracted`` = the offline extraction job's ``extracted.jsonl`` files for the
    window's games: written into a fresh store first, then folded like a game's own dump."""
    cfg = cfg or TickConfig()
    os.environ.update(cfg.env())  # pro-2.5 cost guard, before any lazy LLM import resolves a model
    with db.connect(dsn) as conn:
        db.setup(conn)
        if db.store_is_empty(conn):
            db.bootstrap_from_dir(conn, bootstrap_store)
        gen = db.next_gen(conn)
        scratch = Path(tempfile.mkdtemp(prefix=f"ww_tick_gen{gen}_"))
        try:
            db.materialize(conn, scratch)

            # 1. fold the window's new obs (key-diff vs the snapshot the games seeded from)
            prev_snapshot = db.last_snapshot_dir(conn) or str(bootstrap_store)
            fold = {}
            sources = list(game_store_dirs or [])
            if extracted:
                from Agents.memory.extraction.offline import write_extracted_store
                extracted_dir = scratch.parent / f"{scratch.name}_extracted"
                fold["extracted"] = write_extracted_store(list(extracted), extracted_dir)
                sources.append(str(extracted_dir))
            if sources:
                fold.update(merge_new_obs(scratch, prev_snapshot, sources,
                                          dedup=cfg.obs_fold_dedup, dedup_model=cfg.dedup_model))

            # 2. advance the obs decay clocks
            first_seen, reinforced, counts = db.load_obs_sidecar(conn)
            _stamp_obs_generations(scratch, gen, first_seen, reinforced, counts)

            # 3. fixed-rule credit against the OFF base stream
            sp_path = scratch / "strategy_points.json"
            cstats = cdist = {"skipped": "credit=False"}
            if cfg.credit:
                base_rates = compute_base_rates(off_dumps) if off_dumps else None
                cstats = credit_apply(sp_path, on_dumps, base_rates=base_rates, off_window=off_dumps)
                cdist = credit_distribution(sp_path, min_follow=cfg.prune_min_follow)

            # 4. consolidation store-ops (decay -> synth -> dedup -> prune)
            cons = consolidate(scratch, cfg, obs_gen_map=first_seen, current_gen=gen,
                               reinforced_map=reinforced)

            # 5. freeze the generation, then persist: the snapshot refuses an existing folder, so a
            # collision stops the tick before the database is written
            changes = (cons.get("prune_evict") or {}).pop("changes", [])
            (scratch / "changes.json").write_text(json.dumps(changes, indent=2))
            window_spec = {"on_dumps": on_dumps, "off_dumps": off_dumps,
                           "game_store_dirs": list(game_store_dirs or []), "extracted": list(extracted or [])}
            stats = {"gen": gen, "fold": fold, "credit": cstats, "credit_distribution": cdist,
                     "consolidate": cons}
            from Agents.run_fingerprint import runtime_fingerprint  # subprocess git call — keep lazy
            snapshot_dir = Path(snapshot_root) / f"demo_gen{gen}"
            db.export_snapshot(scratch, snapshot_dir, manifest={
                "gen": gen, "window": window_spec, "stats": stats,
                "runtime_fingerprint": runtime_fingerprint(),
                "credit_rule": "fixed (the ten-seat grading table, plan §9.6 item 10; hard-coded)",
            })
            db.save_obs_sidecar(conn, first_seen, reinforced, counts)
            db.ingest(conn, scratch)
            db.record_tick(conn, gen, stats, window_spec, str(snapshot_dir))
            stats["snapshot_dir"] = str(snapshot_dir)
            return stats
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
            shutil.rmtree(scratch.parent / f"{scratch.name}_extracted", ignore_errors=True)


def main() -> int:
    from dotenv import load_dotenv
    load_dotenv()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--on-dumps", default="",
                    help="glob(s) of the window's memory-ON game-record JSONLs")
    ap.add_argument("--off-dumps", default="",
                    help="glob(s) of the paired memory-OFF game-record JSONLs (the base stream)")
    ap.add_argument("--game-stores", default="",
                    help="glob of the window games' per-game extraction dump dirs (obs fold source)")
    ap.add_argument("--extracted", default="",
                    help="glob(s) of the offline extraction job's extracted.jsonl for the window's games "
                         "(obs fold source)")
    ap.add_argument("--model", default=None, help="synthesis model (default: TickConfig.model)")
    ap.add_argument("--batch", action="store_true",
                    help="a Claude synthesis model runs as one Message Batch (half price, slower)")
    ap.add_argument("--no-credit", action="store_true",
                    help="a fold-only generation: no memory-on window to grade, the counters "
                         "carry over untouched (the dumps are then optional)")
    ap.add_argument("--synth-every", type=int, default=None,
                    help="override TickConfig.synth_every_k_gens (1 = synthesize this gen)")
    ap.add_argument("--snapshot-root", default=DEFAULT_SNAPSHOT_ROOT)
    ap.add_argument("--bootstrap-store", default=DEFAULT_BOOTSTRAP_STORE)
    ap.add_argument("--dsn", default=None, help="Postgres DSN (default: WW_POSTGRES_DSN)")
    args = ap.parse_args()
    if not args.no_credit and not (args.on_dumps and args.off_dumps):
        ap.error("--on-dumps and --off-dumps are required unless --no-credit")
    cfg = TickConfig(credit=not args.no_credit)
    if args.synth_every is not None:
        cfg.synth_every_k_gens = args.synth_every
    if args.model:
        cfg.model = args.model
    cfg.batch = args.batch
    import glob as _glob
    game_dirs = sorted(d for d in _glob.glob(args.game_stores) if Path(d).is_dir()) \
        if args.game_stores else []
    extracted = sorted(f for pat in args.extracted.split() for f in _glob.glob(pat))
    stats = run_tick(args.on_dumps, args.off_dumps, game_dirs,
                     snapshot_root=args.snapshot_root, bootstrap_store=args.bootstrap_store,
                     cfg=cfg, dsn=args.dsn, extracted=extracted)
    print(json.dumps(stats, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
