"""Deterministic sampling helpers for building compact eval datasets."""

from __future__ import annotations

import random
from collections.abc import Iterable

from Agents.schemas.evaluation import EvalCase


# Every action phase that emits a sampleable EvalCase. Night roles (wolf kill-vote,
# healer, investigator, SK, vigilante) all funnel through one runner that stamps
# "night_action"; day discussion/vote stamp their own phase.
KNOWN_ACTION_PHASES = frozenset({"day_discussion", "day_vote", "night_action"})

# What sample_cases selects when a caller passes no action_phases. Day-only by
# default so existing frozen day sets stay reproducible; night actions are opt-in
# via the action_phases knob (in scope for Phase B labeling on v5).
DEFAULT_ACTION_PHASES = frozenset({"day_discussion", "day_vote"})


def classify_game_phase(day: int, game_length: int) -> str:
    if game_length <= 2:
        return "early"
    midpoint = game_length / 2
    return "early" if day <= midpoint else "late"


def sample_cases(
    cases: list[EvalCase],
    game_lengths: dict[str, int],
    games_to_sample: list[str] | None = None,
    per_role_per_phase: int = 1,
    max_samples: int | None = None,
    seed: int = 0,
    action_phases: Iterable[str] | None = None,
) -> list[EvalCase]:
    """
    Stratified sampling per game, role, game phase, and action type.

    Discussion retrievals and vote retrievals are represented separately.
    ``action_phases`` selects which action types are eligible (defaults to
    day-only; pass "night_action" to include night decisions). If max_samples is
    set, cap via round-robin over buckets to keep as much diversity as possible.
    Selection is deterministic for a given seed.
    """
    selected_phases = (
        frozenset(action_phases) if action_phases else DEFAULT_ACTION_PHASES
    )
    unknown = selected_phases - KNOWN_ACTION_PHASES
    if unknown:
        raise ValueError(
            f"Unknown action_phases {sorted(unknown)}; "
            f"choose from {sorted(KNOWN_ACTION_PHASES)}."
        )

    buckets: dict[tuple[str, str, str, str], list[EvalCase]] = {}

    memory_disabled_dropped = 0
    phase_excluded_dropped = 0
    for case in cases:
        if not case.memory_enabled:
            memory_disabled_dropped += 1
            continue
        if games_to_sample and case.trace_id not in games_to_sample:
            continue

        if not case.player_role or not case.day:
            continue

        if case.action_phase not in selected_phases:
            phase_excluded_dropped += 1
            continue
        phase = classify_game_phase(case.day, game_lengths.get(case.trace_id, 3))
        buckets.setdefault(
            (case.trace_id, case.player_role, phase, case.action_phase),
            [],
        ).append(case)

    if memory_disabled_dropped:
        print(
            f"Note: dropped {memory_disabled_dropped} memory-disabled case(s) — "
            "this sampler feeds the memory-pipeline evals, which need retrieval "
            "context to judge (memory-off games yield 0 samples by design)."
        )
    if phase_excluded_dropped:
        print(
            f"Note: dropped {phase_excluded_dropped} case(s) whose action_phase is "
            f"outside the selected set {sorted(selected_phases)} (set action_phases "
            "to include them, e.g. add 'night_action')."
        )

    rng = random.Random(seed)
    samples_by_bucket: list[list[EvalCase]] = []
    for key in sorted(buckets):
        spans = buckets[key].copy()
        rng.shuffle(spans)
        samples_by_bucket.append(spans[: min(per_role_per_phase, len(spans))])

    total_samples = sum(len(spans) for spans in samples_by_bucket)
    if max_samples is None or total_samples <= max_samples:
        return [span for spans in samples_by_bucket for span in spans]

    sampled: list[EvalCase] = []
    while len(sampled) < max_samples and any(samples_by_bucket):
        for spans in samples_by_bucket:
            if not spans:
                continue
            sampled.append(spans.pop(0))
            if len(sampled) >= max_samples:
                break
    return sampled


def print_sample_plan(
    sampled: list[EvalCase],
    game_lengths: dict[str, int],
) -> None:
    for case in sampled:
        phase = classify_game_phase(case.day, game_lengths.get(case.trace_id, 3))
        print(
            f"  {case.span_name} | role={case.player_role} | "
            f"day={case.day} | phase={phase} | "
            f"action={case.action_phase} | "
            f"trace={case.trace_id[:8]}..."
        )
