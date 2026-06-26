"""Batch dedup prompts — v0 baseline (pre-tuning).

Frozen snapshot of the batch prompts before porting per-extraction
decision criteria. These prompts were unchanged throughout the entire
per-extraction tuning cycle (v1-v11b).
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
