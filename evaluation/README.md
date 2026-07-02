# Evaluation Module

This module evaluates the episodic long-term memory pipeline used by the
Werewolf agents.

The intended workflow is:

1. Run full games with `scripts/run_batch.py`.
2. Build a frozen local eval dataset from the per-game eval-case sidecars `run_batch`
   writes (Langfuse traces are a fallback for games predating local emission).
3. Replay specific parts of the memory pipeline from the frozen dataset.
4. Optionally use an LLM judge to score the replayed outputs.
5. Write JSONL results under `evaluation/eval_results/`.

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

The evaluation module uses frozen `EvalCase` records captured during each game —
written to a per-game local sidecar (the primary source) and mirrored to the Langfuse
span. Each `EvalCase` represents one agent turn and includes:

- visible discussion context
- private role context
- generated situation summaries
- retrieved observations and strategy points
- final discussion or vote output

## Structure

```text
evaluation/                the eval subsystem (code + its data)
  src/                     the code (the judge half — capture lives in tracing; see evidence/tracing/):
    core/        config schemas, result schemas, IO, formatting, costs, stats, manifests, settings
    data/        the read side — rehydrate the eval-case span-dicts run_batch captured, then curate + freeze:
      converters/    span-dict → one typed case (EvalCase / Extraction / Dedup / DaySummary)
      sources/       where cases come from: sidecar.py (run_batch's local sidecars, PRIMARY) · langfuse.py (fallback fetch + cost)
      frozen_sets.py  frozen-set record schemas + JSONL I/O · sampling.py  stratified subset selection · batch_layout.py  batch_results/ write layout
    replay/      replay adapters for the summary, retrieval, and action stages (renamed from components/)
    judges/      judge prompts + LLM judge wrappers, one per case type
    labeling/    multi-model golden-label pipeline: engine, voter, exporter, adapters/, pipeline,
                 manual_labelers/ (interactive human CLIs), label_scorer/ (golden-set scorers/NDCG/regen)
    loop/        the v7 compounding-loop harness (generational A/B: credit, synth, consolidate, measure)
    experiments/ command-line eval runners + concluded v6/v7 study runners (inventory below)
    archive/     old eval code kept for auditing only
  config/                  experiment configs (domain subfolders + template/)
  frozen_eval_sets/        shared frozen replay datasets + gold labels (experiment-specific sets live in evidence/<exp>/eval_sets/)
  eval_results/            transient run output (gitignored scratch; keepers graduate to evidence/<exp>/)
```

Model *training* (CE reranker / dedup classifier) is not part of this subsystem — it lives in the
repo-root `training/` package (it trains models; it does not judge cases).

Live code should not import from `evaluation/src/archive`.

Memory snapshots used by normal graph runs and retrieval experiments live in:

```text
memory_stores/
  v1_pre_dedup/
  v1_post_dedup/
  v2/
```

Normal runs default to `v1_post_dedup`. Use `v2` for fresh-store experiments.

To populate or continue the `v2` store while seeding and dumping from the same
versioned directory:

```bash
poetry run python scripts/run_batch.py \
  --configs all_disabled wolf_only all_enabled \
  --runs-per-config 15 \
  --session-prefix v2_fresh_memory_001 \
  --memory-store-dir memory_stores/v2
```

For a batch that should continue learning from an existing store, use
`--memory-store-dir` or separate `--seed-store-dir` and `--dump-store-dir`
arguments.

## Data plane

The eval pipeline reads and writes four data folders — three nested under
`evaluation/`, plus `batch_results/` at the repo root (generation output). They are
stages of one flow, not duplicates:

```text
scripts/run_batch.py ─→ batch_results/<session_prefix>.jsonl   (game-run log; filename = Langfuse session link)
        │                  records self-stamped with runtime_fingerprint + configs + game_id/trace_id
        │              ─→ batch_results/eval_cases/<session_id>/<game_id>.jsonl   (per-game eval-case sidecar;
        │                  record carries the pointer in eval_cases_path)
        ▼
eval-build-* CLIs freeze cases ─→ evaluation/frozen_eval_sets/<id>.jsonl  (+ <id>.manifest.json sidecar)
        │   source = local sidecars (config key `local_results`, preferred — no Langfuse read)
        │   or Langfuse traces (session/trace configs, for games predating local emission)
        ▼
eval-* runners (--config evaluation/config/<domain>/<name>.json) ─→ evaluation/eval_results/…  (judge or gold-label scores)
```

The `eval-build-*` step is where `src/data/` runs against the captured span-dicts:
`sources/sidecar.py` reads the per-game sidecars `run_batch` wrote, `converters/` rehydrate
each into a typed case, `sampling.py` selects a stratified subset, and `frozen_sets.py`
writes the immutable set. (`sources/langfuse.py` is the same path sourced from traces instead.)

**Sidecar span-wrapper shape** (before concluding "a field is empty everywhere"): each line of
a `batch_results/eval_cases/<session>/<game>.jsonl` sidecar is a **span** dict, and the eval-case
payload is nested at `output.eval_case.<field>` (e.g. `line["output"]["eval_case"]["situation_dimensions"]`),
not at the top level. A top-level `line["<field>"]` read always looks empty — that is a wrong-level
read, not missing data; the `*_case_from_span` converters unwrap it, and ad-hoc scans must too.
Query-side `situation_dimensions` is persisted **only in the loop-era sidecars**
(`town_only_run1`/`town_only_run2`/`v2_full`/`legacy`); `ab_*`/`v6ab_*` sessions ran the v5 query
path and carry none, so an empty value there is expected.

| Folder | Role | Git |
|---|---|---|
| `evaluation/config/` | experiment configs, grouped by domain subfolder (+ `template/`) | tracked |
| `evaluation/frozen_eval_sets/` | **shared** frozen sets + gold labels (experiment-specific → `evidence/<exp>/eval_sets/`) | tracked |
| `evaluation/eval_results/` | transient run output — staging only; keepers graduate to `evidence/` | gitignored (scratch) |
| `batch_results/` | per-game run logs (link games → Langfuse traces) | gitignored |

**Staging vs record (two zones).** `evaluation/eval_results/` is throwaway staging —
the runner dumps every iteration there, gitignored, safe to clean. The durable
record is `evidence/<experiment>/`: when a run is a keeper, **graduate** it (result →
`eval_results/`, the exact config → `eval_configs/`, narrative → `report.md`),
stamping lineage (git SHA, config hash, content-hashed inputs) at that point.
Co-locating a run's config with its result is an `evidence/` property, not an
`evaluation/` one — `evaluation/` holds the reusable *templates* (`config/`) and
*shared* inputs (`frozen_eval_sets/`); the frozen run lives in `evidence/`.

`configs/` no longer exists — experiment configs have one home, `evaluation/config/`.
Code-level config stays in modules (`Agents/game_config.py`, per-package
`config.py`, `llm_factory` model constants); there is no central code-config folder.

**Domain taxonomy.** `evaluation/config/`, `evaluation/frozen_eval_sets/`, and `evaluation/eval_results/` share one
subfolder vocabulary — *config asks the question, eval_set is the exam, eval_result
is the grade; same domain name at each stage.* A domain gets a subfolder in a stage
once it holds ≥2 artifacts there; single shared datasets (e.g. `v4_filtering_eval`,
used across reranking / filtering / store_dedup) stay at the folder root.
A frozen set belongs in `evaluation/frozen_eval_sets/` only if it is **shared**
(≥2 consuming configs/experiments, or a standing benchmark); a set built for one
study lives in `evidence/<exp>/eval_sets/`. Each set's `<id>.manifest.json` records
its `scope` (`shared` | `experiment:<name>`) plus optional `consumers` — the
machine-readable marker for the distinction.
`batch_results/` is **flat** for the batch logs — games are domain-agnostic inputs and
the filename is the Langfuse session link. The one subtree is `batch_results/eval_cases/`:
per-game eval-case sidecars keyed by the same session-id convention, written once per
game (overwrite-safe; immune to the appended-JSONL footgun).

**Naming + lineage.** Forward standard for *new* artifacts: short names
`<domain>/<purpose>_vN.{jsonl,json}` — metadata does **not** go in the filename.
Lineage rides a manifest instead: embedded top-level keys for JSON-object artifacts
(`eval_results`, `batch_results`), a `<id>.manifest.json` **sidecar** for
envelope-less JSONL `eval_sets`. Inputs are referenced by content hash
(`{path, sha256, count}`) so staleness is detectable, forming a chain
result → eval_set → batch run. Rationale + the staged design:
[`evidence/refactor/provenance_lineage_rationale.md`](../evidence/refactor/provenance_lineage_rationale.md).
(The manifest writer is forward-looking — legacy artifacts keep their original names
and missing lineage.)

**Legacy.** Concluded-era artifacts live in a `legacy/` subfolder of their data
folder, names untouched (still citable for the writeup). Existing data files are
never renamed — `batch_results` filenames are Langfuse session prefixes, and
`evidence/` reports cite names.

**Labels.** Gold-label files used by deterministic evals live with their sets in
`evaluation/frozen_eval_sets/`. Labelling *process* artifacts (multi-model votes, manual exports from
`evaluation/labeling/`) and experiment-frozen golds live in `evidence/<experiment>/`,
which keeps its own self-contained convention and is not part of this taxonomy.

**scripts/ vs evaluation/.** `scripts/` holds only generation entry points
(`run_batch`, `analyze_batch`) and one-off ops; reusable eval logic lives in
`evaluation/` as a config-driven runner.

**evaluation/ (code) vs evidence/ (record).** Authoritative eval code lives only
here; `evidence/<experiment>/` holds the narrative + artifacts + a provenance
pointer back to the code that produced it — never its own copy of the function.
One-off studies (e.g. the model-comparison runners) write their outputs into
`evidence/<experiment>/`, not `evaluation/eval_results/`. The full layer rule + the
explore→graduate→supersede lifecycle is in **CLAUDE.md → Eval Architecture**.

## Replay, Judges, And Experiments

The evaluation code is split by responsibility:

```text
replay      = produce outputs by replaying part of the agent pipeline on a frozen case
judges      = grade or compare outputs using a rubric
experiments = coordinate datasets, replay, judges, configs, and JSONL output (the CLI layer)
```

For example, an E2E experiment reads frozen cases, replays the summary stage,
replays retrieval, replays the action stage, optionally calls a judge, and writes
one JSONL record per replay. The judge does not know about datasets, output
paths, snapshots, or CLI config. It only receives formatted inputs and returns
scores.

The dependency direction should stay simple:

```text
experiments -> replay
experiments -> judges
judges      -> prompts / schemas / formatters
replay      -> production agent code
```

### `experiments/` inventory

`experiments/` is the CLI layer. It holds two kinds of file, kept distinct on purpose:

**1. Live eval runners** — the authoritative one-runner-per-kind surface. Most are wired as
`eval-*` console scripts (see `pyproject.toml [project.scripts]`): builders
(`eval-build-dataset`/`-extraction-dataset`/`-dedup-dataset`), the agent-decision funnel
(`eval-summary`, `eval-summary-rubric`, `eval-retrieval`, `eval-application`, `eval-captured`,
`eval-e2e`), `eval-extraction`, `eval-day-summary`, dedup (`eval-dedup`, `eval-dedup-score`,
`eval-batch-dedup`), and `eval-graduate`. A few live tools run by module path only:
`dedup_replay`, `batch_dedup_merge_eval`, `extraction_replay`, `eval_auto_dedup` +
`auto_dedup_dataset_builder`.

**2. Concluded v6/v7 study runners** — the apparatus that produced the v5→v6→v7 store-evolution
conclusions. Not part of the live CLI surface; kept runnable because frozen `evidence/v7_final/`
scripts import them and the evidence reports point at them. Their physical disposition (subfolder
vs colocate) is **deferred to the concurrent code + memory-effectiveness review** — the apparatus
and its verdict are two axes of the same files.

| Study runner | What it studied | Record |
|---|---|---|
| `decision_replay.py` | de-luck proxy validation (off-policy decision replay) | `evidence/memory_system/effectiveness/decision_replay/` |
| `criticality_screen.py` | conditioned-vs-flat retrieval (gated the v6 build) | `evidence/phase_b/criticality_screen/` |
| `forced_schema_screen.py` | forced per-memory applicability schema | `evidence/phase_b/forced_schema_screen/` |
| `dimension_gating_screen.py` | retrieval dimension-gating (NEGATIVE → ships default-off) | `evidence/v7_final/review_map.md` |
| `reextract_villager_day.py`, `reextract_cells.py` | v6 per-cell re-extraction store build | `evidence/phase_b/v6_full_store.md` |
| `synthesize_cell_sp.py` | v6 cluster→strategy-point synthesis | `evidence/phase_b/` |
| `recall_flags.py` | deterministic pivotal-turn flagger (v7 recall anchor) | `evidence/v7_final/review_map.md` |
| `synth_deluck_ab.py` | credit-aware vs outcome-halo synthesis A/B | `evidence/v7_final/synth_deluck_ab/` |
| `consolidation_prune.py` | offline credit-prune apply-tool | `evidence/v7_final/review_map.md` |
| `investigator_transmission.py` | v6 static SP A/B (motivates cross-game synthesis) | `evidence/memory_system/effectiveness/v6_sp_ab/` |
| `extraction_model_comparison.py` | extraction model comparison | `evidence/v7_final/extraction_model_ab_compare.py` |

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

Build a local eval set from Langfuse sessions/traces. The builder always writes
a frozen local JSONL dataset for reproducible replay, but the source can be a
Langfuse session ID, session list, session prefix, trace list, or batch-results
JSONL.

Example config using one exact Langfuse session ID:

```json
{
  "eval_set_id": "memory_eval_from_session_001",
  "session_id": "replace_with_langfuse_session_id",
  "created_from": "replace_with_langfuse_session_id",
  "max_games": 5,
  "per_role_per_phase": 1,
  "max_samples": 40,
  "seed": 0,
  "output": "evaluation/frozen_eval_sets/memory_eval_from_session_001.jsonl",
  "overwrite": false
}
```

Save it as:

```text
evaluation/config/build_from_session.json
```

Exactly one source must be set:

- `session_id`: fetch traces for one exact Langfuse session ID.
- `session_ids`: fetch traces for multiple exact Langfuse session IDs.
- `session_prefix`: scan Langfuse sessions, then fetch traces for sessions whose ID starts with this prefix.
- `trace_ids`: use exact Langfuse trace IDs directly.
- `batch_results`: read session IDs from a local `run_batch` JSONL output file, then fetch traces from Langfuse.

Template configs are available in `evaluation/config/template/`:

```text
application_example.json
build_dataset_example.json
build_dataset_session_id_example.json
build_dataset_session_ids_example.json
build_dataset_session_prefix_example.json
build_dataset_trace_ids_example.json
build_dedup_dataset_example.json
build_extraction_dataset_example.json
captured_example.json
dedup_example.json
e2e_example.json
extraction_example.json
retrieval_example.json
summary_flash_vs_lite.json
summary_pairwise_example.json
```

Run:

```bash
poetry run eval-build-dataset --config evaluation/config/build_from_session.json
```

This writes:

```text
evaluation/frozen_eval_sets/memory_eval_from_session_001.jsonl
evaluation/frozen_eval_sets/memory_eval_from_session_001.manifest.json
```

The JSONL dataset is the stable input for all replay experiments.

## Config Files

Experiments are config-first. Put runnable configs under `evaluation/config/`.
Starter templates live under `evaluation/config/template/`.

Paths are resolved relative to the current working directory, so run commands
from the repository root.

The config models are defined in `evaluation/src/core/config_schema.py`.

### Summary Pairwise

Use this to compare how model, prompt, or thinking settings affect situation
summary quality.

Example config:

```json
{
  "experiment_id": "summary_flash_vs_lite",
  "component": "situation_summary",
  "dataset": "evaluation/frozen_eval_sets/memory_eval_001.jsonl",
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
poetry run eval-summary --config evaluation/config/summary_flash_vs_lite.json
```

Template: `evaluation/config/template/summary_flash_vs_lite.json`.

Output includes the baseline and candidate summaries, judge winner, confidence,
brief reasoning, cost estimates, and candidate cost savings.

### Retrieval

Use this to compare memory snapshots and retrieval behavior using captured
situation summaries from the dataset.

Example config:

```json
{
  "dataset": "evaluation/frozen_eval_sets/memory_eval_001.jsonl",
  "snapshots": [
    {
      "label": "v1_post_dedup",
      "observations_path": "memory_stores/v1_post_dedup/observations.json",
      "strategy_points_path": "memory_stores/v1_post_dedup/strategy_points.json"
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
poetry run eval-retrieval --config evaluation/config/retrieval_memory_snapshot.json
```

Template: `evaluation/config/template/retrieval_example.json`.

This replays retrieval for both observations and strategy points. If `judge` is
true, the LLM judge scores relevance, redundancy, unique idea count, and
redundant pairs.

### Application

Use this to evaluate the final discussion or vote action while holding the
frozen turn context fixed.

Example config:

```json
{
  "dataset": "evaluation/frozen_eval_sets/memory_eval_001.jsonl",
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
poetry run eval-application --config evaluation/config/application_captured.json
```

Template: `evaluation/config/template/application_example.json`.

This reruns the production discussion/vote prompt and optionally judges action
quality and strategy application.

### Captured Case Scoring

Use this to judge exactly what was captured in the frozen dataset. This mode
does not regenerate situation summaries, rerun retrieval, rebuild memory
indexes, or rerun the final action prompt.

Example config:

```json
{
  "dataset": "evaluation/frozen_eval_sets/memory_eval_001.jsonl",
  "max_samples": 20,
  "judge_model": "gemini-2.5-pro",
  "sleep_seconds": 1.0
}
```

Run:

```bash
poetry run python -m evaluation.src.experiments.captured --config evaluation/config/captured_v2_memory.json
```

Template: `evaluation/config/template/captured_example.json`.

### E2E Turn Replay

Use this to replay the full turn-level memory path:

```text
summary -> retrieval -> action -> judge
```

Example config:

```json
{
  "dataset": "evaluation/frozen_eval_sets/memory_eval_001.jsonl",
  "snapshots": [
    {
      "label": "v1_post_dedup",
      "observations_path": "memory_stores/v1_post_dedup/observations.json",
      "strategy_points_path": "memory_stores/v1_post_dedup/strategy_points.json"
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
poetry run eval-e2e --config evaluation/config/e2e_memory_snapshot.json
```

Template: `evaluation/config/template/e2e_example.json`.

This is the closest eval to the full episodic memory system, but still at the
single-turn replay level rather than full-game replay.

## Outputs

Experiment outputs are JSONL files under `evaluation/eval_results/` unless an explicit
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
