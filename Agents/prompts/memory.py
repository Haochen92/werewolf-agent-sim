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


NIGHT_ACTION_MEMORY_CONTEXT = """
Relevant observations: (These are specific, detailed observations from past games that are relevant to your night decision):
{retrieved_observations}

Dynamic strategy points (strategies from past games relevant to your current situation):
{strategy_points}

{adoption_instruction}

Adaptive Strategic thinking:
    You have a private strategy note from your previous turns:
    {previous_strategy}

    Update your strategy notes based on new information and relevant observations. If your current
    approach resembles a pattern that led to a bad outcome, adjust. You can reference dynamic strategy
    points to refine your target choice, but do not apply rigidly. Keep your strategy notes concise
    (3-5 sentences). This is private and will not be shared with other players.
"""


SITUATION_ROLE_LENS = {
    "wolf": "Also note: which other player is most dangerous to leave alive — whether a strong villager or the serial killer as a rival faction competing for the win — and whether the pressure on your team could be redirected.",
    "villager": "Also note: who is being evasive, voting inconsistencies, and unresolved accusations.",
    "healer": "Also note: who most needs protection, whether your activity level risks exposing you, and whether it's time to claim.",
    "investigator": "Lead with how your private findings relate to the public narrative — do they confirm, contradict, or add nothing new? Also note whether your communication style is marking you as a power role.",
    "serial_killer": "Also note: who most threatens your survival (whether by closing in on you or by being a strong player), whether suspicion is drifting toward you, and how the wolf-vs-village fight is shaping the field you must outlast.",
    "vigilante": "Also note: whether you have a target worth spending a scarce bullet on and how confident you are, whether holding fire is wiser, and whether your behavior risks exposing you as a power role.",
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


SERIAL_KILLER_SITUATION_SUMMARY = ChatPromptTemplate.from_messages(
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


VIGILANTE_SITUATION_SUMMARY = ChatPromptTemplate.from_messages(
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


# ── v6 live situation summary (step 4C) — aligns the live query with the v6 post-game extraction ──
# Role-agnostic view (each role's payload only populates its own private fields, so this is leak-safe)
# + a v6 dimensional suffix mirroring the extraction dims. The per-cell situation schema is bound by
# the caller (with_structured_output), so the model fills only the fields its cell has. Describes board
# STATE only (Rule 2). Single prompt for all roles/phases; the schema does the tailoring.
V6_SITUATION_SUMMARY_SUFFIX = """
{epistemic_status_rule}

Describe 1-2 distinct situations you are currently facing using the structured fields. Each is used as
a semantic-search query to retrieve relevant past lessons, so describe GAME DYNAMICS, not just who said
what. Only write a second situation if it is a genuinely independent decision; two views of one
conflict is one situation.

Fill in ALL the structured fields your output schema requests (the set depends on your role and phase):
- situation: the core game dynamic (2-3 sentences) — the concrete event or conflict and who is
  involved. Do not restate the dimensional context captured by the other fields.
- information_landscape: what evidence exists and its type (information-rich vs starved).
- players_alive / distance_to_parity / is_swing: the EXACT criticality numbers right now — how many are
  alive; how many more eliminations until the leading evil faction reaches a game-ending parity;
  whether one result now flips which faction is winning.
- criticality_stakes: the IMPLICATION of those numbers as board reality (e.g. "seven alive, a mislynch
  is still recoverable" or "one elimination from a wolf win, every vote decisive"), derived FROM the
  numbers so the two cannot disagree.
- consensus_text / my_position / consensus_direction: how aligned the village is and on what basis;
  where you stand relative to it; whether it aligns with, opposes, or is unrelated to your own read.
- heat_now: how much suspicion rests on you right now, and on what basis.
- target_landscape: the candidate set this decision chooses among — who remains, their public role
  status, and whether the case against each rests on evidence or behavior.
- forward_exposure: the cost a contemplated visible move would carry going forward — what it would
  reveal or commit you to, and how reversible it is.
- public_private_text / divergence_sign: the gap between what you privately know (your role, findings,
  who you saved, a whiffed shot) and the public read, and whether it confirms or contradicts.

Describe board STATE only — no plans, recommendations, or what you should do.
"""


V6_SITUATION_SUMMARY = ChatPromptTemplate.from_messages(
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

Your private information (only what your role knows):
Investigation results: {investigator_results}
Wolf channel: {wolf_channel}
Vigilante results: {vigilante_results}

Your current strategy note:
{previous_strategy}
"""
            + V6_SITUATION_SUMMARY_SUFFIX,
        )
    ]
)
