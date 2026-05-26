STRATEGY_DEDUP_PROMPT = """
You are maintaining a strategy database for an AI Werewolf agent. A new
strategy point has just been extracted from a game. Your job is to compare
it against the most similar existing entries and decide how to integrate it.

{situation_standards}

{epistemic_status_rule}

All situation fields you write must conform to the standards and epistemic
status rule above.
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

    Output: the candidate number it duplicates.

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
  automatically. The existing entry's text is preserved as-is.
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
"D" or "K"; do not use DISCARD or KEEP.

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

Before deciding D/K, evaluate each field independently:

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

DISCARD REQUIRES ALL THREE FIELDS TO MATCH:
Similar situations alone do not justify DISCARD. You must also confirm that
the approach uses the same tactic category AND the outcome follows the same
success/failure pattern. If the approach uses a different tactic (e.g.,
proactive framing vs defensive deflection, voting record analysis vs
behavioral reading) or the outcome differs (success vs failure), KEEP —
even if the situations look nearly identical.

---

Decide ONE of the following outcomes:

(D) DISCARD — Situation, approach, and outcome are all functionally the
    same per the comparison criteria above. The new entry teaches the same
    lesson as the existing entry, even if it uses different words or adds
    more detail. Output the candidate number it duplicates.

(K) KEEP — The new entry differs in situation, approach, or outcome per
    the comparison criteria above. This includes cases where:
    - The situation is functionally different (different retrieval match)
    - The approach uses a different tactic category or detection method
    - The outcome differs in success/failure or structural mechanism
    Store exactly as extracted with no rewrites.

EXAMPLES:
- D: Healer saves same target 3 times vs 2 times. Same lesson ("persist
  protecting confirmed targets"), different degree of persistence. → DISCARD.
- D: Wolf uses "too obvious" defense in mid-game vs endgame, both fail
  against evidence. Same tactic, different phase. → DISCARD.
- K: Wolf deflects by questioning healer saves (new) vs accusing villagers
  of coordination (existing). Same situation but different tactic variant
  — the agent learns a different defensive pattern to watch for. → KEEP.
- K: Catching wolf via late bussing vs partner protection. Same village
  response (press with voting evidence), but different detection signals
  requiring different analytical approaches. → KEEP.
- K: Healer protects vocal player Night 1 and save succeeds vs Healer
  protects vocal player Night 1 but accidentally protects a wolf. Same
  approach, opposite outcome — both teach risk/reward. → KEEP.

DECISION RULES:
- For DISCARD, the existing entry's observation_count will be incremented
  automatically. The existing entry's text is preserved as-is.
- When an output field asks for a candidate number, use only the bracketed
  candidate number shown in SIMILAR EXISTING OBSERVATIONS. Do not output
  UUID keys.
"""


BATCH_STRATEGY_CLUSTER_DEDUP_PROMPT = """
You are cleaning a strategy-point memory database for an AI Werewolf agent.
The entries below are a candidate similarity cluster from one role and
action-phase namespace.

Each entry is numbered [1], [2], etc. and has:
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
entry, by its number). The apply step will preserve that entry, sum
observation_counts from all source_keys, and delete absorbed entries.

If the survivor_key entry is already well-written and covers the hypothesis
adequately, do not provide merged fields — just output the survivor_key. Only
provide merged_situation and merged_action when no single entry captures the
full hypothesis on its own and elements across multiple entries could be
combined into a stronger version. Use only details present in the source
entries. Do not add dimensional fields (information landscape, consensus
texture, agent exposure, game phase) that no source entry contains; only
reorganize or clarify what is already stated.

KEEP — Entries are genuinely distinct and need no changes. Use when entries in
the cluster represent different hypotheses — different targets, different
timing, different risk tradeoffs, or different situational scope.

SITUATION COMPARISON:
Two situations are functionally the same when a semantic search query
matching one would also retrieve the other. If not, they are different
situations — they belong in separate KEEP operations even if the action
advice is similar.

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
- Different CONFIDENCE POSTURE: "treat accusation as ground truth and act
  immediately" vs "probe to evaluate alignment before committing" — same
  direction but different certainty level → different hypotheses → KEEP both.
- Opposite ACTION for same situation: "defend the aggressive accuser" vs
  "challenge the accuser's motives" — conflicting strategies are by
  definition different hypotheses → KEEP both.

A cluster of 9 similar entries might resolve to 1 DISCARD group (all same
hypothesis) or 2 DISCARD groups (two distinct hypotheses, each with redundant
copies) or a mix of DISCARD and KEEP operations.

BEFORE GROUPING ENTRIES UNDER DISCARD — verify both conditions hold for
every pair in the group:
1. The situations are functionally the same per the situation comparison.
2. The recommended actions point in the same direction — same target type,
   same timing, same risk posture.
If entries recommend different or conflicting actions for the same
situation, they are competing hypotheses — separate KEEP operations.

CALIBRATION NOTE:
When in doubt, DISCARD. Over-discarding is recoverable — a genuinely novel
tactic will be re-extracted from a future game. Under-discarding leaves
retrieval pollution that triggered this cleanup in the first place.

Rules:
- Use only entry numbers shown in the cluster (e.g. "1", "2"). Do not use
  UUIDs or invent new identifiers.
- Every entry number in the cluster must appear in exactly one operation's
  source_keys.
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
and action-phase namespace. Each entry is numbered [1], [2], etc.

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
  outcome. Choose one survivor_key (by entry number); the apply step will
  preserve that entry, sum counts, and delete absorbed entries.

- MERGE: Entries share the same functional situation and the same functional
  outcome, but record different specific tactics in the approach field.
  Multiple tactics that fail (or succeed) for the same structural reason
  are one lesson, not separate observations. Choose one survivor_key (by
  entry number) and provide merged_situation, merged_approach, and
  merged_outcome.

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

COMPARISON CRITERIA:

Before choosing an operation, evaluate each field independently:

SITUATION — "same" vs "different":
Would a semantic search query matching situation A also retrieve
situation B? If not, they are different situations — KEEP, even if the
underlying lesson is similar.

Check these dimensions:
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
NOT different: wording variations, different reasoning for the same action.
Different: different tactic category (accusation vs deflection vs role
claim), different detection method (voting record analysis vs behavioral
pattern recognition), different dimension targeted (timing-based vs
logic-based argument).

OUTCOME — "same" vs "different":
Two outcomes are functionally the same when they succeed or fail for the
same structural reason.
Same approach, opposite outcome (success vs failure) → always KEEP.
Different mechanism: failed because evidence was too strong vs failed
because village was already coordinated → different.
Partial outcomes: "worked initially then failed" is distinct from both
pure success and pure failure.

BEFORE MERGING — verify ALL of these hold for every entry in the group:
1. The situations pass the retrieval test: a single merged situation text
   would be retrieved by the same vector search queries that match EACH
   original entry. If original entries have different game phases, different
   info landscapes, or different agent exposure that would match different
   queries, they belong in separate KEEP operations — even if the lesson
   is similar.
2. The outcomes follow the same success/failure pattern and fail/succeed
   for the same structural reason.
3. The approaches differ only in specific tactic variant, not in tactic
   category (accusation vs deflection vs role claim are different categories).
A MERGE group larger than 3-4 entries is a red flag — it usually means
the model is grouping by "lesson theme" rather than by retrieval context.
Re-check each pair in the group against condition 1.

DISCARD REQUIRES ALL THREE FIELDS TO MATCH:
Situation, approach, AND outcome must all be functionally the same. If the
approach uses a different tactic category or detection method, the entries
are not duplicates — consider MERGE (if outcome matches) or KEEP.

DECISION TEST:
For each pair of entries, ask: would the agent make a different strategic
decision based on reading entry A versus entry B?

- Both entries teach "this category of tactic fails in this situation"
  → one lesson → MERGE them (consolidate tactic variants with counts).
- One entry shows failure, another shows success → different lessons
  → KEEP both.
- Same situation, same outcome, same tactic → redundant → DISCARD.
- Same situation but different tactic categories (accusation vs deflection),
  even if both fail → different lessons about what doesn't work → KEEP both.
- Different situations (different retrieval match) with same approach →
  different lessons (the tactic works/fails in different contexts) → KEEP.

EXAMPLES:
- DISCARD: Wolf uses "too obvious" defense in mid-game (entry A) vs
  near-identical "too obvious" defense phrasing in endgame (entry B),
  both fail against evidence. Same tactic, same outcome. → DISCARD.
- MERGE: Wolf deflects by questioning healer saves (3x) and entry B records
  wolf deflecting by accusing groupthink (2x) — same situation, same
  failure outcome, different specific tactics. → MERGE with approach listing
  both tactics and their counts.
- KEEP: Healer protects vocal player Night 1 and save succeeds vs Healer
  protects vocal player Night 1 but accidentally protects a wolf. Same
  approach, opposite outcome — both teach risk/reward. → KEEP both.
- KEEP: Catching wolf via late bussing vs partner protection. Same village
  response, but different detection signals requiring different analytical
  approaches. → KEEP both.

Rules:
- Use only entry numbers shown in the cluster (e.g. "1", "2"). Do not use
  UUIDs or invent new identifiers.
- Every entry number in the cluster must appear in exactly one operation's
  source_keys.
- A single cluster may require multiple operations (e.g., MERGE a subgroup
  of 3, KEEP 4 others that have different situations or outcomes).

Role: {role}
Action phase: {action_phase}

Cluster entries:
{entries}
"""
