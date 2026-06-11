"""Single source of truth for eval-case span names.

Producers (game-time emission sites) and the eval read side
(``evaluation/src/data/langfuse.py``) both import from here, so a rename can
never silently strand the frozen-set builders matching a stale prefix.
"""

# Observation names that start with these prefixes carry an eval case in
# their span output (under the matching ``*_case`` key).
ACTION_EVAL_SPAN_PREFIX = "agent_action_eval_"
EXTRACTION_SPAN_PREFIX = "postgame_extraction_"
DEDUP_SPAN_PREFIX = "dedup_"
DAY_SUMMARY_SPAN_PREFIX = "day_summary_eval_"

# LangChain run names of the dedup LLM calls (Agents/memory/deduplication/
# dedup_agent.py). They match DEDUP_SPAN_PREFIX but carry no dedup_case —
# a name-scoped reader must skip them.
DEDUP_LLM_RUN_NAMES = frozenset({"dedup_observation", "dedup_strategy_point"})


def action_eval_span_name(
    player_id: str, day: int, round_num: int, action_phase: str
) -> str:
    """Per-decision EvalCase span (day discussion/vote and night actions)."""
    return f"agent_action_eval_{player_id}_day_{day}_round_{round_num}_{action_phase}"


def extraction_span_name(game_id: str) -> str:
    """The parent ExtractionCase span — one per game."""
    return f"postgame_extraction_{game_id}"


def extraction_role_run_name(role: str) -> str:
    """Base run name of a per-role extraction LLM call (a ``_{label}`` suffix is
    appended per attempt, e.g. ``_primary_cached``).

    Deliberately shares EXTRACTION_SPAN_PREFIX with the parent case-span: these
    child runs nest under it in the trace, so prefix matches are AMBIGUOUS — a
    reader must select the parent structurally, not by prefix alone.
    """
    return f"postgame_extraction_{role}"


def dedup_span_name(
    item_type: str, perspective: str, action_phase: str, index: int
) -> str:
    """One DedupCase span per post-game dedup decision."""
    return f"dedup_{item_type}_{perspective}_{action_phase}_{index}"


def day_summary_span_name(game_id: str, day: int) -> str:
    """One DaySummaryCase span per discussion day."""
    return f"day_summary_eval_{game_id}_day_{day}"
