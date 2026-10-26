# Memory Type Ablation: Observations vs Strategy Points

## In short

*Added 2026-10-26. The report below is the May 2026 record, unchanged except where marked.*

- **Question.** Agents were shown two kinds of lesson from past games: observations (what happened) and
  strategy points (advice). Given the same turn, does a player act better with observations, strategy
  points, or both?
- **Test.** 120 frozen turns from 3 games, each replayed under the three conditions, scored 1–5 by one
  model judge (`gemini-2.5-flash`).
- **Answer.** No condition was better: the largest gap between any two conditions on any measure was
  0.17 on the 1–5 scale, with no condition ahead on every measure. Showing both kinds together added
  nothing.
- **What followed.** Observations only was chosen in May, on lower complexity. It was later reversed:
  served games today retrieve strategy points only, never observations
  (`server/game/run_config.py::game_run_config`), and for each lesson shown the seat gives a verdict
  (follow, override or not relevant; `Agents/schemas/output.py::StrategyVerdict`). The code default
  still enables both kinds (`Agents/config/run.py::DEFAULT_RETRIEVAL_TYPES_CONFIG`).

## Motivation

The memory system provides agents with two types of retrieved context: observations (factual accounts of past game events) and strategy points (prescriptive advice extracted from patterns across games). Both go through similar pipelines — extraction, deduplication, embedding, retrieval — but strategy points additionally require an adoption tracking pipeline to measure quality and a planned Phase 2 postgame effectiveness scoring system. The two phases come from the [strategy adoption report](../strategy_adoption/report.md): **Phase 1** counted, on each strategy point, how often it was shown and how often agents reported following it; **Phase 2**, deferred, would have had a model score each reported adoption against the game transcript as positive, neutral or negative. The Phase 1 adoption experiment surfaced an attribution ambiguity problem: agents struggled to distinguish which memory type drove their decisions, because observations and strategy points often teach the same lesson from different angles. This raised a direct question: **do strategy points add value beyond what observations already provide?** If not, dropping them would eliminate the adoption pipeline, Phase 2 scoring, and the attribution ambiguity — a significant simplification.

## Design and Hypothesis

We designed a three-condition ablation using the snapshot re-retrieval mode built during the adoption experiment. Each condition replays the same 120 frozen game turns (from the v2 adoption eval set: 230 turns frozen from 3 games played with the v2 adoption prompt, the version the adoption experiment selected) with identical game context but different memory inputs:

1. **Both** — observations + strategy points (the production configuration in May 2026)
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
4. **Adoption Accuracy** (1-5): Does the list of strategy points the agent reported following match what it did? This grades the agent's report, not its action, and is left out of the results table; the judge-context fix below says how it moved.

**Judge context fix.** The initial n=30 run revealed a bug: `application_case_for_judge` was passing the original frozen case's memories to the judge rather than the re-retrieved memories the agent actually received. For the observations-only condition, this meant the judge saw strategy points the agent never had. We fixed this by updating the judged case's `retrieved_observations` and `retrieved_strategy_points` to match the actual inputs, then reran all three conditions.

Dataset: 230 frozen cases from 3 games (v2 adoption eval set), sampled at n=120. All cases use the v2 adoption prompt and prospective schema ordering. Initial n=30 results showed all conditions near 4.8; n=120 revealed this reflected easy-case bias in the small sample.

## Results

| Metric | Both | Obs Only | SP Only |
|--------|------|----------|---------|
| action_quality | 4.46 | 4.33 | **4.50** |
| strategy_application | **4.53** | 4.38 | 4.51 |
| grounding | 4.62 | 4.65 | **4.71** |

The overall scores dropped from n=30 (~4.8) to n=120 (~4.4-4.5), which is expected — larger samples include harder cases (ambiguous game states, weaker role-phase combinations) that weren't represented in the initial 30.

**No additive benefit from combining memory types.** The initial hypothesis was that observations and strategy points would complement each other — observations providing grounded evidence, strategy points providing actionable guidance. The data shows no such complementarity: the "both" condition is not clearly above either single type on any metric. It sits between them on action quality, is lowest on grounding, and leads strategy points alone on strategy application by only 0.02.

Strategy-points-only has the highest number on action quality and grounding and is 0.02 behind "both" on strategy application, but the margins (at most 0.17 between any two conditions) are within noise at n=120 — the ordering could flip with a different sample. No significance test is reported. We note the direction without interpreting it. What the data does tell us: either memory type alone produces equivalent action quality to the full system, and the choice between them is an infrastructure decision rather than a performance one.

## Decision and Tradeoffs

The performance data doesn't pick a winner — but the infrastructure cost does. Either memory type alone matches the combined system, making this a design decision rather than a performance one.

The strongest case for dropping strategy points is operational: they require the adoption tracking pipeline and a planned Phase 2 effectiveness scoring system, while observations achieve equivalent performance with simpler infrastructure (`observation_count` as a built-in quality signal, self-correcting extraction).

The strongest case for keeping strategy points is that this ablation tests retrieval and application in isolation — it doesn't capture whether strategy points improve *learning across games* (e.g., do agents converge on better play faster with prescriptive guidance?). A single-turn replay can't measure multi-game learning trajectories.

### Implications for the Memory System (the May 2026 decision)

> **2026-10-26: what runs now.** The plan below was reversed. Served games retrieve strategy points
> only, never observations (`server/game/run_config.py::game_run_config`); its stated reasons are
> that the town half of the store never had observations, so retrieving them would give the two
> factions different memory, and that strategy points are the lessons the replay shows being weighed.
> Observations are still extracted after a game; since a ruling of 2026-07-15 they are material that
> synthesis distils into strategy points, not something a live prompt shows (the v7 loop enforced it:
> `evaluation/src/loop/invariants.py::assert_observations_retired`). The code default
> (`Agents/config/run.py::DEFAULT_RETRIEVAL_TYPES_CONFIG`) still enables both, for batch runs that do
> not set it. Adoption tracking did not go dormant: each turn now gives a verdict on every strategy
> point shown (follow, override or not relevant; `Agents/schemas/output.py::StrategyVerdict`), and
> each follow raises the point's `used_count` (`Agents/turn/adoption.py::process_strategy_adoption`).

The planned default going forward is observations-only for retrieval. Extraction continues for both memory types — strategy points keep accumulating in the store for future experimentation. Adoption tracking becomes dormant as a consequence (no strategy points retrieved means no adoptions to record), but the infrastructure remains in the codebase.

This is a configuration change, not a removal. The rationale is pragmatic: equivalent performance at lower complexity, with `observation_count` serving as a built-in quality signal that doesn't require an adoption tracking pipeline. Strategy points are available to re-enable if multi-game evaluation or broader game variety reveals scenarios where prescriptive guidance adds measurable value.

Though adoption tracking was to go dormant under this plan, the Phase 1 experiment produced transferable findings regardless. The schema field ordering insight — placing metacognitive fields before action fields to create prospective commitment rather than retrospective rationalization — applies to any structured output task where a model must both act and reflect on its action.

## Lessons

### Ablation infrastructure should be designed into experiment pipelines from the start

The snapshot re-retrieval mode, built during the adoption experiment for a different purpose, made this ablation trivial — three config files and an empty JSON, no code changes. If we had needed to build ablation support after the fact, this experiment would have taken significantly longer and probably been deferred. The lesson: when building an experiment pipeline, include the knobs for the obvious follow-up questions ("what if we remove X?") even if you don't plan to run them immediately.

### Judge context must match agent context in replay experiments

The agent saw the correct data in each condition — observations-only agents received only observations, strategy-points-only agents received only strategy points. But the judge always saw both memory types from the original frozen case. When evaluating "did this agent use its retrieved guidance well?", the judge was grading against memories the agent may never have received.

This didn't produce obvious errors — scores looked plausible. The primary impact was on adoption_accuracy (~1.5 point drop when fixed), while action quality and strategy application scores were less affected. In this case, the core null result held after the fix — but we wouldn't have known that without fixing it first.

The lesson: when an experiment modifies the agent's inputs, verify that every downstream evaluator sees the same modified inputs, not a stale copy from the original case. The failure mode is silent — plausible scores with a subtly wrong reference context.

### Null results reframe the question, not the answer

When an A/B test shows no performance difference, the finding isn't "inconclusive" — it's "the differentiator is somewhere else." We expected this ablation to answer "which memory type produces better actions?" Instead it answered "both are equivalent, so the question is which one is cheaper to maintain." The reframing from a performance question to an infrastructure question was the actual value of running the experiment.

## What's Next

> **2026-10-26.** Whole-game tests of memory followed in June and July 2026; what they found is in the
> [memory hub](../report.md).

These findings feed into a broader architecture decision about the memory system's final shape. That decision requires:

1. **Wider game variety** — the current eval set draws from 3 games with the same player configuration. Testing across more diverse game states would increase confidence.
2. **Multi-game evaluation** — single-turn replay measures application quality but not learning velocity. Do agents improve faster across games with both memory types?
3. **Cost analysis** — strategy points add pipeline complexity (adoption tracking, dedup, planned Phase 2). Even at equal performance, the operational cost difference may tip the decision.

This is a separate undertaking from the current experiment series.

## Artifacts

All artifacts are co-located in `evidence/memory_system/ablation/`.

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

Shared dependency: eval set at `evidence/memory_system/strategy_adoption/eval_sets/phase1_adoption_v2.jsonl` (230 cases from 3 games). Empty store at `memory_stores/v4_deduped/empty.json`. The three configs name the eval set at its May path, `evidence/strategy_adoption/eval_sets/`; it has since moved to the path above.
