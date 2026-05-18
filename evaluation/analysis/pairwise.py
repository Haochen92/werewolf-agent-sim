from __future__ import annotations

from typing import Any


def ordered_outputs(
    *,
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    index: int,
    alternate_order: bool,
) -> tuple[bool, str, dict[str, Any], str, dict[str, Any]]:
    """Return A/B presentation order for a pairwise comparison."""
    swapped = bool(alternate_order and index % 2 == 1)
    if swapped:
        return swapped, "candidate", candidate, "baseline", baseline
    return swapped, "baseline", baseline, "candidate", candidate


def map_judge_winner(
    winner: str,
    *,
    output_a_name: str,
    output_b_name: str,
) -> str:
    if winner == "tie":
        return "tie"
    return output_a_name if winner == "a" else output_b_name


def quality_delta(winner: str) -> int:
    if winner == "candidate":
        return 1
    if winner == "baseline":
        return -1
    return 0


def cost_savings_pct(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
) -> float | None:
    baseline_cost = baseline.get("cost", {}).get("estimated_cost_usd")
    candidate_cost = candidate.get("cost", {}).get("estimated_cost_usd")
    if baseline_cost in (None, 0) or candidate_cost is None:
        return None
    return 1 - (candidate_cost / baseline_cost)


def summarize_pairwise_results(
    results: list[dict[str, Any]],
    *,
    title: str = "PAIRWISE SUMMARY",
) -> None:
    completed = [result for result in results if "judge" in result]
    if not completed:
        print("No completed pairwise comparisons.")
        return

    winner_counts = {"baseline": 0, "candidate": 0, "tie": 0}
    savings: list[float] = []
    for result in completed:
        winner = result["judge"]["winner"]
        winner_counts[winner] = winner_counts.get(winner, 0) + 1
        savings_pct = result.get("deltas", {}).get("cost_savings_pct")
        if savings_pct is not None:
            savings.append(savings_pct)

    print(f"\n{title}")
    print(f"  Completed: {len(completed)}")
    print(
        "  Winners: "
        f"baseline={winner_counts['baseline']}, "
        f"candidate={winner_counts['candidate']}, "
        f"tie={winner_counts['tie']}"
    )
    if savings:
        avg = sum(savings) / len(savings)
        print(f"  Avg candidate cost savings: {avg:.1%}")
