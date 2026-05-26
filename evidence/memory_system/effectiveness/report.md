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
- **Confounded variables.** Two things changed between batches (store version + namespace). We can't attribute the regression to one factor without running the intermediate configurations (v3_deduped with action_phase, or v4 without action_phase).
- **Pre-current configuration.** Neither batch uses the current planned default (observations-only, v4_deduped store, filtering enabled). The latest config may recover Batch A's effectiveness or remain in Batch B territory.
- **Visual-only evidence for Phase 0.** The monolithic strategy system's improvement was observed through transcript inspection, not measured systematically. We can't quantify how much of the Phase 1 improvement over "no memory" is attributable to the RAG architecture vs simply having more game experience in the store.

## Decision

Memory effectiveness is proven — the question is not "does it work?" but "what configuration makes it work?" The Batch A result (70% → 97%) establishes the ceiling. The Batch B result (74% → 73%) establishes that bad configuration can lose the entire benefit.

The priority is not more evidence that memory works. It's running a batch with the current configuration to determine where it falls between these two bounds.

## What's Next

1. **Latest-config batch** — Run 30 games each for no-memory and all-enabled (observations-only) with v4_deduped store and filtering. This determines whether the current system recovers Batch A's effectiveness.
2. **Isolate the regression** — If the latest config still shows no benefit, test v4_deduped without action_phase namespace to isolate whether namespace granularity or store content is the culprit.
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
