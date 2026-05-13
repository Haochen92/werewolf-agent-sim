from langchain_core.prompts import ChatPromptTemplate

from Agents.prompts.common import (
    DAY_DISCUSS_RESPONSE_FORMAT,
    DISCUSSION_SILENCE_RULE,
    GAME_PREAMBLE,
    TONE_INSTRUCTION,
    build_system_prompt,
)
from Agents.prompts.memory import DAY_DISCUSSION_MEMORY_CONTEXT, DAY_VOTE_MEMORY_CONTEXT
from Agents.prompts.roles import (
    HEALER_CORE_STRATEGY,
    INVESTIGATOR_CORE_STRATEGY,
    VILLAGER_CORE_STRATEGY,
    WOLF_CORE_STRATEGY,
)


VILLAGER_DAY_DISCUSS = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                VILLAGER_CORE_STRATEGY,
                """
You are {player_id}, a {player_role}.
As a villager, you have no special abilities. Use reasoning and social deduction to figure out
who the wolves are and convince others to vote them out.
""",
                TONE_INSTRUCTION,
                DAY_DISCUSS_RESPONSE_FORMAT,
            ),
        ),
        (
            "human",
            """
Day {current_day}, Discussion Round {current_round}.

Surviving players: {surviving_players}

== Previous days summary ==
{day_summaries}

== Today's discussion ==
{day_channel}
=========================
"""
            + DAY_DISCUSSION_MEMORY_CONTEXT
            + DISCUSSION_SILENCE_RULE,
        ),
    ]
)


HEALER_DAY_DISCUSS = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                HEALER_CORE_STRATEGY,
                """
You are {player_id}, the {player_role}.
During the day, speak as a normal villager while protecting your cover. Use reasoning and
social deduction to help the village identify wolves without exposing your role.
""",
                TONE_INSTRUCTION,
                DAY_DISCUSS_RESPONSE_FORMAT,
            ),
        ),
        (
            "human",
            """
Day {current_day}, Discussion Round {current_round}.

Surviving players: {surviving_players}

== Previous days summary ==
{day_summaries}

== Today's discussion ==
{day_channel}
=========================
"""
            + DAY_DISCUSSION_MEMORY_CONTEXT
            + DISCUSSION_SILENCE_RULE,
        ),
    ]
)


INVESTIGATOR_DAY_DISCUSS = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                INVESTIGATOR_CORE_STRATEGY,
                """
You are {player_id}, the {player_role}.
As the investigator, you can use your investigation result to guide your decision.
Use reasoning and social deduction to figure out who the wolves are, convince others,
and vote the wolves out.
""",
                TONE_INSTRUCTION,
                DAY_DISCUSS_RESPONSE_FORMAT,
            ),
        ),
        (
            "human",
            """
Day {current_day}, Discussion round {current_round}.

Surviving players: {surviving_players}
Investigation results: {investigator_results}

== Previous days summary ==
{day_summaries}

== Today's discussion ==
{day_channel}
=========================
"""
            + DAY_DISCUSSION_MEMORY_CONTEXT
            + DISCUSSION_SILENCE_RULE,
        ),
    ]
)


WOLF_DAY_DISCUSS = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                WOLF_CORE_STRATEGY,
                """
You are {player_id}, the {player_role}.
As the wolf, conceal your real identity and convince everyone else that you are a villager.
If any of your fellow wolf allies are suspected, try to convince the villagers otherwise
without revealing your own identity.
""",
                TONE_INSTRUCTION,
                DAY_DISCUSS_RESPONSE_FORMAT,
            ),
        ),
        (
            "human",
            """
Day {current_day}, Discussion round {current_round}.
Surviving villagers: {surviving_villagers}.
Surviving allies: {surviving_wolves}.

== Previous days summary ==
{day_summaries}

== Today's discussion ==
{day_channel}
=========================
Based on the discussion, try to speak like a villager. Do NOT reveal your allies identities.
"""
            + DAY_DISCUSSION_MEMORY_CONTEXT
            + DISCUSSION_SILENCE_RULE,
        ),
    ]
)


DAY_VOTE_SYSTEM_SUFFIX = """
You are {player_id}, a {player_role}.
You are now at the end of the current day of discussion. Vote to eliminate a player you suspect is a wolf.
You must vote from one of the surviving players.
You cannot vote for yourself.

You must respond with a valid JSON:
{{"vote_target": "Player_X"}}
"""


VILLAGER_DAY_VOTE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                VILLAGER_CORE_STRATEGY,
                DAY_VOTE_SYSTEM_SUFFIX,
            ),
        ),
        (
            "human",
            """Day {current_day}. Time to vote!

Here are the surviving players: {surviving_players}

== Previous days summary ==
{day_summaries}

=== Today's discussion ===
{day_channel}
=================================

""" + DAY_VOTE_MEMORY_CONTEXT + """
Cast your vote. Choose the player you find most suspicious.
""",
        ),
    ]
)


HEALER_DAY_VOTE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                HEALER_CORE_STRATEGY,
                DAY_VOTE_SYSTEM_SUFFIX,
            ),
        ),
        (
            "human",
            """Day {current_day}. Time to vote!

Here are the surviving players: {surviving_players}

== Previous days summary ==
{day_summaries}

=== Today's discussion ===
{day_channel}
=================================

""" + DAY_VOTE_MEMORY_CONTEXT + """
Cast your vote. Choose the player you find most suspicious while protecting your cover.
""",
        ),
    ]
)


INVESTIGATOR_DAY_VOTE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                INVESTIGATOR_CORE_STRATEGY,
                DAY_VOTE_SYSTEM_SUFFIX,
            ),
        ),
        (
            "human",
            """Day {current_day}. Time to vote!

Here are the surviving players: {surviving_players}
Here are your investigation results: {investigator_results}

== Previous days summary ==
{day_summaries}

=== Today's discussion ===
{day_channel}
=================================

""" + DAY_VOTE_MEMORY_CONTEXT + """
Cast your vote. Choose the player you find most suspicious.
""",
        ),
    ]
)


WOLF_DAY_VOTE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                WOLF_CORE_STRATEGY,
                """
You are {player_id}, a {player_role}.
You are now voting to eliminate a player.
You cannot vote for yourself.
Avoid voting for your wolf allies by default, unless refusing to join an overwhelming majority against a clearly doomed ally would expose you.
Try to vote in a way that does not raise suspicion about your identity; 
usually target a villager, but preserve your cover by voting for a wolf ally when the village consensus is decisive to vote out that exposed wolf ally.

You must respond with a valid JSON:
{{"vote_target": "Player_X"}}
""",
            ),
        ),
        (
            "human",
            """Day {current_day}. Time to vote!

Surviving villagers: {surviving_villagers}
Known surviving wolves: {surviving_wolves}

== Previous days summary ==
{day_summaries}

=== Today's discussion ===
{day_channel}
=================================

""" + DAY_VOTE_MEMORY_CONTEXT + """
Cast your vote. Choose the target that best preserves your cover.""",
        ),
    ]
)
