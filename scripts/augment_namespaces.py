"""Namespace augmentation runner — deepen thin (role, action_phase) memory cells.

Re-mines already-finished games (from a frozen extraction set) to add memory to
specific namespaces that the whole-game extraction under-produced. TARGETED: you
name the cells; it never sweeps all roles. This is a store-build / generation op
(it writes the store), not an eval — hence it lives in scripts/.

Pipeline, per the project's storage contract:
  1. Seed an InMemoryStore from a base store dir (reusing its indexed_cache.pkl).
  2. For each game in the source set, rebuild the extraction prefix offline and
     run the focused (role, phase) deep pass (augment_agent).
  3. Route the augmented items through the SAME downstream dedup as live
     extraction — so they dedup against the base store (and each other) and land
     in the correct namespace. The dedup kept-vs-discarded split is the signal:
     high kept => the cell was thin on NUMBER (augmentation helps); mostly
     discarded => thin on VARIETY (the source games just lack the diversity, and
     more/different games are the only fix).
  4. Optionally dump the augmented store to a NEW dir (never the base dir).

--measure-only runs 1-3 and reports without dumping (the probe): the base store
files are never touched.

Examples:
  # Probe one thin cell against v5_0, report net-new, write nothing:
  poetry run python scripts/augment_namespaces.py \
      --cells investigator:day_vote --measure-only

  # Augment several cells and write a new store:
  poetry run python scripts/augment_namespaces.py \
      --cells investigator:day_vote healer:night_action wolf:day_vote \
      --base-store-dir memory_stores/v5_0 \
      --output-store-dir memory_stores/v5_0_augmented
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Agents.memory.deduplication import (
    run_downstream_observation_dedup,
    run_downstream_strategy_dedup,
)
from Agents.memory.extraction import (
    AugmentTarget,
    augment_game_over_targets,
    build_role_extraction_prefix,
    extraction_inputs_from_frozen_case,
)
from Agents.memory.persistence import (
    dump_memory_to_json_files,
    memory_store_paths,
    seed_memory_from_json_files_cached,
)
from Agents.memory.store import store
from Agents.schemas import GameStrategyOutput

DEFAULT_SOURCE = "evaluation/frozen_eval_sets/extraction/extraction_v5_0.jsonl"
DEFAULT_BASE_STORE = "memory_stores/v5_0"


def parse_cells(raw: list[str]) -> list[AugmentTarget]:
    targets: list[AugmentTarget] = []
    for token in raw:
        if ":" not in token:
            raise SystemExit(f"--cells expects role:phase tokens, got {token!r}")
        role, phase = token.split(":", 1)
        targets.append(AugmentTarget(role=role.strip(), phase=phase.strip()))
    return targets


def load_source(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"Source extraction set not found: {path}")
    cases: list[dict] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        # The extraction frozen set nests the game data under extraction_case.
        case = rec.get("extraction_case", rec)
        cases.append(case)
    return cases


def namespace_count(store_obj, kind: str, role: str, phase: str) -> int:
    """Enumerate (not semantic-search) a namespace and count its items."""
    namespace = (kind, role, phase)
    total, offset, limit = 0, 0, 100
    while True:
        page = store_obj.search(namespace, query=None, limit=limit, offset=offset)
        if not page:
            return total
        total += len(page)
        offset += limit


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cells", nargs="+", required=True, help="role:phase tokens to augment")
    ap.add_argument("--source", default=DEFAULT_SOURCE, help="frozen extraction set jsonl")
    ap.add_argument("--base-store-dir", default=DEFAULT_BASE_STORE,
                    help="store to seed + dedup against (read-only unless --output-store-dir)")
    ap.add_argument("--output-store-dir", default=None,
                    help="dir to dump the augmented store into (MUST differ from base)")
    ap.add_argument("--measure-only", action="store_true",
                    help="dedup + report net-new, do not dump (the probe)")
    ap.add_argument("--max-games", type=int, default=None, help="cap games for a quick run")
    ap.add_argument("--cache-prefix", action="store_true",
                    help="Vertex-cache each game's prefix (pays off with >1 cell/game)")
    args = ap.parse_args()

    targets = parse_cells(args.cells)
    base_dir = Path(args.base_store_dir)
    if args.output_store_dir and Path(args.output_store_dir).resolve() == base_dir.resolve():
        raise SystemExit("--output-store-dir must differ from --base-store-dir (never overwrite the base)")
    if not args.measure_only and not args.output_store_dir:
        raise SystemExit("Provide --output-store-dir, or pass --measure-only to run without writing")

    cases = load_source(Path(args.source))
    if args.max_games is not None:
        cases = cases[: args.max_games]
    print(f"Loaded {len(cases)} games from {args.source}")
    print(f"Targets: {', '.join(t.label for t in targets)}")

    # --- 1. seed the (empty) global store from the base store, reusing its cache ---
    obs_path, sp_path = memory_store_paths(base_dir)
    print(f"Seeding store from {base_dir} ...")
    seed_info = seed_memory_from_json_files_cached(
        observations_path=obs_path, strategy_points_path=sp_path,
        target_store=store, cache_dir=base_dir,
    )
    print(f"  seeded ({'cache' if seed_info.get('from_cache') else 'api'})")

    before = {
        t.label: {
            "observations": namespace_count(store, "observations", t.role, t.phase),
            "strategy_points": namespace_count(store, "strategy_points", t.role, t.phase),
        }
        for t in targets
    }

    # --- 2. focused re-extraction per game, collected per target ---
    # The 2.5-pro output is the expensive artifact; persist EVERY raw candidate
    # (pre-dedup) so the actual text can be inspected — the downstream dedup is
    # KEEP/DISCARD-only (no merge), so its discard count alone can't tell a true
    # duplicate from a lost-merge. Inspecting candidates vs kept is the real test.
    obs_by_target: dict[str, list] = defaultdict(list)
    sp_by_target: dict[str, list] = defaultdict(list)
    candidates: list[dict] = []
    for i, case in enumerate(cases, 1):
        inputs = extraction_inputs_from_frozen_case(case)
        prefix = build_role_extraction_prefix(inputs)
        outputs = augment_game_over_targets(
            prefix, tuple(targets), cache_prefix=args.cache_prefix,
        )
        produced = sum(len(o.observations) + len(o.strategy_points) for o in outputs.values())
        print(f"  game {i}/{len(cases)} -> {produced} items "
              f"({sum(1 for _ in outputs)}/{len(targets)} cells produced)", flush=True)
        for t in targets:
            out = outputs.get(t)
            if out is None:
                continue
            obs_by_target[t.label].extend(out.observations)
            sp_by_target[t.label].extend(out.strategy_points)
            for kind, items in (("observations", out.observations), ("strategy_points", out.strategy_points)):
                for item in items:
                    candidates.append({
                        "game_index": i, "cell": t.label, "kind": kind,
                        "value": item.model_dump(mode="json"),
                    })

    cand_dir = Path("evidence/memory_system/augmentation")
    cand_dir.mkdir(parents=True, exist_ok=True)
    cand_path = cand_dir / "augment_candidates.jsonl"
    cand_path.write_text("\n".join(json.dumps(c) for c in candidates) + "\n")
    print(f"\nPersisted {len(candidates)} raw candidates to {cand_path}")

    # --- 3. dedup each target's pooled output into the store (against base + self) ---
    report: dict[str, dict] = {}
    for t in targets:
        gid = f"augment_{t.role}_{t.phase}"
        obs = obs_by_target[t.label]
        sps = sp_by_target[t.label]
        print(f"\nDedup {t.label}: {len(obs)} candidate obs, {len(sps)} candidate sp ...")
        obs_stats = run_downstream_observation_dedup(store, obs, gid)
        sp_stats = run_downstream_strategy_dedup(store, sps, gid)
        report[t.label] = {
            "candidates": {"observations": len(obs), "strategy_points": len(sps)},
            "observations": obs_stats.model_dump(mode="json"),
            "strategy_points": sp_stats.model_dump(mode="json"),
            "before": before[t.label],
            "after": {
                "observations": namespace_count(store, "observations", t.role, t.phase),
                "strategy_points": namespace_count(store, "strategy_points", t.role, t.phase),
            },
        }

    # --- 4. optional dump to a NEW dir ---
    if args.output_store_dir:
        out_dir = Path(args.output_store_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_obs, out_sp = memory_store_paths(out_dir)
        dump_memory_to_json_files(
            observations_path=out_obs, strategy_points_path=out_sp, target_store=store,
        )
        print(f"\nDumped augmented store to {out_dir}")

    # --- report ---
    print("\n================ NAMESPACE AUGMENTATION REPORT ================")
    print(f"{'cell':28} {'kind':14} {'cands':>6} {'kept':>5} {'disc':>5} {'repl':>5} "
          f"{'before':>7} {'after':>6}")
    for label, r in report.items():
        for kind in ("observations", "strategy_points"):
            s = r[kind]
            print(f"{label:28} {kind:14} {r['candidates'][kind]:>6} "
                  f"{s['kept']:>5} {s['discarded']:>5} {s['replaced']:>5} "
                  f"{r['before'][kind]:>7} {r['after'][kind]:>6}")

    print("\nInterpretation caveat: the online dedup is KEEP/DISCARD only (no MERGE),"
          " so 'kept' is NOT 'distinct' — a near-dup that should merge into an"
          " existing item is kept as a SEPARATE entry instead. Discards are fine"
          " (true duplicates). The real net-new-variety = kept items that survive a"
          " batch MERGE pass + visual inspection of the candidate text. Run the"
          " batch dedup over the augmented cell (or --output-store-dir then inspect)"
          " before trusting the kept count.")
    if args.measure_only:
        print("\n[measure-only] base store files untouched.")

    # Persist the machine-readable report next to the source for the record.
    report_path = Path("evidence/memory_system/augmentation")
    report_path.mkdir(parents=True, exist_ok=True)
    out_json = report_path / "augment_probe_report.json"
    out_json.write_text(json.dumps(report, indent=2))
    print(f"Report written to {out_json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
