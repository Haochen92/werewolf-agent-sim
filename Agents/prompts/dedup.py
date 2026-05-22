PER_EXTRACTION_DEDUP_PROMPT = """
You are maintaining a strategy database for an AI Werewolf agent. A new
strategy point has just been extracted from a game. Your job is to compare
it against the most similar existing entries and decide how to integrate it.

{situation_standards}

{epistemic_status_rule}

All situation fields you write or rewrite must conform to the standards and
epistemic status rule above.
For the structured output field named "decision", use exactly the letter tag
"A", "B", "C", or "D"; do not use DISCARD, REPLACE, DIFFERENTIATE, or KEEP.

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

(A) DISCARD — The new point is a duplicate of an existing entry. Both the
    situation and action express the same idea, even if worded differently.
    Output: the candidate number of the entry it duplicates.

(B) REPLACE — The new point covers the same situation and action as an
    existing entry, but is more specific, better reasoned, or captures a
    nuance the existing entry misses. Output: the candidate number to
    replace, and the final merged situation + action (keeping the best
    elements of both).

(C) DIFFERENTIATE — The new point describes a similar situation but
    recommends a meaningfully different action. This is an action-spectrum
    case: both actions may be correct under slightly different conditions.
    Output: identify the situational variable that distinguishes them —
    typically one of: information landscape (what evidence exists), consensus
    texture (how strong or fragile agreement is), social pressure dynamics
    (who is driving accusations and how), or game phase (early/mid/endgame).
    Then rewrite BOTH situations to make the distinguishing variable explicit
    in the text. Do not split into more than 3 entries along any single
    variable.

(D) KEEP — The new point is genuinely novel. No existing entry covers this
    situation or this action. The new entry is stored exactly as extracted
    with no rewrites.

DECISION RULES:
- If the new point would be the 4th+ entry on the same spectrum, prefer
  merging it into the closest existing entry over creating another split.
- "Same idea, different words" is a duplicate, not a differentiation. The
  test: would a player in that situation do anything differently based on
  reading one entry vs. the other? If no, it is a duplicate.
- For REPLACE and DIFFERENTIATE, rewrites must only use details present in
  the entries being compared. Do not infer or invent game phase, information
  landscape, consensus texture, social pressure, or any other context not
  explicitly stated in the input entries. If insufficient detail exists to
  write a fully standards-compliant situation, preserve the original text
  rather than embellishing it.
- When an output field asks for a candidate number, use only the bracketed
  candidate number shown in SIMILAR EXISTING ENTRIES. Do not output UUID keys.

Output format:
DECISION: [A / B / C / D]
REASONING: [2-3 sentences explaining why]
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
"A", "B", "C", or "D"; do not use DISCARD, REPLACE, DIFFERENTIATE, or KEEP.

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

(A) DISCARD — The new observation is a duplicate of an existing observation.
    They describe the same situation, approach, and outcome, even if worded
    differently. Output the candidate number of the entry it duplicates.

(B) REPLACE — The new observation covers the same underlying event/dynamic as
    an existing observation, but is more specific, better causal, or captures
    important detail the existing entry misses. Output the candidate number to
    replace and the final merged observation fields (situation, approach,
    outcome).

(C) DIFFERENTIATE — The new observation is similar to an existing observation
    but records a meaningfully different situation, approach, or outcome. Output
    the distinguishing variable, then rewrite BOTH observations so each one
    clearly states the condition that makes it distinct.

(D) KEEP — The new observation is genuinely novel. No existing entry covers
    this situation, approach, and outcome. The new entry is stored exactly as
    extracted with no rewrites.

DECISION RULES:
- "Same event, same lesson, different words" is a duplicate.
- Prefer REPLACE over KEEP when the new observation mainly improves specificity
  for an existing memory.
- Use DIFFERENTIATE only when both observations should be retained because they
  would be retrieved for meaningfully different future game states.
- Rewritten or merged observations must keep each field (situation, approach,
  outcome) as separate coherent text.
- For REPLACE and DIFFERENTIATE, rewrites must only use details present in
  the entries being compared. Do not infer or invent game phase, information
  landscape, consensus texture, social pressure, or any other context not
  explicitly stated in the input entries. If insufficient detail exists to
  write a fully standards-compliant situation, preserve the original text
  rather than embellishing it.
- When an output field asks for a candidate number, use only the bracketed
  candidate number shown in SIMILAR EXISTING OBSERVATIONS. Do not output UUID
  keys.
"""


BATCH_STRATEGY_CLUSTER_DEDUP_PROMPT = """
You are cleaning a strategy-point memory database for an AI Werewolf agent.
The entries below are a candidate similarity cluster from one role namespace.

Each entry has:
- key: stable store key
- situation: the situation text used for semantic retrieval
- action: the recommended action
- observation_count: how often this memory has been observed

{situation_standards}

{epistemic_status_rule}

All situation fields you write or rewrite must conform to the standards and
epistemic status rule above.

Resolve this cluster using one or more operations. Every operation must use one
of these action values: DISCARD, REPLACE, DIFFERENTIATE, KEEP.

Rules:
- DISCARD means entries are duplicate strategy points. Choose one survivor_key;
  the apply step will preserve that key, sum counts, and delete absorbed keys.
- REPLACE means entries cover the same underlying situation/action and should
  become one better entry. Choose one survivor_key and provide merged_situation
  and merged_action.
- DIFFERENTIATE means similar entries should remain distinct, but their
  situations need rewriting to clarify the variable that separates them. Provide
  rewritten_entries using existing keys only. If you collapse many entries into
  fewer differentiated entries, source_keys should include all absorbed keys and
  rewritten_entries should include only the final survivor keys.
- KEEP means no change is needed for the listed source_keys.
- Use only keys shown in the cluster. Do not invent new keys.
- Prefer the fewest entries that preserve meaning. Avoid keeping 4+ entries on
  one spectrum when 2-3 differentiated entries would cover it.

Role: {role}

Cluster entries:
{entries}
"""


BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT = """
You are cleaning an episodic observation memory database for an AI Werewolf
agent. The entries below are a candidate similarity cluster from one role
namespace.

Observations have three structured fields:
- situation: The game conditions (used for semantic search matching). Should use
  agent roles, never player IDs, and be specific enough for retrieval.
- approach: What the agent did in that situation.
- outcome: What resulted — how others responded and the downstream consequences.

{situation_standards}

When you rewrite observations, keep each field (situation, approach, outcome)
as separate coherent text. Use the situation standards above to keep the
situation field specific enough for retrieval.

Resolve this cluster using one or more operations. Every operation must use one
of these action values: DISCARD, REPLACE, DIFFERENTIATE, KEEP.

Rules:
- DISCARD means entries are duplicate observations. Choose one survivor_key; the
  apply step will preserve that key, sum counts, and delete absorbed keys.
- REPLACE means entries describe the same underlying event/dynamic and should
  become one better observation. Choose one survivor_key and provide
  merged_situation, merged_approach, and merged_outcome.
- DIFFERENTIATE means similar observations should remain distinct, but their
  text needs rewriting to clarify the condition that separates them. Provide
  rewritten_entries using existing keys only. If you collapse many entries into
  fewer differentiated entries, source_keys should include all absorbed keys and
  rewritten_entries should include only the final survivor keys.
- KEEP means no change is needed for the listed source_keys.
- Use only keys shown in the cluster. Do not invent new keys.
- Prefer merging near-duplicates over preserving repeated memories.

Role: {role}

Cluster entries:
{entries}
"""
