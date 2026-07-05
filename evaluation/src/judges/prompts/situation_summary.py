"""Prompt text for the situation-summary rubric judge."""

SUMMARY_RUBRIC_SYSTEM_PROMPT = """\
You are evaluating a situation-summary output for an AI agent playing \
Werewolf. The summary will be used as semantic-search queries for retrieving \
relevant observations and strategy points from a memory store.

Score the output on five dimensions (1-5 each). Be strict — a score of 3 \
means adequate, 4 means good, 5 means excellent.\
"""


SUMMARY_RUBRIC_USER_PROMPT = """\
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

SITUATION SUMMARY OUTPUT:
{situations}

---

{summary_rubric}

Return ONLY valid JSON:
{{
  "faithfulness": <1-5>,
  "specificity": <1-5>,
  "retrieval_usefulness": <1-5>,
  "non_redundancy": <1-5>,
  "role_perspective": <1-5>,
  "brief_reasoning": "<1-2 sentences explaining the key strength or weakness>"
}}
"""


SUMMARY_RUBRIC = """\
Score each dimension from 1 to 5:

1. FAITHFULNESS: Does the summary avoid fabricating claims, roles, motives, \
or pressure not present in the visible discussion and private context?
   1 = major fabrications (invented accusations, wrong role attributions)
   2 = several claims not traceable to context
   3 = mostly faithful with minor embellishments
   4 = all major claims traceable, minor wording liberties
   5 = every claim directly traceable to the provided context

2. SPECIFICITY: Does the summary capture the current decision-relevant game \
dynamics rather than generic facts that could apply to any game state?
   1 = vague platitudes ("the village is divided", "trust is uncertain")
   2 = mentions topic but lacks situational detail
   3 = some specific dynamics but mixed with generic framing
   4 = well-grounded in current game state with specific details
   5 = precisely scoped to this moment's dynamics, names specific players/events

3. RETRIEVAL USEFULNESS: Would these situation descriptions retrieve \
strategy/observation memories that match the agent's current role, pressure, \
and phase?
   1 = would match irrelevant or random memories
   2 = too broad, would retrieve mostly noise
   3 = reasonable match but could be more targeted
   4 = would retrieve relevant memories for the role and situation
   5 = would retrieve highly targeted advice for this exact scenario

4. NON-REDUNDANCY: Does each listed situation add a distinct retrieval angle?
   1 = mostly the same dynamic restated differently
   2 = significant overlap between situations
   3 = some overlap but each adds something
   4 = mostly distinct angles with minor overlap
   5 = every situation adds a clearly unique retrieval angle

5. ROLE PERSPECTIVE: Does the summary preserve what this role privately knows \
and frame situations from the agent's perspective?
   1 = ignores role entirely, reads like an omniscient narrator
   2 = mentions role but doesn't incorporate private knowledge
   3 = some role grounding but inconsistent perspective
   4 = well-grounded in role with private knowledge integrated
   5 = fully framed from the agent's perspective with role-specific concerns\
"""
