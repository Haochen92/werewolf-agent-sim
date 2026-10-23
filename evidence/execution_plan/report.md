# Measuring whether memory compounds: the power analysis and the pre-registration

> **What this is.** A decision record from July 2026. It explains why the planned way of measuring
> "does memory compound across games" was retired before any money was spent on it, what replaced
> it, and how the replacement was fixed in a signed pre-registration before data existed. The last
> section reports what that signed run found.
>
> **Companion docs.** The same story in date order: [`experiment_log.md`](experiment_log.md). This
> report condenses the five planning documents in this folder, removed on 2026-10-22 and kept in git history at commit `24dfd3a7`:
> `compounding_measurement_plan.md`, `power_analysis/` (`decision_rationale.md`, `mde_table.md`),
> `v7_run_preregistration_DRAFT.md` (signed, despite its file name), `phase_b_plan_review.md` and
> `v6_wide_migration_roadmap.md`. What happened after the run is in
> [`../credit/blindspot_fix/experiment_log.md`](../credit/blindspot_fix/experiment_log.md) §①, §⑥
> and §⑦; the earlier loop runs are in [`../v7_final/`](../v7_final/).

---

## 1. The question

The agents keep a memory of written lessons from past games. A learning loop plays games in batches, called *generations*. After each generation it scores every lesson by how the decisions that followed it turned out, removes the lessons that did badly, and writes new ones. The question was whether this makes the memory better generation after generation. The project called this *compounding*.

**The score.** Each game gets one number for how well the town decided. Every decision a town player made after day 1 (day votes and night actions) is graded against the hidden roles revealed at the end: +1 good (for example, voting for a wolf), 0 neutral, −1 bad (for example, voting out a villager). Day 1 is skipped because memory cannot have made a difference yet. The grades are averaged, so the score runs from −1 (every decision bad) to +1 (every decision good). A game with 12 graded decisions, 7 good, 2 neutral and 3 bad, scores (7 − 3) ÷ 12 = +0.33. The score ignores who won, so a lucky win does not count as good play.

**Games wobble.** The same setup gives very different scores from game to game, because each game is a different deal: who the wolves are, who holds which power role, how the talk goes. These are the 15 memory-off games from the first town-only run of the loop:

> −0.15, −0.10, −0.04, +0.08, +0.13, +0.17, +0.27, +0.35, +0.35, +0.46, +0.46, +0.53, +0.68, +0.88, +0.93

They average +0.33, but a single game can land anywhere from below zero to near +1, with no memory and nothing learning. A typical game sits about 0.33 away from the average. This spread, not any lack of labels or judges, was the obstacle.

**The planned test.** Average that score for each generation, draw the best straight line through the averages, and check whether it slopes upward by more than chance would explain. The worry was that each generation gives only one average from a handful of games that wobble this much. So before paying for another run, the plan was to check, for free, whether this test could even see a realistic improvement.

## 2. What the simulation showed

**The idea: test the test before paying for it.** Build pretend runs in which the right answer is known, then check whether the planned test finds it. Each pretend run took four steps:

1. **Start from games where nothing improves:** the 15 memory-off scores above.
2. **Build a pretend run from them.** For a run of 4 games per generation over 6 generations (the size of the previous paid run), draw 4 scores at random for each generation, putting each back after drawing it, so a score can be drawn again. Nothing in this pretend run improves.
3. **Plant an improvement: add a known amount to every score,** growing a little each generation, so the run ends +0.15 higher than it started:

   | Generation | 1 | 2 | 3 | 4 | 5 | 6 |
   |---|---|---|---|---|---|---|
   | Added to each game's score | +0.00 | +0.03 | +0.06 | +0.09 | +0.12 | +0.15 |

4. **Run the planned test.** Fit the best straight line through the 24 scores and ask whether it slopes upward by more than chance would explain. The usual bar for "more than chance": with no real improvement, a slope that steep would appear less than 5% of the time.

The whole thing was repeated 2,000 times with fresh random draws, and the *hit rate* is the share of repeats in which the test reported the planted improvement. Statisticians call this hit rate *power*, and the usual target is 80%. Other run sizes were simulated the same way. No model was called, so it cost nothing.

**Why +0.15.** It is the middle of the plan's own estimate of a realistic improvement (+0.1 to +0.2). That estimate came from the largest memory effect ever measured on this score, about +0.2, from an earlier experiment with a fixed memory on older prompts. A learning memory was not expected to beat that by much, and the score had little room above the town's +0.33 anyway. The simulation also planted +0.05, +0.10, +0.20 and +0.30, and +0.00 to check for false alarms.

**The result: the test mostly missed it.**

| Run size | Cost | How often the test noticed the planted +0.15 |
|---|---|---|
| 24 games (the size of the previous run) | $7 | about 1 time in 9 (11%) |
| 200 games (the largest size tried) | $56 | about half the time (56%) |

At the size the project could afford, a real improvement would come back as "no effect" nearly 9 times out of 10. The test was not broken: a large planted improvement (+0.60) was caught 85% of the time even at 24 games. It failed at exactly the size the project expected to find.

**Why the simulation can be trusted.** A standard textbook formula for the same test, computed separately, gave almost the same hit rates. And when nothing was planted, the test raised a false alarm only 2–3% of the time, as it should.

**One assumption it corrected.** The plan expected each game's score to swing by about ±0.9, which is how much a single graded decision swings. A game's score averages several decisions, so it swings about three times less (0.33 in the main set of games, 0.32 and 0.27 in two other sets checked for comparison). The test still missed, even with that better news.

**Its main limit.** The simulation treats each generation as separate, while in a real run every generation shares the same growing memory. That probably makes the test look better than it is, so the real miss rate is likely worse, not better.

## 3. The call: drop the trend, compare the same boards instead

The trend test was dropped on 2026-07-05, before any paid run used it. The compounding question was left open, not answered.

**Why not just play more games?** Even 200 games missed the improvement half the time. A long run also risks the hosted model changing partway through, which would spoil any comparison across generations.

**The replacement.** Let the loop learn for several generations without measuring anything. Then play a set of boards twice, once with the final memory and once without. A *board* is one fixed deal of roles and random seed, so both copies start with the same luck, and the difference between them comes from the memory. A finished memory carries its whole effect into every game at once, which is easier to see than a slow rise spread thin across early generations.

**The tradeoff.** This design says whether the final memory makes a difference, not when or how fast it got there. The two copies of a board stop matching once memory changes a single move, so pairing removes the luck of the deal, not everything after it. The new design's ability to detect the effect was never simulated; it rested on the reasoning above.

A standing rule came out of this: no paid compounding run without first simulating whether its test can detect the effect it is looking for.

## 4. The pre-registration

The project owner signed the pre-registration on 2026-07-16, before any game of the run was played. It fixed in writing:

- **What is compared:** the same boards played with memory and without. Only the town received the loop's lessons. A short list of *tells* (public behaviours that hint at a hidden role) was shown to every seat in the memory games, wolves included, since it describes public behaviour. A check stops the run if the memory setting that actually runs differs from the declared one, the slip that had spoiled an earlier run.
- **One main measure:** the town's decision score, compared board by board. Other measures were listed in advance as secondary, never to be promoted to the main result.
- **Size and budget:** 4 learning generations of 10 games with memory and 10 without, then 60 test games, estimated at $77–98.
- **No stopping on results:** a fixed number of games; the run could halt only on an automatic validity check.
- **How a bad result would be read:** a null or negative result is reported as "no compounding detected", not rerun with a different measure. No prompt edits during the run.

This is why the outcome in §5 counts as a result. The measure, the size and the reading of a negative were fixed before any data existed, so there was no room to pick a friendlier measure afterwards.

**One change after signing, before any test game.** The signed design had three conditions on 20 boards each, with the main comparison between the final memory and the memory after the first generation. On 2026-07-20, after the learning games but before any test game, the owner changed it to two conditions on 30 boards: final memory against no memory. The recorded reasons: the first-generation memory held no lessons yet, so that comparison would have needed a stand-in, and the extra boards made the main comparison more precise. The change was written into a file beside the data. It does change the question: the test now asks whether the finished memory beats no memory, not whether it improved from one generation to the next.

## 5. What the run found

The four learning generations finished on 2026-07-19 at a cost of $25.74, leaving a memory of 168 lessons. The test ran on 2026-07-20: 30 boards, each played once with that memory and once without (60 games).

**The main result leans toward harm but is not significant.** The town's decision score was 0.147 lower with memory than without (p ≈ 0.06: a gap this size would appear about 6% of the time by chance). Memory did worse on 19 of the 30 boards. As committed, this was reported as "no compounding detected", with the estimate leaning toward harm.

**A secondary measure was clearer.** In the same games, town players with memory voted for a real threat about 15 percentage points less often (the rate without memory was near 50%) and abstained more (31% against about 23%). This measure counts votes one by one, which overstates its certainty somewhat, and it was not the main measure. The likely cause: cautious lessons told the investigator and healer to keep what they knew to themselves and told town players to abstain when unsure, and the loop's scoring could not penalise abstaining. That failure is the case study in [the credit report](../credit/report.md) §6.

On 2026-07-21 the owner closed the memory research without a further run. No memory version was shown to help, no memory was promoted, and every live game starts with memory off (a player can switch it on).

**A caveat found later (2026-10-04).** At the model setting the test games used, the players produced zero reasoning tokens: they answered without a reasoning step. Both sides ran the same way, so the comparison is fair, but the result is about players that do not reason first.

## 6. Lessons

- **Test the test before paying for it.** A score can measure the right thing and still be too noisy to notice a realistic change at the number of games you can afford. Here it noticed a realistic improvement about 1 time in 9.
- **When an effect builds up slowly, compare the finished state against none on the same boards** instead of looking for a trend across generations.

---

**Provenance.** Simulation: `evaluation/src/instrument_validation/power/mde_simulation.py`, seed
20260618, 2,000 repetitions per setting, readout `power_analysis/mde_table.md` (2026-07-05).
Pre-registration signed at `6ae7865`; the build run and the endpoint both ran at `a010dc6`.
Build run: `batch_results/v7_compound_town5/` (`loop_history.json`, `cost_report.json`). Endpoint and
amendment: `batch_results/v7_endpoint_ab/` (`PREREG_AMENDMENT.md`, `endpoint_result.json`).
Checkpoint replay console entry: `eval-checkpoint-replay`.
