"""Export items for manual labeling in ChatGPT/Claude.

Generates markdown files with full context, batched by configurable size,
ready to paste into a chat interface for human labeling.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from evaluation.src.labeling.base import LabelingAdapter, LabelItem
from evaluation.src.labeling.config import ExportConfig


def export_for_manual(
    config: ExportConfig,
    adapter: LabelingAdapter,
    system_instructions: str,
    context_renderer: Callable[[LabelItem], str] | None = None,
) -> list[Path]:
    """Export labeling items as markdown batches for manual review.

    Each case's response block asks for the adapter's ``manual_response_field``
    per item. With ``config.write_answers_template``, also writes
    ``answers_template.json`` (simple-golden shape, labels null) for the person's
    answers, in the same order as the batches.

    Blindness is the adapter's job: its ``format_for_manual`` (or the given
    ``context_renderer``) must not show any model's label for the item, or the
    person's labels can no longer be used to calibrate that model.

    Args:
        config: Export configuration, including the optional ``keys`` filter.
        adapter: Domain adapter for item formatting.
        system_instructions: Preamble text with labeling instructions and scale.
        context_renderer: Optional function to render rich context (game state etc.)
            per item. If None, uses adapter.format_for_manual().

    Returns:
        List of paths to generated batch files (the answers template is not in it).
        Raises ValueError if ``config.keys`` names a key no candidate item has.
    """
    items = adapter.load_items(config.candidates_path)

    if config.cases is not None:
        items = [it for it in items if it.case_index in config.cases]

    if config.keys is not None:
        wanted_keys = set(config.keys)
        found_keys = {item.key for item in items}
        missing_keys = sorted(wanted_keys - found_keys)
        if missing_keys:
            raise ValueError(f"Export keys not found among the candidate items: {missing_keys}")
        items = [item for item in items if item.key in wanted_keys]

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
                f'"type": "{item.item_type}", "{adapter.manual_response_field}": _}}'
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

    if config.write_answers_template:
        template_path = config.output_dir / "answers_template.json"
        template_rows = []
        for case_idx in case_indices:
            for item in items_by_case[case_idx]:
                template_rows.append(
                    {"case_index": item.case_index, "key": item.key, "label": None, "note": ""}
                )
        template = {"labeler": "owner", "labels": template_rows}
        template_path.write_text(json.dumps(template, indent=2) + "\n")
        print(f"Wrote {len(template_rows)} answer rows to {template_path}")

    return written
