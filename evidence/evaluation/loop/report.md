# The v7 learning loop: how it was checked

This page covers every check made on the v7 learning loop (June–July 2026, nine-seat), with as much of the
loop as the checks need for context. Checks that another report already tells are listed here with a link;
the ones with no other home are told in full. Whether memory improved from batch to batch is the design
question, closed in the [execution plan report](../../memory_system/v7/execution_plan/report.md); the scoring design is in
the [credit report](../../credit/report.md); the June–July run records are in [v7_final](../../memory_system/v7/).
How the evaluation reports fit together: [the hub](../report.md).

## What the loop is

The agents keep written lessons (*strategy points*: short IF-situation → THEN-action advice for one role).
The loop played games in batches called *generations*, half with memory on and half with it off. Between
generations it did three things:

- **Credit** scored each lesson by the decisions it was followed at. A fixed rule graded each decision on what
  it did (its target, the target's true role, what came of it), not on whether the side won (*de-lucked*),
  and the grades were compared with memory-off play of the same kind of decision.
- **Prune** removed lessons that kept doing worse than memory-off play.
- **Synthesis** wrote new lessons from fresh accounts of plays in finished games.

The players were `gemini-3.1-flash-lite`, with zero reasoning tokens in every game; the code is
`evaluation/src/loop/`, mapped in its `README.md`.

**How it ended.** The one run under rules fixed in advance finished on 2026-07-19, and its endpoint test
closed negative: on 30 paired boards the town's decision score was 0.147 lower with memory (p ≈ 0.06), lower
on 19 of 30. The memory research closed on 2026-07-21 ([execution plan](../../memory_system/v7/execution_plan/report.md) §5).
The discussion tagger, an LLM judge of each player's day, had been retired from credit on 2026-07-13
([its note](../llm_judge/discussion_tagger.md)).

**What is live today.** The batch harness stayed in `evaluation/src/loop/`, but credit, prune and synthesis
graduated into the deployed memory tick (`Agents/memory/consolidation/`, `tick.py::run_tick`, after each
memory-on game; prune at −0.15 with at least 8 follows). The credit that runs today is the ten-seat port, so
the nine-seat checks below do not validate it; its own checks are in the [credit report](../../credit/report.md)
§5 and [deterministic_audits](../deterministic_audits/experiment_log.md) §5. The ten-seat memory has no
loop and has not been tested at scale.

## Every check on the loop

| Check | Question | Result | Trust | Where it is told |
|---|---|---|---|---|
| **Batch score** (`loop/measure.py`) | One de-lucked decision score per arm per generation, with no model call | Deterministic and unit-tested; pinned to the rule the July endpoint pre-registered | ✅ | Below |
| **Fail-loud guards** (`loop/invariants.py`) | Does a wrongly set-up run stop at once? | Both invalid June runs were caught on audit, and each slip became a guard | ✅ | Below; the guards themselves in [experimental controls](../experimental_controls/report.md) |
| **The July 19 run** | Did the loop run a declared experiment to its planned end? | Yes, with the guards on | ✅ | Below; the result in the [execution plan](../../memory_system/v7/execution_plan/report.md) |
| **Credit validators** | Does a decision's grade carry signal above luck, and which shortcuts fail? | Signal for some channels; override-based decay and a survival window ruled out | 🟡 | Below |
| **Held-out reproduction** | Does a lesson's score on half the games predict the other half? | r = +0.54 over 31 lessons; 8 of 9 flagged losers stayed negative | 🟡 | [credit](../../credit/report.md) §5 |
| **Attribution spot-check** | Do "followed" claims match what the agent did? | 13 of 15 | 🟡 | [credit](../../credit/report.md) §5 |
| **Blind-spot fix check** | Would the fixed rules have pruned the lesson that made the town abstain? | 9 of 12 checks passed; recorded games only | 🟡 | Below; the lesson's story in [credit](../../credit/report.md) §6 |
| **Tell scoring and the fold** | Which public behaviours give a role away, and can the list stay current between batches? | Strong associations on 60 held-out games; no gain in play shown; off on the live site | 🟡 | [tell_extraction](../../extraction/tell_extraction/report.md); the detector in [llm_judge](../llm_judge/report.md), case 8 |
| **First link** | Did an accusation change a listener's mind, or join a crowd already forming? | Built and unit-tested, never run | ⏸ | Below |
| **Synthesis A/B and offline prune** | Does the lesson writer write better lessons when it sees each lesson's score? | One unblinded read of two cases | ⚠️ | Below |

✅ sound · 🟡 usable with caveats · ⚠️ smoke test only · ⏸ built, never run.

## The machinery, and the two runs it caught

**The batch score.** `measure.py::generation_score` reads saved game files and gives each arm one mean
de-lucked decision score per generation, with no model call. Day 1 is skipped (no memory has acted yet),
only memory-on decisions count on the memory arm, and decisions are bucketed by arm, not by a per-decision
flag, so the two arms stay like for like (`tests/evaluation/test_loop_measure.py`). The same per-game score
is the July endpoint's pre-registered town score, and a test pins it to that rule, so later credit changes
cannot move the measure under a run.

**The two runs it caught.** Both June runs were invalid, and both were caught on audit. Run 1 had a distorted,
unpaired baseline. In v2 the memory arm silently ran memory for every side instead of the town alone, so the
"memory-off" control faced memory-using wolves; stronger opponents depress the town's score, and de-lucking
removes luck, not opponent strength, so the town result could not be repaired. A cache collision also scored
memory-off games with memory-on tags. Each slip became a guard that stops the run: the arm guard (each arm
runs the memory set-up it declares), a guard against observations reaching a lessons-only prompt, and the
run-stamp check (model, backend, prompt and commit unchanged mid-run). With the guard, v2 would have crashed
in its first generation instead of finishing a $15 run; the two runs together cost about $80–115.

**The July 19 run.** Four generations of 10 memory-on and 10 memory-off games (80 games), town-only memory,
lessons only, $25.74, a 168-lesson store. The fixes held: the run declared its arm (`expect_factions:
town_only`) and `loop_history.json` records the four town roles as the memory arm in every generation;
partial generations from crashed attempts were set aside, not pooled, as the signed rules required; and the
per-generation scores were recorded but not read as a trend, as planned. It shows the loop ran a declared
experiment to its end; it is not evidence that the store improved, which was the endpoint's question.

**What the machinery does not measure.** The quality of the lessons consolidation writes. The evict rule
evicted nothing in any of the four July generations.

## Credit validators

Four $0 scripts that re-score recorded games, run in June on 180 nine-seat games from the v6 paired A/B
(not the loop's own games), before the loop was trusted to prune; standing checks since 2026-07-04 in
`evaluation/src/instrument_validation/credit/`.

| Validator | Question | June result |
|---|---|---|
| Separability (`g2_separability.py`) | Is a decision's grade related to its side's win more than a shuffled-win null allows? | Yes for some channels: town day vote r = +0.56, healer block +0.42, serial-killer kill +0.26, wolf blend +0.22; null for the investigator's finds and wolf night targets |
| Override validity (`g3a_verdict_validity.py`) | Does the agent's follow-or-override verdict say which lessons are good? | No: agents followed almost every lesson (town day votes: 3 overrides against 334 follows), so credit was built on the decision's outcome instead |
| Held-out reproduction (`heldout_credit_reproduction.py`) | Does a lesson's score repeat on the other half of the games? | Yes in direction; told in [credit](../../credit/report.md) §5 |
| Windowed credit (`windowed_credit.py`) | Does crediting a decision over later days add clean signal? | No: survival one day on correlated +0.14 with the immediate grade and drifted toward the win itself as the window grew (+0.14 → +0.37 → 1.0) |

**Override validity on the ten-seat game (2026-10-24).** Re-run on the 20 Claude Haiku 5.5 memory-on demo
games of 2026-10-14 with the live credit rules, the first half of the June finding no longer holds: agents
now override often, 593 times against 1,154 follows (a third of the verdicts where a lesson applied). The
conclusion holds for a different reason: decisions where the agent overrode a lesson did no better than
decisions where it followed one (mean grade +0.17 over 106 against +0.24 over 248; 0.18 worse within the same
role and phase). An override still does not mark a bad lesson, so credit stays on the decision's outcome.
Twenty games, most role-and-phase groups under 15 decisions, no significance test, discussion decisions not
graded by these rules, and no control for how hard the board was. Runner
`evaluation/experiments/v8_override_validity.py`; output
`../../memory_system/v8/data/override_validity/summary.json`.

**What they can and cannot claim.** In the June epoch the grade carried signal for some channels and lesson
scores repeated, which justified pruning on credit and ruled out two shortcuts. They do not show that pruning
improves play, and the blind-spot case below shows a repeatable score can still miss a harm. The separability
correlations are recorded without their decision counts. Record: [v7_final/experiment_log.md](../../memory_system/v7/experiment_log.md)
§1–2, §6 (its `review_map.md` mislabels the override check as "tagger verdict validity").

## Blind-spot fix check

**Why.** After the endpoint, a lesson telling the vigilante to abstain under uncertainty had 19 follows and a
score of exactly zero, because every town abstain was graded neutral ([credit](../../credit/report.md) §6).
On 2026-07-21 two fixes were built: a town abstain on a day with no lynch is graded bad, and the
investigator's finds get a conversion channel.

**How.** `evaluation/experiments/credit_blindspot_validation.py` re-scores the two July runs under the old and
new rules and simulates the prune, at no cost. Six lessons were labelled in advance, three harmful and three
good, and it asks: does a harmful lesson become prunable; do the good ones stay; how many defensible abstains
does the new rule penalise? It runs on the endpoint games, where the fixes were designed, and on the build
run's games, which are different.

**Result.** 9 of 12 checks passed (`../../credit/blindspot_fix/step1_validation.md`). The abstain lesson went
from 0.00 to −0.62 on the build-run games and from −0.11 to −0.83 on the endpoint games, pruned in both; all
three good lessons stayed. The three failures are a scope gap: no rule reaches the healer-silence lesson, and
the investigator-silence lesson had too few uses on one corpus.

**Limits.** About −0.74 of the lesson's raw −0.89 reflects no-lynch days being bad for everyone, and only
about −0.15 is the lesson's own excess, so the rule is a pruning selector, not an estimate of harm. The labels
came from the same reading that motivated the fix, so a pass is necessary, not sufficient. A fresh run under
the fixed credit was never made. The fix is built into the ten-seat rules. Record:
[credit/blindspot_fix/](../../credit/blindspot_fix/) (`experiment_log.md` §②–⑤).

## First link

**What it is.** Discussion credit pays a speaker by where the day's lynch landed, so it cannot tell a speaker
who moved the room from one who joined a pile already forming. `loop/first_link.py` takes each accusation a
speaker aims at a named player and measures how the addressed listeners' next stated read of that target
changed, minus each listener's own drift on that target before the push, so a bandwagon join scores about
zero. It is a diagnostic only and never feeds prune or synthesis.

**Status.** Built in July 2026 with a unit test (`tests/evaluation/test_read_ledger_first_link.py`); no
recorded run. Its design is in [read_tactic_credit_redesign.md](../../credit/read_tactic_credit_redesign.md) §3.
Its docstring names two undercounts it would carry: about 40% of "unchanged" read entries are filler, and the
read scale is coarse. It also cannot tell persuading the room from reading it just before it turns.

## Synthesis A/B and the offline prune

- **Synthesis A/B** (`evaluation/src/studies/synth_deluck_ab.py`, 2026-06-19). Does synthesis that sees each
  lesson's credit write better lessons than synthesis weighted by the extraction model's own verdict, which
  follows the outcome? Three arms per deceiver cell were read side by side. On the serial killer's day vote,
  the outcome-weighted arm reproduced the passive "blend in, abstain" loser in all three clusters, and the
  credit-aware arm wrote a conditioned policy each time; on its night action the two were about equal.
- **Offline prune** (`evaluation/src/studies/consolidation_prune.py`). Dropping lessons with at least 8 follows
  and a score of −0.15 or less from a copy of the store removed 8 lessons in June; the live store was not
  switched.

**Trust: ⚠️.** The synthesis verdict is the author's unblinded read of two cells, with no rubric; the prune
study's outcome is a count. Neither shows a store that plays better. Records:
`../../memory_system/v7/runs/synth_deluck_ab/` and `synth_deluck_ab_flite/`; [v7_final/experiment_log.md](../../memory_system/v7/experiment_log.md) §3–4.

## Bottom line

The loop's machinery earned its rating: its checks caught both invalid June runs, became guards, and held
through the July run to its planned end. The credit validators answered the questions credit rests on,
within one epoch, and the July endpoint then showed what they could not see: a lesson whose harm the rules
priced at zero, which the blind-spot fix reaches on recorded games. Everything here is the nine-seat game;
the ten-seat credit that runs today has its own checks.

## Sources

| What | Where |
|---|---|
| Loop code and module map | `evaluation/src/loop/` (`driver`, `measure`, `credit`, `credit_backfill`, `conversion_credit`, `invariants`, `consolidate`, `first_link`); `evaluation/src/loop/README.md` |
| Tests named above | `tests/evaluation/test_loop_measure.py`, `test_loop_invariants.py`, `test_credit_blend.py`, `test_credit_blindspot_fix.py`, `test_read_ledger_first_link.py` (largely AI-written and unaudited; cited for what they pin) |
| Credit validators | `evaluation/src/instrument_validation/credit/` |
| June runs | [v7_final](../../memory_system/v7/) (`experiment_log.md` §1–6, §11–12; `runs/`); v2's cost in `runs/v2_full/cost_report.json` |
| Pre-registration, the July run, the result | [execution plan](../../memory_system/v7/execution_plan/report.md) §4–5; [its data](../../memory_system/v7/execution_plan/data/README.md) `v7_compound_town5/`, `v7_endpoint_ab/` |
| Blind-spot fix | `evaluation/experiments/credit_blindspot_validation.py`; [credit/blindspot_fix/](../../credit/blindspot_fix/) |
| Tells | `evaluation/src/loop/{tells,tell_credit,tell_fold}.py`; [tell_extraction](../../extraction/tell_extraction/report.md); [store_curation/tells.md](../../store_curation/tells.md) |
| Ten-seat credit | `Agents/memory/consolidation/`; [credit](../../credit/report.md) |

*Inspected 2026-06-28; widened and re-checked against the code and records 2026-10-23; slimmed on 2026-10-24
to the checks, with the parts told elsewhere linked. The previous version is in git history.*
