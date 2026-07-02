# Sampled Human Review — the third evaluation modality

> **Where this sits.** The eval system judges each memory component on a three-rung **modality ladder**,
> cheapest-but-noisiest first: ① **LLM-as-judge** (→ [`../llm_judge/report.md`](../llm_judge/report.md)) →
> ② **sampled human + pro-LLM review** *(this folder)* → ③ **golden-set labels**
> (→ [`../labeling/report.md`](../labeling/report.md)). Rung ② is the one with **no system behind it** — and
> that gap is the headline of this report.
>
> **Status: ⛔ underbuilt — a real apparatus we *used* heavily but never *built*.** Slated to be hardened
> (the sampler); the plan is [`plan.md`](plan.md).

## What it is

Pull a handful of real decision cases, put each in front of a **human** *and* an **advanced model** (a
stronger LLM than the one being judged), and read them — "does this situation summary actually read like the
right retrieval query? did this extraction invent anything? is this merge faithful?" It is the modality that
answers the questions an automated judge can't: **information gain, subtle fabrication, and "does this read
right to a person."**

## Why it matters — it was the actual workhorse of v5→v7

Most of the *qualitative* design calls in the memory pipeline were made this way, not by a judge or a golden
set: extraction-selection phrasing, situation-summary wording, the dedup "tricky cases", the day-summary
saturation diagnosis. When you change a prompt or add a dimension you rarely have a golden set for the new
question, and the LLM-judge is itself uncalibrated (→ `../llm_judge/`), so the honest fallback is to **read
the cases**. That is rung ② doing the real work.

## The gap — why it's the weakest rung despite carrying the most weight

It was **used** as a methodology but never **systematised**, and that costs it on two axes:

1. **No principled sampler.** *Which* cases got reviewed was ad-hoc — whatever was on hand, or eyeballed
   outliers. With no disciplined selection there's selection bias: you tend to read the cases that confirm the
   change, and an unrepresentative handful can't generalise. **This is the missing piece the build targets.**
2. **No durability, no record.** The review happened in a terminal / a chat and left **no artifact** — so its
   findings aren't reproducible or citable as evidence, only as judgment.

And it is **not cheap**: needing a human *and* a pro-LLM per case, it costs about what golden-labelling costs —
**without** golden-labelling's reusability. So in practice it was a **compromise**: reached for when a full
golden set wasn't worth building, but inheriting the cost without the rigor. That trade is defensible for
one-off diagnosis; it is *not* a substitute for a golden set, and the reports that lean on it say so.

## How much to trust it

As a *lens* it is the strongest of the three — a human catches what a machine judge structurally cannot. As a
*measurement* it is the weakest: unsampled, unrecorded, unreproducible. The correct reading of any rung-②
finding is **"a real signal a person saw," not "a metric."** Hardening it (below) is what would let it produce
evidence, not just judgment — and the same sampler is the front door that *feeds* rung ③ (you sample a cohort,
then either eyeball it here or promote it to a golden set).

## Plan

The build — a deterministic case **sampler** (select → cohort → replay → surface) plus a recorded review
loop — is specified in [`plan.md`](plan.md). It is the apparatus this folder is named for, and the tool the
upcoming v5/v6/v7 + eval concurrent review will run on.

*(Created 2026-06-30 as the type-③ modality folder in the by-modality eval-hub. Status: documented, not yet
built — the honest state.)*

## BUILD — 2026-07-02: the sampler exists (status flip: "not built" → "built, smoke-tested")

The apparatus above is now built (Phase 3 of the eval-hardening pass). The two gaps this report named —
**no principled sampler** and **no durable record** — both close:

- **Code (the reusable logic):** [`../../../evaluation/src/diagnosis/sampler.py`](../../../evaluation/src/diagnosis/sampler.py)
  — the four steps as importable functions. **SELECT** on two combinable, outcome-blind signals:
  a deterministic per-case decision score (`decision_scoring.score_vote`/`score_night_target`, the
  DEFAULT) plus a **computed** leverage anchor (`is_swing`/`distance_to_parity` via
  `query_criticality`, never the LLM situation-dimension fill — Phase 1 showed the wolf-side `is_swing`
  fill scores 0.606, worse than the always-False constant). The application-judge score is an **opt-in**
  outlier source, flagged `(uncalibrated)` in every output because that judge's calibration is a later
  phase. `assert_outcome_blind` makes the halo rule executable — selecting on `winner`/`won`/… raises.
  **COHORT** via `data.sampling.sample_cases` (stratified, seed-deterministic). **REPLAY**
  (`replay_case_stage`) is wired to the live `replay/` harness but **guarded default-OFF** (refuses
  unless `enabled=True` after spend sign-off — the `dimension_audit --regen` discipline; building is $0).
  **RECORD** = `ReviewVerdict` + `append_verdict` to a durable local JSONL.
- **CLI:** [`../../../evaluation/src/experiments/case_sampler.py`](../../../evaluation/src/experiments/case_sampler.py)
  (`eval-case-sample` console entry — registers on next install). Thin: args → pipeline → files.
- **Tests:** `tests/test_diagnosis_sampler.py` (14) — halo-rule raises on an outcome signal, outlier
  selection on synthetic scores, same-seed→same-cohort determinism, the computed-not-filled anchor, the
  uncalibrated-judge flag, verdict round-trip. Suite green.
- **Smoke ($0, real local sidecar data — `batch_results/ab_nh_town.jsonl`, read-only):**
  [`sampler_smoke/`](sampler_smoke/) — `review_packets.md` (9 human-readable packets), `cohort_strata.json`,
  and `verdicts.jsonl` (one demo verdict exercising the record path). The 9-case cohort drew from all three
  channels — **by reason:** 3 `outlier:decision_score` · 3 `leverage:is_swing` · 4 `cohort:stratified`;
  **by role:** vigilante 3 · healer 3 · investigator 2 · villager 1; **by phase:** day_vote 4 · night_action 3
  · day_discussion 2; **by game-phase:** late 5 · early 4. Regenerate:
  `poetry run python evaluation/src/experiments/case_sampler.py --batch batch_results/ab_nh_town.jsonl
  --out evidence/evaluation/sampled_human_review/sampler_smoke --n-outliers 3 --n-leverage 3 --cohort-max 4
  --seed 0 --emit-demo-verdict`.

**What this does and does not change.** It closes the *methodology* gaps (selection bias + no record); it
does **not** retro-fit the v5→v7 qualitative calls that were made by the old ad-hoc reading — those stay
"a real signal a person saw," per the trust reading above. The sampler is the tool the upcoming
v5/v6/v7 + eval concurrent review runs on, and the front door that feeds rung ③ (sample → review →
promote the worth-labelling ones).
