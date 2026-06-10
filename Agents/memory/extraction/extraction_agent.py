"""Extraction agent: the post-game `llm.invoke` (primary → backup, with retries) that turns a
finished game's pre-built prompt into a structured GameStrategyOutput. Prompt construction and
input formatting live in inputs.py (this package).

Two entry points share one primary→backup fallback core:
  extract_postgame          — single all-roles prompt (legacy / A/B baseline)
  extract_postgame_per_role — fan out the six roles concurrently over a shared
                              cacheable prefix, then merge their outputs
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from logging import getLogger

from Agents.llm_factory import get_llm_pro, get_llm_pro_backup
from Agents.schemas import GameStrategyOutput

from .inputs import build_role_extraction_tail

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
class ExtractionResult:
    output: GameStrategyOutput
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


def _invoke_with_fallback(
    prompt: str,
    run_name: str,
    max_retries: int,
    backup_max_retries: int,
) -> ExtractionResult | None:
    """Run the extraction call on primary → backup with per-model retries.

    Returns an ExtractionResult (output + model label) or None if every attempt
    on both models fails.
    """
    models = (
        ("primary", get_llm_pro(), max_retries),
        ("backup", get_llm_pro_backup(), backup_max_retries),
    )
    for label, llm, retries in models:
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
    return _invoke_with_fallback(
        prompt, "postgame_extraction", max_retries, backup_max_retries
    )


def extract_postgame_per_role(
    prefix: str,
    roles: tuple[str, ...] = EXTRACTION_ROLES,
    max_workers: int = 6,
    max_retries: int = 2,
    backup_max_retries: int = 2,
) -> ExtractionResult | None:
    """Fan the extraction out over `roles`, concurrently, then merge.

    Each role's prompt is the shared `prefix` plus that role's lock tail — so the
    prefix is byte-identical across calls (the unit explicit caching reuses). Roles
    run concurrently on a thread pool (the calls are network-bound). A role that
    fails entirely is dropped (partial extraction beats none); the merged output
    concatenates observations and strategy points in `roles` order. Returns None
    only if every role failed.
    """
    role_outputs: dict[str, GameStrategyOutput] = {}
    role_models: dict[str, str] = {}

    def _one(role: str) -> ExtractionResult | None:
        prompt = prefix + build_role_extraction_tail(role)
        return _invoke_with_fallback(
            prompt, f"postgame_extraction_{role}", max_retries, backup_max_retries
        )

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_one, role): role for role in roles}
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
