"""Prompt text for the retrieved-memory relevance judge."""

RETRIEVAL_SYSTEM_PROMPT = """\
You are evaluating retrieved memory items for an AI Werewolf agent.
Judge both relevance to the current situation and qualitative redundancy.
"""


RETRIEVAL_USER_PROMPT = """\
You are checking whether retrieved {item_type} are useful for the current
Werewolf situation.

{situation_standards}

CURRENT RETRIEVAL QUERY SITUATIONS:
{situations}

RETRIEVED ITEMS:
{items}

STEP 1 — CLUSTER BY LESSON
Group the items by the strategic lesson they teach. Two items belong in the
same cluster if a player in this situation would not make a meaningfully
different decision after reading both versus reading just one.

For observations: the lesson is the tactical takeaway, NOT the specific
game anecdote. "Healer stayed quiet and survived" and "Healer stayed quiet
and the village won" teach the same lesson (low profile preserves the
Healer) even though the details differ. They belong in one cluster.

For strategy points: the lesson is the recommended action in context.
"Vote with consensus when under suspicion" and "Align with the majority
to reduce heat" are the same lesson. "Voice doubt but still vote with
consensus" is a different lesson.

If two items would cause the same behavioral change in the player, they
MUST share a cluster regardless of surface differences.

STEP 2 — SCORE

RELEVANCE (1-5): How useful is this set for the agent's current decision?
1 = unrelated to the current situation
2 = surface keyword match but different dynamics
3 = broadly topical but not actionable here
4 = mostly relevant, minor mismatches
5 = directly relevant and actionable for this role and decision

UNIQUE_LESSONS: The number of clusters from Step 1 that are relevant to
the current situation. Irrelevant clusters do not count.

EFFICIENCY (1-5): How much of the retrieved set carries unique value?
1 = nearly every item duplicates another; massive waste
2 = most items repeat a lesson already covered
3 = about half the items add a new lesson
4 = most items contribute a distinct lesson
5 = every item is the sole member of its cluster (zero waste)

Respond ONLY with valid JSON, no markdown fences:
{{
  "clusters": [
    {{
      "lesson": "5-10 word summary of the strategic takeaway",
      "items": [1, 4],
      "relevant": true
    }}
  ],
  "relevance": N,
  "unique_lessons": N,
  "efficiency": N,
  "brief_reasoning": "1-2 sentences"
}}
"""
