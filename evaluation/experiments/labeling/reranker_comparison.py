"""Compare reranker methods on golden retrieval labels via NDCG@k.

Scores golden-labeled cases with multiple reranking methods and compares
ranking quality against human-assigned graded relevance (0/1/2).
Defaults to test split only (from reranker_split.json).

Methods:
  - bi-encoder: Gemini embedding cosine similarity (scores in golden labels)
  - cross-encoder: fine-tuned MiniLM cross-encoder (local CPU inference)
  - flash-lite: production LLM reranker (gemini-3.1-flash-lite, 1-5 scores)
  - cohere: Cohere rerank-v3.5 API (optional)

Usage::

    # Default: test split, bi-encoder + cross-encoder + flash-lite
    poetry run python -m evaluation.experiments.labeling.reranker_comparison

    # Evaluate on all data (with warning)
    poetry run python -m evaluation.experiments.labeling.reranker_comparison --split all

    # Specific methods only
    poetry run python -m evaluation.experiments.labeling.reranker_comparison \
        --methods bi-encoder cross-encoder

    # Include Cohere
    poetry run python -m evaluation.experiments.labeling.reranker_comparison \
        --include-cohere

    # Save scores to JSON for later analysis
    poetry run python -m evaluation.experiments.labeling.reranker_comparison \
        --save-scores reranker_scores.json
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import time
from collections import defaultdict
from pathlib import Path

from evaluation.core.settings import REPO_ROOT, load_project_env

load_project_env()

GOLDEN_LABELS_PATH = (
    REPO_ROOT / "evidence" / "extraction" / "situation_summary"
    / "retrieval_golden_labels.json"
)
CE_MODEL_PATH = (
    REPO_ROOT / "evidence" / "fine_tuning" / "cross_encoder"
    / "reranker_v4"
)
OBS_STORE = REPO_ROOT / "Agents" / "memory_stores" / "v4_deduped_v2" / "observations.json"
SP_STORE = REPO_ROOT / "Agents" / "memory_stores" / "v4_deduped_v2" / "strategy_points.json"
SPLIT_PATH = (
    REPO_ROOT / "evidence" / "fine_tuning" / "cross_encoder" / "reranker_split.json"
)

ALL_METHODS = ["bi-encoder", "cross-encoder", "flash-lite", "flash-35", "cohere"]


# ---------------------------------------------------------------------------
# NDCG helpers (same formula as situation_retrieval_ndcg.py)
# ---------------------------------------------------------------------------

def dcg_at_k(rels: list[int], k: int) -> float:
    return sum(
        (2 ** rels[i] - 1) / math.log2(i + 2)
        for i in range(min(k, len(rels)))
    )


def ndcg_at_k(rels: list[int], k: int) -> float:
    actual = dcg_at_k(rels, k)
    ideal = dcg_at_k(sorted(rels, reverse=True), k)
    return actual / ideal if ideal > 0 else 1.0


# ---------------------------------------------------------------------------
# Memory store text lookup (for labels that only have key + relevance)
# ---------------------------------------------------------------------------

def _load_memory_texts() -> dict[str, dict]:
    """Load memory store items keyed by item key, with text and type."""
    key_to_item: dict[str, dict] = {}

    with open(OBS_STORE) as f:
        obs_data = json.load(f)
    for items in obs_data["namespaces"].values():
        for item in items:
            val = item["value"]
            key_to_item[item["key"]] = {
                "situation": val.get("situation", ""),
                "approach": val.get("approach", ""),
                "outcome": val.get("outcome", ""),
                "mem_type": "observation",
            }

    with open(SP_STORE) as f:
        sp_data = json.load(f)
    for items in sp_data["namespaces"].values():
        for item in items:
            key_to_item[item["key"]] = {
                "situation": item["value"].get("situation", ""),
                "mem_type": "strategy_point",
            }

    return key_to_item


# ---------------------------------------------------------------------------
# Document formatting (matches production pipeline exactly)
# ---------------------------------------------------------------------------

def _format_obs_text(fields: dict) -> str:
    """Same as Agents/reranker.py:_format_observation_candidate."""
    parts = [f"Situation: {fields['situation']}"]
    if fields.get("approach"):
        parts.append(f"Approach: {fields['approach']}")
    if fields.get("outcome"):
        parts.append(f"Outcome: {fields['outcome']}")
    return " | ".join(parts)


def _format_sp_text(fields: dict) -> str:
    """Same as Agents/reranker.py:_format_strategy_point_candidate."""
    return fields["situation"]


def build_case_items(
    case: dict, key_to_item: dict[str, dict],
) -> list[dict]:
    """Build unified (query, doc_text, relevance, bi_score) items for a case.

    Some labels only have (key, relevance) without text or bi-encoder score;
    the text is looked up from the memory store.
    """
    query = "\n".join(case["golden_situations"])
    items = []
    for label in case.get("observation_labels", []):
        key = label["key"]
        if "situation" in label:
            fields = label
            mem_type = "observation"
        else:
            fields = key_to_item.get(key)
            if not fields:
                continue
            mem_type = fields["mem_type"]
        items.append({
            "query": query,
            "doc_text": _format_obs_text(fields),
            "relevance": label["relevance"],
            "bi_score": label.get("score"),
            "mem_type": mem_type,
            "key": key,
        })
    for label in case.get("strategy_labels", []):
        key = label["key"]
        if "situation" in label:
            fields = label
            mem_type = "strategy_point"
        else:
            fields = key_to_item.get(key)
            if not fields:
                continue
            mem_type = fields.get("mem_type", "strategy_point")
        items.append({
            "query": query,
            "doc_text": _format_sp_text(fields),
            "relevance": label["relevance"],
            "bi_score": label.get("score"),
            "mem_type": mem_type,
            "key": key,
        })
    return items


# ---------------------------------------------------------------------------
# Scorers — each returns list[list[float]] parallel to all_items
# ---------------------------------------------------------------------------

def score_bi_encoder(all_items: list[list[dict]]) -> list[list[float]]:
    return [
        [it["bi_score"] if it["bi_score"] is not None else 0.0 for it in case_items]
        for case_items in all_items
    ]


def score_cross_encoder(all_items: list[list[dict]]) -> list[list[float]]:
    import torch
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    torch.set_num_threads(1)
    from sentence_transformers.cross_encoder import CrossEncoder

    if not CE_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Cross-encoder model not found at {CE_MODEL_PATH}. "
            "Download with: modal volume get cross-encoder-reranker-output "
            "reranker_v2_768pairs/ evidence/fine_tuning/cross_encoder/reranker_v2_768pairs/"
        )

    model = CrossEncoder(str(CE_MODEL_PATH))
    results = []
    for case_items in all_items:
        pairs = [(it["query"], it["doc_text"]) for it in case_items]
        scores = model.predict(pairs)
        results.append([float(s) for s in scores])
    return results


def score_flash_lite(all_items: list[list[dict]]) -> list[list[float]]:
    from Agents.llm_factory import create_chat_model

    from Agents.prompts import RERANK_PROMPT
    from Agents.schemas import RerankResult

    llm = create_chat_model("gemini-3.1-flash-lite", temperature=0.0)
    chain = RERANK_PROMPT | llm.with_structured_output(RerankResult)

    results = []
    for ci, case_items in enumerate(all_items):
        situations_text = "\n".join(
            f"- {s}" for s in case_items[0]["query"].split("\n")
        )
        numbered = "\n".join(
            f"[{i}] {it['doc_text']}" for i, it in enumerate(case_items)
        )
        try:
            result = chain.invoke(
                {"situations": situations_text, "candidates": numbered},
            )
            score_map = {r.index: r.relevance for r in result.rankings}
            scores = [float(score_map.get(i, 1)) for i in range(len(case_items))]
        except Exception as e:
            print(f"    case {ci}: flash-lite failed ({e}), using fallback scores")
            scores = [0.0] * len(case_items)
        results.append(scores)
        time.sleep(0.2)
    return results


def score_cohere(all_items: list[list[dict]]) -> list[list[float]]:
    import cohere

    co = cohere.ClientV2()
    results = []
    for ci, case_items in enumerate(all_items):
        query = case_items[0]["query"]
        docs = [it["doc_text"] for it in case_items]
        try:
            response = co.rerank(
                model="rerank-v3.5",
                query=query,
                documents=docs,
                top_n=len(docs),
            )
            score_map = {r.index: r.relevance_score for r in response.results}
            scores = [score_map.get(i, 0.0) for i in range(len(case_items))]
        except Exception as e:
            print(f"    case {ci}: cohere failed ({e}), using fallback scores")
            scores = [0.0] * len(case_items)
        results.append(scores)
        time.sleep(0.1)
    return results


def score_flash_35(all_items: list[list[dict]]) -> list[list[float]]:
    from Agents.llm_factory import create_chat_model
    from Agents.prompts import RERANK_PROMPT
    from Agents.schemas import RerankResult

    llm = create_chat_model("gemini-3.5-flash", temperature=0.0)
    chain = RERANK_PROMPT | llm.with_structured_output(RerankResult)

    results = []
    for ci, case_items in enumerate(all_items):
        situations_text = "\n".join(
            f"- {s}" for s in case_items[0]["query"].split("\n")
        )
        numbered = "\n".join(
            f"[{i}] {it['doc_text']}" for i, it in enumerate(case_items)
        )
        try:
            result = chain.invoke(
                {"situations": situations_text, "candidates": numbered},
            )
            score_map = {r.index: r.relevance for r in result.rankings}
            scores = [float(score_map.get(i, 1)) for i in range(len(case_items))]
        except Exception as e:
            print(f"    case {ci}: flash-3.5 failed ({e}), using fallback scores")
            scores = [0.0] * len(case_items)
        results.append(scores)
        time.sleep(0.2)
    return results


SCORERS = {
    "bi-encoder": score_bi_encoder,
    "cross-encoder": score_cross_encoder,
    "flash-lite": score_flash_lite,
    "flash-35": score_flash_35,
    "cohere": score_cohere,
}


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def _rank_relevances(items: list[dict], scores: list[float]) -> list[int]:
    """Rank items by scores descending, return relevance labels in ranked order."""
    ranked = sorted(range(len(items)), key=lambda i: scores[i], reverse=True)
    return [items[i]["relevance"] for i in ranked]


def evaluate(
    cases: list[dict],
    all_items: list[list[dict]],
    method_scores: dict[str, list[list[float]]],
    ks: list[int],
) -> dict[str, dict]:
    methods = list(method_scores.keys())

    header = f"{'Case':>4}  {'Role':>13}  {'Phase':>16}  {'n':>3}"
    for m in methods:
        abbr = m[:7]
        for k in ks:
            header += f"  {abbr + '@' + str(k):>12}"
    print(header)
    print("-" * len(header))

    agg = {
        m: {f"@{k}": [] for k in ks}
        for m in methods
    }
    role_agg: dict[str, dict[str, dict[str, list]]] = defaultdict(
        lambda: {m: {f"@{k}": [] for k in ks} for m in methods}
    )

    for ci, (case, items) in enumerate(zip(cases, all_items)):
        idx = case["case_index"]
        role = case["player_role"]
        phase = case["action_phase"]
        line = f"{idx:4d}  {role:>13}  {phase:>16}  {len(items):3d}"

        for m in methods:
            rels = _rank_relevances(items, method_scores[m][ci])
            for k in ks:
                val = ndcg_at_k(rels, k)
                agg[m][f"@{k}"].append(val)
                role_agg[role][m][f"@{k}"].append(val)
                line += f"  {val:12.3f}"
        print(line)

    print("-" * len(header))
    mean_line = f"{'MEAN':>4}  {'':>13}  {'':>16}  {'':>3}"
    for m in methods:
        for k in ks:
            vals = agg[m][f"@{k}"]
            mean_line += f"  {sum(vals) / len(vals):12.3f}"
    print(mean_line)

    print()
    print("Bootstrap 95% CIs:")
    rng = random.Random(42)
    for m in methods:
        parts = []
        for k in ks:
            vals = agg[m][f"@{k}"]
            boots = []
            for _ in range(10000):
                sample = [vals[rng.randint(0, len(vals) - 1)] for _ in range(len(vals))]
                boots.append(sum(sample) / len(sample))
            boots.sort()
            lo = boots[int(0.025 * len(boots))]
            hi = boots[int(0.975 * len(boots))]
            parts.append(f"@{k}={sum(vals)/len(vals):.3f} [{lo:.3f}, {hi:.3f}]")
        print(f"  {m:>15}: {'  '.join(parts)}")

    print()
    print("Per-role means:")
    for role in sorted(role_agg.keys()):
        line = f"  {role:>13}"
        for m in methods:
            for k in ks:
                vals = role_agg[role][m][f"@{k}"]
                line += f"  {m[:7]}@{k}={sum(vals) / len(vals):.3f}"
        print(line)

    return agg


def _load_split_cases(split: str) -> set[int] | None:
    if split == "all":
        return None
    if not SPLIT_PATH.exists():
        raise FileNotFoundError(
            f"Split manifest not found: {SPLIT_PATH}\n"
            "Run: poetry run python evidence/fine_tuning/cross_encoder/generate_split.py"
        )
    with open(SPLIT_PATH) as f:
        manifest = json.load(f)
    if split not in manifest:
        raise ValueError(f"Unknown split '{split}'. Choose from: train, val, test, all")
    return set(manifest[split])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare reranker methods on golden retrieval labels via NDCG@k",
    )
    parser.add_argument(
        "--methods", nargs="+", default=["bi-encoder", "cross-encoder", "flash-lite"],
    )
    parser.add_argument("--include-cohere", action="store_true")
    parser.add_argument("--k", type=int, nargs="+", default=[3, 5])
    parser.add_argument(
        "--split", default="test", choices=["train", "val", "test", "all"],
        help="Which split to evaluate (default: test)",
    )
    parser.add_argument("--cases", type=int, nargs="+", help="Override: specific case indices")
    parser.add_argument("--save-scores", type=Path, help="Save raw scores to JSON")
    args = parser.parse_args()

    if args.split == "all" and not args.cases:
        print("=" * 60)
        print("WARNING: Evaluating on ALL data including training set")
        print("  Metrics are NOT comparable to held-out evaluation")
        print("=" * 60)
        print()

    methods = list(args.methods)
    if args.include_cohere and "cohere" not in methods:
        methods.append("cohere")

    with open(GOLDEN_LABELS_PATH) as f:
        data = json.load(f)

    cases = sorted(data["labels"], key=lambda c: c["case_index"])
    if args.cases:
        cases = [c for c in cases if c["case_index"] in args.cases]
    else:
        split_cases = _load_split_cases(args.split)
        if split_cases is not None:
            cases = [c for c in cases if c["case_index"] in split_cases]

    key_to_item = _load_memory_texts()
    all_items = [build_case_items(c, key_to_item) for c in cases]
    total_items = sum(len(items) for items in all_items)

    print(f"Evaluating {len(cases)} cases ({total_items} items) with methods: {methods}")
    print(f"Split: {args.split}  |  NDCG@k for k={args.k}")
    print()

    method_scores: dict[str, list[list[float]]] = {}
    for m in methods:
        print(f"Scoring with {m}...", flush=True)
        t0 = time.time()
        method_scores[m] = SCORERS[m](all_items)
        elapsed = time.time() - t0
        print(f"  done in {elapsed:.1f}s ({total_items / elapsed:.0f} items/s)")
    print()

    evaluate(cases, all_items, method_scores, args.k)

    if args.save_scores:
        save_data = {
            "cases": [c["case_index"] for c in cases],
            "methods": methods,
            "ks": args.k,
            "scores": {
                m: method_scores[m] for m in methods
            },
        }
        args.save_scores.parent.mkdir(parents=True, exist_ok=True)
        with open(args.save_scores, "w") as f:
            json.dump(save_data, f, indent=2)
        print(f"\nScores saved to {args.save_scores}")


if __name__ == "__main__":
    main()
