"""Export items for manual labeling in ChatGPT/Claude.

Generates markdown files with full context, batched by configurable size,
ready to paste into a chat interface for human labeling.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from evaluation.labeling.base import LabelingAdapter, LabelItem
from evaluation.labeling.config import ExportConfig


def export_for_manual(
    config: ExportConfig,
    adapter: LabelingAdapter,
    system_instructions: str,
    context_renderer: Callable[[LabelItem], str] | None = None,
) -> list[Path]:
    """Export labeling items as markdown batches for manual review.

    Args:
        config: Export configuration.
        adapter: Domain adapter for item formatting.
        system_instructions: Preamble text with labeling instructions and scale.
        context_renderer: Optional function to render rich context (game state etc.)
            per item. If None, uses adapter.format_for_manual().

    Returns:
        List of paths to generated batch files.
    """
    items = adapter.load_items(config.candidates_path)

    if config.cases is not None:
        items = [it for it in items if it.case_index in config.cases]

    items_by_case: dict[int, list[LabelItem]] = {}
    for item in items:
        items_by_case.setdefault(item.case_index, []).append(item)

    case_indices = sorted(items_by_case.keys())
    render = context_renderer or adapter.format_for_manual

    sections: list[tuple[int, str]] = []
    for case_idx in case_indices:
        case_items = items_by_case[case_idx]
        section_parts = [f"# Case {case_idx}"]
        section_parts.append("")

        for item in case_items:
            section_parts.append(render(item))
            section_parts.append("")

        section_parts.append(f"## Response for Case {case_idx}")
        section_parts.append("")
        section_parts.append(
            f"Rate each of the {len(case_items)} items above. JSON format:"
        )
        section_parts.append("```json")
        response_items = []
        for idx, item in enumerate(case_items, 1):
            response_items.append(
                f'  {{"idx": {idx}, "key": "{item.key[:12]}", '
                f'"type": "{item.item_type}", "relevance": _}}'
            )
        section_parts.append("[\n" + ",\n".join(response_items) + "\n]")
        section_parts.append("```")

        sections.append((case_idx, "\n".join(section_parts)))

    config.output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for batch_start in range(0, len(sections), config.batch_size):
        batch = sections[batch_start : batch_start + config.batch_size]
        batch_num = batch_start // config.batch_size + 1
        case_ids = [ci for ci, _ in batch]

        batch_text = (
            system_instructions
            + "\n\n---\n\n"
            + "\n\n---\n\n".join(s for _, s in batch)
        )
        batch_path = config.output_dir / f"batch_{batch_num:02d}.md"
        batch_path.write_text(batch_text)
        written.append(batch_path)

        n_items = sum(
            len(items_by_case[ci]) for ci in case_ids
        )
        print(
            f"  Batch {batch_num}: {len(batch)} cases, {n_items} items "
            f"→ {batch_path.name} ({batch_path.stat().st_size / 1024:.1f} KB)"
        )

    print(f"\nWrote {len(written)} batch files to {config.output_dir}")
    return written
