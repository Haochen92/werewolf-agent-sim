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
    SERIAL_KILLER_CORE_STRATEGY,
    VIGILANTE_CORE_STRATEGY,
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
Day {current_day} discussion.
{firing_brief}

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
Day {current_day} discussion.
{firing_brief}

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
Day {current_day} discussion.
{firing_brief}

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
Day {current_day} discussion.
{firing_brief}
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


SERIAL_KILLER_DAY_DISCUSS = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                SERIAL_KILLER_CORE_STRATEGY,
                """
You are {player_id}, the {player_role}.
You are playing alone against everyone. During the day, pose as an ordinary villager:
join the hunt for the wolves, deflect suspicion from yourself, and never reveal that you
are the serial killer. You can be voted out, so blending in is survival.
""",
                TONE_INSTRUCTION,
                DAY_DISCUSS_RESPONSE_FORMAT,
            ),
        ),
        (
            "human",
            """
Day {current_day} discussion.
{firing_brief}

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


VIGILANTE_DAY_DISCUSS = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                VIGILANTE_CORE_STRATEGY,
                """
You are {player_id}, the {player_role}.
You are on the village's side. During the day, speak as an ordinary villager and protect
your cover — do not reveal that you can shoot at night. Use reasoning and social deduction
to help find the wolves.
""",
                TONE_INSTRUCTION,
                DAY_DISCUSS_RESPONSE_FORMAT,
            ),
        ),
        (
            "human",
            """
Day {current_day} discussion.
{firing_brief}

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


DAY_VOTE_SYSTEM_SUFFIX = """
You are {player_id}, a {player_role}.
You are now at the end of the current day of discussion. Vote to eliminate a player you suspect is a wolf.
You must vote from one of the surviving players, or "abstain" when it is offered.
You cannot vote for yourself.
{abstain_instruction}

You must respond with a valid JSON:
{{"adopted_strategy_keys": [1, 3], "vote_target": "exact player_id from the surviving players list, or \\"abstain\\"", "updated_strategy": "your updated private strategy note"}}
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
You may also vote "abstain" when it is offered (an abstain plurality means no elimination) — blending with an abstaining village can be good cover, and a no-lynch day costs the village a chance to find a wolf.
{abstain_instruction}

You must respond with a valid JSON:
{{"adopted_strategy_keys": [1, 3], "vote_target": "exact player_id from the surviving players list, or \\"abstain\\"", "updated_strategy": "your updated private strategy note"}}
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


SERIAL_KILLER_DAY_VOTE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                SERIAL_KILLER_CORE_STRATEGY,
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
Cast your vote. Vote in the way that best deflects suspicion from you and removes a threat to your survival.
""",
        ),
    ]
)


VIGILANTE_DAY_VOTE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                VIGILANTE_CORE_STRATEGY,
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
