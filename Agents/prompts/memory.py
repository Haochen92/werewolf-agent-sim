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
In adopted_strategy_keys, list only strategy points whose advice your action \
follows (e.g. [1, 3]). Do not list points you read but acted against. An \
empty list is fine if none of the points match your action."""


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
    "investigator": "Lead with how your private findings relate to the public narrative — do they confirm, contradict, or add nothing new? Also note whether your communication style is marking you as a power role.",
}


SITUATION_SUMMARY_PROMPT = """You are an AI agent playing Werewolf.
Your role: {player_role}
Current day: {current_day}, Round: {current_round}

Recent game events and discussion:
{recent_events}

Your current strategy note:
{previous_strategy}

{situation_standards}

{epistemic_status_rule}

Your role-specific lens:
{role_lens}

Describe 1-2 distinct situations you are currently facing using the structured
fields. Each situation will be used as a semantic search query to retrieve
relevant strategy advice, so describe GAME DYNAMICS, not just who said what.

Only write a second situation if it captures a genuinely independent decision.
Two views of the same conflict is one situation, not two.

For each situation, fill in ALL structured fields:
- situation: The core game dynamic (2-3 sentences). Lead with the concrete
  event or conflict and who is involved. Do not embed dimensional context
  here — use the dedicated fields below.
- information_landscape: Evidence type and richness (1 sentence).
- game_phase: Phase and what changed recently (1 sentence).
- consensus_texture: Village alignment and driver (1 sentence).
- agent_exposure: Your position and basis (1 sentence).

Do NOT include plans, recommendations, or what you should do. Only describe
what is happening and the tension it creates.
"""


SITUATION_SUMMARY_SUFFIX = """
Your current strategy note:
{previous_strategy}

{situation_standards}

{epistemic_status_rule}

Your role-specific lens:
{role_lens}

Describe 1-2 distinct situations you are currently facing using the structured
fields. Each situation will be used as a semantic search query to retrieve
relevant strategy advice, so describe GAME DYNAMICS, not just who said what.

Only write a second situation if it captures a genuinely independent decision.
Two views of the same conflict is one situation, not two.

For each situation, fill in ALL structured fields:
- situation: The core game dynamic (2-3 sentences). Lead with the concrete
  event or conflict and who is involved. Do not embed dimensional context
  here — use the dedicated fields below.
- information_landscape: Evidence type and richness (1 sentence).
- game_phase: Phase and what changed recently (1 sentence).
- consensus_texture: Village alignment and driver (1 sentence).
- agent_exposure: Your position and basis (1 sentence).

Do NOT include plans, recommendations, or what you should do. Only describe
what is happening and the tension it creates.
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
