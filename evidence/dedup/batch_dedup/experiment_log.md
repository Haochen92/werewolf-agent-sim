# Batch dedup — the offline whole-store pass (experiment log)

**What this is.** The **offline** dedup layer: the whole store swept in similarity clusters on a strong
model. Prompt tuning was only *one* of several threads here (hence the folder is `batch_dedup`, not
"prompt tuning") — this chapter covers all of them: **(1)** why an offline pass is needed at all;
**(2)** porting the per-extraction decision criteria into the cluster-resolution prompts (v0→v3 + a
"lite" variant); **(3)** the **two-pass** pipeline (flash-lite triage → 2.5-pro verify, **89.2%**);
**(4)** merge-rewrite quality (why only a pro model can write merges); and **(5)** the discovery that
the pass is **not idempotent**, which motivated incremental dedup. Companions: the folder
[report.md](../report.md) is the destination (how batch dedup works *today*); the mechanics reference is
[../batch_architecture.md](../batch_architecture.md); the incremental/freeze-old story this kicks off is
[../incremental_convergence.md](../incremental_convergence.md); the chronological overview is
[../experiment_log.md](../experiment_log.md).

**Reading contract.** In rough time order; prompt variants and the two-pass design are shown as tried,
with the idempotency test (a second run removed another ~10%) left in place because it's what exposed
the convergence problem. Eval JSONs are in [data/](data/), frozen prompts in
[prompt_versions/](prompt_versions/).

**The shape of the journey.**

1. **Why a second pass** — online dedup is greedy, top-N-bounded, and never re-examines old pairs; batch
   re-clusters the whole store and can MERGE.
2. **Form the clusters** — no single similarity threshold cuts cleanly; connected/union-find blobs into
   one giant cluster, so the pass runs **bounded** (greedy, non-transitive, capped at 15) — the mode the
   live v7 loop actually sets.
3. **Port the criteria** — the cluster prompts never had the per-extraction criteria; v0 (untuned) → v1
   (ported) → v2 (indexed keys + anti-over-merge) → v3 (drop the KEEP-bias note, cap clusters at 15).
4. **Pick the model** — 3.5-flash is the best single model; flash-lite over-merges *and* can't write
   merges; 2.5-pro writes good merges but is slow and fabricates → **two-pass** (flash-lite triage →
   2.5-pro verify) wins at **89.2%**.
5. **Merge quality** — only a pro model preserves all three merged fields; weak models silently drop
   `merged_approach`/`merged_outcome` (the reason MERGE is pro-only).
6. **The idempotency alarm** — a second full run removed another ~10%, so the pass isn't idempotent →
   incremental mode + the freeze-old guard.

**Bottom line (what we run).** Periodic-maintenance dedup runs **two-pass — flash-lite triage → 2.5-pro
verify — with the v3 default prompt** (89.2%, the best-accuracy config; the lite prompt is the speed
option for more frequent runs). The **gate and bounded clustering already run live** (online dedup + the
v7 loop); the offline two-pass pass itself is **built and validated but off by default — one flag**
(`IncrementalDedupConfig`). The one unclosed risk before flipping it on is merge fabrication (below).

**Model names, once.** *flash / pro / lite* are capability **tiers**; the numbers (`3.5`, `2.5`, `3.1`)
are **generations** — so the newer `gemini-3.5-flash` can and does beat the older `gemini-2.5-pro` here.
Not a typo.

**Why this layer is hard — one fault line.** Almost every problem below is a face of a single fact:
**embedding similarity ≠ situation identity.** Cosine groups by *topic*, but topic-similar entries can
teach *different* lessons — which is why a similarity graph blobs into one cluster (§Forming the
clusters), why flash-lite over-merges (§Results), and why a second full sweep isn't idempotent
(re-clustering a changed store re-litigates settled entries — §Idempotency Test). Three problems, one
root cause.

---

## Why a second (offline) pass

Online per-extraction dedup already searches the whole store across games — but it's a **greedy,
insertion-time** check: each new entry is compared only against its **top-N** neighbours at the moment
it lands, it **never re-examines a pair once both are kept**, and it can't MERGE. So near-duplicates
that fell outside each other's top-N window, or were both kept before they sat together, accumulate (and
under *parallel* per-game generation, concurrent entries aren't seen at all). The **batch** pass closes
that gap: it re-clusters the *whole* store and re-examines every near-duplicate together, on a strong
model that can MERGE variants into one entry with summed counts.

That leaves a second problem specific to this pass: the batch cluster-resolution prompts had **never
been updated** with the decision criteria refined during per-extraction tuning (v1→v11b, which reached
83–85%). Batch is also harder than per-extraction — a cluster holds 2–25 entries and needs *multiple*
operations, not one D/K call, and observations keep **MERGE** here (a full cluster lets a strong model
consolidate tactic variants with counts). So the work below ports those criteria, then tunes for the
cluster setting.

## Forming the clusters

Before any prompt, the pass must decide *which entries are compared together* — the first hard problem,
because **clustering decides what the LLM ever sees as a candidate group** (the prompt only resolves
*within* a cluster). The trouble is that the embedding space is too smooth to cut cleanly — the same
topic-not-stance problem as the overview's [§2](../experiment_log.md) — so no single similarity
threshold separates near-duplicates from distinct lessons, and the *method* matters as much as the
threshold. Three modes were built; each trades recall against blast radius:

- **`connected` — similarity graph / union-find.** Draw an edge wherever two situations embed above the
  threshold, then take connected components (BFS). *Pro:* highest recall — catches a duplicate however
  it's worded. *Con:* **transitive** — A~B and B~C pull `{A,B,C}` together even if A≁C, so any threshold
  low enough to catch real duplicates collapses the whole namespace into **one giant cluster**. This is
  the union-find blob.
- **`agglomerative` — hierarchical.** Re-embed every situation, build the full cosine matrix, run scipy
  linkage, cut at `1 − threshold`, chunk by the size cap. *Pro:* most principled — a global view of the
  distance structure. *Con:* heavy (re-embeds everything, needs scipy), and un-gated it has the same
  global-blob tendency as `connected`.
- **`bounded` — greedy, capped (the one that ships).** Take the highest-value seed (the most-reinforced
  entry), pull its top neighbours above threshold, **cap the cluster at `max_cluster_size`**, mark them
  consumed, repeat. *Pro:* non-transitive and bounded — each item lands in exactly one small cluster, so
  no drift and no blob; conservative and controllable. *Con:* a duplicate can be missed if it falls
  outside the seed's capped neighbourhood (the same top-N-bound limit as online — a later full-store
  refresh can still catch it).

**The decision: `bounded` — and it's the live method, not just a code default.** Every real run config
sets it explicitly: the v7 consolidation loop
([consolidate.py](../../../evaluation/src/loop/consolidate.py): `cluster_mode="bounded",
similarity_threshold=0.70, max_cluster_size=15`), the de-luck A/B, and the cell-SP synthesis — and a
produced store records it (`memory_stores/v6_1_sp_cluster/manifest_sp.json`: `"cluster_mode":
"bounded"`). The rationale is the retrieval-impact finding that **conservative dedup beats aggressive**
(17% reduction won on relevance and efficiency; 39% *lost* observation relevance —
[store_retrieval_impact](../store_retrieval_impact/experiment_log.md)): `bounded` is the mode that
*mechanically* enforces that conservatism, so it was the natural pick. `connected` and `agglomerative`
stay available behind the flag for one-off full-store consolidation but are not used in the loop.

**The size cap was tuned 8 → 25 → 15.** It started at 8, was raised to 25, then cut to **15** when the
eval showed accuracy falls off a cliff above ~15 entries (26–74% vs 80–100% for smaller clusters).

**The blob returned once — in the *global* `agglomerative` path — and forced the gate.** A system-wide
run that clustered a whole namespace un-gated over-merged across unrelated game states (the commit calls
it "the global agglomerative blob-merge"); the fix was to **gate-partition the clustering** (2026-06-16)
so entries in different criticality / verdict / information-landscape / exposure buckets can never enter
the same cluster. That is the same v6 gate the overview's [§9](../experiment_log.md) describes, applied
on the clustering side — clustering now runs *inside* a gate partition.

*Point-in-time: `bounded` is the choice as of this log, but the clustering approach is under active
revision in the v7 loop — this section will be updated when that work lands.*

## Dataset

Source: `eval_sets/batch_dedup_clusters_v4.json` — 34 clusters (19 observation, 15 strategy) with 522 total items, extracted from v4 memory store pre-dedup.

Golden labels: `eval_sets/batch_dedup_golden_labels.json` — 17 clusters, 149 items. Eval set uses 11 clusters (111 keys): 9 with real DISCARD/MERGE operations + 2 pure-KEEP controls. Golden distribution: KEEP=77, DISCARD=20, MERGE=14.

## Prompt Versions

Each important checkpoint is stored in `evidence/dedup/batch_dedup/prompt_versions/`.

### v0 (baseline)

The original batch prompts before any changes. Stored as `prompt_versions/batch_v0_baseline.py`.

Key gaps vs per-extraction v11b:
- No situation comparison section (4 dimensions + retrieval test)
- No approach/outcome comparison criteria (observations)
- No "all three fields must match for DISCARD" calibration
- No before-DISCARD verification checklist
- Strategy DISCARD rewrite instruction lacks "only when needed" guidance

### v1 (ported per-extraction criteria)

Stored as `prompt_versions/batch_v1_criteria.py`. Ported all refined criteria from per-extraction tuning:
- Situation comparison (4 dimensions + retrieval test) for both prompts
- Approach/outcome comparison criteria for observations
- Field-match calibration (MERGE needs situation+outcome; DISCARD needs all three)
- BEFORE GROUPING verification checklist for strategy DISCARD
- Expanded decision test with confidence posture and opposite action examples
- "Only rewrite when needed" guidance for strategy DISCARD

### v2 (indexed keys + anti-over-merge)

Stored as `prompt_versions/batch_v2_anti_overmerge.py`. Two structural changes:
- **Numbered indices**: Entries formatted as [1], [2], ... instead of UUIDs. Remapped back to real keys after LLM response. Eliminated UUID truncation on longer prompts and fixed 3.5-flash JSON parse failure on 23-entry clusters.
- **BEFORE MERGING checklist**: Replaced "MERGE REQUIRES" with explicit retrieval-diversity gate and merge group size warning (>3-4 entries is a red flag). Changed observation calibration to "when in doubt KEEP".

### v3 (remove KEEP calibration note) — current

Stored as `prompt_versions/batch_v3_no_keep_bias.py`. Removed "when in doubt KEEP" calibration note from observation prompt — it overcorrected 3.5-flash which was already conservative. Kept all other v2 changes. Also lowered `DEFAULT_MAX_CLUSTER_SIZE` from 25 to 15.

## Results

### Model comparison (v1 prompts, UUIDs)

| Model | Accuracy | Time | Notes |
|---|---|---|---|
| gemini-3.5-flash | 89.8% (79/88) | 357s | Cluster 4 JSON parse failure (23 entries) |
| gemini-2.5-pro | 72.1% (80/111) | 687s | Heavy over-merge: 12 KEEP→MERGE |
| gemini-3.1-flash-lite (medium) | 69.4% (77/111) | 126s | Heavy over-merge: 14 KEEP→MERGE |

### Model comparison (v3 prompts, indexed keys)

| Model | Accuracy | Time | Notes |
|---|---|---|---|
| gemini-3.5-flash | 86.5% (96/111) | 343s | All clusters work, 0 KEEP→MERGE |
| gemini-2.5-pro | 83.8% (93/111) | 513s | Over-merge fixed: 12→2 KEEP→MERGE |
| gemini-3.1-flash-lite (medium) | 72.1% (80/111) | 145s | Still over-merges: 19 KEEP→MERGE |

### Accuracy by cluster size (v3)

| Size | Clusters | 3.5-flash | 2.5-pro |
|---|---|---|---|
| 2-5 | C5, C20, C33 | 100% | 100% |
| 8-10 | C0, C11, C16, C21 | 80-100% | 80-100% |
| 11-16 | C14, C25, C28 | 64-100% | 64-100% |
| 23 | C4 | 74% | 65% |

Cluster 25 (strategy, 11 entries) is consistently hard — 64% for both models.

### Key findings

1. **Indexed keys are strictly better** — eliminates UUID truncation and JSON parse failures, saves tokens, no downside.
2. **BEFORE MERGING checklist was the key improvement** for 2.5-pro — reduced over-merge from 12 to 2 errors.
3. **Calibration bias should be neutral** — "when in doubt KEEP" hurt 3.5-flash; "when in doubt DISCARD" only applies to strategy. The right bias depends on downstream retrieval quality and agent strategy application, not on the prompt.
4. **Cluster size limit of 15 is well-supported** — all models degrade sharply above 15 entries.
5. **flash-lite is not viable as a standalone model** for batch dedup — the lite prompt fixes over-merge (85.6% accuracy) but flash-lite has the same merge rewrite limitation as 3.5-flash: it drops `merged_approach` and `merged_outcome` fields, outputting only `merged_situation`. Only 2.5-pro produces complete merge rewrites (see Merge Rewrite Quality). This is why two-pass is needed: flash-lite triages, 2.5-pro writes the merges.
6. **Two-pass pipeline (flash-lite triage → 2.5-pro verification) is the recommended production approach** — combines flash-lite's speed and KEEP/DISCARD precision with 2.5-pro's merge quality, cutting 2.5-pro call volume by ~69% (see *Time and throughput*). **3.5-flash remains the best single-model option** — fastest, most accurate, no over-merge tendency. 2.5-pro is close but 50% slower with no accuracy advantage.

## Merge Rewrite Quality

After scoring per-key action accuracy, we evaluated the quality of merged text (merged_situation, merged_approach, merged_outcome) using a separate LLM judge (gemini-2.5-pro). This matters because a correct MERGE decision with bad rewrite text degrades the memory store.

### Judge dimensions

- **Retrieval coverage** (1-5): Will the merged situation be retrieved by the same queries that matched each original entry?
- **Merge quality** (1-5): Is the rewritten text well-formed, specific, and an improvement?
- **Information preservation** (1-5): Were important nuances preserved (tactic counts, conditions, mechanisms)?
- **Fabrication detected** (bool): Did the rewrite introduce context not in source entries?

Pipeline: `evaluation/experiments/batch_dedup_merge_eval.py` extracts MERGE/DISCARD-with-rewrite operations from eval result JSONs, pairs with source entries from the cluster file, and sends to the judge.

### Results (v3 prompts)

| Model | Cases | Retrieval Coverage | Merge Quality | Info Preservation | Fabrication Rate |
|---|---|---|---|---|---|
| gemini-3.5-flash | 3 | 4.33 | 4.00 | 1.67 | 0% |
| gemini-2.5-pro | 9 | 4.89 | 4.78 | 4.00 | 33% |

(The case counts differ because the two source runs emitted different numbers of merge/rewrite
operations to judge — 2.5-pro merges far more than 3.5-flash. Figures recomputed from the surviving
[data/](data/) `merge_quality_*.json` artifacts.)

### Analysis

**3.5-flash drops merged_approach and merged_outcome fields entirely** during MERGE operations — it only outputs merged_situation. This is the root cause of the 1.67 information preservation score. Three attempts to fix this via prompt/schema changes all failed:

1. Verbose "REQUIRED for MERGE" schema descriptions — caused 3+ cluster JSON parse failures
2. Detailed per-field merge rules in prompt (~7750 chars) — 4 cluster failures
3. Minimal one-sentence "all three fields are required" addition (~7425 chars) — 3 cluster failures

The observation prompt at ~7383 chars is at 3.5-flash's structured output capacity limit. Any additional instruction text triggers JSON parse failures on MERGE-heavy clusters. This is a model limitation, not a prompt issue.

**3.5-flash run-to-run variance**: Re-runs with identical v3 prompts showed different clusters failing JSON parse (C25 on one run, none on another) and C14 accuracy fluctuating between 40-100%. The model is non-deterministic near its capacity boundary. Best observed: 86.5% (96/111). Worst same-prompt re-run: 81.0% (81/100, 1 cluster failed).

**2.5-pro writes high-quality merges** with good information preservation (4.0/5) but fabricates 33% of the time — introducing game context not present in source entries.

**Open risk — nothing catches the fabrication before it lands.** MERGE is the one **irreversible,
store-mutating** operation in the pipeline (a DISCARD just drops a near-identical copy; a bad MERGE
rewrites the survivor with invented context), and 2.5-pro — the *only* model that preserves all three
fields, so the one we must use to write merges — fabricates on ~1/3 of them. The apply layer
(`operations.py`) validates keys and merges metadata but does **no content check** against the source
entries, so a fabricated merge would land. Today's safeguards are only partial: the pass is **dry-run
unless `--apply`**, MERGE is the **rarest** operation, and bounded clustering keeps merge volume low. The
fix is half-built — the `fabrication_detected` judge from this very eval
(`evaluation/src/experiments/batch_dedup_merge_eval.py`) is the obvious pre-apply gate, just not wired
into the apply path yet. **This is the single most important open risk in the batch pipeline**, and the
one to close before turning the offline pass on by default.

## Time and throughput (the win is latency, not dollars)

### Per-model performance on 111-key eval set (11 clusters, v3 prompts)

| Model | Accuracy | Total Time | Time/Cluster | Relative Speed |
|---|---|---|---|---|
| gemini-3.1-flash-lite (medium) | 72.1% | 145s | 13.2s | 1.0x (baseline) |
| gemini-3.5-flash | 86.5% | 342s | 31.1s | 2.4x slower |
| gemini-2.5-pro | 83.8% | 513s | 46.7s | 3.5x slower |

At production scale (v4 store: 522 items, ~50 clusters), a full 2.5-pro batch dedup run takes 30-40 minutes — which is why it's a periodic-maintenance operation, not something to run after every game. **Per-token pricing is comparable across these models, so the axis that matters here is wall-clock latency and 2.5-pro throughput/load, not dollars.**

### Two-pass pipeline: flash-lite triage + 2.5-pro verification

Analysis of flash-lite's per-prediction precision revealed an asymmetric error pattern that enables a two-pass pipeline:

**Flash-lite confusion matrix (v3 prompts, 111 keys):**

| Golden ↓ \ Model → | KEEP | DISCARD | MERGE | MISSING |
|---|---|---|---|---|
| KEEP (77) | **56** | 2 | 19 | 0 |
| DISCARD (20) | 2 | **13** | 4 | 1 |
| MERGE (14) | 3 | 0 | **11** | 0 |

**Flash-lite precision by predicted action:**

| Prediction | Precision | Interpretation |
|---|---|---|
| KEEP | 56/61 = **91.8%** | Highly reliable — only 5 errors out of 61 predictions |
| DISCARD | 13/15 = **86.7%** | Reliable — only 2 errors out of 15 predictions |
| MERGE | 11/34 = **32.4%** | Unreliable — 23 of 34 predictions were wrong (19 KEEP, 4 DISCARD) |

Flash-lite's dominant error mode is over-merging: it flags entries as MERGE that should be KEEP. But when it says KEEP or DISCARD, it's right ~90% of the time. This makes it an effective triage model.

**Two-pass design:**

1. **Pass 1 (flash-lite, medium thinking):** Runs on all clusters. KEEP and DISCARD decisions are trusted. All MERGE decisions are escalated to pass 2.
2. **Pass 2 (2.5-pro):** Only processes the keys flash-lite flagged as MERGE (~30% of total). Re-decides KEEP/MERGE/DISCARD and writes merge text where appropriate.

**Projected time/throughput savings on 111-key eval set:**

- Pass 1: 11 clusters at 13.2s/cluster = ~145s (111 keys)
- Pass 2: ~34 MERGE-flagged keys across fewer, smaller clusters at 46.7s/cluster ≈ ~140s
- Total: ~285s vs 513s for pure 2.5-pro (44% time reduction)
- 2.5-pro API volume: ~34 keys vs 111 keys (69% reduction)

At production scale (522 items), the savings compound because flash-lite processes the full store quickly and only the ambiguous MERGE cases reach the slow 2.5-pro pass.

**For strategy points** (KEEP/DISCARD only, no MERGE operation), flash-lite may be sufficient on its own — the over-merge problem doesn't apply. This needs separate validation.

### Two-pass golden eval results (v3 prompts)

End-to-end accuracy validation of the two-pass pipeline on the 111-key golden eval set.

| Approach | Accuracy | Time | Escalation Rate |
|---|---|---|---|
| **Two-pass (lite→pro)** | **89.2% (99/111)** | **311s** | **25% (28/111 keys)** |
| 3.5-flash single-pass | 86.5% (96/111) | 343s | — |
| 2.5-pro single-pass | 83.8% (93/111) | 513s | — |
| flash-lite standalone | 72.1% (80/111) | 145s | — |

The two-pass pipeline is the best approach across all dimensions: highest accuracy (+2.7pp over next best), fastest of the accurate options, and gets 2.5-pro's merge rewrite quality where it matters.

**Strategy clusters had 0% escalation** — all KEEP/DISCARD decisions handled by flash-lite alone. Escalation only happens on observation clusters with real MERGE candidates.

**Per-cluster results:**

| Cluster | Kind | Size | Accuracy | Escalated | Notes |
|---|---|---|---|---|---|
| C0 | obs | 10 | 80% (8/10) | 0/10 | Flash-lite missed 2 DISCARDs |
| C4 | obs | 23 | 83% (19/23) | 8/23 | Largest cluster, good targeting |
| C5 | obs | 5 | 100% (5/5) | 0/5 | Pure-KEEP control |
| C11 | obs | 10 | 100% (10/10) | 6/10 | Perfect with escalation |
| C14 | obs | 15 | 80% (12/15) | 10/15 | 2.5-pro over-merged 3 items |
| C16 | obs | 8 | 100% (8/8) | 4/8 | Perfect with escalation |
| C20 | strat | 2 | 100% (2/2) | 0/2 | Pure-KEEP control |
| C21 | strat | 9 | 89% (8/9) | 0/9 | 1 missed DISCARD |
| C25 | strat | 11 | 82% (9/11) | 0/11 | Over-discarded 2 |
| C28 | strat | 16 | 100% (16/16) | 0/16 | Perfect |
| C33 | strat | 2 | 100% (2/2) | 0/2 | Perfect |

**Confusion matrix (12 errors):**

| Golden ↓ \ Model → | KEEP | DISCARD | MERGE | MISSING |
|---|---|---|---|---|
| KEEP (77) | **71** | 2 | 4 | 0 |
| DISCARD (20) | 2 | **17** | 0 | 1 |
| MERGE (14) | 3 | 0 | **11** | 0 |

No dominant error mode. The 4 KEEP→MERGE errors come from 2.5-pro over-merging on escalated items, consistent with its known tendency.

**Escalation rate: golden eval vs full store.** The golden eval showed 25% escalation (28/111 keys), much lower than the 64% seen on the full v4 store dry run. The full store has more large/ambiguous observation clusters that trigger flash-lite's over-merge tendency. At production scale, the escalation rate will likely fall between these bounds depending on cluster composition.

**Full-store dry run results (v4, 522 items):**

| | v4 (raw) | Two-pass result | v4_deduped_v2 (3.5-flash) | v4_deduped (v0) |
|---|---|---|---|---|
| Observations | 324 | 279 (-14%) | 269 (-17%) | 150 (-54%) |
| Strategy | 198 | 160 (-19%) | 163 (-18%) | 167 (-16%) |
| **Total** | **522** | **439 (-16%)** | **432 (-17%)** | **320 (-39%)** |

The two-pass produces comparable store sizes to 3.5-flash single-pass (16% vs 17% reduction), with the advantage of proper merge rewrite quality from 2.5-pro.

### Recommendation (preliminary — see *Resolved recommendation* below)

**Two-pass pipeline (flash-lite triage → 2.5-pro verification)** is the recommended production approach:
- Best accuracy (89.2%) and fastest accurate option (311s on eval set)
- Flash-lite handles all strategy KEEP/DISCARD decisions standalone (0% escalation)
- 2.5-pro writes high-quality merge text only where needed
- Comparable store-size outcomes to 3.5-flash single-pass, with better merge quality

**Remaining concern:** Full-store escalation rate (64%) is higher than golden eval (25%). This affects efficiency but not accuracy — the pipeline still produces correct results, just with more 2.5-pro calls than optimal. Potential mitigations: stronger anti-merge bias in flash-lite triage prompt, or cluster size limits that reduce ambiguity.

## Flash-lite Anti-Overmerge Prompt Tuning

The default v3 observation prompt causes flash-lite to over-merge (19 KEEP→MERGE errors, 32.4% MERGE precision). A dedicated "lite" prompt variant was created to address this without changing 2.5-pro's prompt.

### Prompt changes (v3 → lite)

Stored as `prompt_versions/batch_v4_lite_anti_overmerge.py`. Key additions to observation prompt only (strategy prompt unchanged):

- **CALIBRATION note at top**: "KEEP is the default. Most entries should be kept. MERGE is rare."
- **MERGE RED FLAGS checklist**: 6 conditions that indicate over-merge (different game phases, different player counts, etc.)
- **Group size tightening**: Merge groups >3 entries flagged as "almost always wrong"
- **"When in doubt KEEP" directive**: Explicit instruction for ambiguous cases
- Prompt length: 7284 chars (99 chars shorter than default 7383 chars)

### Golden eval results (lite prompt, flash-lite only)

| Approach | Accuracy | Time | Notes |
|---|---|---|---|
| **flash-lite + lite prompt** | **85.6% (95/111)** | **132s** | KEEP→MERGE: 1 (down from 19) |
| flash-lite + v3 default | 72.1% (80/111) | 145s | KEEP→MERGE: 19 |
| two-pass (lite→pro, v3) | 89.2% (99/111) | 311s | Best overall |
| 3.5-flash (v3) | 86.5% (96/111) | 343s | Best single-model |

**Confusion matrix (lite prompt, 16 errors):**

| Golden ↓ \ Model → | KEEP | DISCARD | MERGE | MISSING |
|---|---|---|---|---|
| KEEP (77) | **74** | 2 | 1 | 0 |
| DISCARD (20) | 2 | **13** | 4 | 1 |
| MERGE (14) | 5 | 1 | **8** | 0 |

**Per-prediction precision:**

| Prediction | Default v3 | Lite prompt | Change |
|---|---|---|---|
| KEEP | 56/61 = 91.8% | 74/81 = 91.4% | ~same |
| DISCARD | 13/15 = 86.7% | 13/16 = 81.2% | ~same |
| MERGE | 11/34 = 32.4% | 8/13 = **61.5%** | +29pp |

The lite prompt fixed the over-merge problem. MERGE precision jumped from 32.4% to 61.5%. The error profile flipped from over-merge (19 KEEP→MERGE) to slight under-merge (5 MERGE→KEEP), which is the safe direction. KEEP and DISCARD precision remained stable.

### V4 full-store dry run comparison

| Config | Obs Items | Obs Remain | Obs Merged | Obs Disc | Strat Items | Strat Remain | Strat Disc | Total | Remain | Red% |
|---|---|---|---|---|---|---|---|---|---|---|
| v4 raw (3.5-flash) | 324 | 150 | 174 | 0 | 198 | 147 | 51 | 522 | 297 | 43.1% |
| v4_deduped_v2 (3.5-flash) | 324 | 269 | 54 | 1 | 198 | 163 | 35 | 522 | 432 | 17.2% |
| two-pass (lite→pro, v3) | 324 | 279 | 40 | 5 | 198 | 160 | 38 | 522 | 439 | 15.9% |
| **flash-lite + lite prompt** | **324** | **280** | **44** | **0** | **198** | **160** | **38** | **522** | **440** | **15.7%** |

Flash-lite with the lite prompt produces nearly identical store-level outcomes to the two-pass pipeline (440 vs 439 remaining), without requiring 2.5-pro at all. Strategy point decisions are identical across both (160 remaining, 38 discarded) — the lite prompt only changes observation behavior.

The observation merge count (44) is slightly higher than two-pass (40), suggesting flash-lite still has a mild over-merge tendency that 2.5-pro would catch. However, the 0 observation discards (vs 5 in two-pass) shows the lite prompt is more conservative overall.

### Two-pass with lite prompt (validated)

Initial eval had a bug: `--prompt-variant` wasn't passed to the triage call in `call_model_two_pass()`. After fixing (`batch_dedup_eval.py` lines 153-166), re-ran with the lite prompt actually applied.

| Approach | Accuracy | Time | Escalation | MERGE→KEEP |
|---|---|---|---|---|
| Two-pass + v3 default | **89.2% (99/111)** | 311s | 25% (28 keys) | 3 |
| Two-pass + lite prompt | 84.7% (94/111) | **227s** | **12% (13 keys)** | 7 |
| Flash-lite + lite standalone | 85.6% (95/111) | 132s | — | 5 |
| 3.5-flash single-pass | 86.5% (96/111) | 343s | — | — |

The lite prompt halved escalation (25% → 12%) and reduced total time by 27% (311s → 227s), but accuracy dropped 4.5pp (89.2% → 84.7%). The cause: the lite prompt's conservatism prevents legitimate MERGEs from reaching 2.5-pro (7 MERGE→KEEP errors vs 3 with default). The v3 default prompt's "over-escalation" is actually beneficial — 2.5-pro catches false MERGEs while confirming real ones.

### Resolved recommendation

This is the settled verdict (it supersedes the preliminary one above, after the harness-bug fix).
**Two-pass pipeline remains the recommended approach.** The prompt variant choice is a speed/accuracy tradeoff:

- **Best accuracy: two-pass + v3 default prompt** (89.2%, 311s, 25% escalation). Over-escalation is a feature — all real MERGEs reach 2.5-pro for verification. Use this for periodic maintenance dedup where quality matters most.
- **Best speed/cost ratio: two-pass + lite prompt** (84.7%, 227s, 12% escalation). 27% faster, 52% fewer 2.5-pro calls. Trades 4.5pp accuracy for efficiency. Use this if running dedup more frequently (e.g., after every few games) where cumulative cost matters.

Current default: **v3 default prompt**. Switch to lite if batch dedup frequency increases.

## Idempotency Test

Ran the two-pass pipeline (v3 default prompt) on `v4_deduped_v2` — a store that was already deduped once with 3.5-flash. If the pipeline were idempotent, it should produce near-zero changes.

### Results

| | Before (v4_deduped_v2) | After 2nd run | Removed | % |
|---|---|---|---|---|
| Observations | 269 | 239 | 30 merged | 11.2% |
| Strategy | 163 | 148 | 15 discarded | 9.2% |
| **Total** | **432** | **387** | **45** | **10.4%** |

**The pipeline is not idempotent.** A second run removed another 45 items (10.4% of the store).

Stored at `memory_stores/v2_idempotency` for comparison. Report at `eval_results/store_dedup/v2_idempotency_report.json`.

### Analysis of second-pass changes

**Observation merges (30 absorbed, 22 survivors rewritten):**
- Rewrite quality is good: 2.5-pro preserved all three fields (situation, approach, outcome) in 22/22 cases. Tactic counts added where missing (9/22 had counts before → 22/22 after).
- Game phase markers preserved in 19/22 situations. Player IDs correctly generalized out.
- However, some merges combined genuinely distinct situations. Example: an early-game investigator accusation (no established credibility) was merged with an endgame investigator lead (rich information, final wolf). These would be retrieved by different queries and represent different lessons.

**Strategy discards (15 removed):**
- Mostly legitimate. E.g., three near-identical "first night wolf target selection" strategies (ec98a356, d6191f69, a579efaf) discarded as duplicates of survivors (44dbaaee, 54a1a2d3) that express the same advice with minor wording differences.

### Root causes

1. **Re-clustering after dedup changes composition.** The first dedup removes entries, changing which entries fall into the same similarity cluster on the next run. Entries that were in separate clusters before may now be grouped together, creating new merge/discard opportunities.
2. **Model non-determinism on borderline cases.** The same cluster presented twice may get different KEEP/MERGE/DISCARD decisions, especially near the decision boundary.
3. **Embedding similarity != situation identity.** Entries with similar embeddings (so they cluster together) may describe functionally different situations. The LLM correctly keeps them separate in one clustering context but merges them in another.

### Implications for production

Running batch dedup repeatedly on the same store will cause cumulative shrinkage — each pass removes ~10% of items. Some removals are legitimate (the first pass missed them), but others degrade the store by merging retrieval-distinct entries.

**Mitigations:**
- **Incremental dedup**: Track last dedup timestamp, only process clusters containing new entries. Prevents re-processing old entries while still comparing new entries against old neighbors. **Implemented** — see below.
- **Full-store refresh (deliberate)**: Periodic re-run without `--incremental` to consolidate older entries that have been superseded by newer experience. The 10.4% shrinkage is partly legitimate — strategy discards are mostly correct, and observation rewrites update language to be more general/retrievable. The risk is only from unbounded repeated full-store runs.

### Incremental dedup (implemented)

Added `--incremental` flag to `memory_batch_deduplication.py`. Mechanism:

1. After each `--apply` run, writes `.last_dedup_at` timestamp to the store directory
2. On next `--incremental` run, reads this timestamp and scans JSON files for entries with `created_at > last_dedup_at`
3. Clusters are built normally (all entries participate in similarity matching), but only clusters containing at least one new entry are sent to the LLM
4. All-old clusters are skipped — no re-processing, no cost

Usage:
```
# Routine after-game dedup (only new entries)
poetry run python Agents/memory_batch_deduplication.py --store-dir <path> --incremental --apply --two-pass

# Periodic full-store refresh (deliberate re-processing)
poetry run python Agents/memory_batch_deduplication.py --store-dir <path> --apply --two-pass
```

This gives two complementary modes:
- **Incremental** (after each batch of games): integrates new entries against existing store, prevents bloat
- **Full refresh** (less frequently): re-processes everything, consolidates older entries reflecting newer dynamics

## Next Steps

1. ~~**Implement and validate the two-pass pipeline**~~ — **Done.** Two-pass infrastructure in `memory_batch_deduplication.py` (CLI: `--two-pass`, `--triage-model`, `--verify-model`). Golden eval: 89.2% accuracy, best of all approaches. See [two-pass golden eval results](#two-pass-golden-eval-results-v3-prompts).
2. ~~**Measure retrieval impact of v3-calibrated store**~~ — **Done.** v4_deduped_v2 (v3 prompts, 432 items) outperforms both v4 and v4_deduped on retrieval quality at n=39. See [store_retrieval_impact](../store_retrieval_impact/experiment_log.md#phase-2).
3. ~~**Tune flash-lite triage prompt**~~ — **Done.** Lite anti-overmerge prompt created and evaluated. Standalone: 85.6% (up from 72.1%). Two-pass with lite: 84.7% at 12% escalation vs 89.2% at 25% escalation with v3 default. See [flash-lite anti-overmerge prompt tuning](#flash-lite-anti-overmerge-prompt-tuning) and [two-pass with lite prompt](#two-pass-with-lite-prompt-validated).
4. ~~**Solve idempotency before integration**~~ — **Done.** Incremental dedup mode (`--incremental`) implemented. Tracks `.last_dedup_at` timestamp, skips all-old clusters. See [incremental dedup](#incremental-dedup-implemented).
5. ~~**Integrate batch dedup into the game pipeline**~~ — **Done.** `BatchDedupConfig` added to `MemoryPersistenceConfig` (disabled by default). When enabled, runs incremental two-pass dedup after memory dump in `post_game_analysis()`. Enable via `build_game_config(memory_persistence_config=MemoryPersistenceConfig(batch_dedup=BatchDedupConfig(enabled=True)))`.

## Current live state (2026-06-25)

**This isn't shelved — the parts that earned their keep run today.** The deterministic **gate**
(`gate_enabled=True`) and **bounded clustering** are live: the gate on every online dedup decision,
bounded clustering in the v7 consolidation loop (`evaluation/src/loop/consolidate.py`). What's off is the
**offline two-pass whole-store sweep** — built, wired, and validated, but **one flag** from on
(`IncrementalDedupConfig.enabled=False`, `Agents/memory/persistence/config.py:51`; the system-wide
refresh is manual-only). What shipped from this log:

- **Bounded clustering, gate-partitioned.** The cluster mode is the conservative `bounded`
  (the retrieval-impact finding that aggressive merging hurts —
  [../store_retrieval_impact/experiment_log.md](../store_retrieval_impact/experiment_log.md)), running
  **inside** a deterministic gate partition (`Agents/memory/dedup_gate.py`, v6 — postdates this log),
  not just the `(memory_kind, role, action_phase)` namespace.
- **Two-pass is the resolved config** (flash-lite triage → 2.5-pro verify, v3 default prompt;
  `two_pass=True` within the incremental config); MERGE/rewrite stays a batch-only, pro-model operation.
- **The idempotency alarm was right.** The "second run removes another ~10%" finding here led directly
  to incremental mode and its **freeze-old guard** — now built and live (it was "not yet built" at the
  time of [../incremental_convergence.md](../incremental_convergence.md); see that doc's status banner).
- **Open before flipping the offline pass on: merge fabrication is unguarded** (see *Merge Rewrite
  Quality*) — the one risk to close first.

Full current-vs-documented gaps: [../report.md](../report.md) § *Current-vs-documented gaps*.
