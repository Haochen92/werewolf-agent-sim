"""Generate golden situation queries for expanded eval cases.

Uses the production situation summary pipeline (structured output with
dimensional framework) to generate 1-2 situation descriptions per case.
Outputs a JSON file compatible with retrieve_new_candidates.py.

Usage:
    # Generate for all cases in the expanded dataset
    poetry run python evidence/fine_tuning/cross_encoder/reranker/generate_situations.py

    # Use a different model
    poetry run python evidence/fine_tuning/cross_encoder/reranker/generate_situations.py \
        --model gemini-2.5-pro

    # Generate for a subset
    poetry run python evidence/fine_tuning/cross_encoder/reranker/generate_situations.py \
        --max-cases 10
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from evaluation.core.settings import REPO_ROOT, load_project_env

load_project_env()

EVAL_DATASET = REPO_ROOT / "eval_sets" / "v4_reranker_expanded.jsonl"
OUTPUT_DIR = REPO_ROOT / "evidence" / "fine_tuning" / "cross_encoder" / "reranker"
GOLDEN_LABELS_PATH = (
    REPO_ROOT / "evidence" / "extraction" / "situation_summary"
    / "retrieval_golden_labels.json"
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--eval-dataset", type=Path, default=EVAL_DATASET,
    )
    parser.add_argument(
        "--model", type=str, default="gemini-2.5-pro",
    )
    parser.add_argument(
        "--thinking-level", type=str, default="medium",
    )
    parser.add_argument(
        "--output", type=Path,
        default=OUTPUT_DIR / "expanded_golden_situations.json",
    )
    parser.add_argument(
        "--max-cases", type=int, default=None,
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Skip cases already in output file",
    )
    args = parser.parse_args()

    from evaluation.components.situation_summary import run_situation_summary_variant
    from evaluation.core.config_schema import VariantConfig
    from evaluation.data.datasets import read_eval_dataset

    records = read_eval_dataset(args.eval_dataset)
    print(f"Loaded {len(records)} eval records from {args.eval_dataset.name}")

    with open(GOLDEN_LABELS_PATH) as f:
        existing_golden = json.load(f)
    existing_ids = {c["case_id"] for c in existing_golden["labels"]}
    print(f"Existing golden labels: {len(existing_ids)} cases (will skip)")

    existing_results = {}
    if args.resume and args.output.exists():
        with open(args.output) as f:
            prev = json.load(f)
        for c in prev["cases"]:
            existing_results[c["case_index"]] = c
        print(f"Resuming: {len(existing_results)} cases already generated")

    config = VariantConfig(
        label=f"{args.model}-golden-gen",
        model=args.model,
        temperature=0.0,
        thinking_level=args.thinking_level,
    )

    cases_to_process = []
    for i, record in enumerate(records):
        if record.case_id in existing_ids:
            continue
        cases_to_process.append((i, record))

    if args.max_cases:
        cases_to_process = cases_to_process[:args.max_cases]

    print(f"Generating situations for {len(cases_to_process)} new cases")
    print(f"Model: {args.model}, thinking: {args.thinking_level}")
    print(flush=True)

    results = list(existing_results.values())
    done_indices = set(existing_results.keys())
    failed = []
    total_time = 0

    for idx, record in cases_to_process:
        if idx in done_indices:
            continue

        case = record.eval_case
        role = case.player_role
        phase = case.action_phase
        print(f"  Case {idx:3d} ({role:>13} {phase})...", end=" ", flush=True)

        start = time.time()
        try:
            gen_result = run_situation_summary_variant(case, config, max_retries=2)
        except Exception as e:
            elapsed = time.time() - start
            print(f"FAILED ({elapsed:.1f}s): {e}")
            failed.append({"case_index": idx, "error": str(e)})
            continue
        elapsed = time.time() - start
        total_time += elapsed

        situations = gen_result["situations"]
        print(f"{len(situations)} situations ({elapsed:.1f}s)")

        results.append({
            "case_index": idx,
            "case_id": record.case_id,
            "player_role": role,
            "day": case.day,
            "round": case.round,
            "action_phase": phase,
            "golden_situations": situations,
            "model": args.model,
        })

        if len(results) % 10 == 0:
            _save(args.output, results, args.model, failed)

    _save(args.output, results, args.model, failed)

    print(f"\n{'='*60}")
    print(f"Generated situations for {len(results)} cases in {total_time:.0f}s")
    if failed:
        print(f"Failed: {len(failed)} cases")
    avg_sits = sum(len(c["golden_situations"]) for c in results) / max(len(results), 1)
    print(f"Average situations per case: {avg_sits:.1f}")
    print(f"Wrote: {args.output}")


def _save(output_path: Path, results: list, model: str, failed: list):
    output = {
        "description": f"Generated golden situations for expanded eval dataset",
        "model": model,
        "cases": sorted(results, key=lambda c: c["case_index"]),
    }
    if failed:
        output["failed"] = failed
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
        f.write("\n")


if __name__ == "__main__":
    main()
