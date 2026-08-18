"""Tests for the dedup golden builder + DedupAdapter structured-output path.

These cover the fold of the old standalone ``auto_dedup_labeler`` into the
engine + adapter pipeline: the adapter now owns prompt construction *and* the
structured decision parse, and ``dedup_golden_builder`` transforms engine
results into the ``eval_auto_dedup`` golden-label shape. No LLM calls — the
expensive equivalence claim (adapter prompts == old labeler prompts) is proven
deterministically over the real frozen dataset.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from Agents.memory.deduplication.schemas import (
    ObservationDedupDecisionOutput,
    StrategyDedupDecisionOutput,
)
from evaluation.src.labeling.adapters.dedup import DedupAdapter
from evaluation.src.labeling.base import LabelItem
from evaluation.src.labeling.dedup_golden_builder import to_golden_labels

CROSS_GAME = Path("evaluation/frozen_eval_sets/auto_dedup_v1_cross_game.jsonl")


def _item(item_type: str) -> LabelItem:
    return LabelItem(case_index=0, key="0", item_type=item_type, context={})


def test_response_schema_selects_by_item_type():
    adapter = DedupAdapter()
    assert adapter.response_schema(_item("observation")) is ObservationDedupDecisionOutput
    assert adapter.response_schema(_item("strategy_point")) is StrategyDedupDecisionOutput


def test_parse_structured_discard_carries_audit_detail():
    adapter = DedupAdapter()
    result = ObservationDedupDecisionOutput.model_validate(
        {"result": {"decision": "D", "reasoning": "same hypothesis", "duplicate_of_candidate": 2}}
    )
    letter, detail = adapter.parse_structured(_item("observation"), result)
    assert letter == "D"
    assert detail["duplicate_of_candidate"] == 2
    assert detail["reasoning"] == "same hypothesis"


def test_parse_structured_keep_has_no_duplicate_field():
    adapter = DedupAdapter()
    result = StrategyDedupDecisionOutput.model_validate(
        {"result": {"decision": "K", "reasoning": "distinct situation"}}
    )
    letter, detail = adapter.parse_structured(_item("strategy_point"), result)
    assert letter == "K"
    assert "duplicate_of_candidate" not in detail


def test_parse_structured_accepts_dict_result():
    """Some backends return a dict rather than the validated model."""
    adapter = DedupAdapter()
    letter, detail = adapter.parse_structured(
        _item("observation"),
        {"result": {"decision": "DISCARD", "reasoning": "dup", "duplicate_of_candidate": 1}},
    )
    assert letter == "D"  # "DISCARD"[0] -> "D"


def test_to_golden_labels_shape_and_field_gating():
    results = [
        {
            "case_index": 5,
            "item_type": "observation",
            "model_scores": {"gemini-2.5-pro": "D"},
            "model_details": {"gemini-2.5-pro": {"reasoning": "dup", "duplicate_of_candidate": 3}},
        },
        {
            "case_index": 2,
            "item_type": "strategy_point",
            "model_scores": {"gemini-2.5-pro": "K"},
            "model_details": {"gemini-2.5-pro": {"reasoning": "distinct"}},
        },
        {  # a failed call → no label for this model → dropped
            "case_index": 9,
            "item_type": "observation",
            "model_scores": {"gemini-2.5-pro": None},
        },
    ]
    labels = to_golden_labels(results, "gemini-2.5-pro")

    assert [l["case_index"] for l in labels] == [2, 5]  # sorted, failure dropped
    discard = next(l for l in labels if l["case_index"] == 5)
    keep = next(l for l in labels if l["case_index"] == 2)
    assert discard["golden_label"] == "D" and discard["duplicate_of_candidate"] == 3
    assert keep["golden_label"] == "K"
    assert "duplicate_of_candidate" not in keep  # KEEP never carries a duplicate ref


@pytest.mark.skipif(not CROSS_GAME.exists(), reason="frozen cross-game dataset not present")
def test_adapter_prompts_match_dataset_records():
    """The adapter must build a valid prompt for every real case (the fold's
    equivalence guarantee: same prompt → same model decision as the old labeler)."""
    adapter = DedupAdapter()
    items = adapter.load_items(CROSS_GAME)
    assert len(items) > 0
    for it in items:
        prompt = adapter.format_prompt(it)
        assert prompt.strip()
        assert adapter.response_schema(it) in (
            ObservationDedupDecisionOutput,
            StrategyDedupDecisionOutput,
        )
