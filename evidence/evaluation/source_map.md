# Evaluation System — Source Map & Reliability Inventory

> **Working doc (2026-06-27).** The pre-write-up inventory for the eval system — the *judge* half of
> the capture↔judge split (capture = `evidence/tracing/report.md`). Built from two sweeps: a code map of
> `evaluation/` + a reliability read of the eval-method evidence. Purpose: stamp down **what each eval
> piece is, where it lives, and HOW RELIABLE it is** — because that gates how much we can trust the v7
> A/B run (and what we can conclude if it's inconclusive).
>
> **Folder home is provisional.** This seeds a candidate `evidence/evaluation/` hub; final placement is
> the deferred `evidence/→experiments/+decisions/` taxonomy call. Don't treat the folder as settled.
>
> **Companion: [`report.md`](report.md)** = the synthesised **case-type × modality view** (the judge-half
> write-up). Decided 2026-06-28: it's a **logical** view — folders stay physically intact, the report points
> *into* them — and per-case we decide just-in-time whether a physical colocation earns itself. This
> `source_map.md` stays the inventory + reliability audit it links back to.
>
> **Reliability is NOT verified end-to-end.** Unlike tracing (simple in principle + execution), this is
> the most complex system after the memory design and co-evolved with it. Statuses below were *as-claimed
> in the evidence*; the 🔍 flags were **verified in code on 2026-06-28** — corrections folded into the
> tables; see **VERIFY-IN-CODE PASS — RESULTS** at the tail for the per-item verdicts.

## Reliability legend

| Tag | Meaning |
|-----|---------|
| ✅ **VALIDATED** | rigorously checked (correlation / held-out / cross-method convergence) — trust within stated power |
| 🟡 **PARTIAL** | validated in part; real caveats |
| ⚠️ **CLAIMED-UNVERIFIED** | asserted but not independently checked, or known confound/outcome-halo |
| 🔴 **WEAK / NULL** | measured weak/null, or "not robustly demonstrated" |
| ⏸ **DEFERRED** | designed, not executed (e.g. human judge calibration) |
| 🔍 **NEEDS-CODE-READ** | behaviour not confirmable from docs/sweep — verify in code before trusting |

## The spine (how to read this inventory)

The eval system is **two tiers + cross-cutting instruments**, sitting on a data substrate:

```
Tier 0  DATA PLANE      frozen cases → sampled sets        (boundary object; mostly capture)
Tier 1  END-TO-END A/B  "did it work?"  memory-on vs off, de-lucked whole-game outcome
Tier 2  COMPONENT FUNNEL "why?"  situation → retrieval → application → (extraction/dedup/day-summary)
 X-cut  METRICS         de-lucked outcome proxies (the scoring instruments both tiers rely on)
 X-cut  A/B METHODOLOGY drift guards · variance · fair-at-low-N (the "directional despite low N" layer)
 V7     LOOP            generational compounding (credit → consolidate → measure)
 PARK   LABELING/TRAIN  fine-tuning data (CE reranker, dedup classifier) — secondary, parked
```

The **diagnosis funnel** (how you drill into a null result) maps onto Tier-2 modules — see the last section.

---

## Tier 0 — Data plane / case-IO (the input substrate)

Mostly the *capture* side's output; included because the eval reads it. Boundary object = the frozen case/set.

| Piece | Code | Reliability | Notes |
|-------|------|-------------|-------|
| Frozen-set builder | `experiments/dataset_builder.py` (`eval-build-dataset`) → `frozen_eval_sets/<id>.jsonl` + `.manifest.json` | ✅ (tested: `test_eval_case_sink`, `test_local_case_source`, `test_langfuse_fetch`) | source = local sidecars (preferred) or Langfuse |
| Stratified sampling | `data/sampling.py` (`sample_cases`) | ✅ (tested: `test_sampling`) | **default day-only**; `night_action` opt-in via `action_phases`. Stratifies by game/role/phase/action. **This is the eval-side selection policy** (vs capture). |
| Case loaders | `data/{cases,local_cases,datasets,extraction_cases,dedup_cases,day_summary_cases}.py` | ✅/🟡 | legacy span/decision formats (A/B/C→K/M/D) mapped; old formats in `archive/legacy_cases.py` |
| Langfuse read | `data/langfuse.py` | 🟡 | network-dependent; the post-422 cheap-read path (capture report §4) |
| Provenance manifest | `core/manifest.py` (tested), `core/costs.py` | ✅ / ⚠️ | costs.py has magic `chars/token=4` + dated Gemini-only pricing → **cost figures are estimates, not billing truth** |

---

## Tier 1 — End-to-end A/B ("did it work?")

| Piece | Code | Evidence | Reliability | Notes |
|-------|------|----------|-------------|-------|
| Paired A/B (deciding run) | ⭐ **`scripts/run_batch.py`** (paired-by-`game_id`) → `paired_ab/analyze_ab.py` → `core/stats.py` (NOT `synth_deluck_ab.py`/`e2e.py` — those are a synth-A/B + a turn-replay); apparatus → [`evaluation/end_to_end_ab/report.md`](end_to_end_ab/report.md) | `memory_system/effectiveness/paired_ab/{report,experiment_log}.md` | ✅ **VALIDATED** (N=30, **same-epoch drift-controlled**; game_id-paired but **seed-luck≈0 → pairing adds ~no power**) | **town helps +17/+23pp** (win underpowered MDE~36pp; **proxies carry the signal** — correct_elim p=.028, mislynch p=.036, healer_save p=.005, all **Wilcoxon**); **wolf/SK null** (channel-limited) |
| Older does-memory-help | (run_batch arms) | `memory_system/effectiveness/report.md` | ⚠️ **CLAIMED-UNVERIFIED** | Batch A 70→97% (p=.012, but best-of-6 → Bonf p≈.073) **NOT replicated** Batch B (73.3%, p=1.0). 23pp swing = store+namespace confound. Establishes the *ceiling* + *config-sensitivity*, not a verdict. |

**Headline you can trust:** town memory helps (direction robust). **Caveat:** win-rate underpowered at N=30; the *proxies* are the evidence, so Tier-1 trust inherits Metrics reliability (below).

---

## Tier 2 — Component funnel ("why?")

The per-stage judges/replay that explain a Tier-1 result. **All judges are LLM-based (`max_retries=1`) → inherently noisy.**

| Stage | Code | Evidence | Reliability | Notes |
|-------|------|----------|-------------|-------|
| Situation-summary | `replay/situation_summary.py`, `judges/pairwise_summary.py`, `experiments/summary.py` (`eval-summary`) | `extraction/situation_summary/{experiment_log,report}.md` | 🟡 **PARTIAL** | golden NDCG@10=0.83 baseline solid; v4b prompt +0.049; **specific levers (core-dilemma, criticality) within noise**; villager weakest role |
| Retrieval relevance | `replay/retrieval.py`, `judges/retrieval.py`, `experiments/retrieval.py` (`eval-retrieval`), `experiments/recall_flags.py` | situation NDCG; `retrieval/` | 🟡 **PARTIAL** | **VERIFIED:** `<2 items` short-circuits the LLM → relevance=**1** (min) but efficiency=**5** (max) (`judges/retrieval.py:19-30,48`) — *not* "minimal." Net bias: efficiency UP, redundancy_ratio→0, relevance DOWN. ⚠️ fallback rows are **silently pooled** into the judged averages (no counter); strategy_points often return ≤1 item → a thin/off arm gets inflated efficiency = arm-asymmetry in the *diagnostic* metric. Live judge model = gemini-2.5-flash (config), not the module's 2.5-pro. |
| Application / adherence | `replay/application.py`, `judges/application.py`, `experiments/application.py` (`eval-application`), `loop/memory_adherence.py` | `memory_system/strategy_adoption/{report,judge_validation_protocol}.md` | ⏸ **DEFERRED** | adoption tracked + v2 prompt locked (n=120, machine-judge only) but **NO human calibration** — the one load-bearing judge is uncalibrated |
| Decision-replay screen | `experiments/decision_replay.py` | `memory_system/effectiveness/decision_replay/{experiment_log,report_screening_layer}.md` | ✅ **VALIDATED (as a screen)** | converges with paired A/B (town helps where prompt THIN, null where hard-coded). **Off-policy; ±5–9pp; triage not verdict.** |
| Extraction judge | `judges/extraction.py`, `per_role_extraction.py`, `experiments/extraction_eval.py` (`eval-extraction`, ✅ real entry `pyproject.toml:37`), `extraction_builder.py` | `extraction/quality/report.md`; apparatus → [`evaluation/extraction/report.md`](extraction/report.md) | 🟡 **PARTIAL — de-bugged, NOT calibrated** (apparatus-inspected 2026-06-28; ⭐ downgraded from ✅) | 2 judge bug-fixes verified live (epistemic scope, specificity-field); player-ID mechanical check sound (0% most models, **2.5-flash still leaks**). BUT **machine-only, no golden/human anchor** (fails the ✅ bar its own legend sets); original 5 dims **ceiling-saturated** (only added strategy_depth/novelty discriminate); model-ranking **n=5-10 + regen/backend-confounded**; **v7 synthesis quality UNJUDGED**. Engineering-strong, not validated. |
| Dedup judge (×2) | `judges/dedup.py` (online K/M/D) + `judges/batch_dedup.py` (batch merge); **golden scorer** `experiments/dedup_score.py` (no console entry) + `eval-dedup` (LLM judge) | `dedup/{per_extraction,batch_dedup}/experiment_log.md`; apparatus report → [`evaluation/dedup/report.md`](dedup/report.md) | 🟡 **PARTIAL** (apparatus-inspected 2026-06-28) | TWO layers: **deterministic golden scorer = the system's STRONGEST L2** (human golden 65 online / 111 batch keys; 78-89% decision accuracy) — but the **LLM quality judges** (`DedupScores`/`BatchDedupMergeScores`, incl. the load-bearing `fabrication_detected`) are uncalibrated, and golden numbers are **stale** (pre-v6 prompt/gate + Google→Vertex shift). ✅ `batch_dedup.py:87` silent-fail bug **FIXED 2026-06-28** (was swallowing ALL errors; now split-handled). Irony: strong scorer has no console entry, weak judge does. |
| Day-summary judge | `judges/day_summary.py`, `experiments/day_summary_eval.py` (**module-only, no `eval-*` script**) | `extraction/day_summary/experiment_log.md` | ⚠️ **CLAIMED-UNVERIFIED** (apparatus-inspected 2026-06-28; report sharpened 2026-06-29) | machine-judge-only, **no golden/human calibration**; **reference-based** (judge sees the transcript) so saturation is **mechanistic, not uniform** — grounded dims (`completeness`/`accuracy`/`epistemic`) MOVED & caught real bugs (dropped accusers, fabricated GM announcement), presence-check dims (`village_dynamics`=5.00 flat, `evidence_type`) saturate on prompt-forced structure → trust as a *smoke alarm*, discard as a *ranker*; underpowered (n=18 single-run, opportunistic/un-stratified, "indistinguishable"); **regen+judge confound** (harness regenerates AND judges in one pass → can't isolate judge vs gen noise); **measures intrinsic rubric quality, not the stated objective** (downstream usefulness). = a **smoke test, not a metric** (report.md case 1). |
| Criticality screen | `experiments/criticality_screen.py` | `phase_b/criticality_screen/experiment_log.md` | 🔴 **WEAK / NOT ROBUST** | conditioning retrieval on criticality **does not reliably help** (within ±0.03 noise; high-crit N=7–23). Kept as metadata gate, **not a live lever.** |
| Forced-schema screen | `experiments/forced_schema_screen.py`, `dimension_gating_screen.py` (tested) | `phase_b/forced_schema_screen/experiment_log.md` | 🟡 **DIRECTIONAL** | safe on v6 (+0.021, N=48); coverage fix (prompt-body) 0.27→0.97; adopted, not deployed at scale |

---

## Cross-cutting — Metrics (the scoring instruments)

The de-lucked outcome proxies that **both tiers depend on.** This is where Tier-1's trust actually lives.

| Proxy group | Code | Evidence | Reliability | Notes |
|-------------|------|----------|-------------|-------|
| Town primary basket | `Agents/compute_metrics.py` + `core/stats.py` | `metrics/{proxy_win_monotonicity,town_metric_refinement}.md` | ✅ **VALIDATED** | `town_vote_accuracy`, `correct_elimination_rate`, **`town_mislynch_rate`** (the old `mislynch_rate` was an internal decision-replay key, not this field), `serial_killer_lynched` — \|r\|≈0.55–0.65, p<0.01 (**point-biserial**; N=50/180). **The trustworthy core.** |
| Investigator | ″ | `metrics/town_metric_refinement.md` | 🟡 **PARTIAL** | only `investigator_find_to_lynch_rate` (conversion) validated (+0.396); **find-rate NOT validated** (~0) |
| Deceiver (wolf/SK) | ″ | `metrics/deceiver_metric_refinement.md` | ⚠️ **CLAIMED-UNVERIFIED** | SK kill metrics OK (+0.26..+0.32); `wolf_suspicion_drawn`/`sk_suspicion_drawn` (faction-split; outcome-proximate tautology); **wolf offense null/unmeasured** |
| Discussion scoring (metrics **proxy**) | `metrics` Phase 1; Phase 2 deferred | `metrics/discussion_scoring_plan.md` | 🔴 **NULL / DEFERRED** | the *metrics-basket* discussion proxy: Phase-1 lead-vs-blend r=−0.093 (null); Phase-2 exposure-trajectory tagger deferred. ⚠️ **NOT the v7 loop tagger** — that one IS built (see Loop §). |
| Metric design v2 | — | `metrics/experiment_log.md` | ✅ design / 🟡 impl | basket rationale locked; per-proxy validation is the rows above |

> **Verified:** `push_scores_to_langfuse` (`compute_metrics.py:519-550`) pushes **every** non-None metric field
> (~50, str→CATEGORICAL / else NUMERIC), not a curated basket — the "validated proxies get pushed" claim is
> true but the push is *indiscriminate*. **Significance machinery** (`core/stats.py`): Clopper–Pearson CIs
> (analytic, **not** bootstrap) · Fisher exact (unpaired) · exact McNemar + Wilcoxon signed-rank (paired) ·
> point-biserial (proxy validation); all two-sided; **no built-in multiple-comparison correction** (Bonferroni
> is applied by hand in the evidence scripts). It's the *primary* home, not the only one (a couple of evidence
> scripts call scipy directly).

---

## Cross-cutting — A/B methodology (fair & directional at low N)

The "make low-N runs trustworthy" layer. **`metrics/variance_reduction_levers.md` is mis-filed here (it's method, not a metric)** — absorb into this section of the write-up.

| Piece | Code/Evidence | Reliability | Notes |
|-------|---------------|-------------|-------|
| Drift guards | `model_drift/drift_surfaces_and_guards.md`; `Agents/run_fingerprint.py` | ✅ **DOCUMENTED** | Jun-11 drift caught (p=.0028); fix = **interleave arms, never compare cross-epoch** + $3 canary. Judge **backend is env-driven, NOT a pinned constant** — but recorded in `runtime_fingerprint.llm_backend` + hard-asserted constant *within* a loop run (`assert_fingerprint_consistent`); cross-run safety = detection, not pinning (a human must still check it matches). Embedding alias still unpinnable; cross-day gate **manual**. |
| Variance / power | drift doc (the MDE/seed numbers live here, not in `variance_reduction_levers.md`); apparatus → [`evaluation/methodology/report.md`](methodology/report.md) | 🟡 | seed effect ≈0; **MDE at N=30 ≈0.18 vote-acc / ~36pp win** → win structurally underpowered; **pairing BUILT but ≈0 variance power** (same-epoch is the real control); bootstrap proposed; **CUPED N/A** (no pre-treatment covariate) |
| Paired same-seed design | `paired_ab/experiment_log.md` | ✅ | within-pair, same board, same-epoch baseline |
| Arm-guard | `--expect-factions` → `loop/{driver.py:331,invariants.py:185-210,config.py:19}` (**NOT** `run_batch.py`) | ✅ **VERIFIED (hard-fails ×2)** | fail-closed: `assert_arm_declared` blocks all spend unless declared (or explicit `--unchecked-arm`); `assert_arm_factions` reads the ON arm's *actual* enabled factions → **raises** `ARM MISMATCH` at gen 1. Kills the v2 arms-race confound at the source. |

---

## v7 — Loop subsystem (generational compounding)

Well-tested mechanically; the *measurement* is LLM-free, the *credit tiers* are paid.

| Piece | Code | Reliability | Notes |
|-------|------|-------------|-------|
| Driver / orchestration | `loop/driver.py`, `config.py` | 🟡 **VERIFIED (32 config fields, small confound surface)** | both arms run **same gen, same boards** → credit/synth/prune/model toggles arm-symmetric by construction. ⚠️ dead/footgun: `arm` is **label-only (not read)** — `arm=off` does NOT give a memory-off run; `frozen_base_rates` declared but unwired. reranking/filtering aren't loop config (run_batch flags the loop never sets → rerank-OFF/filter-OFF). See toggle-locks table below. |
| Credit apply | `loop/credit.py` (tested `test_credit_blend`), `credit_backfill.py` | 🟡 | `discussion_mode=tagger` (DEFAULT) = **paid** omniscient tagger; the rolling window *conceptually* re-tags every gen (O(gens²) worst case) but a **per-`game_id` tag cache (default-on, `driver.py:260`) dedupes it → realized paid LLM calls are O(gens)**; `discussion_mode=floor` = free day-vote endpoint; rolling-window non-stationarity guard |
| Consolidate | `loop/consolidate.py` (tested), `merge.py` (tested) | ✅ mechanics | prune/evict offline-testable; synth+SP-dedup paid; PROVEN-SP exemption |
| Measure | `loop/measure.py` (tested) | ✅ **LLM-free** | per-faction de-luck slope; buckets by arm; skips day-1 |
| Invariants | `loop/invariants.py` (tested) | ✅ | explicit store/credit/faction assertions |
| Discussion tagger (v7 credit) | `loop/discussion_tagger.py` (`0762e72`; tested inputs) | 🟡 **VALIDATED METRIC, not yet a memory verdict** | omniscient LLM verdict (noisy) — deleak-ablated (leak negligible, N=6) + blinded/verbosity-controlled retest (N=24) → real wolf/SK discussion signal the vote proxy misses: partial r(verdict, **won** \| deluck, verbosity) ≈ +0.56 wolf / +0.60 SK (town +0.02). ✅ **halo-tension RESOLVED** (verify-#9): the retracted +0.556 is a *different quantity* (undifferenced **town** credit-level), not this wolf/SK corr-with-win. Open: correlational (validates the metric, NOT a memory effect), single-epoch, uncalibrated. |

> Loop mechanics are the best-tested part of the eval system. The **open question is the science** (does
> memory compound), not the plumbing — and that rests on Metrics + A/B reliability above. See
> `project-ship-roadmap` / `project-v7-loop-graduation` memories: both v2 paid runs were INVALID; the
> compounding question is OPEN.

### v7-loop toggle-locks (what MUST be pinned for a fair A/B — verified 2026-06-28)

The loop runs **both arms in one generation on the same boards** (`driver.py:136-155`; OFF arm hard-wired to
`all_disabled --no-memory-seed --no-memory-dump`), so credit/synth/prune/evict/decay/model toggles are
**arm-symmetric by construction** — they evolve the *shared* store identically between gens. The actual
confound surface is small; lock these before any v7 run:

| Lock | Where | Why it confounds |
|------|-------|------------------|
| `expect_factions` + matching `configs` | `config.py:19` (+ `--configs`) | THE v2 trap. ON-arm factions come from `configs` (default `all_enabled` = **all roles** = the arms-race board), NOT from `arm`. For town-only pass BOTH `configs=town_only` AND `--expect-factions town_only`; the guard hard-fails on mismatch but YOU declare intent. |
| `base_store` | `run_loop`/CLI arg (`driver.py:158`), **not** a config field | seed store + namespace = the documented 23pp Batch-A/B confound. |
| `model` + `dedup_model` | `config.py:17,65` | temp-0 scores differ across model/backend — pin one tier across compared runs. |
| `off_baseline=True` | `config.py:33` | False removes the same-epoch de-luck baseline (credit silently falls back to ON-derived base rates, haloed). |

**Cost:** `discussion_mode=tagger` (default) is paid (**~O(gens) realized** — a per-`game_id` tag cache dedupes the rolling re-tag; O(gens²) is the uncached worst case); set `floor` for cheap/zero-spend smoke.
Paid ops = synthesize, sp_dedup, tagger, obs_dedup_merge — everything else is free/deterministic; `measure.py`
is entirely LLM-free.

## Parked — Labeling + Training (fine-tuning data)

**Structural moves 2026-06-29:** `training/` left `evaluation/` for **repo root** (it trains models, it doesn't judge cases). `evaluation/src/labeling/` was **repurposed** as the consolidated labelling home, with the per-domain golden-label tools moved in from `experiments/`. Root `training/{engine,adapters/*,runner/modal_runner}` = CE training (dedup classifier, reranker). **Secondary/parked** (see `feedback-memory-pipeline-prompt-freeze`, `project-fine-tuning-plan`) — not on the headline eval path; map but don't centre the write-up on it.

**Engine+adapter consolidation 2026-06-29 (Step 1):** the generic multi-model engine `{engine,voter,merger,exporter,adapters/*}` is **no longer orphaned in the live tree** — `auto_dedup_labeler` (a single-model LLM labeler that verbatim-duplicated `DedupAdapter`) was **folded into the engine+adapter path and deleted**. The engine gained **optional structured-output** support (`adapter.response_schema`/`parse_structured`, additive — other adapters keep the free-text path); `DedupAdapter` now owns prompt + structured K/D parse; the thin `dedup_golden_builder` driver runs `engine.label_items([one ModelSpec], DedupAdapter)` → the `eval_auto_dedup` golden shape. Equivalence to the old labeler proven by byte-identical prompts over all 232 cross-game cases (no API spend). The reranker/`context_relevance` adapters remain exercised only by **frozen evidence scripts** (`evidence/.../scripts/*`, old `evaluation.labeling` import path). The **three remaining tools are interactive human CLIs** (`batch_dedup_labeler` cluster-MERGE, `situation_retrieval_labeler` live-store retrieval, `day_summary_labeler` coverage) — no panel, no copy-paste export, human labels in-terminal; they don't fit the per-item adapter shape, so they were grouped into `labeling/manual_labelers/` (2026-06-29) rather than the pipeline proper. NOTE: golden-label *creation* is genuine modality-(c) eval infra.

**Pipeline assembly 2026-06-29 (entry point):** added `labeling/pipeline.py` — one config-driven staged CLI (`run`/`label`/`export`/`consolidate`) that finally assembles the automated stages (`LABEL → [EXPORT off-ramp] → CONSOLIDATE`). Surfaced that the pieces never actually composed: `merger`/`exporter` had **zero callers**, and `merger.merge` assumed one-model-per-file + the reranker adapter's composite `item_key` (broke for `dedup`). `pipeline.stage_consolidate` votes adapter-agnostically across the engine's per-entry `model_scores` (+ human label files), and **`merger.merge` was retired/deleted** (it never composed; git history preserves it — its dead `MergeConfig`/`ManualSourceConfig`/`LabelingRunConfig` went with it). Smoke-tested in `tests/test_labeling_pipeline.py`. Topological flow + run instructions now in `labeling/report.md` §1.

## Archive (superseded — do not import live)

`archive/{legacy_cases, legacy_retrieval_judge, eval_retrieval_v1, situation_summary_model_comparison, dedup_model_comparison}.py`.

---

## v7-RUN TRUST SCORECARD (the bottom line)

**Trust (validated + convergent):**
- **Town memory helps** — paired A/B (N=30) + decision-replay screen converge; town proxy basket \|r\|≈0.6.
- **Drift is controlled** — same-epoch interleaved arms + canary.
- **Extraction quality** judge is engineering-strong (2 real bug-fixes) — but **de-bugged ≠ calibrated** (machine-only, no golden; 🟡 not ✅ as of 2026-06-28).

**Do NOT over-read (the reliability ceiling):**
1. **Win-rate is underpowered at N≈30** (MDE ~36pp) — proxies carry all the signal; a "null" win-rate ≠ no effect.
2. ⭐ **The wolf-memory null is a POWER + INVALID-RUNS problem, not a missing instrument — and the old
   "halo-vs-skill tension" is RESOLVED (verified 2026-06-28).** Both channels where wolf memory might help
   have been probed: (i) the **v7 loop discussion tagger is a VALIDATED deceiver-skill metric** — blinded +
   verbosity-controlled + deleak-ablated, partial r(verdict, **won** | deluck, verbosity) ≈ +0.56 wolf /
   +0.60 SK (town +0.02), N=24 — capturing skill the vote proxy can't see. The earlier "halo" worry was a
   *different quantity*: the retracted "+0.556" is an undifferenced **town** credit-level, NOT this wolf/SK
   corr-with-win (verify-#9 — no contradiction). (ii) the **SP channel was A/B'd** (`v6_sp_ab`, N=30) — **but
   for town + the serial killer only; the WOLF was explicitly EXCLUDED** (wolf v6_1 memory was stale
   post-`bbc7c5b`; wolf ablation deferred). So what's *actually* open: the **validated paired A/B used
   observations-only + outcome/vote proxies blind to discussion skill** (its wolf null is channel-limited);
   the v7 runs that would convert the tagger metric into a clean wolf-memory verdict were **INVALID** (unpaired
   / arms-race confound); the tagger is correlational + uncalibrated at small N; and **no direct wolf SP/obs
   A/B has ever been run.** → Still can't call wolf-memory irreducible — but because of **power + invalid runs
   + a deferred wolf-direct measurement**, NOT a missing instrument and NOT a hidden contradiction. (Only the
   metrics-side discussion *proxy* is genuinely deferred.)
3. **Config-sensitivity is real** (96.7→73.3) — before a v7 run, lock the (verified small) confound surface:
   **`expect_factions`+matching `configs`** (the v2 trap; default `all_enabled` = arms-race board),
   **`base_store`/namespace** (the 23pp confound), **`model`/`dedup_model`** (temp-0 backend sensitivity),
   **`off_baseline=True`** (same-epoch baseline). Fail-closed guards auto-enforce factions + provenance drift;
   the human still owns `base_store` choice + model-tier pinning. (See the v7-loop toggle-locks table.)
4. **Retrieval levers (criticality, core-dilemma) are within noise** — base v6 retrieval is fine; don't bank on those levers.
5. **The application judge is human-uncalibrated** (⏸) — adoption/quality numbers are machine-judge-only.

---

## VERIFY-IN-CODE PASS — RESULTS (done 2026-06-28)

Verified by parallel code-readers; corrections folded into the tables above. Per-item verdicts:

1. **`core/stats.py` — ✅ CONFIRMED (primary home) / NUANCED.** Clopper–Pearson CIs (analytic, **not** bootstrap), Fisher exact (unpaired arms), exact McNemar + Wilcoxon signed-rank (paired), point-biserial (proxy validation). All two-sided; **no built-in multiple-comparison correction** (Bonferroni applied by hand in evidence scripts). Not the *only* home — `town_echo_read.py` uses scipy `mannwhitneyu` directly, `diagnose_wolf_sk_proxies.py` calls `fisher_exact` inline, bootstrap CIs live in `training/evaluator.py`. ⚠️ Which test backs which headline: paired-A/B figures (`correct_elim p=.028`, `mislynch p=.036`, `healer_save p=.005`) are **Wilcoxon**, NOT Fisher; the metric-validation `p<0.01` are **point-biserial**.
2. **`judges/retrieval.py` fallback — ⚠️ NUANCED (bias confirmed, worse than stated).** `<2 items` → relevance=1 **but efficiency=5** (max), not "minimal." Net: efficiency UP, redundancy_ratio→0, relevance DOWN. **No counter; fallback rows silently pooled into the judged averages** → a thin/off arm (strategy_points often ≤1 item) gets inflated efficiency = arm-asymmetry in the *diagnostic* metric. (Fix candidate: tag/exclude `<2` rows from efficiency/redundancy aggregates.)
3. **`Agents/compute_metrics.py` — ✅ CONFIRMED / one rename.** Validated proxies are computed AND pushed. Corrections: `mislynch_rate` → **`town_mislynch_rate`**; `suspicion_drawn` is faction-split (`wolf_`/`sk_`). File computes a ~50-field superset; `push_scores_to_langfuse` pushes **every** non-None field (indiscriminate, not a curated basket).
4. **`--expect-factions` arm-guard — ✅ CONFIRMED (location corrected).** Real flag, **hard-fails** (AssertionError) twice (pre-spend declaration gate + per-gen ARM MISMATCH). Lives in `loop/{driver,invariants,config}.py`, **NOT** `scripts/run_batch.py`.
5. **`loop/driver.py`+`config.py` toggle matrix — ✅ CONFIRMED + mapped.** 32 config fields; small confound surface (both arms same gen/boards). Dead toggles: `arm` (label-only footgun — `arm=off` is a silent no-op), `frozen_base_rates` (unwired). Locks + matrix added above.
6. **Dedup + day-summary judges — ✅ RESOLVED.** Dedup → 🟡 PARTIAL (decision-maker golden-anchored; quality judges uncalibrated; `batch_dedup.py:87` silent-failure bug). Day-summary → ⚠️ CLAIMED-UNVERIFIED (uncalibrated, leniency-saturated, n=18).
7. **`eval-extraction` entry — ✅ CONFIRMED real** (`pyproject.toml:37`). Hedge dropped.
8. **Backend consistency — 🟡 NUANCED.** Backend is **env-driven (not a hardcoded single value)**, but recorded in `runtime_fingerprint.llm_backend` and **hard-asserted constant within a loop run**. Cross-run safety = detection-via-fingerprint, not a pinned constant — a human must still check the recorded backend matches before comparing runs.
9. ⭐ **Tagger-validity tension — ✅ RESOLVED: NO CONTRADICTION.** Claim A (+0.56/+0.60 partial r, **wolf/SK**, corr-with-**win** | deluck+verbosity) and Claim B (+0.556, **town** villager/day_discussion, raw undifferenced *level*, retracted as a halo) are **different quantities at coincidentally-equal magnitude** — different LHS, faction, and question; the retest's town row (+0.02) *agrees* with B's retraction. **Net: the tagger is a validated deceiver-skill METRIC, NOT a demonstrated wolf-memory effect** (correlational, N=24/single-epoch/uncalibrated; deleak-ablation ran on N=6, skill-retest on N=24). Scorecard #2 rewritten.
10. **`v6_sp_ab` — 🟡 NUANCED (wolf-scope overstated).** Facts hold (N=30 paired, nothing p<0.05 on outcomes, "SP-alone *trends* harmful / obs+SP synergy"). BUT **the wolf was explicitly EXCLUDED** — the deceiver arm is the **serial killer**, wolf ablation deferred (wolf v6_1 stale post-`bbc7c5b`). So this probed SP memory for town+SK only; for wolf it's a *deferred/proxy* probe, not direct. Only `experiment_log.md` exists (no `report.md`); 6 arms, not 5. Scorecard #2 corrected.

**Residual / newly-surfaced (not blocking — a fix or a watch):**
- 🔧 retrieval fallback pooling (#2) — synthetic `efficiency=5` silently inflates the diagnostic average; arm-asymmetric.
- ✅ `batch_dedup.py:87` swallow-all-exceptions bug **FIXED 2026-06-28** — now splits invalid-output vs call-failed (matches the online judge; `ValidationError` imported).
- 🔧 dead toggles `arm` / `frozen_base_rates` — `arm=off` is a silent no-op footgun.
- ⏳ still genuinely uncalibrated (no human anchor): application judge (⏸), day-summary judge (⚠️), dedup quality scores (🟡).
- ⏳ **direct wolf SP/obs A/B never run** (deferred post-`bbc7c5b`) — the one missing direct measurement for wolf memory.

## Structural notes (for the write-up + the reorg)

- **Two-axis mining holds:** every `memory_system/effectiveness/*` doc is both a *verdict* (→ writeup ch.) and an *apparatus-proof* (→ this report's credibility thread). E.g. drift doc = the system caught its own confound.
- **Orphans/mis-files to absorb:** `metrics/variance_reduction_levers` (→ A/B-methodology section), `store_progression` (narrative spine → writeup), `phase_b/plan_review` + `v6_wide_migration_roadmap` (roadmaps).
- **No single source folder** — the eval system co-evolved across experiments; this report is a *synthesis-with-pointers*, not a colocation (unlike tracing).
- **Diagnosis funnel ↔ modules** (the "how we diagnose a null" section): (1) did retrieval fire → EvalCase fields + `recall_flags.py`; (2) relevant → `judges/retrieval.py` + situation NDCG; (3) used → `judges/application.py` + `loop/memory_adherence.py`; (4) decision changed → `replay/application.py` (captured vs none); (5) outcome changed → metrics + `synth_deluck_ab.py` + paired A/B + decision-replay screen.

## The eval-report skeleton (agreed structure, 2026-06-27 → INSTANTIATED 2026-06-28 in [`report.md`](report.md))

Organize by **case-type × modality**, with the outcome A/B on top — supersedes the bare two-tier spine.
**Built as a logical view** (`report.md`): pointers into intact folders, per-section `Inspect:` queues + JIT
`Colocation:` calls. The structure:
- **Axis 1 — the 4 case types:** day-summary · agent-decision (situation-summary → retrieval → application) ·
  extraction (obs/SP quality + v7 synthesis) · dedup (online + batch). *(= the capture report's 4 cases.)*
- **Axis 2 — the modality ladder** (orthogonal; a calibration chain): **LLM-judge** (cheap, noisy) →
  **human + advanced-agent eyeballing** (needs the case-pull sampler — UNDERBUILT, see below) →
  **labeling + golden sets** (gold; *validates* the judge; human spot-check *calibrates* it = the deferred
  `judge_validation_protocol`).
- **On top:** the **end-to-end A/B** (did it work) — the outcome layer the per-case evals diagnose.
- **Instruments:** metrics proxies + judge rubrics.

## Planned build (this pass) — the case-pull / diagnosis sampler (modality #2)

**Decision (2026-06-27):** modality #2 (human+agent eyeballing) is **underbuilt and WILL be built during
this consolidation pass**, *build-as-we-document* when the write-up reaches the diagnosis/modality-#2
section. **Intentional, scoped exception** to "finish/freeze > new depth" — justified: (a) load-bearing for
trusting/diagnosing v7, (b) the bottleneck behind expensive v5→v7 iteration, (c) **small** (composes existing
parts). Discipline: **MVP-shaped, in service of the write-up + v7 — not a diagnostic platform.**

**Minimal shape:** ① **select** suspect/leveraged cases = score-outliers (§2.8 Langfuse scores) + a
**deterministic leverage anchor** (`is_swing` / distance-to-parity / de-luck proxy) as the pivotalness proxy
— **never the outcome-halo** (the `extraction_selection` lesson) → ② **cohort** via `data/sampling.py`
(`games_to_sample` + stratify) → ③ **replay** cheaply via `replay/*` (no full re-run) → ④ **surface** for
human / advanced-agent review.

**Trigger:** after the verify-in-code pass, at the diagnosis-section of the eval write-up, *before* leaning
on it for v7 diagnosis. **Not now** (now = read/verify pass).
