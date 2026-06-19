"""Extraction agent: the post-game `llm.invoke` (primary → backup, with retries) that turns a
finished game into structured memory. Prompt construction and input formatting live in inputs.py.

Entry points:
  extract_postgame_per_cell — v6 (LIVE): fan out over (role, phase) cells concurrently, each a dual
                              {observations, strategy_points} call in the v6 cell schema, merged.
  extract_postgame_per_role — v5: fan out the six roles over a shared cacheable prefix
                              (GameStrategyOutput); kept for the offline store-builders / experiments.
  extract_postgame          — v5: single all-roles prompt (legacy / A/B baseline).
"""

from __future__ import annotations

import contextvars
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from logging import getLogger

from Agents.llm_factory import DEFAULT_PRO_MODEL, get_llm_pro, get_llm_pro_backup
from Agents.observability import extraction_role_run_name
from Agents.schemas import GameStrategyOutput
from Agents.schemas.memory import cell_dual_extraction_schema, cell_observation_schema_for

from .cell_units import ROLE_UNITS
from .inputs import (
    build_cell_extraction_prefix,
    build_cell_observation_tail,
    build_cell_strategy_tail,
    build_role_extraction_tail,
)
from .prefix_cache import create_prefix_cache

logger = getLogger(__name__)

# Fixed 9-player casting → every game contains all six role types, so the fan-out
# always covers the full set (no need to read which roles are present).
EXTRACTION_ROLES: tuple[str, ...] = (
    "villager",
    "wolf",
    "investigator",
    "healer",
    "serial_killer",
    "vigilante",
)


@dataclass
class CellExtractionOutput:
    """Merged v6 per-cell extraction: flat lists of the (heterogeneous) cell observation / strategy
    objects across every (role, phase) cell. Duck-types to GameStrategyOutput for the downstream
    dedup/store — both expose .observations / .strategy_points."""

    observations: list
    strategy_points: list


@dataclass
class ExtractionResult:
    output: GameStrategyOutput | CellExtractionOutput
    model_used: str


def _invoke_extraction_model(llm, prompt: str, run_name: str) -> GameStrategyOutput:
    result = llm.with_structured_output(GameStrategyOutput).invoke(
        prompt,
        config={"run_name": run_name},
    )
    if isinstance(result, GameStrategyOutput):
        return result

    if isinstance(result, dict):
        logger.warning(
            "Received dict instead of GameStrategyOutput, attempting to cast: %s",
            result,
        )
        return GameStrategyOutput.model_validate(result)

    raise TypeError(f"Unexpected post-game extraction result type: {type(result)!r}")


def _invoke_attempts(attempts, run_name: str) -> ExtractionResult | None:
    """Try each (label, llm, prompt, retries) attempt in order; first success wins.

    Each attempt is its own model + prompt so the primary can be a cache-bound
    model invoked with the tail only while the backup re-sends the full prompt.
    Returns an ExtractionResult (output + label) or None if all attempts fail.
    """
    for label, llm, prompt, retries in attempts:
        for attempt in range(retries + 1):
            try:
                output = _invoke_extraction_model(llm, prompt, f"{run_name}_{label}")
                return ExtractionResult(output=output, model_used=label)
            except Exception as e:
                logger.warning(
                    "%s failed with %s model on attempt %s: %s",
                    run_name,
                    label,
                    attempt + 1,
                    e,
                )
        logger.warning("%s exhausted %s model attempts.", run_name, label)

    return None


def extract_postgame(
    prompt: str,
    max_retries: int = 2,
    backup_max_retries: int = 2,
) -> ExtractionResult | None:
    """Call the extraction LLM with a pre-built single all-roles prompt.

    Returns an ExtractionResult with the output and model label, or None if
    all attempts fail.
    """
    attempts = (
        ("primary", get_llm_pro(), prompt, max_retries),
        ("backup", get_llm_pro_backup(), prompt, backup_max_retries),
    )
    return _invoke_attempts(attempts, "postgame_extraction")


def extract_postgame_per_role(
    prefix: str,
    roles: tuple[str, ...] = EXTRACTION_ROLES,
    max_workers: int = 6,
    max_retries: int = 2,
    backup_max_retries: int = 2,
    cache_prefix: bool = False,
) -> ExtractionResult | None:
    """Fan the extraction out over `roles`, concurrently, then merge.

    Each role's prompt is the shared `prefix` plus that role's lock tail — so the
    prefix is byte-identical across calls (the unit explicit caching reuses). Roles
    run concurrently on a thread pool (the calls are network-bound). A role that
    fails entirely is dropped (partial extraction beats none); the merged output
    concatenates observations and strategy points in `roles` order. Returns None
    only if every role failed.

    With `cache_prefix`, the shared prefix is created as a Vertex context cache
    once up front (so the concurrent calls all hit it rather than racing an
    implicit cache); each role's PRIMARY call then sends only its tail against the
    cache-bound model, while the BACKUP re-sends the full prompt (it runs on a
    different model that can't share the cache). If cache creation is unavailable
    or fails, this transparently falls back to the full uncached prompt.
    """
    cache = None
    if cache_prefix:
        model_id = os.getenv("GOOGLE_GENAI_PRO_MODEL", DEFAULT_PRO_MODEL)
        cache = create_prefix_cache(prefix, model_id=model_id)

    role_outputs: dict[str, GameStrategyOutput] = {}
    role_models: dict[str, str] = {}

    def _one(role: str) -> ExtractionResult | None:
        tail = build_role_extraction_tail(role)
        full = prefix + tail
        if cache is not None:
            # Primary: cached prefix + tail only. Backup: full prompt (no cache —
            # different model). Tag primary so cache hits are visible in model_used.
            attempts = (
                ("primary_cached", cache.model, tail, max_retries),
                ("backup", get_llm_pro_backup(), full, backup_max_retries),
            )
        else:
            attempts = (
                ("primary", get_llm_pro(), full, max_retries),
                ("backup", get_llm_pro_backup(), full, backup_max_retries),
            )
        return _invoke_attempts(attempts, extraction_role_run_name(role))

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            # contextvars (langchain's ambient RunnableConfig callbacks AND the active
            # Langfuse/OTEL span) don't auto-propagate into worker threads, which would
            # silently drop tracing of the per-role calls — the span survives but its
            # child generations vanish. Snapshot the submitting thread's context and run
            # each worker inside it so the generations nest under the extraction span.
            futures = {
                pool.submit(contextvars.copy_context().run, _one, role): role
                for role in roles
            }
            for future in as_completed(futures):
                role = futures[future]
                try:
                    res = future.result()
                except Exception as e:  # defensive — _one already swallows call errors
                    logger.warning("Per-role extraction crashed for %s: %s", role, e)
                    res = None
                if res is not None:
                    role_outputs[role] = res.output
                    role_models[role] = res.model_used
    finally:
        if cache is not None:
            cache.delete()

    missing = [r for r in roles if r not in role_outputs]
    if missing:
        logger.warning("Per-role extraction produced nothing for roles: %s", missing)
    if not role_outputs:
        return None

    merged = GameStrategyOutput(
        observations=[
            o for r in roles if r in role_outputs for o in role_outputs[r].observations
        ],
        strategy_points=[
            s for r in roles if r in role_outputs for s in role_outputs[r].strategy_points
        ],
    )
    used_backup = sorted(r for r, m in role_models.items() if m == "backup")
    model_used = "per_role"
    if used_backup:
        model_used += f" (backup: {','.join(used_backup)})"
    if missing:
        model_used += f" (missing: {','.join(missing)})"
    return ExtractionResult(output=merged, model_used=model_used)


def _extract_one_cell(
    prefix: str,
    role: str,
    phase_wording: str,
    rep_phase: str,
    cache,
    max_retries: int,
    backup_max_retries: int,
) -> tuple[list, list, str] | None:
    """Extract one (role, phase-group) cell as a dual {observations, strategy_points} call.

    Returns (observations, strategy_points, model_label) or None if the cell has no schema
    (e.g. villager·night) or every attempt failed. Mirrors the per-role primary→backup fallback:
    with a prefix cache the primary sends only the per-cell tail against the cache-bound model while
    the backup re-sends the full prompt (different model, can't share the cache)."""
    schema = cell_dual_extraction_schema(role, rep_phase)
    if schema is None:
        return None
    obs_schema = cell_observation_schema_for(role, rep_phase)
    tail = build_cell_observation_tail(role, phase_wording, rep_phase, obs_schema) + (
        build_cell_strategy_tail(role, phase_wording)
    )
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
    run_name = f"{extraction_role_run_name(role)}_{rep_phase}"
    for label, llm, prompt, retries in attempts:
        for attempt in range(retries + 1):
            try:
                result = llm.with_structured_output(schema).invoke(
                    prompt, config={"run_name": f"{run_name}_{label}"}
                )
                if isinstance(result, dict):
                    result = schema.model_validate(result)
                return list(result.observations), list(result.strategy_points), label
            except Exception as e:
                logger.warning(
                    "cell %s/%s failed with %s model on attempt %s: %s",
                    role, rep_phase, label, attempt + 1, e,
                )
        logger.warning("cell %s/%s exhausted %s model attempts.", role, rep_phase, label)
    return None


def extract_postgame_per_cell(
    inputs: dict[str, str],
    roles: tuple[str, ...] = EXTRACTION_ROLES,
    max_workers: int = 8,
    max_retries: int = 2,
    backup_max_retries: int = 2,
    cache_prefix: bool = False,
) -> ExtractionResult | None:
    """v6 post-game extraction: fan out over (role, phase-group) CELLS concurrently, then merge.

    The v6 successor to extract_postgame_per_role — one dual {observations, strategy_points} call per
    cell (villager·day; day+night for the other five roles = 11 cells), each producing the role/phase's
    structured v6 cell schema. The role/phase-neutral prefix is byte-identical across cells (the unit
    explicit caching reuses, exactly like the role fan-out). A cell with no schema or total failure is
    dropped (partial extraction beats none); merged output concatenates all cells' observations and
    strategy points. Returns None only if every cell produced nothing."""
    prefix = build_cell_extraction_prefix(inputs)
    cache = None
    if cache_prefix:
        model_id = os.getenv("GOOGLE_GENAI_PRO_MODEL", DEFAULT_PRO_MODEL)
        cache = create_prefix_cache(prefix, model_id=model_id)

    cells = [
        (role, group, wording, rep)
        for role in roles
        for (group, wording, rep) in ROLE_UNITS.get(role, [])
    ]
    obs_all: list = []
    sp_all: list = []
    used_backup: list[str] = []
    missing: list[str] = []

    try:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            # Snapshot the submitting thread's context so langchain's RunnableConfig callbacks and
            # the active tracing span propagate into the workers (same reason as the role fan-out).
            futures = {
                pool.submit(
                    contextvars.copy_context().run,
                    _extract_one_cell,
                    prefix, role, wording, rep, cache, max_retries, backup_max_retries,
                ): (role, group)
                for (role, group, wording, rep) in cells
            }
            for future in as_completed(futures):
                role, group = futures[future]
                try:
                    res = future.result()
                except Exception as e:  # defensive — _extract_one_cell already swallows call errors
                    logger.warning("Per-cell extraction crashed for %s/%s: %s", role, group, e)
                    res = None
                if res is None:
                    missing.append(f"{role}/{group}")
                    continue
                obs, sps, label = res
                obs_all.extend(obs)
                sp_all.extend(sps)
                if label == "backup":
                    used_backup.append(f"{role}/{group}")
    finally:
        if cache is not None:
            cache.delete()

    if not obs_all and not sp_all:
        logger.warning("Per-cell extraction produced nothing across all cells.")
        return None

    model_used = "per_cell"
    if used_backup:
        model_used += f" (backup: {','.join(sorted(used_backup))})"
    if missing:
        model_used += f" (missing: {','.join(sorted(missing))})"
    return ExtractionResult(
        output=CellExtractionOutput(observations=obs_all, strategy_points=sp_all),
        model_used=model_used,
    )
