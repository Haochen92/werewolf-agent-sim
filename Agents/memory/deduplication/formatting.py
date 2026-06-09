"""Plain-text/dict formatting of store search results for dedup prompts and tracing."""

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
        lines.append(
            f"[{i}] Candidate: {i}; Key: {item.key} "
            f"(similarity={item.score:.3f}, observed={value.get('observation_count', 1)}x)\n"
            f"    Situation: {value.get('situation', '')}\n"
            f"    Approach: {value.get('approach', '')}\n"
            f"    Outcome: {value.get('outcome', '')}"
        )
    return "\n\n".join(lines)
