"""Night-phase prompt templates, built from the role cards (Agents/prompts/roles/).

Every solo role's night turn is the same scaffold around its card's night words; the pack's chat and
the carrier's kill take the pack's words (roles/pack.py), with the chat after the public record. All
of them follow the shared-prefix layout (layout.py): the rules block (the {preamble} input, composed
per game from the dealt lineup) as the system message, then the public record every call shares.
"""

from importlib import import_module

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel

from Agents.prompts.common import READS_COMMIT_INSTRUCTION, build_system_prompt, json_contract
from Agents.prompts.layout import BOARD, PUBLIC_RECORD, SHARED_SYSTEM
from Agents.prompts.memory import NIGHT_ACTION_MEMORY_CONTEXT
from Agents.prompts.roles import pack
from Agents.schemas.lineup_output import NIGHT_OUTPUTS, CarrierOutput, WolfChatOutput


# --- The ten-seat night ---
# Every turn, the pack's included, asks for the reads first.

# The pack's chat: private to the wolves, so after the public record.
_WOLF_CHAT = """
=== Wolf night chat history ===
{wolf_channel}

"""


def _night(playstyle: str, ability: str, schema: type[BaseModel], after_board: str,
           turn: str) -> ChatPromptTemplate:
    """A night turn: the public record, the board and ``after_board`` (the pack's chat), then the
    card, the contract, the memories and the strategy note, then the turn's own lines."""
    human = (
        PUBLIC_RECORD + BOARD + after_board
        + build_system_prompt(playstyle, ability, json_contract(schema), NIGHT_ACTION_MEMORY_CONTEXT)
        + "\n" + "{tell_book}" + READS_COMMIT_INSTRUCTION + turn
    )
    return ChatPromptTemplate.from_messages([("system", SHARED_SYSTEM), ("human", human)])


def night_template(role: str) -> ChatPromptTemplate:
    """A dealt role's own night turn, from its card."""
    card = import_module(f"Agents.prompts.roles.{role}").CARD
    words = card.night
    return _night(card.playstyle, words.ability, NIGHT_OUTPUTS[role], "",
                  "Night of Day {current_day}.\n" + words.context
                  + ("{night_lot}" if words.lot else "") + words.closing)


def wolf_chat_template(role: str) -> ChatPromptTemplate:
    """One wolf's turn in the pack chat: up to three rounds, the carrier first, with a pass."""
    card = import_module(f"Agents.prompts.roles.{role}").CARD
    return _night(card.playstyle, pack.CHAT_ABILITY, WolfChatOutput, _WOLF_CHAT,
                  "Night of Day {current_day}, chat round {current_round}.\n" + pack.CHAT_CONTEXT
                  + "{night_lot}" + pack.CHAT_CLOSING)


def carrier_template(role: str) -> ChatPromptTemplate:
    """The carrier's turn after the chat: it names the pack's target."""
    card = import_module(f"Agents.prompts.roles.{role}").CARD
    return _night(card.playstyle, pack.CARRIER.ability, CarrierOutput, _WOLF_CHAT,
                  "Night of Day {current_day}: the pack's target.\n" + pack.CARRIER.context
                  + "{night_lot}" + pack.CARRIER.closing)
