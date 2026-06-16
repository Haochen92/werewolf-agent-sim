"""Strategy-point SYNTHESIS — the `cluster_synth` sp_source.

Distils generalized strategy points from CLUSTERS of observations in a deduped v6 store, rather than
extracting them per game. Reuses batch_deduplication's clustering primitives but partitions by
``gate_key`` ONLY (situation regime — is_swing + alive-bucket + consensus_direction), deliberately NOT
the net_verdict pair-check, so each cluster spans MIXED outcomes; the outcome spread is the weighting
signal the synthesis LLM uses ("this move worked across N instances" vs "mostly backfired → corrective").

This is the SP path that justifies SPs existing (generalization across games); the per_run path
(reextract_cells --with-sp) is the cheap single-game baseline. Offline store-build tooling — the
offline runner is evaluation/src/experiments/synthesize_cell_sp.py.
"""

from __future__ import annotations

from collections import defaultdict
from logging import getLogger
from typing import Any

from langgraph.store.base import BaseStore
from pydantic import BaseModel, Field, create_model

from Agents.llm_factory import get_llm_pro, get_llm_pro_backup
from Agents.memory.batch_deduplication.clustering import (
    _build_clusters_for_items,
    _fetch_namespace_items,
)
from Agents.memory.dedup_gate import gate_key, situation_for_dedup
from Agents.prompts.cell_prompt import dimension_menu
from Agents.prompts.extraction import CELL_SP_SYNTHESIS_PROMPT
from Agents.schemas.memory import cell_strategy_schema_for

logger = getLogger(__name__)


def cluster_observations_for_synth(
    store: BaseStore, namespace: tuple[str, str, str], config,
) -> tuple[dict[str, Any], list[list[str]]]:
    """Observation clusters for SP synthesis: partition by gate_key (situation regime, verdict-agnostic
    so a cluster spans mixed outcomes), then agglomerate within each partition with the shared
    clustering primitives. Returns (items_by_key, clusters)."""
    items = _fetch_namespace_items(store, namespace)
    partitions: dict[Any, dict[str, Any]] = defaultdict(dict)
    for key, item in items.items():
        partitions[gate_key(item.value)][key] = item
    clusters: list[list[str]] = []
    for part in partitions.values():
        clusters.extend(_build_clusters_for_items(store, namespace, part, config))
    return items, clusters


def _format_cluster(cluster_keys: list[str], items_by_key: dict[str, Any]) -> str:
    """Render a cluster's observations for the synthesis prompt — situation residual + approach +
    outcome, each tagged with its net_verdict so the LLM can weight by the outcome spread."""
    lines: list[str] = []
    for i, key in enumerate(cluster_keys, 1):
        v = items_by_key[key].value
        situation = situation_for_dedup(v.get("dimensions", {}), v.get("situation", ""))
        lines.append(f"[{i}] (outcome: {v.get('net_verdict', '?')})")
        lines.append(f"situation: {situation}")
        lines.append(f"approach: {v.get('approach', '')}")
        lines.append(f"outcome: {v.get('outcome', '')}")
        lines.append("")
    return "\n".join(lines).strip()


def _sp_container(sp_schema: type[BaseModel]) -> type[BaseModel]:
    return create_model(
        f"{sp_schema.__name__}Synthesis",
        __base__=BaseModel,
        strategy_points=(list[sp_schema], Field(description="Synthesized strategy points for this cluster.")),
    )


def synthesize_cluster_sps(
    role: str,
    action_phase: str,
    cluster_keys: list[str],
    items_by_key: dict[str, Any],
    *,
    max_retries: int = 2,
) -> list:
    """Synthesize 1-N strategy points from one observation cluster. Returns SP cell objects (their
    action_phase is set by the model within the cell's allowed phases)."""
    sp_schema = cell_strategy_schema_for(role, action_phase)
    if sp_schema is None:
        return []
    container = _sp_container(sp_schema)
    prompt = CELL_SP_SYNTHESIS_PROMPT.format(
        role=role,
        phase=action_phase,
        observations=_format_cluster(cluster_keys, items_by_key),
        dimension_menu=dimension_menu(sp_schema),
    )
    run = f"sp_synth_{role}_{action_phase}"
    for label, llm in (("primary", get_llm_pro()), ("backup", get_llm_pro_backup())):
        chain = llm.with_structured_output(container)
        for attempt in range(max_retries + 1):
            try:
                res = chain.invoke(prompt, config={"run_name": f"{run}_{label}"})
                if isinstance(res, dict):
                    res = container.model_validate(res)
                return list(res.strategy_points)
            except Exception as e:  # noqa: BLE001
                logger.warning("%s %s attempt %s failed: %s", run, label, attempt + 1, e)
    return []
