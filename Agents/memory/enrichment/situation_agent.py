"""Per-role situation-summary LLM call.

This is an LLM-agent concern colocated here for now — a candidate to move into a
dedicated agents/llm module later.
"""
from __future__ import annotations

from logging import getLogger

from Agents.llm_factory import get_llm
from Agents.prompt_inputs import build_agent_prompt_input as _build_agent_prompt_input
from Agents.prompts import (
    HEALER_SITUATION_SUMMARY,
    INVESTIGATOR_SITUATION_SUMMARY,
    SERIAL_KILLER_SITUATION_SUMMARY,
    VIGILANTE_SITUATION_SUMMARY,
    VILLAGER_SITUATION_SUMMARY,
    WOLF_SITUATION_SUMMARY,
)
from Agents.schemas import SituationSummary
from Agents.state import (
    HealerDayState,
    InvestigatorDayState,
    VillagerDayState,
    WolfDayState,
)

logger = getLogger(__name__)


def _generate_situations_for_agent(
    payload: VillagerDayState | HealerDayState | WolfDayState | InvestigatorDayState,
    max_retries: int = 1,
) -> list[str]:
    player_id = payload["player_id"]
    role = payload["player_role"]
    current_day = payload["current_day"]
    current_round = payload["current_round"]
    prompt_template = {
        "villager": VILLAGER_SITUATION_SUMMARY,
        "healer": HEALER_SITUATION_SUMMARY,
        "investigator": INVESTIGATOR_SITUATION_SUMMARY,
        "wolf": WOLF_SITUATION_SUMMARY,
        "serial_killer": SERIAL_KILLER_SITUATION_SUMMARY,
        "vigilante": VIGILANTE_SITUATION_SUMMARY,
    }.get(role, VILLAGER_SITUATION_SUMMARY)
    chain = prompt_template | get_llm().with_structured_output(SituationSummary)

    for attempt in range(max_retries + 1):
        try:
            result = chain.invoke(
                _build_agent_prompt_input(payload),
                config={
                    "run_name": (
                        f"situation_summary_{role}_day_{current_day}_round_{current_round}"
                    )
                },
            )
            return result.composed_situations
        except Exception as e:
            logger.warning(f"Situation summary LLM call failed for {player_id}: {e}")
            if attempt < max_retries:
                continue
            break

    logger.error(f"{player_id} situation summary failed all retries, using fallback")
    return [f"Day {current_day} as {role}, round {current_round}"]
