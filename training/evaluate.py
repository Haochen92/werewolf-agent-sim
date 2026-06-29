"""Standalone evaluation of a saved cross-encoder (CPU).

Replaces the old ``eval_*_modal.py`` scripts: cross-encoder inference is cheap,
so held-out evaluation runs locally with no GPU. Uses the adapter's evaluator,
so metrics match what training reports.

    poetry run python -m evaluation.training.evaluate \
        --adapter reranker --model models/cross_encoder/reranker_v4 --split test

    poetry run python -m evaluation.training.evaluate \
        --adapter dedup --model models/cross_encoder/ce_minilm_dedup_run1
"""
from __future__ import annotations

import argparse
import json

from .adapters import get_adapter
from .evaluator import evaluate_saved


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", required=True, help="adapter name (reranker, dedup)")
    parser.add_argument("--model", required=True, help="path to the saved cross-encoder")
    parser.add_argument("--split", default="test", help="held-out split (reranker: val/test)")
    args = parser.parse_args()

    adapter = get_adapter(args.adapter)
    records = adapter.held_out_records(args.split)
    print(f"[{args.adapter}] evaluating {args.model} on {len(records)} records (split={args.split})")

    metrics = evaluate_saved(args.model, records, adapter.evaluator)
    print(json.dumps(metrics, indent=2, default=str))


if __name__ == "__main__":
    main()
