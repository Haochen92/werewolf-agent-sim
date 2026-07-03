"""Score batch cluster-dedup operations against golden labels (deterministic, no LLM).

Given the model's per-cluster operations (from ``replay.batch_dedup``) and the
human golden operations, computes per-key action accuracy and the
KEEP/DISCARD/MERGE confusion. Sibling of ``audits.dedup_score`` (which scores the
online per-decision dedup); this one scores the batch cluster pass.
"""

from __future__ import annotations

from collections import Counter
from typing import Any


def key_action_labels(ops: list[dict]) -> dict[str, str]:
    """Map each key to the action of the operation that references it."""
    key_to_action: dict[str, str] = {}
    for op in ops:
        for key in op["source_keys"]:
            key_to_action[key] = op["action"]
    return key_to_action


def score_cluster(
    golden_ops: list[dict],
    model_ops: list[dict],
    cluster_id: int,
) -> dict[str, Any]:
    golden_keys = key_action_labels(golden_ops)
    model_keys = key_action_labels(model_ops)

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

    all_golden: Counter[str] = Counter()
    all_model: Counter[str] = Counter()
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

    print(f"{'='*60}")
