"""Base adapter protocol for domain-specific labeling behavior.

Each labeling task (reranker relevance, dedup decisions, etc.) subclasses
``LabelingAdapter`` to plug domain logic into the generic engine.
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class LabelItem:
    """A single item to be labeled, with its context."""

    case_index: int
    key: str
    item_type: str
    context: dict[str, Any]
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class LabelResult:
    """A single model's label for an item."""

    case_index: int
    key: str
    label: int | str | None
    model: str


@dataclass
class VoteResult:
    """Consensus outcome from multi-model voting."""

    label: int | str | None
    confidence: str
    scores: dict[str, int | str | None]


class LabelingAdapter(ABC):
    """Domain-specific adapter for the labeling pipeline.

    Subclass this to plug in a new labeling task. The engine calls these
    methods to format prompts, parse responses, and structure output.
    """

    @property
    @abstractmethod
    def label_values(self) -> list[int] | list[str]:
        """Valid label values (e.g., [0, 1, 2] or ["Keep", "Discard"])."""

    @abstractmethod
    def format_prompt(self, item: LabelItem) -> str:
        """Render the full labeling prompt for a single item."""

    @abstractmethod
    def parse_response(self, text: str) -> int | str | None:
        """Extract a label from model output text. Returns None on parse failure."""

    def response_schema(self, item: LabelItem) -> type | None:
        """Optional Pydantic schema for structured output.

        When this returns a model class, the engine calls the LLM with
        ``with_structured_output(schema)`` and routes the result through
        :meth:`parse_structured` instead of free-text :meth:`parse_response`.
        Default ``None`` keeps the free-text path, so existing adapters are
        unaffected. Per-item because the schema can depend on ``item_type``.
        """
        return None

    def parse_structured(
        self, item: LabelItem, result: Any
    ) -> tuple[int | str | None, dict[str, Any]]:
        """Extract ``(label, detail)`` from a structured-output result.

        Only called when :meth:`response_schema` returns non-None. ``detail`` is
        audit provenance (e.g. the model's reasoning) carried into the entry's
        ``model_details``; it is never used for voting (only the label is).
        """
        raise NotImplementedError

    @abstractmethod
    def item_key(self, item: LabelItem) -> str:
        """Unique string key for checkpointing and merge lookups."""

    @abstractmethod
    def load_items(self, candidates_path: Path) -> list[LabelItem]:
        """Load items to label from the candidates file."""

    @abstractmethod
    def build_output_entry(self, item: LabelItem, vote: VoteResult) -> dict[str, Any]:
        """Build a single output entry for the merged results."""

    def load_cases_metadata(self, candidates_path: Path) -> list[dict[str, Any]]:
        """Load per-case metadata (case_index, role, etc.) from candidates file.

        Default implementation extracts from the candidates JSON.
        """
        with open(candidates_path) as f:
            data = json.load(f)
        return data.get("cases", data if isinstance(data, list) else [])

    def normalize_manual_key(self, raw_key: str, key_style: str = "full",
                             truncation_length: int = 12) -> str:
        """Convert a manual label key to canonical form for matching.

        Override if the manual export uses a non-standard key format.
        """
        if key_style == "truncated":
            return raw_key[:truncation_length]
        return raw_key

    def manual_key_from_item(self, item: LabelItem,
                             key_style: str = "full",
                             truncation_length: int = 12) -> str:
        """Derive the manual-label lookup key from an item.

        For truncated keys (e.g., ChatGPT batches), returns the truncated form.
        """
        if key_style == "truncated":
            return item.key[:truncation_length]
        return item.key

    def format_for_manual(self, item: LabelItem, game_state: str | None = None) -> str:
        """Render markdown for human labeling. Override for domain-specific context."""
        lines = [f"### Item [{item.key[:12]}] ({item.item_type})"]
        for k, v in item.context.items():
            lines.append(f"**{k}:** {v}")
        return "\n".join(lines)
