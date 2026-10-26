# Extraction selection and the outcome halo: journey log (June to October 2026)

> **What this is.** The chronological path from "does extraction pick the moves that mattered?" to
> today's design: a verdict checked by a second model and a rule-based grade stored beside it. Later
> entries supersede earlier ones. Where a reading or a design changed, the change is shown in its place
> rather than edited away.
>
> **Companion docs.** The current design, stated destination-first, is in
> [`report.md`](report.md), which also defines the terms used here (observation, verdict,
> cell, de-halo, grade). This log condenses the folder's earlier `experiment_log.md` (2026-06-17) and
> the halo thread of [`outcome_halo_case_study.md`](outcome_halo_case_study.md) (2026-07-26),
> [`memory_system/v7/extraction_coverage_ab_spec.md`](../../memory_system/v7/extraction_coverage_ab_spec.md)
> (2026-06-19), and the v8 [log](../../memory_system/v8/experiment_log.md) and
> [decisions](../../memory_system/v8/decisions.md) §13 (October 2026). The earlier log is in git history at `2382b34c`.

---

## ① Motivation: the store learns from a model's hindsight

**2026-06-17 · the question.** An idea to "mine the high-leverage turns" assumed extraction already
looked for the turns that mattered. Before building anything to steer it, the prompt was read to see
what extraction actually did. At the time (nine-seat game) it was one pass over the whole game, with
every role, every private action and the outcome in view. It asked for "patterns, mistakes, and
pivotal moments", judged each move's effect "from the END of the game", and gave each a one-word
verdict. It asked for a fixed 4 to 8 observations per role.

The design was defensible. Only after the game can a model see the multi-day chains of cause and
effect a lesson needs, and the outcome is the one fact every move is ultimately judged by. The open
questions were whether the model's hindsight judgment of each move was reliable, and whether a fixed
count padded quiet games and cut rich ones short.

## ② The first check and the first proposal (2026-06-17)

**Test: does the verdict follow the result?** *Catches:* the risk that verdicts were noise. The
932 observations in the store of the time were split by whether the player's side won (no model
call). Winners' verdicts were 64% positive and 25% negative; losers' 21% positive and 65% negative.
Only 3% were unclear. The split held for every role.

*Reading at the time.* The verdict was not noise: the model used the outcome it was given. So the
outcome labels were called trustworthy. But the cleanness looked like a halo: the verdict seemed to
answer "did your side win?" and stamp it on every move, not "did this move matter?". Nothing in the
store graded single decisions by rule, so the test could not say which.

**Proposal.** Hand the existing whole-game pass a deterministic list of the turns the game's own
arithmetic marked as decisive, and replace the fixed count with a budget drawn from it. Do not cut
extraction into turn-by-turn calls, which would lose the multi-day chains. Use the objective signal
to steer which moves get attention, never what the lesson says. Gated: the extraction prompt fed
labels other studies depended on, so a change had to be a deliberate, versioned experiment.

## ③ Verify → decide

**2026-06-19 · the selection test.** *Catches:* the risk that a cheaper extraction model misses the
decisive turns, and that the list would fix it. Three games, 12 flagged turns, Gemini 2.5 Pro and
Gemini Flash-Lite with and without the list, plus a "be exhaustive" variant
(`memory_system/v7/extraction_coverage_ab_spec.md`).

- By the automatic count, Pro covered 12 of 12 flagged turns and Flash-Lite 3 of 12, with the list or
  without it. The exhaustive variant also stayed at 3.
- A manual read showed the count was wrong. It matched only observations that stated how many players
  were alive, which Flash-Lite's terse text often left out. On the most-flagged cell, Flash-Lite
  captured the same night-kill sequence as Pro.
- A separate model comparison, also on three games, found Gemini 3.5 Flash close to Pro in volume
  and distinctness.

*Decision:* neither the list nor the exhaustive instruction was scaled. Extraction quality was judged
comparable across models on this slice, so the binding problem was placed in synthesis, which weights
lessons by verdicts, not in extraction's selection. Three games show the direction only. The
lesson about the metric was kept: read the observations, do not trust a text-matching count of them.

**2026-07-26 · the case study.** *Catches:* the risk that the halo is only a correlation, with
verdicts that are right on average. In a game where the project owner played the Serial Killer, two
of the owner's night kills could be checked against known intent
([`outcome_halo_case_study.md`](outcome_halo_case_study.md)). The model charged the wolves'
simultaneous kill to the owner's first night, and called the second night's correct wolf kill a
"fatal error" on a story the day record does not support. The two forms were named: credit across
sides, and working back from the loss.

*Decision at the time:* no pipeline change, because memory research had closed on 2026-07-21 and the
live game shipped memory off. The case named the test that would settle the question: compare the
model's verdicts with rule-based grades on agent-only games. That needed a grader for every decision,
which did not exist yet.

The June reading that the outcome labels were trustworthy did not survive this case: a verdict that
grades the result can be wrong about the move.

**2026-10-11 · the ten-seat test game.** *Catches:* the risk that the halo carried over to the new
game and its new extraction prompts. One test game, its 43 observations read in full against the
engine records. Of the town's
28 verdicts (town won), about 21 were positive and 1 negative; of the evil side's 11 (lost), 7 negative
and 1 positive. Five day-2 abstains were credited with another player's later kill.

*Fix 1, a prompt rule.* The extraction prompt gained "outcome is not credit" and the evidence rule
(a move that merely came before a good or bad night is unclear). By one reading of the same game the
halo about halved, from about 20% of verdicts to about 10%. The same day, in the prompts written for
seeding the ten-seat store, the per-cell prompt dropped its fixed count ("6-12") for "usually a few,
fewer or none when no decision mattered".

*Fix 2, a second-model check.* On the 40 observations of a re-extraction of that game, a reader marked 4 clear halos and 3 verdicts
supported by a mechanical result. Four judges were compared. Claude Haiku 5.5 changed 5 verdicts,
caught all 4 halos and erased none of the 3 supported ones, at $0.006. *Decision (owner):* keep
extraction on Gemini 3.8 Flash with the fixed prompts and add the de-halo pass, configurable and on by
default. This was a deliberate exception to an earlier rule of no extra judge. One game, one reader:
this chose the judge, it did not size its accuracy.

**2026-10-11 · seeding the store, 12 games.** The pass revised 146 of 567 verdicts (26%), mostly negative to
unclear (90) and positive to unclear (35). A read of one game's 19 revisions found most fair and a few
over-corrections (a Fortune Teller's death after it skipped its self-bet, turned to unclear although
that bet gives immunity by rule). The originals were kept in the de-halo records.

**2026-10-12 · 40 games re-extracted offline.** Extraction left the live game and became a batch job
(decisions §11). 19 games ran on Gemini 3.8 Flash and 21 on Claude Sonnet 5.5; de-halo revised 25% and
29% of their verdicts.

**2026-10-13 · the halo measured.** *Catches:* the risk named in July, that the verdict grades the
result and not the decision. The ten-seat grading table for credit had just been built, so the test
cost nothing. 482 night and vote observations of 19 games, each verdict fitted against its role's
average grade in that game and whether its side won (`evaluation/experiments/v8_verdict_halo.py`).

| | Per step of grade | For the side winning |
|---|---|---|
| Verdict as extracted | +0.33 | +0.74 |
| After de-halo | +0.29 | +0.50 |

The verdict followed the side's win about twice as strongly as one step of grade. De-halo removed
about a third of that, and on the losing side only: losers' negatives fell from 53% to 27%, winners'
positives from 57% to 54%. The prompt rule of 2026-10-11 was already in place for these games.

*A gap in the test:* an observation did not say which decision it described, so the grade was the
role's average for the game, not the move's own.

*Rulings (owner):*
- Every observation names the decision it describes, so it can be graded. New extraction asks for
  it; the 40 games already extracted are tagged by a model pass.
- Each observation stores both the verdict and the grade. Which one synthesis reads is a config
  setting. The published store is the verdict variant; a grade variant is synthesized beside it.
- Which writes better lessons is unknown. The fair test randomizes per seat in the same games and
  needs on the order of 1,000 followed lessons per variant. Deferred; the demo run uses the verdict
  variant.

**2026-10-13 · tags checked, the fit repeated per observation.** *Catches:* the risk that the model
tags name the wrong decision. Claude Haiku 5.5 tagged 2,277 observations ($0.08). A blind reader
(Claude Sonnet) named the decision from the record for 102 random observations: 98 agreed, against a
bar of 90% set beforehand. Graded by the table, 1,711 of 2,277 observations received a grade.

The fit was then repeated on 1,472 observations of all 40 games, every phase, each against its own
decision's grade. Same picture: side won +0.80 against +0.40 per step of grade as extracted, +0.53
against +0.36 after de-halo. Vote and discussion verdicts followed the result most (+0.84 each).

*Built the same day:* synthesis can read the grade instead of the verdict, and in that mode it does
not see the extraction model's end-of-game text. A grade-variant store was synthesized ($4.75, not
reviewed). A fair comparison with the published store would first rebuild the verdict variant with
the same code.

## ④ Where it stands (2026-10-22)

- Live in the offline extraction job: the prompt rule, de-halo, and observations naming their
  decision. The grade is computed by a separate script and stored beside the verdict.
- Synthesis reads the verdict by default. The two variants have not been compared.
- The selection list from June is a research option only. Whether ten-seat extraction captures the
  decisive moves has not been measured, only read.
- The served game runs with memory off by default; the ten-seat memory has not been tested at scale.

---

**Sources.** [`experiment_log.md`](experiment_log.md) and [`netverdict_calibration.py`](netverdict_calibration.py)
(2026-06-17) · [`memory_system/v7/extraction_coverage_ab_spec.md`](../../memory_system/v7/extraction_coverage_ab_spec.md)
(2026-06-19) · [`outcome_halo_case_study.md`](outcome_halo_case_study.md) and
`outcome_halo_human_game.json` (2026-07-26) · [v8 log](../../memory_system/v8/experiment_log.md),
entries of 2026-10-11 to 2026-10-13 · [v8 decisions](../../memory_system/v8/decisions.md) §11, §13 ·
`evidence/memory_system/v8/data/halo/` (`summary.json`, `observation_summary.json`) · commits
`de4134b2` and `fba61f9d` (prompt rule, count dropped), `395cfa7f` (de-halo), `e8b974a4` (decision
named).
