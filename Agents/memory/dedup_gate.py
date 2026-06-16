"""Structured dedup GATE — the deterministic partition shared by both dedup paths (per-game and batch).

The point (see the dedup discussion): with v6's many dimensions, "is this a duplicate?" is not a
reliable high-dimensional LLM/cosine judgment. So the hard structured fields become a DETERMINISTIC
gate — two observations only become dedup candidates if they share a `gate_key` — which collapses the
LLM's job to the free-text residual WITHIN an already-matched bucket. `net_verdict` is a separate hard
rule (different verdict never collapses — the contrast IS the lesson), not part of the partition key
(keeping the key minimal avoids over-fragmenting).

Backward-compatible: a v5 observation has none of the v6 fields, so `gate_key` returns None and the
filter is a no-op (current behavior). Only v6 observations are gated.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _read(obs: Any, field: str) -> Any:
    """Read a field from either a stored value dict or an Observation-like object."""
    return obs.get(field) if isinstance(obs, Mapping) else getattr(obs, field, None)


def _alive_bucket(players_alive: Any) -> str:
    """Coarse criticality bucket — early/mid/late is a different playbook; finer is noise."""
    if not isinstance(players_alive, int):
        return "unknown"
    if players_alive >= 8:
        return "early"   # 8-9 alive
    if players_alive >= 5:
        return "mid"     # 5-7 alive
    return "late"        # <=4 alive (endgame)


def gate_key(obs: Any) -> tuple | None:
    """Deterministic partition key from the v6 structured fields: is_swing + alive bucket +
    consensus_direction. Returns None if `obs` carries no v6 fields (a v5 entry) — then gating is a
    no-op. net_verdict is intentionally NOT in the key (it's the separate same_verdict rule)."""
    is_swing = _read(obs, "is_swing")
    players_alive = _read(obs, "players_alive")
    consensus_direction = _read(obs, "consensus_direction")
    if is_swing is None and players_alive is None and consensus_direction is None:
        return None
    return (bool(is_swing), _alive_bucket(players_alive), consensus_direction)


def same_verdict(a: Any, b: Any) -> bool:
    """The verdict-aware rule: observations with DIFFERENT net_verdict are never duplicates (the
    positive/negative contrast is itself the lesson). Missing verdict (v5) imposes no constraint."""
    va, vb = _read(a, "net_verdict"), _read(b, "net_verdict")
    if va is None or vb is None:
        return True
    return va == vb


def gate_filter(item: Any, candidates: list[Any]) -> list[Any]:
    """Narrow cosine candidates to the item's gate bucket AND same net_verdict, so dedup only ever
    compares already-homogeneous entries. No-op when the item has no v6 fields (gate_key None).
    Candidates are store search-items (read via `.value`) or plain dicts/objects."""
    key = gate_key(item)
    if key is None:
        return candidates
    kept = []
    for c in candidates:
        value = getattr(c, "value", c)
        if gate_key(value) == key and same_verdict(item, value):
            kept.append(c)
    return kept
