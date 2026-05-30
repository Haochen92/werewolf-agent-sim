"""Evaluate cross-encoder on golden dedup cases via Modal GPU.

Scores all golden set pairs with the cross-encoder, sweeps auto-dedup
thresholds, and compares with cosine similarity baseline.

Usage:
    poetry run modal run evidence/fine_tuning/cross_encoder/dedup_prefilter/eval_modal.py \
        --run-name ce_minilm_run1
"""

from __future__ import annotations

import json
import modal

MINUTES = 60

app = modal.App("cross-encoder-eval")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "sentence-transformers>=3.0",
        "accelerate>=1.1.0",
        "numpy",
    )
)

vol = modal.Volume.from_name("cross-encoder-finetune-output", create_if_missing=True)


@app.function(
    image=image,
    gpu="T4",
    timeout=10 * MINUTES,
    secrets=[modal.Secret.from_name("huggingface")],
    volumes={"/output": vol},
)
def run_eval(
    cases_json: str,
    run_name: str,
    base_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
) -> str:
    from sentence_transformers.cross_encoder import CrossEncoder
    import numpy as np

    cases = json.loads(cases_json)
    pairs = [(c["new_sit"], c["top_sit"]) for c in cases]

    print(f"\nLoading BASE model: {base_model}")
    base_ce = CrossEncoder(base_model)
    base_scores = base_ce.predict(pairs).tolist()

    model_path = f"/output/{run_name}"
    print(f"\nLoading FINE-TUNED model: {model_path}")
    ft_ce = CrossEncoder(model_path)
    ft_scores = ft_ce.predict(pairs).tolist()

    results = []
    for i, c in enumerate(cases):
        results.append({
            **c,
            "base_score": float(base_scores[i]),
            "ft_score": float(ft_scores[i]),
        })

    return json.dumps(results)


def _sweep_thresholds(cases, score_key, label=""):
    import numpy as np

    d_scores = [c[score_key] for c in cases if c["golden_label"] == "D"]
    k_scores = [c[score_key] for c in cases if c["golden_label"] in ("K", "M", "M/K")]

    print(f"\n  Score distribution ({label}):")
    print(f"    D (duplicates):  mean={np.mean(d_scores):.4f} ± {np.std(d_scores):.4f} "
          f"min={np.min(d_scores):.4f} max={np.max(d_scores):.4f} (n={len(d_scores)})")
    print(f"    K (keep):        mean={np.mean(k_scores):.4f} ± {np.std(k_scores):.4f} "
          f"min={np.min(k_scores):.4f} max={np.max(k_scores):.4f} (n={len(k_scores)})")
    print(f"    Gap (D-K means): {np.mean(d_scores) - np.mean(k_scores):.4f}")

    best_zero_error = None
    best_one_error = None

    all_scores = [c[score_key] for c in cases]
    lo = min(all_scores) - 0.5
    hi = max(all_scores) + 0.5
    step = (hi - lo) / 40
    d_range = np.arange(lo, hi, step)
    k_range = np.arange(lo, hi, step)

    for d_thresh in d_range:
        for k_thresh in k_range:
            if k_thresh >= d_thresh:
                continue

            auto_d = auto_k = correct_d = correct_k = wrong_d = wrong_k = llm = 0
            for c in cases:
                score = c[score_key]
                label_val = c["golden_label"]
                if score >= d_thresh:
                    auto_d += 1
                    if label_val == "D":
                        correct_d += 1
                    else:
                        wrong_d += 1
                elif score < k_thresh:
                    auto_k += 1
                    if label_val in ("K", "M", "M/K"):
                        correct_k += 1
                    else:
                        wrong_k += 1
                else:
                    llm += 1

            total_auto = auto_d + auto_k
            total_wrong = wrong_d + wrong_k
            if total_auto == 0:
                continue

            auto_rate = total_auto / len(cases)
            result = {
                "d_thresh": round(float(d_thresh), 2),
                "k_thresh": round(float(k_thresh), 2),
                "auto_rate": auto_rate,
                "auto_d": auto_d, "auto_k": auto_k, "llm": llm,
                "correct_d": correct_d, "correct_k": correct_k,
                "wrong_d": wrong_d, "wrong_k": wrong_k,
                "accuracy": (correct_d + correct_k) / total_auto,
            }

            if total_wrong == 0:
                if best_zero_error is None or auto_rate > best_zero_error["auto_rate"]:
                    best_zero_error = result
            if total_wrong <= 1:
                if best_one_error is None or auto_rate > best_one_error["auto_rate"]:
                    best_one_error = result

    if best_zero_error:
        r = best_zero_error
        print(f"    BEST ZERO-ERROR: d≥{r['d_thresh']:.2f} k<{r['k_thresh']:.2f}  "
              f"auto={r['auto_rate']:.1%} ({r['auto_d']}D+{r['auto_k']}K auto, {r['llm']} LLM)")
    else:
        print(f"    No zero-error threshold found")

    if best_one_error:
        r = best_one_error
        print(f"    BEST ≤1-ERROR:  d≥{r['d_thresh']:.2f} k<{r['k_thresh']:.2f}  "
              f"auto={r['auto_rate']:.1%} ({r['auto_d']}D+{r['auto_k']}K auto, {r['llm']} LLM)  "
              f"errors={r['wrong_d']}D+{r['wrong_k']}K")

    return best_zero_error, best_one_error


def _format_entry(entry: dict, item_type: str, mode: str = "full") -> str:
    if mode == "dedup":
        if item_type == "strategy_point":
            return entry.get("action", "")
        else:
            return f"{entry.get('situation', '')} {entry.get('approach', '')} {entry.get('outcome', '')}"
    else:
        if item_type == "strategy_point":
            return f"Situation: {entry.get('situation', '')}\nAction: {entry.get('action', '')}"
        else:
            return (
                f"Situation: {entry.get('situation', '')}\n"
                f"Approach: {entry.get('approach', '')}\n"
                f"Outcome: {entry.get('outcome', '')}"
            )


@app.local_entrypoint()
def main(
    run_name: str = "ce_minilm_run1",
    base_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    dataset: str = "eval_sets/dedup_v2_sampled.jsonl",
    golden: str = "eval_sets/dedup_v2_golden_labels.json",
    text_mode: str = "dedup",
    embedding_cache: str = "evidence/dedup_golden_eval/embedding_cache.json",
):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path.cwd()))
    from evaluation.data.datasets import read_dedup_dataset

    records = read_dedup_dataset(Path(dataset))

    with open(golden) as f:
        golden_data = json.load(f)
    golden_map = {g["case_id"]: g["golden_label"] for g in golden_data["labels"]}
    golden_idx_map = {g["case_index"]: g["golden_label"] for g in golden_data["labels"]}

    emb_cache = {}
    cache_path = Path(embedding_cache)
    if cache_path.exists():
        with open(cache_path) as f:
            cached = json.load(f)
        for c in cached:
            emb_cache[c["case_id"]] = c
        print(f"Loaded {len(emb_cache)} cached embedding sims from {cache_path}")

    cases = []
    for record in records:
        label = golden_map.get(record.case_id) or golden_idx_map.get(record.dedup_case.candidates[0].model_dump().get("case_index"))
        if not label or label not in ("D", "K", "M", "M/K"):
            continue

        case = record.dedup_case
        new_entry = case.new_entry
        if not new_entry.get("situation") or not case.candidates:
            continue
        top_cand = case.candidates[0]
        if not top_cand.situation:
            continue

        top_cand_dict = top_cand.model_dump() if hasattr(top_cand, "model_dump") else top_cand

        if text_mode in ("full", "dedup"):
            new_text = _format_entry(new_entry, case.item_type, mode=text_mode)
            top_text = _format_entry(top_cand_dict, case.item_type, mode=text_mode)
        else:
            new_text = new_entry.get("situation", "")
            top_text = top_cand.situation

        cached = emb_cache.get(record.case_id, {})
        if case.item_type == "strategy_point":
            gemini_sim = cached.get("max_action_sim", 0.0)
        else:
            gemini_sim = cached.get("max_content_sim", 0.0)

        cases.append({
            "case_id": record.case_id,
            "item_type": case.item_type,
            "golden_label": label,
            "new_sit": new_text,
            "top_sit": top_text,
            "gemini_sim": gemini_sim,
        })

    print(f"Prepared {len(cases)} golden cases (text_mode={text_mode})")
    print(f"Sending to Modal for cross-encoder scoring...")

    results_json = run_eval.remote(
        cases_json=json.dumps(cases),
        run_name=run_name,
        base_model=base_model,
    )

    results = json.loads(results_json)
    import numpy as np

    print(f"\n{'='*60}")
    print("CROSS-ENCODER SCORES vs GEMINI AUTO-DEDUP SIMILARITY")
    print(f"{'='*60}")

    print(f"\n{'case_id':>45s}  {'type':>16s}  {'label':>5s}  {'gemini':>7s}  {'base_ce':>7s}  {'ft_ce':>7s}")
    print("-" * 110)
    for c in sorted(results, key=lambda x: x["ft_score"], reverse=True):
        short_id = c["case_id"][-16:]
        print(f"{short_id:>45s}  {c['item_type']:>16s}  {c['golden_label']:>5s}  "
              f"{c['gemini_sim']:7.4f}  {c['base_score']:7.4f}  {c['ft_score']:7.4f}")

    print(f"\n{'='*60}")
    print("THRESHOLD SWEEP — ALL CASES COMBINED")
    print(f"{'='*60}")

    print("\n--- Gemini field-specific sim (production auto-dedup baseline) ---")
    _sweep_thresholds(results, "gemini_sim", "Gemini")

    print("\n--- Base cross-encoder (pre-trained) ---")
    _sweep_thresholds(results, "base_score", "base CE")

    print("\n--- Fine-tuned cross-encoder ---")
    _sweep_thresholds(results, "ft_score", "fine-tuned CE")

    for itype in ("strategy_point", "observation"):
        subset = [c for c in results if c["item_type"] == itype]
        if not subset:
            continue
        print(f"\n{'='*60}")
        print(f"THRESHOLD SWEEP — {itype.upper()}")
        print(f"{'='*60}")
        print(f"\n--- Gemini ({itype}) ---")
        _sweep_thresholds(subset, "gemini_sim", f"Gemini {itype}")
        print(f"\n--- Fine-tuned CE ({itype}) ---")
        _sweep_thresholds(subset, "ft_score", f"FT CE {itype}")
