# Observation Dedup Prompt — Draft v2

Replaces lines 121-162 of `Agents/prompts/dedup.py` (the decision section of
`OBSERVATION_DEDUP_PROMPT`). The header and input formatting above line 121
are unchanged.

## Changes from baseline

1. **DISCARD loosened** from "exact duplicate" to "same strategic lesson"
2. **MERGE tightened** to specifically mean different variants of the agent's
   own tactic (not different opposing tactics or detection signals)
3. **KEEP expanded** to explicitly include different detection signals and
   opposing tactics, even when the agent's response is similar
4. **Two-stage decision test** added: lesson identity first (D vs not-D),
   then signal novelty (M vs K)
5. **Calibration cascade** added: doubt → D over M, doubt → M over K
6. **obs_count guidance** added: high-count generalized entries raise the
   bar for merge

## Draft prompt text

```
Decide ONE of the following outcomes:

(D) DISCARD — The new observation teaches the same strategic lesson as an
    existing entry. The situation type, the tactic or signal being described,
    and the outcome all point to the same actionable takeaway — even if
    specific details differ (player count, game phase, number of
    repetitions, specific wording). Output the candidate number it
    duplicates.

(M) MERGE — The new observation shares the same situation and the same
    functional outcome as an existing entry, but records a genuinely
    different variant of the agent's own tactic in the approach field.
    Multiple tactics that succeed or fail for the same structural reason
    are one lesson with multiple data points — MERGE accumulates them.
    Output the candidate number to merge with and the final merged
    observation fields (situation, approach, outcome). The merged approach
    field MUST list ALL distinct tactics from both entries.

(K) KEEP — The new observation teaches a genuinely novel lesson. Either
    the situation dynamics are meaningfully different, the outcome differs,
    OR the observation teaches the agent to recognize a different signal
    or counter a different opposing tactic — even if the agent's own
    response looks similar. The new entry is stored exactly as extracted.

DECISION TEST — apply in two stages, in order:

Stage 1 — Lesson Identity (DISCARD vs everything else):
Summarize each entry's core lesson in one sentence starting with "An agent
reading this learns..." If the sentences are functionally identical, the
answer is DISCARD — regardless of differences in game phase, player count,
specific numbers, or narrative detail. Stop here.

  - "Learns to persist protecting the same target after a successful save"
    — same lesson whether the healer saved 2 times or 3 times. → DISCARD.
  - "Learns that the 'too obvious' meta-defense fails against strong
    evidence" — same lesson whether it happens mid-game or endgame. The
    game phase changed but the tactic, the defense, and the failure
    are identical. → DISCARD.
  - If the existing entry already generalizes the pattern well (especially
    with high observation_count), adding game-state flavor like a specific
    night number or "revenge" motive does not create a new lesson.
    → DISCARD.

Stage 2 — Signal Novelty (MERGE vs KEEP):
If the lessons are NOT identical, determine WHY they differ. Consider both
sides of the interaction — what the agent does AND what signal or opposing
tactic the agent is observing or countering.

  KEEP when the observation teaches the agent to detect a different signal
  or counter a different opposing tactic, even if the agent's response is
  similar:
  - Catching a wolf via "late bussing" (joining the correct vote
    suspiciously late) vs "partner protection" (refusing to vote against
    partner). Both lead to "press with voting evidence → wolf eliminated,"
    but these are different detection heuristics an agent must learn
    independently. → KEEP.
  - Countering a wolf's "you two are too coordinated" accusation in a 2v1
    vs countering a wolf's "the dead Investigator lied" smear. Both lead
    to "ignore deflection, trust evidence," but the wolf tactic being
    recognized is different. → KEEP.
  - Success vs failure of the same tactic in different conditions teaches
    different risk/reward lessons. → KEEP.

  MERGE when the situation and outcome are the same but the agent's own
  approach used a different tactic variant:
  - Wolf tried "frame job" defense in one game and "honest mistake" defense
    in another; both failed because the evidence was too strong. Same
    lesson ("weak excuses fail against hard evidence"), different tactic
    variants. → MERGE.

CALIBRATION:
- When in doubt between DISCARD and MERGE, choose DISCARD. An existing
  entry with high observation_count already validates the pattern across
  games — bump the count rather than merging in marginal detail.
- When in doubt between MERGE and KEEP, choose MERGE.
- Over-accumulation is the primary failure mode. A genuinely novel
  observation will be re-extracted from a future game.

DECISION RULES:
- For DISCARD, the existing entry's observation_count will be incremented
  automatically.
- For MERGE, the rewritten observation must keep each field (situation,
  approach, outcome) as separate coherent text. Use only details present
  in the entries being compared. Do not infer or invent context not
  explicitly stated in the input entries.
- When an output field asks for a candidate number, use only the bracketed
  candidate number shown in SIMILAR EXISTING OBSERVATIONS. Do not output
  UUID keys.
```

## Tricky cases this draft addresses

| Case | Bias | How the draft handles it |
|---|---|---|
| 2 | Phase/degree over-differentiation | Stage 1 lesson identity: "persist protecting same target" is same lesson regardless of save count |
| 16 | Over-merging same response, different tactic | Stage 2 KEEP example: different opposing tactic → KEEP even if agent response is similar |
| 21 | Over-merging same response, different signal | Stage 2 KEEP example: late bussing vs partner protection are different detection heuristics |
| 22 | Merge bias over discard | Stage 1: existing entry already generalizes + high obs_count guidance |
| 24 | Merge bias over discard | Stage 1 lesson identity: identical tactic/outcome → DISCARD despite surface details |
| 40 | Phase over-differentiation | Stage 1 example: "too obvious" defense same lesson across phases |
