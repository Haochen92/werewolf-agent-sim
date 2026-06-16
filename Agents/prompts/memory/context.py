"""Decision-time memory-injection blocks: the retrieved observations + strategy-points context
spliced into each day/night prompt, the strategy-adoption instruction, and the per-memory
applicability instruction (prompt-body delivery that drives full per-memory coverage)."""


ADOPTION_INSTRUCTION = """\
In adopted_strategy_keys, list only strategy points whose advice your action \
follows (e.g. [1, 3]). Do not list points you read but acted against. An \
empty list is fine if none of the points match your action."""


# Prompt-body delivery of the per-memory reasoning (the field description stays terse). Stating it in
# the body — not just the schema field — is what drives flash-lite to cover every memory rather than a
# scattered subset (forced_schema_screen: coverage 0.27 -> 0.97). Brace-free: safe to .format().
MEMORY_APPLICABILITY_INSTRUCTION = """
Before you decide, work through the numbered observations above ONE BY ONE: in memory_applicability,
output exactly one verdict for EACH numbered observation, in order — fully_applies, partly_applies, or
does_not_apply to your CURRENT board — each with a one-line why. Then act, applying each lesson only to
the degree its situation matches yours. If no observations are shown above, use an empty list.
"""


DAY_DISCUSSION_MEMORY_CONTEXT = """
Relevant observations: (These are specific, detailed observations from past games that are relevant to the current situation):
{retrieved_observations}
""" + MEMORY_APPLICABILITY_INSTRUCTION + """
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
""" + MEMORY_APPLICABILITY_INSTRUCTION + """
Dynamic strategy points (strategies from past games relevant to your current situation):
{strategy_points}

{adoption_instruction}
"""


NIGHT_ACTION_MEMORY_CONTEXT = """
Relevant observations: (These are specific, detailed observations from past games that are relevant to your night decision):
{retrieved_observations}
""" + MEMORY_APPLICABILITY_INSTRUCTION + """
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

