# Evaluation Module

This module evaluates the episodic long-term memory pipeline used by the
Werewolf agents.

The intended workflow is:

1. Run full games with `scripts/run_batch.py`.
2. Use Langfuse spans from those games to build a frozen local eval dataset.
3. Replay specific parts of the memory pipeline from the frozen dataset.
4. Optionally use an LLM judge to score the replayed outputs.
5. Write JSONL results under `eval_results/`.

The evaluation module does not rerun whole games. It replays individual frozen
agent turns.

## Pipeline

During a normal game, each memory-enabled agent turn follows this path:

```text
game state and private role context
  -> situation_summary LLM call
  -> semantic retrieval over observations and strategy points
  -> final discussion or vote action
```

At the end of a game, postgame extraction creates long-term memory entries:

```text
full game history
  -> observations
  -> strategy_points
  -> memory store snapshots
```

The evaluation module uses frozen `EvalCase` records captured from Langfuse.
Each `EvalCase` represents one agent turn and includes:

- visible discussion context
- private role context
- generated situation summaries
- retrieved observations and strategy points
- final discussion or vote output

## Structure

```text
evaluation/
  core/          config schemas, result schemas, IO, formatting, costs, settings
  data/          Langfuse fetching, EvalCase conversion, dataset sampling
  components/    replay adapters for summary, retrieval, and action stages
  judges/        judge prompts and LLM judge wrappers
  experiments/   command-line experiment entrypoints
  archive/       old eval code kept for auditing only
```

Live code should not import from `evaluation/archive`.

Memory snapshots used by normal graph runs and retrieval experiments live in:

```text
Agents/memory_stores/
  v1_pre_dedup/
  v1_post_dedup/
  v2/
```

Normal runs default to `v1_post_dedup`. Use `v2` for fresh-store experiments.

To populate the fresh `v2` store without seeding from an older store:

```bash
poetry run python scripts/run_batch.py \
  --configs all_disabled wolf_only all_enabled \
  --runs-per-config 15 \
  --session-prefix v2_fresh_memory_001 \
  --dump-store-dir Agents/memory_stores/v2 \
  --no-memory-seed
```

For a batch that should continue learning from an existing store, use
`--memory-store-dir` or separate `--seed-store-dir` and `--dump-store-dir`
arguments.

## Components, Judges, And Experiments

The evaluation code is split by responsibility:

```text
components  = produce outputs by replaying part of the agent pipeline
judges      = grade or compare outputs using a rubric
experiments = coordinate datasets, components, judges, configs, and JSONL output
```

For example, an E2E experiment reads frozen cases, runs the summary component,
runs retrieval, runs the action component, optionally calls a judge, and writes
one JSONL record per replay. The judge does not know about datasets, output
paths, snapshots, or CLI config. It only receives formatted inputs and returns
scores.

The dependency direction should stay simple:

```text
experiments -> components
experiments -> judges
judges      -> prompts / schemas / formatters
components  -> production agent code
```

## Step 1: Run Games

Run a batch of games with different memory settings:

```bash
poetry run python scripts/run_batch.py \
  --configs all_disabled all_enabled wolf_only \
  --runs-per-config 3 \
  --session-prefix memory_eval_001
```

This writes batch metadata to:

```text
batch_results/memory_eval_001.jsonl
```

The actual turn-level eval payloads are captured in Langfuse spans named
`agent_action_eval_*`.

## Step 2: Build A Frozen Dataset

Build a local eval set from the Langfuse sessions/traces:

Example config:

```json
{
  "eval_set_id": "memory_eval_001",
  "batch_results": "batch_results/memory_eval_001.jsonl",
  "created_from": "memory_eval_001",
  "max_games": 5,
  "per_role_per_phase": 1,
  "max_samples": 40,
  "seed": 0,
  "overwrite": false
}
```

Save it as:

```text
configs/eval/build_memory_eval_001.json
```

Exactly one source must be set:

- `batch_results`
- `session_prefix`
- `session_id`
- `session_ids`
- `trace_ids`

Run:

```bash
poetry run eval-build-dataset --config configs/eval/build_memory_eval_001.json
```

This writes:

```text
eval_sets/memory_eval_001.jsonl
eval_sets/memory_eval_001.manifest.json
```

The JSONL dataset is the stable input for all replay experiments.

## Config Files

Experiments are config-first. Put configs under `configs/eval/`.

Paths are resolved relative to the current working directory, so run commands
from the repository root.

The config models are defined in `evaluation/core/config_schema.py`.

### Summary Pairwise

Use this to compare how model, prompt, or thinking settings affect situation
summary quality.

Example config:

```json
{
  "experiment_id": "summary_flash_vs_lite",
  "component": "situation_summary",
  "dataset": "eval_sets/memory_eval_001.jsonl",
  "alternate_order": true,
  "baseline": {
    "label": "flash_current",
    "model": "gemini-2.5-flash",
    "prompt_id": "current",
    "temperature": 0.0
  },
  "candidate": {
    "label": "flash_lite_current",
    "model": "gemini-2.5-flash-lite",
    "prompt_id": "current",
    "temperature": 0.0,
    "thinking_budget": 0
  },
  "judge": {
    "model": "gemini-2.5-pro",
    "prompt_id": "pairwise_summary_v1",
    "temperature": 0.0
  },
  "max_cases": 20,
  "sleep_seconds": 0.5
}
```

Run:

```bash
poetry run eval-summary --config configs/eval/summary_flash_vs_lite.json
```

Output includes the baseline and candidate summaries, judge winner, confidence,
brief reasoning, cost estimates, and candidate cost savings.

### Retrieval

Use this to compare memory snapshots and retrieval behavior using captured
situation summaries from the dataset.

Example config:

```json
{
  "dataset": "eval_sets/memory_eval_001.jsonl",
  "snapshots": [
    {
      "label": "v1_post_dedup",
      "observations_path": "Agents/memory_stores/v1_post_dedup/observations.json",
      "strategy_points_path": "Agents/memory_stores/v1_post_dedup/strategy_points.json"
    }
  ],
  "top_k": 3,
  "max_retrieved_items": 0,
  "max_samples": 20,
  "judge": true,
  "judge_model": "gemini-2.5-pro",
  "sleep_seconds": 1.0
}
```

Run:

```bash
poetry run eval-retrieval --config configs/eval/retrieval_memory_snapshot.json
```

This replays retrieval for both observations and strategy points. If `judge` is
true, the LLM judge scores relevance, redundancy, unique idea count, and
redundant pairs.

### Application

Use this to evaluate the final discussion or vote action while holding the
frozen turn context fixed.

Example config:

```json
{
  "dataset": "eval_sets/memory_eval_001.jsonl",
  "memory_mode": "captured",
  "max_samples": 20,
  "judge": true,
  "judge_model": "gemini-2.5-pro",
  "sleep_seconds": 1.0
}
```

`memory_mode` can be:

- `captured`: use the retrieved memories captured in the original run
- `none`: clear retrieved observations and strategy points

Run:

```bash
poetry run eval-application --config configs/eval/application_captured.json
```

This reruns the production discussion/vote prompt and optionally judges action
quality and strategy application.

### E2E Turn Replay

Use this to replay the full turn-level memory path:

```text
summary -> retrieval -> action -> judge
```

Example config:

```json
{
  "dataset": "eval_sets/memory_eval_001.jsonl",
  "snapshots": [
    {
      "label": "v1_post_dedup",
      "observations_path": "Agents/memory_stores/v1_post_dedup/observations.json",
      "strategy_points_path": "Agents/memory_stores/v1_post_dedup/strategy_points.json"
    }
  ],
  "summary": {
    "label": "summary_current",
    "model": "gemini-2.5-flash",
    "prompt_id": "current",
    "temperature": 0.0
  },
  "top_k": 3,
  "max_retrieved_items": 0,
  "max_samples": 20,
  "judge": true,
  "judge_model": "gemini-2.5-pro",
  "sleep_seconds": 1.0
}
```

Run:

```bash
poetry run eval-e2e --config configs/eval/e2e_memory_snapshot.json
```

This is the closest eval to the full episodic memory system, but still at the
single-turn replay level rather than full-game replay.

## Outputs

Experiment outputs are JSONL files under `eval_results/` unless an explicit
`output` path is provided in the config.

Each line is one replayed case or one replayed case/snapshot/item-type
combination. This makes partial runs easy to inspect and avoids losing all
results if a later case fails.

## Notes

- Set `GOOGLE_API_KEY` for Gemini model calls.
- Set Langfuse credentials in `.env` before building datasets from Langfuse.
- `evaluation/archive/` is kept only for auditing old code.
- Modern dataset building expects Langfuse spans whose output includes
  `eval_case`.
- The evals are intended to be reproducible from local frozen datasets. Rebuild
  the dataset only when you want to change the sampled source turns.
