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
    BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT_LITE,
    BATCH_STRATEGY_CLUSTER_DEDUP_PROMPT,
)

PROMPT_VARIANTS = {
    "default": {
        "observation": BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT,
        "strategy": BATCH_STRATEGY_CLUSTER_DEDUP_PROMPT,
    },
    "lite": {
        "observation": BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT_LITE,
        "strategy": BATCH_STRATEGY_CLUSTER_DEDUP_PROMPT,
    },
}
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


def _extract_ops(result, index_to_key: dict[str, str]) -> list[dict]:
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
    return ops


def _invoke_model(
    cluster: dict,
    model: str,
    thinking_level: str | None,
    entries: str,
    index_to_key: dict[str, str],
    prompt_variant: str = "default",
):
    llm = create_chat_model(model, temperature=0.0, thinking_level=thinking_level)
    ns = cluster["namespace"]
    role = ns[1] if isinstance(ns, list) else ns.split("/")[1]
    action_phase = ns[2] if isinstance(ns, list) else ns.split("/")[2]
    kind = cluster["kind"]

    prompts = PROMPT_VARIANTS[prompt_variant]

    if kind == "strategy_points":
        prompt = prompts["strategy"].format(
            role=role,
            action_phase=action_phase,
            entries=entries,
            situation_standards=SITUATION_STANDARDS,
            epistemic_status_rule=EPISTEMIC_STATUS_RULE,
        )
        schema = StrategyBatchDedupOutput
    else:
        prompt = prompts["observation"].format(
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
    return result


def call_model(
    cluster: dict,
    model: str,
    thinking_level: str | None,
    prompt_variant: str = "default",
) -> dict[str, Any]:
    entries, index_to_key = format_entries(cluster)
    result = _invoke_model(cluster, model, thinking_level, entries, index_to_key, prompt_variant=prompt_variant)
    return {"operations": _extract_ops(result, index_to_key)}


def call_model_two_pass(
    cluster: dict,
    triage_model: str,
    triage_thinking: str | None,
    verify_model: str,
    verify_thinking: str | None,
    prompt_variant: str = "default",
) -> dict[str, Any]:
    """Two-pass: triage model classifies, KEEP/DISCARD trusted, MERGE escalated."""
    entries, index_to_key = format_entries(cluster)
    key_to_index = {v: k for k, v in index_to_key.items()}

    triage_result = _invoke_model(
        cluster, triage_model, triage_thinking, entries, index_to_key,
        prompt_variant=prompt_variant,
    )

    trusted_ops = []
    merge_keys: set[str] = set()
    for op in triage_result.operations:
        real_keys = _remap_keys(op.source_keys, index_to_key)
        if op.action == "MERGE":
            merge_keys.update(real_keys)
        else:
            trusted_ops.append(op)

    escalated_count = len(merge_keys)

    if not merge_keys:
        ops = _extract_ops(triage_result, index_to_key)
        return {"operations": ops, "escalated_keys": 0, "total_keys": len(index_to_key)}

    if len(merge_keys) < 2:
        for op in triage_result.operations:
            if op.action == "MERGE":
                op.action = "KEEP"
                op.merged_situation = None
                op.survivor_key = None
                if hasattr(op, "merged_approach"):
                    op.merged_approach = None
                if hasattr(op, "merged_outcome"):
                    op.merged_outcome = None
        ops = _extract_ops(triage_result, index_to_key)
        return {"operations": ops, "escalated_keys": escalated_count, "total_keys": len(index_to_key)}

    verify_items = [
        item for item in cluster["items"] if item["key"] in merge_keys
    ]
    verify_cluster = dict(cluster, items=verify_items, size=len(verify_items))
    verify_entries, verify_index_to_key = format_entries(verify_cluster)

    verify_result = _invoke_model(
        verify_cluster, verify_model, verify_thinking,
        verify_entries, verify_index_to_key,
    )

    all_ops = (
        _extract_ops(type(triage_result)(operations=trusted_ops), index_to_key)
        + _extract_ops(verify_result, verify_index_to_key)
    )
    return {
        "operations": all_ops,
        "escalated_keys": escalated_count,
        "total_keys": len(index_to_key),
    }


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
    parser.add_argument("--model", default=None)
    parser.add_argument("--thinking", default=None)
    parser.add_argument("--two-pass", action="store_true",
                        help="Run two-pass eval (flash-lite triage -> 2.5-pro verify)")
    parser.add_argument("--triage-model", default="gemini-3.1-flash-lite")
    parser.add_argument("--triage-thinking", default="medium")
    parser.add_argument("--verify-model", default="gemini-2.5-pro")
    parser.add_argument("--verify-thinking", default=None)
    parser.add_argument("--source", type=Path, default=REPO_ROOT / "eval_sets" / "batch_dedup_clusters_v4.json")
    parser.add_argument("--labels", type=Path, default=REPO_ROOT / "eval_sets" / "batch_dedup_golden_labels.json")
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
        args.output = REPO_ROOT / "evidence" / "dedup" / "batch_prompt_tuning" / f"eval_{model_slug}{thinking_slug}{variant_slug}_{ts}.json"

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
