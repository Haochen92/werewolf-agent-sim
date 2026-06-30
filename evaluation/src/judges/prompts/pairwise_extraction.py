"""Prompt text for the pairwise extraction judge."""

PAIRWISE_EXTRACTION_SYSTEM_PROMPT = """\
You are comparing two sets of extracted observations and strategy points \
from the same Werewolf game, filtered to a single role's perspective. \
Score each output independently on eight dimensions, then choose the \
better output overall. Do not prefer an output just because it has more items.
"""


PAIRWISE_EXTRACTION_USER_PROMPT = """\
GAME CONTEXT:
- Roles: {roles}
- Outcome: {game_outcome}

GAME TRANSCRIPT:
{formatted_discussions}

AGENT STRATEGY NOTES DURING GAME:
{formatted_strategy_notes}

{situation_standards}

{epistemic_status_rule}

---

ROLE BEING EVALUATED: {role}

OUTPUT A ({label_a}, {num_observations_a} observations, \
{num_strategy_points_a} strategy points):

OBSERVATIONS:
{observations_a_formatted}

STRATEGY POINTS:
{strategy_points_a_formatted}

---

OUTPUT B ({label_b}, {num_observations_b} observations, \
{num_strategy_points_b} strategy points):

OBSERVATIONS:
{observations_b_formatted}

STRATEGY POINTS:
{strategy_points_b_formatted}

---

Score EACH output independently on these eight dimensions (1-5):

1. SPECIFICITY: Does the situation + dimensional fields make items \
distinctive for semantic search? 1=vague; 5=precisely scoped.

2. EPISTEMIC COMPLIANCE (strategy points ONLY): Do strategy points respect \
the role's knowledge level? 1=pervasive violations; 5=correct certainty level.

3. GROUNDING: Is every claim traceable to the game transcript? \
1=fabricated events; 5=every detail traceable.

4. COVERAGE: Do items cover the key strategic moments for this role? \
1=misses important dynamics; 5=captures all major decision points.

5. DIVERSITY: Are items distinct from each other? \
1=mostly duplicate; 5=every item adds a distinct idea.

6. PERSPECTIVE COMPLIANCE (observations ONLY): Are observations written \
from the assigned role's perspective? 1=opposing side's actions described; \
5=consistently framed from assigned role.

7. STRATEGY DEPTH (strategy points ONLY): Does the action field provide \
concrete conditions, specific action, and reasoning for WHY? \
1=generic platitudes; 5=specific technique with learned nuance.

8. NOVELTY: Does each item capture a non-obvious insight beyond \
common-sense fundamentals? 1=obvious advice; 5=surprising pattern.

Then choose the overall winner considering all dimensions.

Respond ONLY with valid JSON, no markdown fences:
{{"output_a": {{"specificity": N, "epistemic_compliance": N, \
"grounding": N, "coverage": N, "diversity": N, \
"perspective_compliance": N, "strategy_depth": N, "novelty": N, \
"brief_reasoning": "1-2 sentences"}}, \
"output_b": {{"specificity": N, "epistemic_compliance": N, \
"grounding": N, "coverage": N, "diversity": N, \
"perspective_compliance": N, "strategy_depth": N, "novelty": N, \
"brief_reasoning": "1-2 sentences"}}, \
"winner": "a or b or tie", "confidence": N, \
"brief_reasoning": "2-3 sentences explaining overall comparison"}}
"""
