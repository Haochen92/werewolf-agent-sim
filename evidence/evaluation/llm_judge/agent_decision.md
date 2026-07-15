# Agent-Decision Funnel — Evaluation Apparatus Report

> **Scope: the apparatus, not the design.** Covers *how we measure* each stage of the agent-decision funnel
> — what the agent **saw** (situation-summary) → what it **retrieved** → how it **used** it (application) —
> and *how far to trust those measurements* (L1 + L2). The component **designs** stay in their original
> folders (`extraction/situation_summary/`, `retrieval/`, `memory_system/strategy_adoption/`). Lens +
> skeleton: [`../report.md`](../report.md); ledger: [`../source_map.md`](../source_map.md).
>
> **Why one report for three stages:** the funnel's diagnostic value is *which stage fails* — a retrieval
> miss vs an application miss are different fixes. Splitting them loses the chain.
>
> **Verdict: 🟡 PARTIAL, weakest at the live edge.** Every stage's *live* judge is uncalibrated
> machine-on-machine; the one real anchor (situation-NDCG golden) isn't wired into retrieval; and the path
> actually shipping in v6 (baseline bi-encoder, rerank/filter OFF) is the **thinnest-measured** of all.

## Objective the apparatus targets

The funnel is the core of "does memory help, and *where*." To diagnose a null you must localise it: did
retrieval fire → was it relevant → was it used → did the decision change. The apparatus has a distinct
instrument per stage, and they do **not** share calibration.

---

## Stage 1 — Situation-summary (what the agent saw)

**L1 — three instruments, do not conflate:**
- **Pairwise-preference judge** (`judges/situation_summary_pairwise.py`, harness `experiments/summary.py` → console
  `eval-summary`): which of two summary variants is the better *retrieval query*. `PairwiseJudgeScores`
  (`core/schemas.py:79-84`): two `SummaryDimensionScores` × {faithfulness, specificity,
  retrieval_usefulness, non_redundancy, role_perspective} 1-5, + `winner` + `confidence`. Model =
  `JudgeConfig.model` (default **gemini-2.5-pro**, `config_schema.py:41`); `max_retries=1`. Position-bias
  controlled (order alternated by case index). **No ground truth.**
- **Single-rubric summary judge** (`judges/situation_summary.py::run_summary_judge`, harness `experiments/summary_eval.py`
  → console `eval-summary-rubric`): scores *one* summary on its own (not pairwise) against the same 5 dims via
  `SituationSummaryScores` (`core/schemas.py:222-269`). ⭐ The **only** funnel judge on a **stronger model** —
  `DEFAULT_SUMMARY_JUDGE_MODEL = gemini-3.1-pro-preview` (`summary.py:24`, the one intentional override of the
  package default; matched by `config_schema.py:191`). **No ground truth.** (Promoted to a console entry in the
  2026-06-29 experiments pass; distinct from the pairwise `eval-summary`.)
- **Golden-NDCG retrieval metric** (`labeling/label_scorer/situation_retrieval_ndcg.py`; **no console entry**,
  `python -m`): ranking quality of retrieved memories vs graded human relevance (0/1/2), NDCG@{3,5,10},
  **offline / zero API**. ⚠️ Two NDCG impls coexist (linear `rel` vs exponential `2^rel−1`) → cross-harness
  numbers not comparable.

**L2 — trust:**
- The headline **NDCG@10=0.83 is the linear-gain, N=20-human-case baseline**; the exponential re-score is
  **0.732@10**. The *live* golden file has grown to **108 cases / 1919 judgments**, labeller
  `human+claude+opus-4.6+4-model-consensus` — i.e. the "human golden" anchor is now **machine-augmented**
  (~20 human cases + auto-labels), never human-re-validated.
- **Stale:** anchored to `v4_deduped_v2` store + 2026-05 prompts; live is v6_1.
- **Levers within noise:** core-dilemma was net-**negative** on clean cases (−0.084) and was removed in v4;
  v4b prompt = **+0.061** (expanded-label; the +0.049 in source_map is the unlabeled-biased figure). Only
  **villager +0.196** survives — and that's an upstream **store-coverage** gap surfacing through stage 1, not
  a summary-quality finding (the harness can't separate bad-query from bad-store).
- Pairwise path has the **regen+judge confound** (generates both variants and judges in one pass); the NDCG
  path is clean (offline replay). NDCG results are **console-only** — no result artifact (a reproducibility gap).

**Verdict: 🟡 (leaning ⚠️ on freshness).** Genuinely the strongest *anchor design* in the repo (real graded
golden + proper offline NDCG), but stale, partly machine-anchored, small-N on the levers.
**Cheapest upgrade:** re-run NDCG golden-mode against the **v6_1 store** (offline, **free** — just repoint
the hard-coded `STORE_DIR`/`EVAL_DATASET` constants in `situation_retrieval_ndcg.py:41-42`); refreshes the single most-stale
headline number.
**Anchoring the summary judges:** the pairwise and single-rubric judges both grade summary *content* with **no
ground truth** — the same no-anchor gap as day-summary. The situation-summary is fundamentally an extraction
task (extract what is critical about the situation), so the fix is a reference-point golden set (critical
situation elements → coverage/recall, game-state faithfulness → precision):
[`golden_set_method.md`](golden_set_method.md). This is distinct from the NDCG golden above, which anchors
*retrieval ranking*, not summary content.

---

## Stage 2 — Retrieval (what it pulled)

**L1:** retrieval-quality judge (`judges/retrieval.py` → console `eval-retrieval`; replay
`replay/retrieval.py` rebuilds an `InMemoryStore` and retrieves **deterministically**). `RetrievalScores`
(`core/schemas.py:26-31`): `clusters[]`, `relevance` 1-5, `unique_lessons` ≥0, `efficiency` 1-5,
`brief_reasoning`. **`redundancy_ratio` is a deterministic derivation** (`1 − unique_lessons/item_count`,
`replay/retrieval.py:110-113`), **NOT LLM-judged** *(source_map error — see corrections).* Live judge model
= **gemini-2.5-flash** (config default, `config_schema.py:150`); the module constant
`DEFAULT_RETRIEVAL_JUDGE_MODEL = gemini-2.5-pro` (`retrieval.py:16`) is now **defined-but-unused** —
`run_retrieval_judge` (`retrieval.py:44`) makes `model` a required arg with no default. `max_retries=1`.
**Capacity** (top_k
3/5/7) is measured by the *application* proxy (`eval-application`, n=120), not this judge. `recall_flags.py`
is a deterministic pivotal-turn flagger (no LLM, no scores). `context_eval/` is a deferred labeling program.

**L2 — trust:**
- **`<2`-item fallback (verified):** relevance=1 **but efficiency=5 (max)**, redundancy_ratio→0; fallback
  rows are **silently pooled** into judged averages in **two** places (`experiments/retrieval.py:115-132` +
  `core/report.py:99-110`) with no counter → arm-asymmetric inflation (strategy_points often ≤1 item).
  **Nuance:** this is **current-code** behaviour; the *frozen evidence dumps* were produced by a legacy judge
  that returned `None` on `<2` (no Judge line on `(1 items)` blocks), so the **archived tables are not
  contaminated** — the bug bites the next run.
- **No golden anchor** — pure uncalibrated machine-on-machine (gemini-2.5-flash judging gemini-retrieved
  sets). A relevance golden *exists* (the stage-1 situation NDCG) but is **not wired into `eval-retrieval`**.
- **CE reranker NDCG@5=0.882** (CI [0.822,0.938]) is golden-labelled + leak-bounded (case-level hold-out;
  leak retrain within CI) — but graded against labels with a known **topical-over-credit bias** that modestly
  inflates the observation number.
- **Live v6 = baseline bi-encoder + per-situation cap=3; reranking AND filtering are OFF for every role**
  (`Agents/tracing.py:34-54` all-False). So the well-measured designs (rerank/filter) are **not live**, and
  the live path has the **weakest** dedicated apparatus (n=5 frozen scenarios + the v4-stale retrieval judge).
- Severe staleness (all v4 stores) + small-N (n=5 scenarios drive filtering/reranking conclusions).

**Verdict: 🟡 (the live retrieval judge alone is 🔴).** Cheapest upgrade: two ~1-line fixes — tag/exclude
`<2`-item rows from the efficiency/redundancy aggregates (+emit a fallback counter), and pin the live judge
model (or document the flash choice). The real fix (wire the situation-NDCG golden into `eval-retrieval`)
needs v6_1 re-labelling.

---

## Stage 3 — Application / adherence (how it used it)

**L1 — two judges:**
- **(A) ApplicationScores** (`judges/turn_action.py` → console `eval-application`; the *reported* instrument).
  Mixes adherence + quality: `action_quality` 1-5, `strategy_application` 1-5, `grounding` 1-5,
  `adoption_accuracy` 1-5 (nullable), `attribution_direction` over/under/accurate (nullable),
  `fabricated_claims[]`, `brief_reasoning` (`core/schemas.py:34-57`). The frozen n=120 runs used
  **gemini-2.5-flash**; the module constant `DEFAULT_APPLICATION_JUDGE_MODEL = gemini-2.5-pro`
  (`turn_action.py:18`) is **defined-but-unused** — `run_application_judge` (`turn_action.py:29`) makes `model`
  a required arg with no default. `max_retries=1`. `replay/turn_action.py` does captured-vs-none
  memory-swap replay; the n=120 report numbers came from `captured.py` (judge-only on frozen rows).
- **(B) DecisionAdherence** (`loop/memory_adherence.py`): per-memory `implied_direction` (verdict-aware),
  `action_followed`, `application`, `evidence`; gemini-2.5-pro; **outcome-blind**. Despite living in `loop/`,
  it's wired **only** into `decision_replay.py` (no console entry), **not** the v7 production loop.

**L2 — trust (the headline = uncalibrated):**
- **No human label exists** — every number is gemini-2.5-flash self-output; the report admits it
  ("no systematic pro-model evaluation was run"). `judge_validation_protocol.md` is the **designed-but-unrun**
  Bucket-B calibration: ~28 stratified judgments (oversample the contested 2-3 band), **blind** independent
  self-label (join on case ID, not review-and-agree), report within-±1-band agreement + a directional sign
  test. Cost ≈ **half a day, one labeller, zero new code/compute**.
- **Regen+judge confound** (eval-application regenerates the action then judges; decision_replay fuses
  `_replay_vote` + adherence judge). **Staleness** (pre-v5 sets; flash-vs-pro drift). **Small-N**: n=120
  *cases from only 3 games*, **v1 was n=30**, and a **single outlier game swings v3**. `adoption_rate` is
  **flat ~49-52% across all prompt versions** (the prompt moved accuracy, not volume — a near-zero-info dim).
- **Scope note:** the portfolio headline (memory-on vs off win rate) is **judge-free**, so this judge
  protects a *secondary qualitative* claim — calibration matters but isn't top-line load-bearing.

**Verdict: ⏸ DEFERRED (uncalibrated).** The one load-bearing human-uncalibrated judge; calibration is fully
designed but never run. **Cheapest upgrade: execute the existing Bucket-B protocol verbatim** (~half day,
zero code) — converts ⏸ → 🟡/✅ on the trust axis.

---

## Cross-funnel L2 themes

1. **Uncalibrated end-to-end.** Every *live* stage judge (pairwise summary, retrieval, application) is
   machine-on-machine. The only ground-truth anchors — the situation-NDCG golden and the CE-reranker golden —
   are (a) partly machine-augmented and (b) **not wired into the live judges** they could calibrate.
2. **The live path is the least-measured.** v6 ships baseline bi-encoder retrieval with rerank/filter OFF;
   the heavily-studied designs are dormant. Diagnostic confidence is highest where the code isn't running.
3. **Staleness is uniform** — every funnel anchor is on v4 stores + 2026-05 prompts + pre-backend-shift,
   and the live judge models drifted flash↔pro between module defaults and configs.
4. **Confounds recur:** regen+judge in the pairwise and application harnesses; the `<2`-item pooling in
   retrieval. (Retrieval's own judge harness is *not* regen-confounded — retrieval is deterministic.)

## Verdict + cheapest upgrades (whole funnel)

**🟡 PARTIAL** — the apparatus can localise a *gross* funnel failure but cannot certify near-peer
differences or trust the live edge. Three cheap, high-leverage upgrades, in order: (1) **run the application
Bucket-B calibration** (~half day, zero code) — closes the one ⏸; (2) **fix the retrieval `<2` pooling +
pin the model** (~2 lines); (3) **re-baseline situation-NDCG on v6_1** (free path edit). The deeper fix —
wiring the situation-NDCG golden into the live retrieval judge — needs v6_1 re-labelling (the deferred
context_eval program).

## Evidence (code + L2 artifacts)

- **Code:** `evaluation/src/judges/{situation_summary_pairwise,situation_summary,retrieval,turn_action}.py`,
  `judges/prompts/{situation_summary_pairwise,situation_summary,retrieval,turn_action}.py`, `judges/config.py`,
  `replay/{situation_summary,retrieval,turn_action}.py`,
  `experiments/{summary,summary_eval,retrieval,application,recall_flags,captured}.py`,
  `labeling/label_scorer/situation_retrieval_ndcg.py`, `loop/memory_adherence.py`,
  `core/schemas.py::{PairwiseJudgeScores,RetrievalScores,ApplicationScores}`.
- **L2 artifacts (pointed-at):** situation golden `../../extraction/situation_summary/outputs/retrieval_golden_labels.json`
  (⚠️ shared cross-component asset — read by reranker training + context_eval; do **not** move); the deferred
  calibration design `../../memory_system/strategy_adoption/judge_validation_protocol.md`; application results
  `../../memory_system/strategy_adoption/eval_results/captured_eval_*.jsonl`; CE reranker golden
  `../../fine_tuning/cross_encoder/reranker/`; retrieval frozen reports `../../retrieval/{filtering,reranking}/`.

## Colocation call (JIT, 2026-06-28)

**Stays put — nothing moved; all pointed-at.** This case unifies three physically separate folders, so a
*logical* section here is the natural home; a physical merge would shatter `extraction/`, `retrieval/`, and
`memory_system/`. The situation golden is a shared cross-component asset (reranker + context_eval) → must be
pointed-at. Key numbers distilled above for standalone value.

*(Inspected 2026-06-28 — three parallel apparatus reads, synthesised. Judge-folder verification sweep
2026-06-30 — re-pointed refactor-stale refs after the `prompts/`-package split, `config.py` model-DRY, and
`core/schemas.py` shift; refined the model-routing story (per-module `DEFAULT_*_JUDGE_MODEL` constants are now
unused aliases — `run_retrieval_judge`/`run_application_judge` require `model`); surfaced the previously
undocumented third Stage-1 instrument, the single-rubric `eval-summary-rubric` judge on gemini-3.1-pro-preview.
No verdict change — every live judge remains uncalibrated. Design-folder note 2026-07-02: the situation-summary
design folder (`extraction/situation_summary/`) was brought to the report+log standard — a destination-first
`report.md` (v6 cell schema, how it works today) + a curated `experiment_log.md` (the model-comparison and
golden-label-NDCG threads, originals verbatim in Appendices A/B). Apparatus and verdict unchanged.)*
