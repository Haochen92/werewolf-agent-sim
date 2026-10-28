# The lesson that pruning failed to remove

A Level 3 case study for [Curating the lessons](curating_lessons.md), step 2: one lesson from the July
nine-seat learning loop, why credit kept it, and how its score moves under each fix.

## The lesson

The July loop played games, credited the lessons, wrote new ones and pruned the store, four times over.
One lesson it kept was for the Vigilante's day vote:

> "Abstain from voting when the information landscape is entirely speculative and no clear consensus
> exists, in order to preserve your vigilante identity and avoid creating a public voting record that can
> be scrutinized by wolves."

Players followed it 19 times, and it survived every credit pass. The finished store then played 30 boards
against no memory and leaned worse
([Testing whether memory helps](../testing_memory/testing_memory.md#what-each-test-led-to)), and in
those memory games 111 of the town's 117 abstentions fell on days that ended with nobody voted out. That
sent me looking for advice to hold back, without showing that this lesson caused the result: about half of
the store's 168 lessons advised some form of caution.

## Why credit kept it

**Every town abstention was graded neutral.** An abstention's harm is a vote that never happened, and a
rule that grades whom a player voted for has nothing to grade. The 19 follows came out 2 good, 15 neutral
and 2 bad: an average of exactly zero.

**The comparison with memory-off play was missing, and the code used zero in its place.** The lesson was
tagged as concealment advice, so credit looked for memory-off concealment on the Vigilante's vote, found
none, and compared zero with zero: a score of 0.00, never near the prune line at −0.15.

## Its score under each fix

I re-scored its follows (15 on day 2, 4 on day 3) against memory-off Vigilante votes from the same loop.
The score is the difference times n/(n + 5).

| Grading of an abstention | Compared with | Lesson average | Memory-off average | Score |
|---|---|---|---|---|
| Neutral, as in July | nothing (zero used) | 0.00 | 0.00 | 0.00, kept |
| Neutral | all days | 0.00 | +0.20 | −0.16, pruned, just |
| Neutral | the same days | 0.00 | +0.10 | −0.08, kept |
| Bad on a day nobody was voted out | all days | −0.79 | +0.02 | −0.64, pruned |
| Bad on a day nobody was voted out | the same days | −0.79 | −0.31 | −0.38, pruned |

Matching by day fixed the June mistake (step 3 of the main page), but it would have sheltered this lesson:
Vigilantes without memory also abstained on over half their day-2 votes. Only the grading rule catches it.
Under that rule the June villager lesson scores −0.18 against its own day: pruned, just.

The rule carries a strategic judgement: the town needs eliminations to win, and every day without one hands
the killers another night. An abstention on a day when someone was voted out stays neutral. A gentler rule,
bad only when this one vote could have decided the day, would spare every abstainer in a mass abstention,
which is exactly how this failure looked.

## The fix in today's rules

The ten-seat rules close both gaps. A town abstention on a day that ends with nobody voted out is graded
bad, and a lesson with no memory-off comparison is left unscored, never compared with zero
([the rule table](../../../evidence/credit/report.md#2-how-one-decision-is-graded)).

Re-scoring the July store with the new rule pruned this lesson and kept three control lessons I had chosen
in advance as good advice. That check is weaker than it sounds: one control had no follows in those games,
so it could not have been pruned, and the controls were scored against all days only.

## What a small replay can and cannot show

A replay plays a recorded turn again with a different store and grades the new decision by the same rules.
My first replay used turns from earlier games and saw nothing: their frozen discussion came from players
who had never seen these lessons, so the hesitant talk the harm ran through never happened.

The corrected replay used the loop's own failure turns: 100 town decisions from the memory games of the
30-board test, which no lesson had been written from. It compared whole stores, not this lesson alone:

| Store | Mean grade |
|---|---|
| No memory | +0.13 |
| Full store, 168 lessons | +0.04 |
| Pruned under the corrected rules, 142 lessons | +0.14 |

Between any two stores only 2 to 6 decisions changed (McNemar p 0.5 to 1.0), so this shows a direction,
not a size. A replay also holds every other player to the record, so it cannot see a speech that changes
how the room votes, which is where much of the abstention spread.

## Why match on the day, not on the day's outcome

The comparison could be narrowed further, to days that also ended with nobody voted out. Vigilantes
without memory grade almost as badly on those days, and the lesson's score shrinks to between zero and
−0.15. But the outcome is partly what the lesson causes: on the same boards, memory games ended more days
with nobody voted out than games without it. Matching on the outcome would remove the harm along with the bias. The game day is
fixed before anyone decides, so matching on it removes the mix of situations without hiding the effect.

## What was not done

The corrected loop was never played again, so whether it would learn a better store is untested. The
[blind-spot log](../../../evidence/credit/blindspot_fix/experiment_log.md) is the record.

<!-- Sources and verification, 2026-10-28:
Lesson text, 19 follows, 111 of 117 abstentions on no-lynch days, 30 boards: evidence/credit/report.md §6;
blindspot_fix/experiment_log.md §①. Lesson record: blindspot_fix/scored_stores/loop_run__neutral/
strategy_points.json, namespace vigilante/day_vote, key 90324c3c-c8a6-4d00-a1c2-ee1312034c74:
positive 2 / neutral 15 / negative 2 (verified 2026-10-28); loop_run__deadlock_negative: 2 / 0 / 17.
Endpoint result (-0.147, 19 of 30 boards, p 0.065): testing_memory.md "What the endpoint showed".
Caution share: 89 caution-family lessons of 168 (blindspot_fix/step1_validation.md, endpoint corpus).
Zero baseline: evaluation/src/loop/credit.py base_for returns 0.0 when the cell is missing; the lesson's
sp_type is "concealment", so it looked up conceal/vigilante/day_vote, absent from
scored_stores/loop_run__neutral/base_rates.json (plain vigilante/day_vote +0.20, n 90).
Table: evaluation/experiments/credit_day_matched_check.py -> evidence/credit/day_matched_baseline/results.json
(july_vigilante_abstain; nine-seat grader credit_backfill; follow days 15 x 2, 4 x 3; as run base all days
+0.200 -> -0.158, same days +0.102 -> -0.081; corrected lesson -0.789, base all days +0.022 -> -0.643, same
days -0.306 -> -0.383). Memory-off Vigilante day-2 abstain rate 0.548 (n 31). Row 1 is the July pass as run.
The step-1 figure -0.62 (step1_validation.md, loop_run) was still computed against zero. June lesson -0.18:
results.json june_villager_abstain.corrected.score_same_day -0.179.
Prune line -0.15 and the n/(n+5) damping: Agents/memory/consolidation/config.py, credit.py.
Strategic reason and the pivotal-vote alternative: experiment_log.md ④e ("pivotality refinement").
Controls: experiment_log.md ③ and step1_validation.md (three good controls kept; base_for, all days).
Replays: experiment_log.md ④ (first replay on held-out June-era cases, null; frozen discussion) and ④b
(100 endpoint memory-on town cases; empty +0.13, full_store +0.04, fixed_pruned +0.14 overall mean value;
discordant pairs 2-6, McNemar p 0.5-1.0; held out: 0 of 30 game ids overlap the 40 loop games). 26 lessons
removed for the 142-lesson store (step1_validation.md, endpoint corpus, fixed: 25 pruned, 1 evicted).
Outcome matching: experiment_log.md ④e (memory-off Vigilantes on no-lynch days -0.82 vs the lesson -0.97;
outcome-matched difference about -0.15 endpoint, about 0 loop; memory games 33% vs 27% of day-2-and-later
days with no lynch on paired boards). The log calls this "day-conditioning"; it means the day's outcome.
Corrected loop never played: experiment_log.md ⑥.
Models: the July players were gemini-3.1-flash-lite at the "minimal" thinking level, which produced no
reasoning tokens (experiment_log.md ⑦). -->
