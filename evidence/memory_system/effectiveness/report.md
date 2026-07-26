# Memory Effectiveness: Does Episodic Memory Improve Gameplay?

**Scope:** the one question that justifies the whole memory pipeline — does giving agents episodic
memory produce measurably better game outcomes? This is the current-truth hub for that answer. The
deciding experiment — a paired, seeded A/B on the frozen `v5_0` store — establishes that *static* memory
improves **town decision quality**: the pre-registered proxy basket moves significantly on the clean
interleaved raw arm, while the win-rate direction is consistent but underpowered at N=30, so it
corroborates the direction rather than proving the magnitude. **Companion docs:** the store's
version-by-version arc is
[`../store_progression.md`](../store_progression.md); the full A/B statistics and design are in
[`paired_ab/`](paired_ab/report.md); the open *compounding* question lives in
[`../../execution_plan/compounding_measurement_plan.md`](../../execution_plan/compounding_measurement_plan.md).

**Provenance.** The A/B arms ran 2026-06-11 on `gemini-3.1-flash-lite` / Vertex, prompt_bundle
`16f7f700`, store `memory_stores/v5_0` (consumption mode, `--no-memory-dump`). Every win-rate and proxy
below was independently re-verified from `batch_results/ab_*.jsonl` on 2026-07-02 (own pairing + a
separate stats path).

## The verdict

- ✅ **Static memory measurably improves *town* decision quality.** On the frozen `v5_0` store, the
  pre-registered decision-quality basket moves significantly on the clean interleaved raw arm (N=30).
  Win-rate direction is consistent across every town arm, though win rate alone is underpowered at this N.
- ⚪ **No detectable wolf or serial-killer (SK) benefit in this A/B.** At N=30 the wolf and SK arms are
  null on win rate and proxies. Not the final word: a later v7 loop run gave a tentative wolf-side
  positive for *compounding* memory (from a run invalidated for its own primary question, so tentative
  only), and a dedicated wolf arm is planned in the compounding measurement plan (linked above).
- ⚠️ **The benefit is epoch-sensitive, not store-fragile.** A later run on the v6 store did not
  replicate the town lift; the cause is a risen no-memory baseline between epochs, not a broken store
  (a same-epoch control exonerates the store).
- ❓ **Whether memory *compounds* across games is open.** Owned by the compounding measurement plan
  (linked above), not this report.

## The instruments — how we measure "outcome"

Two rulers measure whether memory helped; the report leans on the second.

**Win rate** is the obvious ruler and the weak one: one binary win/loss per game, dominated by setup
luck (a wolf-favored draw can decide a game before anyone reasons well). At N=30 the minimum detectable
effect is ≈36pp, so a flat win rate means "underpowered to detect," not "no effect." It corroborates
direction but rarely reaches significance.

**The town decision-quality basket** is the primary endpoint. Each proxy is graded mechanically against
the true hidden roles — correct-elimination, mislynch, healer save of the real night target, vote
accuracy — so it measures *decisions, not luck* by construction, and yields several graded events per
game rather than one bit. It was validated separately: each proxy tracks its faction's win at
|r|≈0.55–0.65, p<0.01, in both pooled and treatment-free views
([`../../metrics/proxy_win_monotonicity.md`](../../metrics/proxy_win_monotonicity.md)). That is why the
basket is the endpoint and win rate the directional co-read.

## The deciding experiment — the `v5_0` paired A/B

The earlier evidence (below) showed memory *can* move outcomes but left the current configuration
unresolved. To remove the setup-luck confound, we ran a paired, seeded, same-epoch A/B. Each of 30
boards is played twice under identical initial conditions, differing only in whether memory is on.

Pairing on `game_id` pins the board setup — the role draw and the scheduler's turn-order tie-breaks,
both seeded from `game_id`. It does *not* pin the LLM's sampling
nondeterminism, which stays as within-pair noise; the paired tests average over it across the 30 pairs
(**McNemar** on discordant win/loss pairs, a paired **Wilcoxon** on per-pair proxy differences). Setup
luck is the noise source we argue dominates in werewolf, so holding it fixed is what isolates the
treatment. The store is the frozen `v5_0` in consumption mode (it cannot grow, so the treatment is
constant); arms cross raw / reranked / all-on retrieval with the town / wolf / SK factions. Full design
and the wolf/SK arm tables are in [`paired_ab/`](paired_ab/report.md).

**Town win rate rises on every arm** (N=30 each; off = the same-epoch fresh baseline, 27% town win):


| Arm (memory on for) | Town win off→on | Δ    | McNemar p |
| ------------------- | ---------------- | ----- | --------- |
| raw town            | 27% → 43%       | +17pp | 0.267     |
| reranked town       | 27% → 60%       | +33pp | **0.013** |
| all-on (all roles)  | 27% → 50%       | +23pp | 0.167     |

The direction is unanimous, but only the reranked arm reaches significance, and win rate is underpowered
at N=30 (see *The instruments*). So this table reads as *consistent direction*, not three independent
proofs. The primary endpoint is the pre-registered decision-quality basket on the **interleaved raw
arm** (N=30, paired Wilcoxon):


| Proxy                    | off → on      | Δ      | p         |
| ------------------------ | -------------- | ------- | --------- |
| healer town-save rate    | 0.370 → 0.598 | +0.228  | **0.005** |
| correct-elimination rate | 0.470 → 0.638 | +0.168  | **0.028** |
| town mislynch rate       | 0.530 → 0.362 | −0.168 | **0.036** |
| town vote accuracy       | 0.560 → 0.710 | +0.149  | 0.053     |

Bold marks p<0.05 uncorrected; the Bonferroni line over the ≤3 pre-registered primaries is 0.017. Three of four move
significantly and all four move the same way. Counted honestly, though, the four rows are not four
independent witnesses: correct-elimination and mislynch rate are exact complements (they divide the same
lynches two ways, so they are one test with two signs), and vote accuracy is the per-vote grain of that
same threat-identification construct. The basket's independent constructs are **two — threat
identification and healer protection — and both move in memory's favor**, with healer-save clearing even
the Bonferroni line. Town memory is improving the town's *decisions*, not just its luck. (The basket is the powered primary; the single significant win rate — reranked town — carries a drift caveat, so we anchor on the raw arm; see *Confounds and rejected readings*.)

## Side-findings that shaped later work

**No detectable deceiver benefit — with a mechanistic hypothesis, not a proven law.** In this A/B the
wolf arm is flat (win 33%→30%, p=1.000) and the SK arm trends down (win 40%→20%, p=0.146); neither
faction's proxies improve at N=30. One plausible reading is that town plays an inference game where
cross-game patterns compound, while wolf and SK play in-the-moment deception that static memory does not
sharpen. That is a hypothesis, not a finding: the arms are underpowered, we entertained iteration-
specific theories at the time (retrieval precision, myopic framing, an adherence gap; see
[`paired_ab/`](paired_ab/report.md)), and the tentative wolf-side positive from the later v7 loop run
argues for holding the door open. What *is* firm is the design consequence: outcome and decision quality
diverge most in the deceiver cells (a win can hide bad play, a loss good play), so v7's credit design
de-lucks by decision quality rather than win/loss.

**Reranking showed no measured advantage over raw — so it was deprioritized, not disproven.** Town
memory helps whether retrieval is raw or reranked, and the reranked-vs-raw contrast on town vote
accuracy is null (0.710→0.686, Wilcoxon p=0.518). At N=30 that is underpowered to exclude a small
effect, and the reranked arm also carries the drift caveat below, so sharper *ranking* is a
deprioritized lever, not a refuted one. This pointed v6 toward *structured* criticality gating — exact
numeric gating rather than embedding similarity — where v6 later found no gain either.

## The pre-rebuild batches — historical ceiling, not a citable anchor

Before the `v5` rebuild, two unpaired 30-game batches on the old game established that memory *can* move
outcomes dramatically. They remain useful as a ceiling-and-sensitivity record, never as a current
number.


| Condition   | Batch A (v3_deduped) | Batch B (v4 + action_phase) |
| ----------- | -------------------- | --------------------------- |
| No memory   | 70.0% (21/30)        | 74.2% (23/31)               |
| Wolf only   | 87.1% (27/31)        | 83.3% (25/30)               |
| All enabled | **96.7%** (29/30)    | 73.3% (22/30)               |

Batch A's all-enabled lift (96.7% vs 70%, Fisher **p=0.012**) is the strongest single-batch signal in
the set — villagers went from losing one game in three to one in thirty. But it is the best cell of six
comparisons (Bonferroni-borderline, not decisive), and the *same* condition collapsed to baseline in
Batch B (73.3%, p=1.0) while two variables changed at once (store version and namespace granularity).
So these show the ceiling memory can reach and that configuration can lose the entire benefit, nothing
tighter.

**A hard boundary applies:** the `v4→v5` rebuild changed the game itself (9 players, 3 factions, a
sequential scheduler), so comparing any Batch A/B figure to a `v5` figure is a category error. They are
context, never a comparator.

## Why the v6 store did not replicate the town lift

A later paired A/B on the v6 dimension store (2026-06-17, N=30, its *own* fresh same-epoch baseline)
found town-obs **flat** (villager win +6pp, p=0.77; decision-quality basket Δ≈0), which reads at first
like the store broke the benefit. It did not: the v5 (06-11) and v6 (06-17) runs sit in **different
epochs**, and the confound is a risen baseline, not a degraded store.

**The dominant cause — the no-memory baseline rose to memory's old ceiling.** Between the two runs the
prompt bundle changed (`16f7f700`→`1cb76993`, Phase-B prompt fixes), on top of the backend drift the
06-11 epoch-shift finding already demonstrated. The no-memory town proxies jumped accordingly: vote
accuracy 0.560→0.674, correct-elimination 0.470→0.622, mislynch rate 0.530→0.378, win 27%→37%
(06-17 values recompute from `batch_results/v6ab_*.jsonl` `all_disabled`, N=30, re-verified 2026-07-05).
The 06-17 *no-memory* baseline already plays at roughly the level `v5` memory had lifted town *to*, so
there was no headroom left to show — flat, not harmful.

**A same-epoch control exonerates the store.** An off-policy replay screen
([`../strategy_adoption/forced_schema_screen/`](../strategy_adoption/forced_schema_screen/experiment_log.md)) scores
both stores in *one* epoch: v5-store 0.625 ≈ v6-store 0.604, both below the no-memory floor 0.667
(McNemar p=1.0). Even the `v5_0` store that "worked" reads flat in the later epoch — the flatness is the
epoch, not the schema.

**One real but mild bug.** v6 applies net-first outcome framing to *town* as well as the deceivers
(`_compose_outcome`, `Agents/schemas/memory.py:41-49`), and v5 evidence shows that hurts town. But
town-obs came out flat, not below baseline, so it is a minor contributor, not the cause. Full analysis
in [`v6_sp_ab/experiment_log.md`](v6_sp_ab/experiment_log.md); store arc in
[`../store_progression.md`](../store_progression.md).

## Confounds and rejected readings

Three investigation threads sit behind the results; they set method rules but do not change the verdict.

**The discarded historical-epoch baseline (a standing rule).** The original memory-off baseline
(villagers 67% / SK 27% / wolves 7%) came from an earlier epoch, and a fresh 10-game re-run of it
shifted systematically (Fisher **p=0.0028**) despite byte-identical play prompts — most likely silent
Vertex-side model drift. We discarded it and re-ran the baseline fresh inside the A/B's own epoch
(villagers 27% / SK 40% / wolves 33%), which is the off-control every table above uses. The rule this
set: never pair against a historical-epoch baseline.

**The reranked arm's drift caveat (why we anchor on raw).** The one significant win rate (reranked town,
+33pp) carries a risk the raw arm does not: the raw arm interleaved with the baseline in time, but the
reranked and all-on arms ran later the same day, after the baseline finished, with no intraday drift
canary (that arrived 06-12). Pairing cancels role-draw luck but not intraday drift, so anchoring the
town verdict on the interleaved raw arm's basket sidesteps the risk.

**The confounded v5_1 pilot (refuted).** An early v5_1 pilot (unpaired, growing store, raw retrieval)
suggested memory *hurt* town by −32pp (p=0.043). The paired A/B refuted it: the collapse was the
confound, a moving store and an old-epoch baseline, not memory. See
[`v5_baseline_proxy_analysis.md`](v5_baseline_proxy_analysis.md).

## What remains open

Whether memory that *compounds* across generations helps *more over time* is a different, unresolved
question. Two paid loop runs meant to answer it were both invalidated (a biased de-lucked baseline in
one, a config slip that ran the wrong arm in the other), so the magnitude is open, not negative. The
plan of record (claim ladder, power/MDE calc, and the readout redesign that gates any further paid runs)
is [`../../execution_plan/compounding_measurement_plan.md`](../../execution_plan/compounding_measurement_plan.md).

## Artifacts

The A/B statistics live in [`paired_ab/`](paired_ab/report.md); the pre-rebuild JSONLs and the stats
regenerator are co-located here.


| File                                                           | Description                                                                                                                              |
| -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `paired_ab/report.md`                                          | Full`v5_0` A/B stats — all arms (town/wolf/SK × raw/reranked/all-on), pre-registered called shots                                      |
| `paired_ab/experiment_log.md`                                  | A/B design, epoch-drift finding, seed set, wolf/SK diagnostics                                                                           |
| `batch_results/ab_*.jsonl` (repo root)                         | Paired A/B raw results:`ab_baseline`, `ab_arms_{town,wolf,sk}`, `ab_rr_*`, `ab_allon`                                                    |
| `v6_sp_ab/experiment_log.md`                                   | v6 non-replication A/B (6 arms) + cross-epoch analysis                                                                                   |
| `regenerate_stats.py`                                          | Recomputes every p-value/CI for the pre-rebuild batches from the JSONLs (uses`evaluation/src/core/stats.py`) — no hand-typed statistics |
| `batch_results/werewolf_flashlite_3_v1.jsonl`                  | Batch A: no_memory (30) + wolf_only (31), v3_deduped store                                                                               |
| `batch_results/werewolf_flashlite_3_v1_deduped.jsonl`          | Batch A: all_enabled (30), v3_deduped store                                                                                              |
| `batch_results/v4_action_phase_v2.jsonl`                       | Batch B: no_memory, v4 store with action_phase                                                                                           |
| `batch_results/v4_action_phase_v2_wolf_only_all_enabled.jsonl` | Batch B: wolf_only (30), v4 store                                                                                                        |
| `batch_results/v4_action_phase_v2_all_enabled_remainder.jsonl` | Batch B: all_enabled remainder (18), v4 store                                                                                            |
