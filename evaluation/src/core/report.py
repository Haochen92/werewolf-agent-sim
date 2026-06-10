"""Generate a human-readable markdown report from experiment JSONL output."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any


def _format_observation_item(item: dict[str, Any], index: int) -> str:
    obs = item.get("observation", item)
    score = item.get("score")
    score_str = f"{score:.3f}" if score is not None else "N/A"
    parts = [f"Situation: {obs.get('situation', '')}"]
    if obs.get("approach"):
        parts.append(f"Approach: {obs['approach']}")
    if obs.get("outcome"):
        parts.append(f"Outcome: {obs['outcome']}")
    return f"  [{index}] (score: {score_str}) {' | '.join(parts)}"


def _format_strategy_point_item(item: dict[str, Any], index: int) -> str:
    sp = item.get("strategy_point", item)
    score = item.get("score")
    score_str = f"{score:.3f}" if score is not None else "N/A"
    situation = sp.get("situation", "")
    action = sp.get("action", "")
    return f"  [{index}] (score: {score_str}) {situation} -> {action}"


def _format_items(item_type: str, items: list[dict[str, Any]]) -> str:
    if not items:
        return "  (none retrieved)"
    formatter = (
        _format_observation_item
        if item_type == "observations"
        else _format_strategy_point_item
    )
    return "\n".join(formatter(item, i) for i, item in enumerate(items, 1))


def _format_quality(quality: dict[str, Any] | None) -> str:
    if not quality:
        return ""
    rel = quality.get("relevance", "?")
    eff = quality.get("efficiency", "?")
    unique = quality.get("unique_lessons", "?")
    reasoning = quality.get("brief_reasoning", "")
    line = f"  Judge: relevance={rel} efficiency={eff} unique_lessons={unique}"
    if reasoning:
        line += f"\n  Reasoning: {reasoning}"
    return line


def _score_distribution(values: list[int | float]) -> str:
    counts = Counter(values)
    return ", ".join(
        f"{count}× score {score}"
        for score, count in sorted(counts.items(), reverse=True)
    )


def _stat_row(label: str, values: list[int | float]) -> str:
    if not values:
        return f"| {label} | - | - | - | - |"
    return (
        f"| {label} "
        f"| {mean(values):.2f} "
        f"| {median(values):.0f} "
        f"| {min(values)} "
        f"| {_score_distribution(values)} |"
    )


def _build_summary_stats(records: list[dict[str, Any]]) -> list[str]:
    by_group: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for r in records:
        by_group[(r["pipeline"], r["item_type"])].append(r)

    lines: list[str] = ["## Summary Statistics", ""]

    for (pipeline, item_type), group in sorted(by_group.items()):
        judged = [
            r for r in group if r.get("retrieval_quality") is not None
        ]
        lines.append(f"### {pipeline} / {item_type} (n={len(group)})")
        lines.append("")

        counts = [r["retrieved_count"] for r in group]
        lines.append(
            f"Avg retrieved: {mean(counts):.1f} | "
            f"Median: {median(counts):.0f} | "
            f"Range: {min(counts)}–{max(counts)}"
        )
        lines.append("")

        if judged:
            relevance = [r["retrieval_quality"]["relevance"] for r in judged]
            efficiency = [r["retrieval_quality"]["efficiency"] for r in judged]
            unique = [r["retrieval_quality"]["unique_lessons"] for r in judged]

            lines.append(
                "| Dimension | Mean | Median | Min | Score Distribution |"
            )
            lines.append("|---|---|---|---|---|")
            lines.append(_stat_row("Relevance", relevance))
            lines.append(_stat_row("Efficiency", efficiency))
            lines.append(_stat_row("Unique Lessons", unique))
        else:
            lines.append("(no judge scores)")

        lines.append("")

    lines.append("---")
    lines.append("")
    return lines


def generate_retrieval_report(
    jsonl_path: Path,
    dataset_path: Path | None = None,
) -> Path:
    records: list[dict[str, Any]] = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    if not records:
        report_path = jsonl_path.with_suffix(".md")
        report_path.write_text("# Retrieval Report\n\nNo records found.\n")
        return report_path

    captured_items: dict[str, dict[str, list]] = {}
    if dataset_path and dataset_path.exists():
        with open(dataset_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                ds_record = json.loads(line)
                case_id = ds_record.get("case_id", "")
                case = ds_record.get("eval_case", {})
                captured_items[case_id] = {
                    "observations": case.get("retrieved_observations", []),
                    "strategy_points": case.get("retrieved_strategy_points", []),
                }

    by_case: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        by_case[record["case_id"]].append(record)

    lines: list[str] = ["# Retrieval Experiment Report", ""]
    lines.extend(_build_summary_stats(records))

    for case_id, case_records in by_case.items():
        first = case_records[0]
        role = first.get("role", "?")
        day = first.get("day", "?")
        rnd = first.get("round", "?")
        action_phase = first.get("action_phase", "?")
        situations = first.get("situations", [])

        lines.append(f"## {role} / {action_phase} / day {day} round {rnd}")
        lines.append("")
        lines.append("**Situations:**")
        for sit in situations:
            lines.append(f"- {sit}")
        lines.append("")

        if case_id in captured_items:
            lines.append("### Captured (original game)")
            for item_type in ("observations", "strategy_points"):
                items = captured_items[case_id].get(item_type, [])
                lines.append(f"**{item_type}** ({len(items)} items):")
                lines.append(_format_items(item_type, items))
                lines.append("")

        by_pipeline: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in case_records:
            by_pipeline[(r["snapshot"], r["pipeline"])].append(r)

        for (snapshot, pipeline), pipeline_records in by_pipeline.items():
            lines.append(f"### {snapshot} / {pipeline}")
            for r in pipeline_records:
                item_type = r["item_type"]
                items = r.get("retrieved_items", [])
                pre_count = r.get("pre_pipeline_count", "?")
                lines.append(
                    f"**{item_type}** ({len(items)} items, "
                    f"{pre_count} pre-filter):"
                )
                lines.append(_format_items(item_type, items))
                quality_str = _format_quality(r.get("retrieval_quality"))
                if quality_str:
                    lines.append(quality_str)
                lines.append("")

        lines.append("---")
        lines.append("")

    report_path = jsonl_path.with_suffix(".md")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
