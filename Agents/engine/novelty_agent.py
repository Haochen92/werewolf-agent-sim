from logging import getLogger
from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from Agents.llm_factory import get_llm_judge


from Agents.formatters import (
    format_day_channel,
)
from Agents.schemas import (
    NoveltyJudgment,
)
logger = getLogger(__name__)


NOVELTY_JUDGE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You judge whether a new message in an ongoing Werewolf day discussion adds NEW substance.

NOVEL (novel=true) — it introduces at least one of:
- a new argument, observation, or piece of evidence not already raised,
- a new or changed suspicion, or a concrete proposal/question that moves things forward,
- a direct response to a specific player (answering or defending).

NOT NOVEL (novel=false) — it merely:
- restates or agrees with a point already made,
- echoes the general sentiment ("let's be cautious", "watch for X") without adding anything,
- reinforces an existing accusation with no new angle or evidence.

Lean toward novel=true when genuinely uncertain; only gate clear restatement/echo.""",
        ),
        (
            "human",
            """Discussion so far:
{day_channel}

New message from {player_id}:
"{candidate_message}"

Does this add new substance, or is it restatement/echo?""",
        ),
    ]
)


def judge_proactive_novelty(candidate_message: str, payload: dict[str, Any], current_day: int) -> bool:
    """External novelty judge for a PROACTIVE utterance. True = keep, False = gate to a pass.

    Disinterested third-party judge (not self-assessment — the form Smoke 2/3 validated).
    Fails open (True) on the opener (nothing to echo yet) or any judge error, so the gate
    never silences a legitimate turn due to its own failure.
    """
    today = [
        m for m in payload.get("day_channel", [])
        if m.day == current_day and m.player != "game_master" and not getattr(m, "passed", False)
    ]
    if not today:
        return True
    try:
        result = (
            NOVELTY_JUDGE_PROMPT | get_llm_judge().with_structured_output(NoveltyJudgment)
        ).invoke(
            {
                "day_channel": format_day_channel(today),
                "candidate_message": candidate_message,
                "player_id": payload.get("player_id", ""),
            },
            config={"run_name": f"novelty_judge_{payload.get('player_id', '')}"},
        )
        return bool(result.novel)
    except Exception as exc:
        logger.warning(f"novelty judge failed: {exc}; defaulting to novel")
        return True

