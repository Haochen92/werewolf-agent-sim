PER_EXTRACTION_DEDUP_PROMPT = """
You are maintaining a strategy database for an AI Werewolf agent. A new
strategy point has just been extracted from a game. Your job is to compare
it against the most similar existing entries and decide how to integrate it.

{situation_standards}

All situation fields you write or rewrite must conform to the standards above.
For the structured output field named "decision", use exactly the letter tag
"A", "B", "C", or "D"; do not use DISCARD, REPLACE, DIFFERENTIATE, or KEEP.

---

NEW EXTRACTION:
Role: {new_role}
Situation: {new_content}
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
    situation or this action. Output: confirm it should be added as-is, or
    suggest minor wording improvements.

DECISION RULES:
- If the new point would be the 4th+ entry on the same spectrum, prefer
  merging it into the closest existing entry over creating another split.
- "Same idea, different words" is a duplicate, not a differentiation. The
  test: would a player in that situation do anything differently based on
  reading one entry vs. the other? If no, it is a duplicate.
- For REPLACE and DIFFERENTIATE, the output must meet the quality bar in the
  situation standards above: the situation must describe a recognizable game
  dynamic using the dimensional framework and epistemic status rule. The
  action must explain a non-obvious mechanism, not restate common-sense play.
- When an output field asks for a candidate number, use only the bracketed
  candidate number shown in SIMILAR EXISTING ENTRIES. Do not output UUID keys.

Output format:
DECISION: [A / B / C / D]
REASONING: [2-3 sentences explaining why]
[Then the relevant output for your decision as specified above]
"""


BATCH_DEDUP_PROMPT = """
You are cleaning a strategy database for an AI Werewolf agent. Below are all
stored strategy points for the role of {role}. Each entry has a unique key,
a "content" field (the situation — this is what semantic search matches
against), and an "action" field (the recommended action).

{situation_standards}

All situation fields you write or rewrite must conform to the standards above.

---

ENTRIES:
{entries}

---

YOUR TASK: Identify clusters of entries that describe overlapping situations.

CLUSTER TYPES:

1. DUPLICATE — Multiple entries describe the same situation AND recommend
   the same action (even if worded differently). Test: would a player do
   anything differently after reading entry A vs. entry B? If no, they are
   duplicates.
   → Merge into a single entry. Produce one situation + action that keeps
   the best specificity from all entries in the cluster.

2. CONTRADICTION — Multiple entries describe the same situation but recommend
   actions that genuinely conflict (not just differ in degree). One says do
   X, another says the opposite of X.
   → First, check whether a genuine difference along one of the dimensional
   axes (information landscape, consensus texture, social pressure, game
   phase) justifies both actions. If yes, rewrite each entry's situation to
   make that difference explicit, and reclassify as an action-spectrum group.
   → If no genuine situational difference exists, flag as a true
   contradiction. Recommend which action to keep, with reasoning based on
   game-theoretic soundness.

3. ACTION-SPECTRUM — Multiple entries describe similar situations but
   recommend actions that vary by degree along a situational variable.
   → Identify the underlying variable — typically one of: information
   landscape, consensus texture, social pressure dynamics, or game phase.
   Collapse the spectrum into 2-3 entries maximum, each with a situation
   that explicitly encodes where on the variable it applies. Do not preserve
   more than 3 entries per spectrum.

---

For each cluster, output:

CLUSTER: [short descriptive label]
TYPE: [DUPLICATE / CONTRADICTION / ACTION-SPECTRUM]
KEYS: [list of entry keys]
REASONING: [why these belong together, and for contradictions/spectrums,
which dimensional variable distinguishes them]
PROPOSED RESOLUTION:
  [For duplicates: one merged situation + action]
  [For action-spectrums: 2-3 entries with distinct situations + actions]
  [For true contradictions: which to keep and why]

After listing all clusters, list any entries that do NOT belong to any
cluster (singletons). These require no action but confirm coverage.
"""
