# Observation Dedup Prompt — Draft v2 (Merged)

Replaces lines 121-162 of `Agents/prompts/dedup.py` (the decision section of
`OBSERVATION_DEDUP_PROMPT`). The header and input formatting above line 121
are unchanged.

## Design rationale

Merges two independent drafts. Takes Draft 2's structure (labeled rules,
shared D/M opening, "which side changed?" framing) and Draft 1's reasoning
scaffolds ("An agent reading this learns..." stem, one fully worked KEEP
example). Optimized for flash/flash-lite models: concise, scannable rules,
explicit branching, but with enough context that a model unfamiliar with
Werewolf dynamics can follow the examples.

## Draft prompt text

```
Decide ONE of the following outcomes:

(D) DISCARD — The core strategic lesson is identical. The new entry teaches
    the agent the same actionable takeaway as the existing entry, even if
    specific surface details differ (player count, game phase, number of
    repetitions, wording). The existing entry's observation_count will be
    incremented automatically. Output the candidate number it duplicates.

(M) MERGE — The core strategic lesson is identical, but the new entry
    records a genuinely different variant of the agent's own tactic that
    succeeded or failed for the same structural reason. Output the candidate
    number to merge with and the final merged observation fields (situation,
    approach, outcome). The merged approach field MUST list ALL distinct
    tactics from both entries.

(K) KEEP — The observation teaches a genuinely novel lesson: a different
    detection heuristic, a different opposing tactic to counter, or a
    meaningfully different situation or outcome. The new entry is stored
    exactly as extracted.

DECISION TEST — apply in two stages, in order:

STAGE 1 — Lesson Identity (DISCARD vs everything else):
Summarize each entry's core lesson in one sentence: "An agent reading this
learns..." If the sentences are functionally identical, DISCARD. Stop here.

Do not let surface differences prevent DISCARD:
- SAME LESSON, DIFFERENT DEGREE → DISCARD. "Persist protecting the same
  target" is the same lesson whether the healer saved 2 or 3 times.
- SAME LESSON, DIFFERENT PHASE → DISCARD. The "too obvious" meta-defense
  failing against strong evidence is the same lesson in mid-game or
  endgame, if the tactic, defense, and outcome are identical.
- GENERALIZED ENTRY ALREADY COVERS IT → DISCARD. If the existing entry
  (especially with high observation_count) already captures the principle,
  do not MERGE just to add flavor details like a night number or motive.
  Bump the count instead.

STAGE 2 — Signal Novelty (MERGE vs KEEP):
If the lessons differ, determine which side of the interaction is different:

→ OPPONENT SIGNAL OR TACTIC DIFFERS → KEEP.
  The agent must learn to recognize each trigger independently, even if its
  own response is similar both times. Example: catching a wolf via "late
  bussing" (joining the correct vote suspiciously late) vs "partner
  protection" (refusing to vote against partner). Both lead to "press with
  voting evidence → wolf eliminated," but these are different detection
  heuristics — an agent trained on one would not recognize the other. KEEP.

→ OUTCOME DIFFERS (success vs failure of same tactic) → KEEP.
  Same tactic in different conditions producing opposite results teaches
  different risk/reward lessons.

→ SAME TRIGGER, AGENT'S OWN TACTIC DIFFERS → MERGE.
  The situation and outcome are the same, but the agent tried a different
  method. Example: wolf claimed "frame job" in one game and "honest mistake"
  in another; both failed because evidence was too strong. Combine the
  tactic variants under one observation.

CALIBRATION:
- When in doubt between DISCARD and MERGE, choose DISCARD.
- When in doubt between MERGE and KEEP, choose MERGE.
- Over-accumulation is the primary failure mode — a genuinely novel
  observation will be re-extracted from a future game.

DECISION RULES:
- For MERGE, the rewritten observation must keep each field (situation,
  approach, outcome) as separate coherent text. Use only details present
  in the entries being compared. Do not infer or invent context not
  explicitly stated in the input entries.
- When an output field asks for a candidate number, use only the bracketed
  candidate number shown in SIMILAR EXISTING OBSERVATIONS. Do not output
  UUID keys.
```

## Tricky cases coverage

| Case | Bias | Mechanism that addresses it |
|---|---|---|
| 2 | Degree over-differentiation | Stage 1: SAME LESSON, DIFFERENT DEGREE rule |
| 16 | Over-merging same response, different tactic | Stage 2: OPPONENT SIGNAL OR TACTIC DIFFERS → KEEP |
| 21 | Over-merging same response, different signal | Stage 2: KEEP example (bussing vs protection) |
| 22 | Merge bias over discard | Stage 1: GENERALIZED ENTRY ALREADY COVERS IT rule |
| 24 | Merge bias over discard | Stage 1: lesson identity test catches identical lessons |
| 40 | Phase over-differentiation | Stage 1: SAME LESSON, DIFFERENT PHASE rule |
