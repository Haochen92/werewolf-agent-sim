"""Compounding loop — (b) CONSOLIDATION: prune/evict by realized credit + credit-aware synthesis.

Runs on a credited store (after credit.credit_apply). Three levers, all toggleable:
  PRUNE   drop SPs whose de-luck lift < tau with enough follows (b1 — the stably-harmful ones).
  EVICT   drop SPs surfaced >= R times but NEVER followed (the agent consistently rejects them = dead).
  SYNTH   credit-aware synthesis (CREDIT_SYNTH_PROMPT, realized track record) for cells with NEW obs —
          adds fresh SPs; existing SPs PERSIST so their credit accumulates across generations.

Existing SPs keep their keys (credit history intact); prune/evict cull, synth grows. SYNTH-DEDUP: synth
APPENDS, so a freeze-old KEEP/DISCARD SP dedup runs right after (_dedup_strategy_points) to collapse
near-duplicate synthesized SPs onto the credited older survivor — otherwise re-synthesizing active cells
each generation smears the credit signal across duplicates. Pure prune/evict is LLM-free → testable
offline; synth + the SP dedup are the paid steps (flash-lite).
"""

from __future__ import annotations

import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from evaluation.src.loop.config import LoopConfig
from evaluation.src.loop.credit import sp_lift


def _cell_of(ns_key: str) -> str:
    return "/".join(ns_key.split("/")[1:])  # "strategy_points/role/phase" -> "role/phase"


def _evict_ok(v: dict, cfg: LoopConfig) -> bool:
    """Should a retrieved-but-never-followed SP be evicted? Scope-aware (§10b applicability funnel): if
    the non-follow is DOMINATED by not_relevant, the situation simply didn't hold here = a retrieval/
    scoping miss, NOT bad content, so sparing it avoids deleting good advice over a retrieval artifact.
    Evict only when the agent APPLIED it and overrode it (override-dominant = rejected on the merits);
    no verdict signal at all (both 0) is a coverage gap, not evidence => also spared."""
    if not cfg.evict_require_override:
        return True  # legacy blunt evict: any surfaced-but-unfollowed SP
    ov = v.get("override_count", 0)
    nr = v.get("not_relevant_count", 0)
    return ov > 0 and ov >= nr


def prune_and_evict(sp_namespaces: dict, base_rates: dict, cfg: LoopConfig) -> dict:
    """Mutate sp_namespaces in place: drop harmful (lift<tau, follow>=N) + rejected-on-merits
    (retrieved>=R, follow==0, override-dominant) SPs. Never drops a positive-lift SP, nor one whose
    non-follow is a retrieval mismatch (not_relevant-dominant). Returns {pruned, evicted, kept, spared}."""
    pruned = evicted = kept = spared = 0
    for ns_key, recs in list(sp_namespaces.items()):
        base = base_rates.get(_cell_of(ns_key), [0.0])[0]
        survivors = []
        for r in recs:
            v = r["value"]
            lift = sp_lift(v, base)
            follow = v.get("follow_count", 0)
            retrieved = v.get("retrieved_count", 0)
            # PROVEN-SP EXEMPTION (edge 1): a POSITIVE de-luck lift with even thin evidence is never
            # dropped — a rare-but-proven lesson survives any prune/evict/age rule. Degradation is
            # CREDIT-only: a note leaves via negative lift (souring) or never-followed dead weight, never
            # because it merely got old (edge 2).
            if lift is not None and lift > 0 and follow >= cfg.protect_min_follow:
                survivors.append(r)
                kept += 1
                continue
            if cfg.prune and lift is not None and lift < cfg.prune_tau and follow >= cfg.prune_min_follow:
                pruned += 1
                continue
            if cfg.evict and follow == 0 and retrieved >= cfg.evict_min_retrieved:
                if _evict_ok(v, cfg):
                    evicted += 1
                    continue
                spared += 1  # surfaced+unfollowed but not_relevant-dominant => retrieval's problem, keep
            survivors.append(r)
            kept += 1
        sp_namespaces[ns_key] = survivors
    return {"pruned": pruned, "evicted": evicted, "kept": kept, "spared": spared}


def evict_observations(obs_path: str | Path, obs_gen_map: dict, current_gen: int, cfg: LoopConfig) -> dict:
    """Decay observations by AGE x FREQUENCY (obs carry no credit, so they can't be pruned by lift).
    Drop obs that are BOTH old (first seen <= current_gen - min_age) AND rare (observation_count <=
    max_count). Keeps old-but-recurring lessons (high count survive any age) and every recent obs. Edits
    obs.json in place; the SHA-keyed embedding cache auto-rebuilds on the changed file.

    obs_gen_map: record `key` -> first-seen generation (driver sidecar). Stable across dedup merges (the
    survivor keeps its key, so a merged-and-reinforced obs keeps its ORIGINAL age but grows its count =
    exactly the 'old but proven' case we want to keep). Recency is a SELECTION here, not an LLM weight."""
    obs_path = Path(obs_path)
    store = json.loads(obs_path.read_text())
    dropped = kept = 0
    for ns_key, recs in list(store.get("namespaces", {}).items()):
        survivors = []
        for r in recs:
            gen = obs_gen_map.get(r.get("key"), 0)
            count = r["value"].get("observation_count", 1)
            if gen <= current_gen - cfg.obs_evict_min_age and count <= cfg.obs_evict_max_count:
                dropped += 1
                continue
            survivors.append(r)
            kept += 1
        store["namespaces"][ns_key] = survivors
    obs_path.write_text(json.dumps(store, indent=2))
    return {"obs_dropped": dropped, "obs_kept": kept}


def _synth_cluster(live: list, depleted: bool, obs_gen_map: dict | None, synth_lookback: int | None,
                   incremental: bool) -> bool:
    """NEW-CLUSTERS-ONLY gate: re-synthesize a cluster only if it carries a NEW obs (first-seen after the
    last synth tick). The cell-level gate in synthesize() admits a cell on enough TOTAL new obs, but
    without THIS, every cluster in an admitted cell — including all-old ones — got re-synthesized each
    tick, regenerating SP variants of already-distilled lessons that don't exact-dedup → the store
    compounded ~6x/run (5.4 -> 34 SPs/cell). Return True (synthesize) when we can't/shouldn't filter:
    a DEPLETED cell replenishes from its old clusters; non-incremental or no gen map => full re-synth."""
    if not live:
        return False
    if not incremental or depleted or obs_gen_map is None or synth_lookback is None:
        return True
    return any(obs_gen_map.get(k, 0) > synth_lookback for k in live)


def _track_record(sp_recs: list, base: float, min_follow: int = 5) -> str:
    rows = [(sp_lift(r["value"], base), r["value"].get("follow_count", 0), r["value"].get("action", ""))
            for r in sp_recs]
    rows = [(lf, f, a) for lf, f, a in rows if lf is not None and f >= min_follow]
    if not rows:
        return ""
    return "\n".join(f"- realized lift {lf:+.2f} (followed {f}x): {a}"
                     for lf, f, a in sorted(rows, reverse=True))


def synthesize(store_dir: Path, sp_namespaces: dict, base_rates: dict, cfg: LoopConfig,
               prev_obs_counts: dict | None = None,
               obs_gen_map: dict | None = None, current_gen: int | None = None) -> tuple[dict, dict]:
    """Credit-aware synthesis for cells with NEW obs since prev tick (incremental). Appends fresh SPs to
    sp_namespaces. Returns ({added, cells_synthed}, current_obs_counts). LLM step (model via cfg.env())."""
    # imported lazily so pure prune/evict stays import-light + LLM-free
    from Agents.memory.batch_deduplication.config import BatchDedupRunConfig
    from Agents.memory.persistence import memory_store_paths, seed_memory_from_json_files_cached
    from Agents.memory.store import store
    from Agents.memory.strategy_synthesis import cluster_observations_for_synth, synthesize_cluster_sps
    from Agents.schemas.roles import VALID_ACTION_PHASES_BY_ROLE, roles as ALL_ROLES

    obs_path, sp_path = memory_store_paths(store_dir)
    seed_memory_from_json_files_cached(observations_path=obs_path, strategy_points_path=sp_path,
                                       target_store=store, cache_dir=store_dir)
    cfgd = BatchDedupRunConfig(similarity_threshold=0.70, cluster_mode="bounded", max_cluster_size=15)
    prev = prev_obs_counts or {}
    # "New obs since last synth" must count ARRIVALS (by first-seen generation), NOT the net count change.
    # Net change cancels additions against obs DECAY (removals), so once decay >= additions the trigger
    # reads "no new obs" even when fresh obs DID arrive — silently STALLING synthesis (the gen-6 stall).
    # obs_gen_map (record key -> first-seen gen) makes the trigger decay-immune; net change is the fallback.
    synth_lookback = (current_gen - cfg.synth_every_k_gens) if current_gen is not None else None
    obs_counts: dict[str, int] = {}
    tasks = []
    for role in ALL_ROLES:
        for phase in VALID_ACTION_PHASES_BY_ROLE.get(role, []):
            cell = f"{role}/{phase}"
            items, clusters = cluster_observations_for_synth(store, ("observations", role, phase), cfgd)
            obs_counts[cell] = len(items)
            if obs_gen_map is not None and synth_lookback is not None:
                new_obs = sum(1 for k in items if obs_gen_map.get(k, 0) > synth_lookback)
            else:
                new_obs = obs_counts[cell] - prev.get(cell, 0)   # fallback: net change (no gen map)
            depleted = len(sp_namespaces.get(f"strategy_points/{cell}", [])) < cfg.synth_replenish_floor
            if cfg.incremental and new_obs < cfg.synth_min_new_obs and not depleted:
                continue  # not enough fresh evidence AND the cell isn't depleted → skip (cost guard)
            tr = _track_record(sp_namespaces.get(f"strategy_points/{cell}", []),
                               base_rates.get(cell, [0.0])[0], min_follow=cfg.synth_track_min_follow)
            for cl in clusters:
                live = [k for k in cl if k in items]
                if _synth_cluster(live, depleted, obs_gen_map, synth_lookback, cfg.incremental):
                    tasks.append((role, phase, live, items, tr))

    now = datetime.now(timezone.utc)
    added = 0

    def _run(t):
        role, phase, live, items, tr = t
        return role, synthesize_cluster_sps(role, phase, live, items, max_retries=1, track_record=tr)

    if tasks:
        with ThreadPoolExecutor(max_workers=12) as pool:
            for role, sps in pool.map(_run, tasks):
                for sp in sps:
                    ns = f"strategy_points/{role}/{sp.action_phase}"
                    sp_namespaces.setdefault(ns, []).append({
                        "created_at": now.isoformat(), "key": str(uuid.uuid4()),
                        "namespace": ["strategy_points", role, sp.action_phase],
                        "updated_at": now.isoformat(),
                        "value": {"observation_count": 1, "last_observed": now.isoformat(), "game_id": "",
                                  "situation": sp.composed_situation, "action": sp.action,
                                  "direction": sp.direction, "honesty": sp.honesty,
                                  "follow_count": 0, "retrieved_count": 0, "positive_count": 0,
                                  "neutral_count": 0, "negative_count": 0,
                                  "dimensions": sp.model_dump(mode="json")},
                    })
                    added += 1
    # with_track_record = cells synthesized using a realized-credit track record (the credit-AWARE path).
    # 0 while < synth_track_min_follow follows have accumulated => synthesis is silently halo-only; this
    # makes the thesis mechanism observable per generation instead of hoped.
    with_tr = len({(r, p) for r, p, _live, _items, tr in tasks if tr})
    return ({"added": added, "cells_synthed": len({(r, p) for r, p, *_ in tasks}),
             "with_track_record": with_tr}, obs_counts)


def _dedup_strategy_points(store_dir: Path, model: str) -> dict:
    """SP KEEP/DISCARD dedup (freeze-old) over the just-synthesized store. Collapses near-duplicate SPs,
    keeping the credited OLDER survivor (it absorbs the discarded dup's counts/timestamps). SPs NEVER
    MERGE — combining two directives is incoherent; this is the design's keep/discard, gate-partitioned by
    direction/honesty. Freeze-old (created_at boundary) makes the just-synthesized SPs the 'new' set and
    prior SPs frozen, so credit history survives. Reuses the production dedup core (persists to store).
    `model` runs the resolution: flash-lite is safe here (KEEP/DISCARD is schema-enforced, no merge text)
    and avoids the pro-2.5 cost on the per-generation re-dedup."""
    from Agents.memory.batch_deduplication.config import BatchDedupRunConfig
    from Agents.memory.batch_deduplication.orchestration import run_batch_memory_dedup
    report = run_batch_memory_dedup(BatchDedupRunConfig(
        seed_store_dir=store_dir, dump_store_dir=store_dir, model=model,
        incremental=True, apply=True, memory_kinds=["strategy_points"]))
    return {"ran": True, "namespaces": len(getattr(report, "stats", []))}


def consolidate(store_dir: str | Path, cfg: LoopConfig, prev_obs_counts: dict | None = None,
                obs_gen_map: dict | None = None, current_gen: int | None = None) -> dict:
    """Full consolidation tick on a (credited) store dir. Returns stats + obs_counts (for next tick).

    obs_gen_map/current_gen (driver-supplied) enable observation decay BEFORE synthesis, so the
    synthesizer distills only the surviving (recent or proven-recurring) obs."""
    store_dir = Path(store_dir)
    obs_path, sp_path = memory_store_paths_local(store_dir)
    base_rates = json.loads((store_dir / "base_rates.json").read_text()) \
        if (store_dir / "base_rates.json").exists() else {}

    oe = {}
    if cfg.evict_observations and obs_gen_map is not None and current_gen is not None:
        oe = evict_observations(obs_path, obs_gen_map, current_gen, cfg)

    # SYNTH -> DEDUP -> PRUNE (prune runs LAST). The SP-dedup collapses near-dup SPs onto the credited
    # survivor, ABSORBING its counts — so it can push a survivor across the eviction threshold. Pruning
    # BEFORE the dedup (the old order) let those dedup-bumped strongly-bad SPs (lift<tau & follow>=N) escape
    # eviction for a generation and get followed — the harmful tail that dragged outcomes below baseline.
    # Prune on the FINAL post-dedup counts so the tail is evicted the same generation it appears.
    # (FAST-CULL / SLOW-SYNTH still holds: synthesis (paid) only every k gens; prune/evict run every gen.)
    store = json.loads(sp_path.read_text())
    ns = store.setdefault("namespaces", {})
    do_synth = cfg.synthesize and (current_gen is None or current_gen % cfg.synth_every_k_gens == 0)
    syn, obs_counts = ({}, prev_obs_counts or {})
    if do_synth:
        syn, obs_counts = synthesize(store_dir, ns, base_rates, cfg, prev_obs_counts,
                                     obs_gen_map=obs_gen_map, current_gen=current_gen)
    sp_path.write_text(json.dumps(store, indent=2))   # persist synth before the SP dedup reads the store
    sd = {}
    if cfg.sp_dedup and syn.get("added"):             # only when synthesis added SPs to dedup
        sd = _dedup_strategy_points(store_dir, cfg.dedup_model)
    # prune LAST, on the post-dedup store (re-read: the dedup mutated the file on disk, not `ns`)
    store = json.loads(sp_path.read_text())
    ns = store.setdefault("namespaces", {})
    pe = prune_and_evict(ns, base_rates, cfg) if (cfg.prune or cfg.evict) else {}
    sp_path.write_text(json.dumps(store, indent=2))
    return {"prune_evict": pe, "obs_evict": oe, "synth": syn, "sp_dedup": sd, "obs_counts": obs_counts}


def memory_store_paths_local(store_dir: Path):
    """Avoid importing Agents (LLM-heavy) for the pure prune/evict path."""
    return store_dir / "observations.json", store_dir / "strategy_points.json"
