"""Evaluate batch cluster-dedup models against golden labels (CLI).

Thin runner that chains regen + scoring: for each selected cluster it replays the
batch-dedup prompt (``replay.batch_dedup``, single- or two-pass) and scores the
model operations against human golden labels (``audits.batch_dedup_score``),
reporting per-key accuracy and DISCARD/MERGE/KEEP confusion.

Usage::

    poetry run python -m evaluation.src.experiments.frozen_case_evals.batch_dedup_judge \\
        --model gemini-3.5-flash --thinking medium \\
        --source evaluation/frozen_eval_sets/batch_dedup_clusters_v4.json \\
        --labels evaluation/frozen_eval_sets/batch_dedup_golden_labels.json
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from evaluation.src.audits.batch_dedup_score import print_summary, score_cluster
from evaluation.src.core.settings import REPO_ROOT
from evaluation.src.replay.batch_dedup import (
    PROMPT_VARIANTS,
    call_model,
    call_model_two_pass,
)

EVAL_CLUSTER_IDS = [0, 4, 11, 14, 16, 21, 25, 28, 33, 5, 20]


def run_eval(
    clusters: list[dict],
    labels: dict,
    model: str,
    thinking_level: str | None,
    cluster_ids: list[int],
    two_pass: dict | None = None,
    prompt_variant: str = "default",
) -> list[dict]:
    label_by_id = {l["cluster_id"]: l for l in labels["labels"]}
    results = []
    total_escalated = 0
    total_eval_keys = 0

    for cid in cluster_ids:
        if cid not in label_by_id:
            print(f"  Skipping cluster {cid}: no golden label")
            continue

        cluster = clusters[cid]
        golden = label_by_id[cid]
        print(f"  Cluster {cid:2d} ({cluster['kind'][:4]}, size={cluster['size']:2d})...", end=" ", flush=True)

        t0 = time.time()
        try:
            if two_pass:
                model_result = call_model_two_pass(
                    cluster,
                    triage_model=two_pass["triage_model"],
                    triage_thinking=two_pass["triage_thinking"],
                    verify_model=two_pass["verify_model"],
                    verify_thinking=two_pass["verify_thinking"],
                    prompt_variant=prompt_variant,
                )
            else:
                model_result = call_model(cluster, model, thinking_level, prompt_variant=prompt_variant)
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                "cluster_id": cid,
                "error": str(e),
            })
            continue
        elapsed = time.time() - t0

        score = score_cluster(golden["operations"], model_result["operations"], cid)
        score["elapsed_s"] = round(elapsed, 1)
        score["model_operations"] = model_result["operations"]
        if "escalated_keys" in model_result:
            score["escalated_keys"] = model_result["escalated_keys"]
            score["total_keys_in_cluster"] = model_result["total_keys"]
            total_escalated += model_result["escalated_keys"]
            total_eval_keys += model_result["total_keys"]

        results.append(score)

        status = f"{score['accuracy']:.0%} ({score['correct']}/{score['total_keys']})"
        esc = f"  esc={model_result['escalated_keys']}/{model_result['total_keys']}" if "escalated_keys" in model_result else ""
        print(f"{status}  [{elapsed:.1f}s]{esc}  golden={score['golden_distribution']}  model={score['model_distribution']}")

    if two_pass and total_eval_keys:
        print(f"\n  Escalation rate: {total_escalated}/{total_eval_keys} = {total_escalated/total_eval_keys:.0%}")

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate batch dedup models")
    parser.add_argument("--model", default=None)
    parser.add_argument("--thinking", default=None)
    parser.add_argument("--two-pass", action="store_true",
                        help="Run two-pass eval (flash-lite triage -> 2.5-pro verify)")
    parser.add_argument("--triage-model", default="gemini-3.1-flash-lite")
    parser.add_argument("--triage-thinking", default="medium")
    parser.add_argument("--verify-model", default="gemini-2.5-pro")
    parser.add_argument("--verify-thinking", default=None)
    parser.add_argument("--source", type=Path, default=REPO_ROOT / "evaluation" / "frozen_eval_sets" / "batch_dedup_clusters_v4.json")
    parser.add_argument("--labels", type=Path, default=REPO_ROOT / "evaluation" / "frozen_eval_sets" / "batch_dedup_golden_labels.json")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--prompt-variant", default="default",
                        choices=list(PROMPT_VARIANTS.keys()),
                        help="Prompt variant to use (default: standard v3 prompts)")
    parser.add_argument("--cluster-ids", type=str, default=None,
                        help="Comma-separated cluster IDs (default: eval set)")
    args = parser.parse_args()

    if not args.two_pass and not args.model:
        parser.error("--model is required unless --two-pass is used")

    with open(args.source) as f:
        clusters = json.load(f)
    with open(args.labels) as f:
        labels = json.load(f)

    cluster_ids = (
        [int(x) for x in args.cluster_ids.split(",")]
        if args.cluster_ids
        else EVAL_CLUSTER_IDS
    )

    two_pass_config = None
    if args.two_pass:
        two_pass_config = {
            "triage_model": args.triage_model,
            "triage_thinking": args.triage_thinking,
            "verify_model": args.verify_model,
            "verify_thinking": args.verify_thinking,
        }
        model_label = f"two-pass ({args.triage_model} -> {args.verify_model})"
        print(f"Running batch dedup eval: {model_label}")
        print(f"  Triage: {args.triage_model} (thinking={args.triage_thinking})")
        print(f"  Verify: {args.verify_model} (thinking={args.verify_thinking})")
    else:
        model_label = args.model
        print(f"Running batch dedup eval: {args.model} (thinking={args.thinking})")
    if args.prompt_variant != "default":
        print(f"Prompt variant: {args.prompt_variant}")
    print(f"Clusters: {cluster_ids}\n")

    results = run_eval(
        clusters, labels, args.model, args.thinking, cluster_ids,
        two_pass=two_pass_config,
        prompt_variant=args.prompt_variant,
    )
    print_summary(results, model_label, args.thinking if not args.two_pass else "two-pass")

    if args.output is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        if args.two_pass:
            model_slug = "two_pass_lite_pro"
        else:
            model_slug = args.model.replace("/", "_").replace("-", "_")
        thinking_slug = f"_think_{args.thinking}" if args.thinking and not args.two_pass else ""
        variant_slug = f"_{args.prompt_variant}" if args.prompt_variant != "default" else ""
        args.output = REPO_ROOT / "evidence" / "dedup" / "batch_dedup" / f"eval_{model_slug}{thinking_slug}{variant_slug}_{ts}.json"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump({
            "model": model_label,
            "thinking": args.thinking if not args.two_pass else "two-pass",
            "prompt_variant": args.prompt_variant,
            "two_pass": two_pass_config,
            "timestamp": datetime.now().isoformat(),
            "cluster_ids": cluster_ids,
            "results": results,
        }, f, indent=2)
        f.write("\n")
    print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
