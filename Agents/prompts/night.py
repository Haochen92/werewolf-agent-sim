"""Night-phase prompt templates, built from the role cards (Agents/prompts/roles/).

Every solo role's night turn is the same scaffold around its card's night words; the pack's
chat and the carrier's kill take the pack's words (roles/pack.py) with the chat under the
transcript. The rules block arrives as the {preamble} input, composed per game from the dealt
lineup (compose.preamble).
"""

from importlib import import_module

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from Agents.prompts.common import (
    READS_COMMIT_INSTRUCTION,
    REASONING_DISCIPLINE,
    build_system_prompt,
    json_contract,
)
from Agents.prompts.memory import NIGHT_ACTION_MEMORY_CONTEXT
from Agents.prompts.roles import pack
from Agents.schemas.lineup_output import NIGHT_OUTPUTS, CarrierOutput, WolfChatOutput


# --- The night transcript every turn carries ---

_NIGHT_TRANSCRIPT = """
== Dead so far (public) ==
{dead_roster}

== Roles still in play (fixed cast minus revealed deaths) ==
{alive_roles}

=== Previous days ===
{day_summaries}

=== Today's day discussion ===
{day_channel}
=========================

"""


# --- The ten-seat night ---
# Every turn, the pack's included, asks for the reads first.

def _system(playstyle: str, ability: str, schema: type[BaseModel]) -> str:
    return build_system_prompt(
        "{preamble}", REASONING_DISCIPLINE, playstyle, ability, json_contract(schema),
        NIGHT_ACTION_MEMORY_CONTEXT,
    )


# The night transcript with the pack's chat under it.
_PACK_TRANSCRIPT = """
== Dead so far (public) ==
{dead_roster}

== Roles still in play (fixed cast minus revealed deaths) ==
{alive_roles}

=== Previous days ===
{day_summaries}

=== Today's day discussion ===
{day_channel}

=== Wolf night chat history ===
{wolf_channel}
=========================

"""


def night_template(role: str) -> ChatPromptTemplate:
    """A dealt role's own night turn, from its card."""
    card = import_module(f"Agents.prompts.roles.{role}").CARD
    words = card.night
    human = (
        "{tell_book}" + READS_COMMIT_INSTRUCTION
        + "Night of Day {current_day}.\n" + words.context + _NIGHT_TRANSCRIPT
        + ("{night_lot}" if words.lot else "") + words.closing
    )
    return ChatPromptTemplate.from_messages([
        ("system", _system(card.playstyle, words.ability, NIGHT_OUTPUTS[role])),
        ("human", human),
    ])


def wolf_chat_template(role: str) -> ChatPromptTemplate:
    """One wolf's turn in the pack chat: up to three rounds, the carrier first, with a pass."""
    card = import_module(f"Agents.prompts.roles.{role}").CARD
    human = (
        "{tell_book}" + READS_COMMIT_INSTRUCTION
        + "Night of Day {current_day}, chat round {current_round}.\n" + pack.CHAT_CONTEXT
        + _PACK_TRANSCRIPT
        + "{night_lot}" + pack.CHAT_CLOSING
    )
    return ChatPromptTemplate.from_messages([
        ("system", _system(card.playstyle, pack.CHAT_ABILITY, WolfChatOutput)),
        ("human", human),
    ])


def carrier_template(role: str) -> ChatPromptTemplate:
    """The carrier's turn after the chat: it names the pack's target."""
    card = import_module(f"Agents.prompts.roles.{role}").CARD
    human = (
        "{tell_book}" + READS_COMMIT_INSTRUCTION
        + "Night of Day {current_day}: the pack's target.\n" + pack.CARRIER.context
        + _PACK_TRANSCRIPT
        + "{night_lot}" + pack.CARRIER.closing
    )
    return ChatPromptTemplate.from_messages([
        ("system", _system(card.playstyle, pack.CARRIER.ability, CarrierOutput)),
        ("human", human),
    ])
