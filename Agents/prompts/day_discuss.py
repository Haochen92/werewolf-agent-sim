"""Day-discussion prompt templates: each surviving role's discuss ChatPromptTemplate.

Every template is the same scaffold — GAME_PREAMBLE, the role's CORE_STRATEGY, the discussion
tone/response-format, and a shared transcript block (previous-day summaries + today's discussion) —
wrapped around two role-specific pieces: a framing paragraph and the one info line that role is given
(its private results, or the wolf rosters). The `_discuss_template` factory holds the shared text once
so each role is a one-line table entry. Wolf is the structural outlier: roster framing + a cover
reminder. The discussion-only tone/silence/response-format blocks live here (not in common) since only
the discuss phase uses them.
"""

from langchain_core.prompts import ChatPromptTemplate

from Agents.prompts.common import GAME_PREAMBLE, build_system_prompt
from Agents.prompts.memory import DAY_DISCUSSION_MEMORY_CONTEXT
from Agents.prompts.roles import (
    HEALER_CORE_STRATEGY,
    INVESTIGATOR_CORE_STRATEGY,
    SERIAL_KILLER_CORE_STRATEGY,
    VIGILANTE_CORE_STRATEGY,
    VILLAGER_CORE_STRATEGY,
    WOLF_CORE_STRATEGY,
)


TONE_INSTRUCTION = """
Speak naturally and conversationally, like you're playing a casual game with friends.
Keep statements short and direct. Don't over-explain your reasoning in a single message.
Avoid formal or legalistic phrasing — say "you still haven't answered" not
"your continued avoidance of this specific question makes your deflections increasingly suspicious."
Avoid canned openers and filler — don't start with "I agree with X that...", "fair point",
"good point", "classic wolf move", and don't mirror the structure of the message before yours.
A short reaction is fine; not every turn needs a full paragraph. If you agree with someone, add
a new reason or a new piece of information rather than just seconding what they said.
"""


DISCUSSION_SILENCE_RULE = """
Silence rule:
If you were directly addressed (asked a question or accused), you MUST respond this turn:
set pass_turn=false and answer or defend.
Otherwise, speak only if you have at least one of:
1. A new concrete observation not yet discussed.
2. A change in your suspicion with new reasoning.
3. Role-specific private information that makes speaking strategically necessary.
If none of those apply, set pass_turn=true to decline this turn.
Do NOT restate suspicions, repeat appeals for information, or agree without adding new reasoning.
When there is no concrete information yet, don't manufacture suspicion out of how talkative, quiet,
aggressive, or cautious someone is — it's acceptable to say there's little to go on. If you want to
move things forward, prefer information-generating moves: propose a concrete test, point to a
specific contradiction, or track the voting record once there is one.
"""


DAY_DISCUSS_RESPONSE_FORMAT = """
You must respond with a valid JSON.

When speaking:
{{
    "adopted_strategy_keys": [1, 3],
    "memory_applicability": [{{"memory_index": 1, "verdict": "partly_applies", "why": "short reason vs your current board"}}],
    "pass_turn": false,
    "message": "your discussion message",
    "updated_strategy": "your updated private strategy note for future turns",
    "addressed_targets": [{{"target": "player_2", "addressed_form": "response", "stance": "defense"}}]
}}

When declining to speak (only if you were NOT directly addressed):
{{
    "adopted_strategy_keys": [],
    "memory_applicability": [{{"memory_index": 1, "verdict": "does_not_apply", "why": "short reason vs your current board"}}],
    "pass_turn": true,
    "message": "",
    "updated_strategy": "your updated private strategy note for future turns",
    "addressed_targets": []
}}
"""


# --- Shared transcript framing ---

_DISCUSS_HEADER = """
Day {current_day} discussion.
{firing_brief}
"""

_DISCUSS_TRANSCRIPT = """
== Previous days summary ==
{day_summaries}

== Today's discussion ==
{day_channel}
=========================
"""


# --- Factory ---

def _discuss_template(core_strategy, framing, context, *, trailer=""):
    """Build a day-discussion template from the shared scaffold.

    `framing` is the role's identity/goal paragraph, `context` the info line(s) it gets
    (surviving players + any private results), `trailer` an optional reminder after the
    transcript (only the wolf uses it, for the speak-like-a-villager cover note).
    """
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                build_system_prompt(
                    GAME_PREAMBLE,
                    core_strategy,
                    framing,
                    TONE_INSTRUCTION,
                    DAY_DISCUSS_RESPONSE_FORMAT,
                ),
            ),
            (
                "human",
                _DISCUSS_HEADER
                + context
                + _DISCUSS_TRANSCRIPT
                + trailer
                + DAY_DISCUSSION_MEMORY_CONTEXT
                + DISCUSSION_SILENCE_RULE,
            ),
        ]
    )


# --- Discussion templates ---

VILLAGER_DAY_DISCUSS = _discuss_template(
    VILLAGER_CORE_STRATEGY,
    """
You are {player_id}, a {player_role}.
""",
    """
Surviving players: {surviving_players}
""",
)


HEALER_DAY_DISCUSS = _discuss_template(
    HEALER_CORE_STRATEGY,
    """
You are {player_id}, the {player_role}.
During the day, speak as a normal villager while protecting your cover.
""",
    """
Surviving players: {surviving_players}
""",
)


INVESTIGATOR_DAY_DISCUSS = _discuss_template(
    INVESTIGATOR_CORE_STRATEGY,
    """
You are {player_id}, the {player_role}.
As the investigator, you can use your investigation result to guide your decision.
""",
    """
Surviving players: {surviving_players}
Investigation results: {investigator_results}
""",
)


WOLF_DAY_DISCUSS = _discuss_template(
    WOLF_CORE_STRATEGY,
    """
You are {player_id}, the {player_role}.
As the wolf, conceal your real identity and convince everyone else that you are a villager.
If any of your fellow wolf allies are suspected, try to convince the villagers otherwise
without revealing your own identity.
""",
    """Surviving villagers: {surviving_villagers}.
Surviving allies: {surviving_wolves}.
""",
    trailer="""Based on the discussion, try to speak like a villager. Do NOT reveal your allies identities.
""",
)


SERIAL_KILLER_DAY_DISCUSS = _discuss_template(
    SERIAL_KILLER_CORE_STRATEGY,
    """
You are {player_id}, the {player_role}.
You are playing alone against everyone. During the day, pose as an ordinary villager:
join the village's hunt for the threats, deflect suspicion from yourself, and never reveal that you
are the serial killer. You can be voted out, so blending in is survival.
""",
    """
Surviving players: {surviving_players}
""",
)


VIGILANTE_DAY_DISCUSS = _discuss_template(
    VIGILANTE_CORE_STRATEGY,
    """
You are {player_id}, the {player_role}.
You are on the village's side. Whether to stay hidden as an ordinary villager or to claim your role
is your own decision and can change with the situation: staying hidden keeps you safe, while
claiming — or hinting at what your shots have taught you — can lend weight to your reads but
paints a target on you (both the wolves and the serial killer gain from removing you).
""",
    """
Surviving players: {surviving_players}
What you have learned from your shots: {vigilante_results}
""",
)
