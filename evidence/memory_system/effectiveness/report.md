# Memory Effectiveness: Does Episodic Memory Improve Gameplay?

**Scope:** the one question that justifies the whole memory pipeline — does giving agents episodic
memory produce measurably better game outcomes? This is the current-truth hub for that answer. The
deciding experiment (a paired, seeded A/B on the frozen `v5_0` store) has run and closed the question
for *static* memory. **Companion docs:** the store's version-by-version arc is
[`../store_progression.md`](../store_progression.md); the full A/B statistics and design are in
[`paired_ab/`](paired_ab/report.md); the open *compounding* question lives in
[`../../execution_plan/compounding_measurement_plan.md`](../../execution_plan/compounding_measurement_plan.md).

**Provenance.** The A/B arms ran 2026-06-11 on `gemini-3.1-flash-lite` / Vertex, prompt_bundle
`16f7f700`, store `memory_stores/v5_0` (consumption mode, `--no-memory-dump`). Every win-rate and proxy
below was independently re-verified from `batch_results/ab_*.jsonl` on 2026-07-02 (own pairing + a
separate stats path).

## The verdict

- ✅ **Static memory measurably helps *town* play.** Proven by the `v5_0` paired A/B — the town
  decision-quality basket moves significantly on the clean interleaved raw arm, win-rate direction is
  consistent across every town arm.
- ✅ **Memory does *not* help the deceivers.** Wolf and serial-killer (SK) arms are null on win rate
  and on their proxies. Memory helps the inference game, not the deception game.
- ⚠️ **The benefit is epoch-sensitive, not store-fragile.** A later run on the v6 store did not
  replicate the town lift; the cause is a risen no-memory baseline between epochs, not a broken store
  (a same-epoch control exonerates the store).
- ❓ **Whether memory *compounds* across games is open.** Owned by the compounding measurement plan
  (linked above), not this report.

## The deciding experiment — the `v5_0` paired A/B

The earlier evidence (below) showed memory *can* move outcomes but left the current configuration
unresolved, so we ran the confound-killer: a **paired, seeded, same-epoch A/B**. Each of 30 boards is
played twice with *identical initial conditions* — same role draw, same RNG, same personas — differing
only in whether memory is on. Pairing on `game_id` cancels the dominant noise source in werewolf, the
luck of the setup (a wolf-favored draw, an easy or hard board), so a within-pair comparison isolates
the treatment. Binary win/loss is read with **McNemar** on the discordant pairs (both-win and both-lose
pairs carry no signal); dense proxies use a **paired Wilcoxon** on per-pair differences. The store is
the frozen `v5_0` in consumption mode (it cannot grow, so the treatment is constant), and arms cover
raw / reranked / all-on retrieval crossed with the town / wolf / SK factions. Full design and the
wolf/SK arm tables are in [`paired_ab/`](paired_ab/report.md).

One design note carries weight. The original memory-off baseline (villagers 67% / SK 27% / wolves 7%)
came from an earlier epoch, and a fresh 10-game re-run of it shifted systematically (Fisher **p=0.0028**)
despite byte-identical play prompts — most likely silent Vertex-side model drift. That baseline was
discarded and re-run fresh in the A/B's own epoch, giving a same-epoch off-control (villagers 27% / SK
40% / wolves 33%). This run set a standing rule: never pair against a historical-epoch baseline.

**Town win rate rises on every arm** (N=30 each; off = the same-epoch fresh baseline, 27% town win):

| Arm (memory on for) | Town win off→on | Δ | McNemar p |
|---|---|---|---|
| raw town | 27% → 43% | +17pp | 0.267 |
| reranked town | 27% → 60% | +33pp | **0.013** |
| all-on (all roles) | 27% → 50% | +23pp | 0.167 |

The direction is unanimous, but only the reranked arm's win rate reaches significance, and win rate is
underpowered at N=30 (the minimum detectable effect is ≈36pp). So the win-rate table is read as
*consistent direction*, not as three independent proofs. The load-bearing evidence is the
pre-registered town decision-quality basket on the **interleaved raw arm** (N=30, paired Wilcoxon):

| Proxy | off → on | Δ | p |
|---|---|---|---|
| healer town-save rate | 0.370 → 0.598 | +0.228 | **0.005** |
| correct-elimination rate | 0.470 → 0.638 | +0.168 | **0.028** |
| town mislynch rate | 0.530 → 0.362 | −0.168 | **0.036** |
| town vote accuracy | 0.560 → 0.710 | +0.149 | 0.053 |

Bold marks p<0.05 uncorrected; the Bonferroni line over the ≤3 pre-registered primaries is 0.017. Three of four move
significantly and all four move the same way. Healer-save clears even the Bonferroni line;
correct-elimination and mislynch-rate cluster just above it. Town memory is improving the town's
*decisions*, not just its luck.

### Why the raw basket is the anchor, not the +33pp win

The single significant win rate (+33pp, reranked, p=0.013) is *not* the citable headline, for two
reasons.

First, **power**: win rate at N=30 is underpowered (MDE ≈36pp), so a flat win rate here means
"underpowered," not "no effect." The basket is pre-registered, has more signal per game, and is
significant — it is the stronger instrument.

Second, **an unguarded temporal risk on the reranked arm specifically**. All arms ran the same day with
an identical `runtime_fingerprint`, but they did not all overlap the baseline in time. The raw arm
*interleaved* with the baseline (08:11–13:11); the reranked and all-on arms ran 12:57–18:31, after the
baseline had finished at 12:06. Pairing on `game_id` cancels role-draw luck but not intraday drift, and
06-11 had no intraday canary to detect drift (that discipline arrived 06-12). So the one significant
win rate carries a small unguarded drift risk that the interleaved raw arm does not. Anchoring on the
raw arm's basket sidesteps it.

A note on a retracted claim: an earlier portfolio headline read "+17pp, p=0.013." That was a fusion
error — the +17pp effect belongs to the raw arm (p=0.267), the p=0.013 to the reranked arm (+33pp). It
was corrected on 2026-07-02 and should never be re-cited in the fused form.

## Side-findings that shaped later work

**Memory does not help the deceivers.** The wolf arm is flat (wolf-faction win 33%→30%, p=1.000) and
the SK arm trends down (SK win 40%→20%, p=0.146); neither faction's proxies improve. Mechanistically this fits — town
plays an inference game where cross-game patterns compound, while wolf and SK play in-the-moment
generative deception that memory doesn't sharpen. This null is *why* v7's credit design de-lucks by
decision quality rather than win/loss: outcome and decision quality diverge most exactly in the
deceiver cells, where a win can hide bad play and a loss can hide good play.

**Reranking adds nothing over raw retrieval.** Town memory helps whether retrieval is raw or reranked,
and the reranked-vs-raw contrast on town vote accuracy is null (0.710→0.686, Wilcoxon p=0.518). Sharper
*ranking* is not the lever. This result pointed v6 away from fuzzy reranking and toward *structured*
criticality gating — testing whether exact numeric gating (not embedding similarity) was the missing
precision. (v6 later answered that too: no.)

## The pre-rebuild batches — historical ceiling, not a citable anchor

Before the `v5` rebuild, two unpaired 30-game batches on the old game established that memory *can* move
outcomes dramatically. They remain useful as a ceiling-and-sensitivity record, never as a current
number.

| Condition | Batch A (v3_deduped) | Batch B (v4 + action_phase) |
|---|---|---|
| No memory | 70.0% (21/30) | 74.2% (23/31) |
| Wolf only | 87.1% (27/31) | 83.3% (25/30) |
| All enabled | **96.7%** (29/30) | 73.3% (22/30) |

Batch A's all-enabled lift (96.7% vs 70%, Fisher **p=0.012**) is the strongest single-batch signal in
the set — villagers went from losing one game in three to one in thirty. **Multiplicity caveat:** it is
the best cell of six condition-batch comparisons, so under a Bonferroni-style correction p=0.012 is
borderline, not decisive. And the *same* all-enabled condition collapsed to baseline in Batch B
(73.3%, p=1.0), which changed two variables at once (store version and namespace granularity) — a
confound the batches cannot resolve. So these show the ceiling memory can reach and that configuration
can lose the entire benefit, nothing tighter.

**A hard boundary applies:** the `v4→v5` rebuild changed the game itself — 9 players, 3 factions, a
sequential scheduler — so these numbers do not transfer, and comparing any Batch A/B figure to a `v5`
figure is a category error. They are context, never a comparator.

## Why the v6 store did not replicate the town lift

A later paired A/B on the v6 dimension store (2026-06-17, N=30 boards, run against its *own* fresh
same-epoch baseline) found town-obs **flat** (villager win +6pp, p=0.77; the decision-quality basket
Δ≈0), which reads at first like the store broke the benefit.
It did not. The v5 A/B (06-11) and the v6 run (06-17) sit in **different epochs**, and the confound is a
risen baseline, not a degraded store.

**The dominant cause — the no-memory baseline rose to memory's old ceiling.** Between the two runs the
prompt bundle changed (`16f7f700`→`1cb76993`, Phase-B prompt fixes), on top of the backend drift the
06-11 epoch-shift finding already demonstrated. The no-memory town proxies jumped accordingly: vote
accuracy 0.560→0.674, correct-elimination 0.470→0.622, mislynch rate 0.530→0.378, win 27%→37% (the
06-11 values are the OFF columns in `paired_ab/report.md`; the 06-17 values recompute from the
`batch_results/v6ab_*.jsonl` `all_disabled` arm, N=30 — re-verified 2026-07-05). The 06-17 *no-memory*
baseline already plays at roughly the level `v5` memory had lifted town *to*, so there was no headroom
left to show — flat, not harmful.

**A same-epoch control exonerates the store.** An off-policy replay screen
([`../../phase_b/forced_schema_screen/`](../../phase_b/forced_schema_screen/experiment_log.md)) scores
the v5 and v6 stores in *one* epoch: v5-store 0.625 ≈ v6-store 0.604, both below the no-memory floor
0.667 (paired McNemar p=1.0). Even the `v5_0` store that "worked" reads flat in the later epoch, so the
flatness is the epoch, not the schema.

**One real but mild bug.** v6 applies net-first outcome framing to *town* as well as the deceivers. The
`_compose_outcome` helper (`Agents/schemas/memory.py:41-49`) always leads with the end-of-game verdict,
and the role-aware immediate-first compose that town wants was specified but deferred. v5 evidence shows
net-first framing hurts town, so this is a genuine drag — but town-obs came out flat, not below
baseline, so it is a minor contributor, not the cause. The fix is to implement the deferred role-aware
compose. (The `v6` non-replication is analyzed in full in
[`v6_sp_ab/experiment_log.md`](v6_sp_ab/experiment_log.md); the store-arc framing is in
[`../store_progression.md`](../store_progression.md).)

A note on the pilot that preceded all this: an early confounded `v5_1` pilot (unpaired, growing store,
raw retrieval) suggested memory *hurt* town by −32pp (p=0.043). The paired A/B refuted it — the collapse
was the confound, not memory. See [`v5_baseline_proxy_analysis.md`](v5_baseline_proxy_analysis.md).

## What remains open

Static memory helps town; whether memory that *compounds* across generations helps *more over time* is a
different question and is unresolved. Two paid loop runs meant to answer it were both invalidated (a
biased de-lucked baseline in one, a config slip that ran the wrong arm in the other), so the compounding
magnitude is open, not negative. The plan of record — claim ladder, power/MDE calc, and the readout
redesign that gates any further paid runs — is
[`../../execution_plan/compounding_measurement_plan.md`](../../execution_plan/compounding_measurement_plan.md).

## Artifacts

The A/B statistics live in [`paired_ab/`](paired_ab/report.md); the pre-rebuild JSONLs and the stats
regenerator are co-located here.

| File | Description |
|------|-------------|
| `paired_ab/report.md` | Full `v5_0` A/B stats — all arms (town/wolf/SK × raw/reranked/all-on), pre-registered called shots |
| `paired_ab/experiment_log.md` | A/B design, epoch-drift finding, seed set, wolf/SK diagnostics |
| `batch_results/ab_*.jsonl` (repo root) | Paired A/B raw results: `ab_baseline`, `ab_arms_{town,wolf,sk}`, `ab_rr_*`, `ab_allon` |
| `v6_sp_ab/experiment_log.md` | v6 non-replication A/B (6 arms) + cross-epoch analysis |
| `regenerate_stats.py` | Recomputes every p-value/CI for the pre-rebuild batches from the JSONLs (uses `evaluation/src/core/stats.py`) — no hand-typed statistics |
| `batch_results/werewolf_flashlite_3_v1.jsonl` | Batch A: no_memory (30) + wolf_only (31), v3_deduped store |
| `batch_results/werewolf_flashlite_3_v1_deduped.jsonl` | Batch A: all_enabled (30), v3_deduped store |
| `batch_results/v4_action_phase_v2.jsonl` | Batch B: no_memory, v4 store with action_phase |
| `batch_results/v4_action_phase_v2_wolf_only_all_enabled.jsonl` | Batch B: wolf_only (30), v4 store |
| `batch_results/v4_action_phase_v2_all_enabled_remainder.jsonl` | Batch B: all_enabled remainder (18), v4 store |
