"""The consolidation steps that advance the live store, in two parts (decisions §14).

- **The credit pass** (``run_credit_pass``; deterministic, no model call): recompute every lesson's
  labels from the memory-on games in the window (batch-run files and served games, ``sources``), then
  prune and evict automatically at the configured thresholds. It needs nothing from extraction or
  synthesis, so it can run after every memory-on game. Each pass is recorded in ``credit_runs`` with
  every change it made.
- **The learning tick** (``run_tick``; paid, every N games): fold the window's new observations (the
  offline extraction job's output), advance the decay clocks, synthesize (reading the lessons' labels
  as the last credit pass left them) and run the point dedup, persist to Postgres, and export the
  frozen ``demo_gen{k}`` snapshot. It never prunes or evicts; that is the credit pass's.

Baseline coherence in production (load-bearing): the OFF window MUST be memory-off, agent-only
games graded by the same fixed rule — mode-1 traffic (+ the self-play trickle) is that stream. The
human-seat poisoning guard lives in ``credit_rules._iter_game_records``, so human-involved games
are inert here even if a glob accidentally includes them; per-game extraction dump dirs for
human games must still be excluded by the caller (extraction has no record-level guard). The
offline extraction job's output (``--extracted``) skips its human-seat games itself.

Ten-seat since 2026-10-13: the store bootstraps from ``ten_seat_v2`` and its snapshots go to their own
folder (the nine-seat ``demo_snapshots`` are left as they are).

    poetry run python -m Agents.memory.consolidation.tick credit \
        --files "batch_results/demo_on/games_*.jsonl" --db --off "batch_results/v8_seed_*/games/*.jsonl"
    poetry run python -m Agents.memory.consolidation.tick learn \
        --extracted "batch_results/extraction_runs/demo_on_*/extracted.jsonl" --model claude-sonnet-5-5 --batch
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from dataclasses import replace
from pathlib import Path

import Agents.memory.consolidation.db as db
from Agents.memory.consolidation.config import TickConfig
from Agents.memory.consolidation.credit import credit_apply, credit_distribution
from Agents.memory.consolidation.credit_rules import compute_base_rates
from Agents.memory.consolidation.obs_fold import merge_new_obs
from Agents.memory.consolidation.store_ops import consolidate, prune_and_evict

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


def _bootstrapped(conn, bootstrap_store: str | Path) -> None:
    db.setup(conn)
    if db.store_is_empty(conn):
        db.bootstrap_from_dir(conn, bootstrap_store)


def run_credit_pass(window, off_window: str, cfg: TickConfig | None = None, dsn: str | None = None,
                    bootstrap_store: str | Path = DEFAULT_BOOTSTRAP_STORE) -> dict:
    """Credit every stored lesson from the window's memory-on games, then prune and evict (decisions
    §14). ``window``: games already loaded (``sources.games_from_files`` / ``games_from_db``) or a glob
    spec of batch-run dumps; ``off_window``: the memory-off games' dumps the baselines come from. Returns
    the counts and every change, which are also recorded in ``credit_runs``."""
    from Agents.memory.consolidation.credit_rules import _iter_game_records

    cfg = cfg or TickConfig()
    games = list(_iter_game_records(window))
    with db.connect(dsn) as conn:
        _bootstrapped(conn, bootstrap_store)
        scratch = Path(tempfile.mkdtemp(prefix="ww_credit_"))
        try:
            db.materialize(conn, scratch)
            sp_path = scratch / "strategy_points.json"
            cstats = credit_apply(sp_path, games, base_rates=compute_base_rates(off_window), off_window=off_window)
            cdist = credit_distribution(sp_path, min_follow=cfg.prune_min_follow)
            store = json.loads(sp_path.read_text())
            rates = json.loads((scratch / "base_rates.json").read_text())
            pe = prune_and_evict(store.setdefault("namespaces", {}), rates, cfg) if (cfg.prune or cfg.evict) else {}
            sp_path.write_text(json.dumps(store, indent=2))
            changes = pe.pop("changes", [])
            db.ingest(conn, scratch)
            stats = {"games": len(games), "credit": cstats, "credit_distribution": cdist, "prune_evict": pe}
            db.record_credit_run(conn, stats, changes, [g.get("game_id") for g in games])
            return {**stats, "changes": changes}
        finally:
            shutil.rmtree(scratch, ignore_errors=True)


def run_tick(game_store_dirs: list[str] | None = None,
             snapshot_root: str | Path = DEFAULT_SNAPSHOT_ROOT,
             bootstrap_store: str | Path = DEFAULT_BOOTSTRAP_STORE,
             cfg: TickConfig | None = None, dsn: str | None = None,
             extracted: list[str] | None = None) -> dict:
    """One learning generation. ``extracted`` = the offline extraction job's ``extracted.jsonl`` files
    for the window's games: written into a fresh store first, then folded like a game's own dump.
    Prune and evict are the credit pass's, never the tick's."""
    cfg = replace(cfg or TickConfig(), prune=False, evict=False)
    os.environ.update(cfg.env())  # pro-2.5 cost guard, before any lazy LLM import resolves a model
    with db.connect(dsn) as conn:
        _bootstrapped(conn, bootstrap_store)
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

            # 3. consolidation store-ops (decay -> synth -> dedup), on the labels the last credit pass left
            cons = consolidate(scratch, cfg, obs_gen_map=first_seen, current_gen=gen,
                               reinforced_map=reinforced)

            # 4. freeze the generation, then persist: the snapshot refuses an existing folder, so a
            # collision stops the tick before the database is written
            window_spec = {"game_store_dirs": list(game_store_dirs or []), "extracted": list(extracted or [])}
            stats = {"gen": gen, "fold": fold, "consolidate": cons}
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
    import glob as _glob

    from dotenv import load_dotenv
    load_dotenv()
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="step", required=True)
    credit = sub.add_parser("credit", help="credit every lesson, then prune and evict (no model call)")
    credit.add_argument("--files", default="", help="glob(s) of batch-run memory-ON game-record JSONLs")
    credit.add_argument("--db", action="store_true", help="also the server's memory-on AI-only games")
    credit.add_argument("--off", required=True, help="glob(s) of the memory-OFF game records (the baselines)")
    learn = sub.add_parser("learn", help="fold new observations and synthesize (paid)")
    learn.add_argument("--game-stores", default="",
                       help="glob of the window games' per-game extraction dump dirs (obs fold source)")
    learn.add_argument("--extracted", default="",
                       help="glob(s) of the offline extraction job's extracted.jsonl for the window's games")
    learn.add_argument("--model", default=None, help="synthesis model (default: TickConfig.model)")
    learn.add_argument("--batch", action="store_true",
                       help="a Claude synthesis model runs as one Message Batch (half price, slower)")
    learn.add_argument("--synth-every", type=int, default=None,
                       help="override TickConfig.synth_every_k_gens (1 = synthesize this gen)")
    learn.add_argument("--snapshot-root", default=DEFAULT_SNAPSHOT_ROOT)
    for p in (credit, learn):
        p.add_argument("--bootstrap-store", default=DEFAULT_BOOTSTRAP_STORE)
        p.add_argument("--dsn", default=None, help="Postgres DSN (default: WW_POSTGRES_DSN)")
    args = ap.parse_args()
    cfg = TickConfig()
    if args.step == "credit":
        from Agents.memory.consolidation.sources import games_from_db, games_from_files

        games = games_from_files(args.files) if args.files else []
        if args.db:
            games += games_from_db(args.dsn)
        stats = run_credit_pass(games, args.off, cfg=cfg, dsn=args.dsn, bootstrap_store=args.bootstrap_store)
    else:
        if args.synth_every is not None:
            cfg.synth_every_k_gens = args.synth_every
        if args.model:
            cfg.model = args.model
        cfg.batch = args.batch
        game_dirs = sorted(d for d in _glob.glob(args.game_stores) if Path(d).is_dir()) \
            if args.game_stores else []
        extracted = sorted(f for pat in args.extracted.split() for f in _glob.glob(pat))
        stats = run_tick(game_dirs, snapshot_root=args.snapshot_root, bootstrap_store=args.bootstrap_store,
                         cfg=cfg, dsn=args.dsn, extracted=extracted)
    print(json.dumps(stats, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
