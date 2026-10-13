"""Which layout the seat and memory-lookup prompts are built with: today's, or the shared-prefix one.

Set by the environment variable WW_PROMPT_LAYOUT, read when a template is built (a bench arm or a
batch run is its own process). "shared_prefix" builds every call so it opens with what all seats and
call types have in common, and only then what differs:

    system: the rules, the same for every call of a game
    user:   the public record (earlier days, today's transcript), ending on a rule line
            -> the cache boundary: Claude's mark, OpenAI's explicit breakpoint
            then the board, the role card, the call's instructions, private results, brief, memory

Today's layout puts the role card in the system message and seat-specific lines before the
transcript, so two seats share only the preamble (evidence/caching/experiment_log.md §12). The
shared-prefix layout is a variant behind this flag until the hallucination bench has compared the two.
"""

from __future__ import annotations

import os

from Agents.prompts.common import REASONING_DISCIPLINE, build_system_prompt

LAYOUT_ENV = "WW_PROMPT_LAYOUT"


def shared_prefix() -> bool:
    """Whether templates are built in the shared-prefix layout."""
    return os.environ.get(LAYOUT_ENV, "").strip().lower() == "shared_prefix"


# The system message of every seat turn and memory lookup in the shared-prefix layout.
SHARED_SYSTEM = build_system_prompt("{preamble}", REASONING_DISCIPLINE)

# The public record every call opens with. Its closing rule line is the only one in the user message:
# it is where a Claude request is marked and an OpenAI request gets its breakpoint.
PUBLIC_RECORD = """== Previous days ==
{day_summaries}

== Today's discussion ==
{day_channel}
=========================
"""

# Public too, but it changes at the day's vote, between a day's turns and the night after it, so it
# comes after the boundary: night calls still share the day's transcript.
BOARD = """
== Dead so far (public) ==
{dead_roster}

== Roles still in play (fixed cast minus revealed deaths) ==
{alive_roles}

"""
