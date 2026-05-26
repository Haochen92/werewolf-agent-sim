"""2D threshold sweeps for dedup pre-filter calibration.

SP: sweep (action_sim, situation_sim) jointly for discard/keep.
Obs: sweep content_sim for discard, field-level (approach/outcome) for keep.

Usage:
    poetry run python scripts/sweep_2d_thresholds.py \
        --cache evidence/auto_dedup/cross_game_embedding_cache.json
"""

import argparse
import json
from dataclasses import dataclass
from itertools import product
from pathlib import Path

import numpy as np


GOLDEN_D = "D"
GOLDEN_K = "K"


@dataclass
class Result2D:
    action_discard: float
    action_keep: float
    sit_discard: float
    sit_keep: float
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
    def errors(self) -> int:
        return self.wrong_auto_discard + self.wrong_auto_keep


@dataclass
class ObsFieldResult:
    content_discard: float
    field_keep: float
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
    def errors(self) -> int:
        return self.wrong_auto_discard + self.wrong_auto_keep


def sweep_sp_2d(cases, action_range, sit_range):
    sp = [c for c in cases if c["item_type"] == "strategy_point" and c.get("max_action_sim") is not None]
    if not sp:
        return []

    action_vals = np.arange(*action_range)
    sit_vals = np.arange(*sit_range)
    results = []

    for a_d, a_k in product(action_vals, action_vals):
        if a_k >= a_d:
            continue
        for s_d, s_k in product(sit_vals, sit_vals):
            if s_k >= s_d:
                continue

            r = Result2D(
                action_discard=round(float(a_d), 3),
                action_keep=round(float(a_k), 3),
                sit_discard=round(float(s_d), 3),
                sit_keep=round(float(s_k), 3),
                total=len(sp),
                auto_discard=0, auto_keep=0, llm_fallback=0,
                correct_auto_discard=0, correct_auto_keep=0,
                wrong_auto_discard=0, wrong_auto_keep=0,
            )

            for c in sp:
                a_sim = c["max_action_sim"]
                s_sim = c["situation_sim"]
                label = c["golden_label"]

                if a_sim >= a_d and s_sim >= s_d:
                    r.auto_discard += 1
                    if label == GOLDEN_D:
                        r.correct_auto_discard += 1
                    else:
                        r.wrong_auto_discard += 1
                elif a_sim < a_k or s_sim < s_k:
                    r.auto_keep += 1
                    if label in (GOLDEN_K, "M/K", "M"):
                        r.correct_auto_keep += 1
                    else:
                        r.wrong_auto_keep += 1
                else:
                    r.llm_fallback += 1

            results.append(r)

    return results


def sweep_obs_field_keep(cases, discard_range, field_range):
    obs = [c for c in cases if c["item_type"] == "observation" and c.get("max_content_sim") is not None]
    if not obs:
        return []

    discard_vals = np.arange(*discard_range)
    field_vals = np.arange(*field_range)
    results = []

    for d_thresh in discard_vals:
        for f_thresh in field_vals:
            if f_thresh >= d_thresh:
                continue

            r = ObsFieldResult(
                content_discard=round(float(d_thresh), 3),
                field_keep=round(float(f_thresh), 3),
                total=len(obs),
                auto_discard=0, auto_keep=0, llm_fallback=0,
                correct_auto_discard=0, correct_auto_keep=0,
                wrong_auto_discard=0, wrong_auto_keep=0,
            )

            for c in obs:
                content_sim = c["max_content_sim"]
                label = c["golden_label"]

                if content_sim >= d_thresh:
                    r.auto_discard += 1
                    if label == GOLDEN_D:
                        r.correct_auto_discard += 1
                    else:
                        r.wrong_auto_discard += 1
                else:
                    should_keep = False
                    for pc in c.get("per_candidate", []):
                        a_sim = pc.get("approach_sim", 1.0)
                        o_sim = pc.get("outcome_sim", 1.0)
                        if a_sim < f_thresh or o_sim < f_thresh:
                            should_keep = True
                            break

                    if should_keep:
                        r.auto_keep += 1
                        if label in (GOLDEN_K, "M/K", "M"):
                            r.correct_auto_keep += 1
                        else:
                            r.wrong_auto_keep += 1
                    else:
                        r.llm_fallback += 1

            results.append(r)

    return results


def print_sp_2d_results(results):
    zero_error = [r for r in results if r.errors == 0 and r.auto_rate > 0]
    if zero_error:
        best = max(zero_error, key=lambda r: r.auto_rate)
        print(f"\nBEST ZERO-ERROR (2D): "
              f"action_discard≥{best.action_discard:.2f} AND sit_discard≥{best.sit_discard:.2f}  |  "
              f"action_keep<{best.action_keep:.2f} OR sit_keep<{best.sit_keep:.2f}  "
              f"auto_rate={best.auto_rate:.1%}  "
              f"({best.auto_discard}D + {best.auto_keep}K auto, {best.llm_fallback} LLM)")

        # Show top-10 zero-error by auto_rate
        top = sorted(zero_error, key=lambda r: r.auto_rate, reverse=True)[:10]
        print(f"\nTOP-10 ZERO-ERROR (2D):")
        print(f"{'a_disc':>7s} {'s_disc':>7s} {'a_keep':>7s} {'s_keep':>7s} "
              f"{'auto%':>6s} {'autoD':>5s} {'autoK':>5s} {'LLM':>4s}")
        print("-" * 60)
        for r in top:
            print(f"{r.action_discard:7.2f} {r.sit_discard:7.2f} "
                  f"{r.action_keep:7.2f} {r.sit_keep:7.2f} "
                  f"{r.auto_rate:6.1%} {r.auto_discard:5d} {r.auto_keep:5d} "
                  f"{r.llm_fallback:4d}")
    else:
        print("\nNo zero-error 2D results found.")

    # Compare with 1D baseline
    one_d = [r for r in results
             if r.sit_discard <= 0.70 and r.sit_keep <= 0.70
             and r.errors == 0 and r.auto_rate > 0]
    if one_d:
        best_1d = max(one_d, key=lambda r: r.auto_rate)
        print(f"\n1D BASELINE (sit thresholds inactive): "
              f"action≥{best_1d.action_discard:.2f} / <{best_1d.action_keep:.2f}  "
              f"auto_rate={best_1d.auto_rate:.1%}")


def print_obs_field_results(results):
    zero_error = [r for r in results if r.errors == 0 and r.auto_rate > 0]
    if zero_error:
        best = max(zero_error, key=lambda r: r.auto_rate)
        print(f"\nBEST ZERO-ERROR (field-keep): "
              f"content_discard≥{best.content_discard:.2f}  |  "
              f"approach<{best.field_keep:.2f} OR outcome<{best.field_keep:.2f}  "
              f"auto_rate={best.auto_rate:.1%}  "
              f"({best.auto_discard}D + {best.auto_keep}K auto, {best.llm_fallback} LLM)")

        top = sorted(zero_error, key=lambda r: r.auto_rate, reverse=True)[:10]
        print(f"\nTOP-10 ZERO-ERROR (field-keep):")
        print(f"{'c_disc':>7s} {'f_keep':>7s} "
              f"{'auto%':>6s} {'autoD':>5s} {'autoK':>5s} {'LLM':>4s}")
        print("-" * 50)
        for r in top:
            print(f"{r.content_discard:7.2f} {r.field_keep:7.2f} "
                  f"{r.auto_rate:6.1%} {r.auto_discard:5d} {r.auto_keep:5d} "
                  f"{r.llm_fallback:4d}")
    else:
        print("\nNo zero-error field-keep results found.")

    # Compare: content_sim for both (1D baseline)
    at_most_one = [r for r in results if r.errors <= 1 and r.auto_rate > 0]
    if at_most_one:
        best_1e = max(at_most_one, key=lambda r: r.auto_rate)
        print(f"\nBEST ≤1-ERROR (field-keep): "
              f"content≥{best_1e.content_discard:.2f}  field<{best_1e.field_keep:.2f}  "
              f"auto_rate={best_1e.auto_rate:.1%}  "
              f"errors={best_1e.errors}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, required=True)
    args = parser.parse_args()

    with args.cache.open() as f:
        cases = json.load(f)

    sp_count = sum(1 for c in cases if c["item_type"] == "strategy_point")
    obs_count = sum(1 for c in cases if c["item_type"] == "observation")
    print(f"Loaded {len(cases)} cases ({sp_count} SP, {obs_count} obs)")

    # SP 2D sweep: action_sim x situation_sim
    print(f"\n{'=' * 70}")
    print("SP 2D SWEEP: action_sim × situation_sim")
    print(f"{'=' * 70}")

    sp_results = sweep_sp_2d(
        cases,
        action_range=(0.85, 0.97, 0.01),
        sit_range=(0.70, 0.92, 0.01),
    )
    print_sp_2d_results(sp_results)

    # Obs field-level keep sweep
    print(f"\n{'=' * 70}")
    print("OBS SWEEP: content_sim discard × field-level (approach/outcome) keep")
    print(f"{'=' * 70}")

    obs_results = sweep_obs_field_keep(
        cases,
        discard_range=(0.93, 0.99, 0.005),
        field_range=(0.85, 0.96, 0.005),
    )
    print_obs_field_results(obs_results)


if __name__ == "__main__":
    main()
