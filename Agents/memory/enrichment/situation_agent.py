"""Per-role/phase situation-summary LLM call (the live retrieval query).

v6: the query is composed in the SAME per-cell dimension schema as the post-game extraction
(`cell_situation_schema_for` ⇒ `compose_situation_embed`), so a live query embed-matches the stored
v6 observations. Falls back to the legacy v5 SituationSummary for any (role, phase) without a v6 cell.

This is an LLM-agent concern colocated here for now — a candidate to move into a dedicated agents/llm
module later.
"""
from __future__ import annotations

from logging import getLogger

from pydantic import BaseModel, Field, create_model

from Agents.llm_factory import get_llm
from Agents.prompts.prompt_inputs import (
    build_agent_prompt_input as _build_agent_prompt_input,
    compose_cell_guidance,
)
from Agents.prompts import (
    HEALER_SITUATION_SUMMARY,
    INVESTIGATOR_SITUATION_SUMMARY,
    SERIAL_KILLER_SITUATION_SUMMARY,
    VIGILANTE_SITUATION_SUMMARY,
    VILLAGER_SITUATION_SUMMARY,
    WOLF_SITUATION_SUMMARY,
)
from Agents.prompts.memory import V6_SITUATION_SUMMARY
from Agents.schemas import SituationSummary
from Agents.schemas.memory import cell_situation_schema_for
from Agents.state import (
    HealerDayState,
    InvestigatorDayState,
    VillagerDayState,
    WolfDayState,
)

logger = getLogger(__name__)

_LEGACY_PROMPT_BY_ROLE = {
    "villager": VILLAGER_SITUATION_SUMMARY,
    "healer": HEALER_SITUATION_SUMMARY,
    "investigator": INVESTIGATOR_SITUATION_SUMMARY,
    "wolf": WOLF_SITUATION_SUMMARY,
    "serial_killer": SERIAL_KILLER_SITUATION_SUMMARY,
    "vigilante": VIGILANTE_SITUATION_SUMMARY,
}

# Cache the per-cell summary containers (list[CellSituation], 1-2 items) so we build each once.
_SUMMARY_CONTAINER_CACHE: dict[type, type[BaseModel]] = {}


def _summary_container(cell_schema: type[BaseModel]) -> type[BaseModel]:
    cached = _SUMMARY_CONTAINER_CACHE.get(cell_schema)
    if cached is None:
        cached = create_model(
            f"{cell_schema.__name__}Summary",
            __base__=BaseModel,
            situations=(
                list[cell_schema],
                Field(min_length=1, max_length=2,
                      description="1-2 distinct situations you currently face, each with its "
                                  "structured dimensional fields for semantic search."),
            ),
        )
        _SUMMARY_CONTAINER_CACHE[cell_schema] = cached
    return cached


def _generate_situations_for_agent(
    payload: VillagerDayState | HealerDayState | WolfDayState | InvestigatorDayState,
    action_phase: str,
    max_retries: int = 1,
) -> list[str]:
    player_id = payload["player_id"]
    role = payload["player_role"]
    current_day = payload["current_day"]
    current_round = payload["current_round"]
    run_name = f"situation_summary_{role}_{action_phase}_day_{current_day}_round_{current_round}"

    cell_schema = cell_situation_schema_for(role, action_phase)
    extra: dict = {}
    if cell_schema is not None:
        chain = V6_SITUATION_SUMMARY | get_llm().with_structured_output(
            _summary_container(cell_schema)
        )
        compose = lambda r: [s.composed_situation for s in r.situations]  # noqa: E731
        extra = compose_cell_guidance(role, action_phase, cell_schema)
    else:
        prompt_template = _LEGACY_PROMPT_BY_ROLE.get(role, VILLAGER_SITUATION_SUMMARY)
        chain = prompt_template | get_llm().with_structured_output(SituationSummary)
        compose = lambda r: r.composed_situations  # noqa: E731

    for attempt in range(max_retries + 1):
        try:
            result = chain.invoke(
                {**_build_agent_prompt_input(payload), **extra}, config={"run_name": run_name}
            )
            return compose(result)
        except Exception as e:
            logger.warning(f"Situation summary LLM call failed for {player_id}: {e}")
            if attempt < max_retries:
                continue
            break

    logger.error(f"{player_id} situation summary failed all retries, using fallback")
    return [f"Day {current_day} as {role}, round {current_round}"]
