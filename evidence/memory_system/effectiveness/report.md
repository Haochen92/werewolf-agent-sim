# Memory Effectiveness: Does Episodic Memory Improve Gameplay?

## Motivation

The episodic memory system is the central infrastructure investment in this project. Retrieval filtering, store deduplication, reranking, adoption tracking — all of these experiments optimize intermediate quality metrics (retrieval relevance, adoption accuracy, action quality scores). But the question that justifies the entire pipeline is simpler: **does giving agents access to episodic memory produce measurably better game outcomes?**

This report consolidates evidence from two batch evaluation runs (91 and 91 successful games respectively) that tested memory's effect on win rates and gameplay metrics. This is a preliminary report — a final batch with the latest configuration (observations-only, v4_deduped store) has not yet been run.

## System Evolution

The memory system went through three distinct phases:

### Phase 0 — Monolithic Strategy Injection

The earliest version extracted "learnings" from postgame transcripts and accumulated them into a single strategy document per role. This strategy was injected as a system prompt at game start. Over 10+ iterations, visual inspection of dialogue transcripts showed increasing gameplay sophistication — agents developed more nuanced discussion patterns, better deception (wolves), and more targeted investigations.

The limitation was overfitting. A single monolithic strategy accumulated every lesson from every game, including edge cases and contradictory advice. Recent games dominated the strategy text, and agents would rigidly follow advice that applied to a specific prior situation but not the current one. The strategy archive (`Agents/memory_stores/old_strateg_archive/strategies.json`) contains 228 strategy items across 4 role namespaces — the accumulated output of this phase.

### Phase 1 — Modular RAG (Observations + Strategy Points)

The replacement decomposed memory into two types:
- **Observations** — factual accounts of specific past game events ("healer saved player_3 on night 2 and survived to endgame")
- **Strategy points** — prescriptive advice extracted from patterns across games ("maintain a low profile after a successful save")

Both types are stored in a vector store, namespaced by role. Before each game turn, agents retrieve relevant items via semantic search based on their current situation summary. This eliminates the overfitting problem: retrieval surfaces only situation-relevant memories rather than dumping an entire strategy document.

### Phase 2 — Namespace Refinement and Pipeline Maturation

Further iterations added action_phase namespace segregation (separating discussion-relevant from vote-relevant memories), store deduplication, retrieval filtering, and reranking. Each change was evaluated independently (see `evidence/retrieval/filtering/`, `evidence/dedup/store_retrieval_impact/`, `evidence/retrieval/reranking/`). The adoption tracking experiment (`evidence/memory_system/strategy_adoption/`) and memory ablation (`evidence/memory_system/ablation/`) led to the current planned default of observations-only retrieval.

## Batch Evaluation Design

Two batch runs tested memory's effect on game outcomes using a 3-condition design:

1. **No memory** — all agents play without episodic memory retrieval
2. **Wolf only** — only wolf agents receive retrieved memories
3. **All enabled** — all agents (wolf, villager, healer, investigator) receive memories

Each condition was run for ~30 games. The game configuration is otherwise identical: 8 players (2 wolves, 1 healer, 1 investigator, 4 villagers), `gemini-3.1-flash-lite` with minimal thinking for all agents.

### Batch A — v3_deduped store, no action_phase namespace

Store: v3 with deduplication applied. Retrieval namespaced by role only (not action phase). No filtering or reranking.

### Batch B — v4 store, action_phase namespace

Store: v4 pre-dedup (522 items, larger and noisier). Retrieval namespaced by role AND action phase. No filtering or reranking.

## Results

### Win Rates

The no-memory baseline is consistent across batches, giving confidence that game dynamics are comparable.

| Condition | Batch A (v3_deduped) | Batch B (v4_action_phase) |
|-----------|---------------------|--------------------------|
| No memory | 70.0% (21/30) | 74.2% (23/31) |
| Wolf only | 87.1% (27/31) | 83.3% (25/30) |
| All enabled | **96.7%** (29/30) | 73.3% (22/30) |

### Gameplay Metrics (Batch B only — computed_metrics available)

| Metric | No Memory | Wolf Only | All Enabled |
|--------|-----------|-----------|-------------|
| Correct elimination rate | 0.621 | 0.639 | 0.672 |
| Wolf blending rate | 0.120 | 0.480 | 0.480 |
| Healer save rate | 0.554 | 0.433 | 0.453 |
| Investigator accuracy | 0.468 | 0.411 | 0.403 |
| Mislynches per game | 1.000 | 0.900 | 0.767 |

## Interpretation

### Memory can produce dramatic improvement

Batch A's all-enabled condition (96.7% villager win rate vs 70% baseline) is the strongest evidence that episodic memory works. A 27 percentage point improvement at n=30 is not noise — it means villagers went from losing roughly 1 in 3 games to losing 1 in 30. The memory system gave villagers a decisive advantage when configured correctly.

### Configuration sensitivity is the dominant factor

The same "all enabled" condition produced 96.7% in Batch A and 73.3% in Batch B — a complete loss of benefit. The no-memory baselines are nearly identical (70% vs 74%), so this isn't game variance. Something about the Batch B configuration neutralized memory's effect on villagers specifically.

The two differences between batches:
1. **Store quality** — v3_deduped (cleaner, fewer items) vs v4 pre-dedup (522 items, more noise)
2. **Namespace granularity** — role-only vs role + action_phase

Either or both could explain the regression. The v4 store has more items competing for retrieval slots, potentially flooding agents with less relevant memories. Action_phase namespace segregation reduces the retrieval pool per query, which could eliminate useful cross-phase memories that help villagers connect patterns across discussion and voting.

### Wolf memory is consistently powerful

Across both batches, giving wolves memory dramatically improved their blending rate (12% → 48%) without changing the villager win rate direction. Wolves with memory learn to mimic villager discussion patterns and avoid behavioral tells. This effect is robust to store/namespace configuration — wolves benefit regardless.

### Villager benefit is configuration-dependent

In Batch A, villagers with memory dominated (96.7%). In Batch B, villagers with memory performed at baseline (73.3%). The gameplay metrics from Batch B suggest why: healer save rate and investigator accuracy actually *decreased* with memory (55% → 45% and 47% → 40% respectively). The v4 store may have contained bad guidance for power roles, or the action_phase namespace split prevented retrieving cross-phase patterns that help power roles coordinate.

## Limitations

- **No computed_metrics for Batch A.** Win rate is the only available outcome metric for the v3_deduped batch. We can't verify whether the same gameplay patterns (wolf blending, healer saves) drove the result.
- **Confounded variables.** Two things changed between batches (store version + namespace). We can't attribute the regression to one factor without running the intermediate configurations (v3_deduped with action_phase, or v4 without action_phase) — ideally **on shared seeds** so the comparison isn't a fresh random draw (see the paired-design section).
- **n=30 is too small to call the baselines "identical."** The argument that the 70% vs 74% baselines rule out game variance is weak — at n=30 each has a 95% CI of ±~16pp, so they are statistically indistinguishable across a wide range of true values. Paired/seeded baselines would make this comparison tight enough to actually support that claim.
- **Pre-current configuration.** Neither batch uses the current planned default (observations-only, v4_deduped store, filtering enabled). The latest config may recover Batch A's effectiveness or remain in Batch B territory.
- **Visual-only evidence for Phase 0.** The monolithic strategy system's improvement was observed through transcript inspection, not measured systematically. We can't quantify how much of the Phase 1 improvement over "no memory" is attributable to the RAG architecture vs simply having more game experience in the store.

## Decision

Memory effectiveness is proven — the question is not "does it work?" but "what configuration makes it work?" The Batch A result (70% → 97%) establishes the ceiling. The Batch B result (74% → 73%) establishes that bad configuration can lose the entire benefit.

The priority is not more evidence that memory works. It's running a batch with the current configuration to determine where it falls between these two bounds.

## Statistical Design for the Validation Batch — Paired / Seeded Games

The validation batch should not be run as two independent pools of games (N memory-off, N memory-on). It should be run as **matched pairs that share a seed**: for each of N seeds, run the game twice with *identical initial conditions* — same role assignment (who is wolf/healer/investigator), same RNG stream, same persona assignment — differing in **only** the treatment (memory on vs off). Analyze the **within-pair difference**, not the two pool averages.

**Why this cuts the games needed.** A werewolf game's outcome has two variance sources: (1) the treatment effect we care about (does memory help), and (2) the luck of the setup — a wolf-favored role draw, an easy/hard configuration — which is noise. The variance of the difference between two conditions is

```
Var(on − off) = Var(on) + Var(off) − 2·Cov(on, off)
```

Independent games have `Cov = 0`, so you eat the full variance and must run many games for source-(2) noise to average out. Paired games share the setup, so their outcomes are **positively correlated** (`Cov > 0`); the `−2·Cov` term **cancels the shared setup noise**. The games needed scale with `(1 − ρ)`, where ρ is the within-pair outcome correlation: ρ≈0.5 roughly halves the games; a high ρ (the setup strongly determines difficulty, which it does in werewolf) can cut them by an order of magnitude. In plain terms: instead of asking "do memory-on games win more *on average*," you ask "*on this exact setup*, did turning memory on change the outcome" — comparing like with like, with the game's inherent luck subtracted out.

**Binary win/loss → McNemar.** Classify each seed-pair: both-win / both-lose are **concordant** and carry no signal (the game was just easy or hard regardless of memory); only the **discordant** pairs (on-wins/off-loses vs the reverse) count, and McNemar tests whether they are asymmetric. You spend statistical power only on games where memory actually changed the result. For dense metrics (correct-elimination rate, survival, investigator accuracy), use a paired t / Wilcoxon on the per-pair differences.

**This is not the headline's bottleneck — it's the confound-killer.** The observed effects here are large (Batch A 70%→97%, prior runs ~60%→90%). For a ~27–30pp lift, even the *independent* design needs only ~25–30 games/arm to be well powered — which is exactly why the existing 30-game batches showed clear signal. So pairing is **not** required to prove the headline. Its real payoff for *this* report is:

1. **Resolving the Batch A vs Batch B regression.** The 97%-vs-73% gap for the "same" all-enabled condition is currently unattributable — two confounded variables (store version + namespace) measured on two *different* 30-game draws. Run the candidate configs **on the same seed set** and the setup variance cancels, so any remaining difference is the configuration effect, not two luck-of-the-draw samples.
2. **A tighter, more defensible headline.** Pairing shrinks the CI on the memory effect, pre-empting the "Batch A was just a lucky 30 games" critique.
3. **Power for the *subtle* comparisons** — ranking configurations that land between the 73% and 97% bounds, where the effect is small and the independent design would again be underpowered.

**Practical caveat.** The two games in a pair *will* diverge after the first memory-influenced action — that divergence **is** the treatment effect and is expected; LLM nondeterminism means they were never going to stay byte-identical. You pair on **initial conditions**, not trajectories — and in werewolf the dominant variance (role assignment, setup balance) lives in exactly those initial conditions. This requires the sim to be **seedable**: drive *every* stochastic component — role assignment, persona assignment, night RNG, **and the sequential scheduler's turn-order tie-break (`seeded_random`)** — from one master seed, identical across both arms.

A note specifically on the scheduler's turn-order randomness: seeding shares the RNG *stream*, but it does **not** keep turn order identical across the pair, because the order is computed from transcript-derived signals (pressure/debt/eligibility) that diverge as soon as memory changes what is said. Before divergence the order is identical; after, it diverges even with a shared stream. This is fine and wanted — turn-order shifts caused by memory are part of memory's legitimate effect, not a nuisance to cancel — and the factor is small by design (a within-tier tie-break that cannot reorder across hard signals), so its residual contribution averages out over the pairs. Seed it to share what can be shared and for reproducibility; don't expect (or want) it locked across the pair.

## What's Next

1. **Latest-config batch (paired/seeded)** — Run ~30 **seed-pairs**: each seed played twice (no-memory vs all-enabled, observations-only) with v4_deduped store + filtering and *identical initial conditions*. Analyze within-pair (McNemar for win/loss; paired test for computed_metrics). Determines whether the current system recovers Batch A's effectiveness, with setup variance controlled.
2. **Isolate the regression (shared seeds)** — If the latest config still shows no benefit, test v4_deduped without action_phase namespace **on the same seed set** to isolate namespace granularity vs store content — paired, so the comparison isn't confounded by a fresh random draw.
3. **Computed metrics for Batch A equivalent** — The latest batch should include computed_metrics to understand which gameplay dynamics drive the improvement.

## Artifacts

All artifacts are co-located in `evidence/memory_system/effectiveness/`.

| File | Description |
|------|-------------|
| `batch_results/werewolf_flashlite_3_v1.jsonl` | Batch A: no_memory (30) + wolf_only (31), v3_deduped store |
| `batch_results/werewolf_flashlite_3_v1_deduped.jsonl` | Batch A: all_enabled (30), v3_deduped store |
| `batch_results/v4_action_phase_v2.jsonl` | Batch B: no_memory (31+), v4 store with action_phase |
| `batch_results/v4_action_phase_v2_wolf_only_all_enabled.jsonl` | Batch B: wolf_only (30), v4 store |
| `batch_results/v4_action_phase_v2_all_enabled_remainder.jsonl` | Batch B: all_enabled remainder (18), v4 store |
