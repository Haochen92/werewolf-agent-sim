"""Merge multiple label sources into final consensus labels.

Combines per-model label files and manual (human) label sources via
the voter module, using the adapter for key normalization and output formatting.
"""
from __future__ import annotations

import glob
import json
from collections import Counter
from pathlib import Path
from typing import Any

from evaluation.labeling.base import LabelingAdapter, LabelItem, VoteResult
from evaluation.labeling.config import ManualSourceConfig, MergeConfig
from evaluation.labeling.voter import vote, agreement_stats


def _load_model_labels(path: Path) -> dict[str, int | str]:
    """Load a per-model engine output into {case_index:key → label}.

    Uses composite keys (case_index:key) since the same memory can be
    retrieved for multiple cases. Handles both the engine output format
    (results list with model_scores) and the legacy format (cases list
    with observation_labels/strategy_labels).
    """
    labels = {}
    data = json.load(open(path))

    if "results" in data:
        for entry in data["results"]:
            scores = entry.get("model_scores", {})
            label = next((v for v in scores.values() if v is not None), None)
            if label is not None:
                composite = f"{entry['case_index']}:{entry['key']}"
                labels[composite] = label
        return labels

    for case in data.get("cases", []):
        case_idx = case["case_index"]
        for item in case.get("observation_labels", []) + case.get("strategy_labels", []):
            score = item.get("relevance")
            if score is not None:
                ms = item.get("model_scores", {})
                actual = next((v for v in ms.values() if v is not None), score)
                composite = f"{case_idx}:{item['key']}"
                labels[composite] = actual
    return labels


def _load_manual_labels(
    source: ManualSourceConfig,
    adapter: LabelingAdapter,
) -> dict[str, int | str]:
    """Load human labels from a file or directory of batch files.

    Returns {normalized_key → label} using the adapter's key normalization.
    """
    labels = {}

    if source.format == "batch_dir":
        for fpath in sorted(Path(source.path).glob("batch_*_response.json")):
            data = json.load(open(fpath))
            for case in data:
                case_idx = case.get("case_index")
                for item in case.get("labels", []):
                    raw_key = item.get("key", "")
                    norm_key = adapter.normalize_manual_key(
                        raw_key, source.key_style, source.key_truncation_length
                    )
                    composite = f"{case_idx}:{norm_key}"
                    labels[composite] = item["relevance"]
    else:
        data = json.load(open(source.path))
        cases = data if isinstance(data, list) else data.get("cases", [])
        for case in cases:
            case_idx = case.get("case_index")
            for item in case.get("labels", case.get("observation_labels", []) + case.get("strategy_labels", [])):
                raw_key = item.get("key", "")
                norm_key = adapter.normalize_manual_key(
                    raw_key, source.key_style, source.key_truncation_length
                )
                composite = f"{case_idx}:{norm_key}"
                labels[composite] = item.get("relevance", item.get("label"))

    return labels


def merge(
    config: MergeConfig,
    adapter: LabelingAdapter,
) -> dict[str, Any]:
    """Merge all label sources and compute consensus.

    Returns the full output dict ready for JSON serialization.
    """
    model_labels: dict[str, dict[str, int | str]] = {}
    for name, path in config.model_label_files.items():
        model_labels[name] = _load_model_labels(path)
        print(f"Loaded {len(model_labels[name])} {name} labels")

    manual_labels: dict[str, dict[str, int | str]] = {}
    for source in config.manual_sources:
        manual_labels[source.name] = _load_manual_labels(source, adapter)
        print(f"Loaded {len(manual_labels[source.name])} {source.name} labels")

    items = adapter.load_items(config.candidates_path)

    votes: list[VoteResult] = []
    ties: list[dict] = []
    results: list[dict] = []

    cases_metadata = adapter.load_cases_metadata(config.candidates_path)
    case_map = {c.get("case_index", i): c for i, c in enumerate(cases_metadata)}

    items_by_case: dict[int, list[tuple[LabelItem, VoteResult]]] = {}

    for item in items:
        scores: dict[str, int | str | None] = {}

        for name, labels in manual_labels.items():
            source_cfg = next(s for s in config.manual_sources if s.name == name)
            manual_key = adapter.manual_key_from_item(
                item, source_cfg.key_style, source_cfg.key_truncation_length
            )
            composite = f"{item.case_index}:{manual_key}"
            scores[name] = labels.get(composite)

        composite_key = adapter.item_key(item)
        for name, labels in model_labels.items():
            scores[name] = labels.get(composite_key)

        result = vote(scores, config.voting)
        votes.append(result)

        if result.confidence == "tie":
            ties.append({
                "case_index": item.case_index,
                "key": item.key,
                "type": item.item_type,
                "scores": result.scores,
                "situation": item.context.get("situation", "")[:100],
            })

        entry = adapter.build_output_entry(item, result)
        results.append(entry)

        items_by_case.setdefault(item.case_index, []).append((item, result))

    stats = agreement_stats(votes)
    total = len(votes)

    print(f"\nMerged {total} items across {len(items_by_case)} cases")
    for conf, count in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {conf:20s}: {count:4d} ({count/max(total,1)*100:.1f}%)")

    if ties:
        print(f"\n{len(ties)} ties need manual tiebreaking:")
        for t in ties[:10]:
            print(f"  case {t['case_index']} {t['type']} "
                  f"{t['scores']} | {t['situation']}...")
        if len(ties) > 10:
            print(f"  ... and {len(ties) - 10} more")

    label_dist = Counter()
    none_count = 0
    for entry in results:
        label = entry.get("relevance", entry.get("label"))
        if label is not None:
            label_dist[label] += 1
        else:
            none_count += 1
    print(f"\nLabel distribution:")
    for label in sorted(label_dist):
        print(f"  {label}: {label_dist[label]}")
    if none_count:
        print(f"  None (unresolved): {none_count}")

    output = {
        "description": "Multi-model consensus labels",
        "sources": {
            "model": list(config.model_label_files.keys()),
            "manual": [s.name for s in config.manual_sources],
        },
        "stats": {"total_items": total, **stats},
        "results": results,
    }

    if not config.dry_run:
        config.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config.output_path, "w") as f:
            json.dump(output, f, indent=2)
            f.write("\n")
        print(f"\nWrote: {config.output_path}")
    else:
        print("\nDry run — not writing output.")

    if ties:
        ties_path = config.output_path.parent / "ties.json"
        with open(ties_path, "w") as f:
            json.dump(ties, f, indent=2)
            f.write("\n")
        print(f"Wrote ties to: {ties_path}")

    return output
