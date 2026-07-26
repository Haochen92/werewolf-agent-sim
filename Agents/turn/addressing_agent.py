"""Addressed-target extraction for a human turn — the tagging an LLM does inline, done post-hoc.

An LLM seat emits ``addressed_targets`` as part of its structured decision, and the reactive/
proactive scheduler runs on those tags (a question/accusation OPENS an obligation; a response/
mention DISCHARGES one). A human just types free text, so this classifier tags the human's message
the same way — same form/stance vocabulary — so human speech drives the scheduler identically to an
agent's. Runs after the human's message; fails open to no tags so a classifier error never stalls
the turn (the deterministic discharge-from-``owes`` in the driver still clears the human's debts).
"""

from logging import getLogger
from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from Agents.llm_factory import get_llm_extractor
from Agents.prompts.prompt_formatters import format_day_channel_for_day
from Agents.schemas import AddressingExtraction
from Agents.schemas.game_events import AddressedTarget

logger = getLogger(__name__)


ADDRESSING_EXTRACTOR_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You tag whom a Werewolf day-discussion message addresses, for turn scheduling.

For each player the message addresses, emit one entry:
- addressed_form: question=directly asks the target something that expects their reply; response=replies to the target; mention=talks about the target in the third person.
- stance: accusation=suspects/blames the target of being evil or lying; defense=supports/protects; agreement=agrees; neutral=no clear stance. Passing commentary (e.g. noting someone has been quiet) is neutral, not accusation.

Only tag a player named or clearly referred to. A general remark to the room, addressing no one
specific, gets an empty list. Never invent a player who is not in the roster.""",
        ),
        (
            "human",
            """Living players (excluding the speaker): {roster}

Discussion so far:
{day_channel}

New message from {player_id}:
"{message}"

Who does this message address?""",
        ),
    ]
)


def extract_addressed_targets(
    message: str, payload: dict[str, Any], current_day: int
) -> list[AddressedTarget]:
    """Tag whom a human's message addresses, so it drives the reactive scheduler like an LLM's
    self-tagged addressed_targets.

    Returns [] on an empty/absent message or any extractor error — fail open, so a tagging failure
    drops only that turn's OPENINGS (new questions/accusations) and never stalls the turn; the
    driver's discharge-from-``owes`` handles the human's own obligations regardless.
    """
    if not message or not message.strip():
        return []
    self_id = payload.get("player_id", "")
    roster = [p for p in _surviving(payload) if p != self_id]
    try:
        result = (
            ADDRESSING_EXTRACTOR_PROMPT
            | get_llm_extractor().with_structured_output(AddressingExtraction)
        ).invoke(
            {
                "roster": ", ".join(roster),
                "day_channel": format_day_channel_for_day(payload.get("day_channel", []), current_day),
                "player_id": self_id,
                "message": message,
            },
            config={"run_name": f"addressing_extract_{self_id}"},
        )
        return _sanitize_against_roster(result.addressed_targets, roster)
    except Exception as exc:
        logger.warning(f"addressing extraction failed: {exc}; defaulting to no addressees")
        return []


def _sanitize_against_roster(
    targets: list[AddressedTarget], roster: list[str]
) -> list[AddressedTarget]:
    """Enforce the roster in code, not just the prompt: drop any addressee not a living player other
    than the speaker (``roster`` already excludes self), deduping exact (target, form) pairs. This
    rejects self-addressing, dead/invented players, and non-player labels ("all"/"everyone") before
    they can be written onto the persisted DayChannel entry."""
    allowed = set(roster)
    seen: set[tuple[str, str]] = set()
    cleaned = []
    for target in targets:
        if target.target not in allowed:
            logger.warning("addressing extractor returned an off-roster target: %r", target.target)
            continue
        key = (target.target, target.addressed_form)
        if key not in seen:
            seen.add(key)
            cleaned.append(target)
    return cleaned


def _surviving(payload: dict[str, Any]) -> list[str]:
    """The living roster, from either a flat night payload or a faction-split day payload (mirrors
    how build_agent_prompt_input / _reads_coverage enumerate survivors)."""
    return payload.get("surviving_players") or (
        payload.get("surviving_wolves", []) + payload.get("surviving_villagers", [])
    )
