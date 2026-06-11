"""Namespace augmentation: a focused re-extraction pass that deepens ONE
``(role, action_phase)`` memory namespace from an already-finished game.

The whole-game extraction (extraction_agent.py) spreads a fixed output budget
across every role and phase, so rare phases — ``day_vote``, ``night_action`` —
land few items even when the transcript holds more. This agent re-mines the same
game with a tail that pins both the role and a single phase and asks for an
exhaustive deep pass on that slice. It shares the cached ``ROLE_EXTRACTION_PREFIX``
(so a multi-cell run over one game can reuse a single prefix cache) and routes
its output through the SAME downstream dedup/dump path — augmented items are
structurally indistinguishable from main-extractor items and are policed by the
same whole-store dedup.

Targeted by design: callers name the cells to augment; this never sweeps all
roles. It is the offline counterpart to extract_postgame_per_role.
"""

from __future__ import annotations

import contextvars
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from logging import getLogger

from Agents.llm_factory import DEFAULT_PRO_MODEL, get_llm_pro, get_llm_pro_backup
from Agents.schemas import GameStrategyOutput
from Agents.schemas.roles import VALID_ACTION_PHASES_BY_ROLE

from .extraction_agent import ExtractionResult, _invoke_attempts
from .inputs import build_role_phase_extraction_tail
from .prefix_cache import create_prefix_cache

logger = getLogger(__name__)


@dataclass(frozen=True)
class AugmentTarget:
    """One ``(role, action_phase)`` namespace to deepen."""

    role: str
    phase: str

    def __post_init__(self) -> None:
        valid = VALID_ACTION_PHASES_BY_ROLE.get(self.role)
        if valid is None:
            raise ValueError(f"Unknown role: {self.role!r}")
        if self.phase not in valid:
            raise ValueError(
                f"action_phase {self.phase!r} is not valid for role {self.role!r}; "
                f"valid: {valid}"
            )

    @property
    def label(self) -> str:
        return f"{self.role}/{self.phase}"


def _filter_to_target(output: GameStrategyOutput, target: AugmentTarget) -> GameStrategyOutput:
    """Keep only items tagged with the assigned role AND phase.

    Structured-output validation already rejects phases invalid for a role, but
    the model can still tag an item with a *neighbouring valid* phase (e.g. a
    day_discussion lesson during a day_vote pass). Those belong to a different
    namespace, so drop them here rather than letting them widen the target cell.
    """
    return GameStrategyOutput(
        observations=[
            o
            for o in output.observations
            if o.perspective == target.role and o.action_phase == target.phase
        ],
        strategy_points=[
            s
            for s in output.strategy_points
            if s.perspective == target.role and s.action_phase == target.phase
        ],
    )


def augment_namespace_for_game(
    prefix: str,
    target: AugmentTarget,
    *,
    cache=None,
    max_retries: int = 2,
    backup_max_retries: int = 2,
) -> ExtractionResult | None:
    """Run the focused (role, phase) deep pass over one game's prefix.

    `prefix` is the shared role-neutral extraction prefix for the game (build it
    once with build_role_extraction_prefix). With `cache` (a Vertex prefix cache
    bound to that prefix), the primary call sends only the tail against the cache;
    the backup re-sends the full prompt. Returns the filtered ExtractionResult
    (items pinned to the target cell) or None if the call failed entirely.
    """
    tail = build_role_phase_extraction_tail(target.role, target.phase)
    full = prefix + tail
    if cache is not None:
        attempts = (
            ("primary_cached", cache.model, tail, max_retries),
            ("backup", get_llm_pro_backup(), full, backup_max_retries),
        )
    else:
        attempts = (
            ("primary", get_llm_pro(), full, max_retries),
            ("backup", get_llm_pro_backup(), full, backup_max_retries),
        )

    result = _invoke_attempts(attempts, f"namespace_augment_{target.role}_{target.phase}")
    if result is None:
        return None
    return ExtractionResult(
        output=_filter_to_target(result.output, target),
        model_used=result.model_used,
    )


def augment_game_over_targets(
    prefix: str,
    targets: tuple[AugmentTarget, ...],
    *,
    cache_prefix: bool = False,
    max_workers: int = 6,
) -> dict[AugmentTarget, GameStrategyOutput]:
    """Augment several cells of ONE game, concurrently, sharing the prefix.

    When `cache_prefix` is set and more than one cell is requested, the shared
    prefix is created as a Vertex context cache once (so the concurrent primary
    calls hit it rather than racing an implicit cache); falls back transparently
    to the full uncached prompt if caching is unavailable. Returns a map from
    target to its filtered output (cells that failed entirely are omitted).
    """
    cache = None
    if cache_prefix and len(targets) > 1:
        model_id = os.getenv("GOOGLE_GENAI_PRO_MODEL", DEFAULT_PRO_MODEL)
        cache = create_prefix_cache(prefix, model_id=model_id)

    results: dict[AugmentTarget, GameStrategyOutput] = {}
    try:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            # Snapshot the submitting thread's context so the per-cell LLM calls
            # nest under the active trace span (contextvars don't auto-propagate
            # into worker threads) — same reason as the per-role extractor.
            futures = {
                pool.submit(
                    contextvars.copy_context().run,
                    augment_namespace_for_game,
                    prefix,
                    t,
                    cache=cache,
                ): t
                for t in targets
            }
            for future in as_completed(futures):
                t = futures[future]
                try:
                    res = future.result()
                except Exception as e:  # defensive — the call already swallows errors
                    logger.warning("Namespace augment crashed for %s: %s", t.label, e)
                    res = None
                if res is not None:
                    results[t] = res.output
    finally:
        if cache is not None:
            cache.delete()

    return results
