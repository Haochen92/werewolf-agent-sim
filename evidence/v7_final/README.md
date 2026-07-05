# `v7_final/` — the v7 campaign record

This folder is the **record of the v7 compounding campaign**: the pre-registered cheap-screen gates, the
compounding runs, the tagger de-leak work, and the design docs behind the generational loop
(`evaluation/src/loop/`). It is the narrative + data half; the standing loop *code* lives in
`evaluation/src/loop/` and the standing validation *rulers* it graduated live in
`evaluation/src/instrument_validation/`.

**HOME RULE.** New v7 verification code is born in `evaluation/src/` — `instrument_validation/` for
standing *ruler* checks (re-run every epoch), `studies/` for one-shot *screens*. **This folder holds
outputs + narrative only** — the probe scripts below are frozen dated records of screens that already
settled their question, not maintained code (their `poetry run` lines are kept honest to their new
location, but they are not on any test path).

**Every probe script here carries a `FROZEN RECORD` stamp above its docstring — anything without one
doesn't belong in this folder.**

## Read order

1. **[`review_map.md`](review_map.md)** — the map: every v7 design decision → what to read → the
   generating harness. Start here.
2. **[`report.md`](report.md)** — the verdict-first write-up (what v7 concluded).
3. **[`experiment_log.md`](experiment_log.md)** — the chronological journey (why each choice, in order).
4. **[`plan.md`](plan.md)** — the pre-registered plan (claim ladder, gates, spend gating).

Other root docs: [`consolidation_design.md`](consolidation_design.md),
[`discussion_credit_design.md`](discussion_credit_design.md),
[`production_design.md`](production_design.md),
[`extraction_coverage_ab_spec.md`](extraction_coverage_ab_spec.md),
[`EVALUATOR_BRIEF.md`](EVALUATOR_BRIEF.md), [`evaluator_review.md`](evaluator_review.md), and the data
artifact `credit_backfill_ledger.json` (per-game SP → lift/shrunk_lift/follow; read by
`synthesis_checks/sp_synthesis_quality_check.py` and the loop's `credit_backfill.py`).

## Folder map

| Folder | What's in it |
|--------|--------------|
| **`runs/`** | The run-output dirs: the paired compounding runs, the smokes, and the synth A/Bs (data + the salvage/tagger scripts that live inside `runs/v2_full/`). |
| **`gates/`** | The pre-registered $0 GO/NO-GO gate screens (G3b, G3c). |
| **`discussion_credit/`** | The screens sizing/validating the discussion-credit design (free floor + paid tagger). |
| **`extraction_screens/`** | The zero-spend extraction model/shape/recall screens. |
| **`synthesis_checks/`** | Read-checks on synthesized SP content + retrieval dimensions. |

## Probe inventory (one line each — question it answered → where the verdict lives)

**`gates/`** — the pre-registered $0 gates from `plan.md` §5 (deterministic GO/NO-GO screens run on
already-generated games before any paid compounding run):

- **`g3b_target_advocacy.py`** — G3b: does structured advocacy (accusation stance) steer the vote, and
  toward *correct* removals (the offense channel)? → the deterministic offense signal exists; `plan.md`
  §6.2/§10a.
- **`g3c_retrieval_applicability.py`** — G3c: is the retrieval-waste (not_relevant 30–69%) fixable by a
  score/rank *knob*, or a hard semantic problem? → similarity ≠ applicability (score doesn't separate) →
  needs structured gating; `plan.md` §10b.
- **`g3c_gating_efficacy.py`** — the G3c follow-on: does a *criticality* gate dimension separate
  applicable from not_relevant? → fed the dimension-gating screen, which validated **NEGATIVE** → gating
  ships default-OFF (`instrument_validation/dimensions/dimension_gating_screen.py`).

**`discussion_credit/`** — sizing + validating the discussion-credit tiers (`discussion_credit_design.md`):

- **`discussion_credit_deterministic.py`** — the FREE deterministic slice (advocacy correctness):
  coverage / separation / held-out reproduction → how much of discussion credit is achievable with no
  LLM (the "floor" mode; `credit.py:_discussion_ledger`).
- **`discussion_coverage_check.py`** — two free measurements: M1 day-vote-endpoint credit coverage +
  defense-heat reach; M2 how often a hidden read is acted on at night without day-heat → whether the
  night-exposure axis is worth wiring.
- **`tagger_accuracy.py`** — are the omniscient tagger's per-field tags (role_reveal / framing /
  credibility) CORRECT vs ground truth? → validated; **graduated 2026-07-02** to
  `instrument_validation/tagger/tagger_validation.py` (mode=accuracy); this is the frozen original.

**`extraction_screens/`** — zero-spend extraction screens (read the already-extracted stores):

- **`extraction_model_ab_compare.py`** — pro / flash-3.5 / flash-lite extraction on the same 3-game
  slice (obs volume, intra-cell distinctness, de-halo corr) → **flash-lite ≈ pro** (the cost pin).
- **`extraction_quota_screen.py`** — is the "6–12 obs" quota binding (padding pressure), and do bigger
  cells carry more near-restatement? → two free extraction-*shape* screens.
- **`recall_capture_metric.py`** — does suggestive-anchoring lift flash-lite's capture of deterministic
  pivotal turns toward pro's? → the recall-arm capture metric (companion to `audits/recall_flags.py`).

**`synthesis_checks/`** — read-checks on the synthesizer's output:

- **`sp_synthesis_quality_check.py`** — does cluster-synthesis concentrate SP quality (carried-vs-dropped
  lift), or is it quality-blind? → outcome-blind by construction → improvement must come from the
  credit-prune, not synthesis.
- **`inspect_synth_dims.py`** — does a cross-regime conditioned directive get tagged to a *single* regime
  (retrieval misalignment) by the synthesizer? → a manual-read dimension inspection.

## Gate naming

`G2` / `G3a` / `G3b` / `G3c` are the **pre-registered $0 gates from `plan.md` §5**. (G2 = decision
separability above luck; G3a-c = verdict validity / target-advocacy / retrieval-applicability + gating.)
G2, G3a, the leverage anchor, and the tagger/credit rulers have since **graduated** to
`evaluation/src/instrument_validation/` as standing rulers (see `review_map.md`); the `gates/` scripts
here remain as the dated screens.

## Trigger-dated (re-open on a specific decision, not standing yet)

These scripts settled their question once and are parked, but re-open as **standing** work if a specific
decision lands:

- **`gates/g3b_target_advocacy.py` · `discussion_credit/discussion_credit_deterministic.py` ·
  `discussion_credit/discussion_coverage_check.py`** — re-open **if the §0.5 discussion-credit decision
  lands on a deterministic-channel path** (i.e. if discussion credit moves off the LLM tagger onto a
  deterministic channel signal).
- **`extraction_screens/recall_capture_metric.py` · `extraction_screens/extraction_model_ab_compare.py`**
  — re-open on an **extraction model / prompt revisit**.
