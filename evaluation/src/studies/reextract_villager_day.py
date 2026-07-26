"""Re-extract the villager·day cell into a fresh v6 store (cheap-first slice of the Phase B
dimension build). Reads the frozen v5_0 source games' extraction inputs, re-mines each with the v6
VillagerDayObservation schema (criticality numbers + stakes-as-implication, consensus split, heat,
target landscape) and a scoped villager·day prompt, and writes RAW observations (NO production dedup
— the criticality screen reads retrieval, not dedup; rerank≈raw) into memory_stores/v6_0.

Only villager·day is migrated to the v6 schema; the live extraction path and the other roles are
untouched (see evidence/extraction/situation_dimensions/dimension_schema_build_spec.md §8b). After the criticality screen
shows the lever, the full DAG + live rewiring follow.

  poetry run python evaluation/src/studies/reextract_villager_day.py --limit 2   # smoke
  poetry run python evaluation/src/studies/reextract_villager_day.py             # full 20 games
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

from Agents.llm_factory import get_llm_pro, get_llm_pro_backup
from Agents.memory.extraction import extraction_inputs_from_frozen_case
from Agents.memory.persistence import memory_store_paths
from Agents.prompts import EPISTEMIC_STATUS_RULE, GAME_RULES
from Agents.prompts.extraction import VILLAGER_DAY_EXTRACTION_PROMPT
from Agents.schemas.memory import StoredObservation, VillagerDayExtraction, VillagerDayObservation
from evaluation.src.core.manifest import build_manifest

logger = getLogger(__name__)

DEFAULT_SOURCE = "evaluation/frozen_eval_sets/extraction/extraction_v5_0.jsonl"
DEFAULT_OUTPUT = "memory_stores/v6_0"
SCHEMA_VERSION = "werewolf_observations.v6_villager_day"


def load_cases(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"Source extraction set not found: {path}")
    cases = []
    for line in path.read_text().splitlines():
        if line.strip():
            rec = json.loads(line)
            cases.append(rec.get("extraction_case", rec))
    return cases


def _build_prompt(inputs: dict[str, str]) -> str:
    """Brace-safe substitution (game transcripts can contain literal braces that would break
    str.format): replace each known placeholder token in turn; inserted content is never re-scanned."""
    prompt = VILLAGER_DAY_EXTRACTION_PROMPT
    subs = {
        "{game_rules}": GAME_RULES,
        "{epistemic_status_rule}": EPISTEMIC_STATUS_RULE,
        "{formatted_roles}": inputs["formatted_roles"],
        "{formatted_discussions}": inputs["formatted_discussions"],
        "{formatted_strategy_notes}": inputs["formatted_strategy_notes"],
        "{game_outcome}": inputs["game_outcome"],
    }
    for token, value in subs.items():
        prompt = prompt.replace(token, value)
    return prompt


def _invoke(prompt: str, run_name: str, max_retries: int) -> VillagerDayExtraction | None:
    """Primary (pro) then backup, each with retries; first valid VillagerDayExtraction wins."""
    for label, llm, retries in (
        ("primary", get_llm_pro(), max_retries),
        ("backup", get_llm_pro_backup(), max_retries),
    ):
        chain = llm.with_structured_output(VillagerDayExtraction)
        for attempt in range(retries + 1):
            try:
                result = chain.invoke(prompt, config={"run_name": f"{run_name}_{label}"})
                if isinstance(result, dict):
                    result = VillagerDayExtraction.model_validate(result)
                if isinstance(result, VillagerDayExtraction):
                    return result
            except Exception as e:  # noqa: BLE001 — try the next attempt/model
                logger.warning("%s %s attempt %s failed: %s", run_name, label, attempt + 1, e)
    return None


def extract_one(case: dict, max_retries: int) -> tuple[str, str, list[VillagerDayObservation]]:
    """Re-extract villager day-phase observations for one game. Returns
    (game_id, game_outcome, observations)."""
    game_id = case.get("game_id", "")
    inputs = extraction_inputs_from_frozen_case(case)
    prompt = _build_prompt(inputs)
    result = _invoke(prompt, f"reextract_villager_day_{str(game_id)[:8]}", max_retries)
    if result is None:
        logger.warning("game %s produced no villager·day extraction", game_id)
        return game_id, inputs["game_outcome"], []
    # The schema already pins perspective=villager + day phases; guard defensively anyway.
    obs = [
        o
        for o in result.observations
        if o.perspective == "villager" and o.action_phase in ("day_discussion", "day_vote")
    ]
    return game_id, inputs["game_outcome"], obs


def _stored_value(obs: VillagerDayObservation, game_id: str, winner: str, now: datetime) -> dict:
    """A v6 StoredObservation: composed-embed situation + payload + the criticality numbers the
    conditioned retrieval reads (reranker-only, never embedded)."""
    return StoredObservation(
        observation_count=1,
        last_observed=now,
        game_id=game_id,
        situation=obs.composed_situation,
        approach=obs.approach,
        outcome=obs.outcome,
        net_verdict=obs.net_verdict,
        source_game_winner=winner,
        role_faction_won=(winner == "villagers"),
        players_alive=obs.players_alive,
        distance_to_parity=obs.distance_to_parity,
        is_swing=obs.is_swing,
        consensus_direction=obs.consensus_direction,
    ).model_dump(mode="json")


def build_store_doc(
    games: list[tuple[str, str, list[VillagerDayObservation]]]
) -> tuple[dict, dict[str, int]]:
    now = datetime.now(timezone.utc)
    namespaces: dict[str, list[dict]] = {}
    counts: dict[str, int] = {}
    for game_id, winner, observations in games:
        for o in observations:
            ns_key = f"observations/villager/{o.action_phase}"
            entry = {
                "created_at": now.isoformat(),
                "key": str(uuid.uuid4()),
                "namespace": ["observations", "villager", o.action_phase],
                "updated_at": now.isoformat(),
                "value": _stored_value(o, game_id, winner, now),
            }
            namespaces.setdefault(ns_key, []).append(entry)
            counts[ns_key] = counts.get(ns_key, 0) + 1
    doc = {
        "description": (
            "v6 villager·day cell — RAW re-extraction (no dedup). Situation is the composed embed "
            "string; players_alive/distance_to_parity/is_swing/consensus_direction are reranker-only "
            "criticality fields for conditioned retrieval. Built by reextract_villager_day.py."
        ),
        "namespaces": namespaces,
        "schema_version": SCHEMA_VERSION,
        "updated_at": now.isoformat(),
    }
    return doc, counts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default=DEFAULT_SOURCE)
    ap.add_argument("--output-store-dir", default=DEFAULT_OUTPUT)
    ap.add_argument("--limit", type=int, default=None, help="max games (smoke test)")
    ap.add_argument("--max-retries", type=int, default=2)
    ap.add_argument("--max-workers", type=int, default=6)
    args = ap.parse_args()

    out_dir = Path(args.output_store_dir)
    obs_path, _ = memory_store_paths(out_dir)
    if obs_path.exists():
        raise SystemExit(f"{obs_path} exists — refusing to overwrite. Remove it first.")

    cases = load_cases(Path(args.source))
    if args.limit:
        cases = cases[: args.limit]
    print(f"Re-extracting villager·day from {len(cases)} games -> {out_dir}", flush=True)

    games: list[tuple[str, str, list[VillagerDayObservation]]] = []
    with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        futures = {pool.submit(extract_one, c, args.max_retries): c for c in cases}
        for fut in as_completed(futures):
            game_id, winner, obs = fut.result()
            games.append((game_id, winner, obs))
            print(f"  game {str(game_id)[:8]} ({winner}): {len(obs)} villager·day obs", flush=True)

    doc, counts = build_store_doc(games)
    obs_path.parent.mkdir(parents=True, exist_ok=True)
    obs_path.write_text(json.dumps(doc, indent=2))

    n_obs = sum(counts.values())
    manifest = build_manifest(
        artifact=obs_path,
        config={
            "source": args.source,
            "n_games": len(cases),
            "schema": "VillagerDayObservation",
            "dedup": "none (raw)",
        },
        inputs=[args.source],
        created_from="reextract_villager_day.py",
        case_count=n_obs,
        extra={"namespace_counts": counts},
    )
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    print(f"\nWrote {n_obs} observations to {obs_path}", flush=True)
    for k in sorted(counts):
        print(f"  {k}: {counts[k]}", flush=True)
    games_with_obs = sum(1 for _, _, o in games if o)
    print(f"games with >=1 obs: {games_with_obs}/{len(games)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
