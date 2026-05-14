from __future__ import annotations

import random

from Agents.schemas.evaluation import EvalCase


SUPPORTED_ACTION_TYPES = {"discussion", "vote"}


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
) -> list[EvalCase]:
    """
    Stratified sampling per game, role, game phase, and action type.

    Discussion retrievals and vote retrievals are represented separately.
    If max_samples is set, cap via round-robin over buckets to keep as much
    diversity as possible. Selection is deterministic for a given seed.
    """
    buckets: dict[tuple[str, str, str, str], list[EvalCase]] = {}

    for case in cases:
        if not case.memory_enabled:
            continue
        if games_to_sample and case.trace_id not in games_to_sample:
            continue

        if not case.player_role or not case.day:
            continue

        phase = classify_game_phase(case.day, game_lengths.get(case.trace_id, 3))
        if case.action_type not in SUPPORTED_ACTION_TYPES:
            continue
        buckets.setdefault(
            (case.trace_id, case.player_role, phase, case.action_type),
            [],
        ).append(case)

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
            f"action={case.action_type} | "
            f"trace={case.trace_id[:8]}..."
        )
