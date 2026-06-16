# Forced-applicability screen: store × schema 2×2 (v6 build) — 2026-06-16

**Question.** The original applicability probe (2026-06-13) found that FORCING one applies/partly/does-not
verdict per retrieved memory HURT the vote (0.75→0.55) on the cautious **v5/net-horizon** store. v6 was
built to fix that content. Untested cell (the log flagged it): *good content × forced schema*. Does
forcing per-memory reasoning still hurt on v6, and does v6 memory get **engaged** more?

**Method.** `evaluation/src/experiments/forced_schema_screen.py`. Five arms per held-out town day-vote,
**all votes regenerated in ONE epoch** (the load-bearing discipline — do NOT compare to the prior
0.75→0.55 / +0.120, different epoch): `off` (floor), `v5_plain`, `v6_plain`, `v5_forced`, `v6_forced`.
Each memory arm retrieves top-5 from its OWN store with its OWN native query (v5 = frozen v5 situation
summary; v6 = regenerated under the v6 cell schema), same-game memory excluded from both pools.
n=48 held-out town day-votes (10 games never in the v6 source set), days 2–8, villager/healer/investigator.
Forced arms use `DayVoteOutputStructuredApplicability` (eval-only scaffold). Result:
`run_n48.json`.

## Vote accuracy (hit-a-threat rate; within-run only)

| arm | accuracy | net_value |
|-----|----------|-----------|
| off (no memory) | **0.667** | 0.458 |
| v5_plain | 0.625 | 0.396 |
| v6_plain | 0.604 | 0.375 |
| v5_forced | **0.521** | 0.229 |
| v6_forced | **0.625** | 0.438 |

**Store × schema (forced − plain):** v5 = **−0.104** (forcing HURTS), v6 = **+0.021** (forcing neutral).

## Reads

1. **The old "forcing hurts" REPLICATED same-epoch on v5** (0.625→0.521, −0.104) — and v6 content
   NEUTRALIZES it (0.604→0.625, +0.021). The over-caution collapse is a property of the **cautious v5
   content**, not of the forced schema. This is the cell the prior log left empty; it now has a
   directional answer: **the forced schema is SAFE on v6 where it was HARMFUL on v5.**
2. **v6's value is unlocked by the schema, not by passive retrieval.** Under the plain schema v6 ≈ v5
   (paired flips 3 vs 4, McNemar p=1.0 — a wash). Under the **forced** schema v6 beats v5
   (0.625 vs 0.521; paired flips **8 toward v6 vs 3 toward v5**, p=0.23 — directional, n=48). The richer
   dimensions pay off specifically when the agent is made to reason over each item — consistent with the
   whole v6 thesis (dimensions help when *engaged*, not when dumped).
3. **Engagement/consideration: v6 > v5, but MODEST not "dramatic."** engaged_as_applicable
   (fully+partly) v5 0.649 → v6 **0.697** (+0.048); rejected_does_not_apply 0.351 → 0.303; verdict mix
   shifts toward applicable (fully 34→40, does-not 52→44). v6 memory is judged to fit the board more
   often — the expected sign of better-matched dimensions — but the magnitude is small at n=48.

## Honest caveats (do NOT overclaim)

- **No memory arm beats the no-memory floor (0.667) on this replay slice.** v6_forced and v5_plain both
  land at 0.625, below off. This is the documented day≥3 prompt-ceiling / low-engagement zone, and the
  town memory *win* lives at the GAME level (paired A/B), not in this off-policy vote-replay. So this
  screen says **"forced schema is safe on v6 / v6 engages more,"** NOT "v6+forced beats no-memory."
- **Reliability gap persists on BOTH stores:** row_reliability ≈ 0.33–0.35 — flash-lite emits one
  verdict-per-memory only a third of the time (148/240 and 145/240 verdicts emitted). The "one row per
  memory" contract degrades as memory count grows. **Direct implication for the production migration:**
  the added field on `DayVoteOutput`/`DayDiscussOutput` will NOT reliably cover every memory on
  flash-lite — needs either fewer memories shown, a stronger model for this step, or tolerance for
  partial coverage.
- n=48, McNemar not significant — **triage, not verdict.** Directions are consistent and clean; the
  vote 2×2 is the robust part, the engagement delta is the suggestive part.

## Bottom line

The user's hypothesis is **directionally confirmed on the part that matters**: forcing per-memory
reasoning no longer hurts once the content is v6 (−0.104 on v5 → +0.021 on v6), and v6 memory beats v5
**specifically under the forced schema** (the schema unlocks the dimensions). The "consideration improved
dramatically" half is **only modestly supported** (engaged 0.649→0.697). Enough signal to carry the
forced-applicability schema into the freeze-gate as a v6 arm — but score BOTH vote and engagement, and
fix the one-verdict-per-memory reliability before/at production migration.

## Per-memory coverage: WHY the model under-emits (2026-06-16, n=60 forced-only)

Followed up the reliability gap (one-verdict-per-memory ~0.33). Captured each decision's emitted
`memory_index` set to test the hypothesis *"it drops the low-ranked tail"* (memories are injected in
descending relevance). Runs: `run_coverage_n60.json` (unnumbered), `run_coverage_n60_numbered.json`.

**Hypothesis 1 (tail-drop) — REFUTED.** Coverage-by-rank is FLAT, not declining: v6 rank 1→5 =
0.68/0.50/0.55/0.65/0.52; v5 = 0.63/0.53/0.57/0.45/0.57. Rank 5 is covered as often as rank 2. Emitted
index sets are scattered arbitrary subsets (`[3]` alone, `[5]` alone, `[1,4]`, `[2,4]`, `[1,3,5]`) — a
clean top-prefix only 28–38% of the time. So it is NOT deprioritizing the tail; it emits verdicts for a
*random partial subset*.

**Hypothesis 2 (missing indices → can't track the list) — ALSO REFUTED.** Numbered every injected memory
`1. … 2. …` in `format_retrieved_observations` (the scattered subsets looked like list-tracking failure).
Re-ran: coverage did NOT improve — if anything nudged down (within temp-1.0 noise):

| arm | verdicts emitted | row_reliability | clean-prefix |
|---|---|---|---|
| v5_forced unnumbered | 165/300 | 0.233 | 0.283 |
| v5_forced **numbered** | 134/300 | 0.117 | 0.217 |
| v6_forced unnumbered | 174/300 | 0.333 | 0.383 |
| v6_forced **numbered** | 164/300 | 0.233 | 0.283 |

Numbering verified present in the prompt, so the null is real. ⇒ **the under-emission is NOT a
list-tracking / indexing problem.** It is flash-lite simply not adhering to "one verdict per memory" — it
comments on whichever memories it finds salient and skips the rest, numbered or not.

**What this means for the production migration.** Numbering memories is still a PREREQUISITE for any
per-memory `memory_index` field (kept), but it is NOT sufficient for coverage. Real coverage levers,
untested here: (a) **pin the list length in the schema** (dynamic `memory_applicability` with
min=max=N) so structured-output retry forces N rows — RISK: flash-lite may emit filler/rubber-stamp
verdicts to hit the count; (b) **show fewer memories** (top_k=3) so "one each" is tractable; (c) a
**stronger model** for this step. The honest status: on flash-lite the forced field gets PARTIAL
per-memory coverage regardless of numbering — design the migration around partial coverage or change one
of (a)/(b)/(c).

## Prompt-limit vs output-limit — DECISIVE: it was DELIVERY (2026-06-16, v6-only n=60)

The "one verdict per memory" instruction lived ONLY in the pydantic field description (0% in the prompt
body). Ran base / promptbody / pin to disambiguate (`run_variants_n60.json`):
- **base** — instruction in field-desc only: 168/300 verdicts, row_reliability 0.27, ranks 0.48–0.63.
- **promptbody (A)** — same instruction ALSO stated in the prompt body ("output exactly one verdict for
  each of the N numbered observations"): **302/300 verdicts, reliability 0.97, every rank 1.0.**
- **pin (B)** — `memory_applicability` length pinned to N in the schema: **300/300, reliability 1.0.**

**Verdict: PROMPT/DELIVERY limitation, NOT output limitation.** Coverage went 0.27 → 0.97 purely by
moving the instruction into the prompt body. The model was always capable; it wasn't attending to an
instruction buried in a structured-output field description (consistent with the prior "delivery matters"
finding). Both A and B produce **real, distinct** rows — all_same_verdict_frac 0.0, distinct_why_ratio
1.0 under both — so neither is rubber-stamping/filler. Capability was never the gate.

**Two consequences worth carrying:**
1. **The earlier engagement metric was optimistically biased by partial coverage.** Under full coverage,
   engaged_as_applicable drops 0.798 → ~0.55 and `does_not_apply` ~quadruples (34 → 133/134). The
   memories base SILENTLY SKIPPED were disproportionately the inapplicable ones — so the partial-coverage
   "v6 engages more (0.697)" read was inflated. The true applicable rate is ~55%; the v6-vs-v5 engagement
   comparison should be re-run under prompt-body full coverage to be clean.
2. **Full per-memory coverage does NOT hurt the vote on v6** (acc base 0.617 / promptbody 0.60 / pin 0.65,
   within noise) — forcing complete reasoning is safe here (contrast v5, where the *content* hurt).

**Production migration takeaway.** Put the per-memory instruction in the PROMPT BODY (the memory-context
block), not just the added field's description — that alone fixes coverage. Pinning the list length is a
viable belt-and-suspenders (also full, also non-filler) but the prompt-body line is the lighter touch and
the natural home. Either lands with the forced-applicability field on `DayVoteOutput`/`DayDiscussOutput`.
