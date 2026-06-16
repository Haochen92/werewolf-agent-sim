"""Plain-text/dict formatting of store search results for dedup prompts and tracing."""

# ---------------------------------------------------------------------------
# v6 structured-residual situation display
# ---------------------------------------------------------------------------
# The LLM should judge only the FREE-TEXT residual within an already-gated bucket — never re-reason the
# fields the structured gate already decided. So the situation shown to the dedup LLM is the non-gated
# dimension fields, field-by-field (not the composed prose blob). Hidden = the gated structured fields
# + their prose echoes (criticality_stakes, consensus_text) + routing + the approach/outcome (own slots).
_SITUATION_HIDE = frozenset({
    "players_alive", "distance_to_parity", "is_swing", "consensus_direction", "net_verdict",
    "criticality_stakes", "consensus_text", "perspective", "action_phase",
    "approach", "impact_on_final_game_outcome", "immediate_response", "outcome",
})
# A v6 entry is one carrying these dimension fields; absent them, fall back to the composed prose.
_V6_MARKERS = ("information_landscape", "my_position", "target_landscape", "heat_now", "forward_exposure")


def _residual_situation(dims: dict) -> str:
    """Non-gated situation dimensions, field-by-field, with readable labels."""
    lines = []
    for key, value in dims.items():
        if key in _SITUATION_HIDE or not value:
            continue
        lines.append(f"{key.replace('_', ' ')}: {value}")
    return "\n".join(lines)


def _situation_for_dedup(dims: dict, fallback: str) -> str:
    """Structured residual when the entry has v6 dimensions; else the composed prose (v5 / pre-dims)."""
    if not any(dims.get(m) for m in _V6_MARKERS):
        return fallback
    return _residual_situation(dims)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialize_candidates(items: list) -> list[dict]:
    """Serialize store search results into plain dicts for tracing."""
    result = []
    for i, item in enumerate(items, 1):
        value = item.value
        candidate: dict = {
            "candidate_number": i,
            "key": item.key,
            "similarity": round(item.score or 0.0, 4),
            "observation_count": value.get("observation_count", 1),
            "situation": value.get("situation", ""),
        }
        if "action" in value:
            candidate["action"] = value["action"]
        if "approach" in value:
            candidate["approach"] = value["approach"]
        if "outcome" in value:
            candidate["outcome"] = value["outcome"]
        result.append(candidate)
    return result


def _format_existing_entries(items: list) -> str:
    if not items:
        return "(none)"
    lines = []
    for i, item in enumerate(items, 1):
        value = item.value
        lines.append(
            f"[{i}] Candidate: {i}; Key: {item.key} "
            f"(similarity={item.score:.3f}, observed={value.get('observation_count', 1)}x)\n"
            f"    Action: {value.get('action', '')}\n"
            f"    Situation: {value.get('situation', '')}"
        )
    return "\n\n".join(lines)


def _format_existing_observations(items: list) -> str:
    if not items:
        return "(none)"
    lines = []
    for i, item in enumerate(items, 1):
        value = item.value
        situation = _situation_for_dedup(value.get("dimensions", {}), value.get("situation", ""))
        lines.append(
            f"[{i}] Candidate: {i}; Key: {item.key} "
            f"(similarity={item.score:.3f}, observed={value.get('observation_count', 1)}x)\n"
            f"    Situation: {situation}\n"
            f"    Approach: {value.get('approach', '')}\n"
            f"    Outcome: {value.get('outcome', '')}"
        )
    return "\n\n".join(lines)
