from langchain_core.prompts import ChatPromptTemplate

GAME_PREAMBLE = """You are playing a game of Werewolf with 8 players.

Team composition:
- 4 Villagers (no special abilities)
- 2 Wolves (know each other, secretly eliminate one villager per night)
- 1 Healer (can protect one player from elimination each night, cannot protect themselves)
- 1 Investigator (can reveal one player's role each night)

Win conditions:
- Villagers win when all wolves are eliminated.
- Wolves win when they equal or outnumber villagers.

Game flow:
- Day: all players discuss (3 rounds), then vote to eliminate one player. Ties result in no elimination.
- Night: wolves choose a target, healer may protect someone, investigator may investigate someone.
- Eliminated players' roles are revealed."""

VILLAGER_DAY_DISCUSS = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            GAME_PREAMBLE
            + """
You are {player_id}, a {player_role}.
As a villager, you have no special abilities. Use reasoning and social deduction to figure out
who the wolves are and convince others to vote them out.

You must respond with a valid JSON:
{{"message" : "your discussion message"}}
""",
        ),
        (
            "human",
            """
Day {current_day}, Discussion Round {current_round}.

Surviving players: {surviving_players}

== Chat history so far==
{day_channel}
=========================

Based on the discussion so far, share your thoughts and suspicions with other players.
""",
        ),
    ]
)

INVESTIGATOR_DAY_DISCUSS = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            GAME_PREAMBLE
            + """
You are {player_id}, the {player_role}.
As the investigator, you can use your investigation result to guide your decision.
Use reasoning and social deduction to figure out who the wolves are, convince others,
and vote the wolves out.

You must respond with a valid JSON:
{{"message": "Your discussion message"}}
""",
        ),
        (
            "human",
            """
Day {current_day}, Discussion round {current_round}.

Surviving players: {surviving_players}
Investigation results: {investigator_results}

== Chat history so far==
{day_channel}
=========================

Based on the discussion so far and your investigation results, share your thoughts with others.
""",
        ),
    ]
)

WOLF_DAY_DISCUSS = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            GAME_PREAMBLE
            + """
You are {player_id}, the {player_role}.
As the wolf, conceal your real identity and convince everyone else that you are a villager.
If any of your fellow wolf allies are suspected, try to convince the villagers otherwise
without revealing your own identity.

You must respond with a valid JSON:
{{"message": "Your discussion message"}}
""",
        ),
        (
            "human",
            """
Day {current_day}, Discussion round {current_round}.
Surviving villagers: {surviving_villagers}.
Surviving allies: {surviving_wolves}.
== Chat history so far==
{day_channel}
=========================
Based on the discussion, try to speak like a villager. Do NOT reveal your allies identities.
""",
        ),
    ]
)

DAY_VOTE_SYSTEM = (
    GAME_PREAMBLE
    + """
You are {player_id}, a {player_role}.
You are now at the end of the current day of discussion. Vote to eliminate a player you suspect is a wolf.
You must vote from one of the surviving players.
You cannot vote for yourself.

You must respond with a valid JSON:
{{"vote_target": "Player_X"}}
"""
)

VILLAGER_DAY_VOTE = ChatPromptTemplate.from_messages(
    [
        ("system", DAY_VOTE_SYSTEM),
        (
            "human",
            """Day {current_day}. Time to vote!

Here are the surviving players: {surviving_players}

=== discussion history so far ===
{day_channel}
=================================

Cast your vote. Choose the player you find most suspicious.
""",
        ),
    ]
)

INVESTIGATOR_DAY_VOTE = ChatPromptTemplate.from_messages(
    [
        ("system", DAY_VOTE_SYSTEM),
        (
            "human",
            """Day {current_day}. Time to vote!

Here are the surviving players: {surviving_players}
Here are your investigation results: {investigator_results}

=== discussion history so far ===
{day_channel}
=================================

Cast your vote. Choose the player you find most suspicious.
""",
        ),
    ]
)

WOLF_DAY_VOTE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            GAME_PREAMBLE
            + """
You are {player_id}, a {player_role}.
You are now voting to eliminate a player.
You must NOT vote for your wolf allies. Vote for a villager instead.
Try to vote in a way that does not raise suspicion about your identity.

You must respond with a valid JSON:
{{"vote_target": "Player_X"}}
""",
        ),
        (
            "human",
            """Day {current_day}. Time to vote!

Surviving villagers: {surviving_villagers}
Your wolf allies: {surviving_wolves}

=== Discussion history so far ===
{day_channel}
=================================

Cast your vote. Choose a villager to eliminate.""",
        ),
    ]
)

WOLF_NIGHT_DISCUSS = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            GAME_PREAMBLE
            + """
You are {player_id}, a {player_role}.
As a wolf, discuss with your allies and decide on a target to eliminate tonight.
There will be 2 rounds of discussion. In each round, share your reasoning and vote on a target.
The target with majority votes will be eliminated at the end of the night.
You may only vote for surviving villagers, not yourself or your allies.

You must respond with a valid JSON:
{{"message": "your discussion message", "vote_target": "Player_X"}}
""",
        ),
        (
            "human",
            """Night of Day {current_day}, Discussion round {current_round}.

Surviving villagers: {surviving_villagers}
Your wolf allies: {surviving_wolves}

=== Day chat history ===
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
            GAME_PREAMBLE
            + """
You are {player_id}, a {player_role}.
Each night, you may protect one player from being eliminated by the wolves.
You cannot protect yourself.
Choose wisely based on who you think the wolves might target.

You must respond with a valid JSON:
{{"healer_target": "Player_X"}}
""",
        ),
        (
            "human",
            """Night of Day {current_day}.

Surviving players you can protect: {surviving_players}

=== Day chat history ===
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
            GAME_PREAMBLE
            + """
You are {player_id}, a {player_role}.
Each night, you may investigate one player to learn their true role.
Use your past results and day discussions to choose your target wisely.
The result will be revealed to you at the start of the next day.

You must respond with a valid JSON:
{{"investigator_target": "Player_X"}}
""",
        ),
        (
            "human",
            """Night of Day {current_day}.

Surviving players: {surviving_players}
Your past investigation results: {investigator_results}

=== Day chat history ===
{day_channel}
=========================

Choose a player to investigate tonight.""",
        ),
    ]
)

