"""Merge multi-model dedup labels and compute agreement.

Aligns outputs from 3 model runs by case_index, normalizes decisions,
and splits into agreed (clean labels) vs disagreed (needs manual review).

Usage:
    poetry run python evidence/fine_tuning/dedup_classifier/merge_agreement.py \
        --inputs cases_flash35.jsonl cases_flashlite.jsonl cases_flash25.jsonl \
        --output-agreed agreed_labels.jsonl \
        --output-disagreed disagreed_labels.jsonl
"""

from __future__ import annotations

import argparse
import json
import logging
from collections import Counter
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

DECISION_NORMALIZATION = {
    "D": "D",
    "K": "K",
    "DISCARD": "D",
    "KEEP": "K",
    "discard": "D",
    "keep": "K",
}


def normalize_decision(raw: str) -> str:
    return DECISION_NORMALIZATION.get(raw, raw)


def load_cases(path: Path) -> dict[int, dict]:
    cases = {}
    with open(path) as f:
        for line in f:
            record = json.loads(line)
            record["decision"] = normalize_decision(record["decision"])
            cases[record["case_index"]] = record
    return cases


def main():
    parser = argparse.ArgumentParser(
        description="Merge multi-model dedup labels by agreement",
    )
    parser.add_argument(
        "--inputs",
        type=Path,
        nargs="+",
        required=True,
        help="Model output JSONL files to merge",
    )
    parser.add_argument(
        "--output-agreed",
        type=Path,
        required=True,
        help="Output JSONL for cases where all models agree",
    )
    parser.add_argument(
        "--output-disagreed",
        type=Path,
        required=True,
        help="Output JSONL for cases where models disagree (needs manual review)",
    )
    args = parser.parse_args()

    model_outputs = []
    model_names = []
    for path in args.inputs:
        cases = load_cases(path)
        model_outputs.append(cases)
        # Infer model name from first record
        first = next(iter(cases.values()))
        model_names.append(first.get("dedup_model", path.stem))
        logger.info(f"Loaded {len(cases)} cases from {path} (model: {model_names[-1]})")

    all_indices = sorted(
        set().union(*(cases.keys() for cases in model_outputs))
    )
    logger.info(f"Total unique case indices: {len(all_indices)}")

    stats = Counter()
    agreed = []
    disagreed = []

    for idx in all_indices:
        records = [cases.get(idx) for cases in model_outputs]

        if any(r is None for r in records):
            stats["missing_in_some_models"] += 1
            continue

        is_auto = records[0]["auto"]
        if is_auto:
            stats["auto_skip"] += 1
            continue

        decisions = [r["decision"] for r in records]
        unique_decisions = set(decisions)

        base_record = {
            "case_index": idx,
            "item_type": records[0]["item_type"],
            "perspective": records[0]["perspective"],
            "action_phase": records[0]["action_phase"],
            "game_id": records[0]["game_id"],
            "new_entry": records[0]["new_entry"],
            "candidates": records[0]["candidates"],
            "similarity_scores": records[0]["similarity_scores"],
            "model_decisions": {
                name: {
                    "decision": r["decision"],
                    "reasoning": (r.get("decision_detail") or {}).get("reasoning"),
                }
                for name, r in zip(model_names, records)
            },
        }

        if len(unique_decisions) == 1:
            base_record["label"] = decisions[0]
            base_record["agreement"] = "unanimous"
            agreed.append(base_record)
            stats[f"agreed_{decisions[0]}"] += 1
        else:
            majority = Counter(decisions).most_common(1)[0]
            base_record["majority_label"] = majority[0]
            base_record["majority_count"] = majority[1]
            base_record["agreement"] = "disagreed"
            disagreed.append(base_record)
            stats["disagreed"] += 1
            vote_pattern = "/".join(decisions)
            stats[f"pattern_{vote_pattern}"] += 1

    args.output_agreed.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_agreed, "w") as f:
        for record in agreed:
            f.write(json.dumps(record) + "\n")

    with open(args.output_disagreed, "w") as f:
        for record in disagreed:
            f.write(json.dumps(record) + "\n")

    total_llm = stats["agreed_D"] + stats["agreed_K"] + stats["disagreed"]
    agreement_rate = (
        (stats["agreed_D"] + stats["agreed_K"]) / total_llm * 100
        if total_llm > 0
        else 0
    )

    logger.info(f"")
    logger.info(f"=== Results ===")
    logger.info(f"Auto decisions (skipped):  {stats['auto_skip']}")
    logger.info(f"LLM-decided cases:         {total_llm}")
    logger.info(f"  Agreed D (unanimous):    {stats['agreed_D']}")
    logger.info(f"  Agreed K (unanimous):    {stats['agreed_K']}")
    logger.info(f"  Disagreed:               {stats['disagreed']}")
    logger.info(f"  Agreement rate:          {agreement_rate:.1f}%")
    logger.info(f"")
    logger.info(f"Wrote {len(agreed)} agreed cases to {args.output_agreed}")
    logger.info(f"Wrote {len(disagreed)} disagreed cases to {args.output_disagreed}")

    if stats["disagreed"] > 0:
        logger.info(f"")
        logger.info(f"Disagreement patterns:")
        for key, count in sorted(stats.items()):
            if key.startswith("pattern_"):
                logger.info(f"  {key.replace('pattern_', '')}: {count}")


if __name__ == "__main__":
    main()
