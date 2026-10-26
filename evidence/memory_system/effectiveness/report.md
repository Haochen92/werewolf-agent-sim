# Memory effectiveness: did a fixed store of past-game lessons improve play?

This is the record of the June 2026 static-memory test on the nine-seat game: whether giving the agents a
fixed store of notes from past games made them play better, how that was measured, what it found, and why
a later test on a different store did not repeat it. It is an experiment report: the mechanism is
described as it ran in June, and anything about today's system is dated. The version-by-version account
of the memory system is the [memory overview](../report.md); the full A/B statistics and design are in
[`paired_ab/`](paired_ab/report.md); the separate question of whether a memory that rewrites itself
improves over time is answered in the [v7 report](../v7/report.md).

## In short

- **Question.** Does a fixed store of notes from past games make the town decide better than no memory?
- **Test.** 30 paired boards (each fixed deal played once with memory and once without, 2026-06-11), on a
  frozen store with plain retrieval, scored by measures graded against the hidden roles.
- **Answer.** Selected town decision measures improved: the healer saved the real night target 37% → 60%
  of the time (p = 0.005), and town eliminations hit an enemy 47% → 64% (p = 0.028). The town's win rate
  rose 27% → 43%, not significant (p = 0.27). Wolves and the lone killer gained nothing. Every game ran
  with players that produced no reasoning before answering.
- **What followed.** A later A/B on a different store, run against a higher no-memory baseline, found no
  town effect; it was not a replication of the June test. Separately, the pre-registered v7 endpoint
  detected no compounding benefit. The owner closed the memory research on 2026-07-21: the investigation
  is closed, and the hypothesis was not disproved.

## Scope

**The players did not reason.** Every game behind the June A/B and the v6 A/B played its turns on
`gemini-3.1-flash-lite` at thinking level "minimal", which for this model and output produced zero
reasoning tokens (probe of 2026-10-04). The run fingerprints confirm "minimal" on all 398 June A/B game
records ([`../../credit/blindspot_fix/experiment_log.md`](../../credit/blindspot_fix/experiment_log.md) §⑦)
and on all 180 records of the v6 A/B (checked 2026-10-26). The per-decision replays regenerated turns
with the same model and temperature. Both arms of every comparison ran alike, so each comparison is fair,
but each result is a result for a player that answers without a reasoning step. The pre-rebuild batches
carry no fingerprint, so their thinking level is not recorded.

**The terms used below.**

- An **observation** is a short account of one move and its effect, written after a game by a model that
  could see every hidden role. The June A/B retrieved observations only. (A **strategy point** is a short
  piece of advice for a role and situation; it enters only in the v6 section.)
- **`v5_0`** is the store used throughout: the observations extracted from 20 memory-off games on the
  rebuilt nine-seat game, then frozen. It was read **read-only** in every arm (the run setting called
  this *consumption mode*): games read from it and wrote nothing back, so the treatment stayed the same
  from the first game to the last.
- An **arm** is one condition of the comparison, for example memory on for the town's four roles only.
  The **raw** arm used plain retrieval (the five most similar observations, about 3.4 shown per decision
  after near-repeats collapse). The **reranked** arm fetched about ten candidates and let a model reranker
  keep the best three. The **all-on** arm gave every role memory, with plain retrieval.
- A **board** is one fixed deal: the role draw and the seed that sets the turn order.
- An **epoch** is a stretch of runs over which the model service and the prompts behave the same. Runs
  on different days, or before and after a prompt change, may sit in different epochs.
- SK is the lone killer (serial killer), the third faction.

**Today (checked 2026-10-26).** None of this describes served games now. In served games memory is the
player's switch and starts off (`frontend/src/app/(site)/_components/ticket/TicketOffice.tsx`); whether a
deployment offers it at all is a setting (`server/config.py`, `WW_MEMORY_ENABLED`). With it on, every AI
seat retrieves strategy points only, never observations (`server/game/run_config.py::game_run_config`).

## The verdict

- ✅ **The June static-memory A/B reported improvements on selected town decision measures.** On the
  frozen `v5_0` store and the raw arm (N=30), the healer's saves and the town's eliminations improved
  significantly. Win-rate direction is consistent across every town arm, though win rate alone is
  underpowered at this N. Part of the gain may reflect a baseline that drew low (see *Was the baseline a
  low draw?* below).
- ⚪ **No detectable wolf or SK benefit in this A/B.** At N=30 the wolf and SK arms are null on win rate
  and on their own proxies.
- ⚠️ **A later A/B on a different store (v6), run against a higher no-memory baseline, found no town
  effect; it was not a replication of this test.** One plausible reading is a risen no-memory baseline
  between epochs, not a broken store (a same-epoch control found the two stores alike). That reading is
  not established.
- ⚪ **Separately, the pre-registered v7 endpoint detected no compounding benefit** (see *Compounding:
  closed* below). That question belongs to the [v7 report](../v7/report.md), not this one.

## The instruments: how we measure "outcome"

Two rulers measure whether memory helped; the report leans on the second.

**Win rate** is the obvious ruler and the weak one: one binary win/loss per game, dominated by setup
luck (a wolf-favoured draw can decide a game before anyone reasons well). At N=30 the minimum detectable
effect is ≈36pp, so a flat win rate means "underpowered to detect," not "no effect." It corroborates
direction but rarely reaches significance.

**The town decision-quality basket** is the primary endpoint. Each proxy is graded mechanically against
the true hidden roles (correct elimination, mislynch, healer save of the real night target, vote
accuracy), so it measures *decisions, not luck* by construction, and yields several graded events per
game rather than one bit. Grading against the roles rather than the game's result is what the project
calls **de-lucked**. The basket was validated separately, on 50 earlier v5 games (30 memory-off, 20
memory-on): correct elimination, mislynch rate and vote accuracy each track the villagers' win at
|r|≈0.55–0.65, p<0.01, in both the pooled and the memory-off-only views; healer town-save rate tracks it
more weakly (r = +0.36 pooled, p = 0.010; +0.33 memory-off only, p = 0.079)
([`../../metrics/proxy_win_monotonicity.md`](../../metrics/proxy_win_monotonicity.md)). That is why the
basket is the endpoint and win rate the directional co-read.

## The deciding experiment: the `v5_0` paired A/B

The earlier evidence (below) showed memory *can* move outcomes but left the current configuration
unresolved. To remove the setup-luck confound, we ran a paired, seeded, same-epoch A/B. Each of 30
boards is played twice under identical initial conditions, differing only in whether memory is on.

Pairing on the game's identifier pins the board: the role draw and the scheduler's turn-order
tie-breaks, both seeded from it. It does *not* pin the LLM's sampling nondeterminism, which stays as
within-pair noise; the paired tests average over it across the 30 pairs (**McNemar** on discordant
win/loss pairs, a paired **Wilcoxon** on per-pair proxy differences). Setup luck is the noise source we
argue dominates in werewolf, so holding it fixed is what isolates the treatment. The store is the frozen
`v5_0`, read-only; arms cross raw / reranked / all-on retrieval with the town / wolf / SK factions. Full
design and the wolf/SK arm tables are in [`paired_ab/`](paired_ab/report.md).

**Which measures were fixed in advance.** The proxies were chosen by the independent validation above
before any A/B result. The written pre-registration (2026-06-11) was committed after the raw arms had
run and before any reranked game finished; it named one primary proxy per arm for the reranked and
all-on arms (town vote accuracy for the town). The raw arm's results were therefore not *called shots*
(predictions written down before the data): they are reported with the multiplicity caveat below
([`paired_ab/experiment_log.md`](paired_ab/experiment_log.md), "Pre-registration").

**Town win rate rose on every town arm** (N=30 each; off = the same-epoch fresh baseline, 27% town win):

| Arm (memory on for) | When it ran | Town win off→on | Δ | McNemar p |
| --- | --- | --- | --- | --- |
| raw town | interleaved with the baseline | 27% → 43% | +17pp | 0.267 |
| reranked town | later the same day, after the baseline finished | 27% → 60% | +33pp | 0.013 |
| all-on (all roles) | later the same day, after the baseline finished | 27% → 50% | +23pp | 0.167 |

The direction is unanimous, but only the reranked arm's p is below 0.05, and that arm ran after the
baseline had finished, with no check for drift within the day (see *Confounds and rejected readings*);
the record does not rest on it. Win rate is underpowered at N=30 (see *The instruments*), so this table
reads as *consistent direction*, not three independent proofs. The endpoint is the decision-quality
basket on the **interleaved raw arm** (N=30, paired Wilcoxon):

| Proxy | off → on | Δ | p |
| --- | --- | --- | --- |
| healer town-save rate | 0.370 → 0.598 | +0.228 | **0.005** |
| correct-elimination rate | 0.470 → 0.638 | +0.168 | **0.028** |
| town mislynch rate | 0.530 → 0.362 | −0.168 | **0.036** |
| town vote accuracy | 0.560 → 0.710 | +0.149 | 0.053 |

Bold marks p<0.05 uncorrected; a Bonferroni line over three tests is 0.017. Three
of four move significantly and all four move the same way. Counted honestly, though, the four rows are
not four independent witnesses: correct-elimination and mislynch rate are exact complements (they divide
the same lynches two ways, so they are one test with two signs), and vote accuracy is the per-vote grain
of that same threat-identification construct. The basket's independent constructs are **two, threat
identification and healer protection, and both move in memory's favour**, with healer-save clearing the
three-test Bonferroni line. Over all 24 raw-arm tests (three arms by eight proxies) the strict line is
0.002, which no single result clears; about 7 of the 24 fell below 0.05 against about 1.2 expected by
chance. These are better town *decisions* on selected measures, not just luck; the win rate did not
move significantly.

## Side-findings that shaped later work

**No detectable deceiver benefit, with a mechanistic hypothesis, not a proven law.** In this A/B the
wolf arm is flat (win 33%→30%, p=1.000) and the SK arm trends down (win 40%→20%, p=0.146); neither
faction's proxies improve at N=30. One plausible reading is that town plays an inference game where
cross-game patterns compound, while wolf and SK play in-the-moment deception that static memory does not
sharpen. That is a hypothesis, not a finding: the arms are underpowered, and we entertained
iteration-specific theories at the time (retrieval precision, outcome framing, an adherence gap; see
[`paired_ab/`](paired_ab/report.md)). What *is* firm is the design consequence: outcome and decision
quality diverge most in the deceiver cells (a win can hide bad play, a loss good play), so v7's credit
design graded lessons by decision quality against the roles (de-lucked) rather than by win/loss.

**Reranking showed no measured advantage over raw, so it was deprioritised, not disproven.** Town
memory helps whether retrieval is raw or reranked, and the reranked-vs-raw contrast on town vote
accuracy is null (0.710→0.686, Wilcoxon p=0.518). At N=30 that is underpowered to exclude a small
effect, and the reranked arm also carries the drift caveat below, so sharper *ranking* is a
deprioritised lever, not a refuted one. This pointed v6 toward matching lessons by structured situation
fields (players alive, how close a side is to winning) rather than by text similarity alone, where v6
later found no gain either.

## Screening layer: per-decision replays

*Absorbed 2026-10-26 from [`decision_replay/report_screening_layer.md`](decision_replay/report_screening_layer.md).
The frozen-turn method (how a turn is rebuilt, scored and what any replay can and cannot show) is
explained once in [Replay screens](../../evaluation/evaluation_scopes/turn/report.md); this section keeps
what the memory screens found.*

**Why a second layer.** The paired A/B answers *whether* memory helps at the game level. It cannot
cheaply answer *why*, or *which* of a dozen candidate fixes is worth building: each whole-game arm costs
~$15–30 and is exposed to possible model drift between days. A decision replay freezes one recorded
decision, swaps **only** the retrieved-memory block, regenerates that one action and scores it against
the true roles. It is paired at the decision (role luck cancels), both arms run in one sitting (so drift
would hit both alike), and it needs no judge wherever the target is a role lookup. It trades statistical
power for speed and isolation: a pre-filter that kills dead levers for ~$1 before any reaches a
whole-game arm.

**What a screen can and cannot claim.** It sees *local* decision quality at a frozen board (direction
and mechanism), not trajectory, magnitude or win rate. So its findings are reported as **direction and
mechanism**, tiered, and the win-rate question stays with the A/B. We never headline a screen p-value. A
screen earns a claim two ways, both robust to small N: by showing the mechanism in the cell-level
breakdown, and by converging with an independent cut.

**Which store the screens used.** The screens below replayed decisions from a June 12 town arm that used
a variant of `v5_0`: the same 20 games re-extracted so that each observation's outcome leads with its
effect on the game's final result (**net-first framing**) rather than its immediate effect. They are not
replays of the June A/B's own store.

**Agreement with the A/B, and its limits.** The two layers were built independently and point the same
way:

| | paired A/B (whole game, N=30, `v5_0` store) | decision replay (per decision, net-first variant) |
| --- | --- | --- |
| town | decision basket significant on the raw arm (healer saves p=0.005, correct eliminations p=0.028); win +17pp raw (p=0.267) and +23pp all-on (p=0.167), not significant, direction only | +0.078 net value on day-2 votes, +0.117 in the endgame (helps) |
| wolf / SK | null | null |

*Takeaway: town memory helped and deceiver memory was null, by a whole-game test at N=30 (the decision
basket significant, win rate the underpowered direction) and by a per-decision test run in one sitting.
Both contradict an earlier −40pp "town collapse" in the net-first town arm, which the record attributes
to suspected drift between days, not to memory (the drift is suspected, not established; see the
2026-10-25 correction notes in [`paired_ab/experiment_log.md`](paired_ab/experiment_log.md)).* The
agreement is one of direction across two stores and two days, not a replication of the A/B's size. The
screen's role is convergent mechanism, not a standalone verdict, so its small per-cell N never has to
carry the headline.

**The cheap-lever ladder.** We used the screen to test, in sequence, every cheap way to make the agent
*use* memory better, before paying for an expensive content rebuild. All point the same way.

| lever | what changed | finding | tier |
| --- | --- | --- | --- |
| reorder / memory-link | emit the reasoning before the vote | syncs vote↔reasoning 75%→92.5% (N=40) but raises memory engagement ≈0 (judge-free echo, N=150) and can flip a *correct* vote to wrong on bad content | suggestive |
| force applicability | a forced per-memory "does this apply?" verdict | the model *can* reason about applicability: it separates situation match from lesson transfer (N=20); but forcing it *hurts* the vote (0.75→0.55) through over-caution | suggestive |
| outcome framing | rewrite each lesson net outcome → immediate outcome | **situation-dependent** (below) | suggestive |

*Takeaway: no single blanket setting (schema, instruction or framing) wins everywhere; the right call
flips with the situation.* The capability finding is the one to dwell on: the agent *can* judge which
memory applies, so the bottleneck was not capability. What hurts is forcing the deliberation, which makes
a weak model over-cautious; separating "can it" from "does it help" is what stopped us shipping a
plausible but harmful fix.

**The assumption that flipped.** Outcome framing first read as a clean null: N=40, immediate − net =
+0.025, p=1.0. But that sample came from day≥3, which the screen had already flagged as the zone where
the base prompt already covers the decision and memory ≈ no memory for **everything**, so a null there
says nothing about framing. Stratified, it flips:

| stratum | net (cautious) | immediate (actionable) | imm − net |
| --- | --- | --- | --- |
| day-2, info-starved (N=30) | **+0.10** (vs −0.067 off) | −0.067 | **−0.167** (4 worse / 0 better, p=0.125) |
| day-5+, endgame (N=20) | 0.30 | 0.20 | −0.10 (p=1.0) |

*Takeaway: at day 2 the cautious framing converts would-be mislynches into defensible abstains
(mislynch 0.23 → 0.07), and the "actionable" reframe undoes that, pushing the agent to vote when the
board has nothing to hit.* This is **direction and mechanism at N=30, p=0.125: a suggestive claim, not a
proven one.** Its sturdier half is the *"net helps at day 2"* leg, which reproduces the day-2 caution
benefit the screen's own stratification shows; the *"immediate hurts"* leg is the new directional bit.
We do **not** pool the strata to manufacture significance: the stratum split *is* the finding, and
pooling is what hid it the first time.

**What it screened to.** Every cheap lever is null or harmful, and the framing result shows *why*: the
best lesson depends on the situation, so no blanket framing can be right. The remaining lever was content
that carries the **condition** (be cautious when information is thin, act when the threat is clear). That
pointed to conditioned extraction, a whole-game step, rather than another cheap patch. The screen did its
job: it spent ~$1 per question to keep us from spending ~$20 confirming a dead lever.

**Lessons from the screen.**

- **A cheap paired screen earns its keep by triage, not significance.** Pairing cancels role luck and
  running both arms in one sitting exposes them to the same drift, so small N buys *direction*; the
  win-rate burden stays with whole games. Build screens to kill levers, not to prove them, and report
  them in that frame so a reader never mistakes a screen for a verdict.
- **Pooling hides structure, learned twice.** Pooling days hid the day-2 framing effect; pooling roles
  would hide the cell differences that are the finding. Stratify, report the cells, and let the
  cross-cell pattern (not any single significant cell) carry the weight.
- **Capability is not adoption.** A model can reason about a memory's applicability when forced to, yet
  doing so degrades the decision. Measuring "can it" separately from "does it help" is what distinguishes
  a real diagnosis from a plausible story.

**Provenance (screens).** Game and replay model `gemini-3.1-flash-lite` at temperature 1.0 (replays
match the games' model and temperature); adherence and coherence judges `gemini-2.5-pro` /
`gemini-2.5-flash` (used only off the headline path). Driver: `evaluation/src/studies/decision_replay.py`
(the screens ran it from its June path, `evaluation/src/experiments/`). Commits `d335d2c` → `b332550`.
Per-finding artifacts in [`decision_replay/`](decision_replay/) (`echo_*`, `coherence_*`,
`applicability_*`, `framing_*` JSONs); full reasoning trail in
[`decision_replay/experiment_log.md`](decision_replay/experiment_log.md).

## The pre-rebuild batches: historical ceiling, not a citable anchor

Before the `v5` rebuild, two unpaired 30-game batches on the old game established that memory *can* move
outcomes dramatically. They remain useful as a ceiling-and-sensitivity record, never as a current
number. Each cell is the villagers' win rate.

| Condition | Batch A (v3_deduped) | Batch B (v4 + action_phase) |
| --- | --- | --- |
| No memory | 70.0% (21/30) | 74.2% (23/31) |
| Wolf only | 87.1% (27/31) | 83.3% (25/30) |
| All enabled | **96.7%** (29/30) | 73.3% (22/30) |

Batch A's all-enabled lift (96.7% vs 70%, Fisher **p=0.012**) is the strongest single-batch signal in
the set: villagers went from losing one game in three to one in thirty. But it is the best cell of six
comparisons (Bonferroni-borderline, not decisive), and the *same* condition collapsed to baseline in
Batch B (73.3%, p=1.0) while two variables changed at once (store version and namespace granularity, that is, how finely
the store is split by role and phase).
So these show the ceiling memory can reach and that configuration can lose the entire benefit, nothing
tighter.

**A hard boundary applies:** the `v4→v5` rebuild changed the game itself (9 players, 3 factions, a
sequential scheduler), so comparing any Batch A/B figure to a `v5` figure is a category error. They are
context, never a comparator.

## Why the v6 A/B found no town effect

A later paired A/B on the v6 store (2026-06-17, N=30, its *own* fresh same-epoch baseline) found the
town arm with observations **flat** (villager win +6pp, p=0.77; decision-quality basket Δ≈0), which reads
at first like the store broke the benefit. The v6 store was rebuilt around structured situation fields.
It was not a replication of the June test: the v5 (06-11) and v6 (06-17) runs sit in **different
epochs**, with a different store and a changed prompt bundle, so the two cannot be compared directly.
The evidence below favours a risen baseline over a degraded store.

**One plausible reading: the no-memory baseline rose to memory's old ceiling.** Between the two runs the
prompt bundle changed (`16f7f700`→`1cb76993`, a round of play-prompt fixes), on top of the backend drift
suspected, not established, in the 06-11 epoch shift (re-tested as pairs: exact McNemar p = 0.18; see
[`paired_ab/experiment_log.md`](paired_ab/experiment_log.md)). The no-memory town proxies jumped
accordingly: vote accuracy 0.560→0.674, correct-elimination 0.470→0.622, mislynch rate 0.530→0.378, win
27%→37% (06-17 values recompute from `batch_results/v6ab_*.jsonl` `all_disabled`, N=30, re-verified
2026-07-05). The 06-17 *no-memory* baseline already plays at roughly the level `v5` memory had lifted
town *to*, so there was no headroom left to show: flat, not harmful.

**A same-epoch control finds the two stores alike.** An off-policy replay screen
([`../strategy_adoption/forced_schema_screen/`](../strategy_adoption/forced_schema_screen/experiment_log.md))
scores both stores in *one* epoch: v5-store 0.625 ≈ v6-store 0.604, both below the no-memory floor 0.667
(McNemar p=1.0). Even the `v5_0` store that "worked" reads flat in the later epoch, which fits the epoch
reading better than a fault in the v6 schema.

**One real but mild bug.** v6 applies net-first outcome framing to *town* as well as the deceivers
(`Agents/schemas/memory.py::_compose_outcome`), and v5 evidence shows that hurts town. But the town arm
came out flat, not below baseline, so it is a minor contributor, not the cause. Full analysis in
[`v6_sp_ab/experiment_log.md`](v6_sp_ab/experiment_log.md); store arc in the
[memory overview](../report.md).

## Confounds and rejected readings

Four threads sit behind the results. The second qualifies the town result; the others set method rules
or record readings that were rejected.

**The discarded historical-epoch baseline (a standing rule).** The original memory-off baseline
(villagers 67% / SK 27% / wolves 7%) came from an earlier epoch, and a fresh 10-game re-run of it
shifted systematically (Fisher **p=0.0028**) despite byte-identical play prompts. Silent Vertex-side
model drift was suspected, not established: on the 20 deals both baselines shared, tested as pairs,
villager wins fell from 12 to 7 (exact McNemar p = 0.18; see the re-test note in
[`paired_ab/experiment_log.md`](paired_ab/experiment_log.md)). We discarded it and re-ran the baseline
fresh inside the A/B's own epoch (villagers 27% / SK 40% / wolves 33%), which is the off-control every
table above uses. The rule this set: never pair against a historical-epoch baseline.

**Was the baseline a low draw? (added 2026-10-26).** Two facts in the record bear on it, and the record
does not separate them from a memory effect. Town measures also improved in the arms where only the
wolves or only the lone killer had memory and the town had none: town mislynch rate 0.530 → 0.406
(p = 0.042) and 0.530 → 0.343 (p = 0.029) ([`paired_ab/report.md`](paired_ab/report.md)); town memory
cannot explain those. And a canary of 10 memory-off games on the baseline's seeds the next day
(2026-06-12) played at town vote accuracy 0.699 and a 51% villager win, against the baseline's 0.560 and
27%, about the level the raw town arm reached with memory (0.710)
([`paired_ab/experiment_log.md`](paired_ab/experiment_log.md), "Phase A town-regression — conclusion").
Both fit a baseline that drew low, or drift between days (suspected, not established). Part of the raw
arm's gain may therefore reflect the baseline rather than town memory.

**The reranked arm's drift caveat (why we anchor on raw).** The one significant win rate (reranked town)
carries a risk the raw arm does not: the raw arm interleaved with the baseline in time, but the reranked
and all-on arms ran later the same day, after the baseline finished, with no intraday drift canary (that
arrived 06-12). Pairing cancels role-draw luck but not intraday drift, so anchoring the town verdict on
the interleaved raw arm's basket sidesteps the risk.

**The confounded v5_1 pilot (refuted).** An early pilot on `v5_1` (a store that grew as memory-on games
wrote back into it; unpaired; raw retrieval) suggested memory *hurt* town by −32pp (p=0.043). The paired
A/B refuted it: the collapse was the confound, a moving store and an old-epoch baseline, not memory. See
[`v5_baseline_proxy_analysis.md`](v5_baseline_proxy_analysis.md).

## Compounding: closed

Whether memory that *compounds* across generations helps *more over time* is a different question. Two
paid loop runs meant to answer it were both invalidated (a biased de-lucked baseline in one, a config
slip that ran the wrong arm in the other). A pre-registered endpoint run then tested it: 30 boards, each
played once with the loop's final memory and once without. The town's decision score was 0.147 lower
with memory, on 19 of the 30 boards (p ≈ 0.06), and, as committed, this was reported as "no compounding
detected", with the estimate leaning toward harm. The owner closed the memory research on 2026-07-21
without a further run. Closed is not disproved: the run detected no compounding, at this size and with
players that answered without a reasoning step. The pre-registration and result are in the
[v7 report](../v7/report.md), "The pre-registration" and "What the signed run found".

## Artifacts

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

**Provenance.** The A/B arms ran 2026-06-11 on `gemini-3.1-flash-lite` / Vertex, prompt bundle
`16f7f700`, store `memory_stores/v5_0` read-only (run flag `--no-memory-dump`). Every win rate and proxy
above was independently re-verified from `batch_results/ab_*.jsonl` on 2026-07-02 (own pairing and a
separate stats path).
