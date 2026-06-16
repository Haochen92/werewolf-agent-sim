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
