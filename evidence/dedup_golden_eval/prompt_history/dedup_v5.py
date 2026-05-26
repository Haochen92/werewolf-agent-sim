"""Dedup prompts v5.

Source: git show c59570c^:Agents/prompts/dedup.py (parent of c59570c)

Key changes from v4:
- Removed "doubt -> M over K" calibration that biased toward MERGE
- Added "MERGE is the rarest outcome" framing (not yet present; that was
  added implicitly via the flat decision rules favoring D and K)
- Restructured into clearer decision rules: "same lesson, different words"
  is DISCARD; different approach wording alone does NOT justify KEEP
- DISCARD defined as exact duplicate (situation + approach + outcome same)
- MERGE defined around same situation/outcome with different tactic variant
- KEEP only when situation meaningfully different OR outcome genuinely differs
- Single-pass decision test: "would the agent make a different strategic
  decision based on reading the new observation versus the existing one?"

Strategy prompt was unchanged from v4 through v6 (only observation prompt
changed between v5 and v6).
"""

STRATEGY_DEDUP_PROMPT = """
You are maintaining a strategy database for an AI Werewolf agent. A new
strategy point has just been extracted from a game. Your job is to compare
it against the most similar existing entries and decide how to integrate it.

{situation_standards}

{epistemic_status_rule}

All situation fields you write or rewrite must conform to the standards and
epistemic status rule above.
For the structured output field named "decision", use exactly the letter tag
"D" or "K".

---

NEW EXTRACTION:
Role: {new_role}
Situation: {new_situation}
Action: {new_action}

SIMILAR EXISTING ENTRIES ({total_similar_count} entries above similarity
threshold; top {top_n} shown):
{existing_entries}

---

Decide ONE of the following outcomes:

(D) DISCARD — The new point expresses the same hypothesis as an existing
    entry. Both describe the same situation and recommend the same action
    direction — the agent reading one entry vs the other would do the same
    thing. Differences in wording, phrasing, or emphasis do not make entries
    distinct.

    Output: the candidate number it duplicates. If the new entry is better
    written — more specific situation dimensions, more actionable advice, or
    captures a concrete detail the existing entry lacks — output the improved
    situation and action fields to overwrite the existing entry. Do not add
    dimensional fields (information landscape, consensus texture, agent
    exposure, game phase) that neither entry contains; only reorganize or
    clarify what is already stated. If roughly equal or the existing entry is
    better, output only the candidate number with no rewrite.

(K) KEEP — The new point is genuinely novel. Either the situation is
    meaningfully different (different game phase, information landscape,
    consensus texture, or agent exposure), OR the action recommends a
    different choice that would lead the agent to a different target,
    different timing, or different risk tradeoff. The new entry is stored
    exactly as extracted with no rewrites.

DECISION TEST:
Place an agent in the situation described. Would it take a different action
after reading the new entry than it would after reading the existing entry?
Apply this concretely:

- Different TARGET: "target the leader" vs "target a quiet moderate" → KEEP.
- Different TIMING: "act immediately" vs "wait for more evidence" → KEEP.
- Different RISK TRADEOFF: "accept healer risk for disruption" vs "avoid
  healer risk for guaranteed kill" → KEEP.
- Different SCOPE: "target the most vocal player" vs "target the most vocal
  player, but only if no healer save was announced" — the second adds a
  situational condition that changes when the action applies → KEEP.
- Different WORDS, SAME ACTION: "target the vocal player" vs "target the
  organizer" vs "target the player taking charge" → DISCARD. On the ground,
  these point to the same player.
- Different REASONING, SAME ACTION: "kill the leader to prevent coordination"
  vs "kill the leader because they might be the Investigator" → DISCARD.
  The agent does the same thing regardless of the reasoning.

CALIBRATION NOTE:
When in doubt, DISCARD. Over-discarding is recoverable — a genuinely novel
tactic will be re-extracted from a future game. Under-discarding creates
permanent retrieval pollution that requires batch cleanup.

DECISION RULES:
- For DISCARD, the existing entry's observation_count will be incremented
  automatically. If you provide a rewrite, it replaces the existing entry's
  text while preserving the accumulated count.
- For DISCARD with rewrite, use only details present in the entries being
  compared. Do not infer or invent context not explicitly stated.
- When an output field asks for a candidate number, use only the bracketed
  candidate number shown in SIMILAR EXISTING ENTRIES. Do not output UUID
  keys.

Output format:
DECISION: [D / K]
REASONING: [2-3 sentences explaining your application of the decision test]
[Then the relevant output for your decision as specified above]
"""


OBSERVATION_DEDUP_PROMPT = """
You are maintaining an episodic observation database for an AI Werewolf agent.
A new observation has just been extracted from a game. Your job is to compare
it against the most similar existing observations and decide how to integrate
it.

Observations have three structured fields:
- situation: The game conditions (used for semantic search matching)
- approach: What the agent did
- outcome: What resulted

For the structured output field named "decision", use exactly the letter tag
"D", "M", or "K"; do not use DISCARD, MERGE, or KEEP.

---

NEW OBSERVATION:
Role: {new_role}
Situation: {new_situation}
Approach: {new_approach}
Outcome: {new_outcome}

SIMILAR EXISTING OBSERVATIONS ({total_similar_count} entries above similarity
threshold; top {top_n} shown):
{existing_entries}

---

Decide ONE of the following outcomes:

(D) DISCARD — The new observation is an exact duplicate of an existing
    observation. The situation, approach, AND outcome all express the same
    idea, even if worded differently. Output the candidate number of the
    entry it duplicates.

(M) MERGE — The new observation shares the same situation and the same
    functional outcome as an existing observation, but records a different
    specific tactic in the approach field. This includes cases where the
    agent tried a different excuse, defense, accusation, or voting pattern
    but achieved the same result for the same structural reason.
    Output the candidate number to merge with and the final merged
    observation fields (situation, approach, outcome). The merged approach
    field MUST list ALL distinct tactics from both entries. The merged
    outcome field summarizes the shared lesson. Increment observation_count
    to reflect the combined total.

(K) KEEP — The new observation is genuinely novel. Either the situation is
    meaningfully different, or the outcome differs from all existing entries.
    The new entry is stored exactly as extracted with no rewrites.

DECISION RULES:
- "Same lesson, different words" is a duplicate (D).
- If the situation and outcome are functionally identical, different approach
  wording alone does NOT justify KEEP. Multiple tactics that fail (or succeed)
  for the same structural reason are one lesson, not separate observations.
  Use MERGE (M) to accumulate the tactic variants.
- Use KEEP (K) only when the situation is meaningfully different OR the outcome
  genuinely differs from all candidates.
- The test for MERGE vs KEEP: would the agent make a different strategic
  decision based on reading the new observation versus the existing one? If
  the lesson is "this category of tactic fails in this situation," adding
  another example of the same category does not change the decision — MERGE it.
- For MERGE, the rewritten observation must keep each field (situation,
  approach, outcome) as separate coherent text. Use only details present in
  the entries being compared. Do not infer or invent context not explicitly
  stated in the input entries.
- When an output field asks for a candidate number, use only the bracketed
  candidate number shown in SIMILAR EXISTING OBSERVATIONS. Do not output
  UUID keys.
"""
