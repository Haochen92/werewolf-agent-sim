from langchain_core.prompts import ChatPromptTemplate

from Agents.prompts.common import GAME_PREAMBLE, build_system_prompt
from Agents.prompts.roles import (
    HEALER_CORE_STRATEGY,
    INVESTIGATOR_CORE_STRATEGY,
    SERIAL_KILLER_CORE_STRATEGY,
    VIGILANTE_CORE_STRATEGY,
    WOLF_CORE_STRATEGY,
)


WOLF_NIGHT_DISCUSS = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                WOLF_CORE_STRATEGY,
                """
You are {player_id}, a {player_role}.
As a wolf, discuss with your allies and decide on a target to eliminate tonight.
There will be 2 rounds of discussion. In each round, share your reasoning and vote on a target.
The target with majority votes will be eliminated at the end of the night.
You may only vote for surviving villagers, not yourself or your allies.

You must respond with a valid JSON:
{{
    "message": "your discussion message",
    "vote_target": "exact player_id from the surviving villagers list",
    "updated_strategy": "your updated private strategy note for future turns"
}}
""",
            ),
        ),
        (
            "human",
            """Night of Day {current_day}, Discussion round {current_round}.

Surviving villagers: {surviving_villagers}
Your wolf allies: {surviving_wolves}

=== Day summaries ===
{day_summaries}

=== Today's day discussion ===
{day_channel}

=== Wolf night chat history ===
{wolf_channel}
=========================

Discuss with your allies and decide on a target.""",
        ),
    ]
)


HEALER_NIGHT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                HEALER_CORE_STRATEGY,
                """
You are {player_id}, a {player_role}.
Each night, you may protect one player from being eliminated by the wolves.
You cannot protect yourself.
Choose wisely based on who you think the wolves might target.

You must respond with a valid JSON:
{{"healer_target": "exact player_id from the surviving players list", "updated_strategy": "your updated private strategy note for future turns"}}
""",
            ),
        ),
        (
            "human",
            """Night of Day {current_day}.

Surviving players you can protect: {surviving_players}

=== Day summaries ===
{day_summaries}

=== Today's day discussion ===
{day_channel}
=========================

Choose a player to protect tonight.""",
        ),
    ]
)


INVESTIGATOR_NIGHT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                INVESTIGATOR_CORE_STRATEGY,
                """
You are {player_id}, a {player_role}.
Each night, you may investigate one player to learn their true role.
Use your past results and day discussions to choose your target wisely.
The result will be revealed to you at the start of the next day.

You must respond with a valid JSON:
{{"investigator_target": "exact player_id from the surviving players list", "updated_strategy": "your updated private strategy note for future turns"}}
""",
            ),
        ),
        (
            "human",
            """Night of Day {current_day}.

Surviving players: {surviving_players}
Your past investigation results: {investigator_results}

=== Day summaries ===
{day_summaries}

=== Today's day discussion ===
{day_channel}
=========================

Choose a player to investigate tonight.""",
        ),
    ]
)


SERIAL_KILLER_NIGHT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                SERIAL_KILLER_CORE_STRATEGY,
                """
You are {player_id}, a {player_role}.
Each night, you eliminate one player. You may target anyone still alive except yourself.
You are immune to being killed at night, but you can still be voted out during the day.
Choose your target based on who most threatens your survival or your path to being the last one standing.

You must respond with a valid JSON:
{{"serial_killer_target": "exact player_id from the surviving players list", "updated_strategy": "your updated private strategy note for future turns"}}
""",
            ),
        ),
        (
            "human",
            """Night of Day {current_day}.

Surviving players you can target: {surviving_players}

=== Day summaries ===
{day_summaries}

=== Today's day discussion ===
{day_channel}
=========================

Choose a player to eliminate tonight.""",
        ),
    ]
)


VIGILANTE_NIGHT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                VIGILANTE_CORE_STRATEGY,
                """
You are {player_id}, a {player_role}.
Each night you may shoot one player, or hold your fire. You have a small fixed number of bullets for the whole game and cannot reload.
The trade-offs, stated plainly:
- A shot that hits a wolf or the serial killer removes a threat to the village.
- A shot that hits a fellow villager kills an ally and weakens your own side.
- A bullet you never fire stays unused — if the game ends or you die with bullets in hand, they are never spent.
- The serial killer cannot be killed at night: shooting them will not remove them, but you will be told your target was immune, which confirms they are the serial killer — information you can use later.
Whether to shoot, and whom, is your own decision.
To take a shot, set "vigilante_target" to a surviving player (not yourself). To hold your fire this night, set "vigilante_target" to "hold_fire".

What you have learned from your past shots:
{vigilante_results}

You must respond with a valid JSON:
{{"vigilante_target": "exact player_id from the surviving players list, or \\"hold_fire\\"", "updated_strategy": "your updated private strategy note for future turns"}}
""",
            ),
        ),
        (
            "human",
            """Night of Day {current_day}.

You have {vigilante_bullets} bullet(s) remaining.
Surviving players you could shoot: {surviving_players}

=== Day summaries ===
{day_summaries}

=== Today's day discussion ===
{day_channel}
=========================

Decide whether to take a shot tonight, and at whom.""",
        ),
    ]
)
