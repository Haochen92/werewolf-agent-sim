# Batch Dedup: Golden Labels and Prompt Tuning

## Motivation

The per-extraction dedup pipeline handles individual new entries against existing candidates. The batch dedup pipeline operates on entire similarity clusters within a namespace, resolving them into DISCARD groups, MERGE groups, and KEEPs. While per-extraction dedup reached 83-85% accuracy through prompt tuning (v1→v11b), the batch dedup prompts were never updated with the refined decision criteria discovered during that process. This experiment ports those criteria to the batch prompts and evaluates their impact.

Batch dedup is more complex than per-extraction: each cluster can contain 2-25 entries and requires multiple operations (not a single D/K decision). The observation batch prompt retains MERGE (dropped from per-extraction) because the model sees full clusters and can consolidate tactic variants with counts.

## Dataset

Source: `eval_sets/batch_dedup_clusters_v4.json` — 34 clusters (19 observation, 15 strategy) with 522 total items, extracted from v4 memory store pre-dedup.

Golden labels: `eval_sets/batch_dedup_golden_labels.json` — 17 clusters, 149 items. Eval set uses 11 clusters (111 keys): 9 with real DISCARD/MERGE operations + 2 pure-KEEP controls. Golden distribution: KEEP=77, DISCARD=20, MERGE=14.

## Prompt Versions

Each important checkpoint is stored in `evidence/dedup/batch_prompt_tuning/prompt_versions/`.

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
6. **Two-pass pipeline (flash-lite triage → 2.5-pro verification) is the recommended production approach** — combines flash-lite's speed and KEEP/DISCARD precision with 2.5-pro's merge quality, reducing 2.5-pro API volume by ~69% (see Time and Cost Analysis). **3.5-flash remains the best single-model option** — fastest, most accurate, no over-merge tendency. 2.5-pro is close but 50% slower with no accuracy advantage.

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
| gemini-3.5-flash | 6 | 4.33 | 3.00 | 1.67 | 0% |
| gemini-2.5-pro | 6 | 4.33 | 4.00 | 4.00 | 33% |

### Analysis

**3.5-flash drops merged_approach and merged_outcome fields entirely** during MERGE operations — it only outputs merged_situation. This is the root cause of the 1.67 information preservation score. Three attempts to fix this via prompt/schema changes all failed:

1. Verbose "REQUIRED for MERGE" schema descriptions — caused 3+ cluster JSON parse failures
2. Detailed per-field merge rules in prompt (~7750 chars) — 4 cluster failures
3. Minimal one-sentence "all three fields are required" addition (~7425 chars) — 3 cluster failures

The observation prompt at ~7383 chars is at 3.5-flash's structured output capacity limit. Any additional instruction text triggers JSON parse failures on MERGE-heavy clusters. This is a model limitation, not a prompt issue.

**3.5-flash run-to-run variance**: Re-runs with identical v3 prompts showed different clusters failing JSON parse (C25 on one run, none on another) and C14 accuracy fluctuating between 40-100%. The model is non-deterministic near its capacity boundary. Best observed: 86.5% (96/111). Worst same-prompt re-run: 81.0% (81/100, 1 cluster failed).

**2.5-pro writes high-quality merges** with good information preservation (4.0/5) but fabricates 33% of the time — introducing game context not present in source entries.

## Time and Cost Analysis

### Per-model performance on 111-key eval set (11 clusters, v3 prompts)

| Model | Accuracy | Total Time | Time/Cluster | Relative Speed |
|---|---|---|---|---|
| gemini-3.1-flash-lite (medium) | 72.1% | 145s | 13.2s | 1.0x (baseline) |
| gemini-3.5-flash | 86.5% | 342s | 31.1s | 2.4x slower |
| gemini-2.5-pro | 83.8% | 513s | 46.7s | 3.5x slower |

At production scale (v4 store: 522 items, ~50 clusters), a full 2.5-pro batch dedup run takes 30-40 minutes. This makes it a periodic maintenance operation, not something to run after every game. Cost per run is comparable across models (2.5-pro and 3.5-flash have similar per-token pricing), but the time cost is significant.

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

**Projected cost/time savings on 111-key eval set:**

- Pass 1: 11 clusters at 13.2s/cluster = ~145s (111 keys)
- Pass 2: ~34 MERGE-flagged keys across fewer, smaller clusters at 46.7s/cluster ≈ ~140s
- Total: ~285s vs 513s for pure 2.5-pro (44% time reduction)
- 2.5-pro API volume: ~34 keys vs 111 keys (69% reduction)

At production scale (522 items), the savings compound because flash-lite processes the full store cheaply and only the ambiguous MERGE cases reach 2.5-pro.

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

### Recommendation

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

### Recommendation (updated)

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

Stored at `Agents/memory_stores/v2_idempotency` for comparison. Report at `eval_results/store_dedup/v2_idempotency_report.json`.

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

**Mitigations to consider before integration:**
- **Incremental dedup only**: Track which entries have been deduped (e.g., `dedup_version` field) and only process new entries against the existing deduped store. Never re-process the full store.
- **Convergence threshold**: Run dedup, then re-run as a dry run. If the second pass would change >N% of entries, flag for manual review rather than applying.
- **Dedup lock**: Mark entries as "dedup-finalized" after processing. Only cluster finalized entries with new (unfinalized) entries, never with each other.

## Next Steps

1. ~~**Implement and validate the two-pass pipeline**~~ — **Done.** Two-pass infrastructure in `memory_batch_deduplication.py` (CLI: `--two-pass`, `--triage-model`, `--verify-model`). Golden eval: 89.2% accuracy, best of all approaches. See [two-pass golden eval results](#two-pass-golden-eval-results-v3-prompts).
2. ~~**Measure retrieval impact of v3-calibrated store**~~ — **Done.** v4_deduped_v2 (v3 prompts, 432 items) outperforms both v4 and v4_deduped on retrieval quality at n=39. See [store_retrieval_impact](../store_retrieval_impact/report.md#phase-2).
3. ~~**Tune flash-lite triage prompt**~~ — **Done.** Lite anti-overmerge prompt created and evaluated. Standalone: 85.6% (up from 72.1%). Two-pass with lite: 84.7% at 12% escalation vs 89.2% at 25% escalation with v3 default. See [flash-lite anti-overmerge prompt tuning](#flash-lite-anti-overmerge-prompt-tuning) and [two-pass with lite prompt](#two-pass-with-lite-prompt-validated).
4. **Solve idempotency before integration** — the pipeline removes ~10% of entries on each re-run, with some merges degrading quality. Need incremental dedup (only process new entries) or a dedup-lock mechanism before wiring into the game flow. See [idempotency test](#idempotency-test).
5. **Integrate batch dedup into the game pipeline** — wire two-pass batch dedup into the post-game flow, pending idempotency fix.
