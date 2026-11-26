# Claims review of four separate revisions

Reviewed public copy in the four `*.revised.md` files against the originals, original briefs, source mappings, and relevant reports/logs. Final HTML comments were treated as source/supporting notes, not public claims. No draft or original was edited.

The substantive qualifications requested for this pass are mostly preserved. The facts page now treats nonrecurrence as inconclusive; the previous-days page permits full transcripts alongside field extraction; the turn-request page distinguishes written assessments from internal reasoning; the deduction page explicitly says the visitor is not proved to be the blocker. Bundled interventions and the principal replay denominators remain visible.

## Findings

### 1. The visit-report metric lost its definition during tightening

**File:** `writeup/context_engineering/deduction_engine/deduction_engine.revised.md:168`.

“Report errors” and “reply errors” now sound like general accuracy measures. The counts actually concern public-message samples that state or rely on false visit/watch/follow mechanics. The original table defined this narrower measure. This matters to what 6 → 2 and 17 → 17 establish; the source separately scores whether the own result was reported clearly, and that measure does not improve (22/40 → 20/40).

**Evidence:** `evidence/gameplay/data/visit_wording_ab/README.md`, Judging and Arm C; original deduction brief, Open question 5.

**Exact repair:** replace the results cell with:

> Samples stating or relying on false visit rules: reports 6 → 2 of 40; replies 17 → 17 of 55

The scope cell already supplies turns and samples per turn, so no additional methodological inventory is needed.

### 2. “Unrelated input fix” understates a directly relevant bundled repair

**File:** `writeup/context_engineering/deduction_engine/deduction_engine.revised.md:160`.

The bundled fix restored a follow sighting that had been dropped because it named the follower itself. That is part of the watch/follow interaction being tested, not an unrelated input issue. The draft correctly discloses a bundle, but the adjective incorrectly discounts the other change's possible contribution. This wording is inherited from the original.

**Evidence:** `evidence/gameplay/data/visit_wording_ab/README.md`, Arm C: the `visits_of` bug meant player_4's follow never reached any deduction.

**Exact repair:** replace “It also included an unrelated input fix.” with:

> It also restored a follow sighting that a bug had kept out of the deductions.

## Other pages

No material unsupported claim introduced by tightening was found in `facts.revised.md`, `previous_days.revised.md`, or `turn_request.revised.md` in this review. The scope and units of their retained central comparisons fit the mapped evidence. This is a consequential-claims review, not an exhaustive implementation audit or a fresh validation of the original experiments.

The opening-paragraph issue identified during reading was resolved by the parent’s concurrent edit: the current deduction opening describes the written gap without claiming access to internal reasoning or ruling out ambiguity. It is not an outstanding finding.
