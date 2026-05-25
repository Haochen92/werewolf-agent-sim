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
Action: {new_action}
Situation: {new_situation}

SIMILAR EXISTING ENTRIES ({total_similar_count} entries above similarity
threshold; top {top_n} shown):
{existing_entries}

---

SITUATION COMPARISON:
Two situations are functionally the same when a semantic search query
matching one would also retrieve the other. If not, they are different
situations — KEEP, even if the action advice is similar.

Check these dimensions — if any differs enough that a search query for
one would not match the other, the situations are different:
- Information landscape: information-rich vs information-starved changes
  which tactics are available.
- Agent exposure: the agent's position — credibility level, whether under
  suspicion, driving vs observing — changes the available action space.
  E.g., "confirmed non-wolf with high credibility" vs "general villager
  under suspicion" are different situations even if the trigger event
  (post-mislynch) is the same.
- Consensus texture: unified vs split vs no consensus changes social
  strategy.
- Game phase: early vs endgame changes stakes. BUT phase alone does not
  make situations different if the tactic and available information are
  the same.

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
    meaningfully different per the situation comparison above, OR the action
    recommends a different choice that would lead the agent to a different
    target, different timing, or different risk tradeoff. The new entry is
    stored exactly as extracted with no rewrites.

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
- Different CONFIDENCE POSTURE: "treat accusation as ground truth and act
  immediately" vs "probe to evaluate alignment before committing" — same
  direction but different certainty level → KEEP.
- Opposite ACTION for same situation: "defend the aggressive accuser" vs
  "challenge the accuser's motives" — conflicting strategies are by
  definition different hypotheses → KEEP.
- Different WORDS, SAME ACTION: "target the vocal player" vs "target the
  organizer" vs "target the player taking charge" → DISCARD. On the ground,
  these point to the same player.
- Different REASONING, SAME ACTION: "kill the leader to prevent coordination"
  vs "kill the leader because they might be the Investigator" → DISCARD.
  The agent does the same thing regardless of the reasoning.

BEFORE CHOOSING DISCARD — verify both conditions hold:
1. The situations are functionally the same per the situation comparison.
2. The recommended actions point in the same direction — same target type,
   same timing, same risk posture. If the entries recommend different or
   conflicting actions for the same situation, they are competing hypotheses
   — KEEP, not DISCARD.
Focus on what the agent would DO, not on how the entries are worded. If
both conditions hold, DISCARD even if the reasoning or phrasing differs.
If either fails, KEEP.

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

COMPARISON CRITERIA:

Before deciding D/M/K, evaluate each field independently:

SITUATION — "same" vs "different":
Decisive test: would a semantic search query matching situation A also
retrieve situation B? If not, they are different situations — KEEP, even
if the underlying lesson is similar. An observation only helps the agent
if it gets retrieved.

Check these dimensions — if any differs enough that a search query for
one would not match the other, the situations are different:
- Information landscape: information-rich vs information-starved changes
  which tactics are available. Different evidence types (voting record vs
  behavioral read vs role claim) change what signal the agent looks for.
- Consensus texture: unified village vs split village vs no consensus
  changes the agent's social strategy.
- Agent exposure: driving the push vs under suspicion changes the agent's
  risk calculus.
- Game phase: early vs endgame changes the stakes per action. BUT phase
  alone does not make situations different if the tactic and available
  information are the same.

APPROACH — "same" vs "different":
Two approaches are functionally the same when they point the agent toward
the same action on the ground — same target type, same timing, same method.
NOT different: wording ("target the leader" vs "target the organizer"),
reasoning (same action, different justification), degrees of persistence
(protecting 2 vs 3 times).
Different: different tactic category (accusation vs deflection vs role
claim), different detection method (voting record analysis vs behavioral
pattern recognition), different dimension targeted (timing-based vs
logic-based argument), one-off vs persistent pattern (investigating one
night vs committing to a multi-night strategy — this crosses a qualitative
threshold even though it looks like degree).

OUTCOME — "same" vs "different":
Two outcomes are functionally the same when they succeed or fail for the
same structural reason.
Same approach, opposite outcome (success vs failure) → always KEEP.
These teach risk/reward — the agent needs both to know when a tactic
works and when it doesn't.
Different mechanism: failed because evidence was too strong vs failed
because village was already coordinated → different.
Partial outcomes: "worked initially then failed" is distinct from both
pure success and pure failure.

---

Decide ONE of the following outcomes:

(D) DISCARD — Situation, approach, and outcome are all functionally the
    same per the comparison criteria above. The new entry teaches the same
    lesson as the existing entry, even if it uses different words or adds
    more detail. Output the candidate number it duplicates.

(M) MERGE — Situation and outcome are functionally the same, but the
    approach contains a concrete tactic variant — from either side of the
    interaction — that the existing entry does not already cover. This
    includes different enemy tactics (excuses, deflections) recognized by
    the same detection pattern, or different agent tactics (accusations,
    pressure methods) applied in the same situation.
    Output the candidate number to merge with and the final merged
    observation fields (situation, approach, outcome). The merged approach
    field MUST list ALL distinct tactics from both entries.

(K) KEEP — Situation or outcome is functionally different. The new entry
    requires the agent to look for something different, not just respond
    to something different. Store exactly as extracted with no rewrites.

EXAMPLES:
- D: Healer saves same target 3 times vs 2 times. Same lesson ("persist
  protecting confirmed targets"), different degree of persistence. → DISCARD.
- D: Wolf uses "too obvious" defense in mid-game vs endgame, both fail
  against evidence. Same tactic, different phase. → DISCARD.
- M: Wolf deflects by questioning healer saves (new) vs accusing villagers
  of coordination (existing). Same situation (endgame wolf deflection),
  same outcome (village sees through it). Different tactic variant. → MERGE.
- M: Investigator checks one active player Night 1 (existing) vs checks
  active players on Night 1 AND Night 2 (new). One-off → persistent
  crosses a qualitative threshold. → MERGE tactic variant.
- K: Catching wolf via late bussing vs partner protection. Same village
  response (press with voting evidence), but different detection signals
  requiring different analytical approaches. → KEEP.
- K: Healer protects vocal player Night 1 and save succeeds vs Healer
  protects vocal player Night 1 but accidentally protects a wolf. Same
  approach, opposite outcome — both teach risk/reward. → KEEP.

CALIBRATION:
MERGE requires a clearly distinct tactic variant — a different category of
action, not a different description of the same action. If you are unsure
whether the approach difference is a genuine tactic variant or just
different wording, choose DISCARD.

DECISION RULES:
- For MERGE, the rewritten observation must keep each field (situation,
  approach, outcome) as separate coherent text. Use only details present
  in the entries being compared. Do not infer or invent context not
  explicitly stated in the input entries.
- When an output field asks for a candidate number, use only the bracketed
  candidate number shown in SIMILAR EXISTING OBSERVATIONS. Do not output
  UUID keys.
"""


BATCH_STRATEGY_CLUSTER_DEDUP_PROMPT = """
You are cleaning a strategy-point memory database for an AI Werewolf agent.
The entries below are a candidate similarity cluster from one role and
action-phase namespace.

Each entry has:
- key: stable store key
- situation: the situation text used for semantic retrieval
- action: the recommended action
- observation_count: how often this memory has been observed

{situation_standards}

{epistemic_status_rule}

All situation fields you write or rewrite must conform to the standards and
epistemic status rule above.

Resolve this cluster into groups using one or more operations. Every operation
must use one of these action values: DISCARD, KEEP.

DISCARD — Two or more entries express the same hypothesis. They describe the
same situation and recommend the same action direction — an agent reading any
one of them would do the same thing. Choose one survivor_key (the best-worded
entry). The apply step will preserve that key, sum observation_counts from all
source_keys, and delete absorbed keys.

If none of the entries is well-written on its own but elements across multiple
entries could be combined into a stronger version, provide merged_situation and
merged_action for the survivor_key. Use only details present in the source
entries. Do not add dimensional fields (information landscape, consensus
texture, agent exposure, game phase) that no source entry contains; only
reorganize or clarify what is already stated.

KEEP — Entries are genuinely distinct and need no changes. Use when entries in
the cluster represent different hypotheses — different targets, different
timing, different risk tradeoffs, or different situational scope.

DECISION TEST:
For each pair of entries in the cluster, ask: would an agent in the described
situation take a different action after reading one entry vs the other?

- If NO → same hypothesis → group them under one DISCARD operation.
- If YES → different hypotheses → separate KEEP operations.

Apply this concretely:
- Different WORDS, SAME ACTION: "target the vocal player" vs "target the
  organizer" vs "target the player taking charge" → same hypothesis → DISCARD.
- Different REASONING, SAME ACTION: "kill the leader to prevent coordination"
  vs "kill the leader because they might be the Investigator" → same hypothesis
  → DISCARD.
- Different TARGET: "target the leader" vs "target a quiet moderate" → different
  hypotheses → KEEP both.
- Different RISK TRADEOFF: "accept healer risk for disruption" vs "avoid healer
  risk for guaranteed kill" → different hypotheses → KEEP both.
- Different SCOPE: "target the most vocal player" vs "target the most vocal
  player, but only if no healer save was announced" — the second adds a
  situational condition that changes when the action applies → different
  hypotheses → KEEP both.

A cluster of 9 similar entries might resolve to 1 DISCARD group (all same
hypothesis) or 2 DISCARD groups (two distinct hypotheses, each with redundant
copies) or a mix of DISCARD and KEEP operations.

CALIBRATION NOTE:
When in doubt, DISCARD. Over-discarding is recoverable — a genuinely novel
tactic will be re-extracted from a future game. Under-discarding leaves
retrieval pollution that triggered this cleanup in the first place.

Rules:
- Use only keys shown in the cluster. Do not invent new keys.
- Every key in the cluster must appear in exactly one operation.
- Prefer the fewest surviving entries that preserve genuinely distinct
  hypotheses.

Role: {role}
Action phase: {action_phase}

Cluster entries:
{entries}
"""


BATCH_OBSERVATION_CLUSTER_DEDUP_PROMPT = """
You are cleaning an episodic observation memory database for an AI Werewolf
agent. The entries below are a candidate similarity cluster from one role
and action-phase namespace.

Observations have three structured fields:
- situation: The game conditions (used for semantic search matching). Should
  use agent roles, never player IDs, and be specific enough for retrieval.
- approach: What the agent did in that situation. May list multiple tactics
  with per-tactic counts in the format "tactic description (Nx)".
- outcome: What resulted — how others responded and the downstream
  consequences.

{situation_standards}

When you rewrite observations, keep each field (situation, approach, outcome)
as separate coherent text. Use the situation standards above to keep the
situation field specific enough for retrieval.

Resolve this cluster using one or more operations. Every operation must use
one of these action values: DISCARD, MERGE, KEEP.

Rules:
- DISCARD: Entries are exact duplicates — same situation, approach, AND
  outcome. Choose one survivor_key; the apply step will preserve that key,
  sum counts, and delete absorbed keys.

- MERGE: Entries share the same functional situation and the same functional
  outcome, but record different specific tactics in the approach field.
  Multiple tactics that fail (or succeed) for the same structural reason
  are one lesson, not separate observations. Choose one survivor_key and
  provide merged_situation, merged_approach, and merged_outcome.

  Approach field rules for MERGE:
  - List each distinct tactic with its count: "Claiming a 'frame job' (4x),
    pleading genuine mistake (3x), accusing groupthink (5x)".
  - Preserve existing counts from entries being merged. A tactic with no
    existing count annotation is (1x).
  - If the merged list exceeds 7 distinct tactics, group similar variants
    under a category label: "Various weak excuses — frame job, genuine
    mistake, and 3 similar variants (12x total)". Keep the 3-4 most
    distinct tactics listed individually.
  - The merged outcome summarizes the shared lesson.
  - observation_count will be summed automatically.

- KEEP: Entries are genuinely distinct — different situations OR different
  outcomes. No change needed for the listed source_keys.

Decision test: Would the agent make a different strategic decision based on
reading entry A versus entry B? If both entries teach "this category of
tactic fails in this situation," they are one lesson — MERGE them. If one
entry shows failure and another shows success, they are different lessons —
KEEP both.

- Use only keys shown in the cluster. Do not invent new keys.
- A single cluster may require multiple operations (e.g., MERGE a subgroup
  of 5, KEEP 2 others that have different outcomes).
- Prefer merging near-duplicates over preserving repeated memories.

Role: {role}
Action phase: {action_phase}

Cluster entries:
{entries}
"""
