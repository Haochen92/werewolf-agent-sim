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
from Agents.memory.extraction.inputs import build_cell_extraction_prompt
from Agents.memory.persistence import memory_store_paths
from Agents.memory.validators import coerce_consensus_direction
from Agents.schemas.memory import StoredObservation, cell_observation_schema_for
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

# (group label, prompt phase wording, representative action_phase for the schema lookup)
DAY_GROUP = ("day", "day (public discussion and the elimination vote)", "day_vote")
NIGHT_GROUP = ("night", "night (the secret night action)", "night_action")
ROLE_UNITS: dict[str, list[tuple[str, str, str]]] = {
    "villager": [DAY_GROUP],
    "healer": [DAY_GROUP, NIGHT_GROUP],
    "investigator": [DAY_GROUP, NIGHT_GROUP],
    "vigilante": [DAY_GROUP, NIGHT_GROUP],
    "wolf": [DAY_GROUP, NIGHT_GROUP],
    "serial_killer": [DAY_GROUP, NIGHT_GROUP],
}


def _build_prompt(inputs: dict[str, str], role: str, phase_wording: str, rep_phase: str,
                  cell_schema: type[BaseModel]) -> str:
    """Compose the prefix/tail cell-extraction prompt = cached role/phase-neutral prefix + per-cell
    observation tail (the live build_role_extraction_prompt convention). phase_wording is the human
    {phase} display; rep_phase drives the driver/menu guidance lookup."""
    return build_cell_extraction_prompt(inputs, role, phase_wording, rep_phase, cell_schema)


def _container_for(cell_schema: type[BaseModel]) -> type[BaseModel]:
    return create_model(
        f"{cell_schema.__name__}Extraction",
        __base__=BaseModel,
        observations=(list[cell_schema], Field(description=f"{cell_schema.__name__} observations")),
    )


def extract_cell(case: dict, role: str, unit: tuple[str, str, str], max_retries: int):
    """Re-extract one (game, role, phase-group). Returns list of observation objects (action_phase
    set by the model within the cell's allowed phases)."""
    _, phase_wording, rep_phase = unit
    cell_schema = cell_observation_schema_for(role, rep_phase)
    if cell_schema is None:
        return []
    container = _container_for(cell_schema)
    prompt = _build_prompt(
        extraction_inputs_from_frozen_case(case), role, phase_wording, rep_phase, cell_schema
    )
    run = f"reextract_{role}_{unit[0]}_{str(case.get('game_id',''))[:8]}"
    for label, llm in (("primary", get_llm_pro()), ("backup", get_llm_pro_backup())):
        chain = llm.with_structured_output(container)
        for attempt in range(max_retries + 1):
            try:
                res = chain.invoke(prompt, config={"run_name": f"{run}_{label}"})
                if isinstance(res, dict):
                    res = container.model_validate(res)
                return list(res.observations)
            except Exception as e:  # noqa: BLE001
                logger.warning("%s %s attempt %s failed: %s", run, label, attempt + 1, e)
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default=DEFAULT_SOURCE)
    ap.add_argument("--output-store-dir", default=DEFAULT_OUTPUT)
    ap.add_argument("--roles", nargs="+", default=ALL_ROLES)
    ap.add_argument("--append", action="store_true", help="merge into an existing store (keep prior roles)")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--max-retries", type=int, default=2)
    ap.add_argument("--max-workers", type=int, default=8)
    args = ap.parse_args()

    out_dir = Path(args.output_store_dir)
    obs_path, _ = memory_store_paths(out_dir)
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

    def faction_won(role: str, gid: str) -> bool | None:
        w = winners.get(gid)
        return (_FACTION[role] == w) if w else None

    counts: dict[str, int] = {}
    with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        futs = {pool.submit(extract_cell, c, role, unit, args.max_retries): (c, role, unit)
                for c, role, unit in units}
        for fut in as_completed(futs):
            c, role, unit = futs[fut]
            gid = c.get("game_id", "")
            obs_list = fut.result()
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
                    ).model_dump(mode="json"),
                }
                namespaces.setdefault(ns_key, []).append(entry)
                counts[ns_key] = counts.get(ns_key, 0) + 1
            print(f"  {role}/{unit[0]} game {str(gid)[:8]}: {len(obs_list)} obs", flush=True)

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
