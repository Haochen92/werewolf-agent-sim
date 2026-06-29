# Labeling Pipeline — Evaluation Apparatus Report

> **Orientation.** The labeling pipeline is the project's golden-set **factory**: it turns raw candidate
> items (retrieval candidates, dedup pairs, day-summary pairs) into *trusted* labels via a multi-model
> triage with a human in the loop. In the eval ladder it is **modality (c)** — the gold that *validates*
> the cheap LLM-judges (see [`../report.md`](../report.md)). This is the **reference doc** for that
> apparatus: how it works, and how far to trust it. Companions in this folder: the forward
> [`plan.md`](plan.md) (the build) and [`experiment_log.md`](experiment_log.md) (the chronological journey
> it was distilled from). Reliability ledger: [`../source_map.md`](../source_map.md).
>
> **Mental model (one line):**
> `candidates → vendor-diverse panel labels → consolidate (vote → consensus + ties.json) → human labels ties / routed cases → re-consolidate → [calibrate vs human + bias/CI gate — NOT YET BUILT] → golden set`
>
> **Verdict: 🟡 a working, human-in-the-loop label-PRODUCTION engine missing its statistical-VALIDATION
> half.** The triage front is built and produced the real dedup + reranker goldens — and it **already uses
> human labels heavily**: it routes panel *disagreements* to a human, merges those human labels back, and in
> *both* rounds humans made the **decisive corrections** (§2). What is **not yet code** is the **statistical
> calibration** that certifies the panel is trustworthy enough to auto-accept the cases *no human read* —
> measuring the panel against a human *anchor* (agreement, bias, CI). *That measurement* was done **by hand**
> in those experiments — so "by hand" means the **calibration stats, not the labelling**. That gap is this
> report's headline, and the subject of [`plan.md`](plan.md).
>
> *(Scope: the apparatus, not the verdicts it produced. The downstream evals that *consume* these
> goldens — NDCG scorers, the dedup golden-scorer — are a different topic and stay in `experiments/`.)*

## 1. Current capabilities — what the pipeline does today

Present-tense contract, enforced in `evaluation/src/labeling/`:

**Given** a candidates file + a `LabelingAdapter` for the domain, the pipeline **produces** a consensus
golden-label set with a per-item agreement category, plus a `ties.json` of unresolved disagreements
routed to a human. Concretely:

| Stage | Module | What it guarantees |
|-------|--------|--------------------|
| **Single entry point** | `pipeline.py` (`run`/`label`/`export`/`consolidate`) | **NEW 2026-06-29** — one config-driven staged CLI assembling the automated stages: `LABEL → [EXPORT off-ramp] → CONSOLIDATE`. `run` = LABEL→CONSOLIDATE (no-human fast path). Before this, the pieces had no caller and couldn't compose (see *Topological flow* below). |
| **Multi-model labelling** | `engine.py::label_items` | Runs *N* models per item concurrently, **per-model token-bucket rate limiting**, checkpoint-every-*k* + **resume**. Adapter-pluggable; optional **structured output**. |
| **Consensus vote** | `voter.py::vote` | Per-item consensus → a **categorical** confidence: `unanimous` / `majority` / `tie_tiebreaker` / `tie` / `no_response`. **Rule:** majority = strict >½; an unresolved tie / no-consensus is **routed to a human**; an optional tiebreaker model can break ties. |
| **Consolidate** | `pipeline.py::stage_consolidate` | Votes across each engine entry's `model_scores` **+ human label files** (keyed by the entry's own `case_index:key`); emits consensus + `ties.json` + agreement tally. **Adapter-agnostic + multi-model-native** — replaces the now-**deleted** `merger.merge` (reranker-era: one-model-per-file + composite-key only, never composed with `dedup`). |
| **Human export** | `exporter.py::export_for_manual` | Batched markdown for hand-labelling in ChatGPT/Claude. Driven by `pipeline export`. |
| **Domain adapters** | `adapters/{reranker,dedup,context_relevance}.py` (+ `get_adapter` factory) | Per-task rubric prompt + response parsing + key normalization. New tasks subclass `LabelingAdapter` (`base.py`). `dedup` also opts into **structured output** (`response_schema`/`parse_structured`) for parse-robust golden minting. |
| **Dedup golden driver** | `dedup_golden_builder.py` | Runs `engine.label_items([one ModelSpec], DedupAdapter)` → the `eval_auto_dedup` golden shape. **Folds in the old `auto_dedup_labeler`** (deleted 2026-06-29) so the engine+adapter path — not a hand-rolled loop — mints the dedup golden. |
| **Human / retrieval CLIs** | `manual_labelers/{batch_dedup,situation_retrieval,day_summary}_labeler.py` | Interactive `show/sample/label/progress` tools (one runs live-store retrieval). **Not adapters, no panel, no copy-paste export** — the human labels in-terminal ("mode 3"). They don't fit the per-item LLM shape (cluster-MERGE ops, golden-query authoring, coverage annotation), so they're grouped in `manual_labelers/` (moved 2026-06-29) rather than the pipeline proper. |
| **Config** | `config.py` | `LabelingPipelineConfig` (the entry-point config) · `ModelSpec` · `VotingConfig` · `ExportConfig`. JSON-serializable, same pattern as `core/config_schema`. (The dead `LabelingRunConfig`/`MergeConfig`/`ManualSourceConfig` were removed with `merger`.) |

**In one sentence:** the pipeline can run a vendor-diverse panel over a corpus, fuse it into consensus
labels, split the corpus into *auto-labelled* (panel agrees) vs *routed-to-human* (panel disagrees), and
**merge the returned human labels into the final golden** — it is **human-in-the-loop by construction**,
the front half of the protocol in [`experiment_log.md`](experiment_log.md) and `context_eval` §6. (What it
does *not* yet do is tell you *which* agreements are safe to keep without a human — that's §3.)

### Topological flow (how to run it)

```
   CONFIG (LabelingPipelineConfig): candidates + adapter + models + output_dir
                          │
  ┌──────────────────── AUTOMATED ──────────────────────────────────┐
  │  [1] LABEL        pipeline label  → model_scores.json             │
  │         (optional human off-ramp ↓ instead of / alongside [1])    │
  │  [E] EXPORT       pipeline export → export_batches/*.md           │
  │         🧑 human labels in ChatGPT/Claude → response file         │
  │  [2] CONSOLIDATE  pipeline consolidate (+ manual_sources)         │
  │         → consensus_golden.json + ties.json                      │
  └──────────────────────────┬───────────────────────────────────────┘
              🧑 human resolves ties.json → add as a manual_source → re-consolidate
                             │
  ┌──────────── NOT YET BUILT (plan.md second half) ─────────────────┐
  │  [3] CALIBRATE  panel-vs-human agreement+CI, McNemar/TOST, audit  │
  └───────────────────────────────────────────────────────────────────┘
```

- **No-human run:** `pipeline run --config run.json` (LABEL → CONSOLIDATE).
- **Copy-paste run:** `pipeline export` → label batches in ChatGPT/Claude → save responses → set
  `manual_sources` in the config → `pipeline consolidate`.
- **Resolve disagreements:** resolve `ties.json`, add it as a `manual_source`, re-run `consolidate`.

**Why staged, not one call.** Each human point (EXPORT copy-paste; ties resolution; the CALIBRATE
anchor) is a *stage boundary*. A single non-stop entry point can't pause for a human; a staged +
resumable CLI can.

**What assembling it fixed (an apparatus finding).** Before 2026-06-29 the consolidation pieces
(`merger`/`exporter`) had **no caller and had never actually run end-to-end** — every golden to date was
stitched together by bespoke per-domain code, not by the reusable module. Wiring the stages into a single
entry point (`pipeline.stage_consolidate`) is what surfaced that they didn't compose; the new path votes
across the panel's per-model scores directly and is **adapter-agnostic + multi-model-native**
(smoke-tested in `tests/test_labeling_pipeline.py`). The superseded `merger.merge` was **retired** (git
history preserves it).

## 2. How we know the current capabilities work (verification)

Not asserted — *used*, **with humans doing the load-bearing labelling**. The triage front produced two
real golden sets, and in both the human was decisive, not decorative:
- **Dedup classifier** — 3-model panel over 863 LLM-decided cases → 619 unanimous / 244 disagreement →
  **humans reviewed all 244 disagreements *and* audited the 373 "safe" unanimous-D cases (617 manual-review
  records), correcting ~26% of the baseline model's calls** → the 863-case D/K golden (see
  [`experiment_log.md`](experiment_log.md) §3a, source: `../../fine_tuning/dedup_classifier/experiment_log.md`).
- **Reranker** — a vendor-diverse panel (ChatGPT + flash-lite + Mistral + NIM) labelled retrieval pairs,
  then **human manual batches (ChatGPT + Sonnet) corrected ~14 of 84 reviewed items** → the 0/1/2
  relevance golden (source: `../../fine_tuning/cross_encoder/reranker/experiment_log.md`). Here too the
  human was decisive — and the round's lesson (the auto models **over-credited relevance together**,
  caught only by a different-class judge, not by intra-panel agreement) is the second piece of evidence
  for §3's headline gap.

So the front half is **load-bearing and exercised**, and **the goldens are panel + human merges** — not
model-only auto-labels. What the pipeline *cannot* do is **measure** when the panel is trustworthy enough
to keep the cases a human *didn't* read — turn "the panel agreed" into a calibrated confidence. That is §3.

## 3. Limitations + what we plan to build (known gaps)

Criticality-ordered (likelihood × impact × detectability). Freshness: **verified 2026-06-29** against the
current `evaluation/src/labeling/` tree. The build that closes them is [`plan.md`](plan.md); each gap
below names the artifact that will close it.

1. **No panel→human calibration / acceptance test — criticality: HIGH.** Human labels *exist* and are
   merged in (above) — the gap is **code that statistically compares the panel to a human anchor**, so the
   pipeline cannot certify "the panel is trustworthy enough to auto-accept the cases no human read." The
   protocol's acceptance gate (agreement ≥80%, 95% CI lower-bound ≥75%, no significant directional bias)
   was computed **by hand** in every round. → builds `calibration.py::calibrate()` + the gate.
2. **No statistical bias detection — criticality: HIGH.** The most important empirical finding of the
   labelling work is that **a same-vendor panel shares a correlated bias that intra-panel agreement
   cannot reveal** (the dedup D-bias; the reranker over-crediting — §3 of the log). The module's only
   agreement code is `voter.agreement_stats`, a **descriptive tally** — it cannot detect directional
   skew. → builds `calibration.py::bias_test()` (McNemar/sign for *presence*, TOST for *absence* vs a
   pre-registered δ).
3. **No confidence interval on the labelling — criticality: MEDIUM-HIGH.** The voter's "confidence" is
   *categorical* (how the panel voted), **not statistical** (how much to trust it vs truth). There is no
   agreement CI, and — critically — judgments **cluster within a case** (design effect), so a naive
   binomial CI would *overstate* precision. → builds a **cluster-robust (by-case bootstrap) agreement CI**
   + a `sample_size_for_ci()` calculator (the ±X%→N table).
4. **No per-judge / unanimity-tier audit — criticality: MEDIUM.** The protocol's "unanimity is suspect a
   priori" insight needs the skew test run *on the unanimous-agree subset specifically*; and per-judge
   skew (which vendor pulls which way) is never reported. → builds `calibration.py::tier_audit()` + a
   per-judge skew table.
5. **No inter-annotator κ — criticality: LOW.** When a 2nd human dual-labels a slice, there's no Cohen's
   κ. → builds `cohens_kappa()`.
6. **No stratified anchor sampler — criticality: MEDIUM (it gates everything above).** The calibration
   needs ~100–250 human *judgments* stratified by type × agreement-pattern × role, oversampling the
   confident-agree zone, spread across cases. The existing `data/sampling.py` samples *game cases* (wrong
   unit). → builds `anchor.py`.
7. **Rubric parity human↔panel — criticality: LOW.** The panel prompt embeds the rubric
   (`adapter.format_prompt`), but `exporter.format_for_manual` is generic — the human and the panel should
   judge against the *identical* rubric + worked edge cases. → small `exporter`/adapter extension.

**The through-line:** items 1–4 are one missing capability — *the pipeline can produce labels but cannot
say whether they are right*. It is a factory with no quality-control bench. The protocol that designs the
bench already exists (`context_eval` §6); the statistical primitives already exist (`core/stats.py`:
Clopper–Pearson `binomial_ci`, exact `mcnemar_exact`); what's missing is the ~one module that wires them
to a human anchor. That is [`plan.md`](plan.md).

## 4. The build plan (summary)

Full plan: [`plan.md`](plan.md). In brief: a new `calibration.py` + `anchor.py`, three small `core/stats`
additions (TOST, κ, cluster-robust agreement CI), a `CalibrationConfig`, and a thin staged driver that
runs `panel → sample → [human pause] → calibrate → decide(stop/expand) → gold`. Sequenced MVP-first
(Phase 1 = the acceptance test on pure `core/stats` reuse). **Gated**, not urgent: it needs a
vendor-diverse panel run, ~100–250 human judgments, and a stable substrate — so the build unlocks value
only when labelling restarts (which is itself gated on v7 proving memory compounds; see
[[project-ship-roadmap]]).

## Evidence, code & provenance

- **Code (the apparatus):** `evaluation/src/labeling/{engine,voter,exporter,base,config,pipeline}.py`,
  `adapters/{reranker,dedup,context_relevance}.py`, the `dedup_golden_builder.py` driver, and the 3
  human/retrieval CLIs in `manual_labelers/`. Tests: `tests/test_labeling_pipeline.py`,
  `tests/test_dedup_golden_builder.py`. Primitives to reuse: `evaluation/src/core/stats.py`.
- **The design spec for the unbuilt half:** `../../retrieval/context_eval/experiment_log.md` §6 "The
  labeling protocol" (pre-registered acceptance test, staged bias detection, sample-size table).
- **The journey + the limitation evidence:** [`experiment_log.md`](experiment_log.md), distilled from
  `../../fine_tuning/dedup_classifier/`, `../../fine_tuning/cross_encoder/reranker/`,
  `../../retrieval/context_eval/`, `../../fine_tuning/cross_encoder/dedup_prefilter/`.

*(Reference doc, drafted 2026-06-29. Subject to revision as the labelling + scorer inspection continues.
The `labeling/` code folder is slated to rename to `labeling_pipeline/`; update the code refs above when
that lands.)*
