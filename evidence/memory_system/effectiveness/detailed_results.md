# Memory effectiveness: detailed results and statistical notes

This is the supporting reference for the [effectiveness report](report.md), which owns the cross-version
summary. The June tables, replay findings, statistical qualifications and artifact index from the previous
report are retained here. Read this when checking a particular result; it is not the main reading path.
The v6 section here focuses on the town-observation comparison; the main report also indexes the other
v6 arms. v7 and v8 retain their detailed evidence in their own reports.

Editorial reorganisation only: the source records and statistics were not rerun.

## How town play was scored

**Win rate** is the obvious measure and the weak one: one win or loss per game, largely decided by the
deal (a wolf-favoured draw can decide a game before anyone reasons well). With 30 games a side, the
smallest difference the test could reliably see is about 36 points, so a flat win rate means "too few
games to tell", not "no effect". It is read for direction.

**The analysis uses the town decision-quality basket**: four decision measures, each graded against the
true hidden roles, so a game yields several graded decisions instead of one result.

- *Correct elimination*: the share of town eliminations that removed a wolf or the lone killer.
- *Mislynch rate*: the share that removed a town player (the other side of the same count).
- *Healer save*: how often the healer protected the player actually attacked that night.
- *Vote accuracy*: the share of town votes cast against an enemy.

Grading against the roles rather than the game's result is what the project calls **de-lucked**. It still
depends on the situations a game presents and on the scoring rules. The measures were checked before any
A/B result, on 50 earlier v5 games (30 memory-off, 20 memory-on): correct elimination, mislynch rate and vote accuracy each tracked the
villagers' win closely (|r| ≈ 0.55–0.65, p < 0.01, in both the pooled and the memory-off-only views), and
healer save more weakly (r = +0.36 pooled, p = 0.010; +0.33 memory-off only, p = 0.079)
([`../../metrics/proxy_win_monotonicity.md`](../../metrics/proxy_win_monotonicity.md)). No single measure
was named in advance as the raw arm's primary one (see [the timing](#which-measures-were-fixed-in-advance)).

**Terms used below.**

- An **observation** is a short account of one move and its effect, written after a game by a model that
  could see every hidden role. The June A/B retrieved observations only. A **strategy point** is a short
  piece of advice for a role and situation; it enters only in the v6 section.
- **`v5_0`** is the store used in the June A/B: the observations extracted from 20 memory-off games on the
  rebuilt nine-seat game, then frozen. Every arm read it and wrote nothing back (*consumption mode*), so
  the treatment stayed the same from the first game to the last.
- An **arm** is one condition, for example memory on for the town's four roles only. The **raw** arm used
  plain retrieval (the five most similar observations, about 3.4 shown per decision after the cap of three
  per situation, with an item found by both situations kept once). The **reranked** arm fetched about ten
  candidates and let a model reranker keep the best three. The **all-on** arm gave every role memory,
  with plain retrieval.
- A **board** is one fixed deal: the role draw and the seed that sets the turn order.
- An **epoch** is a stretch of runs over which the model service and the prompts behave the same. Runs on
  different days, or before and after a prompt change, may sit in different epochs.
- **SK** is the lone killer (serial killer), the third faction.

**Model setting.** Every game behind the June A/B and the v6 A/B played on `gemini-3.1-flash-lite` at
thinking level "minimal", which for this model and output produced zero reasoning tokens (probe of
2026-10-04). The run fingerprints confirm "minimal" on all 398 June A/B game records
([`../../credit/blindspot_fix/experiment_log.md`](../../credit/blindspot_fix/experiment_log.md) §⑦) and
on all 180 records of the v6 A/B (checked 2026-10-26); the replays regenerated turns with the same model
and temperature. Both arms ran alike, but these results say nothing about higher thinking settings, and
zero reported reasoning tokens does not establish an absence of reasoning inside the model. The early
batches carry no fingerprint, so their thinking level is not recorded.

**Served configuration recorded on 2026-10-26.** None of this describes served games now. In served games memory is the
player's switch and starts off (`frontend/src/app/(site)/_components/ticket/TicketOffice.tsx`); whether a
deployment offers it at all is a setting (`server/config.py`, `WW_MEMORY_ENABLED`). With it on, every AI
seat retrieves strategy points only, never observations (`server/game/run_config.py::game_run_config`).

## The June A/B on the `v5_0` store

**The question: with the deal held fixed, does memory make the town decide better?** Earlier unpaired
batches had swung widely (see [the early batches](#before-the-rebuild-two-unstable-batches)), so this test
played each of 30 boards twice, once with memory and once without, in the same epoch. Pairing fixes the
role draw and the turn order; it does not fix the model's sampling, which stays as noise within each pair.
Memory went to the town, the wolves or the lone killer in turn, each with raw retrieval; the town also
with reranking; and every role at once (all-on). The memory-off baseline was played fresh the same day
(town win 27%), because an older one had shifted (see [the discarded baseline](#the-discarded-historical-baseline-a-standing-rule)).

**The answer: with memory, the town found its enemies more often and the healer saved the right player
more often.** These are the four measures on the raw town arm, the arm played interleaved with the
baseline:

| Measure (30 paired boards) | memory off | memory on | change | p |
| --- | --- | --- | --- | --- |
| healer saves the real target | 0.370 | 0.598 | +0.228 | **0.005** |
| town eliminations hit an enemy | 0.470 | 0.638 | +0.168 | **0.028** |
| town eliminations hit a town player | 0.530 | 0.362 | −0.168 | **0.036** |
| town votes cast against an enemy | 0.560 | 0.710 | +0.149 | 0.053 |

Bold marks p < 0.05, before any correction for the number of tests.

The four rows measure two things, not four. The two elimination rows split the same eliminations two ways,
and vote accuracy measures the same skill one vote at a time; together they are *finding the enemy*. Healer
save is *protection*. Both moved in memory's favour.

The town's win rate rose on every town arm. Only the reranked comparison crossed the unadjusted significance threshold, and its later timing weakens the interpretation:

| Arm (memory on for) | When it ran | Town win, off → on | change | p |
| --- | --- | --- | --- | --- |
| town, raw | interleaved with the baseline | 27% → 43% | +17pp | 0.267 |
| town, reranked | later the same day, after the baseline finished | 27% → 60% | +33pp | 0.013 |
| every role (all-on) | later the same day, after the baseline finished | 27% → 50% | +23pp | 0.167 |

**How sure we are.**

- *Not called in advance.* The raw arm ran before the pre-registration was written, and over all 24 tests
  on the raw arms none clears a correction for that many tests. The detail is under
  [the statistics](#the-statistics-behind-the-june-ab).
- *The baseline may have drawn low.* Town measures also improved in the arms where only the wolves or only
  the lone killer had memory, which town memory cannot explain; and a memory-off rerun of the same boards
  the next day played about as well as the town did with memory. Part of the gain may be a low baseline, or
  drift between days (suspected, not established). The figures are under
  [Was the baseline a low draw?](#was-the-baseline-a-low-draw)
- *The one significant win rate is the weakest arm.* The reranked arm ran after the baseline had finished,
  with no check for drift within the day, so the record does not rest on its p = 0.013.
- *One model setting.* All of it ran at the minimal thinking setting (see Model setting above).

## Side-findings that shaped later work

**No benefit was detected for the deceivers.** The wolf arm was flat (win 33% → 30%, p = 1.000) and the SK
arm trended down (40% → 20%, p = 0.146); neither faction's decision measures improved at 30 boards. One
plausible reading is that the town plays an inference game, where patterns from past games help, while the
wolves and the lone killer play in-the-moment deception that a fixed store does not sharpen. That is a
hypothesis, not a finding: the arms are underpowered, and other explanations were entertained at the time
(retrieval precision, outcome framing, an adherence gap; see [`paired_ab/`](paired_ab/report.md)). What
followed from it is firm: a win can hide bad play and a loss good play, most of all on the deceivers'
side, so v7's credit graded lessons by decision quality against the roles rather than by win or loss.

**Reranking showed no advantage over plain retrieval, so it was set aside, not disproven.** On town vote
accuracy the reranked arm did no better than the raw one (0.710 → 0.686, p = 0.518), and 30 boards are too
few to exclude a small effect. This pointed v6 toward matching lessons by structured situation fields
(players alive, how close a side is to winning) instead of text similarity alone; v6 found no gain either.

## Why the v6 A/B found no town effect

**The question: a later A/B on the v6 store found no town effect. Did the new store break the benefit?**
The v6 test (2026-06-17, 30 paired boards, its own same-day baseline) gave the town observations and found
it flat: villager win +6pp (p = 0.77), decision measures unchanged. The v6 store was rebuilt around
structured situation fields. It was not a replication of the June test: it ran in a different epoch, on a
different store, with a changed prompt bundle.

**One plausible reading: the no-memory baseline had risen to where memory used to lift the town.** Between
the two runs the play prompts changed (a round of fixes), on top of the drift suspected in June. The
no-memory town played much better on 06-17 than on 06-11:

| No-memory town | June 11 | June 17 |
|---|---|---|
| vote accuracy | 0.560 | 0.674 |
| eliminations hit an enemy | 0.470 | 0.622 |
| eliminations hit a town player | 0.530 | 0.378 |
| win rate | 27% | 37% |

That is roughly the level June's memory had lifted the town *to*, which leaves less room for a gain to
show. It does not establish that no room remained.

**A same-day check finds the two stores alike.** A replay screen scored both stores in one sitting: the v5
store 0.625 and the v6 store 0.604, both below no memory at 0.667 (p = 1.0)
([`../strategy_adoption/forced_schema_screen/`](../strategy_adoption/forced_schema_screen/experiment_log.md)).
Even the store that "worked" in June reads flat in the later epoch, which fits the epoch reading better
than a fault in the v6 schema.

**One concern stays open.** v6 frames each lesson's outcome by its effect on the final result
(net-first) for the town as well as the deceivers (`Agents/schemas/memory.py::_compose_outcome`), and the
screens below found framing effects depend on the situation. A flat overall result cannot say whether this
contributed. Full analysis in [`v6_sp_ab/experiment_log.md`](v6_sp_ab/experiment_log.md).

## Screening layer: per-decision replays

**The question: which cheap change would make the agents use memory better, before paying for whole
games?** A whole-game arm costs about $15–30 and is exposed to drift between days. A **decision replay**
takes one recorded decision, swaps only the memory block, regenerates that one action and grades it
against the true roles. Both versions run in one sitting, so drift hits both alike, and a question costs
about $1. It shows the direction and mechanism of a change at one moment of a game, not its effect on
the whole game or the win rate. Running in one sitting reduces timing differences; it does not guarantee identical exposure to provider changes. (The method itself is explained once in
[Replay screens](../../evaluation/evaluation_scopes/turn/report.md); this section keeps what the memory
screens found. Absorbed 2026-10-26 from
[`decision_replay/report_screening_layer.md`](decision_replay/report_screening_layer.md).)

The screens replayed decisions from a June 12 town arm whose store was a variant of `v5_0`: the same 20
games re-extracted so that each observation's outcome leads with its effect on the game's final result
(**net-first framing**). They are not replays of the June A/B's own store.

**The answer: the replays pointed the same way as the A/B, and no prompt-only change helped
everywhere.**

- *Agreement with the A/B.* Memory helped the town's votes on day 2 (+0.078) and in the endgame (+0.117),
  and did nothing detectable for wolves or the lone killer: the same direction as the June A/B, on a
  different store and day, not a replication of its size.
- *The cheap changes.* Each was tested in turn:

| Change | What it did | Finding |
| --- | --- | --- |
| Reasoning before the vote | the seat writes its reasoning first | vote and reasoning agreed more (75% → 92.5%, 40 decisions), but use of memory did not rise (about 0 on a judge-free echo check, 150 decisions), and it could flip a correct vote to wrong on bad content |
| A forced "does this apply?" verdict per memory | the seat judges each memory first | the seat rejected a planted mismatched memory in 13 of 20 decisions and told situation match from lesson transfer, but its votes fell 0.75 → 0.55 (20 decisions), with over-cautious abstentions in the cases read |
| Outcome framing | each lesson's outcome rewritten from final effect to immediate effect | depends on the situation (below) |

- *Framing flips with the situation.* Pooled, the framing change looked like nothing (40 decisions,
  +0.025, p = 1.0), but that sample came from day 3 onward, where the base prompt already covers the
  decision and memory changes little. Split by stage:

| Stage | Final-effect framing (cautious) | Immediate-effect framing | Difference |
| --- | --- | --- | --- |
| day 2, little information (30 decisions) | **+0.10** (no memory: −0.067) | −0.067 | −0.167 (4 worse, 0 better, p = 0.125) |
| day 5 on, endgame (20 decisions) | 0.30 | 0.20 | −0.10 (p = 1.0) |

  On day 2 the cautious framing turned would-be mislynches into defensible abstentions (mislynch
  0.23 → 0.07); the "actionable" rewrite undid that, pushing the seat to vote when there was nothing to hit.

**How sure we are.** Every finding here is suggestive: 20 to 40 decisions per cell, and no screen p-value
is used as a headline. The firmest pieces are the forced verdict's capability result (the seat *can* judge
whether a memory applies) and the day-2 benefit of cautious framing, which the screen's own stage split
had shown before. The strata are not pooled: pooling is what hid the day-2 effect the first time.

**What followed.** None of the prompt changes gave a clear general improvement, so the project next
worked on lessons that state their conditions (be cautious when information is thin, act when the threat
is clear). That was a reason to try conditioned extraction, not evidence that content was the only
remaining limit.

## Before the rebuild: two unstable batches

**The question these answered: why did the June study need a frozen store and paired boards?** Before the
`v5` rebuild, two unpaired batches of about 30 games per condition on the old game produced large
differences that did not persist. Each cell is the villagers' win rate:

| Condition | Batch A (`v3_deduped`) | Batch B (`v4` + action_phase) |
| --- | --- | --- |
| No memory | 70.0% (21/30) | 74.2% (23/31) |
| Wolf only | 87.1% (27/31) | 83.3% (25/30) |
| All enabled | **96.7%** (29/30) | 73.3% (22/30) |

Batch A's all-enabled lift (70% → 96.7%, Fisher p = 0.012) took the villagers from losing one game in
three to one in thirty. But it is the best of six comparisons (borderline after correction), and the same
condition fell back to baseline in Batch B (73.3%, p = 1.0), where the store version and how finely the
store is split by role and phase changed together, so the batches cannot say why. They do not estimate an
achievable ceiling. The `v4 → v5` rebuild also changed the game itself (nine players, three factions, a
sequential scheduler), so no batch figure can be compared with a `v5` figure: they are context, never a
comparator.

## Compounding: closed

Whether a memory that rewrites itself across generations helps *more over time* is a different question.
Two paid loop runs meant to answer it were both invalidated (a biased de-lucked baseline in one, a config
slip that ran the wrong arm in the other). An amended, pre-registered endpoint run tested the finished
memory against none: 30 boards, each played once with the loop's final memory and once without. The town's
decision score was 0.147 lower with memory, on 19 of the 30 boards (paired t-test p = 0.065; Wilcoxon
p = 0.105), and, as committed, this was reported as "no compounding detected", with the estimate leaning
toward harm. It did not directly compare successive memory generations. The owner closed the memory
research on 2026-07-21 without a further run. Closed is not disproved: the run detected no compounding, at
this size and with the minimal-thinking player configuration. The pre-registration and result are in the
[v7 report](../v7/report.md), "The pre-registration" and "What the signed run found".

## Detail for checking

### The statistics behind the June A/B

- **Tests.** Win rates: McNemar on the boards where one side won and the other lost. Decision measures:
  paired Wilcoxon on each board's difference. The full design and the wolf and SK arm tables are in
  [`paired_ab/`](paired_ab/report.md).
- **Corrections.** Over the raw town arm's three distinct measures, a Bonferroni line is 0.017; healer save
  (0.005) clears it. Over all 24 raw-arm tests (three arms by eight measures) the line is 0.002, which no
  single result clears; about 7 of the 24 fell below 0.05, against about 1.2 expected by chance.
- **The two elimination rows are one test.** Correct elimination and mislynch rate are exact complements
  (they divide the same eliminations two ways). Their reported p-values, 0.028 and 0.036, differ only
  because floating-point rounding breaks rank ties differently; both give p = 0.030 once the rates are
  rounded.
- **Win rate's reach.** At 30 boards the minimum detectable effect on win rate is about 36pp.

### Which measures were fixed in advance

The measures were chosen by the separate check above before any A/B result. The written pre-registration
(2026-06-11) was committed after the raw arms had run and before any reranked game finished; it named one
primary measure per arm for the reranked and all-on arms (town vote accuracy for the town). The raw arm's
results were therefore not *called shots* (predictions written down before the data); they are reported
with the multiplicity caveat above ([`paired_ab/experiment_log.md`](paired_ab/experiment_log.md),
"Pre-registration").

### Was the baseline a low draw?

Added 2026-10-26. Two facts in the record bear on it, and the record does not separate them from a memory
effect. Town measures also improved in the arms where only the wolves or only the lone killer had memory and
the town had none: town mislynch rate 0.530 → 0.406 (p = 0.042) and 0.530 → 0.343 (p = 0.029)
([`paired_ab/report.md`](paired_ab/report.md)). And two memory-off canary runs on the baseline's 30 seeds
the next day (2026-06-12; 59 games when the figures were logged) played at town vote accuracy 0.699 and a
51% villager win (30 of 59), against the baseline's 0.560 and 27%, about the level the raw town arm reached
with memory (0.710) ([`paired_ab/experiment_log.md`](paired_ab/experiment_log.md), "Phase A
town-regression — conclusion"). Both fit a baseline that drew low, or drift between days (suspected, not
established).

### The reranked arm's timing

The raw arm was interleaved with the baseline in time; the reranked and all-on arms ran later the same day,
after the baseline finished, with no drift canary within the day (that arrived 06-12). Pairing controls the
starting deal but not drift within the day. Interleaving the raw arm reduces that timing risk; it does not
remove sampling noise or the low-baseline concern.

### The discarded historical baseline (a standing rule)

The original memory-off baseline (villagers 67% / SK 27% / wolves 7%) came from an earlier epoch, and a
fresh 10-game re-run of it shifted systematically (Fisher p = 0.0028) despite byte-identical play prompts.
Silent model drift on the provider's side was suspected, not established: on the 20 deals both baselines
shared, tested as pairs, villager wins fell from 12 to 7 (exact McNemar p = 0.18; see the re-test note in
[`paired_ab/experiment_log.md`](paired_ab/experiment_log.md)). It was discarded and the baseline re-run
fresh inside the A/B's own epoch (villagers 27% / SK 40% / wolves 33%), which is the memory-off control
every June table uses. The rule this set: never pair against a baseline from another epoch.

### The `v5_1` pilot

An early pilot on `v5_1` (a store that grew as memory-on games wrote back into it; unpaired; raw retrieval)
suggested memory *hurt* the town by −32pp (p = 0.043). The collapse did not recur in the paired A/B.
Because the pilot also used a moving store and an older baseline, it cannot isolate memory as the cause,
and the later test does not establish which confound explains it. See
[`v5_baseline_proxy_analysis.md`](v5_baseline_proxy_analysis.md).

### The v6 numbers

The prompt bundle changed `16f7f700` → `1cb76993` between the runs. The 06-17 no-memory values recompute
from `batch_results/v6ab_*.jsonl` `all_disabled` (30 games, re-verified 2026-07-05). The drift suspected
in June was re-tested as pairs (exact McNemar p = 0.18; see
[`paired_ab/experiment_log.md`](paired_ab/experiment_log.md)). The same-day store screen: v5 store 0.625,
v6 store 0.604, no memory 0.667, McNemar p = 1.0. The store's history is in the
[memory overview](../report.md).

### The replay screens

- **Agreement with the A/B, side by side:**

| | Paired A/B (whole game, 30 boards, `v5_0`) | Decision replay (per decision, net-first variant) |
| --- | --- | --- |
| town | selected raw-arm measures significant uncorrected, none clearing the 24-test correction (healer saves p = 0.005, correct eliminations p = 0.028); win +17pp raw (p = 0.267) and +23pp all-on (p = 0.167), not significant | +0.078 net value on day-2 votes, +0.117 in the endgame |
| wolf / SK | null | null |

  Neither reproduced an earlier −40pp "town collapse" in the net-first town arm, which the record discusses
  alongside possible drift between days, without isolating the cause (see the 2026-10-25 correction notes in
  [`paired_ab/experiment_log.md`](paired_ab/experiment_log.md)).
- **What a screen can claim.** Pairing at the decision cancels role luck, and it needs no judge wherever the
  target is a role lookup. It sees local decision quality at a frozen board, not trajectory, magnitude or
  win rate. Cell-level breakdowns and agreement with another analysis help explain a pattern; neither
  removes the uncertainty of a small sample.
- **Lessons from the screens.**
  - *A cheap paired screen earns its keep by triage, not significance.* Small samples buy direction; the
    win-rate question stays with whole games. Use screens to choose follow-up work, keeping the sample
    limits in view when deciding to stop investigating a candidate.
  - *Pooling hides structure, learned twice.* Pooling days hid the day-2 framing effect; pooling roles would
    hide the cell differences that are the finding. Stratify, report the cells, and let the pattern across
    cells carry the weight.
  - *Capability is not adoption.* A model can reason about a memory's applicability when forced to, yet
    doing so degrades the decision. Measuring "can it" apart from "does it help" separates a diagnosis
    from a plausible story.
- **Provenance.** Game and replay model `gemini-3.1-flash-lite` at temperature 1.0 (replays match the
  games' model and temperature); adherence and coherence judges `gemini-2.5-pro` / `gemini-2.5-flash` (used
  only off the headline path). Driver: `evaluation/src/studies/decision_replay.py` (the screens ran it from
  its June path, `evaluation/src/experiments/`). Commits `d335d2c` → `b332550`. Per-finding artifacts in
  [`decision_replay/`](decision_replay/) (`echo_*`, `coherence_*`, `applicability_*`, `framing_*` JSONs);
  full reasoning trail in [`decision_replay/experiment_log.md`](decision_replay/experiment_log.md).

### Artifacts and provenance

The A/B statistics live in [`paired_ab/`](paired_ab/report.md); the pre-rebuild JSONLs and the stats
regenerator are co-located here.

| File | Description |
| --- | --- |
| `paired_ab/report.md` | Generated readout: full `v5_0` A/B stats, all arms (town/wolf/SK × raw/reranked/all-on), pre-registered called shots |
| `paired_ab/experiment_log.md` | A/B design, the suspected epoch shift and its 2026-10-25 paired re-test, seed set, wolf/SK diagnostics |
| `batch_results/ab_*.jsonl` (repo root) | Paired A/B raw results: `ab_baseline`, `ab_arms_{town,wolf,sk}`, `ab_rr_*`, `ab_allon` |
| `decision_replay/experiment_log.md` | The per-decision screens: method, findings, validity analysis, the cheap-lever ladder |
| `decision_replay/*.json` | Per-screen run records (`causal_*`, `echo_*`, `coherence_*`, `applicability_*`, `framing_*`, `reorder_*`) |
| `v6_sp_ab/experiment_log.md` | v6 A/B (6 arms), not a replication of the June test, + cross-epoch analysis |
| `regenerate_stats.py` | Recomputes every p-value/CI for the pre-rebuild batches from the JSONLs (uses `evaluation/src/core/stats.py`); no hand-typed statistics |
| `batch_results/werewolf_flashlite_3_v1.jsonl` | Batch A: no_memory (30) + wolf_only (31), v3_deduped store |
| `batch_results/werewolf_flashlite_3_v1_deduped.jsonl` | Batch A: all_enabled (30), v3_deduped store |
| `batch_results/v4_action_phase_v2.jsonl` | Batch B: no_memory, v4 store with action_phase |
| `batch_results/v4_action_phase_v2_wolf_only_all_enabled.jsonl` | Batch B: wolf_only (30), v4 store |
| `batch_results/v4_action_phase_v2_all_enabled_remainder.jsonl` | Batch B: all_enabled remainder (18), v4 store |

**Provenance.** The A/B arms ran 2026-06-11 on `gemini-3.1-flash-lite` / Vertex, prompt bundle `16f7f700`,
store `memory_stores/v5_0` read-only (run flag `--no-memory-dump`). Every win rate and proxy above was
independently re-verified from `batch_results/ab_*.jsonl` on 2026-07-02 (own pairing and a separate stats
path).
