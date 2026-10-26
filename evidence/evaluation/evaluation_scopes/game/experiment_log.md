# Whole-game evaluation: the detailed record

*The folder was named `end_to_end_ab/` until 2026-10-23.*

This file holds the full detail behind [report.md](report.md). Read report.md first. Come here for how
each paired test was set up, how far it was checked, and every command, count, date and correction.
It replaces the long first version of report.md, first written 2026-06-28 for the June A/B and widened
on 2026-10-23. This file was written 2026-10-23.

---

## 0. The method and what pairing buys

### The aim

Play the same set of deals twice, once in each arm, and decide whether one arm does better.

- A *deal* is the role draw and seating that a game id seeds. Two games with the same id start
  identical.
- An *arm* is one configuration, for example memory on, voices off, or the old evil cards.

The aim is a comparison where the design under test is the only planned difference between the arms.
Two other things could also differ: model drift and the luck of the deal. Each must be either
controlled or measured.

### What pairing by deal does and does not control

Every comparison in this file pairs games by game id. Two facts limit what that buys.

**The deal is reproduced exactly.**

- The chain is `game_id → crc32 → role draw`.
- When the June A/B was set up (nine-seat, 2026-06-11), it reproduced 20 of 20 draws
  ([`paired_ab/experiment_log.md`](../../../memory_system/effectiveness/paired_ab/experiment_log.md)).
- The ten-seat deal is pinned by `tests/engine/test_seedability.py`. That includes the two drawn
  seats, the lone killer and the neutral. This test was written on purpose, and its premise is this
  pairing.
- Seedability is catalogued in [`../../experimental_controls/report.md`](../../experimental_controls/report.md).

**Only the deal is shared.**

- Play runs at temperature 1.0. So the two games part ways after the first line that differs.
- In the nine-seat game, a same-seed check (a *canary*: a small fixed run whose only job is to show
  whether something has shifted) measured how much the deal adds to the noise. It added almost none.
  The spread of results within one seed was 0.249 (standard deviation). Across seeds it was
  0.211–0.262 ([`model_drift/drift_surfaces_and_guards.md`](../../experimental_controls/drift_surfaces_and_guards.md)).
- So pairing cancels little noise.
- Its value is elsewhere. Both arms face the same starting position. And both run in the same sitting,
  the same *epoch*. An epoch is one snapshot of a hosted model, which can change overnight with no
  code change.
- This was not re-measured for the ten-seat game.

### The five tests at a glance

| § | Test | Game | Date | Pairs | Arms differ by | Trust |
|---|---|---|---|---|---|---|
| 1 | June memory A/B | Nine-seat | June 2026 | 30 deals | Memory on or off, one harness | 🟡 |
| 2 | v6 strategy-point A/B | Nine-seat | 2026-06-17 | 30 deals, six arms | Memory type | 🟡 |
| 3 | v7 endpoint A/B | Nine-seat | 2026-07-20 | 30 deals, 60 games | Grown store or no memory | 🟡 |
| 4 | Persona-voice games | Ten-seat | 2026-10-18 | 8 deals | One config flag | ⚠️ |
| 5 | Evil-cover games | Ten-seat | 2026-10-18 | 8 deals | Two code states, three changes | ⚠️ |

✅ sound · 🟡 usable with caveats · ⚠️ smoke test only.

---

## 1. The June memory on/off A/B (nine-seat, June 2026)

> **Warning: the source map's code pointer for this test was wrong.** It named `synth_deluck_ab.py`
> and `e2e.py`. Neither is the game-level A/B (see the corrections below). The real method is the
> chain in this section.

### What it is

On the same 30 deals, do players with memory of past games play better than players without it?

### How it works

**Generation: `scripts/run_batch.py`.**

- The arms are paired by a frozen set of game ids, passed with `--game-ids-file`. The chain
  `game_id → crc32 → role draw` reproduces 20 of 20.
- Each arm plays the same 30 ids.
- The memory treatment is held constant across games:
  - `--retrieval-types observations_only`
  - `--reranking rerank_disabled`
  - `--filtering filter_disabled`
  - top_k=5
  - `--no-memory-dump`, so the frozen store cannot grow during the test.
- The arms run as parallel batches that only read the store. They are paired after the fact.
- The seed sets are made by `scripts/make_ab_seed_set.py`.

**Analysis: `paired_ab/analyze_ab.py`.**

- It pairs the off arm with each on arm by `game_id`.
- Wins are tested with `mcnemar_exact`. Each validated decision score is tested with
  `wilcoxon_paired`.
- `regenerate_stats.py` does the same for older batches that were not paired.

**The de-luck step.** To *de-luck* a score is to remove the luck of the setup from it. Here that
means dividing by opportunity: a rate is counted over the chances a player had, not over whether the
event happened at all.

- The opportunity-based denominators live in `Agents/compute_metrics.py`.
- This works at the level of decision scores (*proxies*: scores that stand in for winning). That is
  the level the A/B relies on.
- The scores were checked against winning with a point-biserial correlation, which tests whether a
  score rises with the faction's win.
- The validated set of scores (the *basket*):

| Score | What it measures |
|---|---|
| `town_vote_accuracy` | Town votes on the right target |
| `correct_elimination_rate` | Eliminations that removed an enemy |
| `town_mislynch_rate` | Town votes that removed a town player |
| `serial_killer_lynched` | Whether the serial killer was voted out |

  Their correlations with winning were |r|≈0.55–0.65, p<0.01.

**Statistics: `core/stats.py`.** Every test is two-sided. No Bonferroni correction is applied
automatically. (A Bonferroni correction tightens the bar when many tests are run at once.) It is
applied by hand.

| Test | What it is | Used for |
|---|---|---|
| Clopper-Pearson | An exact confidence interval for a rate | Intervals |
| Fisher exact | An exact test of two rates from unpaired games | Unpaired comparisons |
| Exact McNemar | An exact test on paired yes/no results; it counts only the pairs where the two games disagree | Paired wins |
| Wilcoxon signed-rank | A paired test on the signed differences between two games of a pair, by rank | Paired decision scores |
| Point-biserial | The correlation between a score and a yes/no outcome | Validating the scores |

**The decision-replay screen: `experiments/decision_replay.py`.**

- It freezes one decision and swaps only the block of retrieved memory.
- It regenerates that one action and scores it against the true roles.
- It is *off-policy*: the rest of the game is not replayed under the new memory.
- Where the target is a role lookup, it needs no judge.
- It labels itself as off-policy, accurate to ±5–9 points, and for triage, not a verdict. In its own
  words: "we never headline a screen p-value".

**`measure.py` (the loop's measure).** It computes de-lucked points per faction, with no model call.
The fitted slope (by ordinary least squares) is computed later, downstream.

> **Corrections (2026-10-23).**
> - `regenerate_stats.py` is not in `paired_ab/`. It sits one level up, at
>   `evidence/memory_system/effectiveness/regenerate_stats.py`.
> - The decision-replay screen now lives at `evaluation/src/studies/decision_replay.py`. It is
>   catalogued in [`../turn/report.md`](../turn/report.md). It is listed here only
>   as the A/B's cross-check.
> - The de-luck basket was validated on the nine-seat game only. `Agents/compute_metrics.py` marks it
>   as not re-validated for the ten-seat game ([`../../metrics/report.md`](../../metrics/report.md)).

### What it can claim

The *MDE* (minimum detectable effect) is the smallest true effect a test would find 80% of the time
at its sample size. It was recomputed, and it confirms the harness's own claims.

| Measure | MDE at N=30 per arm, 80% power | What it means |
|---|---|---|
| Win rate | About 35 points (the doc said about 36) | Win rate cannot show an effect at this size. Only an effect as large as Batch A's (70 → 97) would clear it. |
| Vote accuracy | About 0.18–0.21 on the 0–1 accuracy scale (d≈0.53; the June text wrote "pp") | The headline town gain, `town_vote_accuracy` +0.149 (d≈0.37), is below this. So it came out at p=0.053. |

(*d* is the effect divided by the spread of the data.)

So no single test carries the verdict. What carries it is agreement across the 4 town arms and the
basket.

### How far it was checked

**Pairing buys about no reduction in noise.** This is the sharpest finding. The harness found it
against its own design and owns it.

- A canary ran on the same seed, the same config and the same epoch. It split the noise into parts.
- The effect of the seed (the role draw) was about zero. The spread within one seed was 0.249. Across
  seeds it was 0.211–0.262.
- All the noise is in how games play out at temperature above 0. None is in the board draw.
- In the record's words: "pairing on game_id adds ~no power; same-epoch was the load-bearing part of
  'paired/seeded'."
- The report had justified pairing with `Var(on−off)=…−2Cov`. That assumed a board-luck term, which
  the data showed is not there.
- This does not make the p-values wrong, because they already contain the true noise. It changes what
  the design buys: control of drift, not cancelling of noise.

**The de-luck step is validated** at the level of decision scores.

- The basket clears the point-biserial check against winning at |r|≈0.6, p<0.01.
- De-lucking is what caught and corrected a wrong denominator in the investigator's find rate.

**The screen agrees with the paired A/B.** This is the anchor for the A/B's validity.

| | Paired A/B | Decision-replay screen |
|---|---|---|
| Town | Win +17 and +23 points | Net value +0.078 on day 2, +0.117 in the endgame |
| Wolf and serial killer | No effect | No effect |

Both contradict an earlier "town collapse" of −40 points. That collapse proved to be model drift, not memory.

> *Correction 2026-10-26.* "Proved to be model drift" overstates it. The collapse was put down to a
> suspected change in the model service; that was not established. See the correction notes of
> 2026-10-25 in `evidence/memory_system/effectiveness/paired_ab/experiment_log.md`.

**Drift control.** This is the strongest step the harness took.

- The original baseline was thrown out after a shift in epoch was detected (Fisher p=0.0028).
- That led to three rules: a fresh baseline in the same epoch, always; a $3 memory-off canary that
  must pass first; and *called shots*, predictions written down before the run.
- The system caught its own confound.

**The null ladder.** Wolf and serial-killer memory showed no effect. That null was worked through as a
ladder of checks, free ones first, then paid:

1. validate a test for the deceiving roles on data already owned;
2. retrieval precision;
3. whether the player followed the memory (adherence);
4. the channel through which memory could do harm.

It ended at: "the wolf null may be a measurement gap (town-centric validated basket), not a true
ceiling."

> **Corrections (2026-10-23).**
> - **The win changes in the agreement table were not significant.**
>
>   | Arm | Town win rate | McNemar p |
>   |---|---|---|
>   | Raw town arm (not reranked) | 27% → 43% | 0.267 |
>   | All-roles arm | 27% → 50% | 0.167 |
>   | Reranked arm | 27% → 60% (+33 points) | 0.013 |
>
>   The reranked arm carries a model-drift caveat. Never pair "+17pp" with p=0.013.
>
>   What moved significantly in the raw town arm was the decision basket, over N=30 boards:
>   - healer saves of the real target, 0.37 → 0.60 (Wilcoxon p=0.005);
>   - correct eliminations, 0.47 → 0.64 (p=0.028).
>
>   Sources: [`paired_ab/report.md`](../../../memory_system/effectiveness/paired_ab/report.md) and
>   [`store_progression.md`](../../../memory_system/report.md) (correction of 2026-10-22). So
>   the screen agrees with the A/B on decisions, not on wins.
> - **The wolf-direct arm will not run.** The memory research closed on 2026-07-21 (§3).
> - **Every memory game ran without reasoning.** The game model ran at thinking level "minimal". That
>   produced zero reasoning tokens (found 2026-10-04). The arms matched, so the comparisons stand. But
>   every memory A/B here is about players that do not reason first
>   ([`memory_system/v7/execution_plan/report.md`](../../../memory_system/v7/execution_plan/report.md) §5).

### Trust: 🟡

The method is sound. Its two limits are its own findings: win rate needs far more games, and pairing
by deal buys almost no noise reduction.

### Code and record

`scripts/run_batch.py`, `scripts/make_ab_seed_set.py`,
`evidence/memory_system/effectiveness/paired_ab/analyze_ab.py`,
`evidence/memory_system/effectiveness/regenerate_stats.py`, `evaluation/src/core/stats.py`,
`Agents/compute_metrics.py`, `evaluation/src/studies/decision_replay.py`,
`evaluation/src/loop/measure.py`. Record:
[`paired_ab/report.md`](../../../memory_system/effectiveness/paired_ab/report.md),
[`paired_ab/experiment_log.md`](../../../memory_system/effectiveness/paired_ab/experiment_log.md),
[`store_progression.md`](../../../memory_system/report.md).

---

## 2. The v6 strategy-point A/B (nine-seat, 2026-06-17)

### What it is

The same harness, widened to six arms on 30 shared deals.

- *Observations* are per-game memories of what happened.
- *Strategy points* are lessons distilled from observations.

| Arm | Memory |
|---|---|
| 1 | No memory |
| 2 | Town, observations |
| 3 | Town, strategy points |
| 4 | Serial killer, observations |
| 5 | Serial killer, strategy points |
| 6 | Serial killer, both |

Source: [`v6_sp_ab/experiment_log.md`](../../../memory_system/effectiveness/v6_sp_ab/experiment_log.md).

### How it works

- `v6_sp_ab/launch_arms.sh` starts one `run_batch.py` process per arm.
- All the processes read `v6_sp_ab/game_ids.json`.
- The processes move in lockstep, one game index at a time across all arms. So every arm runs in the
  same epoch.
- The store is seeded read-only (`--no-memory-dump`).
- Retrieval is pinned raw: reranking and filtering are off.
- Wins are tested with paired McNemar and decision scores with Wilcoxon, as in §1.

It adds two things to the method:

- **A stated reason for the deceiver arm.** The serial killer was the deceiver arm, not the wolf. A
  prompt fix had changed how wolves behave, which made the stored wolf memory stale.
- **Metric discipline written into the result.** Only win rate and the validated town basket were
  reported as outcome claims. Three were kept as descriptive only, because they had never been
  validated against winning: the serial-killer basket, the vigilante activity counts and the healer
  activity counts.

### What it can claim

- Nothing reached p<0.05 on an outcome measure at N=30.
- The town-observations arm did not repeat the June town gain: villager wins +6 points, p=0.77.
- So the arm is a replication check and a direction, not a measured effect.

### How far it was checked

The same as §1, with two more limits:

- One arm (town, strategy points) was added mid-run.
- There was no town arm with both memory types.

### Trust: 🟡

For the same reasons and limits as §1, plus the two above.

### Code and record

`evidence/memory_system/effectiveness/v6_sp_ab/launch_arms.sh`, `scripts/run_batch.py`. Record:
[`v6_sp_ab/experiment_log.md`](../../../memory_system/effectiveness/v6_sp_ab/experiment_log.md).

---

## 3. The v7 endpoint A/B (nine-seat, 2026-07-20)

### What it is

The pre-registered test of the v7 learning loop. A memory store built over four generations of games
(168 strategy points) played against no memory, on 30 shared deals, 60 games. To *pre-register* is to
fix and sign the test's design before any data exists.

Sources: [`memory_system/v7/execution_plan/report.md`](../../../memory_system/v7/execution_plan/report.md) §4–5 and its
[`experiment_log.md`](../../../memory_system/v7/execution_plan/experiment_log.md).

### How it works

**The pre-registration.** It was signed on 2026-07-16, before any game. It fixed:

- one primary measure: the town's decision score per board, from the loop's measure
  `evaluation/src/loop/measure.py`, which uses no model;
- secondary measures, named as secondary;
- a fixed number of games;
- halting only on an automatic validity check;
- a written promise that a null or negative result is reported as "no compounding detected".

**One amendment, before data.**

- On 2026-07-20, before any endpoint game, the design changed. Three conditions on 20 boards became
  two conditions on 30 boards.
- The reasons were written into `batch_results/v7_endpoint_ab/PREREG_AMENDMENT.md`, beside the data.
- That file was copied on 2026-10-23 to
  [`memory_system/v7/execution_plan/data/v7_endpoint_ab/`](../../../memory_system/v7/execution_plan/data/README.md).

**Run hardening.** This is recorded in the run's `config.json`, in the same folder.

- Each board's two arms run together. So both face the same capacity and the same model snapshot.
- A board counts only when both arms complete.
- Halted partial boards are set aside and replayed in the same epoch. They are never pooled on one
  side only.
- A screen on each game disqualifies a game whose decisions fell back to defaults.
- At the end, an arm guard and a fingerprint check confirm that the run matched the loop's reference
  commit and backend. The run log shows:
  `[guards] … commit=a010dc68 backend=vertex == loop reference OK`.

### What it can claim

- Whether the finished store beats no memory on the same deals.
- After the amendment, it cannot say when or how fast the store got there.
- The result: with memory, the town's decision score was 0.147 lower (p≈0.06), and lower on 19 of 30
  boards.
- That result is a verdict for chapter 3 of the write-up. This file only rates how it was produced.

### How far it was checked

**The design was simulated before the run, in part.**

- The earlier design was a trend test. It was dropped on 2026-07-05.
- A simulation had shown it would miss a realistic effect about 9 times in 10
  ([`memory_system/v7/execution_plan/report.md`](../../../memory_system/v7/execution_plan/report.md) §2–3, catalogued in
  [`../../experimental_controls/report.md`](../../experimental_controls/report.md)).
- The power of the paired design that replaced it was not simulated.

**The script that computed the per-board paired statistic was not found.**

- The run log prints only pooled scores per decision. They are not the reported primary:

  | Arm | Town score, pooled per decision | Graded decisions |
  |---|---|---|
  | With memory | 0.039 | 458 |
  | Without memory | 0.247 | 438 |

- The −0.147 and p≈0.06 are recorded in the execution-plan report and the
  [blind-spot log](../../../credit/blindspot_fix/experiment_log.md). They are not reproduced from code
  here.

**The per-game data is not under version control.**

- It is in `batch_results/v7_endpoint_ab/`, 123 MB, in the data plane that git ignores.
- Five files were copied on 2026-10-23 to
  [`memory_system/v7/execution_plan/data/v7_endpoint_ab/`](../../../memory_system/v7/execution_plan/data/README.md): the config, the
  amendment, the pooled result, the run log and the final tell book.

### Trust: 🟡

The design is the strongest in this file. It was pre-registered, amended in writing before data,
paired by board, and guarded by checks that stop the run. It loses ✅ for two reasons: its primary
statistic has no committed code, and its data is not versioned.

### Code and record

`evaluation/src/loop/measure.py`. The run's driver and the paired-statistic script were not found.
Record: [`memory_system/v7/execution_plan/report.md`](../../../memory_system/v7/execution_plan/report.md) §4–5,
[`memory_system/v7/execution_plan/experiment_log.md`](../../../memory_system/v7/execution_plan/experiment_log.md),
[`credit/blindspot_fix/experiment_log.md`](../../../credit/blindspot_fix/experiment_log.md). Run files:
[`memory_system/v7/execution_plan/data/v7_endpoint_ab/`](../../../memory_system/v7/execution_plan/data/README.md).

---

## 4. Persona-voice games (ten-seat, 2026-10-18)

### What it is

- Eight deals, each played twice on Claude Haiku 5.5 at thinking level "low".
- One game has every AI seat speak in its puppet's voice (`RunConfig.persona_voices`). The other does
  not.
- Memory is off.
- The owner's question: do the AI seats still read each other as well when the table talks in voices?

Record: [`persona_voice_games/README.md`](../../../game_play_enhancement/data/persona_voice_games/README.md).

### How it works

**Generation.**

- `evaluation/experiments/persona_voice_games.py` runs one game per process.
- The two arms differ by one run-config flag on one commit: `85f5b274` for all 16 games.
- That is the config-flag pattern the project prefers for A/Bs.

**A record per game.**

- A capture: the prompt log, the reads log and the final state.
- A manifest: the git commit, the runtime fingerprint, the run config, the cost, the winner and the
  batch leak check.

**Scoring, with no model call.** `persona_voice_games_score.py` does three things.

- It counts spoken lines and words.
- It scores each seat's stated reads the way the read ledger does:
  - a committed read is checked against the true role;
  - its *Brier score* is averaged. The Brier score is the squared gap between the stated confidence
    and whether the read was right. High confidence counts as 0.85 and low as 0.65;
  - "unclear" reads are counted apart;
  - a wolf's read on its packmate is dropped.
- It splits town votes into three kinds: votes on a non-town player, votes on town, and abstains.

The read ledger is catalogued in [`../../metrics/report.md`](../../metrics/report.md).

### What it can claim

Direction only. The record states its own limits:

- only 8 pairs;
- the games diverge after the deal;
- the voiced arm talked about 19% more, which by itself gives readers more to read;
- wins at n=8 are noise.

The one paired test reported is a sign test on each pair's Brier score. (A sign test counts how many
pairs moved one way.) Reads were better with voices on 7 of 8 pairs, p≈0.07 (mean Brier 0.129 with voices against 0.155 without, from the run's README).

Not checked: the census of factual errors on the voiced lines.

### How far it was checked

- The batch leak check flagged 5 games.
- Reading the flags showed every one was a sentence the receiving seat also held in its own record.
  For example, two killers on one victim share the line "survived: the healer saved them".
- The check was narrowed in `tests/leak_test.py` (`check_night_record_isolation`).
- All 16 games then passed. The manifests keep the original result.
- So this was the method catching a false alarm in its own guard, not a leak in the game.

### Trust: ⚠️ smoke test only

Clean provenance and a one-flag difference. But only 8 pairs, and no measure fixed before the run.

### Code and record

`evaluation/experiments/persona_voice_games.py`, `persona_voice_games_score.py`,
`evaluation/src/loop/read_ledger.py`, `tests/leak_test.py`. Record:
[`persona_voice_games/README.md`](../../../game_play_enhancement/data/persona_voice_games/README.md),
`scores.json`, and the manifest of each game.

---

## 5. Evil-cover games (ten-seat, 2026-10-18)

### What it is

Eight deals, played before and after a set of three changes to the evil seats:

1. ruling R11's role cards ("claim, never deny");
2. implied role claims (deduction slice 13b);
3. a covers line in the deduction block (slice 14).

The question: do evil seats now fake a role claim in whole games, and what does that do to balance?

Record: [`evil_cover_games/README.md`](../../../game_play_enhancement/data/evil_cover_games/README.md).

### How it works

**Two code states, not a flag.**

- The "after" games ran on the working tree that had the changes.
- The "before" games ran at `c61fa762`, from a detached worktree. That is the Versioning Design
  Variants pattern in `CLAUDE.md`.
- Deals 01–04 of the "before" arm are the four step-5 games of the silence calibration
  (`silence_calibration/games/`). The README says they ran from the same code.

**Scoring, with no model call.**

- `evaluation/experiments/evil_cover_screen.py games` reads each capture.
- A claim is the seat's own structured `claim` field on a spoken line, not a judge's reading.
- It counts four things: the winners, the evil seats that claimed a role, how evil seats left the
  game, and whom the day votes removed.

### What it can claim

- Evil seats claimed far more often after the change: 11 of 24 evil seats, against 3 of 24.
- Winners (from the run's README): town 7 and the lone killer 1 before; town 5 and the wolves 3 after.
- A direction for balance. The README itself says eight games give a direction, not an estimate.
- The arms differ by three changes made together. So the games cannot say which change did the work.
  The replay screen in [`../turn/report.md`](../turn/report.md) isolates the card
  text.

### How far it was checked

- All 16 games passed the leak check.
- All ran on the same model, at the same thinking level, on the same day.

**Provenance is weaker than in §4.**

- Twelve of the 16 runs stamp a dirty working tree (uncommitted changes present).
- Each arm spans two commit stamps:

  | Arm | Commit stamps | Prompt-bundle hash (all eight games) |
  |---|---|---|
  | Before | `26a305d6`, `c61fa762` | `d3804d57…` |
  | After | `7f3551f0`, `206189bb` (its fingerprint reads `bbe553f3`) | `31992bb4…` |

- Within each arm, the prompt-bundle hash is the same across all eight games.
- But that hash covers only the top-level prompt modules (`Agents/run_fingerprint.py`). So it does not
  confirm the deduction-engine code or the echo-gate code.
- For the four silence games, "same code" rests on the README's statement.

### Trust: ⚠️ smoke test only

Eight deals, a bundle of changes, and runs from uncommitted trees.

### Code and record

`evaluation/experiments/evil_cover_screen.py` (`games`). Record:
[`evil_cover_games/README.md`](../../../game_play_enhancement/data/evil_cover_games/README.md),
`games_scores.json`, and the manifest of each game.

### The same pattern elsewhere: silence calibration, step 5

Step 5 of the silence calibration uses the same same-deal pattern. It played four games before and
after a change to the silence rule, on the deals of voices-01..04. Its record and its blind reads are
catalogued in [`../../labeling/sampled_reads/report.md`](../../labeling/sampled_reads/report.md).

---

## 6. Verdict and upgrades

### Verdict: 🟡, the A/B harness is sound and knows its limits

What makes it sound:

- pairing on the same `game_id`;
- a baseline in the same epoch;
- detection of drift between epochs;
- the canary;
- called shots, written before the run;
- the right paired tests;
- a screen that agrees with it;
- an honest null ladder.

It can be trusted even though the wolf result is inconclusive. The wolf null is correctly diagnosed
as limited by the channel and by measurement.

It is 🟡, not ✅, for its two stated limits:

- win rate cannot show an effect at this size (MDE about 36 points);
- pairing gives about no reduction in noise.

### Cheapest upgrade (from the harness's own audit)

*CUPED* is a method that cuts noise using a measure taken before the treatment. It does not apply
here. There is no such measure: all the noise comes from sampling at temperature 1.0.

So the upgrades were:

1. bootstrap or beta-binomial confidence intervals at analysis time (about 20 lines; the libraries
   are already installed);
2. more total games on the town arm, from fresh seeds, since pairing adds no power. About N=60–100
   per arm would push the decision scores past a Bonferroni correction. But the doc notes that the
   per-decision screen is a more power-efficient follow-up than buying win-rate games.

Not more pairing, and not CUPED.

> **Update (2026-10-23).** The memory upgrades above are moot. The memory research closed on
> 2026-07-21, and the ten-seat memory (v8) has not been tested at scale. For the October same-deal
> games, the cheapest upgrades are about procedure, not statistics:
> - Fix the measure before the run, as the June called shots and the v7 pre-registration did.
> - Run both arms from one committed tree behind a config flag, where the change allows it. §4 did.
>   §5 could not, since the card text is not a flag.
> - Commit the script that computes a reported paired statistic. §3 lacks one.

---

## Sources

### Code

- `scripts/run_batch.py`
- `evidence/memory_system/effectiveness/paired_ab/analyze_ab.py`
- `evidence/memory_system/effectiveness/regenerate_stats.py`
- `evaluation/src/core/stats.py`
- `evaluation/src/studies/decision_replay.py`
- `evaluation/src/loop/measure.py`
- `Agents/compute_metrics.py`

*(2026-10-23: the long version listed the decision replay at
`evaluation/src/experiments/decision_replay.py` and `regenerate_stats.py` under `paired_ab/`. Both
paths are corrected above.)*

### Data

- The live A/B data is in `batch_results/ab_*.jsonl`. It is in the data plane, so this file points at
  it. `analyze_ab.py` reads it.
- The older does-memory-help batch is stored beside its record, in
  [`../../../memory_system/effectiveness/batch_results/`](../../../memory_system/effectiveness/batch_results/).
- The screen's outputs are stored beside their record, in
  `../../../memory_system/effectiveness/decision_replay/*.json`.
- The seed sets and analysers are in
  [`../../../memory_system/effectiveness/paired_ab/`](../../../memory_system/effectiveness/paired_ab/).

### Where the files stay (decided 2026-06-28)

- Nothing moves. This also holds for the chapter 3 memory verdict.
- The live A/B data is in the data plane. Per `CLAUDE.md`, records point at it rather than copy it.
- The `effectiveness/` folders are what the memory chapter rests on. So they are not moved.
- Inspected 2026-06-28. That inspection rated the method, not the memory verdict.
- 2026-10-23: the October game records stay in `evidence/game_play_enhancement/data/`, where the
  design folders cite them. This file points at them.

### Per test

| What | Code | Record |
|---|---|---|
| Deal seeding (the premise of pairing) | `tests/engine/test_seedability.py` | [`paired_ab/experiment_log.md`](../../../memory_system/effectiveness/paired_ab/experiment_log.md) (20/20, 2026-06-11); [`../../experimental_controls/report.md`](../../experimental_controls/report.md) |
| Same-seed canary (pairing ≈ no noise reduction) | — | [`model_drift/drift_surfaces_and_guards.md`](../../experimental_controls/drift_surfaces_and_guards.md) |
| June memory on/off A/B | `scripts/run_batch.py`, `scripts/make_ab_seed_set.py`, `evidence/memory_system/effectiveness/paired_ab/analyze_ab.py`, `evaluation/src/core/stats.py`, `Agents/compute_metrics.py` | [`paired_ab/report.md`](../../../memory_system/effectiveness/paired_ab/report.md), [`paired_ab/experiment_log.md`](../../../memory_system/effectiveness/paired_ab/experiment_log.md), [`store_progression.md`](../../../memory_system/report.md) (2026-10-22 correction); data `batch_results/ab_*.jsonl` (ignored by git) |
| v6 strategy-point A/B | `evidence/memory_system/effectiveness/v6_sp_ab/launch_arms.sh`, `scripts/run_batch.py` | [`v6_sp_ab/experiment_log.md`](../../../memory_system/effectiveness/v6_sp_ab/experiment_log.md) |
| v7 endpoint A/B | `evaluation/src/loop/measure.py`; the run's driver and the paired-statistic script: not found | [`memory_system/v7/execution_plan/report.md`](../../../memory_system/v7/execution_plan/report.md) §4–5, [`memory_system/v7/execution_plan/experiment_log.md`](../../../memory_system/v7/execution_plan/experiment_log.md), [`credit/blindspot_fix/experiment_log.md`](../../../credit/blindspot_fix/experiment_log.md); run files [`memory_system/v7/execution_plan/data/v7_endpoint_ab/`](../../../memory_system/v7/execution_plan/data/README.md); per-game data `batch_results/v7_endpoint_ab/` (ignored by git) |
| Persona-voice games | `evaluation/experiments/persona_voice_games.py`, `persona_voice_games_score.py`, `evaluation/src/loop/read_ledger.py`, `tests/leak_test.py` | [`persona_voice_games/README.md`](../../../game_play_enhancement/data/persona_voice_games/README.md), `scores.json`, the manifest of each game |
| Evil-cover games | `evaluation/experiments/evil_cover_screen.py` (`games`) | [`evil_cover_games/README.md`](../../../game_play_enhancement/data/evil_cover_games/README.md), `games_scores.json`, the manifest of each game |
| Fingerprint coverage (prompt-bundle hash) | `Agents/run_fingerprint.py` | [`tracing/fingerprinting/report.md`](../../../tracing/fingerprinting/report.md) |

Where each figure comes from across the evaluation reports: [the source map](../../source_map.md). How
the evaluation reports fit together: [the hub](../../report.md).

*Written 2026-10-23 from the long first version of report.md. This file says how far each test can be
trusted. Whether memory, voices or evil covers helped is answered in the design folders linked from
[report.md](report.md).*
