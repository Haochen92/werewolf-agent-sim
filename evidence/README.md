# Evidence Directory

Experiment reports documenting the evaluation and tuning of the werewolf agent memory system. Each subdirectory contains a self-contained experiment with its report, eval configs, eval results, and supporting artifacts.

## Organization

Experiments are grouped by subsystem. Within each group, experiments are independent unless noted otherwise. This catalog covers the full `evidence/` tree, grouped into: **memory pipeline** · **game engine & behavior** · **evaluation apparatus** · the **v6/v7 campaign** · **training** · **meta**. Each entry is a pointer, not a summary — follow it for the actual findings and their provenance.

## Memory Pipeline

### [dedup/](dedup/) — Deduplication

Removing redundant entries from the memory store, both at batch level (periodic maintenance) and per-extraction level (after each game).

| Experiment | Sample | Date | Status |
|---|---|---|---|
| [store_retrieval_impact](dedup/store_retrieval_impact/experiment_log.md) | n=5 + n=39 | May 23, 26 | Phase 1 (n=5) superseded; phase 2 (n=39) is current |
| [batch_dedup](dedup/batch_dedup/experiment_log.md) | n=111 golden | May 26 | Current |
| [per_extraction](dedup/per_extraction/experiment_log.md) | n=50 golden | May 26 | Current |
| [embedding_prefilter](dedup/embedding_prefilter/) | n=65+232 | May 26 | Current |

`store_retrieval_impact` and `batch_dedup` form a timeline — see [dedup/README.md](dedup/README.md).

### [retrieval/](retrieval/) — Retrieval Pipeline

Tuning how memories are retrieved at game time: filtering, reranking, and capacity limits.

| Experiment | Sample | Date | Notes |
|---|---|---|---|
| [filtering](retrieval/filtering/report.md) | n=5 | May 23 | Pre-dedup store; filtering shown unnecessary on clean store |
| [reranking](retrieval/reranking/report.md) | n=5 | May 23 | Strategy-only reranking on v4_deduped; small sample |
| [capacity_limits](retrieval/capacity_limits/report.md) | n=120 | May 24 | Observations-only, top_k=3 vs 5 |
| [context_eval](retrieval/context_eval/experiment_log.md) | — | Jun 1 | Context-based retrieval eval; methodology final, execution DEFERRED (golds conditioned on the v4_deduped_v2 substrate) |
| [per_day_discussion_retrieval](per_day_discussion_retrieval/experiment_log.md) | 3,916 agent-days, $0 | Jul 7 | Design variant (retrieve once per day, not per turn) gated on a recompute pre-test: within-day retrievals almost never identical (0–9%), but the churn is substantially query-paraphrase noise, not adaptation; PARKED as a config-flag candidate |

`filtering` and `reranking` used n=5 on v4_deduped (v0 prompts). Their directional findings hold but absolute numbers are noisy.

### [extraction/](extraction/) — Extraction Quality

Quality of what goes into the memory store and what queries are generated at retrieval time.

| Experiment | Sample | Date | Notes |
|---|---|---|---|
| [post_game](extraction/post_game/report.md) | n=48 | May 24-26 | Judge de-bug, per-role vs single-pass, model bake-off (journey in [experiment_log.md](extraction/post_game/experiment_log.md)) |
| [situation_summary](extraction/situation_summary/report.md) | n=15 / 20 | May 24-27 | How it works today; model comparison + golden-label NDCG retrieval iteration (journey in [experiment_log.md](extraction/situation_summary/experiment_log.md)) |
| [situation_dimensions](extraction/situation_dimensions/report.md) | 4 apparatus | May 24 – Jul 2 | Design + reliability arc of the state-descriptor dimension schema (prose → per-cell schema; retrieval + gating + criticality proxy); NDCG golden, criticality/forced screens, $0 accuracy audit (journey in [experiment_log.md](extraction/situation_dimensions/experiment_log.md)) |
| [day_summary](extraction/day_summary/report.md) | — | — | How the end-of-day summary works today: a structured digest that bounds context and turns discussion into signal |

### [extraction_selection/](extraction_selection/) — Selecting Which Turns to Extract

| Experiment | Date | Notes |
|---|---|---|
| [experiment_log](extraction_selection/experiment_log.md) | Jun 17 | Does extraction infer turn pivotalness, and should we steer it? Diagnostic done (net_verdict calibration); steering recommendation = anchor-injection, gated by the memory-pipeline prompt freeze |

### [caching/](caching/) — Prompt Caching

| Experiment | Date | Notes |
|---|---|---|
| [report](caching/report.md) | — | How caching works today: the pipeline caches exactly one thing — the shared game-transcript prefix of post-game extraction, via explicit Vertex context caching; every in-game turn pays full price by decision (journey in [experiment_log.md](caching/experiment_log.md)) |

### [memory_system/](memory_system/) — Memory System Impact

End-to-end measurements of whether and how episodic memory helps gameplay.

| Experiment | Sample | Date | Notes |
|---|---|---|---|
| [effectiveness](memory_system/effectiveness/report.md) | n=30 games | May 24 | With/without memory; strongest evidence memory works |
| [ablation](memory_system/ablation/report.md) | n=120 | May 24 | Observations vs strategy points vs both |
| [strategy_adoption](memory_system/strategy_adoption/report.md) | n=120 | May 24 | Adoption tracking prompt v1-v3 |
| [augmentation](memory_system/augmentation/experiment_log.md) | n=20 v5_seed | Jun 11 | Namespace-augmentation probe: deepen thin (role, phase) cells by re-mining source games |

## Game Engine & Behavior

The rules the agents play under and the prompt discipline that keeps the eval honest.

| Topic | Date | Notes |
|---|---|---|
| [role_set](role_set/experiment_log.md) | Jun 1 | Phase A #2: 9-player 3-faction casting design; casting + voting LOCKED, no role implemented yet |
| [sequential_discussion](sequential_discussion/report.md) | May 31 – Jun 5 | Phase A #1, SHIPPED: concurrent → sequential day-discussion engine; acceptance A/B in [quality_gate](sequential_discussion/quality_gate/experiment_log.md) |
| [prompt_boundary](prompt_boundary/experiment_log.md) | — | Enforced the prompt (how-to + facts) vs memory (what-signals-mean) division before the roles phase, so the generator isn't baking strategy into the store it will be A/B-tested against |
| [prompt_claims_audit](prompt_claims_audit/experiment_log.md) | Jun 17 | Are the hand-authored PLAYSTYLE tactics actually true? Audit complete; one falsified claim → investigator rewrite drafted behind a default-off flag, ready to A/B |
| [agent_boundaries](agent_boundaries/report.md) | Jun 6 | Information-boundary guarantee: each agent's prompt contains only what its role may know; the leak-regression smoke logs are colocated as the proof |

## Evaluation Apparatus

How the pipeline is measured — and how far each measurement can be trusted.

### [evaluation/](evaluation/) — The Eval Hub

The measurement layer: how we judge whether the memory pipeline works, and (the harder question) how trustworthy each instrument is. [report.md](evaluation/report.md) is the hub; [source_map.md](evaluation/source_map.md) is the reliability ledger (tags, code pointers, dated code-vs-report verification). Per-instrument spokes live inside: `llm_judge/`, `labeling/`, `sampled_human_review/`, `dimension_extraction/`, `discussion_tagger/`, `replay_screens/`, `metrics/`, `loop/`, `end_to_end_ab/`, `hardening_pass/`, `methodology/`. This chapter documents the *apparatus*; the design verdicts it produced live in the subsystem folders above.

### [metrics/](metrics/) — Evaluation Metrics

How we score per-role *play performance* (the key driver of the memory-system impact measurement).
Distinct from the judges in other folders, which score the memory pipeline itself.

| Experiment | Sample | Date | Status |
|---|---|---|---|
| [experiment_log](metrics/experiment_log.md) | — | Jun 6 | Design discussion: audit + proxy-basket decision (per-role decision-quality is not deterministically feasible; use de-lucked, monotonicity-verified outcome proxies) |

This folder is the metric **design** journey; its instrument-**trust** twin is [evaluation/metrics/](evaluation/metrics/). Likewise [discussion_tagger/](discussion_tagger/) (the tagger design) twins [evaluation/discussion_tagger/](evaluation/discussion_tagger/) (the tagger-as-instrument trust report).

### Apparatus Support

| Topic | Date | Notes |
|---|---|---|
| [tracing](tracing/report.md) | Jun 27 | The capture half of eval: agent decisions, extraction, dedup, and day summaries emitted as four case types to a Langfuse trace + local JSONL sidecar, then frozen into reproducible eval sets |
| [prompt_versioning](prompt_versioning/prompt_versioning_analysis.md) | Jun 6 | Reproducibility unit = prompt version + pinned model + generation params; claims verification + the minimal defensible fix for a prompts-as-code setup |
| [model_drift](model_drift/drift_surfaces_and_guards.md) | Jun 12 | Reference note: unpinnable-alias epoch-drift surface map + the interleave-arms guard (never compare to historical runs) |

## The v6/v7 Campaign

The dimension-schema rebuild (Phase B) and the v7 compounding-loop iteration.

| Topic | Date | Notes |
|---|---|---|
| [phase_b](phase_b/plan_review.md) | Jun 13 – 15 | Phase B design specs + cheap screens: [dimension_schema_build_spec](phase_b/dimension_schema_build_spec.md), [procedural_memory_experiment](phase_b/procedural_memory_experiment.md), [v6_full_store](phase_b/v6_full_store.md), the criticality/forced-schema/dimension-accuracy screens, and the v6-wide migration roadmap |
| [v7_final](v7_final/experiment_log.md) | Jun 20 – Jul | Build log of the v7 credit / consolidation / discussion-credit work; the compounding loop itself is the one still-un-run paid test (design docs `consolidation_design.md`, `discussion_credit_design.md` hold current state) |
| [discussion_tagger](discussion_tagger/report.md) | Jun – Jul | The v7 credit-signal instrument: an omniscient LLM tagger scoring discussion merit + night read-quality per turn; apparatus record + full tagged-signal inventory (instrument-trust verdict at [evaluation/discussion_tagger/](evaluation/discussion_tagger/)) |
| [execution_plan](execution_plan/compounding_measurement_plan.md) | Jul 4 | Forward-looking plan for the compounding question; PLANNED, not executed — Phase 0 gates all paid runs |

## Training

### [fine_tuning/](fine_tuning/) — Model Distillation & Training

Off-the-critical-path training tracks (learning-project tier), each with its own `experiment_log.md`.

| Track | Notes |
|---|---|
| [agent_dialogue](fine_tuning/agent_dialogue/experiment_log.md) | Distill cheaper-than-flash-lite dialogue that matches/exceeds quality |
| [dedup_classifier](fine_tuning/dedup_classifier/experiment_log.md) | SFT the per-extraction dedup classifier past the prompt-engineering accuracy ceiling |
| [embedding](fine_tuning/embedding/experiment_log.md) | Domain-specific embeddings (pairs/triplets) to widen the duplicate-vs-distinct margin |
| [cross_encoder](fine_tuning/cross_encoder/) | Cross-encoder [reranker](fine_tuning/cross_encoder/reranker/experiment_log.md) + [dedup_prefilter](fine_tuning/cross_encoder/dedup_prefilter/experiment_log.md) |
| [memory_selection_bandit](fine_tuning/memory_selection_bandit/experiment_log.md) | RL selection-scorer ("contextual bandit") — PARKED, paper design only |

## Meta

### [refactor/](refactor/) — Structure & Convention Notes

| Note | Date | Notes |
|---|---|---|
| [structure_audit](refactor/structure_audit.md) | Jun 6 | Pre-v5 repo structure audit (no code moved) |
| [eval_architecture_convention](refactor/eval_architecture_convention.md), [node_factory_pattern](refactor/node_factory_pattern.md), [provenance_lineage_rationale](refactor/provenance_lineage_rationale.md) | — | Design/convention reference notes underpinning the refactor |

## Reading Guide

Reports vary in maturity. The key distinction:

- **n=5 experiments** (filtering, reranking, store_retrieval_impact phase 1): Directional signals only. Useful for understanding the evaluation journey but absolute numbers should not be cited. These predate the batch dedup prompt tuning (v0 prompts). store_retrieval_impact was extended with a phase 2 (n=39) that supersedes the original numbers.
- **n=15-50 experiments** (situation_summary, extraction_quality, golden label evals): Moderate confidence. Golden label evals are deterministic and don't suffer from small-sample noise the way judge-scored evals do.
- **n=120+ experiments** (ablation, capacity_limits, adoption): High confidence. Large sample, robust methodology.

**Provenance varies by era — do not assume a single store or judge model across the tree.** The early experiments here ran on the v4 memory-store family (522 base items from 48 games) with a `gemini-2.5-flash` judge; the v6/v7 campaign moved to v6/v7-era stores and (per the eval hub) a Vertex backend. Trust each experiment's own provenance stamp for its store, judge model, and backend, and see [evaluation/report.md](evaluation/report.md) + [evaluation/source_map.md](evaluation/source_map.md) for the apparatus history. Where a report's header marks a result as retracted or superseded, that status governs — cite the status, not the original number.
</content>
</invoke>
