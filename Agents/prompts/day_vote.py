"""Day-vote prompt templates, built from the role cards (Agents/prompts/roles/).

Every role's template is the same scaffold — the rules block, the role's identity and vote framing,
the voting rules (the town's shared block, or the card's own guidance for a side whose win makes
"remove a threat to the town" wrong), the JSON contract — and a shared transcript block around
the card's context and closing.
"""

from importlib import import_module

from langchain_core.prompts import ChatPromptTemplate

from Agents.prompts.common import (
    READS_COMMIT_INSTRUCTION,
    REASONING_DISCIPLINE,
    build_system_prompt,
    json_contract,
)
from Agents.prompts.memory import DAY_VOTE_MEMORY_CONTEXT
from Agents.schemas.lineup_output import DayVoteOutput


# --- Shared transcript framing ---

_VOTE_HEADER = "Day {current_day}. Time to vote!\n\n"

_VOTE_TRANSCRIPT = """
== Dead so far (public) ==
{dead_roster}

== Roles still in play (fixed cast minus revealed deaths) ==
{alive_roles}

== Previous days ==
{day_summaries}

=== Today's discussion ===
{day_channel}
=================================

"""


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
    system = build_system_prompt(
        "{preamble}", REASONING_DISCIPLINE, card.playstyle, words.framing,
        words.guidance or _TOWN_GUIDANCE, json_contract(DayVoteOutput),
    )
    human = (
        "{tell_book}" + READS_COMMIT_INSTRUCTION
        + _VOTE_HEADER + words.context.lstrip("\n") + _VOTE_TRANSCRIPT + DAY_VOTE_MEMORY_CONTEXT
        + words.closing
    )
    return ChatPromptTemplate.from_messages([("system", system), ("human", human)])
