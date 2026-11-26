# Comparing like with like: the credit baseline matched by game day (2026-10-28)

Credit compared a lesson's followed decisions with memory-off decisions by the same role and phase, pooled
over every day. The owner asked whether one average per role and phase is fair when lessons fire at
particular moments. It was not. Both abstain lessons on the curating page fired early (the June villager
lesson on day 2 every time; the July Vigilante lesson on days 2 and 3), and early days grade very
differently from late ones. *Note, 2026-10-28:* the June lesson is now in step 3 of the curating page
(`writeup/memory/curating_lessons/curating_lessons.md`); the July lesson has its own page,
[`abstention_credit.md`](../../../writeup/memory/curating_lessons/abstention_credit.md).

Code: `evaluation/experiments/credit_day_matched_check.py` (nine-seat grader `credit_backfill`, no model
calls). Output: `results.json`.

| Lesson, grading | Follows | Lesson average | All-day base → score | Same-day base → score |
|---|---|---|---|---|
| June villager, abstain neutral (as run) | 69 | 0.00 | +0.21 → −0.20 (pruned) | +0.02 → −0.02 (kept) |
| June villager, abstain on a no-lynch day bad | 69 | −1.00 | −0.11 → −0.83 | −0.81 → −0.18 (pruned, just) |
| July Vigilante, abstain neutral (as run) | 19 | 0.00 | +0.20 → −0.16 (pruned, just) | +0.10 → −0.08 (kept) |
| July Vigilante, abstain on a no-lynch day bad | 19 | −0.79 | +0.02 → −0.64 | −0.31 → −0.38 (pruned) |

Scores are the difference times n/(n+5).

Memory-off villagers on day 2 abstained 85% of the time and averaged +0.02; on day 4, 7% and +0.55. So the
June lesson mostly told players to do what they did anyway, and the earlier "77% abstain when following an
abstain lesson, against 32% without memory" (`effectiveness/v6_sp_ab`) compared day-2-heavy follows with
an all-day rate. It is withdrawn from the write-up.

**Why day and not outcome.** The day number is fixed before the decision, so matching on it removes the
situation mix without hiding the lesson's effect. Matching on the day's outcome (a day that ended with no
lynch) would cut through the effect itself: v7's blind-spot log ④e found the outcome is partly what the
lesson causes.

**What followed.** Ten-seat credit now matches the baseline on game day (`credit_rules.py`; `TickConfig`
`baseline_by_day`, `baseline_min_n`; days 1, 2, 3 and 4+; tests in `tests/memory/test_credit_day_baseline.py`).
A day needs at least 20 memory-off decisions, else the follow is compared with all days. A dry run on the
ten-seat demo (20 memory-on games against the 12 memory-off seed games) changed nothing: no (role, phase,
day) bucket reached 20 (at most 12, 16 for 4+), so every follow fell back and the 4 pruned / 4 evicted / 50
protected lists were identical. At a floor of 10, 47 of 148 scores moved and 2 more lessons were pruned; at
5, 117 moved, but buckets of 5–12 decisions are too thin to trust. The day matching takes effect once there
are roughly 20 or more memory-off games per role. The curating page's June example became the "comparing like with
like" section. *Note, 2026-10-28:* that section no longer exists; the June example is in step 3 of the
curating page, with its table in `writeup/memory/curating_lessons/baseline_matching.md`, and the July example
is on [`abstention_credit.md`](../../../writeup/memory/curating_lessons/abstention_credit.md). A paired replay of the followed turns (with and without the lesson) would test the score
itself; it is not built for ten seats.
