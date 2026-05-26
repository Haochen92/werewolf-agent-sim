"""Dedup prompts v6.

Source: git show c59570c:Agents/prompts/dedup.py

Key changes from v5:
- Observation prompt: added two-stage calibration cascade
  - Stage 1: "Different Trigger?" gates KEEP vs same-pattern
  - Stage 2: "Added Value?" gates DISCARD vs MERGE
- DISCARD redefined: existing entry "already covers everything" (not
  "exact duplicate"); subsumes new entry regardless of relative detail level
- MERGE redefined: new entry "adds a concrete detail the existing entry
  lacks" (tactic variant, specific example, contributing factor)
- KEEP redefined: "teaches a different lesson" based on structurally
  different trigger, detection signal, or outcome
- Added "MERGE is the rarest outcome" explicit framing
- Added "An agent reading this learns..." lesson-sentence requirement
  in REASONING
- Removed flat decision rules block; replaced with structured stage test
- Strategy prompt: unchanged from v5
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

(D) DISCARD — The existing entry already covers everything in the new
    entry. The situation, approach, and outcome all express the same idea,
    even if worded differently. No tactic variant, detection signal, or
    contributing factor is present in the new entry that the existing entry
    lacks. Output the candidate number it duplicates. The existing entry's
    observation_count will be incremented automatically.

(M) MERGE — The new entry covers the same situation structure and outcome
    as an existing entry, but adds a concrete detail the existing entry
    lacks: a tactic variant in the approach, a specific example of a
    general pattern, or a contributing factor absent from the existing text.
    Output the candidate number to merge with and the final merged
    observation fields (situation, approach, outcome). The merged approach
    field MUST list ALL distinct tactics from both entries.

(K) KEEP — The new entry teaches a different lesson. The triggering
    situation, detection signal, or outcome is structurally different from
    all existing entries. The agent must learn to recognize this trigger
    independently, even if the approach or response is similar. The new
    entry is stored exactly as extracted with no rewrites.

DECISION TEST — apply in two stages, in order.
In your REASONING, write out the lesson sentences before stating your
decision.

STAGE 1 — Different Trigger? (KEEP vs same-pattern):
Write the core lesson of the new entry and the closest candidate each as:
"An agent reading this learns..."

If the triggering situation or detection signal is structurally different,
KEEP. Stop here.

"Structurally different" means a different game event, role interaction,
or signal initiates the observation — not just different surface details
within the same type of situation:
- Different game event prompting the same analysis → KEEP.
  (e.g., "Investigator killed → analyze voting record" vs "wolf
  eliminated → analyze voting record" are different triggers even though
  the approach is the same.)
- Different wolf tactic requiring different detection → KEEP.
  (e.g., detecting "late bussing" vs detecting "partner protection")
- Different outcome (success vs failure of same approach) → KEEP.

Surface differences do NOT make triggers structurally different:
- Same tactic in a different game phase → same pattern.
- Same lesson at a different scale or degree → same pattern.

If the lessons address the same pattern, proceed to Stage 2.

STAGE 2 — Added Value? (DISCARD vs MERGE):
The entries cover the same pattern. Does the new entry contain anything
the existing entry lacks?

→ NOTHING NEW → DISCARD.
  If the existing entry already covers everything in the new entry,
  DISCARD — regardless of relative detail level. A longer or more
  specific new entry that describes the same lesson is still a discard
  when the existing entry already captures the principle.

→ CONCRETE VARIANT → MERGE.
  The new entry adds a tactic variant, a specific example of a general
  pattern, or a contributing factor not present in the existing text.
  (e.g., existing entry generalizes "wolves use misdirection in endgame";
  new entry adds the specific tactic of questioning healer save choices
  — merge to enrich the general pattern with a concrete instance.)

MERGE is the rarest outcome. Most cases are clear duplicates (DISCARD)
or genuinely different lessons (KEEP). Only choose MERGE when the new
entry demonstrably adds a concrete variant to an existing entry that
shares the same situation structure and outcome.

DECISION RULES:
- For MERGE, the rewritten observation must keep each field (situation,
  approach, outcome) as separate coherent text. Use only details present
  in the entries being compared. Do not infer or invent context not
  explicitly stated in the input entries.
- When an output field asks for a candidate number, use only the bracketed
  candidate number shown in SIMILAR EXISTING OBSERVATIONS. Do not output
  UUID keys.
"""
