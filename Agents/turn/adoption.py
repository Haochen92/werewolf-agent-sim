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

logger = getLogger(__name__)


_VERDICT_COUNTERS = {
    "follow": ("follow_count", "used_count"),  # follow == used (the agent acted on the advice)
    "override": ("override_count",),
    "not_relevant": ("not_relevant_count",),
}


def _read_verdict(v: Any) -> tuple[int | None, str | None]:
    """Read (strategy_index, verdict) from a StrategyVerdict object or its dict form."""
    if isinstance(v, dict):
        return v.get("strategy_index"), v.get("verdict")
    return getattr(v, "strategy_index", None), getattr(v, "verdict", None)


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
) -> tuple[list[int], list[str]]:
    """Apply the per-strategy-point verdicts the agent emitted at this decision.

    Bumps ``retrieved_count`` on every surfaced point, then for each verdict bumps the matching tally
    (follow -> follow_count + used_count; override -> override_count; not_relevant -> not_relevant_count).
    Returns ``(followed_indices, followed_store_keys)`` — the FOLLOW verdicts. The full per-decision
    verdict record (incl. override/not_relevant) lives in the EvalCase (``strategy_verdicts`` +
    ``strategy_index_to_key``); this function's job is the store write-back. Shared by the day and night
    memory-informed paths. Mutates ``result`` by popping the ``_strategy_verdicts`` marker.
    """
    index_map = enriched_payload.get("strategy_point_index_map", {})
    followed_indices: list[int] = []
    followed_store_keys: list[str] = []

    if not (result and index_map):
        return followed_indices, followed_store_keys

    verdicts = result.pop("_strategy_verdicts", [])
    sp_namespace = ("strategy_points", role, action_phase)
    active_store = runtime.store
    if active_store is None:
        return followed_indices, followed_store_keys

    for key in index_map.values():
        item = active_store.get(sp_namespace, key)
        if item is not None:
            value = dict(item.value)
            value["retrieved_count"] = value.get("retrieved_count", 0) + 1
            active_store.put(sp_namespace, key, value, index=False)

    for verdict in verdicts:
        idx, label = _read_verdict(verdict)
        counters = _VERDICT_COUNTERS.get(label)
        key = index_map.get(idx)
        if key is None or counters is None:
            logger.warning(
                f"Bad strategy verdict (index={idx}, verdict={label}) from {player_id} "
                f"(day={day}, round={round_num}, phase={action_phase}, "
                f"valid=[1..{len(index_map)}]), skipping"
            )
            continue
        if label == "follow":
            followed_indices.append(idx)
            followed_store_keys.append(key)
        item = active_store.get(sp_namespace, key)
        if item is not None:
            value = dict(item.value)
            for counter in counters:
                value[counter] = value.get(counter, 0) + 1
            active_store.put(sp_namespace, key, value, index=False)

    return followed_indices, followed_store_keys
