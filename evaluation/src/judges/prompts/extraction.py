"""Prompt text for the postgame-extraction judge."""

EXTRACTION_SYSTEM_PROMPT = """\
You are evaluating the quality of observations and strategy points extracted \
from a completed Werewolf game. The extraction model was given the full game \
transcript and asked to produce episodic memories (observations) and tactical \
principles (strategy points) that will be stored for future games.

Your job is to score the extraction output on eight dimensions. You will be \
given the game context, the game transcript, and the full set of extracted \
items.
"""


EXTRACTION_USER_PROMPT = """\
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

EXTRACTED OBSERVATIONS ({num_observations} items):
{observations_formatted}

EXTRACTED STRATEGY POINTS ({num_strategy_points} items):
{strategy_points_formatted}

---

Score the following five dimensions from 1 to 5:

1. SPECIFICITY: Evaluate the situation field TOGETHER with its dimensional \
fields (information landscape, game phase, consensus texture, agent exposure) \
as a single composed search query. Does the combined text make it distinctive \
enough for semantic search to match only similar game dynamics?
   1 = vague enough to match any game even with dimensional fields
   2 = dimensional fields present but generic (e.g. "mid-game" without what changed)
   3 = some dimensional grounding but could be more precise
   4 = well-grounded with most relevant dimensions qualified with specific detail
   5 = precisely scoped — would match only situations with similar dynamics

2. EPISTEMIC COMPLIANCE (strategy points ONLY — ignore observations for this \
dimension): Do strategy points respect the assigned role's knowledge level? \
Observations are factual post-game records and may use omniscient knowledge. \
Strategy points are reusable advice served to agents during gameplay, so they \
must describe roles at the correct certainty level for the perspective role. \
Own findings and system-confirmed roles are valid; hidden ground truth or \
omniscient narrator perspective is a violation.
   1 = pervasive violations — uses hidden roles and omniscient perspective
   2 = several strategy points use ground truth not available to the role
   3 = mostly compliant with isolated lapses
   4 = strong compliance, roles described at correct certainty level
   5 = every claim at the correct certainty level for the role

3. GROUNDING: Is every claim traceable to the game transcript?
   1 = major fabricated events or dynamics
   2 = some invented context not in the transcript
   3 = minor embellishments but core facts are grounded
   4 = well grounded with trivial paraphrasing
   5 = every detail traceable to the source transcript

4. COVERAGE: Do the extracted items collectively cover the key strategic \
moments and learnings from this game for each role?
   1 = misses the most important dynamics
   2 = captures some events but misses key turning points
   3 = covers the main events but misses subtler dynamics
   4 = good coverage of major and some minor decision points
   5 = captures all major strategic moments across roles

5. DIVERSITY: Are the extracted items distinct from each other?
   1 = mostly duplicate advice in different words
   2 = significant overlap between items
   3 = some redundancy but enough distinct ideas
   4 = mostly distinct with minor thematic overlap
   5 = every item adds a distinct strategic idea

6. PERSPECTIVE COMPLIANCE (observations ONLY — ignore strategy points for \
this dimension): Is each observation written from the assigned role's \
perspective across all three narrative fields (situation, approach, outcome)?
   - situation should describe what the assigned role is facing
   - approach should describe what the assigned role DID or FAILED TO DO — \
not what the opposing side did. If an observation's approach says "The wolves \
identified..." in an Investigator observation, that is a perspective violation.
   - outcome should describe consequences from the assigned role's viewpoint
   1 = pervasive violations — approach routinely describes opposing side's actions
   2 = several observations frame approach from the wrong perspective
   3 = mostly compliant with isolated perspective slips
   4 = strong compliance, minor framing issues at most
   5 = every observation is consistently framed from the assigned role's perspective

7. STRATEGY DEPTH (strategy points ONLY — score 5 for observations-only \
sets): Does the action field provide concrete conditions, a specific \
recommended action, and reasoning for WHY it works in this context?
   1 = generic platitudes ("be careful", "don't reveal your role")
   2 = names an action but no conditions or reasoning
   3 = concrete action but reasoning is thin or obvious
   4 = specific technique with conditions and some reasoning
   5 = specific technique with conditions, reasoning, and learned nuance \
(e.g., "investigate players who voted latest on the eliminated wolf — \
wolves bandwagon late to blend in")

8. NOVELTY: Does each item capture a non-obvious mechanism or insight, or \
does it restate common-sense fundamentals that any experienced player knows? \
Evaluate both observations and strategy points.
   1 = obvious advice ("eliminate active players", "protect important players")
   2 = slightly beyond basics but widely known tactics
   3 = reasonable insight but not surprising to an experienced player
   4 = captures a non-obvious mechanism or pattern
   5 = reframes how you'd approach the situation, surfaces a surprising \
pattern or second-order effect

Respond ONLY with valid JSON, no markdown fences:
{{"specificity": N, "epistemic_compliance": N, "grounding": N, \
"coverage": N, "diversity": N, "perspective_compliance": N, \
"strategy_depth": N, "novelty": N, \
"brief_reasoning": "2-3 sentences explaining your scores"}}
"""
