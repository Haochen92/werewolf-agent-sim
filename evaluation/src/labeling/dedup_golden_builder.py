"""Build a dedup Keep/Discard golden via the labeling engine + ``DedupAdapter``.

Single-model golden minter: runs the production dedup prompt (owned by
``DedupAdapter``) through one model via ``engine.label_items`` with structured
output, then writes an ``eval_auto_dedup``-compatible golden labels file.

Supersedes the old standalone ``auto_dedup_labeler`` — the domain logic now
lives once, in ``DedupAdapter`` (prompt construction + structured parse), and
the generic engine supplies the loop / rate-limit / checkpoint-resume. A panel
golden is the same call with more than one ``ModelSpec``.

Usage::

    poetry run python -m evaluation.src.labeling.dedup_golden_builder \
        --dataset evaluation/frozen_eval_sets/auto_dedup_v1_cross_game.jsonl \
        --output evidence/dedup/embedding_prefilter/data/cross_game_golden_labels.json \
        --model gemini-2.5-pro

    # Resume from a partial run (the engine checkpoints alongside --output)
    poetry run python -m evaluation.src.labeling.dedup_golden_builder \
        --dataset ... --output ... --model gemini-2.5-pro --resume
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from evaluation.src.core.settings import load_project_env
from evaluation.src.labeling.adapters.dedup import DedupAdapter
from evaluation.src.labeling.config import ModelSpec
from evaluation.src.labeling.engine import label_items

load_project_env()


def build_golden(
    dataset: Path,
    model: str,
    output: Path,
    rpm: float | None = None,
    thinking_level: str | None = None,
    max_cases: int = 0,
    resume: bool = False,
    checkpoint_every: int = 1,
) -> list[dict]:
    """Label ``dataset`` with one model via the engine, write the golden file."""
    adapter = DedupAdapter()
    items = adapter.load_items(dataset)
    if max_cases:
        items = items[:max_cases]

    spec = ModelSpec(name=model, rpm_limit=rpm, thinking_level=thinking_level)
    checkpoint = output.with_suffix(".checkpoint.json")
    results = label_items(
        items, [spec], adapter, checkpoint,
        checkpoint_every=checkpoint_every, resume=resume,
    )

    labels = to_golden_labels(results, model)
    _save_golden(output, labels, _read_eval_set_id(dataset), model)

    counts = Counter(l["golden_label"] for l in labels)
    print(f"\nWrote {len(labels)} golden labels to {output}")
    print(f"Distribution: {dict(counts.most_common())}")
    return labels


def to_golden_labels(results: list[dict], model: str) -> list[dict]:
    """Transform engine results into the ``eval_auto_dedup`` golden-label shape.

    ``golden_label`` is the model's K/D; ``duplicate_of_candidate`` + ``reasoning``
    come from the structured ``model_details`` (audit-only — the calibration eval
    reads only ``golden_label``).
    """
    labels: list[dict] = []
    for entry in results:
        label = entry.get("model_scores", {}).get(model)
        if label is None:
            continue
        detail = entry.get("model_details", {}).get(model, {})
        out: dict = {
            "case_index": entry["case_index"],
            "item_type": entry["item_type"],
            "golden_label": label,
        }
        if label == "D" and detail.get("duplicate_of_candidate") is not None:
            out["duplicate_of_candidate"] = detail["duplicate_of_candidate"]
        if detail.get("reasoning"):
            out["reasoning"] = detail["reasoning"]
        labels.append(out)
    return sorted(labels, key=lambda x: x["case_index"])


def _read_eval_set_id(dataset: Path) -> str:
    with dataset.open() as f:
        first = json.loads(f.readline())
    return first.get("eval_set_id", dataset.stem)


def _save_golden(path: Path, labels: list[dict], eval_set_id: str, model: str) -> None:
    counts = Counter(l["golden_label"] for l in labels)
    golden = {
        "eval_set_id": eval_set_id,
        "created_at": datetime.now().isoformat(),
        "labeler": f"LLM:{model}",
        "description": f"Auto-labeled by {model} using production dedup prompts",
        "label_schema": {
            "D": "DISCARD - duplicate of an existing candidate",
            "K": "KEEP - distinct, keep as a new entry",
        },
        "summary": ", ".join(f"{k}={v}" for k, v in counts.most_common()),
        "labels": labels,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(golden, f, indent=2)
        f.write("\n")


def main() -> None:
    p = argparse.ArgumentParser(
        description="Build a dedup golden via the labeling engine + DedupAdapter."
    )
    p.add_argument("--dataset", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--model", type=str, default="gemini-2.5-pro")
    p.add_argument("--rpm", type=float, default=None, help="Per-model requests/min rate limit.")
    p.add_argument(
        "--thinking-level", choices=["minimal", "low", "medium", "high"], default=None
    )
    p.add_argument("--max-cases", type=int, default=0)
    p.add_argument("--resume", action="store_true")
    args = p.parse_args()

    print(f"Dataset: {args.dataset}\nModel: {args.model}\nOutput: {args.output}\n")
    build_golden(
        dataset=args.dataset,
        model=args.model,
        output=args.output,
        rpm=args.rpm,
        thinking_level=args.thinking_level,
        max_cases=args.max_cases,
        resume=args.resume,
    )


if __name__ == "__main__":
    main()
