# Memory Type Ablation: Observations vs Strategy Points

## Motivation

The memory system provides agents with two types of retrieved context: observations (factual accounts of past game events) and strategy points (prescriptive advice extracted from patterns across games). Both go through similar pipelines — extraction, deduplication, embedding, retrieval — but strategy points additionally require an adoption tracking pipeline to measure quality and a planned Phase 2 postgame effectiveness scoring system. The Phase 1 adoption experiment surfaced an attribution ambiguity problem: agents struggled to distinguish which memory type drove their decisions, because observations and strategy points often teach the same lesson from different angles. This raised a direct question: **do strategy points add value beyond what observations already provide?** If not, dropping them would eliminate the adoption pipeline, Phase 2 scoring, and the attribution ambiguity — a significant simplification.

## Design and Hypothesis

We designed a three-condition ablation using the snapshot re-retrieval mode built during the adoption experiment. Each condition replays the same 120 frozen game turns (from the v2 adoption eval set) with identical game context but different memory inputs:

1. **Both** — observations + strategy points (the current production configuration)
2. **Observations only** — observations + empty strategy point store
3. **Strategy points only** — empty observation store + strategy points

The hypothesis was that observations would carry most of the value, based on two structural arguments: observations are self-correcting (postgame extraction captures both success and failure), and `observation_count` is a natural quality signal without needing an adoption tracking layer. We expected the "both" condition to moderately outperform either alone, and strategy-points-only to underperform observations-only.

**Why snapshot replay, not full games.** The alternative — running complete games with only observations or only strategy points — would produce cascading differences. Every agent decision affects subsequent game state: different accusations lead to different votes, different eliminations, different pressure dynamics. By turn 3, the three conditions would be playing entirely different games, and any performance difference could be attributed to the divergent trajectory rather than the memory type. Holding the game state constant and swapping only the memory input isolates exactly what we want to measure: given the same situation, does the memory type affect decision quality? The frozen game states were produced by agents running with both memory types, which gives realistic situations to evaluate against rather than artificial ones.

The snapshot mode works by pointing `build_store_from_snapshots` at different file combinations. An empty store JSON (`{"namespaces": {}}`) produces zero items for the omitted memory type. No code changes were needed beyond creating the empty file and three config files — the existing pipeline handled the ablation by design.

## Evaluation Setup

An LLM judge (`gemini-2.5-flash`) evaluated each replayed turn on four dimensions:

1. **Action Quality** (1-5): Is the action strategically appropriate for this role and game state?
2. **Strategy Application** (1-5): Does the action use retrieved guidance discriminantly? (This evaluates use of *any* retrieved memory, not just strategy points — the name is a holdover.)
3. **Grounding** (1-5): Are all claims traceable to provided context?

**Judge context fix.** The initial n=30 run revealed a bug: `application_case_for_judge` was passing the original frozen case's memories to the judge rather than the re-retrieved memories the agent actually received. For the observations-only condition, this meant the judge saw strategy points the agent never had. We fixed this by updating the judged case's `retrieved_observations` and `retrieved_strategy_points` to match the actual inputs, then reran all three conditions.

Dataset: 230 frozen cases from 3 games (v2 adoption eval set), sampled at n=120. All cases use the v2 adoption prompt and prospective schema ordering. Initial n=30 results showed all conditions near 4.8; n=120 revealed this reflected easy-case bias in the small sample.

## Results

| Metric | Both | Obs Only | SP Only |
|--------|------|----------|---------|
| action_quality | 4.46 | 4.33 | **4.50** |
| strategy_application | 4.53 | 4.38 | **4.51** |
| grounding | 4.62 | 4.65 | **4.71** |

The overall scores dropped from n=30 (~4.8) to n=120 (~4.4-4.5), which is expected — larger samples include harder cases (ambiguous game states, weaker role-phase combinations) that weren't represented in the initial 30.

**No additive benefit from combining memory types.** The initial hypothesis was that observations and strategy points would complement each other — observations providing grounded evidence, strategy points providing actionable guidance. The data shows no such complementarity: the "both" condition sits between the two single-type conditions on every metric rather than above them.

Strategy-points-only has the highest number on all three metrics, but the margins (0.04-0.17) are within noise at n=120 — the ordering could flip with a different sample. We note the direction without interpreting it. What the data does tell us: either memory type alone produces equivalent action quality to the full system, and the choice between them is an infrastructure decision rather than a performance one.

## Decision and Tradeoffs

**No architectural decision is made in this experiment.** The data shows that either memory type alone matches the combined system, but it doesn't tell us which to keep. That is an infrastructure and design question, not a performance one.

The strongest case for dropping strategy points is operational: they require the adoption tracking pipeline and a planned Phase 2 effectiveness scoring system, while observations achieve equivalent performance with simpler infrastructure (`observation_count` as a built-in quality signal, self-correcting extraction).

The strongest case for keeping strategy points is that this ablation tests retrieval and application in isolation — it doesn't capture whether strategy points improve *learning across games* (e.g., do agents converge on better play faster with prescriptive guidance?). A single-turn replay can't measure multi-game learning trajectories.

The tradeoff we're accepting: locking these findings as a reference point without making the final architecture decision. A separate experiment with broader game variety and potentially multi-game evaluation would be needed to make that call definitively.

## Lessons

### Ablation infrastructure should be designed into experiment pipelines from the start

The snapshot re-retrieval mode, built during the adoption experiment for a different purpose, made this ablation trivial — three config files and an empty JSON, no code changes. If we had needed to build ablation support after the fact, this experiment would have taken significantly longer and probably been deferred. The lesson: when building an experiment pipeline, include the knobs for the obvious follow-up questions ("what if we remove X?") even if you don't plan to run them immediately.

### Judge context must match agent context in replay experiments

The initial run produced artificially similar scores across conditions because the judge was evaluating all three against the same memory context (the original frozen case). This is a subtle bug — the agent's action quality can still vary by condition even with a mismatched judge, but the judge's *interpretation* of that action is anchored to the wrong context. For any replay experiment that modifies inputs, the judge must see exactly what the agent saw.

### Equal performance between components doesn't mean either is redundant

The natural instinct when two components perform equally in isolation is to drop one for simplicity. But equal *isolated* performance doesn't rule out complementary effects that only matter in richer contexts (multi-game learning, novel situations, role-specific scenarios). The ablation tells us "neither is clearly better in single-turn replay" — it doesn't tell us "one is sufficient for the full system."

## What's Next

These findings feed into a broader architecture decision about the memory system's final shape. That decision requires:

1. **Wider game variety** — the current eval set draws from 3 games with the same player configuration. Testing across more diverse game states would increase confidence.
2. **Multi-game evaluation** — single-turn replay measures application quality but not learning velocity. Do agents improve faster across games with both memory types?
3. **Cost analysis** — strategy points add pipeline complexity (adoption tracking, dedup, planned Phase 2). Even at equal performance, the operational cost difference may tip the decision.

This is a separate undertaking from the current experiment series.

## Artifacts

All artifacts are co-located in `evidence/memory_ablation/`.

| File | Description |
|------|-------------|
| `eval_configs/both_memory.json` | Config: observations + strategy points, n=120 |
| `eval_configs/observations_only.json` | Config: observations only, n=120 |
| `eval_configs/strategy_points_only.json` | Config: strategy points only, n=120 |
| `eval_results/ablation_n30_both.jsonl` | n=30 results, both memory types |
| `eval_results/ablation_n30_observations_only.jsonl` | n=30 results, observations only |
| `eval_results/ablation_n30_strategy_points_only.jsonl` | n=30 results, strategy points only |
| `eval_results/ablation_n120_both.jsonl` | n=120 results, both memory types |
| `eval_results/ablation_n120_obs_and_sp_only.jsonl` | n=120 results, observations-only + strategy-points-only (distinguished by `snapshot` field) |

Shared dependency: eval set at `evidence/strategy_adoption/eval_sets/phase1_adoption_v2.jsonl` (230 cases from 3 games). Empty store at `Agents/memory_stores/v4_deduped/empty.json`.
