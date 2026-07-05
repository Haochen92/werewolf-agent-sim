"""Prompt text for the pairwise situation-summary judge."""

PAIRWISE_SUMMARY_SYSTEM_PROMPT = """\
You are comparing two situation-summary outputs for an AI agent playing \
Werewolf. The summaries will be used as semantic-search queries for retrieving \
relevant observations and strategy points.

Score each output independently on five dimensions, then choose the better \
output overall. Do not prefer a summary just because it is longer.\
"""


PAIRWISE_SUMMARY_USER_PROMPT = """\
AGENT CONTEXT:
- Player: {player_id}
- Role: {player_role}
- Day {day}, Round {round}
- Action phase: {action_phase}

TODAY'S DISCUSSION AVAILABLE TO THE AGENT:
{day_channel_excerpt}

PRIVATE CONTEXT AVAILABLE TO THE AGENT:
{private_context}

---

OUTPUT A ({output_a_label}):
{output_a}

---

OUTPUT B ({output_b_label}):
{output_b}

---

{summary_rubric}

Score EACH output on these five dimensions, then choose the overall winner.

Return ONLY valid JSON:
{{
  "output_a": {{
    "faithfulness": <1-5>,
    "specificity": <1-5>,
    "retrieval_usefulness": <1-5>,
    "non_redundancy": <1-5>,
    "role_perspective": <1-5>
  }},
  "output_b": {{
    "faithfulness": <1-5>,
    "specificity": <1-5>,
    "retrieval_usefulness": <1-5>,
    "non_redundancy": <1-5>,
    "role_perspective": <1-5>
  }},
  "winner": "a" | "b" | "tie",
  "confidence": <1-5>,
  "brief_reasoning": "1-2 sentences explaining the comparison"
}}
"""
