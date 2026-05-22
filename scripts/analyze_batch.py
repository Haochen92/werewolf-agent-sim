"""Analyze batch results and produce a summary report.

Outputs:
  --format markdown  (default) LLM-pasteable markdown to stdout
  --format json      Structured JSON to stdout
  --format both      Markdown to stdout, JSON to --json-output (default: <input>.analysis.json)

Usage:
  python scripts/analyze_batch.py batch_results/v4_action_phase.jsonl
  python scripts/analyze_batch.py batch_results/*.jsonl --format both
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


RATE_METRICS = [
    "correct_elimination_rate",
    "healer_save_rate",
    "investigator_accuracy",
    "wolf_steering_rate",
    "wolf_blending_rate",
    "wolf_dissent_rate",
    "wolf_power_role_targeting_rate",
]

NUMERIC_METRICS = [
    "game_length",
    "mislynches",
    "healer_save_count",
    "investigator_wolves_found",
    "power_roles_killed_by_wolves",
    "tie_count",
    "no_vote_count",
]

NULLABLE_NUMERIC_METRICS = [
    "investigator_found_wolf_day",
    "wolf_killed_healer_day",
    "wolf_killed_investigator_day",
]

CATEGORICAL_METRICS = [
    "winner",
    "healer_exit_method",
    "investigator_exit_method",
]


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_records(paths: list[Path]) -> list[dict]:
    records = []
    for path in paths:
        with path.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if record.get("status") != "success":
                    continue
                records.append(record)
    return records


def extract_metrics(record: dict) -> dict | None:
    if "computed_metrics" in record:
        return record["computed_metrics"]
    return None


# ---------------------------------------------------------------------------
# Statistics helpers
# ---------------------------------------------------------------------------


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    s = sorted(values)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) / 2


def _std(values: list[float]) -> float | None:
    if len(values) < 2:
        return None
    m = sum(values) / len(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))


def _fmt(value: float | None, decimals: int = 2) -> str:
    if value is None:
        return "-"
    return f"{value:.{decimals}f}"


def _pct(value: float | None) -> str:
    if value is None:
        return "-"
    return f"{value * 100:.0f}%"


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def aggregate_group(metrics_list: list[dict]) -> dict:
    n = len(metrics_list)
    agg: dict[str, Any] = {"n_games": n}

    # Win rates
    winners = [m["winner"] for m in metrics_list]
    winner_counts = Counter(winners)
    agg["win_rates"] = {
        k: round(v / n, 3) for k, v in winner_counts.items()
    }

    # Numeric metrics
    agg["numeric"] = {}
    for metric in NUMERIC_METRICS:
        values = [m[metric] for m in metrics_list if m.get(metric) is not None]
        agg["numeric"][metric] = {
            "mean": round(_mean(values), 3) if _mean(values) is not None else None,
            "median": _median(values),
            "std": round(_std(values), 3) if _std(values) is not None else None,
            "min": min(values) if values else None,
            "max": max(values) if values else None,
        }

    # Nullable numeric metrics (day values)
    agg["nullable_numeric"] = {}
    for metric in NULLABLE_NUMERIC_METRICS:
        values = [m[metric] for m in metrics_list if m.get(metric) is not None]
        agg["nullable_numeric"][metric] = {
            "mean": round(_mean(values), 3) if _mean(values) is not None else None,
            "median": _median(values),
            "n_applicable": len(values),
            "n_null": n - len(values),
        }

    # Rate metrics
    agg["rates"] = {}
    for metric in RATE_METRICS:
        values = [m[metric] for m in metrics_list if m.get(metric) is not None]
        agg["rates"][metric] = {
            "mean": round(_mean(values), 3) if _mean(values) is not None else None,
            "median": round(_median(values), 3) if _median(values) is not None else None,
            "std": round(_std(values), 3) if _std(values) is not None else None,
            "n_applicable": len(values),
            "n_null": n - len(values),
        }

    # Categorical metrics
    agg["categorical"] = {}
    for metric in CATEGORICAL_METRICS:
        values = [m[metric] for m in metrics_list if m.get(metric) is not None]
        agg["categorical"][metric] = dict(Counter(values))

    return agg


def analyze(records: list[dict]) -> dict:
    groups: dict[str, list[dict]] = defaultdict(list)
    skipped = 0

    for record in records:
        metrics = extract_metrics(record)
        if metrics is None:
            skipped += 1
            continue
        config_name = record.get("config_name", "unknown")
        groups[config_name].append(metrics)

    all_metrics = []
    for group_metrics in groups.values():
        all_metrics.extend(group_metrics)

    result: dict[str, Any] = {
        "total_games": len(all_metrics),
        "skipped_no_metrics": skipped,
        "configs": {},
    }

    if all_metrics:
        result["overall"] = aggregate_group(all_metrics)

    for config_name in sorted(groups):
        result["configs"][config_name] = aggregate_group(groups[config_name])

    return result


# ---------------------------------------------------------------------------
# Markdown output
# ---------------------------------------------------------------------------


def render_markdown(analysis: dict, file_label: str = "") -> str:
    lines: list[str] = []
    header = "Batch Analysis"
    if file_label:
        header += f": {file_label}"
    lines.append(f"# {header}")
    lines.append("")

    total = analysis["total_games"]
    skipped = analysis.get("skipped_no_metrics", 0)
    configs = analysis["configs"]
    lines.append(f"**Total games analyzed:** {total}")
    if skipped:
        lines.append(f"**Skipped (no metrics):** {skipped}")
    config_summary = ", ".join(
        f"{name} ({configs[name]['n_games']})" for name in configs
    )
    lines.append(f"**Configs:** {config_summary}")
    lines.append("")

    # Win rates table
    lines.append("## Win Rates")
    lines.append("")
    lines.append("| Config | Games | Wolf Win | Villager Win |")
    lines.append("|--------|------:|--------:|------------:|")

    if "overall" in analysis:
        ov = analysis["overall"]
        lines.append(
            f"| **Overall** | {ov['n_games']} "
            f"| {_pct(ov['win_rates'].get('wolves'))} "
            f"| {_pct(ov['win_rates'].get('villagers'))} |"
        )

    for name, group in configs.items():
        wr = group["win_rates"]
        lines.append(
            f"| {name} | {group['n_games']} "
            f"| {_pct(wr.get('wolves'))} "
            f"| {_pct(wr.get('villagers'))} |"
        )
    lines.append("")

    # Numeric metrics table
    lines.append("## Numeric Metrics (mean ± std)")
    lines.append("")
    config_names = list(configs.keys())
    header_cols = " | ".join(config_names)
    lines.append(f"| Metric | {header_cols} |")
    lines.append("|--------|" + "|".join("------:" for _ in config_names) + "|")

    for metric in NUMERIC_METRICS:
        cells = []
        for name in config_names:
            stats = configs[name]["numeric"][metric]
            m = _fmt(stats["mean"])
            s = _fmt(stats["std"])
            cells.append(f"{m} ± {s}" if s != "-" else m)
        lines.append(f"| {metric} | " + " | ".join(cells) + " |")
    lines.append("")

    # Rate metrics table
    lines.append("## Rate Metrics (mean, n applicable / total)")
    lines.append("")
    lines.append(f"| Metric | {header_cols} |")
    lines.append("|--------|" + "|".join("------:" for _ in config_names) + "|")

    for metric in RATE_METRICS:
        cells = []
        for name in config_names:
            stats = configs[name]["rates"][metric]
            m = _fmt(stats["mean"])
            na = stats["n_applicable"]
            nt = configs[name]["n_games"]
            cells.append(f"{m} ({na}/{nt})")
        lines.append(f"| {metric} | " + " | ".join(cells) + " |")
    lines.append("")

    # Nullable numeric metrics
    lines.append("## Event Timing (mean day, n applicable / total)")
    lines.append("")
    lines.append(f"| Metric | {header_cols} |")
    lines.append("|--------|" + "|".join("------:" for _ in config_names) + "|")

    for metric in NULLABLE_NUMERIC_METRICS:
        cells = []
        for name in config_names:
            stats = configs[name]["nullable_numeric"][metric]
            m = _fmt(stats["mean"], 1)
            na = stats["n_applicable"]
            nt = configs[name]["n_games"]
            cells.append(f"{m} ({na}/{nt})")
        lines.append(f"| {metric} | " + " | ".join(cells) + " |")
    lines.append("")

    # Categorical breakdowns
    lines.append("## Categorical Breakdowns")
    lines.append("")
    for metric in CATEGORICAL_METRICS:
        if metric == "winner":
            continue
        lines.append(f"### {metric}")
        lines.append("")

        all_values = set()
        for name in config_names:
            all_values.update(configs[name]["categorical"][metric].keys())
        sorted_values = sorted(all_values)

        lines.append(f"| Config | " + " | ".join(sorted_values) + " |")
        lines.append("|--------|" + "|".join("------:" for _ in sorted_values) + "|")

        for name in config_names:
            counts = configs[name]["categorical"][metric]
            nt = configs[name]["n_games"]
            cells = [f"{counts.get(v, 0)}/{nt}" for v in sorted_values]
            lines.append(f"| {name} | " + " | ".join(cells) + " |")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help="JSONL batch result file(s) to analyze.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json", "both"),
        default="markdown",
        dest="output_format",
        help="Output format (default: markdown to stdout).",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="JSON output path (used with --format json or both). Defaults to <first_input>.analysis.json.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_records(args.inputs)
    if not records:
        print("No successful records found.", file=sys.stderr)
        raise SystemExit(1)

    analysis = analyze(records)

    file_label = ", ".join(p.name for p in args.inputs)
    analysis["source_files"] = [str(p) for p in args.inputs]

    if args.output_format in ("markdown", "both"):
        print(render_markdown(analysis, file_label))

    if args.output_format == "json":
        print(json.dumps(analysis, indent=2))

    if args.output_format == "both":
        json_path = args.json_output or args.inputs[0].with_suffix(".analysis.json")
        json_path.write_text(json.dumps(analysis, indent=2) + "\n")
        print(f"JSON written to: {json_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
