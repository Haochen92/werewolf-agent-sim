"""Calibrate embedding pre-filter thresholds against golden labels.

For each golden-labeled dedup case, compute the embedding similarities that
the pre-filter would use (action sim for strategy points, content/approach/
outcome sim for observations).  Then sweep discard and keep thresholds to find
ranges that maximise golden-label agreement while minimising LLM fallback.

Usage::

    poetry run python -m evaluation.experiments.eval_auto_dedup \
        --dataset eval_sets/dedup_v2_sampled.jsonl \
        --golden eval_sets/dedup_v2_golden_labels.json

    # Save embeddings to avoid re-computing on next run
    poetry run python -m evaluation.experiments.eval_auto_dedup \
        --dataset eval_sets/dedup_v2_sampled.jsonl \
        --golden eval_sets/dedup_v2_golden_labels.json \
        --cache evidence/dedup_golden_eval/embedding_cache.json

    # Sweep with custom grid
    poetry run python -m evaluation.experiments.eval_auto_dedup \
        --dataset eval_sets/dedup_v2_sampled.jsonl \
        --golden eval_sets/dedup_v2_golden_labels.json \
        --discard-range 0.80 0.95 0.01 \
        --keep-range 0.50 0.75 0.01
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path

import numpy as np

from Agents.memory import embeddings as embedding_model
from Agents.retrieval_filters import cosine_similarity, embed_texts
from evaluation.data.datasets import (
    AutoDedupRecord,
    read_auto_dedup_dataset,
    read_dedup_dataset,
)

logger = logging.getLogger(__name__)

GOLDEN_D = "D"
GOLDEN_K = "K"
GOLDEN_M = "M"


# ---------------------------------------------------------------------------
# Embedding computation
# ---------------------------------------------------------------------------


@dataclass
class CaseEmbeddings:
    case_index: int
    case_id: str
    item_type: str
    golden_label: str
    situation_sim: float
    max_action_sim: float | None = None
    max_content_sim: float | None = None
    max_approach_sim: float | None = None
    max_outcome_sim: float | None = None
    per_candidate: list[dict] = field(default_factory=list)


def _compute_strategy_embeddings(
    new_entry: dict,
    candidates: list[dict],
    situation_sim: float,
) -> dict:
    new_action = new_entry.get("action", "")
    cand_actions = [c.get("action", "") or "" for c in candidates]

    texts = [new_action] + cand_actions
    vecs = embed_texts(texts, embedding_model)
    if len(vecs) < 2:
        return {"max_action_sim": None, "per_candidate": []}

    new_vec = vecs[0]
    per_cand = []
    max_action_sim = 0.0
    for i, cand_vec in enumerate(vecs[1:]):
        sim = cosine_similarity(new_vec, cand_vec)
        per_cand.append({
            "candidate": i + 1,
            "action_sim": round(sim, 4),
            "situation_sim": round(candidates[i].get("similarity", 0.0), 4),
        })
        max_action_sim = max(max_action_sim, sim)

    return {
        "max_action_sim": round(max_action_sim, 4),
        "per_candidate": per_cand,
    }


def _compute_observation_embeddings(
    new_entry: dict,
    candidates: list[dict],
    situation_sim: float,
) -> dict:
    new_sit = new_entry.get("situation", "")
    new_app = new_entry.get("approach", "")
    new_out = new_entry.get("outcome", "")
    new_content = f"{new_sit} {new_app} {new_out}"

    cand_contents = [
        f"{c.get('situation', '')} {c.get('approach', '')} {c.get('outcome', '')}"
        for c in candidates
    ]

    content_texts = [new_content] + cand_contents
    content_vecs = embed_texts(content_texts, embedding_model)
    if len(content_vecs) < 2:
        return {
            "max_content_sim": None,
            "max_approach_sim": None,
            "max_outcome_sim": None,
            "per_candidate": [],
        }

    new_content_vec = content_vecs[0]
    max_content_sim = 0.0
    per_cand = []

    for i, cand_vec in enumerate(content_vecs[1:]):
        sim = cosine_similarity(new_content_vec, cand_vec)
        per_cand.append({
            "candidate": i + 1,
            "content_sim": round(sim, 4),
            "situation_sim": round(candidates[i].get("similarity", 0.0), 4),
        })
        max_content_sim = max(max_content_sim, sim)

    approach_texts = [new_app] + [c.get("approach", "") or "" for c in candidates]
    outcome_texts = [new_out] + [c.get("outcome", "") or "" for c in candidates]
    approach_vecs = embed_texts(approach_texts, embedding_model)
    outcome_vecs = embed_texts(outcome_texts, embedding_model)

    max_approach_sim = 0.0
    max_outcome_sim = 0.0

    if len(approach_vecs) >= 2 and len(outcome_vecs) >= 2:
        for i in range(len(candidates)):
            a_sim = cosine_similarity(approach_vecs[0], approach_vecs[i + 1])
            o_sim = cosine_similarity(outcome_vecs[0], outcome_vecs[i + 1])
            per_cand[i]["approach_sim"] = round(a_sim, 4)
            per_cand[i]["outcome_sim"] = round(o_sim, 4)
            max_approach_sim = max(max_approach_sim, a_sim)
            max_outcome_sim = max(max_outcome_sim, o_sim)

    return {
        "max_content_sim": round(max_content_sim, 4),
        "max_approach_sim": round(max_approach_sim, 4),
        "max_outcome_sim": round(max_outcome_sim, 4),
        "per_candidate": per_cand,
    }


def _load_cases(dataset_path: Path) -> list[tuple[int, str, str, dict, list[dict]]]:
    """Load dataset in either DedupDatasetRecord or AutoDedupRecord format.

    Returns list of (case_index, case_id, item_type, new_entry, candidates_raw).
    """
    cases = []
    try:
        auto_records = read_auto_dedup_dataset(dataset_path)
        for r in auto_records:
            cases.append((
                r.case_index,
                str(r.case_index),
                r.item_type,
                r.new_entry,
                r.candidates,
            ))
        return cases
    except Exception:
        pass

    records = read_dedup_dataset(dataset_path)
    for idx, record in enumerate(records):
        case = record.dedup_case
        candidates_raw = [
            c.model_dump() if hasattr(c, "model_dump") else c
            for c in case.candidates
        ]
        cases.append((
            idx,
            record.case_id,
            case.item_type,
            case.new_entry,
            candidates_raw,
        ))
    return cases


def compute_all_embeddings(
    dataset_path: Path,
    golden_path: Path,
    cache_path: Path | None = None,
) -> list[CaseEmbeddings]:
    if cache_path and cache_path.exists():
        logger.info("Loading cached embeddings from %s", cache_path)
        with cache_path.open() as f:
            cached = json.load(f)
        return [CaseEmbeddings(**c) for c in cached]

    cases = _load_cases(dataset_path)
    with golden_path.open() as f:
        golden_data = json.load(f)

    labels_by_id = {g.get("case_id", ""): g for g in golden_data["labels"]}
    labels_by_index = {g["case_index"]: g for g in golden_data["labels"]}

    results: list[CaseEmbeddings] = []

    for case_index, case_id, item_type, new_entry, candidates_raw in cases:
        golden = labels_by_id.get(case_id) or labels_by_index.get(case_index)
        if golden is None:
            continue

        situation_sim = max(
            (c.get("similarity", 0.0) for c in candidates_raw), default=0.0,
        )

        print(
            f"[{len(results) + 1}] case={golden['case_index']} "
            f"type={item_type:16s} label={golden['golden_label']} "
            f"sit_sim={situation_sim:.3f}",
            end="",
        )

        if item_type == "strategy_point":
            emb = _compute_strategy_embeddings(
                new_entry, candidates_raw, situation_sim,
            )
            ce = CaseEmbeddings(
                case_index=golden["case_index"],
                case_id=case_id,
                item_type=item_type,
                golden_label=golden["golden_label"],
                situation_sim=round(situation_sim, 4),
                max_action_sim=emb["max_action_sim"],
                per_candidate=emb["per_candidate"],
            )
        else:
            emb = _compute_observation_embeddings(
                new_entry, candidates_raw, situation_sim,
            )
            ce = CaseEmbeddings(
                case_index=golden["case_index"],
                case_id=case_id,
                item_type=item_type,
                golden_label=golden["golden_label"],
                situation_sim=round(situation_sim, 4),
                max_content_sim=emb["max_content_sim"],
                max_approach_sim=emb["max_approach_sim"],
                max_outcome_sim=emb["max_outcome_sim"],
                per_candidate=emb["per_candidate"],
            )

        results.append(ce)
        if ce.max_action_sim is not None:
            print(f"  action_sim={ce.max_action_sim:.3f}")
        elif ce.max_content_sim is not None:
            print(
                f"  content_sim={ce.max_content_sim:.3f}"
                f"  approach_sim={ce.max_approach_sim:.3f}"
                f"  outcome_sim={ce.max_outcome_sim:.3f}"
            )
        else:
            print()

    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_path.open("w") as f:
            json.dump(
                [
                    {
                        "case_index": c.case_index,
                        "case_id": c.case_id,
                        "item_type": c.item_type,
                        "golden_label": c.golden_label,
                        "situation_sim": c.situation_sim,
                        "max_action_sim": c.max_action_sim,
                        "max_content_sim": c.max_content_sim,
                        "max_approach_sim": c.max_approach_sim,
                        "max_outcome_sim": c.max_outcome_sim,
                        "per_candidate": c.per_candidate,
                    }
                    for c in results
                ],
                f,
                indent=2,
            )
        print(f"\nCached embeddings to {cache_path}")

    return results


# ---------------------------------------------------------------------------
# Threshold sweep — strategy points
# ---------------------------------------------------------------------------


@dataclass
class ThresholdResult:
    discard_threshold: float
    keep_threshold: float
    total: int
    auto_discard: int
    auto_keep: int
    llm_fallback: int
    correct_auto_discard: int
    correct_auto_keep: int
    wrong_auto_discard: int
    wrong_auto_keep: int

    @property
    def auto_rate(self) -> float:
        return (self.auto_discard + self.auto_keep) / self.total if self.total else 0.0

    @property
    def auto_accuracy(self) -> float:
        auto = self.auto_discard + self.auto_keep
        correct = self.correct_auto_discard + self.correct_auto_keep
        return correct / auto if auto else 0.0

    @property
    def wrong_keeps_as_discard(self) -> int:
        return self.wrong_auto_discard

    @property
    def wrong_discards_as_keep(self) -> int:
        return self.wrong_auto_keep


def sweep_strategy_thresholds(
    cases: list[CaseEmbeddings],
    discard_range: tuple[float, float, float],
    keep_range: tuple[float, float, float],
) -> list[ThresholdResult]:
    sp_cases = [c for c in cases if c.item_type == "strategy_point" and c.max_action_sim is not None]
    if not sp_cases:
        return []

    discard_vals = np.arange(*discard_range)
    keep_vals = np.arange(*keep_range)
    results = []

    for d_thresh, k_thresh in product(discard_vals, keep_vals):
        if k_thresh >= d_thresh:
            continue

        r = ThresholdResult(
            discard_threshold=round(float(d_thresh), 3),
            keep_threshold=round(float(k_thresh), 3),
            total=len(sp_cases),
            auto_discard=0, auto_keep=0, llm_fallback=0,
            correct_auto_discard=0, correct_auto_keep=0,
            wrong_auto_discard=0, wrong_auto_keep=0,
        )

        for c in sp_cases:
            sim = c.max_action_sim
            if sim >= d_thresh:
                r.auto_discard += 1
                if c.golden_label == GOLDEN_D:
                    r.correct_auto_discard += 1
                else:
                    r.wrong_auto_discard += 1
            elif sim < k_thresh:
                r.auto_keep += 1
                if c.golden_label in (GOLDEN_K, GOLDEN_M, "M/K"):
                    r.correct_auto_keep += 1
                else:
                    r.wrong_auto_keep += 1
            else:
                r.llm_fallback += 1

        results.append(r)

    return results


# ---------------------------------------------------------------------------
# Threshold sweep — observations
# ---------------------------------------------------------------------------


def sweep_observation_thresholds(
    cases: list[CaseEmbeddings],
    discard_range: tuple[float, float, float],
    keep_range: tuple[float, float, float],
    keep_mode: str = "content",
) -> list[ThresholdResult]:
    """Sweep observation thresholds.

    keep_mode="content": use content_sim for both discard and keep boundaries.
    keep_mode="field": use field-level sims (approach/outcome) for auto-keep.
    """
    obs_cases = [c for c in cases if c.item_type == "observation" and c.max_content_sim is not None]
    if not obs_cases:
        return []

    discard_vals = np.arange(*discard_range)
    keep_vals = np.arange(*keep_range)
    results = []

    for d_thresh, k_thresh in product(discard_vals, keep_vals):
        if k_thresh >= d_thresh:
            continue

        r = ThresholdResult(
            discard_threshold=round(float(d_thresh), 3),
            keep_threshold=round(float(k_thresh), 3),
            total=len(obs_cases),
            auto_discard=0, auto_keep=0, llm_fallback=0,
            correct_auto_discard=0, correct_auto_keep=0,
            wrong_auto_discard=0, wrong_auto_keep=0,
        )

        for c in obs_cases:
            content_sim = c.max_content_sim
            if content_sim >= d_thresh:
                r.auto_discard += 1
                if c.golden_label == GOLDEN_D:
                    r.correct_auto_discard += 1
                else:
                    r.wrong_auto_discard += 1
            elif _obs_should_auto_keep(c, k_thresh, keep_mode):
                r.auto_keep += 1
                if c.golden_label in (GOLDEN_K, GOLDEN_M, "M/K"):
                    r.correct_auto_keep += 1
                else:
                    r.wrong_auto_keep += 1
            else:
                r.llm_fallback += 1

        results.append(r)

    return results


def _obs_should_auto_keep(
    c: CaseEmbeddings,
    threshold: float,
    mode: str = "content",
) -> bool:
    if mode == "content":
        return (c.max_content_sim or 1.0) < threshold

    if c.max_approach_sim is None or c.max_outcome_sim is None:
        return False
    for pc in c.per_candidate:
        a_sim = pc.get("approach_sim", 1.0)
        o_sim = pc.get("outcome_sim", 1.0)
        if a_sim < threshold or o_sim < threshold:
            return True
    return False


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------


def _print_distribution(cases: list[CaseEmbeddings], item_type: str) -> None:
    subset = [c for c in cases if c.item_type == item_type]
    if not subset:
        return

    print(f"\n{'=' * 70}")
    print(f"EMBEDDING SIMILARITY DISTRIBUTION — {item_type}")
    print(f"{'=' * 70}")

    if item_type == "strategy_point":
        for c in sorted(subset, key=lambda x: x.max_action_sim or 0, reverse=True):
            label_marker = "D" if c.golden_label == GOLDEN_D else "K"
            print(
                f"  case={c.case_index:3d}  label={label_marker}  "
                f"sit_sim={c.situation_sim:.3f}  action_sim={c.max_action_sim:.3f}"
            )
    else:
        for c in sorted(subset, key=lambda x: x.max_content_sim or 0, reverse=True):
            label_marker = c.golden_label[0]
            app = c.max_approach_sim if c.max_approach_sim is not None else 0
            out = c.max_outcome_sim if c.max_outcome_sim is not None else 0
            print(
                f"  case={c.case_index:3d}  label={label_marker}  "
                f"sit_sim={c.situation_sim:.3f}  content={c.max_content_sim:.3f}  "
                f"approach={app:.3f}  outcome={out:.3f}"
            )


def _find_pareto(results: list[ThresholdResult]) -> list[ThresholdResult]:
    pareto: list[ThresholdResult] = []
    for r in results:
        wrong = r.wrong_auto_discard + r.wrong_auto_keep
        auto = r.auto_discard + r.auto_keep
        if auto == 0:
            continue
        dominated = False
        for p in pareto:
            p_wrong = p.wrong_auto_discard + p.wrong_auto_keep
            p_auto = p.auto_discard + p.auto_keep
            if p_auto >= auto and p_wrong <= wrong and (p_auto > auto or p_wrong < wrong):
                dominated = True
                break
        if not dominated:
            pareto = [
                p for p in pareto
                if not (auto >= (p.auto_discard + p.auto_keep)
                        and wrong <= (p.wrong_auto_discard + p.wrong_auto_keep)
                        and (auto > (p.auto_discard + p.auto_keep)
                             or wrong < (p.wrong_auto_discard + p.wrong_auto_keep)))
            ]
            pareto.append(r)
    pareto.sort(key=lambda r: r.auto_rate, reverse=True)
    return pareto


def _print_sweep(label: str, results: list[ThresholdResult]) -> None:
    if not results:
        print(f"\nNo results for {label}")
        return

    pareto = _find_pareto(results)

    print(f"\n{'=' * 70}")
    print(f"THRESHOLD SWEEP — {label}")
    print(f"{'=' * 70}")

    zero_error = [r for r in results if r.wrong_auto_discard == 0 and r.wrong_auto_keep == 0 and r.auto_rate > 0]
    if zero_error:
        best_zero = max(zero_error, key=lambda r: r.auto_rate)
        print(f"\nBEST ZERO-ERROR: discard≥{best_zero.discard_threshold:.2f}  "
              f"keep<{best_zero.keep_threshold:.2f}  "
              f"auto_rate={best_zero.auto_rate:.1%}  "
              f"({best_zero.auto_discard}D + {best_zero.auto_keep}K auto, "
              f"{best_zero.llm_fallback} LLM)")

    at_most_one = [r for r in results if (r.wrong_auto_discard + r.wrong_auto_keep) <= 1 and r.auto_rate > 0]
    if at_most_one:
        best_one = max(at_most_one, key=lambda r: r.auto_rate)
        wrong = best_one.wrong_auto_discard + best_one.wrong_auto_keep
        print(f"BEST ≤1-ERROR:   discard≥{best_one.discard_threshold:.2f}  "
              f"keep<{best_one.keep_threshold:.2f}  "
              f"auto_rate={best_one.auto_rate:.1%}  "
              f"errors={wrong} ({best_one.wrong_auto_discard}D_wrong + {best_one.wrong_auto_keep}K_wrong)")

    print(f"\nPARETO FRONTIER (auto_rate vs errors):")
    print(f"{'discard':>8s} {'keep':>6s} {'auto%':>6s} {'autoD':>5s} {'autoK':>5s} "
          f"{'LLM':>4s} {'errD':>5s} {'errK':>5s} {'acc%':>6s}")
    print("-" * 60)
    for r in pareto[:15]:
        print(
            f"{r.discard_threshold:8.2f} {r.keep_threshold:6.2f} "
            f"{r.auto_rate:6.1%} {r.auto_discard:5d} {r.auto_keep:5d} "
            f"{r.llm_fallback:4d} {r.wrong_auto_discard:5d} {r.wrong_auto_keep:5d} "
            f"{r.auto_accuracy:6.1%}"
        )


def _print_per_case_decision(
    cases: list[CaseEmbeddings],
    item_type: str,
    discard_thresh: float,
    keep_thresh: float,
) -> None:
    subset = [c for c in cases if c.item_type == item_type]
    if not subset:
        return

    print(f"\n{'=' * 70}")
    print(f"PER-CASE DECISIONS at discard={discard_thresh:.2f} keep={keep_thresh:.2f} — {item_type}")
    print(f"{'=' * 70}")

    for c in subset:
        if item_type == "strategy_point":
            sim = c.max_action_sim or 0
            if sim >= discard_thresh:
                decision = "AUTO-D"
            elif sim < keep_thresh:
                decision = "AUTO-K"
            else:
                decision = "LLM   "
            correct = (
                (decision == "AUTO-D" and c.golden_label == GOLDEN_D)
                or (decision == "AUTO-K" and c.golden_label in (GOLDEN_K, "M/K"))
                or decision == "LLM   "
            )
            marker = "OK" if correct else "XX"
            print(
                f"  [{marker}] case={c.case_index:3d}  golden={c.golden_label}  "
                f"decision={decision}  action_sim={sim:.3f}  sit_sim={c.situation_sim:.3f}"
            )
        else:
            content_sim = c.max_content_sim or 0
            if content_sim >= discard_thresh:
                decision = "AUTO-D"
            elif _obs_should_auto_keep(c, keep_thresh, "content"):
                decision = "AUTO-K"
            else:
                decision = "LLM   "
            correct = (
                (decision == "AUTO-D" and c.golden_label == GOLDEN_D)
                or (decision == "AUTO-K" and c.golden_label in (GOLDEN_K, GOLDEN_M, "M/K"))
                or decision == "LLM   "
            )
            marker = "OK" if correct else "XX"
            app = c.max_approach_sim if c.max_approach_sim is not None else 0
            out = c.max_outcome_sim if c.max_outcome_sim is not None else 0
            print(
                f"  [{marker}] case={c.case_index:3d}  golden={c.golden_label}  "
                f"decision={decision}  content={content_sim:.3f}  "
                f"approach={app:.3f}  outcome={out:.3f}"
            )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calibrate embedding pre-filter thresholds against golden labels."
    )
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--golden", type=Path, required=True)
    parser.add_argument("--cache", type=Path, default=None)
    parser.add_argument(
        "--discard-range", nargs=3, type=float, default=[0.80, 0.96, 0.01],
        metavar=("START", "END", "STEP"),
    )
    parser.add_argument(
        "--keep-range", nargs=3, type=float, default=[0.50, 0.76, 0.01],
        metavar=("START", "END", "STEP"),
    )
    parser.add_argument(
        "--show-decisions", action="store_true",
        help="Print per-case decisions for the best Pareto point.",
    )
    parser.add_argument(
        "--obs-keep-mode", choices=["content", "field"], default="content",
        help="Observation auto-keep method: 'content' (content_sim) or 'field' (approach/outcome sims).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    cases = compute_all_embeddings(
        args.dataset, args.golden, args.cache,
    )

    _print_distribution(cases, "strategy_point")
    _print_distribution(cases, "observation")

    discard_range = tuple(args.discard_range)
    keep_range = tuple(args.keep_range)

    sp_results = sweep_strategy_thresholds(cases, discard_range, keep_range)
    _print_sweep("STRATEGY POINTS (action similarity)", sp_results)

    obs_results = sweep_observation_thresholds(
        cases, discard_range, keep_range, keep_mode=args.obs_keep_mode,
    )
    _print_sweep(f"OBSERVATIONS (content sim, keep={args.obs_keep_mode})", obs_results)

    if args.show_decisions:
        sp_zero = [r for r in sp_results if r.wrong_auto_discard == 0 and r.wrong_auto_keep == 0 and r.auto_rate > 0]
        if sp_zero:
            best = max(sp_zero, key=lambda r: r.auto_rate)
            _print_per_case_decision(cases, "strategy_point", best.discard_threshold, best.keep_threshold)

        obs_zero = [r for r in obs_results if r.wrong_auto_discard == 0 and r.wrong_auto_keep == 0 and r.auto_rate > 0]
        if obs_zero:
            best = max(obs_zero, key=lambda r: r.auto_rate)
            _print_per_case_decision(cases, "observation", best.discard_threshold, best.keep_threshold)


if __name__ == "__main__":
    main()
