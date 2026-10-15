"""The shared-prefix layout every seat turn and memory lookup is built in.

Every call opens with what all seats and call types have in common, and only then what differs:

    system: the rules, the same for every call of a game
    user:   the public record (earlier days, today's transcript), ending on a rule line
            -> the cache boundary: Claude's mark, OpenAI's explicit breakpoint
            then the board, the role card, the call's instructions, private results, brief, memory

So votes, night actions and lookups share the day's transcript across seats. The earlier layout (role
card in the system message, seat-specific lines before the transcript) was retired after one comparison:
GPT-6 Luna cost 28% less per call with no detected quality change, and Claude Haiku 5.5 stopped passing
almost every free turn (evidence/caching/experiment_log.md §13-14; git tag prompt-layout-baseline).
"""

from __future__ import annotations

from Agents.prompts.common import REASONING_DISCIPLINE, build_system_prompt

# The system message of every seat turn and memory lookup.
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
