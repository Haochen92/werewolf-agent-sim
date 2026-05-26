"""Run situation summary across multiple models and do pairwise judging."""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

from evaluation.components.situation_summary import run_situation_summary_variant
from evaluation.core.config_schema import JudgeConfig, VariantConfig
from evaluation.data.datasets import read_eval_dataset
from evaluation.judges.pairwise_summary import run_pairwise_summary_judge

REPO_ROOT = Path(__file__).resolve().parent.parent

MODEL_CONFIGS: dict[str, VariantConfig] = {
    "flash-lite-default": VariantConfig(
        label="flash-lite-default",
        model="gemini-3.1-flash-lite",
    ),
    "flash-lite-medium": VariantConfig(
        label="flash-lite-medium",
        model="gemini-3.1-flash-lite",
        thinking_level="medium",
    ),
    "2.5-flash": VariantConfig(
        label="2.5-flash",
        model="gemini-2.5-flash",
    ),
    "3.5-flash": VariantConfig(
        label="3.5-flash",
        model="gemini-3.5-flash",
    ),
}

JUDGE_CONFIG = JudgeConfig(
    model="gemini-3.1-pro-preview",
    prompt_id="pairwise_summary_v1",
    temperature=0.0,
)


def main():
    num_cases = int(sys.argv[1]) if len(sys.argv) > 1 else 15

    dataset_path = REPO_ROOT / "eval_sets" / "v4_filtering_eval.jsonl"
    records = read_eval_dataset(dataset_path)[:num_cases]

    print(f"Cases: {num_cases}", flush=True)
    print(f"Models: {list(MODEL_CONFIGS.keys())}", flush=True)
    print(f"Judge: {JUDGE_CONFIG.model}", flush=True)
    print("", flush=True)

    # Phase 1: Run all models on all cases
    all_outputs: dict[str, list[dict[str, Any]]] = {k: [] for k in MODEL_CONFIGS}

    for model_key, config in MODEL_CONFIGS.items():
        print(f"=== Running {model_key} ===", flush=True)
        for i, record in enumerate(records, 1):
            try:
                result = run_situation_summary_variant(record.eval_case, config)
                all_outputs[model_key].append(result)
                situations = result["situations"]
                print(
                    f"  [{i}/{num_cases}] {record.player_role} d{record.day}r{record.round} "
                    f"-> {len(situations)} situations, {result['latency_ms']}ms",
                    flush=True,
                )
            except Exception as e:
                all_outputs[model_key].append({"error": str(e), "situations": []})
                print(f"  [{i}/{num_cases}] ERROR: {e!s:.80}", flush=True)
            time.sleep(0.5)
        print("", flush=True)

    # Save raw outputs
    out_dir = REPO_ROOT / "evidence" / "situation_summary_quality" / "model_comparison"
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for model_key, outputs in all_outputs.items():
        out_file = out_dir / f"outputs_{model_key}_{timestamp}.jsonl"
        with out_file.open("w") as f:
            for j, (record, output) in enumerate(zip(records, outputs)):
                f.write(json.dumps({
                    "case_id": record.case_id,
                    "player_role": record.player_role,
                    "day": record.day,
                    "round": record.round,
                    "action_phase": record.action_phase,
                    "model": model_key,
                    **output,
                }) + "\n")
        print(f"Saved {model_key} outputs to {out_file.name}", flush=True)

    # Phase 2: Pairwise judging — current (flash-lite-default) vs each alternative
    baseline_key = "flash-lite-default"
    competitors = [k for k in MODEL_CONFIGS if k != baseline_key]

    judge_results_file = out_dir / f"judge_pairwise_{timestamp}.jsonl"
    summary: dict[str, dict[str, int]] = {}

    for comp_key in competitors:
        print(f"\n=== Judging: {baseline_key} vs {comp_key} ===", flush=True)
        wins = {"baseline": 0, "candidate": 0, "tie": 0}

        for i, record in enumerate(records):
            baseline_out = all_outputs[baseline_key][i]
            candidate_out = all_outputs[comp_key][i]

            if baseline_out.get("error") or candidate_out.get("error"):
                print(f"  [{i+1}/{num_cases}] SKIP (error in one output)", flush=True)
                continue

            # Alternate presentation order to reduce position bias
            swapped = i % 2 == 1
            if swapped:
                output_a, output_b = candidate_out, baseline_out
                a_name, b_name = "candidate", "baseline"
            else:
                output_a, output_b = baseline_out, candidate_out
                a_name, b_name = "baseline", "candidate"

            try:
                scores, meta = run_pairwise_summary_judge(
                    record, output_a, output_b, JUDGE_CONFIG
                )
                # Map judge A/B back to baseline/candidate
                if scores.winner == "tie":
                    winner = "tie"
                elif scores.winner == "a":
                    winner = a_name
                else:
                    winner = b_name

                wins[winner] += 1
                print(
                    f"  [{i+1}/{num_cases}] winner={winner} "
                    f"conf={scores.confidence} "
                    f"({scores.brief_reasoning[:60]}...)" if len(scores.brief_reasoning) > 60
                    else f"  [{i+1}/{num_cases}] winner={winner} "
                    f"conf={scores.confidence} ({scores.brief_reasoning})",
                    flush=True,
                )

                with judge_results_file.open("a") as f:
                    f.write(json.dumps({
                        "comparison": f"{baseline_key}_vs_{comp_key}",
                        "case_id": record.case_id,
                        "player_role": record.player_role,
                        "winner": winner,
                        "confidence": scores.confidence,
                        "reasoning": scores.brief_reasoning,
                        "swapped": swapped,
                        "baseline_situations": baseline_out["situations"],
                        "candidate_situations": candidate_out["situations"],
                    }) + "\n")
            except Exception as e:
                print(f"  [{i+1}/{num_cases}] JUDGE ERROR: {e!s:.80}", flush=True)

            time.sleep(1.0)

        summary[comp_key] = wins
        print(f"  Results: baseline={wins['baseline']} candidate={wins['candidate']} tie={wins['tie']}", flush=True)

    # Final summary
    print(f"\n{'='*60}", flush=True)
    print(f"SUMMARY (baseline={baseline_key})", flush=True)
    print(f"{'='*60}", flush=True)
    for comp_key, wins in summary.items():
        total = sum(wins.values())
        print(
            f"\n  vs {comp_key}: "
            f"baseline={wins['baseline']}/{total} "
            f"candidate={wins['candidate']}/{total} "
            f"tie={wins['tie']}/{total}",
            flush=True,
        )

    print(f"\nJudge results saved to {judge_results_file}", flush=True)


if __name__ == "__main__":
    main()
