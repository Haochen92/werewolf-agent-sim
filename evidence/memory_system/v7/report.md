# v7: did a memory that rewrites its own lessons make the town play better?

This is the record of the v7 memory experiment (June and July 2026, the nine-seat game). It covers
the learning loop as it ran then, how the question was measured so the answer could be trusted, and
what the signed test found. The journey in date order is in two logs: the June loop runs in
[`experiment_log.md`](experiment_log.md), and the July plan, build and test in
[`execution_plan/experiment_log.md`](execution_plan/experiment_log.md). What runs today is in
[What followed](#what-followed-and-what-runs-today); this page does not describe today's code
except where it says so, with a date.

## In short

- **Question.** A learning loop played games in rounds, graded every lesson by the decisions that
  followed it, removed the bad ones and wrote new ones. Did the finished memory make the town decide
  better than no memory at all?
- **Test.** Four learning rounds (40 games with memory, 40 without, $25.74), then 30 deals each played
  twice, with the finished memory and without (60 games). The measure, the size and how a negative
  would be read were signed before any game was played (2026-07-16); one change was made after the
  learning games and before any test game.
- **Answer.** The town's decision score was 0.147 lower with memory, and lower on 19 of the 30 deals
  (p ≈ 0.06, not significant). As committed in advance, this was reported as "no compounding
  detected", with the estimate leaning toward harm. Every game ran with players that produced no
  reasoning before answering.
- **What followed.** The owner closed the memory research on 2026-07-21 without a further run. Closed
  is not disproved. The loop's grading and lesson-writing later became the memory system's
  consolidation code; in served games today memory is the player's switch and starts off.

## Scope

**The players did not reason.** Every game behind this report played its turns on
`gemini-3.1-flash-lite` at thinking level "minimal", a 128-token budget on Vertex. A probe on
2026-10-04 found that this model, asked for the game's structured output at that budget, reasons for 0
tokens. The run fingerprints confirm "minimal" on all 222 game records of the June loop runs and all 60
of the July test. Both sides of every comparison ran the same way, so each comparison is fair. Every
result here, positive or negative, is a result for a player that answers without a reasoning step;
none of them says what memory does for one that reasons. Detail and the run-by-run table:
[`../../credit/blindspot_fix/experiment_log.md`](../../credit/blindspot_fix/experiment_log.md) §⑦.

**Dates.** The June loop runs: 2026-06-19 to 06-23. The July plan: 07-04. The power simulation: 07-05.
Pre-registration signed: 07-16. Learning rounds: 07-17 to 07-19. Test games: 07-20. Closure: 07-21.

## The question

**The memory.** The agents keep two kinds of written memory from past games. An *observation* is a
fact about a past game, recorded afterwards by a model that can see every hidden role. A *strategy
point* (here, a *lesson*) is an instruction of the form "if this situation, then this action"; one the
June loop kept told an investigator holding a definite result late in the game to reveal it and force
the vote. Before each decision a player retrieves a few lessons for its role and the moment of the
game, and reports which it followed.

**The loop, as it ran in 2026.** The loop plays games in batches called *generations*. After each one
it does three things:

1. **Credit.** Every decision a player made while following a lesson is graded good, neutral or bad
   against the hidden roles (the score below). A lesson's *lift* is the average grade of the
   decisions that followed it minus the average grade of the same kind of decision in games without
   memory. Grading against the roles rather than the game's result is called *de-lucked*: a lucky
   win does not make a bad move look good.
2. **Synthesise.** A model writes new lessons from the observations gathered so far and from the
   existing lessons' track records.
3. **Prune.** Lessons whose lift falls below −0.15 after at least 8 follows are removed (the July
   settings), and lessons retrieved often but never followed can be evicted. Old observations
   decay out after several generations.

**The hope** was that this makes the memory better generation after generation: lessons that lead to
good decisions survive and bad ones are dropped. The project called this *compounding*. Having
memory at all was a different question, tested separately (below).

**The June static test, for contrast.** A fixed memory, with no loop, was tested on 30 paired deals in
June. It improved selected town decision measures: the healer saved the real target 37% → 60% (p =
0.005), and town eliminations hit an enemy 47% → 64% (p = 0.028). The town win rate went from 27% to
43%, not significant (p = 0.27). Wolves and the lone killer gained nothing. That test, its arms and
its limits are told in [`../effectiveness/report.md`](../effectiveness/report.md).

## The score

**One number per game for how well the town decided.** Every decision a town player made after day 1
(day votes and night actions) is graded against the hidden roles revealed at the end: +1 good (for
example, voting for a wolf), 0 neutral, −1 bad (for example, voting out a villager). Day 1 is skipped
because memory cannot have made a difference yet. The grades are averaged, so the score runs from −1
(every decision bad) to +1 (every decision good).

**A worked example.** A game with 12 graded town decisions, 7 good, 2 neutral and 3 bad, scores
(7 − 3) ÷ 12 = +0.33. The score ignores who won.

**Games wobble.** The same setup gives very different scores from game to game, because each game is a
different deal: who the wolves are, who holds which power role, how the talk goes. These are the 15
memory-off games from the first town-only loop run:

> −0.15, −0.10, −0.04, +0.08, +0.13, +0.17, +0.27, +0.35, +0.35, +0.46, +0.46, +0.53, +0.68, +0.88, +0.93

They average +0.33, but a single game can land anywhere from below zero to near +1, with no memory and
nothing learning. A typical game sits about 0.33 away from the average. This spread, not a lack of
labels or judges, was the obstacle.

## Testing the test before paying for it

**The question: could the planned test see a realistic improvement at an affordable size?** No. At the
size of the previous paid run it would have noticed one about 1 time in 9.

**The planned test.** Average the score for each generation, draw the best straight line through the
averages, and check whether it slopes upward by more than chance would explain. The June runs had been
read this way. Each generation gives only one average from a handful of games that wobble this much,
so before paying for another run the plan (2026-07-04) checked, for free, whether this test could see
a realistic improvement.

**The simulation.** Build pretend runs in which the right answer is known, then check whether the
planned test finds it. Each pretend run took four steps:

1. **Start from games where nothing improves:** the 15 memory-off scores above.
2. **Build a pretend run from them.** For 4 games per generation over 6 generations (the size of the
   previous paid run), draw 4 scores at random for each generation, putting each back after drawing it.
   Nothing in this pretend run improves.
3. **Plant an improvement:** add a known amount to every score, growing each generation, so the run ends
   +0.15 higher than it started:

   | Generation | 1 | 2 | 3 | 4 | 5 | 6 |
   |---|---|---|---|---|---|---|
   | Added to each game's score | +0.00 | +0.03 | +0.06 | +0.09 | +0.12 | +0.15 |

4. **Run the planned test** on the 24 scores: does the line slope upward by more than chance would
   explain? The usual bar is that, with no real improvement, a slope that steep would appear less than
   5% of the time.

This was repeated 2,000 times with fresh draws. The *hit rate* is the share of repeats in which the test
reported the planted improvement; statisticians call it *power*, and the usual target is 80%. Other run
sizes were simulated the same way. No model was called, so it cost nothing.

**Why +0.15.** It is the middle of the plan's own estimate of a realistic improvement (+0.1 to +0.2).
That estimate came from the largest memory effect ever measured on this score, about +0.2, from an
earlier experiment with a fixed memory on older prompts. A learning memory was not expected to beat
that by much, and the score had little room above the town's +0.33. The simulation also planted +0.05,
+0.10, +0.20 and +0.30, and +0.00 to check for false alarms.

**The result: the test mostly missed it.**

| Run size | Cost | How often the test noticed the planted +0.15 |
|---|---|---|
| 24 games (the size of the previous run) | $7 | about 1 time in 9 (11%) |
| 200 games (the largest size tried) | $56 | about half the time (56%) |

At the size the project could afford, a real improvement would come back as "no effect" nearly 9 times
out of 10. The test was not broken: a planted +0.60 was caught 85% of the time even at 24 games. It
failed at the size of effect the project expected to find.

**How sure we are.**

- **It agrees with a formula.** A standard textbook formula for the same test, computed separately, gave
  almost the same hit rates.
- **It does not cry wolf.** With nothing planted, the test raised a false alarm only 2–3% of the time.
- **It corrected one assumption.** The plan expected a game's score to swing by about ±0.9, which is how
  much one graded decision swings. A game averages several decisions, so it swings about three times
  less (0.33 in the main set, 0.32 and 0.27 in two other sets checked). The test still missed.
- **Its main limit flatters the test.** The simulation treats each generation as separate, while in a
  real run every generation shares the same growing memory. That probably makes the test look better
  than it is, so the real miss rate is likely worse.

## The redesign: compare the same deals, finished memory against none

**The trend test was dropped on 2026-07-05, before any paid run used it.** The compounding question was
recorded as open, not answered.

**Why not just play more games?** Even 200 games missed the improvement half the time. A long run also
risks the hosted model changing partway through, which would spoil any comparison across generations.

**The replacement.** Let the loop learn for several generations without measuring anything. Then play a
set of *boards* twice, once with the final memory and once without. A board is one fixed deal of roles
and random seed, so both copies start with the same luck, and the difference between them comes from
the memory. A finished memory carries its whole effect into every game at once, which is easier to see
than a slow rise spread thin across generations.

**The tradeoff.** This design says whether the final memory makes a difference, not when or how fast it
got there. The two copies of a board stop matching once memory changes a single move, so pairing
removes the luck of the deal, not everything after it. The new design's power was never simulated; it
rested on the reasoning above.

A standing rule came out of this: no paid compounding run without first simulating whether its test can
detect the effect it is looking for.

## The pre-registration

**The owner signed it on 2026-07-16, before any game of the run was played.** It fixed in writing:

- **What is compared:** the same boards played with memory and without. Only the town received the
  loop's lessons. A short list of *tells* (public behaviours that hint at a hidden role) was shown to
  every seat in the memory games, wolves included, since it describes public behaviour. A check stops
  the run if the memory setting that actually runs differs from the declared one, the slip that had
  spoiled a June run (below).
- **One main measure:** the town's decision score, compared board by board. Other measures were listed
  in advance as secondary, never to be promoted to the main result.
- **Size and budget:** 4 learning generations of 10 games with memory and 10 without, then 60 test
  games, estimated at $77–98 within a $150 reserve.
- **No stopping on results:** a fixed number of games; the run could halt only on an automatic validity
  check. Partial generations from crashed attempts were set aside, not pooled.
- **How a bad result would be read:** a null or negative result is reported as "no compounding
  detected", not rerun with a different measure. No prompt edits during the run.

This is why the outcome counts as a result. The measure, the size and the reading of a negative were
fixed before any data existed, so there was no room to pick a friendlier measure afterwards.

**One change after signing, before any test game.** The signed design had three conditions on 20 boards
each, with the main comparison between the final memory and the memory after the first generation. On
2026-07-20, after the learning games but before any test game, the owner changed it to two conditions
on 30 boards: final memory against no memory. The recorded reasons: the first-generation memory held no
lessons yet, so that comparison would have needed a stand-in, and the freed games made the main
comparison more precise (about 22% smaller standard error). The change was written into a file beside
the data ([`PREREG_AMENDMENT.md`](execution_plan/data/v7_endpoint_ab/PREREG_AMENDMENT.md)). It changes
the question: the test asks whether the finished memory beats no memory, not whether it improved from
one generation to the next.

## What the signed run found

**Did the finished memory make the town decide better than no memory? No improvement was detected;
the estimate leaned toward harm.**

The four learning generations finished on 2026-07-19 at a cost of $25.74, leaving a memory of 168
lessons. The test ran on 2026-07-20: 30 boards, each played once with that memory and once without (60
games).

- **Main measure.** The town's decision score was 0.147 lower with memory than without, compared board
  by board (p ≈ 0.06: a gap this size would appear about 6% of the time by chance). Memory did worse on
  19 of the 30 boards. As committed, this was reported as "no compounding detected", with the estimate
  leaning toward harm.
- **A secondary measure was clearer.** In the same games, town players with memory voted for a real
  threat about 15 percentage points less often (the rate without memory was near 50%) and abstained
  more (31% of votes against about 23%). Counted vote by vote this gave p < .001, but votes within one
  game are not independent, so that overstates its certainty, and it was not the main measure.

**The explanation the record offers: the grading could not see the harm.** Cautious lessons told the
investigator and healer to keep what they knew to themselves and told town players to abstain when
unsure. The loop's grading scored every town abstain as neutral, and a lesson with no memory-off
comparison was compared with zero, so a lesson telling the vigilante to abstain scored exactly 0.00 and
was never pruned. That case, with its numbers and the fix, is told once in
[the credit report](../../credit/report.md) §6.

**How sure we are.**

- **It rests on** 30 deals, each played both ways, under a design fixed in advance.
- **It is not significant.** "No compounding detected" is the committed reading. The run did not show
  that memory hurts, and it did not show that a self-improving memory cannot help.
- **What the memory arm included.** Besides the town's lessons, the memory games showed a short list
  of tells to every seat, wolves included, and the games without memory did not. The amendment names
  the treatment as the matured store "SPs + tells" against no memory, so the test measures the two
  together; the tells' own effect was never separated.
- **What it does not cover.** Players that reason before answering; a longer run (counter-lessons
  against caution had begun to appear but were outnumbered when the run ended); the loop with its
  grading fixed, which was never played.
- **What the comparison changed.** After the amendment the test compares the finished memory with no
  memory. It cannot say whether the memory improved from one generation to the next.

## The June loop runs: the history that forced the method

**Why the July test was built the way it was.** Two June runs of the loop were both invalid, each for a
different reason, and neither reason threw an error. The July design closes both, and adds the power
check, because in June the run size had been chosen by budget rather than by what the test could
detect.

**The first run (2026-06-21): a distorted baseline.** A lesson's lift compares its decisions with the
same kind of decision in games without memory, so that comparison has to be sound. In the first run it
was not. At first it came from the few memory-off decisions inside the memory games (thin, and biased
toward early boards where retrieval was skipped). Later it came from a separate memory-off arm, but one
played on different deals, so each kind of decision was averaged over different situations. Either way
the lift was wrong, and lift drives both the new lessons and the pruning, so the run's lessons and its
slope could not be trusted. The run also caught a bug that had silently zeroed all credit from the
second generation on; it was fixed mid-run, and the loop gained checks that stop a run when an input
comes back empty instead of letting it produce a plausible wrong number. The completed ten-generation
run cost $65.21; the record puts the first run's attempts at about $100 together. The town's gap
(memory minus no memory) swung around zero: a mean of −0.101 over 10 generations, standard deviation
0.156, 5 games per generation.

**The fix.** Memory-off games on the same boards: each memory game is paired with a memory-off game on
the same deal (the same role draw and scheduler seed), and the memory-off average comes from that arm.

**The second run (2026-06-22): the wrong experiment.** The rerun started from an empty memory, paired its
arms and was meant to give memory to the town only. It ran 4 games per arm per generation and stopped
after 6 of 13 planned generations, under a stopping rule set before the run (a flat trend meant stop,
not more games). It cost $15.00. Its first reading took wolves and the lone killer, assumed to have no memory, as
a control for the noise. An audit of the raw records on 06-23 found that every faction had memory: the
driver defaulted to "all factions" and the town-only setting was never passed. So:

- **There was no control.** Wolves and the killer were receiving memory too; their swings were their
  own memory effect plus noise.
- **The town result is confounded.** A town vote scores well only if it lands on a real enemy. Wolves
  improved by memory hide better, which lowers the town's score whatever the town's own skill. The town
  with memory faced memory-using wolves; the town without faced plain ones.

**The guard that came out of it.** The loop now reads which factions actually had memory in the first
generation's games and crashes unless that matches a declared intent, recording the arm in the run's
history. By the July run, a run also refused to start unless an intent was declared or the check was
waived on purpose (`evaluation/src/loop/driver.py::run_loop`, `evaluation/src/loop/invariants.py::assert_arm_factions`).
The July run declared "town only", and the test's log confirms the arm (healer, investigator,
vigilante, villager) before reporting.

**A by-product, tentative.** Read as what it actually was, a test of every faction with memory on paired
boards, the second run showed one rising pattern (memory minus no memory, generations 2–6, vote and night
decisions; `runs/v2_full/v2_salvage.py`):

| Faction | Average gap | Trend per generation |
|---|---|---|
| Wolves | +0.077 (rising to +0.28 by generation 6) | +0.086 |
| Town | −0.189 | −0.027 |
| Lone killer | −0.142 | +0.027 |

The wolves' gap rose across generations: −0.14, −0.05, −0.11, +0.17, +0.10, +0.28. This is 4 games per
generation with swings of ±0.2–0.3, from a run invalid for its own question, so it is a direction worth
noting, not an effect. It is not part of any verdict. The town row is not a verdict on town memory,
because of the confound above.

## What followed and what runs today

**The closure (2026-07-21).** The owner declined a further run (about $25) and closed the memory
research: no memory version was promoted, and live play shipped with memory off. The verdict across the
memory experiments, in the wording the owner ruled (2026-10-26):

> The June static-memory A/B reported improvements on selected town decision measures. A later A/B on a
> different store, run against a higher no-memory baseline, found no town effect; it was not a
> replication of the June test. Separately, the pre-registered v7 endpoint detected no compounding
> benefit.

The investigation is closed; the hypothesis was not disproved.

**The grading was fixed after the run, and the fix was never played.** A town abstain on a day that
ended with nobody voted out is now graded bad, and a lesson with no memory-off comparison is left
unscored. Re-scoring the recorded games pruned the abstain lesson and kept three lessons chosen in
advance as good ([credit report](../../credit/report.md) §6;
[`../../credit/blindspot_fix/experiment_log.md`](../../credit/blindspot_fix/experiment_log.md)).

**The loop graduated into the memory system's consolidation code** (`Agents/memory/consolidation/`,
ported to the ten-seat game on 2026-10-13). Checked against the code on 2026-10-26, it runs in two
parts:

- **The credit pass** (`tick.py::run_credit_pass`, no model call) grades every stored lesson from the
  memory-on games in a window, with the fixed abstain rule built in, then prunes and evicts.
- **The learning tick** (`tick.py::run_tick`, paid) folds in new observations from the offline
  extraction job, writes new lessons and drops duplicate lessons (keep or discard, never rewritten). It
  never prunes or evicts. Both passes are run by hand; no schedule is in the repository.

**In served games today** (checked 2026-10-26), memory is the player's switch and starts off
(`frontend/src/app/(site)/_components/ticket/TicketOffice.tsx`); whether a deployment offers it at all
is a setting (`server/config.py`, `WW_MEMORY_ENABLED`). With it on, every AI seat retrieves strategy
points only, never observations (`server/game/run_config.py::game_run_config`). Lessons are extracted
offline after a game, never during it, and a served game is never mined into the live store. The
ten-seat memory has not been tested against no memory; see [`../v8/`](../v8/).

**One June gap, and what became of it.** In the second June run, the counts of how often each lesson
was retrieved, overridden or judged not relevant were written in each game's own copy of the memory but
never carried back into the loop's memory. Eviction needs those counts, so it never fired in any June
generation (pruning by lift still worked). On 2026-07-15, before the July run, the credit step began
recounting them from the game records. In the July run eviction then had candidates but removed none:
6 and 7 never-followed lessons in the last two generations were kept. The rule evicts only a lesson
players applied and overrode; one they mostly judged not relevant points at retrieval rather than the
advice, and is spared. Today the credit pass recounts them
the same way (`Agents/memory/consolidation/credit.py::credit_apply`), and the first ten-seat credit pass
evicted 4 lessons ([`../v8/experiment_log.md`](../v8/experiment_log.md)).

## Lessons

- **Test the test before paying for it.** A score can measure the right thing and still be too noisy to
  notice a realistic change at the number of games you can afford. Here the planned test would have
  noticed a realistic improvement about 1 time in 9.
- **When an effect builds slowly, compare the finished state with none on the same deals** instead of
  looking for a trend across rounds.
- **Make the experiment's identity a checked fact, not a launch-time intent.** Both June runs ran a
  different experiment from the one intended, and neither raised an error. Reading what actually ran
  and comparing it with a declared intent turns that failure into a crash in the first generation.
- **Check that a control received no treatment before leaning on it.** The June "no-memory control"
  was assumed from the plan, not read from the records, and the records said otherwise.

## Provenance

| What | Where |
|---|---|
| Power simulation | `evaluation/src/instrument_validation/power/mde_simulation.py`, seed 20260618, 2,000 repetitions per setting; its readout and the July planning documents are in git history at `24dfd3a7` (`evidence/execution_plan/power_analysis/mde_table.md`, 2026-07-05) |
| Pre-registration | signed at `6ae7865`; amendment in [`execution_plan/data/v7_endpoint_ab/PREREG_AMENDMENT.md`](execution_plan/data/v7_endpoint_ab/PREREG_AMENDMENT.md) |
| July learning run (4 generations) | [`execution_plan/data/v7_compound_town5/`](execution_plan/data/v7_compound_town5/): `config.json`, `loop_history.json`, `cost_report.json`, `run_meta.json` |
| July test (30 boards × 2) | [`execution_plan/data/v7_endpoint_ab/`](execution_plan/data/v7_endpoint_ab/): `config.json`, `endpoint_result.json`, `run_meta.json`, the run log; both July runs at commit `a010dc6` |
| June runs | [`runs/`](runs/): `town_only_run1/`, `town_only_run2/` (the first run and its restart), `v2_full/` (the second run, with `run.log` showing the arm that ran, `cost_report.json`, and `v2_salvage.py`); the loop run on `bdfe1fa..52e26b1` |
| Loop design as built in June | [`consolidation_design.md`](consolidation_design.md) |
| Replay screen used afterwards | console entry `eval-checkpoint-replay` |

The per-game records of the July runs (190 MB and 123 MB) were not copied into `execution_plan/data/`;
the [data README](execution_plan/data/README.md) lists what was. The committed `endpoint_result.json`
holds pooled per-decision scores (town 0.039 with memory over 458 decisions, 0.247 without over 438).
The board-paired figures above (−0.147, 19 of 30, p ≈ 0.06) are as recorded in the July log
([`credit/blindspot_fix/experiment_log.md`](../../credit/blindspot_fix/experiment_log.md) §①); no committed
file or script reproduces them, and the record does not name the test behind p ≈ 0.06.
