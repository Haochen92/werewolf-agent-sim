# v6 full-DAG store (step 4B) — build record + quality audit

**Status:** BUILT 2026-06-15. `memory_stores/v6_0` re-extracted to the full v6 cell DAG (all roles ×
all phases) via `evaluation/src/experiments/reextract_cells.py`, RAW (no dedup). Villager·day kept
from the cheap-first slice; healer/investigator/vigilante/wolf/serial_killer appended.

## Store
- **17 namespaces, 993 observations**, all 11 cells covered. 0 entries missing criticality numbers or
  net_verdict.
- Verdict spread: 458 negative / 383 positive / 116 mixed / 36 unclear — balanced, slightly
  negative-leaning (net-horizon honesty; not outcome-biased toward wins).
- Per-namespace counts span 31–80; criticality numbers span the regimes; cell shapes correct (night
  cells carry no consensus/heat; wolf·day carries ally_revealed; vigilante carries bullets_left).

## Held-out discipline (the leak lesson, applied)
Extracted ONLY from the 20 `extraction_v5_0` source games, so any game NOT in that set is a clean
held-out test game. The screen enforces same-game exclusion (always on) + `--held-out-only`. Recorded
in the store manifest.

## Quality audit (track-1 rider — a human read entries)
Spot-checks are faithful: wolf·day captures the net-horizon two-edged effect ("eliminated the
threat without drawing heat… while this ultimately led to your loss"); vigilante·night nails hold-fire
("held fire… a random shot would have killed a villager"); investigator·night frames info-gain with
net-traced consequences. Dimensions stay descriptive (Rule 2).

**⚠ DEFECT — naming-rule violations (player IDs), night-concentrated:**
| | violations / total |
|---|---|
| villager (day-only) | 0 / 119 (0%) |
| day cells (all roles) | 44 / 658 (6.7%) |
| **night cells** | **74 / 335 (22.1%)** |
| **store total** | **118 / 993 (11.9%)** |

Night target decisions tempt the model to name the specific target as `player_N` instead of a
role/behavioral descriptor. Player IDs are game-local-meaningless, so they pollute the retrieval
embedding (a dead token) — no cross-game leak, but degraded recall.

**Not a missing-rule bug (verified):** the built prompt DOES contain the `EPISTEMIC_STATUS_RULE`
(len 2479, including "Never use player IDs (player_1, player_2). Use role-based or behavioral
descriptors instead.") AND a dedicated `NAMING RULE` line — the `{epistemic_status_rule}` placeholder
substitutes correctly. Villager (day-only) obeyed it at 0%. The model simply disobeys in night-target
contexts where the lesson is about WHICH player was targeted. So the fix is emphasis, not plumbing:
add an explicit night-target clause ("even when the lesson is about whom you targeted, name them by
role/behavioral descriptor at the epistemic-appropriate certainty, never player_N").

**Disposition: ACCEPT + FLAG, do not re-extract now.** The naming fix is an extraction-PROMPT change,
which `feedback-memory-pipeline-prompt-freeze` says belongs in the Phase B labelling/prompt-tuning
cycle (it conditions gold labels), not a casual re-spend — and this store is RAW pending that pass
anyway. Fix = strengthen the NAMING RULE for night-target wording (name the target by role/behavior at
the epistemic-status-appropriate certainty; a naive post-hoc `player_N`→role substitution is unsafe,
it would break the epistemic-status rule). Re-extract night cells then.

## ⭐ Re-extraction with per-cell prompt assembler + consensus_direction leak fix (2026-06-15)

After the first full store, two issues were fixed and the store was rebuilt fresh (old kept as
`memory_stores/v6_0_preleakfix`):

- **Per-cell prompt assembler** (`Agents/prompts/dimension_guidance.py`): the extraction + live-query
  prompt's dimension menu is now GENERATED from the cell schema's `Field(description=)` (single source)
  + a per-cell DRIVER/HORIZON registry (spec §2/§6). Prompt ↔ schema ↔ embedding ↔ model-output ↔
  dedup all derive from `(mixin descriptions, cell selector)` — drift-guard test enforces
  menu==schema per cell. (Answers "is the prompt structured per the cell's dimension combination?":
  the field SET was always per-cell via the schema; now the prompt TEXT is too, with per-cell driver/
  horizon.)
- **consensus_direction hindsight leak**: the enum was being set against the hindsight-correct read
  (12.9% of records had a directional enum while the prose said "fractured/no-consensus"). Fixed at
  two layers: (1) Field descriptions pin consensus_direction + divergence_sign to the role's EXPRESSED
  read at the moment, never the outcome → cut contradictions to **7.1%**; (2) `coerce_consensus_direction`
  validates enum-vs-prose at store-write (no-consensus markers → no_clear_direction) → **0% detectable**.
  Subtler hindsight cases (directional enum vs the correct read WITHOUT explicit fractured prose) remain
  undetectable by keyword and would need an outcome-blind LLM relabel — deferred.

New store: **919 obs / 17 namespaces**, 0 missing criticality/verdict, verdicts 423neg/355pos/103mixed/
38unclear, consensus_direction 285 aligns / 223 no_clear / 116 opposes.

**Still NOT fixed (deferred, separate):** the night-target player-ID naming defect (night ~22%) — no
night-naming clause was added this round. And the subtler consensus_direction hindsight cases above.
Both belong to the Phase B prompt-tuning/labelling cycle.

## Pointers
- Runner: `evaluation/src/experiments/reextract_cells.py`; prompt `V6_CELL_EXTRACTION_PROMPT`.
- Schema: `Agents/schemas/memory.py` (11 cells). Screen: `criticality_screen.py`.
- Store manifest: `memory_stores/v6_0/manifest.json`.
