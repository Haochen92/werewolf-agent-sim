# Day-Summary — Evaluation Apparatus Report

> **Scope: the apparatus, not the design.** This covers *how we measure* day-summary quality (the judge +
> harness) and *how far to trust that measurement* (L1 + L2). The day-summary **design** (the extractor,
> prompt v1→v4b, structured-output move) is the memory-system story and stays in
> [`../../extraction/day_summary/experiment_log.md`](../../extraction/day_summary/experiment_log.md). The
> L0/L1/L2 lens + segment skeleton: [`../report.md`](../report.md); reliability ledger:
> [`../source_map.md`](../source_map.md).
>
> **Verdict: ⚠️ WEAK apparatus — treat day-summary scores as a smoke test, not a metric.**

## Objective the apparatus targets

The day summary is the **only** representation of a prior day that any agent sees — raw transcripts are
never re-shown. So summary quality is a bottleneck for multi-day reasoning, and the apparatus should answer:
*does a summary preserve the strategically load-bearing content of the day (accusations, role claims, vote
actions, village dynamics) without fabricating?*

## L1 — the instrument

- **Judge** — `evaluation/src/judges/day_summary.py::run_day_summary_judge`. One LLM (gemini-2.5-pro default,
  `judges/day_summary.py:18`), **reference-based**: it is handed the *raw transcript AND the summary*
  (`prompts/day_summary.py:9,15-32`), so it can check claims against ground truth rather than score blind — which dims
  that buys is the L2 question (below). A 5-dimension rubric each scored 1-5 — `completeness · accuracy ·
  evidence_type_clarity · village_dynamics · epistemic_correctness` (`core/schemas.py::DaySummaryScores`) —
  plus `brief_reasoning`. `max_retries=1` (`day_summary.py:51`); on a parse/validation failure it returns
  `None`.
- **Harness** — `evaluation/src/experiments/day_summary_eval.py` (**module-only**: `python -m
  evaluation.experiments.day_summary_eval …`; no console script). It *regenerates* a summary from a frozen
  transcript with a chosen gen-model/thinking, **then** judges it; aggregates avg/min/max per dimension + a
  per-pair table + a reasoning dump (`eval_summary_*.txt`). **Two silent-N-shrink paths, no counter on
  either:** a generation failure `continue`s before the pair is ever judged (`day_summary_eval.py:54-56`),
  and a judge `None` is filtered out of the aggregate (`day_summary_eval.py:107`) — so effective N can fall
  below 18 without surfacing in the score table.
- **Dataset** — 18 transcript/summary pairs, **opportunistically selected, not stratified**: every day with
  ≥5 discussion messages, one per trace (`day_summary_regen.py:46`), across 8 unique games drawn from two eval
  sets. No balance across roles, outcomes, or difficulty — so the flat-high scores may partly reflect an easy
  sample, not only a lenient judge.
- **Rubric/prompt** — `evaluation/src/judges/prompts/day_summary.py::DAY_SUMMARY_{JUDGE_SYSTEM,JUDGE_USER,RUBRIC}`.

## L2 — how much to trust it

1. **Uncalibrated.** Never checked against human labels or a golden set; no inter-judge agreement. The single
   judge is the sole authority. *(Modality (c) = none.)*
2. **Saturated — but mechanistically, not uniformly.** Scores cluster in ~4.4–5.0, yet the five dims split by
   *whether the judge can check them against the supplied transcript* — the reference-based design (L1) pays
   off on some dims and not others:
   - **Grounded — `completeness`, `accuracy`, `epistemic_correctness`.** Checkable against the transcript +
     game context (did the summary drop player_1? is this attribution in the dialogue? is a death-revealed
     role treated as confirmed?). These are the dims that *moved* and that *caught the real failures* —
     dropped accusers, a fabricated Game-Master announcement, and confirmed-vs-claimed role errors all
     surfaced as 1–3 scores in the design log. Weak as a ranker, but a genuine gross-failure detector at the
     floor.
   - **Presence checks on forced structure — `village_dynamics` (= 5.00 in every run, every model, every
     prompt version), `evidence_type_clarity` (4.89–5.00).** These grade *whether a section/annotation
     exists*, and the prompt *forces* both — SITUATION_STANDARDS injects a "Village dynamics" section and the
     structured output forces per-accusation evidence-type labels — so the judge almost always sees them and
     scores 5. A gauge that never moves carries no information: it cannot separate "genuinely solved" from
     "can't grade this." The design log reads 5.00 as "works as intended" (the L0 reading); the L2 reading is
     "presence check on forced structure — discard as a discriminator."
   Net: trust the grounded trio as a *smoke alarm* (they did ring), discard the two presence-check dims as a
   *metric*.
3. **Noise ≥ signal.** The log itself concludes *"within noise at n=18 single-run; no version is
   statistically distinguishable,"* and per-pair scores swing ±1 between runs. The instrument's resolution is
   coarser than the prompt deltas it is used to compare — the reported deltas (e.g. −0.11, +0.16) are noise.
4. **Confounded by construction.** The harness regenerates *and* judges in one pass, so any measured delta
   conflates (a) generation non-determinism, (b) the prompt change, and (c) judge noise. Nothing isolates
   judge variance (no repeat-judge-same-summary) or generation variance (no repeat-gen).
5. **Measures a proxy, not the objective.** It grades *intrinsic rubric quality*, not *downstream usefulness*
   (does an omission change an agent decision or a retrieval query?). The folder's own "What's missing" §3
   named this gap and never closed it — the deepest limitation.

## Credit (good QC, not laundering)

The author was honest about (2)–(3), and — *precisely because* the judge could not distinguish versions —
made the final call (keep v4b structured output; flash-lite + medium thinking) on **deterministic
architectural grounds** (forced enumeration of accusations, deterministic serialization), not on judge
deltas. Falling back to a non-eval reason when the apparatus can't resolve a difference is the correct move,
and is itself an honest reading of the instrument's limits.

## Verdict + cheapest credible upgrade

⚠️ A lightweight, uncalibrated, saturated single-judge. It is good enough to catch **gross** failures —
hallucinated Game-Master announcements and dropped accusers did surface as 1–3 scores — but **not** to rank
near-peer prompts or certify "good enough for downstream." **Smoke test, not a metric.**

Cheapest upgrade that would make it a metric: (a) a small human-anchored golden set on a few hard pairs — to
turn the two presence-check dims into real discriminators (or prove the forced sections are genuinely good)
*and* to calibrate the already-moving grounded trio against human labels; (b) decouple regeneration from
judging — judge one fixed set of summaries N times to size judge-noise separately from generation noise.

## Evidence (code + L2 artifacts)

- **Code (the instrument):** `evaluation/src/judges/day_summary.py`,
  `evaluation/src/experiments/day_summary_eval.py`, `evaluation/src/core/schemas.py::DaySummaryScores`,
  `evaluation/src/judges/prompts/day_summary.py::DAY_SUMMARY_*`.
- **L2 artifacts:** `../../extraction/day_summary/eval_summary_*.txt` (the per-config score tables — the only
  reliability data that exists). **No golden set** — its absence *is* the headline L2 finding.

*(Inspected 2026-06-28; content-verified 2026-06-29. Colocation: original folder stays put — design-dominated,
→ ch.3; no L2 artifact was self-contained enough to move, so all are pointed-at. Judge-folder sweep 2026-06-30
re-pointed the three prompt references to the `prompts/day_summary.py` module after the package split — no
content change.)*
