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


# Hard pair-checks applied WITHIN a gate bucket (DEDUP only — never retrieval): if two obs disagree on
# any of these, they are never a duplicate (no LLM). Unlike the partition key, pair-checks add precision
# WITHOUT multiplying buckets, so the genuinely playbook-invalidating dims live here:
#   net_verdict          — the positive/negative contrast IS the lesson
#   info_landscape_class — a behavioral-read lesson doesn't transfer to an info-rich board, and vice versa
#   exposure_class       — safe-in-the-majority vs primary-target is a different playbook
_PAIRCHECK_FIELDS = ("net_verdict", "info_landscape_class", "exposure_class")


def compatible(a: Any, b: Any) -> bool:
    """Dedup-compatible only if a and b agree on every pair-check field that BOTH carry. A missing field
    (legacy/v5, or a cell that lacks it) imposes no constraint."""
    for field in _PAIRCHECK_FIELDS:
        va, vb = _read(a, field), _read(b, field)
        if va is not None and vb is not None and va != vb:
            return False
    return True


def same_verdict(a: Any, b: Any) -> bool:
    """The verdict-only pair-check (different net_verdict => never a duplicate). Kept for callers/tests
    that want just the verdict rule; `compatible` is the full pair-check used by the gate."""
    va, vb = _read(a, "net_verdict"), _read(b, "net_verdict")
    return va is None or vb is None or va == vb


# ── Structured-residual situation display (shared by per-game and batch dedup) ──
# The LLM judging dedup should see ONLY the non-gated free-text residual — never re-reason a field the
# gate already decided. So `situation_for_dedup` shows the non-gated situation dims field-by-field (the
# `_SITUATION_HIDE` set strips the gated structured fields + their prose echoes + routing + the
# approach/outcome which have their own slots). Falls back to the composed prose for v5 / pre-dimensions.
_SITUATION_HIDE = frozenset({
    "players_alive", "distance_to_parity", "is_swing", "consensus_direction", "net_verdict",
    "info_landscape_class", "exposure_class",  # coarse gate enums — the gate decides them
    "criticality_stakes", "consensus_text", "perspective", "action_phase",
    "approach", "impact_on_final_game_outcome", "immediate_response", "outcome",
})
_V6_MARKERS = ("information_landscape", "my_position", "target_landscape", "heat_now", "forward_exposure")


def residual_situation(dims: dict) -> str:
    """Non-gated situation dimensions, field-by-field, with readable labels."""
    lines = []
    for key, value in dims.items():
        if key in _SITUATION_HIDE or not value:
            continue
        lines.append(f"{key.replace('_', ' ')}: {value}")
    return "\n".join(lines)


def situation_for_dedup(dims: dict, fallback: str) -> str:
    """Structured residual when the entry has v6 dimensions; else the composed prose (v5 / pre-dims)."""
    if not any(dims.get(m) for m in _V6_MARKERS):
        return fallback
    return residual_situation(dims)


def batch_partition_key(obs: Any) -> tuple | None:
    """Full DEDUP partition for the batch / system-wide pass: the gate_key PLUS the pair-check fields,
    so every cluster the LLM resolves is fully homogeneous (same regime AND same verdict/landscape/
    exposure). Used to pre-partition before clustering (vs the per-game path, which partitions on
    gate_key and applies the pair-checks as edge filters — equivalent homogeneity, simpler here).
    None if the obs has no v6 fields (no gating)."""
    base = gate_key(obs)
    if base is None:
        return None
    return base + tuple(_read(obs, field) for field in _PAIRCHECK_FIELDS)


def gate_filter(item: Any, candidates: list[Any]) -> list[Any]:
    """Narrow cosine candidates to the item's gate bucket AND the hard pair-checks, so dedup only ever
    compares already-homogeneous entries. No-op when the item has no v6 fields (gate_key None).
    Candidates are store search-items (read via `.value`) or plain dicts/objects. DEDUP path only."""
    key = gate_key(item)
    if key is None:
        return candidates
    kept = []
    for c in candidates:
        value = getattr(c, "value", c)
        if gate_key(value) == key and compatible(item, value):
            kept.append(c)
    return kept
