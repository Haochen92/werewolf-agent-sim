"""Consolidation store-ops: prune/evict by realized credit + credit-aware synthesis (production).

Runs on a credited store (after ``credit.credit_apply`` + ``conversion.conversion_apply``):
  PRUNE   drop SPs whose de-luck lift < tau with enough follows, OR whose conversion lift is as
          negative with enough tallies (the concealment class the follow ledger can't reach —
          always on in production, there is no conversion switch).
  EVICT   drop SPs surfaced >= R times but NEVER followed when override-dominant (rejected on the
          merits); not_relevant-dominant non-follows are spared (retrieval's fault, not content's).
  SYNTH   credit-aware synthesis (realized track record) for cells with NEW obs — adds fresh SPs;
          existing SPs PERSIST so their credit accumulates across ticks. A freeze-old KEEP/DISCARD
          SP dedup runs right after synth to collapse near-duplicates onto the credited survivor.

Pure prune/evict is LLM-free → testable offline; synth + the SP dedup are the paid steps.
Graduated from ``evaluation/src/loop/consolidate.py`` (go-live 2026-07-21).
"""

from __future__ import annotations

import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from Agents.memory.consolidation.config import TickConfig
from Agents.memory.consolidation.conversion import CONVERSION_CHANNEL, conversion_lift
from Agents.memory.consolidation.credit import base_for, sp_lift


def memory_store_paths_local(store_dir: Path):
    """Avoid importing the LLM-heavy persistence stack for the pure prune/evict path."""
    return store_dir / "observations.json", store_dir / "strategy_points.json"


def _cell_of(ns_key: str) -> str:
    return "/".join(ns_key.split("/")[1:])  # "strategy_points/role/phase" -> "role/phase"


def _is_proven(v: dict, base: float, cfg: TickConfig) -> bool:
    """PROVEN predicate: positive de-luck lift over the resolved OFF base with enough follows.
    Deliberately DIFFERS from the game-side raw-counter heuristic — this side has the base rates.
    Shared by prune_and_evict's exemption and synthesize's contested-lane cap so the two sites
    can't drift. ``base`` is already resolved (base_for) by the caller."""
    lift = sp_lift(v, base)
    return lift is not None and lift > 0 and v.get("follow_count", 0) >= cfg.protect_min_follow


def _evict_ok(v: dict, cfg: TickConfig) -> bool:
    """Should a retrieved-but-never-followed SP be evicted? Scope-aware: if the non-follow is
    DOMINATED by not_relevant, the situation simply didn't hold = a retrieval/scoping miss, NOT bad
    content — sparing it avoids deleting good advice over a retrieval artifact. Evict only when the
    agent APPLIED it and overrode it; no verdict signal at all is a coverage gap, also spared."""
    if not cfg.evict_require_override:
        return True  # legacy blunt evict: any surfaced-but-unfollowed SP
    ov = v.get("override_count", 0)
    nr = v.get("not_relevant_count", 0)
    return ov > 0 and ov >= nr


def prune_and_evict(sp_namespaces: dict, base_rates: dict, cfg: TickConfig) -> dict:
    """Mutate sp_namespaces in place: drop harmful (follow-lift OR conversion-lift < tau at enough
    evidence) + rejected-on-merits SPs. Never drops a positive-lift SP, nor one whose non-follow is
    a retrieval mismatch. Returns {pruned, evicted, kept, spared}."""
    pruned = evicted = kept = spared = 0
    for ns_key, recs in list(sp_namespaces.items()):
        survivors = []
        for r in recs:
            v = r["value"]
            # same-function OFF base, per SP: concealment-typed SPs difference against the conceal base
            base = base_for(base_rates, _cell_of(ns_key), v.get("sp_type"))
            lift = sp_lift(v, base)
            follow = v.get("follow_count", 0)
            retrieved = v.get("retrieved_count", 0)
            # PROVEN-SP EXEMPTION: a POSITIVE de-luck lift with even thin evidence is never dropped.
            # Degradation is CREDIT-only: a note leaves via negative lift (souring) or as
            # never-followed dead weight, never because it merely got old.
            if _is_proven(v, base, cfg):
                survivors.append(r)
                kept += 1
                continue
            if cfg.prune and lift is not None and lift < cfg.prune_tau and follow >= cfg.prune_min_follow:
                pruned += 1
                continue
            # CONVERSION term (always on): an SP whose presence in investigator find-windows tracks
            # failed conversions is prunable even at follow==0 — the concealment class the follow
            # ledger structurally can't reach. Sits AFTER the proven exemption on purpose: a
            # vote-proven SP is never deleted by the diffuse channel alone.
            clift = conversion_lift(v, base_for(base_rates, CONVERSION_CHANNEL))
            conv_n = v.get("conversion_pos_count", 0) + v.get("conversion_neg_count", 0)
            if clift is not None and clift < cfg.prune_tau and conv_n >= cfg.conversion_min_n:
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


def evict_observations(obs_path: str | Path, obs_gen_map: dict, current_gen: int, cfg: TickConfig,
                       reinforced_map: dict | None = None) -> dict:
    """Decay observations by a COUNT-SCALED survival allowance clocked from the LAST reinforcement
    (obs carry no credit, so they can't be pruned by lift): drop an obs once it has gone
    obs_evict_min_age x observation_count ticks WITHOUT reinforcement. Nothing is immortal, but
    each reinforcement restarts the clock, so a still-recurring lesson survives while a
    distilled-and-abandoned one decays. Edits obs.json in place."""
    obs_path = Path(obs_path)
    reinforced_map = reinforced_map or {}
    store = json.loads(obs_path.read_text())
    dropped = kept = 0
    for ns_key, recs in list(store.get("namespaces", {}).items()):
        survivors = []
        for r in recs:
            key = r.get("key")
            count = r["value"].get("observation_count", 1)
            last_reinforced = reinforced_map.get(key, obs_gen_map.get(key, 0))
            if current_gen - last_reinforced >= cfg.obs_evict_min_age * count:
                dropped += 1
                continue
            survivors.append(r)
            kept += 1
        store["namespaces"][ns_key] = survivors
    obs_path.write_text(json.dumps(store, indent=2))
    return {"obs_dropped": dropped, "obs_kept": kept}


def _synth_cluster(live: list, depleted: bool, obs_gen_map: dict | None, synth_lookback: int | None,
                   incremental: bool) -> bool:
    """NEW-CLUSTERS-ONLY gate: re-synthesize a cluster only if it carries a NEW obs (first-seen
    after the last synth tick). Without this, every cluster in an admitted cell got re-synthesized
    each tick, regenerating SP variants of already-distilled lessons that don't exact-dedup — the
    ~6x/run store bloat. A DEPLETED cell replenishes from its old clusters; non-incremental or no
    gen map => full re-synth."""
    if not live:
        return False
    if not incremental or depleted or obs_gen_map is None or synth_lookback is None:
        return True
    return any(obs_gen_map.get(k, 0) > synth_lookback for k in live)


def _track_record(sp_recs: list, base: float, min_follow: int = 5) -> tuple[str, list[str]]:
    """Render the realized-credit track record for a cell AND return the keys of exactly the SPs
    whose rows it contains (lift known, followed >= min_follow) — the lineage a revised SP joins
    back to via distilled_from."""
    rows = [(sp_lift(r["value"], base), r["value"].get("follow_count", 0), r["value"].get("action", ""),
             r.get("key", "")) for r in sp_recs]
    rows = [row for row in rows if row[0] is not None and row[1] >= min_follow]
    if not rows:
        return "", []
    rows.sort(key=lambda row: (row[0], row[1], row[2]), reverse=True)
    text = "\n".join(f"- realized lift {lf:+.2f} (followed {f}x): {a}" for lf, f, a, _k in rows)
    return text, [k for *_, k in rows]


def synthesize(store_dir: Path, sp_namespaces: dict, base_rates: dict, cfg: TickConfig,
               prev_obs_counts: dict | None = None,
               obs_gen_map: dict | None = None, current_gen: int | None = None) -> tuple[dict, dict]:
    """Credit-aware synthesis for cells with NEW obs since the prev tick (incremental). Appends
    fresh SPs to sp_namespaces. A per-cell CONTESTED-lane cap skips cells whose UNPROVEN SPs
    already fill the quota — proven SPs sit in earned slots outside it (depleted cells exempt).
    Returns ({added, cells_synthed, with_track_record, cells_capped}, current_obs_counts).
    LLM step (model via cfg.env())."""
    # imported lazily so pure prune/evict stays import-light + LLM-free
    from Agents.memory.batch_deduplication.config import BatchDedupRunConfig
    from Agents.memory.persistence import memory_store_paths, seed_memory_from_json_files_cached
    from Agents.memory.store import store
    from Agents.memory.strategy_synthesis import (cluster_observations_for_synth,
                                                   fetch_observations_for_synth, synthesize_cluster_sps)
    from Agents.schemas.roles import VALID_ACTION_PHASES_BY_ROLE, roles as ALL_ROLES

    obs_path, sp_path = memory_store_paths(store_dir)
    seed_memory_from_json_files_cached(observations_path=obs_path, strategy_points_path=sp_path,
                                       target_store=store, cache_dir=store_dir)
    # 0.65 ≡ 0.70 on -001 (below every real obs pair on both scales — the gate deliberately never
    # binds; neighbor ranking + the cluster cap do the selection). Remapped 2026-07-16 for
    # gemini-embedding-2's lower similarity scale.
    cfgd = BatchDedupRunConfig(similarity_threshold=0.65, cluster_mode="bounded", max_cluster_size=15)
    prev = prev_obs_counts or {}
    # "New obs since last synth" must count ARRIVALS (by first-seen tick), NOT the net count change:
    # net change cancels additions against obs DECAY, silently stalling synthesis once decay >=
    # additions. obs_gen_map makes the trigger decay-immune; net change is the fallback.
    synth_lookback = (current_gen - cfg.synth_every_k_gens) if current_gen is not None else None
    obs_counts: dict[str, int] = {}
    cells_capped = 0
    tasks = []
    for role in ALL_ROLES:
        for phase in VALID_ACTION_PHASES_BY_ROLE.get(role, []):
            cell = f"{role}/{phase}"
            # GATE-BEFORE-CLUSTER: fetch keys only, evaluate the admission gates, and cluster ONLY
            # an admitted cell — clustering is the store-size-scaling embedding cost, so a skipped
            # cell must pay ZERO of it.
            items = fetch_observations_for_synth(store, ("observations", role, phase))
            obs_counts[cell] = len(items)
            if obs_gen_map is not None and synth_lookback is not None:
                new_obs = sum(1 for k in items if obs_gen_map.get(k, 0) > synth_lookback)
            else:
                new_obs = obs_counts[cell] - prev.get(cell, 0)   # fallback: net change (no gen map)
            sp_recs = sp_namespaces.get(f"strategy_points/{cell}", [])
            cur_sp_count = len(sp_recs)
            # CONTESTED-lane count: SPs that are NOT proven (same predicate as prune_and_evict's
            # exemption). PROVEN SPs occupy earned slots outside the quota.
            unproven_count = sum(
                1 for r in sp_recs
                if not _is_proven(r["value"], base_for(base_rates, cell, r["value"].get("sp_type")), cfg))
            depleted = cur_sp_count < cfg.synth_replenish_floor  # replenish floor = TOTAL size (lane-agnostic)
            if cfg.incremental and new_obs < cfg.synth_min_new_obs and not depleted:
                continue  # not enough fresh evidence AND the cell isn't depleted → skip (cost guard)
            # HARD per-cell CONTESTED-lane CAP: a cell whose UNPROVEN lane already fills the quota
            # doesn't re-synthesize — a bloat ceiling + cost guard ABOVE the new-obs gate. The cap
            # gates GROWTH, not size: it holds until prune/evict drain the lane below it (culls run
            # every tick, synth only every k). A DEPLETED cell stays exempt so replenish refills it.
            if unproven_count >= cfg.synth_cell_unproven_cap and not depleted:
                cells_capped += 1
                continue
            # SEED FROM NEW ARRIVALS ONLY: an all-old cluster gets discarded by _synth_cluster
            # anyway, so never build one — seed clusters from obs first-seen after the synth tick
            # (old obs still join as neighbours). A DEPLETED cell keeps full seeding.
            seed_keys = ({k for k in items if obs_gen_map.get(k, 0) > synth_lookback}
                         if cfg.incremental and obs_gen_map is not None and synth_lookback is not None
                         and not depleted else None)
            items, clusters = cluster_observations_for_synth(store, ("observations", role, phase), cfgd,
                                                             items=items, seed_keys=seed_keys)
            tr, tr_keys = _track_record(sp_namespaces.get(f"strategy_points/{cell}", []),
                                        base_for(base_rates, cell),
                                        min_follow=cfg.synth_track_min_follow)
            for cl in clusters:
                live = [k for k in cl if k in items]
                if _synth_cluster(live, depleted, obs_gen_map, synth_lookback, cfg.incremental):
                    tasks.append((role, phase, live, items, tr, tr_keys))

    now = datetime.now(timezone.utc)
    added = 0

    def _run(t):
        role, phase, live, items, tr, tr_keys = t
        return role, tr_keys, synthesize_cluster_sps(role, phase, live, items, max_retries=1, track_record=tr)

    if tasks:
        with ThreadPoolExecutor(max_workers=12) as pool:
            for role, tr_keys, sps in pool.map(_run, tasks):
                for sp in sps:
                    ns = f"strategy_points/{role}/{sp.action_phase}"
                    sp_namespaces.setdefault(ns, []).append({
                        "created_at": now.isoformat(), "key": str(uuid.uuid4()),
                        "namespace": ["strategy_points", role, sp.action_phase],
                        "updated_at": now.isoformat(),
                        # distilled_from: keys of the SPs whose track record was fed into synthesis
                        # for this cell — inert lineage metadata (agents never see it).
                        "value": {"observation_count": 1, "last_observed": now.isoformat(), "game_id": "",
                                  "situation": sp.composed_situation, "action": sp.action,
                                  "direction": sp.direction, "honesty": sp.honesty,
                                  # credit class: routes concealment-typed SPs to the concealment
                                  # floor + conceal/<cell> base instead of the endpoint
                                  "sp_type": getattr(sp, "sp_type", "general"),
                                  "follow_count": 0, "retrieved_count": 0, "positive_count": 0,
                                  "neutral_count": 0, "negative_count": 0,
                                  "distilled_from": tr_keys,
                                  "dimensions": sp.model_dump(mode="json")},
                    })
                    added += 1
    # with_track_record = cells synthesized using a realized-credit track record (the credit-AWARE
    # path) — makes the mechanism observable per tick instead of hoped.
    with_tr = len({(r, p) for r, p, _live, _items, tr, _keys in tasks if tr})
    return ({"added": added, "cells_synthed": len({(r, p) for r, p, *_ in tasks}),
             "with_track_record": with_tr, "cells_capped": cells_capped}, obs_counts)


def _dedup_strategy_points(store_dir: Path, model: str) -> dict:
    """SP KEEP/DISCARD dedup (freeze-old) over the just-synthesized store: collapses near-duplicate
    SPs, keeping the credited OLDER survivor (it absorbs the discarded dup's counts/timestamps).
    SPs NEVER MERGE — combining two directives is incoherent. flash-lite is safe here (KEEP/DISCARD
    is schema-enforced, no merge text)."""
    from Agents.memory.batch_deduplication.config import BatchDedupRunConfig
    from Agents.memory.batch_deduplication.orchestration import run_batch_memory_dedup
    report = run_batch_memory_dedup(BatchDedupRunConfig(
        seed_store_dir=store_dir, dump_store_dir=store_dir, model=model,
        incremental=True, apply=True, memory_kinds=["strategy_points"]))
    return {"ran": True, "namespaces": len(getattr(report, "stats", []))}


def consolidate(store_dir: str | Path, cfg: TickConfig, prev_obs_counts: dict | None = None,
                obs_gen_map: dict | None = None, current_gen: int | None = None,
                reinforced_map: dict | None = None) -> dict:
    """Full consolidation pass on a (credited) store dir. Returns stats + obs_counts (for the next
    tick). obs_gen_map/reinforced_map/current_gen enable observation decay BEFORE synthesis, so the
    synthesizer distills only the surviving obs."""
    store_dir = Path(store_dir)
    obs_path, sp_path = memory_store_paths_local(store_dir)
    base_rates = json.loads((store_dir / "base_rates.json").read_text()) \
        if (store_dir / "base_rates.json").exists() else {}

    oe = {}
    if cfg.evict_observations and obs_gen_map is not None and current_gen is not None:
        oe = evict_observations(obs_path, obs_gen_map, current_gen, cfg, reinforced_map)

    # SYNTH -> DEDUP -> PRUNE (prune runs LAST, on the FINAL post-dedup counts): the SP-dedup
    # absorbs a discarded dup's counts into the survivor and can push it across a threshold —
    # pruning before dedup let those strongly-bad SPs escape for a tick and get followed.
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
