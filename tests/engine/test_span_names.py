"""Span-name single-source-of-truth: builders match their own prefixes, and the
known prefix collisions stay documented as tests (a scoped reader must handle them)."""

from Agents.observability import (
    ACTION_EVAL_SPAN_PREFIX,
    DAY_SUMMARY_SPAN_PREFIX,
    DEDUP_LLM_RUN_NAMES,
    DEDUP_SPAN_PREFIX,
    EXTRACTION_SPAN_PREFIX,
    action_eval_span_name,
    day_summary_span_name,
    dedup_span_name,
    extraction_role_run_name,
    extraction_span_name,
)


def test_builders_match_their_prefixes():
    assert action_eval_span_name("player_3", 2, 5, "discussion") == (
        "agent_action_eval_player_3_day_2_round_5_discussion"
    )
    assert action_eval_span_name("p", 1, 0, "night_action").startswith(
        ACTION_EVAL_SPAN_PREFIX
    )
    assert extraction_span_name("abc-123") == "postgame_extraction_abc-123"
    assert extraction_span_name("g").startswith(EXTRACTION_SPAN_PREFIX)
    assert dedup_span_name("observation", "wolf", "vote", 4) == (
        "dedup_observation_wolf_vote_4"
    )
    assert dedup_span_name("x", "y", "z", 0).startswith(DEDUP_SPAN_PREFIX)
    assert day_summary_span_name("g1", 3) == "day_summary_eval_g1_day_3"
    assert day_summary_span_name("g", 1).startswith(DAY_SUMMARY_SPAN_PREFIX)


def test_extraction_child_runs_collide_with_parent_prefix():
    # The per-role LLM runs nest under the parent case-span and share its
    # prefix — a prefix match alone CANNOT identify the parent. (The name
    # functions are even identical modulo the role/game_id slot; the live
    # child runs additionally get a `_{label}` attempt suffix.)
    assert extraction_role_run_name("wolf").startswith(EXTRACTION_SPAN_PREFIX)
    assert extraction_role_run_name("wolf") == extraction_span_name("wolf")


def test_dedup_llm_runs_collide_with_dedup_prefix():
    # The dedup LLM calls carry no dedup_case but match the prefix — a scoped
    # reader must skip exactly these names.
    for name in DEDUP_LLM_RUN_NAMES:
        assert name.startswith(DEDUP_SPAN_PREFIX)
    assert DEDUP_LLM_RUN_NAMES == {"dedup_observation", "dedup_strategy_point"}
