"""Evaluate merge/rewrite quality from batch dedup eval results.

Reads a batch dedup eval result JSON (produced by batch_dedup_eval.py),
extracts MERGE and DISCARD-with-rewrite operations, and uses an LLM judge
to score the merged text quality.

Usage::

    poetry run python -m evaluation.experiments.batch_dedup_merge_eval \
        --result evidence/batch_dedup_golden_eval/eval_gemini_3.5_flash_20260526_132829.json \
        --source eval_sets/batch_dedup_clusters_v4.json \
        --judge-model gemini-2.5-pro
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from evaluation.core.settings import REPO_ROOT, load_project_env
from evaluation.judges.batch_dedup import run_batch_merge_judge

load_project_env()


def _has_merged_text(operation: dict) -> bool:
    return any(
        operation.get(f)
        for f in (
            "merged_situation",
            "merged_approach",
            "merged_outcome",
            "merged_action",
        )
    )


def _extract_merge_cases(
    eval_data: dict,
    clusters: list[dict],
) -> list[dict[str, Any]]:
    """Extract operations with merged text, paired with source entries."""
    cases: list[dict[str, Any]] = []

    for result in eval_data["results"]:
        if "error" in result:
            continue
        cid = result["cluster_id"]
        cluster = clusters[cid]
        items_by_key = {item["key"]: item for item in cluster["items"]}
        ns = cluster["namespace"]
        role = ns[1] if isinstance(ns, list) else ns.split("/")[1]
        action_phase = ns[2] if isinstance(ns, list) else ns.split("/")[2]

        for op in result.get("model_operations", []):
            if not _has_merged_text(op):
                continue

            source_items = [
                items_by_key[k]
                for k in op["source_keys"]
                if k in items_by_key
            ]
            if not source_items:
                continue

            cases.append({
                "cluster_id": cid,
                "kind": cluster["kind"],
                "role": role,
                "action_phase": action_phase,
                "action": op["action"],
                "source_keys": op["source_keys"],
                "source_items": source_items,
                "operation": op,
            })

    return cases


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Judge merge/rewrite quality from batch dedup results",
    )
    parser.add_argument("--result", type=Path, required=True,
                        help="Eval result JSON from batch_dedup_eval.py")
    parser.add_argument("--source", type=Path,
                        default=REPO_ROOT / "eval_sets" / "batch_dedup_clusters_v4.json")
    parser.add_argument("--judge-model", default="gemini-2.5-pro")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    with open(args.result) as f:
        eval_data = json.load(f)
    with open(args.source) as f:
        clusters = json.load(f)

    cases = _extract_merge_cases(eval_data, clusters)
    print(f"Model: {eval_data['model']} (thinking={eval_data.get('thinking')})")
    print(f"Judge: {args.judge_model}")
    print(f"Operations with merged text: {len(cases)}")
    print()

    if not cases:
        print("No merge/rewrite operations found.")
        return

    results: list[dict[str, Any]] = []
    totals: dict[str, float] = {}
    fabrication_count = 0

    for i, case in enumerate(cases, 1):
        kind_short = case["kind"][:4]
        n_keys = len(case["source_keys"])
        print(
            f"[{i}/{len(cases)}] C{case['cluster_id']} {kind_short} "
            f"{case['action']} ({n_keys} entries)...",
            end=" ",
            flush=True,
        )

        t0 = time.time()
        scores = run_batch_merge_judge(
            source_items=case["source_items"],
            operation=case["operation"],
            memory_kind=case["kind"],
            role=case["role"],
            action_phase=case["action_phase"],
            model=args.judge_model,
        )
        elapsed = time.time() - t0

        record: dict[str, Any] = {
            "cluster_id": case["cluster_id"],
            "kind": case["kind"],
            "role": case["role"],
            "action_phase": case["action_phase"],
            "action": case["action"],
            "num_source_keys": n_keys,
            "elapsed_s": round(elapsed, 1),
        }

        if scores:
            record["scores"] = scores.model_dump(mode="json")
            print(
                f"rc={scores.retrieval_coverage} "
                f"mq={scores.merge_quality} "
                f"ip={scores.information_preservation} "
                f"fab={'Y' if scores.fabrication_detected else 'N'} "
                f"[{elapsed:.1f}s]",
            )
            for dim in ("retrieval_coverage", "merge_quality", "information_preservation"):
                totals[dim] = totals.get(dim, 0) + getattr(scores, dim)
            if scores.fabrication_detected:
                fabrication_count += 1
        else:
            record["scores"] = None
            print(f"ERROR [{elapsed:.1f}s]")

        results.append(record)

    scored = [r for r in results if r["scores"] is not None]
    n = len(scored)
    print(f"\n{'='*60}")
    print(f"Scored: {n}/{len(cases)} operations")
    if n:
        print("Averages:")
        for dim in ("retrieval_coverage", "merge_quality", "information_preservation"):
            avg = totals.get(dim, 0) / n
            print(f"  {dim}: {avg:.2f}")
        print(f"Fabrication rate: {fabrication_count}/{n} ({fabrication_count/n:.0%})")
    print(f"{'='*60}")

    if args.output is None:
        model_slug = eval_data["model"].replace("/", "_").replace("-", "_")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = (
            REPO_ROOT / "evidence" / "batch_dedup_golden_eval"
            / f"merge_quality_{model_slug}_{ts}.json"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(
            {
                "eval_model": eval_data["model"],
                "eval_thinking": eval_data.get("thinking"),
                "judge_model": args.judge_model,
                "source_result": str(args.result),
                "timestamp": datetime.now().isoformat(),
                "num_cases": len(cases),
                "results": results,
            },
            f,
            indent=2,
        )
        f.write("\n")
    print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
