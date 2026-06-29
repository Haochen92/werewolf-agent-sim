"""Assembled labeling pipeline — one staged entry point for the non-human stages.

Wires the previously à-la-carte pieces into a single config-driven CLI:

    LABEL        engine.label_items(models)      → model_scores.json      [automated]
    EXPORT       exporter.export_for_manual       → export_batches/*.md    [human off-ramp]
    CONSOLIDATE  vote(model + human voters)        → consensus_golden.json + ties.json

``run`` chains LABEL → CONSOLIDATE for the no-human fast path. The human points
(copy/paste labelling via EXPORT; resolving ``ties.json``; the unbuilt CALIBRATE
stage) are *stage boundaries* — which is why this is a staged CLI, not one call.

CONSOLIDATE votes directly across each engine entry's per-model ``model_scores``
(plus any human label files), keyed by the entry's own ``(case_index, key)``. So it
is **adapter-agnostic** and handles the engine's multi-model-single-file output.
(It replaces the retired ``merger.merge``, which assumed one-model-per-file and the
reranker adapter's composite ``item_key`` — so it never composed with ``dedup``.)

Usage::

    poetry run python -m evaluation.src.labeling.pipeline run         --config run.json
    poetry run python -m evaluation.src.labeling.pipeline label       --config run.json
    poetry run python -m evaluation.src.labeling.pipeline export      --config run.json
    poetry run python -m evaluation.src.labeling.pipeline consolidate --config run.json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from evaluation.src.core.settings import load_project_env
from evaluation.src.labeling.adapters import get_adapter
from evaluation.src.labeling.config import ExportConfig, LabelingPipelineConfig
from evaluation.src.labeling.engine import label_items
from evaluation.src.labeling.exporter import export_for_manual
from evaluation.src.labeling.voter import agreement_stats, vote

load_project_env()

Key = tuple[int, str]


def _load_voters(
    path: Path,
) -> tuple[dict[str, dict[Key, object]], dict[Key, str], dict[Key, dict]]:
    """Load one label file into per-voter columns.

    Returns ``(voters, item_type_by_key, details_by_key)``. Handles two formats:
    the **engine output** (``{results:[{case_index,key,item_type,model_scores,
    model_details}]}`` — each model becomes its own voter) and a **simple golden**
    (``{labels:[{case_index,key,label|golden_label}]}`` — one voter named by
    ``labeler``). A human copy-paste file saved in either shape drops straight in.
    """
    data = json.loads(Path(path).read_text())
    voters: dict[str, dict[Key, object]] = {}
    item_type: dict[Key, str] = {}
    details: dict[Key, dict] = {}

    if "results" in data:
        for e in data["results"]:
            k: Key = (e["case_index"], e["key"])
            item_type[k] = e.get("item_type", "")
            for model, label in e.get("model_scores", {}).items():
                voters.setdefault(model, {})[k] = label
            if e.get("model_details"):
                details[k] = e["model_details"]
    elif "labels" in data:
        name = data.get("labeler", Path(path).stem)
        col: dict[Key, object] = {}
        for label_row in data["labels"]:
            k = (label_row["case_index"], str(label_row.get("key", label_row["case_index"])))
            col[k] = label_row.get("label", label_row.get("golden_label"))
            item_type.setdefault(k, label_row.get("item_type", ""))
        voters[name] = col
    else:
        raise ValueError(f"Unrecognized label file (no 'results' or 'labels'): {path}")

    return voters, item_type, details


def stage_label(config: LabelingPipelineConfig) -> Path:
    """LABEL: run the model panel over all candidates (resumable)."""
    if not config.models:
        raise ValueError("LABEL needs at least one model in config.models")
    adapter = get_adapter(config.adapter, **config.adapter_kwargs)
    items = adapter.load_items(config.candidates_path)
    print(f"LABEL: {len(items)} items × {len(config.models)} model(s) → {config.scores_path}")
    label_items(
        items, config.models, adapter, config.scores_path,
        checkpoint_every=config.checkpoint_every, resume=True,
    )
    return config.scores_path


def stage_export(config: LabelingPipelineConfig) -> list[Path]:
    """EXPORT off-ramp: markdown batches for ChatGPT/Claude copy-paste labelling."""
    adapter = get_adapter(config.adapter, **config.adapter_kwargs)
    export_cfg = ExportConfig(
        candidates_path=config.candidates_path,
        output_dir=config.export_dir,
        batch_size=config.export_batch_size,
    )
    instructions = config.export_instructions or (
        "Label each item per the rubric. Fill the `relevance` field of every JSON row."
    )
    print(f"EXPORT: → {config.export_dir}  (label the batches, save responses, "
          f"then point a manual_source at them for CONSOLIDATE)")
    return export_for_manual(export_cfg, adapter, instructions)


def stage_consolidate(config: LabelingPipelineConfig) -> Path:
    """CONSOLIDATE: vote across model + human voters → consensus + ties."""
    sources: list[Path] = []
    if config.scores_path.exists():
        sources.append(config.scores_path)
    sources.extend(config.manual_sources)
    if not sources:
        raise ValueError(
            "CONSOLIDATE: nothing to consolidate (no model_scores.json, no manual_sources)"
        )

    voters: dict[str, dict[Key, object]] = {}
    item_type: dict[Key, str] = {}
    details: dict[Key, dict] = {}
    for src in sources:
        v, it, det = _load_voters(src)
        for name, col in v.items():
            voters.setdefault(name, {}).update(col)
        item_type.update(it)
        details.update(det)

    keys = sorted(set().union(*[set(col) for col in voters.values()])) if voters else []
    results: list[dict] = []
    ties: list[dict] = []
    votes = []
    for k in keys:
        scores = {name: col.get(k) for name, col in voters.items()}
        v = vote(scores, config.voting)
        votes.append(v)
        entry = {
            "case_index": k[0], "key": k[1], "item_type": item_type.get(k, ""),
            "label": v.label, "confidence": v.confidence, "scores": v.scores,
        }
        if details.get(k):
            entry["model_details"] = details[k]
        results.append(entry)
        if v.confidence == "tie":
            ties.append({"case_index": k[0], "key": k[1], "scores": v.scores})

    stats = agreement_stats(votes)
    label_dist = Counter(e["label"] for e in results if e["label"] is not None)
    output = {
        "description": "Consolidated consensus labels (pipeline.consolidate)",
        "voters": sorted(voters),
        "stats": {"total_items": len(results), **stats, "labels": dict(label_dist)},
        "results": results,
    }
    config.consensus_path.parent.mkdir(parents=True, exist_ok=True)
    config.consensus_path.write_text(json.dumps(output, indent=2) + "\n")

    print(f"CONSOLIDATE: {len(results)} items · voters={sorted(voters)}")
    for conf, n in sorted(stats.items(), key=lambda x: -x[1]):
        print(f"  {conf:16s}: {n}")
    if ties:
        config.ties_path.write_text(json.dumps(ties, indent=2) + "\n")
        print(f"  {len(ties)} ties → {config.ties_path} "
              f"(resolve → add as a manual_source → re-consolidate)")
    print(f"→ {config.consensus_path}")
    return config.consensus_path


def _load_config(path: Path) -> LabelingPipelineConfig:
    return LabelingPipelineConfig.model_validate_json(Path(path).read_text())


def main() -> None:
    parser = argparse.ArgumentParser(description="Assembled labeling pipeline (staged).")
    parser.add_argument("stage", choices=["label", "export", "consolidate", "run"])
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    config = _load_config(args.config)

    if args.stage == "label":
        stage_label(config)
    elif args.stage == "export":
        stage_export(config)
    elif args.stage == "consolidate":
        stage_consolidate(config)
    elif args.stage == "run":
        stage_label(config)
        stage_consolidate(config)


if __name__ == "__main__":
    main()
