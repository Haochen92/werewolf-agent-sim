"""Memory enrichment for agent payloads — the read-side of the memory system.

Extracted from agents.py during the pre-v5 refactor (structure_audit.md group B).
Given an agent's day/night payload, generates retrieval situations, applies the
per-role/per-kind gating from the runnable config, retrieves observations and
strategy points, optionally filters (dedup/MMR) and reranks them, and returns the
enriched payload plus a retrieval-metadata dict for the eval/trace record.

The gating helpers (`_memory_enabled_for_role`, `_retrieval_type_enabled`, …) are
the Phase C independent variable and are covered by
tests/test_memory_enrichment_gating.py.
"""
from .gating import (
    _filtering_enabled_for_role,
    _memory_enabled_for_role,
    _reranking_enabled_for_memory_kind,
    _retrieval_type_enabled,
    _store_dir_from_config,
)
from .situation_agent import _generate_situations_for_agent
from .pipeline import enrich_payload_with_memory

__all__ = [
    "enrich_payload_with_memory",
    "_generate_situations_for_agent",
    "_filtering_enabled_for_role",
    "_memory_enabled_for_role",
    "_reranking_enabled_for_memory_kind",
    "_retrieval_type_enabled",
    "_store_dir_from_config",
]
