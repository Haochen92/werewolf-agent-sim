# Curating the lessons (Level 2, draft)

Rewritten 2026-10-27 after the owner's review, to claim less. Restructured 2026-10-28 (owner): each
scoring step gives its reason and its limits; the baseline reasoning, matching by day and the turn replay
sit in step 3, with the June table in the baseline L3; the July abstention case moved to its own L3, one
sentence kept in step 2; the page closes with limitations, what remains open, and where credit runs.
**Link (Level 3)** specifies a planned investigation. Claim scope is recorded in
[`../../memory_presented_set.md`](../../memory_presented_set.md).

---

## Curating the lessons

A fixed store keeps serving the same advice whether or not it helps. Players decide whether to follow a
lesson from how well it seems to fit, without seeing how it has worked before, so a poor lesson can be
retrieved and followed again and again.

So I added **decision-level credit assignment**: after a game, the decisions made while following a
lesson are graded and compared with play without memory, and lessons that do clearly worse are removed.
It is a rough filter for the most-used advice, not a measurement of what each lesson is worth, and building
it showed how easily such a comparison misleads.

### How a lesson is scored

**1. Linking decisions to lessons.** To score a lesson, credit first has to know which decisions it
shaped. A player sees up to six lessons at once, and nothing in the move itself says which of them it
acted on. So for every lesson shown, the player reports whether it followed it, overrode it or found it not
relevant, and credit scores a lesson only on the decisions where it was marked followed.

That report is the player's own claim, so I checked it. A model reader compared 100 sampled follow reports
from the ten-seat games with the decisions taken: of the 81 it could judge, 74 did what the lesson said and
5 did part of it, and when I hand-labelled 20 of them against the game records, I agreed with every one it
judged. Credit also counts a followed discussion lesson only if the player actually spoke. A matching report
still shows only that the move fitted the lesson, not that the lesson caused it; that question belongs to
the comparison in step 3.

**2. Grading the decision.** Fixed rules score every vote, night action and day of discussion +1 (good),
0 (neutral) or −1 (bad) from the roles revealed after the game: a town vote for an enemy is good and a vote
for a townsperson bad; a Healer who saves a townsperson from an attack is good, and a Vigilante who shoots
one is bad.

I chose rules over the two obvious alternatives. The game's result is too far from any one decision: a win
depends on every player's moves and on luck, so it would credit a lesson for a teammate's good play, the
same halo that made winning moves look good in extraction
([page 1](../extraction_synthesis/extraction_synthesis.md#when-winning-made-a-move-look-good)). A model
judge reading each decision after the game would cost a call per decision, could disagree with itself on a
second reading, and tends to judge by who won as well. Rules cost nothing, give the same grade every time,
and can be checked line by line.

The rules are my definition of a good move, and a proxy. They grade what a move did once the roles are
known, not whether it was wise given what the player knew at the time. Some turns are left unscored, and a
day of discussion is graded through that day's vote. A rule can also simply be wrong, and then every
decision it covers is scored wrongly. That happened once: the rules graded every town abstention as
neutral, which let a July lesson advising the Vigilante to sit out the vote survive every credit pass.
Abstaining on a day that ends with nobody voted out is now graded bad.

**Link (Level 3):** How each decision is graded: the rules for all twelve roles and why each row is so, in
[the credit report](../../../evidence/credit/report.md#2-how-one-decision-is-graded). The July lesson that
survived pruning is a separate case study:
[The lesson that pruning failed to remove](abstention_credit.md).

**3. Comparing with play without memory.** A grade on its own does not say whether a lesson helped.
Some decisions go well almost whatever the player is told, and some go badly: in the June nine-seat games,
a Serial Killer's vote graded +0.71 on average with no memory at all, and a villager's vote on day 2 graded
+0.02. A lesson attached to the first would look good for doing nothing, and one attached to the second
would look bad. To credit a lesson I need the counterfactual, how the same decision would have gone
without it. The baseline stands in for that: decisions made by players with no memory, graded by the same
rules, much like a control group. A lesson's score starts from how far its followed decisions sit above or
below that baseline.

A control only works if it matches, so I try to compare each followed decision with memory-off decisions
made in as similar a moment as possible: the same role, the same kind of decision and the same game day. My
first baseline matched only the role and the kind of decision, and that was not enough. A June villager
lesson to abstain early looked harmful against villagers' votes over the whole game, and credit removed it.
Against day 2 alone, where all its follows fell and villagers without memory abstained most of the time
anyway, it made almost no difference.

Even this is a rough match. Two day-2 votes can come from very different boards, and ten-seat play does
not yet have enough games without memory to fill each day, so for now the comparison still falls back to
the whole game. The closest match is the same turn: a turn replay plays a recorded turn where a lesson was
followed again, once with the lesson and once without, so the lesson is the only difference. A replay costs
a model call for every run, and it sees only that one decision. An effect that cascades through other
players, such as a speech that swings the room's vote, needs whole games played with and without memory
([Testing whether memory helps](../testing_memory/testing_memory.md)). So a replay suits checking credit
from time to time rather than replacing it. The check I would run takes the lessons with at least 8 graded
follows, the only ones credit can prune, and replays up to 10 of each one's followed turns, drawn at
random, with and without the lesson, three times each, offline at batch prices. It would pass if the
lessons credit prunes are ones whose removal improves the grade and the lessons it keeps are not. The
ten-seat replay is not built.

[**Baseline matching and paired replay validation (Level 3)**](baseline_matching.md) explains how the
baseline is built, the June re-scoring that led to matching by day, and the replay design and its limits.

**4. Waiting for enough evidence.** A lesson followed only a few times can look good or bad by luck alone:
a vote that happened to land on a wolf, a night when nobody attacked. Pruning on that evidence would remove
sound advice, so credit holds back in two ways. First, it pulls thin scores toward zero by multiplying the
difference from the baseline by n/(n + 5), where n is the number of graded follows: a lesson with 5 follows
keeps half its difference, and one with 20 keeps four fifths. I set the 5 by hand, not by fitting it, because
in the June runs most lessons had only about three follows. Second, it prunes nothing before 8 follows.
Splitting the June games in two showed why: a lesson with only a few follows in each half turned from
negative to positive, while lessons with dozens of follows kept their sign.

### What the score decides

| Decision | Rule |
|---|---|
| Prune | A score below −0.15 after at least 8 follows |
| Protect from pruning | A positive score after at least 2 follows |
| Evict | Shown at least 8 times and never followed, and overridden at least as often as marked not relevant |

These numbers are judgement calls set on the nine-seat games, not fitted values. The prune line sits at
−0.15 rather than 0 because about half of all lessons sat just below zero by chance, and the margin leaves
those alone. Protection needs only 2 follows because it does less: it only stops a lesson being pruned, and
it is checked again on every pass, so a lesson that turns negative loses it. Two follows is still thin
evidence, and it is the first number I would revisit. Eviction ignores lessons that are only marked not
relevant, because good advice shown in the wrong situation is a retrieval problem, not bad advice.

In practice, credit acts only on the most-used lessons and leaves the rest alone. A wrong prune is cheap to
undo: each pass logs what it removed, and the observations behind a lesson stay in the store, so synthesis
can write it again.

### Limitations

The score is a comparison, not a measurement of cause. Players choose when to follow a lesson, so the
moments they choose may be easier or harder than the baseline's even on the same day, and decisions from
the same game are not independent of each other. It looks only at the decision a lesson was followed on,
not at what that decision did to the rest of the game. And it acts only on lessons followed often enough to
reach the floor, which leaves most lessons unjudged. Its comparison has also been wrong once in a way that
looked convincing, which is a reason to read any single score with care.

### What remains open

The turn replay that would check credit's verdicts is not built for ten seats. Matching by game day is in
the code but waits for more games played without memory before it changes any score. The thresholds were
set on nine-seat games and have not been recalibrated for ten. And no experiment has yet shown that the
lessons credit removes made play worse, or that a store curated this way plays better than one that is not,
which is one reason memory is still treated as an experiment.

### Where credit runs today

Credit is an offline pass over recorded games with no model calls, run separately from the paid synthesis
of new lessons. On ten seats it has run once, over 20 batch games, to show the pass works; it was not a test
of whether the curated lessons are better. Games with a human seat can be credited too, grading only the
AI seats' decisions.

<!-- Sources and verification, 2026-10-28 (owner review: compare like with like; claims an evaluator expects):
June lesson: memory_stores/v6_1/strategy_points.json key bc7b8a88-356e-4a89-a139-ec548f9bfe7a (villager/day_vote;
action quoted, first sentence). Day-matched re-scoring: evaluation/experiments/credit_day_matched_check.py ->
evidence/credit/day_matched_baseline/results.json (nine-seat grader credit_backfill; 69 follows all day 2;
memory-off villager vote +0.21 all days, +0.02 day 2 (n 328), +0.55 day 4; abstain 85% day 2, 7% day 4;
corrected rule: lesson -1.00, day-2 base -0.81 -> -0.18). Pruned by the retroactive b1 prune
(v7/experiment_log.md §3; memory_stores/v6_1_b1pruned lacks the key; run on a copy). Removed 2026-10-28: "77%
vs 32% abstain" (v6_sp_ab) compared day-2-heavy follows with an all-day rate; day 2 alone is 85%.
Follow check: evaluation/experiments/attribution_check_sample.py -> evidence/credit/attribution_check_ten_seat/
(100 stratified ten-seat follow reports from batch_results/v8_demo, 35 discussion / 30 vote / 35 night; reader
agents; 74 match, 5 partial, 2 mismatch, 19 uncheckable (10 wolf night chats whose content the sample left
out); 74/81 = 91%, Wilson 95% 83-96%). Owner hand-labelling of 20 (owner_handcheck.md, 2026-10-28, against the game
records): agreed on all 16 the reader judged; 3 of 4
uncheckable resolved as match from the record, 1 stays. The July check
(15 of 2,387 nine-seat reports, 13 match) is in evidence/credit/report.md §5. Speech guard: credit.py _spoke.
Grading: grading.py; rules-first stance. Night examples: grading.py _grade_healer, _grade_vigilante.
Wolf chat follows: grading.py pack_move_grade + pack_move_channel, by the lesson's pack_move (v8 decisions §18).
Baseline: credit_rules.py decision_channel + day bucket (since 2026-10-28; days 1-3 and 4+, fallback to the
pooled channel under 20 memory-off decisions; TickConfig baseline_by_day). Shrinkage: credit.py (lift *
n/(n+5)); the 5 has no recorded derivation (consolidation_design.md §6a; median follows 3 there).
Rules: store_ops.py (protect lift > 0 and follow >= 2, checked first, recomputed each pass; prune lift < -0.15
and follow >= 8; evict follow == 0, retrieved >= 8, override > 0, override >= not_relevant).
Threshold reasons: consolidation_design.md §6a ("pragmatic, not statistical"). "About 0.3": one standard error
at 8 follows with the memory-off villager vote spread (sd 0.79). Split-half: heldout_credit_reproduction.py
(v6ab, one split by game id, 31 lessons with >= 3 follows per half; Pearson +0.54; the lone flip -0.50 ->
+0.04 at 3/5 follows; 4 of the 9 flagged lessons score identically in both halves because every follow got
the same grade against a shared baseline, so "8 of 9 stayed negative" is not used).
Repair: tick.py run_credit_pass logs every change (credit_runs); source observations stay.
July abstention: credit/report.md §6 (quote; 19 follows; 0.00; +0.20 all-day vigilante/day_vote base, n 90);
same-day rows from credit_day_matched_check.py (loop-run corpus v7_compound_town5 gen1-4; follow days 15 x day 2,
4 x day 3; base as run +0.10, corrected -0.31; lesson corrected -0.79). Three controls kept: blindspot_fix
step 1 (all-day base). Corrected loop unplayed: v7/report.md.
Replay: credit/blindspot_fix/experiment_log.md ④b (100 endpoint-ON town cases, store arms; full store +0.04,
fixed-pruned +0.14 mean value; McNemar p 0.5-1.0). The first replay (④) on a previous epoch's games saw
nothing: frozen turns lacked the discussion the harm ran through.
Credit pass: tick.py (no model call); v8 decisions §14; demo: v8/experiment_log.md (20 games vs 12 memory-off
seed games). Human seats: credit_rules.py _human_seats (§15). Credit is run by hand. -->
