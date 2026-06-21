"""Full-DAG v6 re-extraction (step 4B): re-mine the frozen source games into the v6 cell schema for
ANY role×phase, generalizing reextract_villager_day.py. One LLM call per (game, role, phase-group):
the day call covers day_discussion+day_vote (the merged day cell tags each obs), the night call covers
night_action. Writes RAW observations (no dedup) routed to observations/<role>/<action_phase>.

HELD-OUT DISCIPLINE: extracts ONLY from --source (the 20 extraction_v5_0 games), so any game NOT in
that set stays a clean held-out test game; every screen additionally enforces same-game exclusion.

  poetry run python evaluation/src/experiments/reextract_cells.py \
      --roles healer investigator vigilante wolf serial_killer --append   # add to villager v6_0
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from logging import getLogger
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from pydantic import BaseModel, Field, create_model

from Agents.llm_factory import get_llm_pro, get_llm_pro_backup
from Agents.memory.extraction import extraction_inputs_from_frozen_case
from Agents.memory.extraction.cell_units import ROLE_UNITS
from Agents.memory.extraction.inputs import build_cell_extraction_prompt
from Agents.memory.persistence import memory_store_paths
from Agents.memory.validators import coerce_consensus_direction
from Agents.schemas.memory import (
    StoredObservation,
    StoredStrategyPoint,
    cell_dual_extraction_schema,
    cell_observation_schema_for,
    cell_observations_extraction_schema,
)
from evaluation.src.core.manifest import build_manifest
from evaluation.src.experiments.reextract_villager_day import DEFAULT_SOURCE, SCHEMA_VERSION, load_cases

logger = getLogger(__name__)

DEFAULT_OUTPUT = "memory_stores/v6_0"
ALL_ROLES = ["villager", "healer", "investigator", "vigilante", "wolf", "serial_killer"]
_FACTION = {
    "wolf": "wolves", "serial_killer": "serial_killer",
    "villager": "villagers", "healer": "villagers",
    "investigator": "villagers", "vigilante": "villagers",
}

# Cell fan-out plan now lives in Agents/ (shared with the live extractor); imported above.


def extract_cell(case: dict, role: str, unit: tuple[str, str, str], max_retries: int,
                 with_sp: bool = False, anchor: str = "", amplify: bool = False):
    """Re-extract one (game, role, phase-group). Returns (observations, strategy_points) — the SP list
    is empty unless with_sp (the per_run dual path). action_phase is set by the model within the cell's
    allowed phases. `anchor` injects the recall-arm pivotal-turn recommendation; `amplify` swaps the
    bounded ask for an exhaustive deep single-slice pass (namespace-amplification on the cell path)."""
    _, phase_wording, rep_phase = unit
    cell_schema = cell_observation_schema_for(role, rep_phase)
    if cell_schema is None:
        return [], []
    container = (
        cell_dual_extraction_schema(role, rep_phase) if with_sp
        else cell_observations_extraction_schema(role, rep_phase)
    )
    prompt = build_cell_extraction_prompt(
        extraction_inputs_from_frozen_case(case), role, phase_wording, rep_phase, cell_schema,
        with_sp=with_sp, anchor=anchor, amplify=amplify,
    )
    run = f"reextract_{role}_{unit[0]}_{str(case.get('game_id',''))[:8]}"
    for label, llm in (("primary", get_llm_pro()), ("backup", get_llm_pro_backup())):
        chain = llm.with_structured_output(container)
        for attempt in range(max_retries + 1):
            try:
                res = chain.invoke(prompt, config={"run_name": f"{run}_{label}"})
                if isinstance(res, dict):
                    res = container.model_validate(res)
                return list(res.observations), list(getattr(res, "strategy_points", []))
            except Exception as e:  # noqa: BLE001
                logger.warning("%s %s attempt %s failed: %s", run, label, attempt + 1, e)
    return [], []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default=DEFAULT_SOURCE)
    ap.add_argument("--output-store-dir", default=DEFAULT_OUTPUT)
    ap.add_argument("--roles", nargs="+", default=ALL_ROLES)
    ap.add_argument("--append", action="store_true", help="merge into an existing store (keep prior roles)")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--max-retries", type=int, default=2)
    ap.add_argument("--max-workers", type=int, default=8)
    ap.add_argument("--with-sp", action="store_true",
                    help="per_run dual extraction: also derive strategy points into the SP store")
    ap.add_argument("--anchors-from", default=None,
                    help="glob of finished-game records (ab_*.jsonl) to derive recall-arm pivotal-turn "
                         "anchors from, joined to --source by game_id (suggestive, not a quota)")
    ap.add_argument("--amplify", action="store_true",
                    help="recall-arm: exhaustive deep per-cell pass (drop the bounded item count) to test "
                         "whether amplified cheap-model extraction matches a bounded pro pass")
    args = ap.parse_args()

    # recall-arm: deterministic pivotal-turn flags keyed by game_id (empty if --anchors-from unset)
    anchors_by_gid: dict[str, list] = {}
    if args.anchors_from:
        import glob as _glob

        from evaluation.src.experiments.recall_flags import pivotal_turns
        for rf in sorted(_glob.glob(args.anchors_from)):
            for line in open(rf):
                if not line.strip():
                    continue
                rec = json.loads(line)
                gid = str(rec.get("game_id", ""))
                if gid and gid not in anchors_by_gid and rec.get("day_resolutions"):
                    anchors_by_gid[gid] = pivotal_turns(rec)
        print(f"  recall-arm anchors loaded for {len(anchors_by_gid)} games", flush=True)

    out_dir = Path(args.output_store_dir)
    obs_path, sp_path = memory_store_paths(out_dir)
    if obs_path.exists() and not args.append:
        raise SystemExit(f"{obs_path} exists — pass --append to add roles, or remove it first.")

    cases = load_cases(Path(args.source))
    if args.limit:
        cases = cases[: args.limit]
    winners = {c.get("game_id"): c.get("game_outcome", "unknown") for c in cases}
    units = [(c, role, unit) for c in cases for role in args.roles for unit in ROLE_UNITS[role]]
    print(f"Re-extracting {len(args.roles)} roles over {len(cases)} games "
          f"= {len(units)} cell-calls -> {out_dir}", flush=True)

    now = datetime.now(timezone.utc)
    namespaces: dict[str, list[dict]] = {}
    if args.append and obs_path.exists():
        namespaces = json.loads(obs_path.read_text()).get("namespaces", {})
        print(f"  appending to existing store ({sum(len(v) for v in namespaces.values())} entries, "
              f"{len(namespaces)} namespaces)", flush=True)
    sp_namespaces: dict[str, list[dict]] = {}
    if args.with_sp and args.append and sp_path.exists():
        sp_namespaces = json.loads(sp_path.read_text()).get("namespaces", {})

    def faction_won(role: str, gid: str) -> bool | None:
        w = winners.get(gid)
        return (_FACTION[role] == w) if w else None

    counts: dict[str, int] = {}
    sp_counts: dict[str, int] = {}
    from evaluation.src.experiments.recall_flags import UNIT_PHASES, anchor_text

    def _anchor(case: dict, unit: tuple) -> str:
        turns = anchors_by_gid.get(str(case.get("game_id", "")))
        return anchor_text(turns, UNIT_PHASES.get(unit[0], ())) if turns else ""

    with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        futs = {pool.submit(extract_cell, c, role, unit, args.max_retries, args.with_sp,
                            _anchor(c, unit), args.amplify): (c, role, unit)
                for c, role, unit in units}
        for fut in as_completed(futs):
            c, role, unit = futs[fut]
            gid = c.get("game_id", "")
            obs_list, sp_list = fut.result()
            for sp in sp_list:
                sp_ns = f"strategy_points/{role}/{sp.action_phase}"
                sp_namespaces.setdefault(sp_ns, []).append({
                    "created_at": now.isoformat(), "key": str(uuid.uuid4()),
                    "namespace": ["strategy_points", role, sp.action_phase],
                    "updated_at": now.isoformat(),
                    "value": StoredStrategyPoint(
                        observation_count=1, last_observed=now, game_id=gid,
                        situation=sp.composed_situation, action=sp.action,
                        direction=sp.direction, honesty=sp.honesty,
                        dimensions=sp.model_dump(mode="json"),
                    ).model_dump(mode="json"),
                })
                sp_counts[sp_ns] = sp_counts.get(sp_ns, 0) + 1
            for o in obs_list:
                ns_key = f"observations/{role}/{o.action_phase}"
                entry = {
                    "created_at": now.isoformat(), "key": str(uuid.uuid4()),
                    "namespace": ["observations", role, o.action_phase],
                    "updated_at": now.isoformat(),
                    "value": StoredObservation(
                        observation_count=1, last_observed=now, game_id=gid,
                        situation=o.composed_situation, approach=o.approach, outcome=o.outcome,
                        net_verdict=o.net_verdict, source_game_winner=winners.get(gid),
                        role_faction_won=faction_won(role, gid),
                        players_alive=o.players_alive, distance_to_parity=o.distance_to_parity,
                        is_swing=o.is_swing,
                        consensus_direction=coerce_consensus_direction(
                            o.composed_situation, getattr(o, "consensus_direction", None)
                        ),
                        info_landscape_class=getattr(o, "info_landscape_class", None),
                        exposure_class=getattr(o, "exposure_class", None),
                        dimensions=o.model_dump(mode="json"),
                    ).model_dump(mode="json"),
                }
                namespaces.setdefault(ns_key, []).append(entry)
                counts[ns_key] = counts.get(ns_key, 0) + 1
            sp_note = f" + {len(sp_list)} sp" if args.with_sp else ""
            print(f"  {role}/{unit[0]} game {str(gid)[:8]}: {len(obs_list)} obs{sp_note}", flush=True)

    doc = {
        "description": "v6 full-DAG RAW re-extraction (no dedup). Composed-embed situation + "
                       "reranker-only criticality fields. Built by reextract_cells.py.",
        "namespaces": namespaces, "schema_version": SCHEMA_VERSION, "updated_at": now.isoformat(),
    }
    obs_path.parent.mkdir(parents=True, exist_ok=True)
    obs_path.write_text(json.dumps(doc, indent=2))
    total = sum(len(v) for v in namespaces.values())
    manifest = build_manifest(
        artifact=obs_path,
        config={"source": args.source, "roles": args.roles, "append": args.append,
                "schema": "v6 cell DAG", "dedup": "none (raw)",
                "held_out_note": "store built ONLY from --source games; any other game is held-out"},
        inputs=[args.source], created_from="reextract_cells.py", case_count=total,
        extra={"namespace_counts": {k: len(v) for k, v in sorted(namespaces.items())}},
    )
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"\nStore now has {total} observations across {len(namespaces)} namespaces:", flush=True)
    for k in sorted(namespaces):
        print(f"  {k}: {len(namespaces[k])}", flush=True)

    if args.with_sp:
        sp_total = sum(len(v) for v in sp_namespaces.values())
        sp_path.write_text(json.dumps({
            "description": "v6 per_run strategy points (RAW, no dedup). Derived per game alongside the "
                           "observations (dual extraction). Built by reextract_cells.py --with-sp.",
            "namespaces": sp_namespaces, "schema_version": SCHEMA_VERSION, "updated_at": now.isoformat(),
        }, indent=2))
        print(f"\nSP store now has {sp_total} strategy points across {len(sp_namespaces)} namespaces:", flush=True)
        for k in sorted(sp_namespaces):
            print(f"  {k}: {len(sp_namespaces[k])}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
