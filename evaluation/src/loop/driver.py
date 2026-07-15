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
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from evaluation.src.data import batch_layout
from evaluation.src.loop.credit_backfill import compute_base_rates
from evaluation.src.loop.config import LoopConfig
from evaluation.src.loop.consolidate import consolidate
from evaluation.src.loop.credit import credit_apply, credit_distribution
from evaluation.src.loop.invariants import (
    arm_fingerprint, assert_arm_declared, assert_arm_factions, assert_base_rates, assert_baseline_coherence,
    assert_credit_engaged, assert_discussion_credit_engaged, assert_fingerprint_consistent,
    assert_observations_retired, assert_score, expand_window)
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


def _stamp_obs_generations(store: Path, gen: int, sidecar: Path) -> tuple[dict, dict]:
    """First-seen AND last-reinforced generation per obs record `key`, persisted in a run sidecar. The loop
    clock is GENERATION, not wall-clock: each re-extraction stamps a fresh created_at, so timestamps can't
    be the decay key — but the record key is stable across dedup merges (the survivor keeps its key), so a
    reinforced obs keeps its original first-seen age while its observation_count grows AND its
    last-reinforced clock advances. A reinforcement is detected as a RISE in observation_count for a key we
    already track. Returns (first_seen_map, reinforced_map). The first return value is the flat first-seen
    map synthesis/decay already consume; the reinforced map feeds the count-scaled obs decay.

    Sidecar shape: {"first_seen": {key: gen}, "reinforced": {key: gen}, "counts": {key: count}}. Legacy
    flat {key: gen} sidecars (first_seen only) load as first_seen with reinforced initialized to it and
    counts seeded from THIS pass — that seeding is not itself counted as a reinforcement (no prior count
    to compare against, so we can't know a rise happened)."""
    raw = json.loads(sidecar.read_text()) if sidecar.exists() else {}
    if raw and all(isinstance(v, int) for v in raw.values()):   # legacy flat {key: first_seen} sidecar
        first_seen, reinforced, counts = dict(raw), dict(raw), {}
    else:
        first_seen = raw.get("first_seen", {})
        reinforced = raw.get("reinforced", {})
        counts = raw.get("counts", {})
    obs = json.loads((store / "observations.json").read_text())
    for recs in obs.get("namespaces", {}).values():
        for r in recs:
            key = r.get("key")
            count = r["value"].get("observation_count", 1)
            if key not in first_seen:
                first_seen[key] = reinforced[key] = gen
                counts[key] = count
            elif key not in counts:          # legacy/first-touch: seed the count, NOT a reinforcement
                counts[key] = count
            elif count > counts[key]:        # a genuine rise in count = reinforced this gen
                reinforced[key] = gen
                counts[key] = count
    sidecar.write_text(json.dumps(
        {"first_seen": first_seen, "reinforced": reinforced, "counts": counts}, indent=2))
    return first_seen, reinforced


def _run_one_game(out_jsonl: Path, prefix: str, cfg: LoopConfig, configs: str,
                  seed: Path | None = None, dump: Path | None = None,
                  game_id: str | None = None, extra: tuple = (),
                  experiment: str | None = None, env_extra: dict | None = None) -> None:
    """One game via run_batch (--runs-per-config 1). Separate seed/dump dirs let parallel games share a
    read-only snapshot seed while each dumps to its own store (no shared-store write race). game_id pins
    the role draw + scheduler seed (run_batch --game-ids-file) so the ON and OFF arms run the SAME board —
    the paired A/B: memory is the only difference, which cancels the cross-game variance in on-off."""
    cmd = [
        "poetry", "run", "python", "scripts/run_batch.py",
        "--configs", configs, "--runs-per-config", "1",
        # v7: SP-only injection by default (obs = synthesis substrate, never injected — report §6.8). Passed
        # on BOTH arms: harmless + symmetric on the OFF arm (all_disabled retrieves nothing regardless).
        "--retrieval-types", cfg.retrieval_types,
        "--output", str(out_jsonl), "--session-prefix", prefix,
    ]
    if experiment:  # nest eval-case sidecars under batch_results/<experiment>/ (--output keeps records here)
        cmd += ["--experiment", experiment]
    if seed is not None:
        cmd += ["--seed-store-dir", str(seed)]
    if dump is not None:
        cmd += ["--dump-store-dir", str(dump)]
    if game_id is not None:
        gids = out_jsonl.with_suffix(".gameids.json")
        gids.write_text(json.dumps([game_id]))
        cmd += ["--game-ids-file", str(gids)]
    cmd += list(extra)
    subprocess.run(cmd, cwd=REPO, env={**os.environ, **cfg.env(), **(env_extra or {})}, check=True)


def _game_tasks(run_dir: Path, out_jsonl: Path, prefix: str, cfg: LoopConfig, configs: str,
                seed: Path | None = None, dump_each: bool = False,
                game_id_base: str | None = None, extra: tuple = (),
                experiment: str | None = None, env_extra: dict | None = None) -> list:
    """Build (but don't run) one arm's per-game thunks. Each thunk plays game-k and returns
    (out_k, dump_k). Returned as a list so a caller can pool BOTH arms' thunks together. game_id_base
    (the SAME value for ON and OFF in a generation) pins each game-k's board so the arms play matched
    draws — the paired A/B; memory is the only difference, which cancels cross-game variance in on-off."""
    stem = out_jsonl.stem

    def _make(k: int):
        def _one():
            out_k = run_dir / f"{stem}_g{k}.jsonl"
            dump_k = None
            if dump_each:
                dump_k = run_dir / f"{stem}_store_g{k}"
                dump_k.mkdir(parents=True, exist_ok=True)
            gid = f"{game_id_base}_g{k}" if game_id_base else None
            _run_one_game(out_k, f"{prefix}_g{k}", cfg, configs, seed=seed, dump=dump_k, game_id=gid,
                          extra=extra, experiment=experiment, env_extra=env_extra)
            return out_k, dump_k
        return _one

    return [_make(k) for k in range(cfg.games_per_generation)]


def _concat_games(out_jsonl: Path, results: list) -> list:
    """Concatenate an arm's per-game records (results = [(out_k, dump_k), ...]) into out_jsonl, unlink the
    redundant per-game files, and return the dump dirs (for the freeze-old merge)."""
    dumps: list = []
    with open(out_jsonl, "w") as f:
        for out_k, dump_k in results:
            if out_k.exists():
                f.write(out_k.read_text())
            out_k.unlink(missing_ok=True)
            if dump_k is not None:
                dumps.append(dump_k)
    return dumps


def _run_arms_parallel(run_dir: Path, on_jsonl: Path, off_jsonl: Path, cfg: LoopConfig, configs: str,
                       snapshot: Path, pair_base: str, off_baseline: bool,
                       experiment: str | None = None, on_env: dict | None = None) -> list:
    """Run the ON and OFF arms' games CONCURRENTLY in ONE capped pool (total concurrency =
    game_concurrency), so the OFF baseline overlaps the ON arm instead of running after it (~halves
    per-gen wall-clock at a bounded cap). Independent by construction: OFF (all_disabled, no seed/dump)
    touches nothing; ON seeds read-only from the snapshot and dumps to its own per-game stores; the merge
    happens AFTER all games. Returns the ON dump dirs. Pairing is preserved — game-k is matched by
    game_id across arms regardless of run order."""
    on_tasks = _game_tasks(run_dir, on_jsonl, f"loop_{run_dir.name}_{on_jsonl.stem}",
                           cfg, configs, seed=snapshot, dump_each=True, game_id_base=pair_base,
                           experiment=experiment, env_extra=on_env)
    off_tasks = _game_tasks(run_dir, off_jsonl, f"loop_{run_dir.name}_{off_jsonl.stem}",
                            cfg, "all_disabled", seed=None, dump_each=False, game_id_base=pair_base,
                            extra=("--no-memory-seed", "--no-memory-dump"),
                            experiment=experiment) if off_baseline else []
    n_on = len(on_tasks)
    with ThreadPoolExecutor(max_workers=max(1, cfg.game_concurrency)) as pool:
        results = list(pool.map(lambda t: t(), on_tasks + off_tasks))
    dump_dirs = _concat_games(on_jsonl, results[:n_on])
    if off_baseline:
        _concat_games(off_jsonl, results[n_on:])
    return dump_dirs


def _tell_tick(run_dir: Path, gen: int, on_jsonl: Path) -> dict:
    """One generation's tell pipeline (v1, 2026-07-13): mine + role-blind k=2 detect the ON arm's games
    against the CURRENT frozen checklist, fold (wording dedup into canon, probation/null verdicts,
    publish checklist v_{k+1}), then rebuild the injected book from ALL detected instances to date.
    games_per_generation=10 makes the fold cadence the ledger spec's N=10. Roles accumulate in a sidecar
    because lift denominators span every generation's games. Lazy imports: the tell modules pull LLM
    deps only when the pipeline is ON."""
    from evaluation.src.loop.tell_credit import build_book_file, cast_prior_base, lift_table
    from evaluation.src.loop.tell_fold import fold
    from evaluation.src.loop.tells import detect_games, load_games, mine_games

    store_dir = run_dir / "tell_store"
    state = json.loads((store_dir / "state.json").read_text())
    checklist = json.loads((store_dir / f"checklist_v{state['fold']}.json").read_text())
    games = load_games(str(on_jsonl))

    mined_path = store_dir / f"mined_gen{gen}.jsonl"
    n_mined = mine_games(games, mined_path)
    detected, scanned = detect_games(games, checklist)

    roles_path = store_dir / "roles_by_game.json"
    roles_by_game = json.loads(roles_path.read_text()) if roles_path.exists() else {}
    roles_by_game.update({g["game_id"]: g["roles"] for g in games})
    roles_path.write_text(json.dumps(roles_by_game))

    mined_rows = [json.loads(l) for l in open(mined_path) if l.strip()]
    rep = fold(store_dir, mined_rows, detected, scanned, roles_by_game)
    # the tell family's baseline coherence: the cast prior is the base, registered self-keyed
    assert_baseline_coherence(rep["credited_channels"],
                              {k: tuple(v) for k, v in rep["base_rates"].items()})

    all_detected = [json.loads(l) for l in open(store_dir / "instances.jsonl") if l.strip()]
    all_detected = [r for r in all_detected if r.get("source_kind") == "DETECTED"]
    canon = json.loads((store_dir / "canon.json").read_text())
    text_of = {c["tell_id"]: c["text"] for c in canon}
    n_book = build_book_file(lift_table(all_detected, roles_by_game), text_of,
                             store_dir / "book.json")
    return {**{k: rep[k] for k in ("fold", "new_wordings", "new_canonicals",
                                   "archived_singletons", "archived_null_lift", "checklist")},
            "mined": n_mined, "detected": len(detected), "book": n_book,
            "cast_prior": cast_prior_base(roles_by_game)["tell/vote"][0]}


def _write_loop_config(run_dir: Path, experiment: str, cfg: LoopConfig, base_store: str | None,
                       configs: str) -> None:
    """Stamp the campaign's config.json (the LoopConfig mirror) under batch_results/<experiment>/
    BEFORE the first game, so the per-game run_batch calls (write-if-absent) don't shadow it with
    the thinner run_batch-resolved config."""
    descriptor = batch_layout.build_loop_descriptor(
        experiment, asdict(cfg), base_store=base_store, configs=configs,
        created_at=datetime.now(timezone.utc).isoformat(), argv=sys.argv[1:], run_dir=str(run_dir))
    batch_layout.write_run_config(experiment, descriptor)


def run_loop(run_dir: str | Path, cfg: LoopConfig, *, base_store: str | None = "memory_stores/v6_1",
             configs: str = "all_enabled") -> list[dict]:
    run_dir = Path(run_dir)
    # ⭐ARM-DECLARATION GATE (fail-closed, before ANY spend): refuse to start unless the ON arm is declared
    # (cfg.expect_factions) or the check is explicitly waived (cfg.unchecked_arm). The per-gen
    # assert_arm_factions only fires when an intent is GIVEN, so a forgotten flag silently re-opened the v2
    # trap; this makes declaration the default you cannot omit your way past.
    assert_arm_declared(cfg.expect_factions, cfg.unchecked_arm)
    # ⭐PRO-2.5 COST GUARD. consolidate (synthesis) + credit_apply (tagger) run IN THIS process and resolve
    # their model via get_llm_pro() -> os.getenv("GOOGLE_GENAI_PRO_MODEL", DEFAULT_PRO_MODEL="gemini-2.5-pro").
    # cfg.env() is only applied to game SUBPROCESSES; pin it on the driver's OWN env too so in-process
    # synthesis/tagger/dedup-fallback never silently hit pro-2.5 because of the launch shell (the $55 trap).
    os.environ.update(cfg.env())
    # Stamp run start for the cost-capture window (cost.py sums Langfuse traces from here -> now). Keep the
    # ORIGINAL start on resume so the window still spans every generation.
    run_dir.mkdir(parents=True, exist_ok=True)
    experiment = run_dir.name  # campaign id; eval_cases + config.json nest under batch_results/<experiment>/
    _write_loop_config(run_dir, experiment, cfg, base_store, configs)
    meta_path = run_dir / "run_meta.json"
    if not meta_path.exists():
        meta_path.write_text(json.dumps({"run_started_at": datetime.now(timezone.utc).isoformat()}, indent=2))
    obs_sidecar = run_dir / "obs_generations.json"
    hist_path = run_dir / "loop_history.json"
    # RESUME: a run-dir with a loop_history continues from the next generation, reusing the existing
    # end-state store + obs-decay sidecar (no cold-wipe). The gen records of prior gens stay on disk, so
    # the rolling credit window still resolves. prev_obs_counts (the incremental-synth baseline) is
    # restored from the last consolidate. A fresh run-dir (no history) starts cold as before.
    history: list[dict] = json.loads(hist_path.read_text()) if hist_path.exists() else []
    if history:
        store = run_dir / "store"                       # reuse end-state store; do NOT re-init/wipe
        start_gen = history[-1]["generation"] + 1
        prev_obs_counts = (history[-1].get("consolidate") or {}).get("obs_counts", {}) or {}
        print(f"\n=== RESUMING at generation {start_gen} ({len(history)} gens done; store + sidecar "
              f"reused, no wipe) ===", flush=True)
    else:
        store = _init_store(run_dir, base_store)
        _stamp_obs_generations(store, 0, obs_sidecar)   # warm-start obs = generation 0 (oldest)
        start_gen = 1
        prev_obs_counts = {}
    sp_path = store / "strategy_points.json"

    tell_store = run_dir / "tell_store"
    if cfg.tells and not (tell_store / "canon.json").exists():
        from evaluation.src.loop.tell_fold import init_store
        if not cfg.tell_seed_checklist:
            raise AssertionError("tells=True on a cold tell store needs --tell-seed-checklist "
                                 "(the frozen seed canon)")
        init_store(tell_store, json.loads(Path(cfg.tell_seed_checklist).read_text()))
        if cfg.tell_seed_book:
            shutil.copy2(cfg.tell_seed_book, tell_store / "book.json")

    for gen in range(start_gen, cfg.generations + 1):
        on_jsonl = run_dir / f"gen{gen}_on.jsonl"
        off_jsonl = run_dir / f"gen{gen}_off.jsonl"
        arms = "ON+OFF" if cfg.off_baseline else "ON"
        print(f"\n=== generation {gen}/{cfg.generations} — {arms} arms "
              f"({cfg.games_per_generation}/arm, cap {cfg.game_concurrency} parallel, {cfg.model}) ===",
              flush=True)
        # Freeze the gen-start store as a read-only SNAPSHOT; ON games seed from it (read-only) and dump to
        # their own per-game stores; the OFF arm (all_disabled, no seed/dump) touches nothing. ON+OFF run in
        # ONE capped pool (they overlap within game_concurrency), then ONE freeze-old merge folds the new ON
        # obs in (cross-game dups -> observation_count; snapshot frozen). Pairing holds: game-k is matched
        # by game_id across arms regardless of run order.
        snapshot = run_dir / f"gen{gen}_snapshot"
        if snapshot.exists():
            shutil.rmtree(snapshot)
        shutil.copytree(store, snapshot)
        pair_base = f"pair_{run_dir.name}_gen{gen}"   # SAME boards for ON and OFF this gen (paired A/B)
        # the ON arm (and ONLY the ON arm) reads the current tell book, rebuilt at each fold below
        on_env = ({"WW_TELL_BOOK": str(tell_store / "book.json")}
                  if cfg.tells and (tell_store / "book.json").exists() else None)
        dump_dirs = _run_arms_parallel(run_dir, on_jsonl, off_jsonl, cfg, configs, snapshot, pair_base,
                                       cfg.off_baseline, experiment, on_env=on_env)
        # ⭐ARM GUARD: verify the ON arm enabled memory for exactly the declared factions BEFORE spending
        # the rest of the budget — crashes gen 1 on the v2 trap (configs=all_enabled vs intended town_only).
        # Always surfaced + recorded (even with no --expect-factions) so the arm is never invisible again.
        arm_factions = sorted(assert_arm_factions(on_jsonl, cfg.expect_factions))
        print(f"  arm: memory ENABLED for {arm_factions} (configs={configs}, "
              f"expect={cfg.expect_factions or 'unchecked'})", flush=True)
        # ⭐§6.8 GUARD (v7, 2026-07-15): under the SP-only default the ON games must have run with obs
        # retrieval OFF — observations are synthesis substrate, never injected. Checks the recorded game
        # config AND a sampled decision's retrieved-obs slot; no-ops for the 'both'/'obs_only' arms.
        assert_observations_retired(on_jsonl, cfg.retrieval_types)
        # ⭐PROVENANCE DRIFT GUARD: the runtime_fingerprint (backend/model/temp/prompt/commit) run_batch
        # stamps on each game must hold constant across the whole run; a flip (e.g. a resume under a
        # different env/backend) silently splices incomparable scores. Pin gen-1's into run_meta as the
        # reference; assert every later gen + the OFF arm match it (the 'never compare across backends' rule).
        fp = arm_fingerprint(on_jsonl)
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
        reference = meta.get("runtime_fingerprint")
        if reference is None:
            reference = meta["runtime_fingerprint"] = fp
            meta_path.write_text(json.dumps(meta, indent=2))
        assert_fingerprint_consistent(on_jsonl, reference)
        if cfg.off_baseline:
            assert_fingerprint_consistent(off_jsonl, reference)
        print(f"  fingerprint: backend={fp.get('llm_backend')} game={fp.get('game_model')} "
              f"pro={fp.get('pro_model')} commit={str(fp.get('git_commit', '?'))[:8]}", flush=True)
        mstats = merge_new_obs(store, snapshot, dump_dirs,
                               dedup_model=cfg.dedup_model, no_merge=not cfg.obs_dedup_merge)
        print(f"  merge: {mstats}", flush=True)
        shutil.rmtree(snapshot, ignore_errors=True)      # cleanup snapshot + per-game temp stores
        for d in dump_dirs:
            shutil.rmtree(d, ignore_errors=True)

        # credit runs over the ON arm window (rolling). The de-luck BASELINE comes from the clean,
        # same-epoch OFF arm (consolidation_design §3), NOT the incidental memory-off decisions inside the
        # ON games (thin + biased toward retrieval-skipped/early boards). The off arm is the comparison AND
        # calibrates the baseline. When off_baseline is disabled, credit_apply falls back to the ON glob.
        w = cfg.window_generations or gen
        gens = list(range(max(1, gen - w + 1), gen + 1))
        win_on = expand_window(run_dir, gens, "on")          # explicit list; every file asserted present
        window = " ".join(win_on)
        cstats, cdist = {}, {}
        if cfg.credit:
            base_rates = None
            off_window = None
            if cfg.off_baseline:
                off_window = " ".join(expand_window(run_dir, gens, "off"))
                base_rates = compute_base_rates(off_window)
                assert_base_rates(base_rates, off_ran=True)   # empty base_rates => silent halo
            # OPTION A (decision 2026-07-05): pass the OFF window so credit_apply can score the SAME
            # instrument on the OFF arm (endpoint floor + concealment heat) — the same-instrument base
            # that makes discussion credit a LIFT, not a level. Free since the tagger mode's retirement
            # (2026-07-13): every discussion instrument is deterministic.
            cstats = credit_apply(sp_path, window, base_rates=base_rates,
                                  discussion=cfg.discussion_credit, off_window=off_window)
            follows = assert_credit_engaged(win_on, cstats.get("ledger_keys", 0))  # dead-credit guard
            disc_follows = assert_discussion_credit_engaged(  # discussion analog (build_ledger is blind to it)
                win_on, cstats.get("disc_credited", 0), enabled=cfg.discussion_credit)
            if cfg.off_baseline:  # ⭐baseline-coherence: every credited channel needs a same-function OFF base
                written = json.loads((sp_path.parent / "base_rates.json").read_text())
                assert_baseline_coherence(cstats.get("credited_channels", {}), written)
            cdist = credit_distribution(sp_path, min_follow=cfg.prune_min_follow)  # did credit ENGAGE?
            print(f"  credit: {cstats} window_follows={follows} disc_follows={disc_follows}\n"
                  f"  credit_dist: {cdist}", flush=True)
        tstats = {}
        if cfg.tells:
            tstats = _tell_tick(run_dir, gen, on_jsonl)
            print(f"  tells: {tstats}", flush=True)
        cons = {}
        if cfg.prune or cfg.evict or cfg.synthesize or cfg.evict_observations:
            obs_gen_map, reinforced_map = _stamp_obs_generations(store, gen, obs_sidecar)  # new -> `gen`
            cons = consolidate(store, cfg, prev_obs_counts, obs_gen_map=obs_gen_map, current_gen=gen,
                               reinforced_map=reinforced_map)
            prev_obs_counts = cons.get("obs_counts", prev_obs_counts)
            print(f"  consolidate: prune_evict={cons.get('prune_evict')} "
                  f"obs_evict={cons.get('obs_evict')} synth={cons.get('synth')}", flush=True)
        score = generation_score(                                      # bucket by ARM (file), not the flag
            str(run_dir / f"gen{gen}_on.jsonl"),
            str(run_dir / f"gen{gen}_off.jsonl") if cfg.off_baseline else None)
        assert_score(score, label=f"gen{gen}")                         # 0 decisions => silent empty point
        print(f"  score: { {k: v for k, v in score.items() if not k.startswith('n_')} }", flush=True)
        history.append({"generation": gen, "score": score, "credit": cstats, "tells": tstats,
                        "credit_dist": cdist, "consolidate": cons, "arm_factions": arm_factions})
        # write EVERY generation, not just at the end: the per-gen credit_dist/consolidate stats are
        # computed on the store-as-it-was-that-gen, which the next gen OVERWRITES — so a mid-run crash
        # would lose them irrecoverably (games + score re-derive from the gen records; these don't).
        (run_dir / "loop_history.json").write_text(json.dumps(history, indent=2))
        # Preserve the END-of-gen content (obs + SPs only, light) for post-hoc inspection: the store is
        # overwritten in place by the next gen, so without this the gen-3 content read isn't possible.
        snap = run_dir / f"gen{gen}_store"
        snap.mkdir(exist_ok=True)
        for f in ("observations.json", "strategy_points.json"):
            if (store / f).exists():
                shutil.copy2(store / f, snap / f)

    print(f"\nloop history -> {run_dir / 'loop_history.json'}", flush=True)
    # COST CAPTURE (best-effort, post-hoc, NO auto-abort — surfaces the spend, a human decides). May
    # undercount the final minutes (Langfuse ingestion lag); re-run `python -m evaluation.src.loop.cost`
    # a few minutes later for the settled total.
    try:
        from evaluation.src.loop.cost import run_cost
        rep = run_cost(run_dir)
        (run_dir / "cost_report.json").write_text(json.dumps(rep, indent=2))
        print(f"COST (Langfuse, realized): grand=${rep['grand_total_usd']} games=${rep['games_total_usd']} "
              f"overhead=${rep['overhead_usd']}\n  per-gen games: {rep['per_gen_games_usd']}", flush=True)
    except Exception as e:
        print(f"[cost] capture failed (non-fatal): {e}", flush=True)
    return history


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", default=None,
                    help="campaign output dir; defaults to batch_results/<experiment> when --experiment is given")
    ap.add_argument("--experiment", default=None,
                    help="campaign id; sets the run-dir to batch_results/<experiment> unless --run-dir is passed")
    ap.add_argument("--base-store", default="memory_stores/v6_1", help="warm-start baseline ('' = cold)")
    ap.add_argument("--configs", default="all_enabled", help="run_batch config name (the arm)")
    ap.add_argument("--generations", type=int, default=10)
    ap.add_argument("--games-per-generation", type=int, default=5)
    ap.add_argument("--window-generations", type=int, default=6, help="credit de-luck lookback (gens)")
    ap.add_argument("--synth-every-k", type=int, default=2, help="synthesize every k gens (cull every gen)")
    ap.add_argument("--game-concurrency", type=int, default=5, help="parallel games within a generation")
    ap.add_argument("--model", default="gemini-3.1-flash-lite")
    ap.add_argument("--retrieval-types", default=LoopConfig.retrieval_types,
                    choices=["both", "observations_only", "strategy_points_only"],
                    help="which memory types the ON arm injects; v7 default strategy_points_only (obs are "
                         "synthesis substrate, never injected — report §6.8). 'both' = the v5/v6 obs+SP arm")
    ap.add_argument("--no-synth", action="store_true")
    # threshold knobs (default = the held-out-validated run values; a cheap smoke LOWERS them so the
    # credit-aware path fires at tiny N — validating WIRING, not calibration)
    ap.add_argument("--prune-min-follow", type=int, default=LoopConfig.prune_min_follow)
    ap.add_argument("--synth-track-min-follow", type=int, default=LoopConfig.synth_track_min_follow)
    ap.add_argument("--synth-min-new-obs", type=int, default=LoopConfig.synth_min_new_obs)
    # evict + obs-decay thresholds — also LOWERED in a smoke so those paths fire at tiny N (else the smoke
    # silently skips evict/decay, the paths most likely to hide a bug).
    ap.add_argument("--evict-min-retrieved", type=int, default=LoopConfig.evict_min_retrieved)
    ap.add_argument("--obs-evict-min-age", type=int, default=LoopConfig.obs_evict_min_age)
    ap.add_argument("--protect-min-follow", type=int, default=LoopConfig.protect_min_follow)
    ap.add_argument("--tells", action="store_true", help="run the tell pipeline (mine + detect + fold + book) per generation")
    ap.add_argument("--tell-seed-checklist", default="", help="frozen seed canon JSON (required with --tells on a cold store)")
    ap.add_argument("--tell-seed-book", default="", help="optional gen-1 book JSON (from the held-out lift table)")
    ap.add_argument("--expect-factions", default=None,
                    help="DECLARE which factions the ON arm should give memory ('town_only', 'all', or a "
                         "comma list); crashes gen 1 if --configs enables a different set (the v2 trap guard)")
    ap.add_argument("--unchecked-arm", action="store_true",
                    help="opt OUT of the arm-declaration gate (throwaway smokes only); paid runs MUST instead "
                         "pass --expect-factions — the loop refuses to start with neither")
    args = ap.parse_args()
    cfg = LoopConfig(generations=args.generations, games_per_generation=args.games_per_generation,
                     window_generations=args.window_generations, synth_every_k_gens=args.synth_every_k,
                     game_concurrency=args.game_concurrency, model=args.model,
                     retrieval_types=args.retrieval_types, synthesize=not args.no_synth,
                     prune_min_follow=args.prune_min_follow, synth_track_min_follow=args.synth_track_min_follow,
                     synth_min_new_obs=args.synth_min_new_obs,
                     tells=args.tells, tell_seed_checklist=args.tell_seed_checklist,
                     tell_seed_book=args.tell_seed_book,
                     evict_min_retrieved=args.evict_min_retrieved, obs_evict_min_age=args.obs_evict_min_age,
                     protect_min_follow=args.protect_min_follow, expect_factions=args.expect_factions,
                     unchecked_arm=args.unchecked_arm)
    run_dir = args.run_dir or (f"batch_results/{args.experiment}" if args.experiment else None)
    if run_dir is None:
        ap.error("pass --experiment NAME (or an explicit --run-dir PATH)")
    run_loop(run_dir, cfg, base_store=args.base_store or None, configs=args.configs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
