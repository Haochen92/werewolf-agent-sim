# Evaluation System — Report (the *judge* half) · PARENT INDEX

> **Orientation.** The eval system is the **judge** half of the capture↔judge split (capture = frozen cases,
> [`../tracing/report.md`](../tracing/report.md)). This segment asks *"how do we measure whether each memory
> component meets its objective, and how far can we trust that measurement?"*
>
> **This file is the PARENT INDEX**, distilled *last*. The real content is **one specialised
> apparatus-report per topic**, each in its own subfolder (`<topic>/report.md`), built as we inspect. The
> approach is always **specialised → distilled into broad**: write the per-topic reports first, synthesise
> the parent from them at the end.
>
> **Three docs, three jobs (one fact, one home):**
> - [`source_map.md`](source_map.md) = the **cross-cut audit ledger / index** — owns the reliability *tags*,
>   the 2026-06-28 verify-in-code results, the v7-trust scorecard, the toggle-locks. Full code/evidence
>   pointers live here.
> - `<topic>/report.md` = the **specialised apparatus deep-dive** — owns the per-instrument narrative (L1+L2).
> - this `report.md` = the **distilled broad story** — owns cross-component synthesis (written last).

---

## The lens (what this segment IS about — and what it isn't)

Every original evidence folder braids **two threads**; this segment follows only one.

| Level | Question | Iteration = | Home |
|------|----------|-------------|------|
| **L0 — the design** | does the dedup pipeline / day-summary extractor / retrieval design meet its objective? | a better *design* | **ch.3 memory system** (the *verdict* lens) |
| **L1 — the apparatus** | how do we *measure* whether the design meets its objective? (judge · golden set · replay harness · metrics) | a better *measurement* | **here (eval)** |
| **L2 — apparatus trust** | is that measurement itself any good — anchored, calibrated, low-noise? | a more *trustworthy* measurement | **here (eval)** — see [`source_map.md`](source_map.md) tags |

**This segment = L1 + L2.** The design verdict (L0) appears only as *the objective the apparatus targets* —
never as the subject. So a topic report catalogues the **instrument** and judges **its** reliability; it does
NOT re-derive what the design found (that's the later v5/v6/v7 *verdict* pass over the same folders — same
files, two lenses). Because L0 and L1 co-evolved in the same logs, the apparatus thread can't be *moved* out
of the original folder — hence each topic report **points at the live code** (`evaluation/src/...`, never
copied) and at the **L2 artifacts**, and lives in this new `evidence/evaluation/` hub. **Where a folder's
apparatus thread is thin or uncalibrated, that is itself a finding** (→ the v7-trust scorecard; it's why the
wolf null is *channel-limited*, not a ceiling).

```
            ┌─────────────────────────────────────────────────────────┐
  ON TOP →  │  END-TO-END A/B   "did it work?"  (memory-on vs off)      │
            └─────────────────────────────────────────────────────────┘
  4 CASE TYPES (what gets judged) ──────────────────────────────────────
    day-summary · agent-decision (situation→retrieval→application)
    extraction (obs/SP quality + v7 synthesis) · dedup (online+batch)
  × MODALITY LADDER (how it's judged — a calibration chain) ────────────
    a LLM-judge (cheap, noisy) → b human+agent eyeball (needs the
    case-pull sampler — UNDERBUILT) → c labeling + golden sets (gold)
  CROSS-CUT:  metrics (de-lucked proxies) · A/B methodology (drift/variance)
```

---

## Topic index (the status board)

Apparatus-yield varies: the apparatus-**first** topics (`end_to_end_ab`, `metrics`, `methodology`, parts of
`agent_decision`) are the eval spine; the design-first folders (`day_summary`, `dedup`, `extraction`) carry a
thin, extractable apparatus thread. Full code/evidence pointers per topic: [`source_map.md`](source_map.md).

| Topic | The apparatus (L1) | Trust (L2) | Status |
|-------|--------------------|-----------|--------|
| **End-to-end A/B** | `run_batch.py` paired-by-game_id → `analyze_ab.py` → `core/stats.py` + de-luck proxies + decision-replay screen | 🟡 sound + self-aware (epoch-drift catch, convergent screen); win underpowered (MDE ~36pp); **pairing buys ~0 variance** (same-epoch is the real control) | ✅ **done** → [`end_to_end_ab/report.md`](end_to_end_ab/report.md) |
| **Day-summary** | 5-dim LLM-judge + regen-and-score harness (18 pairs) | ⚠️ smoke-test (uncalibrated · saturated · regen+judge confound · proxy≠objective) | ✅ **done** → [`day_summary/report.md`](day_summary/report.md) |
| **Agent-decision** (situation→retrieval→application) | pairwise-summary + retrieval + application judges + golden-NDCG + replay | 🟡 weakest at the live edge: every live judge uncalibrated; situation-NDCG golden machine-augmented + not wired into retrieval; ⏸ application (Bucket-B unrun); live v6 path thinnest-measured | ✅ **done** → [`agent_decision/report.md`](agent_decision/report.md) |
| **Extraction** (obs/SP + v7 synth) | per-role extraction judge (8 dims) | 🟡 **DE-BUGGED, not calibrated** (2 real bug-fixes; machine-only/no golden; original 5 dims ceiling-saturated; v7 synth unjudged) | ✅ **done** → [`extraction/report.md`](extraction/report.md) |
| **Dedup** (online + batch) | deterministic golden scorer (strong) + 2 LLM quality judges (weak) | 🟡 decision-maker ✅ golden-anchored (65 online / 111 batch keys); quality judges uncalibrated; numbers stale (pre-v6 + backend shift); ✅ silent-fail bug fixed | ✅ **done** → [`dedup/report.md`](dedup/report.md) |
| **Metrics** (instruments) | de-lucked outcome proxies + monotonicity validation | ✅ town basket (\|r\|≈0.6) · 🟡 investigator (find-rate wrong-sign; only conversion validated) · ⚠️ deceiver (SK ok; wolf day-offense unmeasured) · 🔴 discussion; GameScore tiering unbuilt | ✅ **done** → [`metrics/report.md`](metrics/report.md) |
| **A/B methodology** | drift guards + arm-guard (hard-fail ×2) + pairing/stats | 🟡 strong where enforced; cross-epoch gate + embedding-alias drift are MANUAL/undetected; pairing BUILT but ≈0 power; CUPED N/A | ✅ **done** → [`methodology/report.md`](methodology/report.md) |
| **Sampler** (modality b) | case-pull / diagnosis sampler | ⛔ UNDERBUILT — scoped build this pass | to build → `sampler/` |
| **v7 loop** | LLM-free `measure.py` + paid omniscient tagger + invariants | ✅ mechanics (best-tested; caught its own invalid runs) · 🟡 science open (tagger = validated metric not memory verdict; both v2 runs invalid) | ✅ **done** → [`loop/report.md`](loop/report.md) |

---

## Cross-cutting findings (emerging — provisional; the full distillation is written last)

Patterns that only appear when you read all nine topics together. These are the seed of the final distilled
story; sharpen on the next pass.

1. **Every *live* LLM-judge is uncalibrated, machine-on-machine.** day-summary, the agent-decision funnel
   (pairwise-summary · retrieval · application), and extraction all run LLM-judges with **no human/golden
   anchor**. The trustworthy instruments are the *non-LLM* ones: the dedup decision-scorer (human golden),
   the metrics proxies (point-biserial-validated vs win), `measure.py` (LLM-free), and the situation-NDCG +
   CE-reranker goldens.
2. **The real anchors exist but aren't wired into the live judges.** The situation-NDCG golden isn't consumed
   by `eval-retrieval`; the CE-reranker golden isn't live (rerank OFF); the application Bucket-B calibration is
   designed-not-run. Calibration *capacity* exists, disconnected from the live measurement path.
3. **Staleness is uniform.** Nearly every anchor is on **v4 stores + 2026-05 prompts + pre-Google→Vertex**
   backend; live judge models drifted flash↔pro between module defaults and configs. Most headline numbers
   describe superseded code.
4. **The live v6 path is the least-measured.** v6 ships baseline bi-encoder retrieval (rerank/filter OFF) +
   the per-role write-path; the heavily-studied designs (rerank, filtering, criticality/forced-schema dims)
   are dormant or default-off. **Diagnostic confidence is highest where the code isn't running.**
5. **Recurring failure modes to name once, in the parent:** (a) **flat/ceiling-saturated judge dimensions** =
   zero-info gauges (`village_dynamics`=5.00; extraction's original 5 dims); (b) **regen+judge-in-one-harness**
   confounds (day-summary, pairwise-summary, application) — plus extraction model-ranking's related **gen+judge variance blend** (separate passes, same effect); (c) **outcome-halo
   selection/metrics** (net_verdict; `suspicion_drawn` tautology).
6. **What the apparatus does WELL (the credibility thread):** it repeatedly **caught its own errors** —
   epoch-drift (Fisher p=.0028), the arms-race config slip (now an automated invariant), the forced-schema
   field-desc invisibility (retracted an inflated metric), the investigator denominator artifact, both invalid
   v2 runs. Self-correction is the strongest evidence the harness is real.
7. **The recurring cheapest upgrade is one move:** *calibrate one judge / wire an existing golden in.*
   Highest-leverage = the **application Bucket-B calibration** (~½ day, zero code).
8. **Bottom line for v7:** trust the **deterministic / outcome instruments** (town proxies, dedup scorer,
   `measure.py`, the paired-A/B machinery) and the **validated tagger-as-metric**; do NOT lean on the
   uncalibrated LLM-judge layer. The gating need is a **valid paired run (+ a wolf-direct arm)**, not more
   judges.

---

## Per-topic inspection log (filled as we go)

> Each entry: date · topic · what was read (code + md) · verdict · colocation call.

- **2026-06-28 · Day-summary** → [`day_summary/report.md`](day_summary/report.md). Read `judges/day_summary.py`
  + `experiments/day_summary_eval.py` + `extraction/day_summary/experiment_log.md`. Apparatus = single 5-dim
  LLM-judge + regen-and-score harness on 18 pairs. Verdict ⚠️ WEAK (uncalibrated · saturated
  `village_dynamics`=5.00 · noise≥signal · regen+judge confound · measures intrinsic quality not downstream).
  Credit: final design call made on architectural grounds *because* the judge couldn't resolve versions.
  Colocation: original stays put (design→ch.3); no L2 artifact self-contained enough to move → all pointed-at.
- **2026-06-28 · Dedup** → [`dedup/report.md`](dedup/report.md). Read `judges/{dedup,batch_dedup}.py` +
  `core/schemas.py` + the `dedup_{score,eval,replay}` harness + `dedup/{README,report,per_extraction,
  batch_dedup,embedding_prefilter}` md. Two measurement layers: a **deterministic golden scorer** (the
  system's *strongest* L2 — human golden 65 online / 111 batch keys, 78-89% decision accuracy) and **LLM
  quality judges** (uncalibrated). Verdict 🟡: decision-maker ✅ validated, but quality judges uncalibrated +
  numbers stale (pre-v6 prompt/gate, Google→Vertex backend shift) + prefilter re-validation open + ✅
  `batch_dedup.py:87` silent-fail bug FIXED 2026-06-28. Irony: the strong scorer has no console
  entry; the weak judge is `eval-dedup`. Colocation: original stays put; golden files are data-plane /
  code-referenced (point-at); key numbers distilled into the report.
- **2026-06-28 · Agent-decision funnel** → [`agent_decision/report.md`](agent_decision/report.md). 3 parallel
  reads (situation/retrieval/application) synthesised. 🟡: every *live* judge uncalibrated; situation-NDCG
  golden is machine-augmented + stale (v4) + not wired into retrieval; retrieval `<2`-item pooling confirmed
  (current-code, archive uncontaminated); live v6 path (baseline bi-encoder, rerank/filter OFF) is the
  thinnest-measured; application ⏸ (Bucket-B calibration designed-not-run, ~½ day to close). Colocation: stays.
- **2026-06-28 · Extraction** → [`extraction/report.md`](extraction/report.md). ⭐ **Downgraded ✅→🟡**:
  2 judge bug-fixes verified real, but judge is machine-only/no golden, original 5 dims ceiling-saturated,
  model-ranking n=5-10 + regen/backend-confounded, **v7 synthesis quality entirely unjudged**. net_verdict =
  outcome-halo (validates labeling, not selection). Colocation: stays (no golden to move).
- **2026-06-28 · End-to-end A/B** → [`end_to_end_ab/report.md`](end_to_end_ab/report.md). 🟡 apparatus sound +
  self-aware (epoch-drift p=.0028 catch, convergent screen, honest null-ladder). ⭐ source_map **code pointer
  was wrong** (it's `run_batch.py`→`analyze_ab.py`→`stats.py`, NOT synth_deluck_ab/e2e) + **pairing buys ~0
  variance** (seed effect ≈0; same-epoch is the real control). Win underpowered (MDE ~36pp). Colocation: stays.
- **2026-06-28 · Metrics** → [`metrics/report.md`](metrics/report.md). ✅ town basket validated; 🟡 investigator
  (find-rate ~0/wrong-sign, only conversion +0.40 validated; `found_wolf_day` sig wrong-sign); ⚠️ deceiver
  (SK ok; `suspicion_drawn` tautology+opponent-coupled; wolf day-offense unmeasured); 🔴 discussion; GameScore
  tiering unbuilt → indiscriminate Langfuse push. Colocation: stays (shared hub).
- **2026-06-28 · A/B methodology** → [`methodology/report.md`](methodology/report.md). 🟡 strong where enforced
  (arm-guard ×2, in-run fingerprint); cross-epoch gate + embedding-alias drift MANUAL/undetected; pairing
  BUILT but ≈0 power; CUPED N/A. `variance_reduction_levers` mis-filed → methodology, but a move is a
  link-rewrite (6 outbound + 5 inbound), deferred to the batched reorg.
- **2026-06-28 · v7 loop** → [`loop/report.md`](loop/report.md). ✅ mechanics (LLM-free measure, unit-tested
  credit, fail-loud invariants that caught both invalid v2 runs) · 🟡 science open (tagger = validated metric
  not memory verdict; consolidation quality unmeasured). Cheapest: a valid paired town_only rerun + a
  wolf-direct arm. Colocation: stays (retest scripts frozen in v2_full; stdout-only results = a durability gap).
