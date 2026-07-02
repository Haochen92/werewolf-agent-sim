# Day-Summary — Evaluation Apparatus Report

> **Scope: the apparatus, not the design.** This doc covers two things: *how we measure* day-summary
> quality (the judge and its harness — the L1 layer), and *how far to trust that measurement* (the L2
> layer). The day-summary **design** — the extractor, the prompt from v1 to v4b, the move to structured
> output — is a separate story, told in
> [`../../extraction/day_summary/experiment_log.md`](../../extraction/day_summary/experiment_log.md). For
> the L0/L1/L2 lens and the segment skeleton, see [`../report.md`](../report.md); for the reliability
> ledger, [`../source_map.md`](../source_map.md).
>
> **Verdict: ⚠️ WEAK apparatus. Treat day-summary scores as a smoke test, not a metric.**

## What the apparatus is trying to measure

The day summary is the *only* representation of a past day that any agent sees again — raw transcripts are
never re-shown. Summary quality is therefore a bottleneck for multi-day reasoning. The apparatus exists to
answer one question: does a summary preserve the strategically load-bearing content of a day (accusations,
role claims, vote actions, village dynamics) without fabricating anything?

## L1 — the instrument

**The judge.** `run_day_summary_judge` in
[`judges/day_summary.py`](../../../evaluation/src/judges/day_summary.py) is one LLM call, gemini-2.5-pro by
default. It is **reference-based**: it receives the raw transcript *and* the summary, so it can check each
claim against ground truth instead of scoring blind. (Whether that design actually pays off is the L2
question below.) It scores five dimensions on a 1-5 rubric — `completeness`, `accuracy`,
`evidence_type_clarity`, `village_dynamics`, `epistemic_correctness` — plus a `brief_reasoning` string. It
retries once, then returns `None` on a parse or validation failure.

**The harness.** `day_summary_eval.py`
([`experiments/day_summary_eval.py`](../../../evaluation/src/experiments/day_summary_eval.py)) regenerates a
summary from a frozen transcript with a chosen generation model, then judges it, then aggregates
per-dimension avg/min/max plus a per-pair table. It is module-only: run it with
`python -m evaluation.experiments.day_summary_eval`, there is no console script.

One caveat used to sit here, now closed. Two paths can drop a pair from the aggregate: a generation failure
`continue`s before the pair is ever judged, and a judge `None` is filtered out. Until 2026-07-02 neither
decremented a counter, so a shrunk N would not have surfaced. The harness now reconciles input against scored
count in the summary header (`N/18 pairs scored (G generation failures, J judge failures)`). And in the
recorded runs no pair actually dropped — every score table reads 18/18 — so the historical tables are intact;
the fix guards future runs.

**The dataset.** 18 transcript/summary pairs, taken one per trace from every day with ≥5 discussion messages,
across 8 games drawn from two eval sets. The selection is opportunistic rather than deliberately sampled.
Player roles and game outcome don't change what a good summary of a day's discussion is, so there is nothing
to balance on those axes — but *dialogue difficulty* does vary (how many players pile on, how tangled the
role-claim chains are), and the sample isn't stratified by it. So the flat-high scores may partly reflect easy
dialogues, not only a lenient judge.

**The rubric and prompt.** `DAY_SUMMARY_JUDGE_SYSTEM / JUDGE_USER / RUBRIC` in
[`judges/prompts/day_summary.py`](../../../evaluation/src/judges/prompts/day_summary.py).

## L2 — how much to trust it

**1. It is uncalibrated.** The scores were never checked against human labels or a golden set. Nor have we
run a *second judge model* to test inter-model agreement — every score comes from the one gemini-2.5-pro
judge, which stands as the sole authority.

**2. It is saturated — but mechanistically, not uniformly.** Scores cluster in the 4.4-5.0 band, yet the five
dimensions split cleanly by whether the judge can check them against the supplied transcript. This is where
the reference-based design pays off on some dimensions and not others.

- **The grounded trio: `completeness`, `accuracy`, `epistemic_correctness`.** Each is checkable against the
  transcript and the game context. Did the summary drop player_1? Is this attribution actually in the
  dialogue? Is a death-revealed role treated as confirmed? These are the dimensions that moved, and they
  caught the real failures: dropped accusers, a fabricated Game-Master announcement, and confirmed-vs-claimed
  role errors all surfaced as 1-3 scores in the design log. They are weak as a ranker but genuine as a
  gross-failure detector at the floor.
- **The presence-check pair: `village_dynamics` and `evidence_type_clarity`.** `village_dynamics` scores 5.00
  in every run, every model, every prompt version; `evidence_type_clarity` sits at 4.89-5.00. Both grade
  whether a section exists, and the prompt *forces* both to exist — `SITUATION_STANDARDS` injects a "Village
  dynamics" section, and the structured output forces a per-accusation evidence-type label. The judge almost
  always sees them, so it almost always scores 5. That saturation is a limit of the judge as currently set up,
  not evidence the summaries are perfect: without golden labels the judge can only confirm a forced section
  *exists*, not grade how good it is. A gauge that never moves carries no information, so treat these two as
  non-discriminating for now — a golden set would give the judge something to grade against and could turn
  them into real signal (see the upgrade below).

Net: trust the grounded trio as a smoke alarm (it did ring), and discard the presence-check pair as a metric.

**3. It can't rank near-equal versions — though the gross-failure signal is real.** This is a resolution
limit, not a claim that the whole instrument is noise: the grounded trio genuinely caught real failures
(point 2). What it *can't* do is separate near-peer prompt versions. Per-pair scores swing ±1 between runs,
and the design log's own conclusion is that no version is statistically distinguishable at n=18 single-run, so
the reported version-to-version deltas (−0.11, +0.16, and the like) are within that noise. Both shipped
decisions were therefore made on other grounds — architecture and latency — not on judge deltas.

**4. It grades intrinsic fidelity — which is the right objective here, by design.** The rubric measures
whether the summary accurately captures the day's critically-defined information categories (accusations,
role claims, vote actions, dynamics). It deliberately does *not* measure downstream game outcome. Tying
summary quality to who won would make this a credit-assignment objective, which is both the wrong question
for a summarizer and far less controllable than fidelity to the defined categories. The one honest residual
is narrower: we don't directly test whether a *specific* omission changed a *specific* decision or query. But
since the objective is fidelity to the critical categories, not outcome attribution, that residual doesn't
undercut what the metric is for.

**5. It runs on the v5 framework while the pipeline moved to v6 — but the gap is narrower than it looks.** The
component and its judge both still use the legacy v5 `SITUATION_STANDARDS` (the prose
`information_landscape / consensus / drivers` fields), while extraction and the situation-summary query
migrated to the v6 dimensional schema. Day-summary was left explicitly last and optional in that migration
(`evidence/phase_b/v6_wide_migration_roadmap.md`). Two things keep the gap narrow:

- It is not a missing-fields defect. The v6 per-agent dimensions (exposure, heat, target-landscape) are
  re-derived each day, and the board dimensions (swing, distance-to-parity, criticality) are computed
  deterministically. None of them belong in a village-wide summary.
- It is not the completeness risk it first looks like. The hard game-state facts — the full vote tally, the
  elimination, the death-revealed role — are written verbatim by the game master into `day_summaries` at vote
  resolution (`Agents/nodes/orchestrator.py:185-241`), on a deterministic channel separate from the LLM
  summary. A summary miss cannot lose them.

What the LLM summary uniquely holds, and could drop unrecoverably, is only the *argumentative* residue: the
reasoning behind an accusation, who joined a pile-on, the context of a role claim. So the one open question is
whether a faithful v5-framework summary carries enough of that residue for the v6 consumers. That is the same
narrow residual as point 4 — a specific-omission question — now with a v6 edge, and a smaller gap than a
vote-completeness framing would suggest.

## Verdict, and the cheapest credible upgrade

⚠️ This is a lightweight, uncalibrated, saturated single-judge. It is good enough to catch gross failures —
hallucinated Game-Master announcements and dropped accusers did surface as 1-3 scores — but not to rank
near-peer prompts or to certify "good enough for downstream." It is a smoke test, not a metric.

It also does not need to be more. Day-summary is not a measured bottleneck: the memory system's binding limits
are memory *content* quality and the investigator-transmission cap (the v6 A/B), not summary fidelity. And its
worst-case loss is backstopped by the deterministic game-master channel (point 5).

If it did need to become a real metric, the cheapest upgrade is two moves:

- **Build a small human-referenced golden set** on a few hard pairs (plus one easy pair for a ceiling). For
  day-summary the reference points are the day's accusations, role claims, and vote actions; a citing LLM
  judge scores how many of them the summary covers (recall), with the grounded trio as the faithfulness side
  (precision). This is what would turn the two presence-check dimensions into real discriminators and
  calibrate the grounded trio against human labels. The construction method and its refinements are shared
  across the extraction judges: [`golden_set_method.md`](golden_set_method.md).
- **Decouple regeneration from judging.** Judge one fixed set of summaries N times (instead of regenerating
  each run), so judge-noise can be sized apart from the generation non-determinism that drives most of the
  per-pair swing.

## Evidence: code and L2 artifacts

- **The instrument (code):** [`judges/day_summary.py`](../../../evaluation/src/judges/day_summary.py),
  [`experiments/day_summary_eval.py`](../../../evaluation/src/experiments/day_summary_eval.py),
  `core/schemas.py::DaySummaryScores`, `judges/prompts/day_summary.py::DAY_SUMMARY_*`.
- **L2 artifacts:** the per-config score tables in
  [`../../extraction/day_summary/`](../../extraction/day_summary/) (`eval_summary_*.txt`) are the only
  reliability data that exists. There is **no golden set** — and its absence *is* the headline L2 finding.

*(Inspected 2026-06-28; content-verified 2026-06-29; judge-folder sweep 2026-06-30 re-pointed the prompt
references to the split-out `prompts/day_summary.py` module; v6-currency note added 2026-07-01. Revised
2026-07-02 after author review: prose streamlined for readability; the silent-N harness gap fixed in code (it
now reconciles input vs scored count) and downgraded to a closed note; the objective reframed as intended
intrinsic fidelity rather than a proxy-for-outcome shortfall; the "confounded by construction" point dropped
as misleading; and the version-ranking limit scoped away from a blanket "noise ≥ signal" claim. Colocation:
the design-dominated origin stays in `../../extraction/day_summary/` → ch.3; no L2 artifact was self-contained
enough to relocate, so all are pointed at rather than copied.)*
