"""Day-discussion prompt templates, built from the role cards (Agents/prompts/roles/).

Every role's template is the same scaffold — the rules block, the role's identity and discussion
framing, the discussion tone/response-format, and a shared transcript block (previous-day
summaries + today's discussion) — around the card's framing and context. The discussion-only
tone/silence/response-format blocks live here (not in common) since only the discuss phase uses
them.
"""

from importlib import import_module

from langchain_core.prompts import ChatPromptTemplate

from Agents.prompts.common import (
    READS_COMMIT_INSTRUCTION,
    REASONING_DISCIPLINE,
    build_system_prompt,
)
from Agents.prompts.memory import DAY_DISCUSSION_MEMORY_CONTEXT


TONE_INSTRUCTION = """
Speak naturally and conversationally, like you're playing a casual game with friends.
Keep statements short and direct. Don't over-explain your reasoning in a single message.
Avoid formal or legalistic phrasing — say "you still haven't answered" not
"your continued avoidance of this specific question makes your deflections increasingly suspicious."
Avoid canned openers and filler — don't start with "I agree with X that...", "fair point",
"good point", "classic wolf move", and don't mirror the structure of the message before yours.
A short reaction is fine; not every turn needs a full paragraph. If you agree with someone, add
a new reason or a new piece of information rather than just seconding what they said.
Keep your message short: usually 2-3 sentences, about 40-80 words. Make one main point, with
the evidence needed to understand it.
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


ENGAGE_WITH_DISCUSSION_RULE = """
Engage with what has already been said. Read the transcript above before you speak. Do NOT restate a
point another player has already made — an opener like "I agree we can't keep abstaining", "we should
be careful", or "X seems suspicious" adds nothing once someone has already said it, and four players
saying the same thing wastes the day. When you speak, do exactly one of:
- add genuinely NEW information: a specific fact, a concrete read, a challenge, or a proposal not yet
  raised, or
- explicitly build on a prior point by NAMING the player who made it and advancing it — give a new
  reason, draw out a consequence, or push it to a concrete next step. Naming-and-advancing is not the
  same as seconding: "I agree with X" on its own is a restatement, not engagement.
"""


OPENING_ROUND_RULES = """
== Opening round ==
Prepare your opening speech for the start of a day. Every living player will get a chance to speak, without 
knowing what others had made in their opening speech. 
The speech should only include any one of the following 3 scenarios: 
1. Claim your role, if the town does not already know it, or counterclaim another player's claim to the same role. 
2. Share new information from the night that the town does not yet have: the night, whom you targeted, what you learned. A result the morning report already made public, such as a dead player's role, is not news.
3. Challenge a claim made on an earlier day, with a reason.

Deductions, suspicions, advice and general comments wait for the discussion, where they can answer
today's claims. If none of the three applies to you, set pass_turn=true: passing is the normal
answer here, and a statement of another kind is removed before anyone reads it.
Length: one or two sentences, not the usual message length.
"""

# Day 1 has no vote; appended to the opening block on that day.
DAY_ONE_NO_VOTE_RULES = """
== Day 1: no vote ==
Today is the first day. There is little public information, and no elimination vote will be held
today. You are not required to manufacture a read or commitment; passing is equally valid.
"""

PROACTIVE_ROUND_RULES = """
== Open floor ==
You have the floor because you have not spoken since the day began (or since the floor last went
round). Make one or two useful points: a concrete observation or read with the evidence it rests
on, a contradiction you noticed, or a proposal for what to test. Build on what is already in the
transcript rather than repeating it: a point the table has already heard is held back and nobody
hears it. If you have nothing new to add, set pass_turn=true; a pass costs nothing here.
"""

CLOSING_ROUND_RULES = """
== Closing defence ==
The discussion is over, and you have been called to give a last word before the vote: the
moderator's line above names who accused you. Answer the case against you — explain, correct, or
point to what your accusers have overlooked. Do not open a new accusation. Nobody replies to this
turn; the vote follows at once.
Length: two to four sentences.
"""


# --- Shared transcript framing ---

# Prompt-cache layout rule (sections ordered by volatility): the header keeps only the per-DAY
# line; the per-TURN firing_brief lives AFTER the transcript (_FIRING_BRIEF) with the other
# per-turn material (memory context). With everything above the transcript day-stable and the
# transcript append-only, each turn's prompt is a strict prefix-extension of the previous one —
# which is what automatic prefix caching (DeepSeek/OpenAI) needs. Putting the brief back up top
# re-prefills the whole transcript every turn.
_DISCUSS_HEADER = """
Day {current_day} discussion.
"""

_FIRING_BRIEF = """
{firing_brief}
"""

_DISCUSSION_STAGE_RULES = """
{discussion_stage_rules}
"""

_DISCUSS_TRANSCRIPT = """
== Dead so far (public) ==
{dead_roster}

== Roles still in play (fixed cast minus revealed deaths) ==
{alive_roles}

== Previous days ==
{day_summaries}

== Today's discussion ==
{day_channel}
=========================
"""


# --- The ten-seat discussion ---
# The rules block arrives as the {preamble} input, composed per game from the dealt lineup
# (compose.preamble).

# The two examples, in the schema's field order. The example read and the example claim name no
# role and no seat, since a named one gets copied (discussion_evidence.md section 7.5).
DAY_DISCUSS_RESPONSE_FORMAT = """
You must respond with a valid JSON.

When speaking:
{{
    "strategy_verdicts": [{{"strategy_index": 1, "verdict": "follow", "why": "short reason vs your current board"}}],
    "memory_applicability": [{{"memory_index": 1, "verdict": "partly_applies", "why": "short reason vs your current board"}}],
    "reads": [{{"player": "<exact player_id>", "why": "pushed the only counted lynch with no evidence", "suspected_role": "<a role from the line-up, or unclear>", "confidence": "low"}}],
    "updated_strategy": "your updated private strategy note for future turns",
    "pass_turn": false,
    "message": "your discussion message",
    "claim": "<the role this message claims you hold, or none>",
    "addressed_targets": [{{"target": "<exact player_id>", "addressed_form": "response", "stance": "defense"}}]
}}

When declining to speak (only if you were NOT directly addressed):
{{
    "strategy_verdicts": [{{"strategy_index": 1, "verdict": "not_relevant", "why": "short reason vs your current board"}}],
    "memory_applicability": [{{"memory_index": 1, "verdict": "does_not_apply", "why": "short reason vs your current board"}}],
    "reads": [{{"player": "<exact player_id>", "why": "unchanged", "suspected_role": "unclear", "confidence": "low"}}],
    "updated_strategy": "your updated private strategy note for future turns",
    "pass_turn": true,
    "message": "",
    "claim": "none",
    "addressed_targets": []
}}
"""


def day_discuss_template(role: str) -> ChatPromptTemplate:
    """A dealt role's day discussion turn, from its card."""
    card = import_module(f"Agents.prompts.roles.{role}").CARD
    words = card.day_discuss
    system = build_system_prompt(
        "{preamble}", REASONING_DISCIPLINE, card.playstyle, words.framing, TONE_INSTRUCTION, DAY_DISCUSS_RESPONSE_FORMAT,
    )
    human = (
        "{tell_book}" + READS_COMMIT_INSTRUCTION
        + _DISCUSS_HEADER + words.context + _DISCUSS_TRANSCRIPT + _DISCUSSION_STAGE_RULES
        + words.trailer + _FIRING_BRIEF + DAY_DISCUSSION_MEMORY_CONTEXT
        + DISCUSSION_SILENCE_RULE + ENGAGE_WITH_DISCUSSION_RULE
    )
    return ChatPromptTemplate.from_messages([("system", system), ("human", human)])
