"""Day-vote prompt templates, built from the role cards (Agents/prompts/roles/).

Every role's template is the same scaffold in the shared-prefix layout (layout.py): the rules as the
system message, the public record, then the role's identity and vote framing, the voting rules (the
town's shared block, or the card's own guidance for a side whose win makes "remove a threat to the
town" wrong), the JSON contract, and the card's context and closing.
"""

from importlib import import_module

from langchain_core.prompts import ChatPromptTemplate

from Agents.prompts.common import READS_COMMIT_INSTRUCTION, build_system_prompt, json_contract
from Agents.prompts.layout import BOARD, PUBLIC_RECORD, SHARED_SYSTEM
from Agents.prompts.memory import DAY_VOTE_MEMORY_CONTEXT
from Agents.schemas.lineup_output import DayVoteOutput


# --- The vote header ---

_VOTE_HEADER = "Day {current_day}. Time to vote!\n\n"


# --- The ten-seat vote ---
# The rules block arrives as the {preamble} input, composed per game from the dealt lineup
# (compose.preamble).

# The voting rules of a town role: DAY_VOTE_SYSTEM_SUFFIX without its identity line (the card's vote
# framing has it) and its JSON (generated from the schema). A card with its own guidance (the
# wolves, a lone killer, a neutral) uses that instead.
_TOWN_GUIDANCE = """
You are now at the end of the current day of discussion. Vote to eliminate the player you believe
is most likely to be a threat to the town — a wolf or the lone killer.
You must vote from one of the surviving players, or "abstain" when it is offered.
You cannot vote for yourself.
{abstain_instruction}
"""


def day_vote_template(role: str) -> ChatPromptTemplate:
    """A dealt role's day vote, from its card."""
    card = import_module(f"Agents.prompts.roles.{role}").CARD
    words = card.day_vote
    # The public record first (layout.py), then the role card, the voting rules and the contract.
    human = (
        PUBLIC_RECORD + BOARD
        + build_system_prompt(card.playstyle, words.framing, words.guidance or _TOWN_GUIDANCE,
                              json_contract(DayVoteOutput))
        + "\n" + "{tell_book}" + READS_COMMIT_INSTRUCTION
        + _VOTE_HEADER + words.context.lstrip("\n") + DAY_VOTE_MEMORY_CONTEXT + words.closing
    )
    return ChatPromptTemplate.from_messages([("system", SHARED_SYSTEM), ("human", human)])
