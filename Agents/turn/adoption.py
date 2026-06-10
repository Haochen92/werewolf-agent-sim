"""Strategy-adoption impact write-back.

The instrumentation the memory-impact thesis rests on: when an agent acts on
retrieved strategy points, bump ``retrieved_count`` on everything surfaced and
``used_count`` on what it adopted, and emit the per-adoption records. This is a
store WRITE (the eval read-snapshot lives in ``eval.py``).
"""

from logging import getLogger
from typing import Any

from langgraph.runtime import Runtime

from Agents.tracing import GraphContext
from Agents.schemas.memory import StrategyAdoption

logger = getLogger(__name__)


def _process_strategy_adoption(
    result: dict[str, Any] | None,
    enriched_payload: dict[str, Any],
    runtime: Runtime[GraphContext],
    *,
    player_id: str,
    role: str,
    action_phase: str,
    day: int,
    round_num: int,
) -> tuple[list[int], list[str], list[StrategyAdoption]]:
    """Record which retrieved strategy points were surfaced and adopted.

    Bumps ``retrieved_count`` on every surfaced point and ``used_count`` on the
    adopted ones, and returns ``(raw_adopted_indices, adopted_store_keys,
    strategy_adoptions)``. Shared by the day and night memory-informed paths.
    Mutates ``result`` by popping the ``_adopted_strategy_keys`` marker.
    """
    index_map = enriched_payload.get("strategy_point_index_map", {})
    raw_adopted_indices: list[int] = []
    adopted_store_keys: list[str] = []
    strategy_adoptions: list[StrategyAdoption] = []

    if not (result and index_map):
        return raw_adopted_indices, adopted_store_keys, strategy_adoptions

    raw_adopted_indices = result.pop("_adopted_strategy_keys", [])
    sp_namespace = ("strategy_points", role, action_phase)
    active_store = runtime.store
    if active_store is None:
        return raw_adopted_indices, adopted_store_keys, strategy_adoptions

    for key in index_map.values():
        item = active_store.get(sp_namespace, key)
        if item is not None:
            value = dict(item.value)
            value["retrieved_count"] = value.get("retrieved_count", 0) + 1
            active_store.put(sp_namespace, key, value, index=False)

    for idx in raw_adopted_indices:
        key = index_map.get(idx)
        if key is None:
            logger.warning(
                f"Hallucinated adoption index {idx} from {player_id} "
                f"(day={day}, round={round_num}, phase={action_phase}, "
                f"valid=[1..{len(index_map)}]), skipping"
            )
            continue
        adopted_store_keys.append(key)
        item = active_store.get(sp_namespace, key)
        if item is not None:
            value = dict(item.value)
            value["used_count"] = value.get("used_count", 0) + 1
            active_store.put(sp_namespace, key, value, index=False)

    strategy_adoptions = [
        StrategyAdoption(
            strategy_key=key,
            player_id=player_id,
            role=role,
            day=day,
            round=round_num,
            action_phase=action_phase,
        )
        for key in adopted_store_keys
    ]
    return raw_adopted_indices, adopted_store_keys, strategy_adoptions
