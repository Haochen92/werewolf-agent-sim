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
      builders/      frozen-set builders (agent_decision / extraction / dedup) — the eval-build-* CLIs
      sources/       where cases come from: sidecar.py (run_batch's per-game sidecars, PRIMARY) ·
                     batch_records.py (repo-root batch_results/*.jsonl game-run logs) · langfuse.py (fallback fetch + cost)
      frozen_sets.py  frozen-set record schemas + JSONL I/O · sampling.py  stratified subset selection · batch_layout.py  batch_results/ write layout
    replay/      regenerate one pipeline stage on a frozen case: situation_summary, retrieval, application (action),
                 extraction, dedup, batch_dedup, day_summary, plus
      decision_screen/  the off-policy per-turn decision-replay engine (cases/replay/schemas/stats/screens)
    judges/      judge prompts + LLM judge wrappers, one per case type
    labeling/    multi-model golden-label pipeline: engine, voter, exporter, adapters/, pipeline,
                 manual_labelers/ (interactive human CLIs), label_scorer/ (golden-set scorers/NDCG/regen)
    diagnosis/   outcome-blind case sampler for human/pro-LLM review cohorts (rung ② of the modality ladder)
    audits/      re-runnable $0 deterministic audits — the regression surface (dimension fills, scheduler
                 access, whiff conversion, proxy validation, dedup + batch-dedup golden scorers, pivotal-turn flags)
    loop/        the v7 compounding-loop harness (generational A/B: credit, synth, consolidate, measure)
    cli_runner/  command-line eval runners — the live CLI layer (inventory below)
      regen_replay/  thin CLIs, grouped by operation: regen/ (regen-only) · judge/ (judge-only) · both/
      diagnosis/     the case-sampler CLI (command wiring over the diagnosis/ logic package above)
      graduate_run.py · discussion_tagger_eval.py   ops CLIs: promote a keeper run to evidence/ · validate the discussion tagger
    studies/     concluded one-shot study runners — frozen verdicts, kept runnable (table in its __init__.py)
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

## Replay, Judges, And Runners

The evaluation code is split by responsibility:

```text
replay      = produce outputs by replaying part of the agent pipeline on a frozen case
judges      = grade or compare outputs using a rubric
audits      = deterministic $0 checks over recorded data (no LLM; re-runnable as regression audits)
diagnosis   = outcome-blind sampling of cases into human/pro-LLM review cohorts
cli_runner  = coordinate datasets, replay, judges, configs, and JSONL output (the CLI layer)
studies     = concluded one-shot apparatus behind frozen verdicts (its own top-level package, off the CLI surface)
```

For example, an E2E experiment reads frozen cases, replays the summary stage,
replays retrieval, replays the action stage, optionally calls a judge, and writes
one JSONL record per replay. The judge does not know about datasets, output
paths, snapshots, or CLI config. It only receives formatted inputs and returns
scores.

The dependency direction should stay simple:

```text
cli_runner/regen_replay -> replay + judges + audits   (thin CLIs; hold no eval logic)
data/builders                 -> data / core                (freeze frozen sets; the eval-build-* CLIs)
judges      -> prompts / schemas / formatters
replay      -> production agent code
audits      -> data / core (deterministic, never judges)
studies     -> replay / loop (frozen apparatus; nothing live imports studies)
```

A CLI stays out of `judges/` and `replay/` even when it only judges (or only replays): those
packages must not depend on the data plane (config / datasets / JSONL output), so the runnable
command lives in the CLI layer and the *logic* it calls lives in `judges/` + `replay/`.

### `cli_runner/` inventory

`cli_runner/regen_replay/` is the live CLI layer — one config-driven runner per eval kind, wired as
`eval-*` console scripts (see `pyproject.toml [project.scripts]`). Each is a thin wrapper: it reads a
frozen dataset, optionally replays a stage (`replay/`), optionally scores it (an LLM `judges/` grader or
a deterministic `audits/` scorer), and writes JSONL. Runners are grouped into three subpackages by
operation — **filed by capability** (a runner that *can* do both lives in `both/` even if a config mode
exercises only one, e.g. `turn_eval --replay none` is judge-only):

- **`regen/`** — regenerate an output, no judge (model-swap dataset producers, run by module path only):
  `extraction_regen`, `dedup_regen`.
- **`judge/`** — judge a captured output, no regeneration: `extraction_judge` (`eval-extraction`),
  `dedup_judge` (`eval-dedup`).
- **`both/`** — regenerate a stage AND judge/score it: `turn_eval` (`eval-turn`) is one runner over a
  frozen turn, `--replay {none|action|all}` × `--judge {off|application|pipeline}`, collapsing the former
  captured/application/e2e CLIs (their `eval-captured`/`eval-application`/`eval-e2e` names remain as
  aliases). Plus `situation_summary_pairwise` (`eval-summary`), `situation_summary_rubric`
  (`eval-summary-rubric`), `retrieval` (`eval-retrieval`), `day_summary_judge` (`eval-day-summary`),
  `batch_dedup_judge` (`eval-batch-dedup`).

**Ops at `cli_runner/` root** (not frozen-case evals): the discussion-tagger validation runner
`discussion_tagger_eval` (`eval-tagger`, modes `accuracy`/`skill`/`deleak`), the diagnosis-sampler CLI
`diagnosis/case_sampler` (`eval-case-sample`, command wiring over the `diagnosis/` logic package), and
`graduate_run` (`eval-graduate`).

The frozen-set builders live in **`data/builders/`** (`agent_decision`/`extraction`/`dedup`, the
`eval-build-*` CLIs) — they write the read side, so they sit with `data/`, not `cli_runner/`.

Its former flatmates moved out on 2026-07-02:

- **`evaluation/src/audits/`** — the deterministic $0 checks that re-run on any new batch as
  regression audits: `dimension_audit`, `scheduler_access_audit`, `whiff_conversion_audit`, the
  proxy-validation trio (`proxy_rescue`/`accusation_metrics`/`claim_conversion` over the shared
  pre-registered split in `metrics_common`), the dedup golden scorers `dedup_score`
  (`eval-dedup-score`, online per-decision) and `batch_dedup_score` (the batch-cluster golden compare,
  split out of the old `batch_dedup_eval` monolith on 2026-07-03), and `recall_flags`. All
  pytest-covered; batch-record loading shared via `data/sources/batch_records.py`.
- **`studies/`** — the concluded one-shot study runners behind the v5→v6→v7
  store-evolution verdicts (the screen family, the v6 reextraction chain, the synthesis and
  calibration A/Bs). Promoted to its own top-level `evaluation/src/studies/` package on 2026-07-03 (out
  of the `experiments/`→`cli_runner/` rename — studies sit off the CLI surface, so they don't belong
  under it). Kept runnable because frozen `evidence/v7_final/` scripts import them and two held
  re-screens (dimension-gating, wolf) would run on them. The module → question → verdict → evidence
  table lives in `studies/__init__.py`.
- **`replay/decision_screen/`** — the reusable decision-replay engine extracted verbatim
  (golden byte-diff-verified) from the study monolith; the screens in `studies/` are thin consumers.

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

### Turn Eval (captured / action / e2e)

One runner (`eval-turn`, module `regen_replay.both.turn_eval`) judges a frozen turn,
optionally regenerating part of the pipeline first. Two orthogonal knobs:

- `replay`: `none` (judge the turn as captured — no regeneration), `action` (rerun
  the final discussion/vote prompt), or `all` (regenerate summary → retrieval →
  action). `--replay` overrides the config.
- `judge`: `off`, `application` (action-quality rubric), or `pipeline`
  (summary + retrieval + action rubric).
- `memory_mode` (when `replay=action`): `captured` (memories from the original run)
  or `none` (cleared). `replay=all` always retrieves from a `snapshot`.

`replay=none` example (judge as captured):

```json
{
  "dataset": "evaluation/frozen_eval_sets/memory_eval_001.jsonl",
  "replay": "none",
  "judge": "pipeline",
  "max_samples": 20,
  "judge_model": "gemini-2.5-pro"
}
```

`replay=all` example (full path against a snapshot store):

```json
{
  "dataset": "evaluation/frozen_eval_sets/memory_eval_001.jsonl",
  "replay": "all",
  "snapshots": [
    {
      "label": "v1_post_dedup",
      "observations_path": "memory_stores/v1_post_dedup/observations.json",
      "strategy_points_path": "memory_stores/v1_post_dedup/strategy_points.json"
    }
  ],
  "summary": { "label": "summary_current", "model": "gemini-2.5-flash" },
  "top_k": 3,
  "judge": "pipeline",
  "judge_model": "gemini-2.5-pro"
}
```

Run:

```bash
poetry run eval-turn --config evaluation/config/e2e/e2e_v2_memory.json
```

Templates: `evaluation/config/template/{captured,application,e2e}_example.json` (the
three `replay` presets). The `eval-captured` / `eval-application` / `eval-e2e` script
names remain as aliases of `eval-turn`. `replay=all` is the closest eval to the full
episodic memory system, but still at single-turn replay level, not full-game replay.

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
