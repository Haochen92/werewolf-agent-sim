"""Evaluate batch dedup models against golden labels.

Runs the batch dedup prompts on selected clusters and compares model
output against human-labeled golden labels. Scores per-key action
accuracy and reports DISCARD/MERGE/KEEP confusion.

Usage::

    poetry run python -m evaluation.experiments.batch_dedup_eval \
        --model gemini-3.5-flash --thinking medium \
        --source eval_sets/batch_dedup_clusters_v4.json \
        --labels eval_sets/batch_dedup_golden_labels.json
"""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from Agents.llm_factory import create_chat_model
from Agents.memory_batch_deduplication import (
    ObservationBatchDedupOutput,
    StrategyBatchDedupOutput,
)
from Agents.prompts.dedup import (
    BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT,
    BATCH_STRATEGY_CLUSTER_DEDUP_PROMPT,
)
from Agents.prompts.standards import EPISTEMIC_STATUS_RULE, SITUATION_STANDARDS
from evaluation.core.settings import REPO_ROOT


EVAL_CLUSTER_IDS = [0, 4, 11, 14, 16, 21, 25, 28, 33, 5, 20]


def format_entries(cluster: dict) -> tuple[str, dict[str, str]]:
    """Format cluster entries using numbered indices, returning index-to-key map."""
    lines: list[str] = []
    index_to_key: dict[str, str] = {}
    for i, item in enumerate(cluster["items"], 1):
        index_to_key[str(i)] = item["key"]
        val = item.get("value", item)
        lines.append(f"[{i}]")
        lines.append(f"observation_count: {val.get('observation_count', 1)}")
        lines.append(f"last_observed: {val.get('last_observed', 'N/A')}")
        lines.append(f"situation: {val.get('situation', '')}")
        if cluster["kind"] == "strategy_points":
            lines.append(f"action: {val.get('action', '')}")
        else:
            lines.append(f"approach: {val.get('approach', '')}")
            lines.append(f"outcome: {val.get('outcome', '')}")
        lines.append("")
    return "\n".join(lines).strip(), index_to_key


def _remap_keys(source_keys: list[str], index_to_key: dict[str, str]) -> list[str]:
    return [index_to_key.get(k, k) for k in source_keys]


def call_model(
    cluster: dict,
    model: str,
    thinking_level: str | None,
) -> dict[str, Any]:
    llm = create_chat_model(model, temperature=0.0, thinking_level=thinking_level)
    entries, index_to_key = format_entries(cluster)
    ns = cluster["namespace"]
    role = ns[1] if isinstance(ns, list) else ns.split("/")[1]
    action_phase = ns[2] if isinstance(ns, list) else ns.split("/")[2]
    kind = cluster["kind"]

    if kind == "strategy_points":
        prompt = BATCH_STRATEGY_CLUSTER_DEDUP_PROMPT.format(
            role=role,
            action_phase=action_phase,
            entries=entries,
            situation_standards=SITUATION_STANDARDS,
            epistemic_status_rule=EPISTEMIC_STATUS_RULE,
        )
        schema = StrategyBatchDedupOutput
    else:
        prompt = BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT.format(
            role=role,
            action_phase=action_phase,
            entries=entries,
            situation_standards=SITUATION_STANDARDS,
        )
        schema = ObservationBatchDedupOutput

    result = llm.with_structured_output(schema).invoke(
        [{"role": "user", "content": prompt}],
    )
    if isinstance(result, dict):
        result = schema.model_validate(result)

    ops = []
    for op in result.operations:
        d = {
            "action": op.action,
            "source_keys": _remap_keys(op.source_keys, index_to_key),
        }
        if op.survivor_key:
            d["survivor_key"] = index_to_key.get(op.survivor_key, op.survivor_key)
        if hasattr(op, "merged_situation") and op.merged_situation:
            d["merged_situation"] = op.merged_situation
        if hasattr(op, "merged_approach") and op.merged_approach:
            d["merged_approach"] = op.merged_approach
        if hasattr(op, "merged_outcome") and op.merged_outcome:
            d["merged_outcome"] = op.merged_outcome
        if hasattr(op, "merged_action") and op.merged_action:
            d["merged_action"] = op.merged_action
        if hasattr(op, "reasoning"):
            d["reasoning"] = op.reasoning
        ops.append(d)
    return {"operations": ops}


def build_key_labels(golden_ops: list[dict]) -> dict[str, str]:
    """Map each key to its golden action label."""
    key_to_action: dict[str, str] = {}
    for op in golden_ops:
        for key in op["source_keys"]:
            key_to_action[key] = op["action"]
    return key_to_action


def build_key_labels_from_model(model_ops: list[dict]) -> dict[str, str]:
    key_to_action: dict[str, str] = {}
    for op in model_ops:
        for key in op["source_keys"]:
            key_to_action[key] = op["action"]
    return key_to_action


def score_cluster(
    golden_ops: list[dict],
    model_ops: list[dict],
    cluster_id: int,
) -> dict[str, Any]:
    golden_keys = build_key_labels(golden_ops)
    model_keys = build_key_labels_from_model(model_ops)

    all_keys = set(golden_keys) | set(model_keys)
    correct = 0
    total = 0
    confusion: list[dict] = []

    for key in all_keys:
        g = golden_keys.get(key, "MISSING")
        m = model_keys.get(key, "MISSING")
        total += 1
        if g == m:
            correct += 1
        else:
            confusion.append({"key": key[:8], "golden": g, "model": m})

    golden_action_counts = Counter(golden_keys.values())
    model_action_counts = Counter(model_keys.values())

    return {
        "cluster_id": cluster_id,
        "total_keys": total,
        "correct": correct,
        "accuracy": correct / total if total > 0 else 0,
        "golden_distribution": dict(golden_action_counts),
        "model_distribution": dict(model_action_counts),
        "errors": confusion,
    }


def run_eval(
    clusters: list[dict],
    labels: dict,
    model: str,
    thinking_level: str | None,
    cluster_ids: list[int],
) -> list[dict]:
    label_by_id = {l["cluster_id"]: l for l in labels["labels"]}
    results = []

    for cid in cluster_ids:
        if cid not in label_by_id:
            print(f"  Skipping cluster {cid}: no golden label")
            continue

        cluster = clusters[cid]
        golden = label_by_id[cid]
        print(f"  Cluster {cid:2d} ({cluster['kind'][:4]}, size={cluster['size']:2d})...", end=" ", flush=True)

        t0 = time.time()
        try:
            model_result = call_model(cluster, model, thinking_level)
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
        results.append(score)

        status = f"{score['accuracy']:.0%} ({score['correct']}/{score['total_keys']})"
        print(f"{status}  [{elapsed:.1f}s]  golden={score['golden_distribution']}  model={score['model_distribution']}")

    return results


def print_summary(results: list[dict], model: str, thinking: str | None) -> None:
    valid = [r for r in results if "error" not in r]
    if not valid:
        print("No valid results.")
        return

    total_keys = sum(r["total_keys"] for r in valid)
    total_correct = sum(r["correct"] for r in valid)
    total_elapsed = sum(r.get("elapsed_s", 0) for r in valid)

    print(f"\n{'='*60}")
    print(f"Model: {model} (thinking={thinking or 'none'})")
    print(f"Clusters evaluated: {len(valid)}")
    print(f"Overall accuracy: {total_correct}/{total_keys} = {total_correct/total_keys:.1%}")
    print(f"Total time: {total_elapsed:.1f}s")

    all_golden = Counter()
    all_model = Counter()
    for r in valid:
        for a, c in r["golden_distribution"].items():
            all_golden[a] += c
        for a, c in r["model_distribution"].items():
            all_model[a] += c

    print(f"\nGolden distribution: {dict(all_golden)}")
    print(f"Model distribution:  {dict(all_model)}")

    all_errors = []
    for r in valid:
        for e in r.get("errors", []):
            all_errors.append(e)

    if all_errors:
        print(f"\nConfusion ({len(all_errors)} errors):")
        confusion_matrix: Counter[tuple[str, str]] = Counter()
        for e in all_errors:
            confusion_matrix[(e["golden"], e["model"])] += 1
        for (g, m), count in confusion_matrix.most_common():
            print(f"  {g} -> {m}: {count}")

    per_action = {}
    for r in valid:
        golden_keys = build_key_labels(
            next(l["operations"] for l in [r] if True)
            if "model_operations" not in r else []
        )

    print(f"{'='*60}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate batch dedup models")
    parser.add_argument("--model", required=True)
    parser.add_argument("--thinking", default=None)
    parser.add_argument("--source", type=Path, default=REPO_ROOT / "eval_sets" / "batch_dedup_clusters_v4.json")
    parser.add_argument("--labels", type=Path, default=REPO_ROOT / "eval_sets" / "batch_dedup_golden_labels.json")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--cluster-ids", type=str, default=None,
                        help="Comma-separated cluster IDs (default: eval set)")
    args = parser.parse_args()

    with open(args.source) as f:
        clusters = json.load(f)
    with open(args.labels) as f:
        labels = json.load(f)

    cluster_ids = (
        [int(x) for x in args.cluster_ids.split(",")]
        if args.cluster_ids
        else EVAL_CLUSTER_IDS
    )

    print(f"Running batch dedup eval: {args.model} (thinking={args.thinking})")
    print(f"Clusters: {cluster_ids}\n")

    results = run_eval(clusters, labels, args.model, args.thinking, cluster_ids)
    print_summary(results, args.model, args.thinking)

    if args.output is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_slug = args.model.replace("/", "_").replace("-", "_")
        thinking_slug = f"_think_{args.thinking}" if args.thinking else ""
        args.output = REPO_ROOT / "evidence" / "batch_dedup_golden_eval" / f"eval_{model_slug}{thinking_slug}_{ts}.json"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump({
            "model": args.model,
            "thinking": args.thinking,
            "timestamp": datetime.now().isoformat(),
            "cluster_ids": cluster_ids,
            "results": results,
        }, f, indent=2)
        f.write("\n")
    print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
