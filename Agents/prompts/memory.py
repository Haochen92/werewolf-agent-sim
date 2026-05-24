from langchain_core.prompts import ChatPromptTemplate


RERANK_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            """You are a relevance judge for a memory retrieval system in a Werewolf social deduction game.

A player is facing these situations:
{situations}

Below are memory candidates retrieved from past games. Score each candidate's relevance to the player's current situations.

Candidates:
{candidates}

Score every candidate from 1 (irrelevant) to 5 (highly relevant). A candidate is relevant if it describes a similar game dynamic, pressure pattern, or strategic dilemma — even if the surface details differ.""",
        )
    ]
)


ADOPTION_INSTRUCTION = """\
In adopted_strategy_keys (e.g. [1, 3]), report which strategy points you followed.
DO: list a point if you took its recommended action (the text after "Action:").
DON'T: list a point you read but acted against.
DON'T: list a point if your action was shaped by observations, not strategy points.
An empty list is fine if none of the points match your action."""


DAY_DISCUSSION_MEMORY_CONTEXT = """
Relevant observations: (These are specific, detailed observations from past games that are relevant to the current situation):
{retrieved_observations}

Dynamic strategy points (strategies from past games relevant to your current situation):
{strategy_points}

{adoption_instruction}

Adaptive Strategic thinking:
    You have a private strategy note from your previous turns:
    {previous_strategy}

    Update your strategy notes based on new information, relevant observations. If your current approach
    resembles a pattern that led to a bad outcome, adjust.
    You can reference dynamic strategy points to refine your approach, but do not apply rigidly.
    Keep your strategy notes concise (3-5 sentences).
    This is private and will not be shared with other players.
"""


DAY_VOTE_MEMORY_CONTEXT = """
Relevant observations: (These are specific, detailed observations from past games that are relevant to the current situation):
{retrieved_observations}

Dynamic strategy points (strategies from past games relevant to your current situation):
{strategy_points}

{adoption_instruction}
"""


SITUATION_ROLE_LENS = {
    "wolf": "Also note: which villager is most dangerous to leave alive, and whether the pressure on your team could be redirected.",
    "villager": "Also note: who is being evasive, voting inconsistencies, and unresolved accusations.",
    "healer": "Also note: who most needs protection, whether your activity level risks exposing you, and whether it's time to claim.",
    "investigator": "Also note: whether your private findings align with or contradict the public consensus, and whether your communication style is marking you as a power role.",
}


SITUATION_SUMMARY_PROMPT = """You are an AI agent playing Werewolf.
Your role: {player_role}
Current day: {current_day}, Round: {current_round}

Recent game events and discussion:
{recent_events}

Your current strategy note:
{previous_strategy}

{situation_standards}

Your role-specific lens:
{role_lens}

Describe 1-3 distinct situations you are currently facing. Each situation will
be used as a semantic search query to retrieve relevant strategy advice, so
describe the GAME DYNAMICS, not just who said what.

Do not describe the same conflict from multiple angles.

FORMAT: Write each situation as a 2-3 sentence description of a game dynamic
you are facing.

Do NOT include plans, recommendations, or what you should do. Only describe
what is happening.
"""


SITUATION_SUMMARY_SUFFIX = """
Your current strategy note:
{previous_strategy}

{situation_standards}

Your role-specific lens:
{role_lens}

Describe 1-3 distinct situations you are currently facing. Each situation will
be used as a semantic search query to retrieve relevant strategy advice, so
describe the GAME DYNAMICS, not just who said what.

Do not describe the same conflict from multiple angles.

FORMAT: Write each situation as a 2-3 sentence description of a game dynamic
you are facing.

Do NOT include plans, recommendations, or what you should do. Only describe
what is happening.
"""


VILLAGER_SITUATION_SUMMARY = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            """You are an AI agent playing Werewolf.
Your role: {player_role}
Current day: {current_day}, Round: {current_round}

Surviving players: {surviving_players}

Previous days summary:
{day_summaries}

Today's public discussion:
{day_channel}
"""
            + SITUATION_SUMMARY_SUFFIX,
        )
    ]
)


HEALER_SITUATION_SUMMARY = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            """You are an AI agent playing Werewolf.
Your role: {player_role}
Current day: {current_day}, Round: {current_round}

Surviving players: {surviving_players}

Previous days summary:
{day_summaries}

Today's public discussion:
{day_channel}
"""
            + SITUATION_SUMMARY_SUFFIX,
        )
    ]
)


INVESTIGATOR_SITUATION_SUMMARY = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            """You are an AI agent playing Werewolf.
Your role: {player_role}
Current day: {current_day}, Round: {current_round}

Surviving players: {surviving_players}
Your private investigation results:
{investigator_results}

Previous days summary:
{day_summaries}

Today's public discussion:
{day_channel}
"""
            + SITUATION_SUMMARY_SUFFIX,
        )
    ]
)


WOLF_SITUATION_SUMMARY = ChatPromptTemplate.from_messages(
    [
        (
            "human",
            """You are an AI agent playing Werewolf.
Your role: {player_role}
Current day: {current_day}, Round: {current_round}

Surviving villagers: {surviving_villagers}
Known surviving wolf allies: {surviving_wolves}

Previous days summary:
{day_summaries}

Today's public discussion:
{day_channel}

Wolf night chat visible to you:
{wolf_channel}
"""
            + SITUATION_SUMMARY_SUFFIX,
        )
    ]
)
