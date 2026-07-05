"""Prompt text for the final-action application judge."""

APPLICATION_SYSTEM_PROMPT = """\
You are evaluating an AI Werewolf agent's action after it was given retrieved
episodic memories. Focus only on whether the final action and private strategy
update use the provided memory appropriately for the current game state.
"""


APPLICATION_USER_PROMPT = """\
AGENT CONTEXT:
- Role: {player_role}
- Day {day}, Round {round}
- Action phase: {action_phase}

TODAY'S DISCUSSION AVAILABLE TO THE AGENT:
{day_channel_excerpt}

PRIVATE CONTEXT AVAILABLE TO THE AGENT:
{private_context}

SITUATION SUMMARY USED FOR RETRIEVAL:
{situations}

RETRIEVED OBSERVATIONS:
{observations_formatted}

RETRIEVED STRATEGY POINTS:
{strategy_points_formatted}

AGENT'S RESPONSE OR DECISION:
{agent_decision}
Updated Strategy Note: {agent_updated_strategy}
Adoption Self-Report: {agent_adoption_report}

Score from 1 to 5:

1. ACTION QUALITY: Is the action itself strategically appropriate for this
role and game state?
   1 = actively harmful or incoherent
   2 = weak or poorly justified
   3 = plausible but generic
   4 = strong and context-aware
   5 = excellent, specific, and well adapted to the current pressure

2. STRATEGY APPLICATION: Does the action or updated strategy use the retrieved
observations and strategy points discriminantly?
   1 = ignores useful retrieved guidance
   2 = weak connection to retrieved guidance
   3 = loosely aligned but could be coincidental
   4 = clearly adapts useful retrieved guidance
   5 = selectively applies the most relevant guidance while ignoring bad fits

3. GROUNDING: Does the agent's response and updated strategy note only
reference events, statements, accusations, and alliances that appear in
the discussion excerpt, private context, or retrieved memories?
   1 = multiple fabricated claims (invented votes, fake accusations, or
       events that never happened)
   2 = one clear fabrication that influences the decision
   3 = minor embellishment but core reasoning is grounded
   4 = fully grounded with at most trivial paraphrasing liberties
   5 = every claim traces directly to provided context

For Grounding, Look specifically for:
- Player statements or accusations not in the discussion
- Alliances or suspicions attributed to players without evidence
- References to events from previous days not in retrieved memories
- Invented vote counts or consensus that doesn't exist

4. ADOPTION ACCURACY: Does the agent's self-reported adoption list match its
observable behavior? Compare the strategy points the agent claimed to use
against what its action and reasoning actually reflect.
   1 = adoption list is clearly fabricated (claims points it visibly ignored,
       or omits points it clearly used)
   2 = significant mismatch between claims and observable behavior
   3 = partially accurate — some claimed points are reflected, others are not
   4 = mostly accurate with minor over- or under-attribution
   5 = adoption list precisely matches observable strategy use
   If the adoption self-report says "(not captured)", output null for this
   dimension and for attribution_direction — do not guess or infer.

5. ATTRIBUTION DIRECTION: Based on your adoption accuracy analysis, classify
the direction of mismatch:
   "over" = agent claims strategy points it did not observably follow
   "under" = agent omits strategy points it clearly used
   "accurate" = self-report matches observable behavior
   If adoption self-report says "(not captured)", output null.

If the retrieved memories are mostly irrelevant, do not reward blind use of
them. A good agent should ignore irrelevant memories and still take a sound
action.

Respond ONLY with valid JSON:
{{
  "action_quality": N, "strategy_application": N,
  "grounding": N, "adoption_accuracy": N_or_null,
  "attribution_direction": "over"|"under"|"accurate"|null,
  "fabricated_claims": ["list any specific fabrications found, or empty"],
  "brief_reasoning": "1-2 sentences"
}}
"""
