# Baseline matching and paired replay validation

A Level 3 page for [Curating the lessons](curating_lessons.md), step 3: how I build credit's
comparison with play without memory, why I changed it, and how turn replays could check it.

For each lesson, credit subtracts the memory-off baseline from the average grade of its followed
decisions. When the follows fall in several baseline groups (different days, say), the baseline is
weighted by the number of follows in each group. The difference is then multiplied by n/(n + 5), and a
lesson with at least 8 follows below −0.15 is pruned. These thresholds are operating rules I chose, not
significance tests.

## Why match the baseline?

The baseline is an observational comparison: if the followed decisions and the memory-off ones come
from different game situations, their grades can differ even when the lesson has no effect. Game day
is one such difference, because early votes have less to go on than late ones.

The June nine-seat store showed it. A villager lesson to abstain early was followed 69 times, all on
day 2, and under the rules of the time those abstentions averaged 0.00:

| Compared with | Lesson average | Memory-off average | Score |
|---|---|---|---|
| Villager votes, all days | 0.00 | +0.21 | −0.20, pruned |
| Villager votes, day 2 | 0.00 | +0.02 | −0.02, kept |

Memory-off villagers abstained on 85% of their day-2 votes, so the lesson mostly told players to do
what they did anyway. That removed the case for pruning it, not the doubt: under today's rule, which
grades an abstention bad on a day that ends with nobody voted out, the same lesson scores −0.18 against
its own day, pruned, just. So the day-2 row shows the lesson was not harmful under the rule of the time,
not that it was harmless. The July Vigilante lesson is the opposite case: matching by day would have
sheltered it, and only the grading rule catches it
([The lesson that pruning failed to remove](abstention_credit.md)).

Credit now groups the baseline by game day: days 1, 2 and 3 separately, and day 4 onward together. A
group needs at least 20 memory-off decisions, or the follow is compared with all days; on ten seats no
group reaches 20 yet, so every follow still falls back. Day matching removes one difference, not the
board, the information available or which players choose to follow a lesson.

**Why day and not outcome.** The day number is fixed before the decision, so matching on it removes the
mix of situations without hiding the lesson's effect. Matching on the day's outcome, such as a day that
ended with nobody voted out, would cut through the effect itself: the July investigation found that the
outcome is partly what the lesson causes
([blind-spot log](../../../evidence/credit/blindspot_fix/experiment_log.md) ④e).

## Proposed validation with paired turn replays

A **paired turn replay** tests the lesson more directly. Starting from the same recorded player
input, I would replay the decision twice: with the lesson and without it, keeping the model, settings
and the rest of the prompt fixed, so the lesson is the only difference. Each condition runs more than
once, because the model can choose differently on identical input.

The check I would run:

- **Eligible lessons:** at least 8 graded follows, the minimum required for pruning.
- **Sample:** up to 10 randomly selected followed turns per lesson.
- **Replay conditions:** three runs per turn with the lesson and three without it, offline at batch
  prices. Generate both conditions afresh so model or prompt changes since the original game do not
  become part of the comparison.
- **Primary measure:** the mean paired grade difference, with the lesson minus without it, averaged
  over repeated runs and sampled turns. Grade both conditions with the same rules and keep other
  players' actions fixed to the record. Also report how the distribution of chosen moves changes.
- **Pass criterion:** the lessons credit prunes are ones whose removal improves the grade, and the
  lessons it keeps are not. Each estimate carries its uncertainty; an inconclusive result validates
  neither keeping nor pruning.

This measures the lesson's effect on the rule grade at the sampled turns, and those turns were picked
because the lesson was followed there, so it says nothing about the other situations where the lesson
might be retrieved. The paid model calls and the blindness to other players' responses are why the
replay checks credit from time to time instead of replacing it (step 3 of the main page).

## What has been tested

A related nine-seat pilot in July replayed 100 town decisions from the loop's failure games with no
memory, the full store and the corrected, pruned store. It tested a change to the whole store, not the
removal of one lesson. The pruned store graded +0.14 against the full store's +0.04 and no memory's
+0.13, but only 2 to 6 decisions changed between any two stores (McNemar p 0.5 to 1.0), so it shows a
direction only. The ten-seat paired replay has not been built.

Evidence: the [day-matched re-scoring results](../../../evidence/credit/day_matched_baseline/results.json),
[July replay experiment log](../../../evidence/credit/blindspot_fix/experiment_log.md), and
[baseline implementation](../../../Agents/memory/consolidation/credit_rules.py). Further source notes
are recorded in the parent page.
