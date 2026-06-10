# Repo structure audit — pre-v5 refactor scoping

**Date:** 2026-06-06
**Purpose:** Map the whole repository structure before the v5 memory-store rebuild, so the
codebase is understood/owned well enough to debug and tweak, and so there is no structural blind
spot that could silently corrupt the critical memory-system evaluation (Phase C win-rate A/B).
**Status:** Audit only — no code moved. This is the reference for the planned refactor + the
test-gap closure that should precede it.

This audit was produced by four parallel read-only sweeps (Agents/ internals, top-level data
folders, evaluation/+scripts/, test coverage). Line/threshold references were spot-verified.

---

## 0. TL;DR

- **The folder sprawl is one unlabelled pipeline, not redundancy.** Everything top-level is
  justified-keep except `notebooks/` (1 stale file) and `evaluation/archive/` (confirmed dead).
- **The `Agents/` reorg is feasible and low-risk** for the high-value moves (LLM-factory fold,
  memory subpackage, memory-enrichment extraction). One import-cycle hazard to fix first.
- **The real gaping hole is test coverage**, not layout: the eval-critical paths
  (memory-enrichment gating, dedup thresholds, 3-faction winner) have *no* regression net, and
  their failure mode is a silent wrong number in the exact experiment we're about to run.
- **Recommended order:** critical-path tests → refactor (tests are its acceptance net) →
  verify/maybe-tweak extraction → v5 dump. Each step protects the next.

---

## 1. What every top-level folder is (the pipeline)

The data directories are not duplicative — they're stages of one flow, just unlabelled:

```
run_batch.py ─→ batch_results/   (game-run metadata; tracked; ~6M)
                     │
configs/eval/*.json ─→ dataset_builder ─→ eval_sets/   (frozen JSONL datasets; tracked; 22M)
                     │
eval_configs/*.json ─→ experiments/    ─→ eval_results/ (eval outputs; GITIGNORED; 8.6M)
                     │
                     └────────────────── ─→ evidence/   (permanent experiment archive; tracked)
```

| Folder | Role | The distinction that was unclear |
|---|---|---|
| `batch_results/` | game-run metadata (JSONL) | links game sessions → Langfuse trace IDs; read by dataset builders. Tracked (lightweight). |
| `configs/eval/` | **build-time** configs | "which Langfuse sessions to freeze into a dataset". Consumed by `dataset_builder` etc. |
| `eval_sets/` | frozen datasets (22M) | deterministic replay inputs; tracked *on purpose* for reproducibility. |
| `eval_configs/` | **run-time** configs | "replay this dataset with these variants + judge". Organised by subsystem (ablation/, reranking/, …). |
| `eval_results/` | eval outputs (8.6M) | ephemeral; **gitignored** by design. Safe to clean periodically. |
| `evidence/` | the archive | frozen reports + golds; the permanent experiment record. Not read by live code. |
| `models/` | CE/reranker weights (2.1G) | gitignored; rebuildable from Modal. |
| `notebooks/` | 1 stale `.ipynb` | **trim candidate** — unintegrated, last touched May 22. |

**Key mental model:** `configs` vs `eval_configs` = *build vs run*. `eval_results` vs `evidence`
= *scratch vs permanent*. No data is currently duplicated across them.

---

## 2. `Agents/` package — the reorg target

Today: `schemas/` and `prompts/` are clean subpackages; the other **19 files are flat**. Sizes &
the proposed home for each:

| File | Lines | Responsibility | Proposed home |
|---|---|---|---|
| agents.py | 1564 | **3 tangled concerns** (see below) | split |
| nodes.py | 1033 | orchestrator/day/night graph nodes | → `graphs/` (split by phase) — *deferrable* |
| memory_batch_deduplication.py | 1506 | batch clustering dedup (post-game CLI) | → `memory/` |
| memory_deduplication.py | 973 | per-extraction incremental dedup | → `memory/` |
| memory_persistence.py | 643 | seed/dump store to disk | → `memory/` |
| memory.py | 121 | store singleton + retrieval accessors | → `memory/` |
| retrieval_filters.py | 130 | MMR / dedup-gate / cap | → `memory/` |
| reranker.py | 104 | cross-encoder rerank | → `memory/` |
| llm_factory.py | 324 | model/embedding factory | keep (absorb the accessors below) |
| extraction.py | 130 | post-game extraction | keep (repoint its import — see hazard) |
| compute_metrics.py | 387 | outcome metrics + Langfuse publish | keep |
| state.py | 244 | TypedDict graph states | → `graphs/` — *deferrable* |
| scheduler.py | 160 | sequential-discussion speaker ranking | → `graphs/` — *deferrable* |
| formatters.py / prompt_inputs.py / run_fingerprint.py / game_config.py / tracing.py / main.py / constants.py | small | misc support | keep |

### 2.1 `agents.py` splits into three (no internal entanglement)

| Group | Lines (approx) | Symbols | Move to |
|---|---|---|---|
| A — LLM accessors | ~130 | `get_llm`, `get_llm_summary`, `get_llm_judge`, `get_llm_pro`, `get_llm_pro_backup`, `judge_proactive_novelty` | fold into `llm_factory.py` (pure wrappers, zero agents-specific deps) |
| B — memory-enrichment engine | ~300 | `_enrich_payload_with_memory` + `_memory_enabled_for_role` / `_filtering_enabled_for_role` / `_reranking_enabled_for_memory_kind` / `_retrieval_type_enabled` / `_store_dir_from_config` | new `memory/enrichment.py` (imports reranker/retrieval_filters/memory — belongs with them) |
| C — per-role act fns | ~240 | `*_discuss` / `*_vote` / `*_act` / `wolf_night_discuss` + `_run_agent` / `_run_memory_informed_action` / `_run_memory_informed_night_action` | stay in `agents.py` (graphs/ import them by name) |

### 2.2 ⚠️ Import-cycle hazard — fix BEFORE moving accessors

[extraction.py:6](../../Agents/extraction.py#L6) imports `get_llm_pro, get_llm_pro_backup`
**from `Agents.agents`**. If the accessors move to `llm_factory` while extraction still points at
`agents`, the import breaks. **Order:** repoint extraction (and the lazy `nodes.py` import of
`get_llm_summary`) at `llm_factory` first, *then* move the accessors. No reverse dependency exists
(agents.py does not import extraction.py), so no true cycle — just a stale path to update.

### 2.3 `Agents/memory/` subpackage — safe

The six memory files cross-import only each other + are imported externally (by `evaluation/`,
`scripts/`) **by specific symbol, not by module**. An `__init__.py` re-export (`from .core import
store, retrieve_observations_for_agent, …`) keeps every existing import path working → zero
external churn. No circular imports.

### 2.4 Graph colocation (state/scheduler/nodes → `graphs/`) — deferrable

`state.py` is pure schemas (moves anywhere); `scheduler.py` has no graph deps. `nodes.py` (1033L)
is a shared hub that would need splitting by phase (day / night / orchestrator) — higher churn.
**Recommend deferring** unless graph topology is already being touched; it's the one move that
isn't behaviour-trivial.

---

## 3. ⚠️ The actual gaping hole: no regression net on eval-critical paths

The test suite is **27 unit tests, almost entirely `test_scheduler.py`**. Everywhere else,
verification = "run a smoke game and eyeball it." That has worked because smoke games exercise the
happy path — but **a smoke game cannot catch a silent bug that yields a plausible-but-wrong
number**, which is precisely the failure that invalidates an A/B.

### Current coverage

| Test file | Real tests | Covers |
|---|---|---|
| `tests/test_scheduler.py` | 22 | speaker selection (reactive/proactive, K-cap, cooldown, passes) |
| `tests/test_memory_persistence.py` | 4 | retry logic, transient vs permanent embed errors, JSON seeding |
| `tests/test_memory_deduplication_tracing.py` | 1 | a span.update is called (mock) — **not** dedup logic |
| `tests/leak_test.py` | 0 (`check_*`, run post-game by run_batch) | private-info isolation |

### The eval-critical paths with NO unit/regression test, ranked by threat to v5/Phase C

| Rank | Path | Why this failure mode is the dangerous kind | Verified detail |
|---|---|---|---|
| 1 | **Memory-enrichment gating** — `_enrich_payload_with_memory` day-1 gate + per-role on/off routing | This *is* the Phase C independent variable. A silent gate-off makes the "memory-on" arm secretly run memory-off → the headline result measures nothing, and a smoke game looks identical. | config routing in agents.py Group B |
| 2 | **Dedup thresholds** | Silently shape what ends up *in* v5. Over-dedupe → thin memory; under-dedupe → noise. No test pins behaviour; an embedding change makes them meaningless invisibly. | `SP_ACTION_DISCARD=0.93`/`KEEP=0.81`, `OBS_CONTENT_DISCARD=0.96`/`KEEP=0.935`, retrieval net `0.55` — [memory_deduplication.py:35-46](../../Agents/memory_deduplication.py#L35-L46) |
| 3 | **`determine_winner` 3-faction rule** (new in Phase A#2) | Off-by-one in W≥T / SK-parity = wrong winner = every win-rate number invalid. Cheapest possible test (pure fn over counts). | [nodes.py:825](../../Agents/nodes.py#L825) |

**Downgraded from the sweep's "CRITICAL" (worth tests eventually, not blockers):**
`EvalCase` serialization (Pydantic `model_dump` is reliable; a malformed case fails *loudly* at
consume-time, not silently), extraction-returns-None (already retried + logged), reranker/MMR
(affects quality, not correctness).

The three top rows are untested **and** their failure mode is a silent wrong number in the very
experiment about to run. That is the gaping hole — not the file layout.

---

## 4. `scripts/` vs `evaluation/experiments/` — weak enforcement

The split is conceptually sound — `experiments/` = config-driven/reproducible; `scripts/` =
ad-hoc/CLI — but ~6 scripts (`extraction_model_comparison`, `judge_model_comparison`,
`per_role_comparison`, `per_role_judge`, `situation_summary_model_comparison`,
`situation_summary_rubric_judge`) **import** the shared `evaluation/` pieces yet **reimplement the
orchestration loop** (load dataset → iterate → call component/judge → write JSONL) around them.
That duplication is the "not modular enough to own" smell. Fix = extract a thin experiment-runner
the scripts call. Cleanup, not a blocker.

`evaluation/` subpackages, all load-bearing & clean except where noted:
`data/` (Langfuse↔case contract — recently built, leave alone), `core/` (config/schema/format),
`judges/`, `components/`, `experiments/`, `labeling/` (multi-model consensus framework) **vs**
`experiments/labeling/` (one-shot interactive tools — *different thing*), `training/` (Modal CE
training), `archive/` (**dead** — 1532L, referenced only in a comment, imported by nothing →
trim candidate).

---

## 5. Recommended sequencing

The refactor and the test gap converge on one order, because each step is the next one's safety net:

1. **Critical-path tests** (~1.5h, ~150 LoC): gating, dedup thresholds, `determine_winner`.
   De-risks v5 directly *and* becomes the acceptance net for the refactor — you cannot safely move
   `_enrich_payload_with_memory` into a new module without a test asserting its gating still behaves.
2. **Refactor** (behaviour-neutral): repoint extraction's import → fold LLM accessors into
   `llm_factory` → extract `memory/enrichment.py` → `memory/` subpackage. Acceptance per commit:
   tests green + `run_fingerprint` identical + a smoke game's traces unchanged. Defer graph
   colocation. **Touch zero prompts.**
3. **Verify extraction** (separate, deliberate): run the existing extraction judge over recent
   transcripts; *then* decide if the pre-v5 "slight prompt change" is warranted — as its own
   checkpointed change, not folded into the refactor (keeps the refactor verifiably neutral).
4. **v5 dump.**

### Note on the prompt/tracing "freeze" (re-examined)

The freeze rules protect **gold labels that don't exist yet** (all labelling is deferred to
post-v5). Pre-v5/pre-label is therefore the *last clean window* to change the extraction prompt,
not a frozen one. What actually survives as a constraint is thinner: (a) **checkpoint** whatever
prompt produces v5 (provenance), and (b) **keep the refactor verifiably neutral** by not folding a
deliberate prompt/schema change into the structural commits. Neither is "freeze." The trace schema
likewise is not sacred across the v5 cut (`schema_version` exists to rev it); it's out of refactor
scope only because the refactor is structural-only by choice.

---

## 6. Trim candidates (deletion needs explicit sign-off)

| Item | Why | Verdict |
|---|---|---|
| `notebooks/batch_analysis.ipynb` | single stale file, unintegrated | trim |
| `evaluation/archive/` (1532L) | confirmed: nothing live imports it | trim (or keep as explicit audit history) |
| `evaluation/experiments/labeling/` one-shot tools | interactive, not pipeline | keep, but consider isolating from the config-driven experiments |
