"""Generate dedup training cases from extraction artifacts.

Loads extracted observations/strategy_points from model comparison JSONL files,
seeds an in-memory store from a specified store directory, then runs each
extraction through the per-extraction dedup pipeline. Captures the full
input context (new entry + candidates + similarity scores) and model decision
into a JSONL dataset — no Langfuse dependency.

Usage:
    # Single model run:
    poetry run python evidence/fine_tuning/dedup_classifier/generate_dedup_cases.py \
        --store-dir Agents/memory_stores/v4_deduped_v2 \
        --extraction-files evidence/extraction/quality/model_comparison/gemini-3.5-flash_*.jsonl \
        --output evidence/fine_tuning/dedup_classifier/cases_flash35.jsonl \
        --model gemini-3.5-flash

    # Run 3 models in parallel for multi-model agreement labeling:
    poetry run python evidence/fine_tuning/dedup_classifier/generate_dedup_cases.py \
        --store-dir Agents/memory_stores/v4_deduped_v2 \
        --extraction-files evidence/extraction/quality/model_comparison/gemini-3.5-flash_*.jsonl \
        --output evidence/fine_tuning/dedup_classifier/cases_flash35.jsonl \
        --model gemini-3.5-flash &

    poetry run python evidence/fine_tuning/dedup_classifier/generate_dedup_cases.py \
        --store-dir Agents/memory_stores/v4_deduped_v2 \
        --extraction-files evidence/extraction/quality/model_comparison/gemini-3.5-flash_*.jsonl \
        --output evidence/fine_tuning/dedup_classifier/cases_flashlite.jsonl \
        --model gemini-3.1-flash-lite --thinking-level low &

    poetry run python evidence/fine_tuning/dedup_classifier/generate_dedup_cases.py \
        --store-dir Agents/memory_stores/v4_deduped_v2 \
        --extraction-files evidence/extraction/quality/model_comparison/gemini-3.5-flash_*.jsonl \
        --output evidence/fine_tuning/dedup_classifier/cases_flash25.jsonl \
        --model gemini-2.5-flash &
"""

from __future__ import annotations

import argparse
import json
import logging
import uuid
from collections import Counter
from pathlib import Path

from langgraph.store.memory import InMemoryStore

import Agents.memory_deduplication as dedup_module
from Agents.llm_factory import create_embeddings
from Agents.memory_deduplication import (
    DEDUP_SIMILARITY_THRESHOLD,
    DEDUP_TOP_N,
    _call_dedup_llm,
    _call_observation_dedup_llm,
    _embedding_prefilter_observation,
    _embedding_prefilter_strategy_point,
    _serialize_candidates,
)
from Agents.memory_persistence import seed_memory_from_config
from Agents.schemas.memory import Observation, StrategyPoint

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _dedup_without_store_mutation(
    store,
    entry,
    item_type: str,
) -> dict | None:
    """Run dedup classification without modifying the store.

    Mirrors dedup_single_observation / dedup_single_strategy_point but skips
    all store writes (_store_new_*, _update_auto_*, _apply_*_decision).
    Returns a dict with full context for the training dataset, or None on
    LLM failure.
    """
    if item_type == "observation":
        namespace = ("observations", entry.perspective, entry.action_phase)
        new_entry_dict = {
            "situation": entry.composed_situation,
            "approach": entry.approach,
            "outcome": entry.outcome,
        }
    else:
        namespace = ("strategy_points", entry.perspective, entry.action_phase)
        new_entry_dict = {
            "situation": entry.composed_situation,
            "action": entry.action,
        }

    all_similar = store.search(
        namespace,
        query=entry.composed_situation,
        limit=DEDUP_TOP_N,
    )

    candidates = _serialize_candidates(all_similar) if all_similar else []
    similar = [
        item
        for item in all_similar
        if item.score and item.score >= DEDUP_SIMILARITY_THRESHOLD
    ]

    if not similar:
        return {
            "item_type": item_type,
            "perspective": entry.perspective,
            "action_phase": entry.action_phase,
            "new_entry": new_entry_dict,
            "candidates": candidates,
            "decision": "K",
            "decision_detail": None,
            "auto": True,
            "auto_reason": "no_similar",
            "similarity_scores": None,
        }

    if item_type == "observation":
        prefilter_decision, sim_scores = _embedding_prefilter_observation(
            entry, similar,
        )
    else:
        prefilter_decision, sim_scores = _embedding_prefilter_strategy_point(
            entry, similar,
        )

    if prefilter_decision in ("discard", "keep"):
        return {
            "item_type": item_type,
            "perspective": entry.perspective,
            "action_phase": entry.action_phase,
            "new_entry": new_entry_dict,
            "candidates": _serialize_candidates(similar),
            "decision": "D" if prefilter_decision == "discard" else "K",
            "decision_detail": None,
            "auto": True,
            "auto_reason": f"embedding_{prefilter_decision}",
            "similarity_scores": sim_scores,
        }

    # LLM decision required
    if item_type == "observation":
        decision = _call_observation_dedup_llm(entry, similar)
    else:
        decision = _call_dedup_llm(entry, similar)

    if decision is None:
        return None

    return {
        "item_type": item_type,
        "perspective": entry.perspective,
        "action_phase": entry.action_phase,
        "new_entry": new_entry_dict,
        "candidates": _serialize_candidates(similar),
        "decision": decision.decision,
        "decision_detail": decision.model_dump(mode="json"),
        "auto": False,
        "auto_reason": None,
        "similarity_scores": sim_scores,
    }


def load_extractions(
    paths: list[Path],
    item_types: list[str],
    max_games_per_file: int | None,
) -> list[tuple[str, str, Observation | StrategyPoint]]:
    """Load extraction artifacts and construct schema objects.

    Returns list of (game_id, item_type, entry) tuples.
    """
    entries = []
    for path in paths:
        logger.info(f"Loading {path}")
        games = []
        with open(path) as f:
            for line in f:
                games.append(json.loads(line))
        if max_games_per_file and len(games) > max_games_per_file:
            games = games[:max_games_per_file]

        for game in games:
            game_id = game.get("game_id", str(uuid.uuid4()))

            if "observations" in item_types:
                for obs_data in game.get("observations", []):
                    try:
                        obs = Observation(**obs_data)
                        entries.append((game_id, "observation", obs))
                    except Exception as e:
                        logger.warning(f"Skipping invalid observation: {e}")

            if "strategy_points" in item_types:
                for sp_data in game.get("strategy_points", []):
                    try:
                        sp = StrategyPoint(**sp_data)
                        entries.append((game_id, "strategy_point", sp))
                    except Exception as e:
                        logger.warning(f"Skipping invalid strategy point: {e}")

    return entries


def main():
    parser = argparse.ArgumentParser(
        description="Generate dedup training cases from extraction artifacts",
    )
    parser.add_argument(
        "--store-dir",
        type=Path,
        required=True,
        help="Memory store directory to seed from (e.g. Agents/memory_stores/v4_deduped_v2)",
    )
    parser.add_argument(
        "--extraction-files",
        type=Path,
        nargs="+",
        required=True,
        help="Extraction JSONL files from model comparison",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output JSONL path for generated dedup cases",
    )
    parser.add_argument(
        "--item-types",
        nargs="+",
        default=["observations", "strategy_points"],
        choices=["observations", "strategy_points"],
        help="Which item types to process (default: both)",
    )
    parser.add_argument(
        "--max-games-per-file",
        type=int,
        default=None,
        help="Limit games loaded per extraction file",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override dedup LLM model (default: module default gemini-3.1-flash-lite)",
    )
    parser.add_argument(
        "--thinking-level",
        type=str,
        default=None,
        help="Override thinking level for the dedup model",
    )
    args = parser.parse_args()

    if args.model:
        logger.info(f"Overriding dedup model: {args.model}")
        dedup_module.DEDUP_MODEL = args.model
    if args.thinking_level is not None:
        logger.info(f"Overriding thinking level: {args.thinking_level}")
        dedup_module.DEDUP_THINKING_LEVEL = args.thinking_level

    # Create a fresh store (not the global singleton)
    logger.info(f"Seeding fresh store from {args.store_dir}")
    embeddings = create_embeddings("gemini-embedding-001", output_dimensionality=1536)
    fresh_store = InMemoryStore(
        index={"dims": 1536, "embed": embeddings, "fields": ["situation"]},
    )
    seed_result = seed_memory_from_config(
        {"seed_store_dir": str(args.store_dir), "dump_enabled": False},
        target_store=fresh_store,
    )
    logger.info(
        f"Store seeded: {seed_result['observations']} observations, "
        f"{seed_result['strategy_points']} strategy points"
    )

    entries = load_extractions(
        args.extraction_files, args.item_types, args.max_games_per_file,
    )
    logger.info(f"Loaded {len(entries)} entries to process")

    stats = Counter()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    with open(args.output, "w") as out:
        for i, (game_id, item_type, entry) in enumerate(entries, 1):
            logger.info(
                f"[{i}/{len(entries)}] {item_type} "
                f"{entry.perspective}/{entry.action_phase}"
            )

            result = _dedup_without_store_mutation(fresh_store, entry, item_type)

            if result is None:
                stats["failed"] += 1
                continue

            result["game_id"] = game_id
            result["case_index"] = i - 1
            result["dedup_model"] = args.model or dedup_module.DEDUP_MODEL
            out.write(json.dumps(result) + "\n")

            decision = result["decision"]
            auto = result["auto"]
            stats[f"{decision}_auto" if auto else f"{decision}_llm"] += 1
            stats["total"] += 1

    logger.info(f"Done. Wrote {stats['total']} cases to {args.output}")
    logger.info(f"Stats: {dict(stats)}")


if __name__ == "__main__":
    main()
