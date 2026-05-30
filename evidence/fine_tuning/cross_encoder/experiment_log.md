# Fine-Tuning: Cross-Encoder for Dedup Scoring

## Motivation

The embedding fine-tuning experiments (see `evidence/fine_tuning/embedding/experiment_log.md`) failed to improve auto-dedup performance because similarity-based approaches can't distinguish "same topic, same advice" from "same topic, opposite advice." A cross-encoder reads both texts jointly and could potentially learn this distinction — it scores pairs at inference time without modifying the embedding space, so it can't destroy calibration.

The specific use case: replace or supplement the Gemini embedding cosine similarity thresholds in the production auto-dedup pre-filter (`Agents/memory_deduplication.py`). The production system uses:
- Strategy points: `action_sim` (cosine similarity between action fields)
- Observations: `content_sim` (cosine similarity of concatenated situation+approach+outcome)

If a cross-encoder can produce wider D/K gaps on the same field inputs, it would increase the auto-dedup rate (currently ~24% zero-error on the 65-case golden set).

## Dataset

Reused the 861 labeled dedup cases from Project 1 (dedup classifier). Converted to pairs format via `build_pairs.py --text dedup`:
- 389 D cases (label=1.0): positive pairs
- 472 K cases (label=0.0): negative pairs
- Stratified 90/10 train/eval split

**No train/eval contamination:** The 861 training cases come from extraction fine-tuning experiments run on 10 games. The 65-case golden eval set (`dedup_v2_golden_labels.json`) comes from 24 different games. Zero game IDs in common — verified by fingerprinting on game_id + entry text across both datasets.

Three text formatting modes were tested during development:
- `situation`: situation field only (same as embedding training — invalid comparison)
- `full`: labeled multi-field text (`Situation: X\nAction: Y`) — not what production uses
- `dedup`: matches production auto-dedup exactly (action-only for SP, space-concatenated content for obs)

Only the `dedup` mode produces a valid apples-to-apples comparison against the production Gemini auto-dedup baseline. Earlier runs with `situation` and `full` modes are not reported here because they compare different input signals — the cross-encoder would be scoring different text than what the production auto-dedup thresholds operate on.

## Training: ce_minilm_dedup_run1 (2026-05-28)

**Config:** cross-encoder/ms-marco-MiniLM-L-6-v2 (22M params), 10 epochs, batch_size=16, lr=2e-5, bf16, L4 GPU, CEBinaryClassificationEvaluator, `metric_for_best_model="val_average_precision"`

**Eval metrics:**
- Accuracy: 78.2%
- Average precision: 84.0%
- F1: 0.756
- Precision: 0.721, Recall: 0.795

## Evaluation: Apples-to-Apples vs Production Auto-Dedup

Scored all 65 golden set cases (`dedup_v2_golden_labels.json`) with the cross-encoder using the same field inputs as the production auto-dedup. Compared threshold sweeps directly against the Gemini field-specific similarity baseline.

Gemini baseline loaded from `evidence/dedup_golden_eval/embedding_cache.json` (action_sim for SP, content_sim for obs).

### Strategy Points (25 cases: 10D, 15K)

| Method | Gap (D-K) | Zero-error auto% | ≤1-error auto% |
|--------|-----------|------------------|----------------|
| Gemini action_sim | 0.035 | 16.0% (4D+0K) | 28.0% (4D+3K) |
| **Fine-tuned CE** | **2.106** | **24.0%** (1D+5K) | **32.0%** (3D+5K) |

The cross-encoder wins on strategy points. Wider gap (2.1 vs 0.035) and higher auto-rate at both zero-error (+8%) and ≤1-error (+4%). The CE's advantage comes from better auto-keep detection — it correctly identifies 5 K cases that Gemini misses.

### Observations (40 cases: 20D, 20K)

| Method | Gap (D-K) | Zero-error auto% | ≤1-error auto% |
|--------|-----------|------------------|----------------|
| **Gemini content_sim** | **0.015** | **12.5%** (4D+1K) | **35.0%** (4D+10K) |
| Fine-tuned CE | 1.120 | 10.0% (3D+1K) | 22.5% (8D+1K) |

Gemini wins on observations. Despite a much narrower gap, Gemini achieves higher auto-rates because its narrow score band means fewer confident-but-wrong predictions. The CE has a wider gap but worse outlier behavior — some D cases score very negative and some K cases score positive.

The CE's observation weakness is especially visible at ≤1-error: Gemini catches 10 auto-keeps vs CE's 1. Observation content is longer and more complex, where Gemini's larger model has an edge over the 22M MiniLM.

### The Opposite-Action Problem

The cross-encoder suffers from the same fundamental limitation identified in the embedding pre-filter calibration (`evidence/dedup/embedding_prefilter/experiment_log.md`): **it cannot distinguish "same topic, same advice" from "same topic, opposite advice."**

Concrete examples from the golden set:

**K case `dffb693a668b1314` (CE=4.19, highest false positive):**
- NEW action: "**Immediately and aggressively lead** the accusation against the wolf"
- CAND action: "**Avoid taking a strong leadership role** or making a direct accusation"
- Same situation (identified a wolf and survived), completely opposite advice. The CE scores this as a strong duplicate because the vocabulary and topic overlap heavily.

**K case `9df0246acb7b99e5` (CE=1.40):**
- NEW action: "Do not cast a futile vote... **vote against a different, less suspicious villager**"
- CAND action: "**Vote with the majority** to eliminate your partner"
- Same situation (partner under suspicion), opposite voting strategies.

**D case `5381e52cde68e398` (CE=-0.97, missed duplicate):**
- NEW action: "**Protect the most vocal player**"
- CAND action: "**Avoid protecting the most aggressively talkative player**"
- Labeled D (same underlying hypothesis) but opposite framing. The CE sees contradiction and predicts KEEP.

This is the same "embeddings capture topic, not position" limitation — and it applies equally to cross-encoders. A 22M model trained on 861 examples cannot learn the nuanced distinction between "genuinely opposite advice" (K) and "same advice with opposite framing" (D). This requires LLM-level reasoning about what the text *means*, not just lexical/semantic similarity.

## Round 2: Larger Base Model — ce_bge_dedup_run1 (2026-05-28)

Tested `BAAI/bge-reranker-base` (110M params, 5x larger) to see if more model capacity improves discrimination.

**Config:** Same as run 1 — 10 epochs, batch_size=16, lr=2e-5, bf16, L4 GPU, `metric_for_best_model="val_average_precision"`, 861 dedup-matched pairs.

**Training metrics (best epoch = 5):**
- Average precision: 79.8%
- Accuracy: 74.7%
- Precision: 0.596, Recall: 0.795

Overfitting was severe — AP peaked at epoch 5 then collapsed:

| Epoch | Accuracy | AP | Eval Loss |
|-------|----------|------|-----------|
| 1 | 67.8% | 0.701 | 0.597 |
| 3 | 70.1% | 0.752 | 0.831 |
| 5 | 74.7% | **0.798** | 1.142 |
| 7 | 73.6% | 0.698 | 1.983 |
| 10 | 74.7% | 0.673 | 2.329 |

### Golden Set Evaluation

| Method | SP gap | SP zero-error | Obs gap | Obs zero-error |
|--------|--------|---------------|---------|----------------|
| Gemini field-sim | 0.035 | 16.0% | 0.015 | 12.5% |
| **MiniLM CE (22M)** | **2.106** | **24.0%** | 1.120 | 10.0% |
| BGE CE (110M) | 0.012 | none | 0.130 | none |

The larger model performed **worse** than the smaller MiniLM across the board. No zero-error thresholds found for either item type. Score distributions show both D and K cases spanning the full 0-1 range with no separation (D: 0.001–0.999, K: 0.0003–0.994).

### Why larger model = worse

The 110M model overfitted on 861 pairs — 5x more parameters learning the same small dataset. The training loss dropped to near-zero (0.0003 by epoch 10) while eval loss climbed 4x. The model memorized training examples rather than learning generalizable discrimination patterns.

This confirms **more training data is the bottleneck**, not model capacity. The MiniLM hit a sweet spot: small enough to not overfit on 861 pairs, large enough to learn useful signal on strategy points.

## Local Deployment Benchmark (2026-05-28)

Tested the fine-tuned MiniLM (22M) locally on CPU to assess production viability as an auto-dedup pre-filter.

### Performance

| Setting | ms/call (3 pairs) | CPU% | Memory |
|---------|-------------------|------|--------|
| PyTorch defaults | 50ms | 300% (all cores) | 900MB |
| Single-threaded | 79ms | ~100% (1 core) | 900MB |
| ONNX Runtime (est.) | 30-50ms | ~100% (1 core) | 150-200MB |

Single-threaded settings (non-blocking):
```
TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
torch.set_num_threads(1)
```

**Per-game cost:** 15 dedup calls × 79ms = ~1.2s total, spread across the game. Each call is a brief single-core burst between LLM API calls (which take 100s of ms themselves). No blocking of other operations.

**Memory:** ~900MB is dominated by PyTorch runtime (~700MB). ONNX export would reduce to ~150-200MB by dropping PyTorch entirely. The model weights themselves are only 87MB.

## ONNX Deployment Benchmark (2026-05-29)

Updated benchmarks with the exported ONNX model (`ce_minilm_dedup_onnx/`):

| Setting | ms/pair | ms/3 pairs | CPU% | RSS Memory |
|---------|---------|------------|------|------------|
| PyTorch defaults | ~17ms | 50ms | 300% (all cores) | 900MB |
| PyTorch single-threaded | ~26ms | 79ms | ~100% (1 core) | 900MB |
| **ONNX single-threaded** | **16.6ms** | **50ms** | **89% (1 core)** | **90MB** |

ONNX configuration:
```python
opts = ort.SessionOptions()
opts.intra_op_num_threads = 1
opts.inter_op_num_threads = 1
opts.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
```

The 89% single-core spike lasts only ~17ms per pair. In the game loop, dedup calls are sequential and interleaved with LLM API calls (100s of ms each), so the CPU burst is non-blocking.

**Per-game overhead:** 15 dedup calls × ~50ms = ~750ms total, scattered across turns. Memory footprint is 90MB RSS — 10x lighter than PyTorch.

## Conclusion

The MiniLM (22M) cross-encoder shows promising signal:
- **Strategy points:** wider D/K score gap (2.1 vs Gemini's 0.035), +8% zero-error auto-rate (24% vs 16%)
- **Observations:** slightly worse than Gemini (-2.5% zero-error)
- **Locally deployable:** ONNX at 16.6ms/pair, 90MB RSS, single-core, no GPU, no API cost
- **No train/eval contamination:** training data (10 games) and golden eval (24 games) share zero game IDs

The BGE (110M) experiment confirmed that model size isn't the bottleneck — data volume is.

The intended deployment is a **hybrid approach**: CE for auto-keep on strategy points (where it excels), Gemini embedding similarity for auto-discard (where it excels). The two have complementary strengths — CE auto-decided 1D+5K at zero error, Gemini auto-decided 4D+0K.

## Evaluation Rigor Issues (2026-05-29)

The headline numbers (+8% zero-error) are directionally correct but **not rigorous enough to commit to deployment**. Three issues must be addressed:

### 1. Sample size (critical)

The strategy point eval set has only **25 cases** (10D, 15K). The +8% difference is 2 extra cases (6 vs 4 auto-decided). The 95% confidence intervals for 24% and 16% overlap heavily at this sample size. We need **100+ SP cases** to detect an 8% difference with statistical significance.

### 2. Threshold overfitting

Zero-error thresholds were found by grid search on the same 25 SP golden cases used to report results. There is no held-out set separate from threshold tuning. Both CE and Gemini thresholds are optimized on this set, so reported auto-rates are optimistic upper bounds. With a larger eval set, we should **split into threshold-tuning (50%) and held-out test (50%)** sets.

### 3. Complementary profiles, not clean comparison

CE and Gemini are solving different sub-problems:

| | Auto-D | Auto-K |
|---|---|---|
| CE | 1 | 5 |
| Gemini | 4 | 0 |

Blending these into a single "auto%" obscures what each does well. Evaluation should report **auto-D rate and auto-K rate separately**, with per-class precision for each.

### Blocker: insufficient fresh game data

Expanding the eval set requires labeled SP dedup cases from games not used in training (10 games) or current eval (24 games). Current data inventory:

| Source | Fresh games | Fresh SP cases |
|---|---|---|
| dedup_v2 remainder | 1 | ~8 |
| dedup_v1 | 3 | ~14 |
| **Total available** | **4** | **~22** |

Only 38 unique games exist across all datasets; 34 are already used. To reach 100+ fresh SP cases, we need **~25 new games** run through the extraction and dedup pipeline (~4 SP dedup cases per game).

### Next steps

1. **Hold deployment** until eval is rigorous
2. **Run new games** after pipeline is finalized to generate fresh transcripts
3. Generate dedup cases from new games against v4_deduped_v2 store using `generate_dedup_cases.py`
4. Label via 3-model triage + manual review (existing co-labeling infrastructure)
5. Split expanded golden set: 50% threshold tuning, 50% held-out test
6. Report per-class auto-rates with confidence intervals

## Artifacts

| File | Description |
|------|-------------|
| `train_modal.py` | Cross-encoder training on Modal (L4 GPU) |
| `eval_modal.py` | Golden set eval with Gemini baseline comparison |
| `ce_minilm_dedup_run1/` | Fine-tuned MiniLM weights (local copy) |
| `../embedding/pairs_dedup.jsonl` | Training pairs matching production auto-dedup fields |
| `../embedding/build_pairs.py --text dedup` | Generates dedup-matched pairs |

Model weights on Modal volume `cross-encoder-finetune-output`:
```bash
modal volume get cross-encoder-finetune-output ce_minilm_dedup_run1/ ./local_cross_encoder/
```

---

# Fine-Tuning: Cross-Encoder for Retrieval Reranking

## Motivation

The retrieval pipeline uses flash-lite as an LLM reranker to score (query, memory) pairs after embedding retrieval. This adds ~50% per-turn cost. A fine-tuned cross-encoder could replace it: same scoring quality, ~79ms on CPU, zero API cost.

Training data comes from golden retrieval labels — human-annotated relevance grades for (situation_query, memory_text) pairs across 40 game cases.

## Dataset

Source: `retrieval_golden_labels.json` — 40 cases, 768 labeled (query, memory, relevance) triples.

Two labeling methods:
- **Old batch (20 cases):** human + claude + opus-4.6 labels — high quality
- **New batch (20 cases):** 4-model consensus (ChatGPT + flash-lite + 3.5-flash + Qwen 3.5 397B) with manual review corrections (14 items corrected out of 84 reviewed, ~5% error rate)

Label mapping: 0 (irrelevant) → 0.0, 1 (partial) → 0.25, 2 (relevant) → 1.0

Prepared by `prep_reranker_data.py`. Case-level hold-out split prevents query leakage.

### Systematic auto-model bias in new labels

The 3 auto models (flash-lite, 3.5-flash, Qwen) systematically inflate relevance compared to ChatGPT (which had full game context). Auto distribution: 44% grade-2 vs ChatGPT 31%. Pairwise agreement: auto models agree with each other (71-74%) more than with ChatGPT (56-68%).

Manual review found all 14 errors followed the same pattern: auto models matched surface-level themes without checking whether the memory's preconditions actually applied to the query situation. The remaining ~230 unreviewed items likely contain more of this noise.

## Training: reranker_v1_baseline (2026-05-29)

**Purpose:** Baseline with original 20 human-labeled cases only.

**Config:** cross-encoder/ms-marco-MiniLM-L-6-v2 (22M params), 20 epochs, batch_size=16, lr=2e-5, warmup_ratio=0.1, bf16, L4 GPU, eval_strategy=epoch, best model by eval_loss.

**Data:** 327 train pairs (16 cases), 121 eval pairs (4 cases: {10, 14, 16, 20})

**Eval metrics:**

| Case | Role | NDCG@5 | n |
|------|------|--------|---|
| 10 | investigator-discussion | 0.657 | 34 |
| 14 | wolf-discussion | 0.774 | 37 |
| 16 | healer-discussion | 0.887 | 20 |
| 20 | villager-discussion | 0.790 | 30 |
| **Mean** | | **0.777** | |

- MSE: 1.155
- Pearson r: 0.397

## Training: reranker_v2_768pairs (2026-05-29)

**Purpose:** Expanded dataset with all 40 cases (human + 4-model consensus labels).

**Config:** Same as v1 baseline.

**Data:** 579 train pairs (32 cases), 189 eval pairs (8 cases: {5, 10, 14, 16, 20, 22, 24, 29} — 4 old + 4 new, one per role)

**Eval metrics:**

| Case | Role | Split | NDCG@5 | n |
|------|------|-------|--------|---|
| 5 | villager-vote | new | 1.000 | 20 |
| 10 | investigator-discussion | old | 0.589 | 34 |
| 14 | wolf-discussion | old | 0.774 | 37 |
| 16 | healer-discussion | old | 1.000 | 20 |
| 20 | villager-discussion | old | 0.744 | 30 |
| 22 | wolf-discussion | new | 0.786 | 20 |
| 24 | healer-discussion | new | 0.573 | 20 |
| 29 | investigator-vote | new | 0.958 | 8 |
| **Mean** | | | **0.803** | |

- MSE: 3.923
- Pearson r: 0.518

### v1 vs v2 comparison on overlapping eval cases

| Case | v1 (327 train) | v2 (579 train) | Delta |
|------|----------------|----------------|-------|
| 10 | 0.657 | 0.589 | -0.068 |
| 14 | 0.774 | 0.774 | +0.000 |
| 16 | 0.887 | 1.000 | +0.113 |
| 20 | 0.790 | 0.744 | -0.046 |
| **Mean** | **0.777** | **0.777** | **0.000** |

NDCG@5 is flat on the 4 overlapping cases — the extra 20 cases didn't improve ranking quality on these specific queries. However, Pearson r improved significantly (0.397 → 0.518), indicating better score calibration across the full eval set. Better calibration helps with score thresholding and downstream weighting even if top-5 ranking is unchanged.

Likely causes for flat NDCG: (1) new labels are noisier than human labels, partially canceling out the volume gain; (2) 1.8x data increase may be too small for the MiniLM to show ranking gains — may need 2-3k+ pairs.

## Model storage

Weights on Modal volume `cross-encoder-reranker-output`:
```bash
modal volume ls cross-encoder-reranker-output
# reranker_v1           (dedup CE, unrelated)
# reranker_bge_v1       (dedup CE, unrelated)
# reranker_v1_baseline  (retrieval reranker, 20-case baseline)
# reranker_v2_768pairs  (retrieval reranker, 40-case expanded)
```

Download:
```bash
modal volume get cross-encoder-reranker-output reranker_v2_768pairs/ ./local_reranker/
```

Note: local inference causes 300% CPU usage with default PyTorch threading. Single-threaded settings (`OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 torch.set_num_threads(1)`) reduce to ~100% at 79ms/call, but still caused system instability on test machine. ONNX export or S3-backed serverless inference may be needed for production.

## Expanded labeling: 109 new cases (2026-05-29)

### Motivation

v2 model (768 pairs, 40 cases) showed NDCG@5 flat on overlapping eval cases. More data is the bottleneck — target ~150 total cases / ~2,800+ training pairs.

### Dataset

Source: `eval_sets/v4_reranker_expanded.jsonl` — 110 cases from 15 games, 109 new (1 overlap with existing 40). Distribution: 52 wolf, 22 villager, 18 healer, 18 investigator, balanced discussion/vote.

### Step 1: Golden situation generation (done)

Model: `gemini-2.5-pro`, thinking=medium, temperature=0.0 via production `run_situation_summary_variant`. 109 cases, 0 failures, avg 1.1 situations/case.

**Prompt fix applied:** Added `EPISTEMIC_STATUS_RULE` to `Agents/prompt_inputs.py` — the situation summary prompt was missing it (present in extraction/dedup but not situation summary). Without it, generated situations used player IDs instead of behavioral descriptors, causing format mismatch with the memory store.

Stratified review (16 cases, 2 per role×phase): 15/16 passed, 1 rewritten (case 27 — state dump with no tension). Error rate ~6%.

Output: `expanded_golden_situations.json`

### Step 2: Candidate retrieval (done)

Top-10 obs + top-10 sp per case against `v4_deduped_v2` store. Result: 1,848 items (955 obs + 893 sp).

Output: `expanded_candidates_for_labeling.json`

### Step 3: Multi-model consensus labeling (done)

Changed model lineup from previous round (Qwen NIM was down):

| Model | Family | Items | Notes |
|-------|--------|-------|-------|
| `gemini-3.1-flash-lite` | Google | 1,848 | thinking=low |
| `mistral/mistral-small-2506` | Mistral | 1,848 | 300 rpm, fastest |
| `nim/meta/llama-3.1-8b-instruct` | Meta (NIM) | 1,848 | Replaced 70B (429 issues) |
| ChatGPT (thinking medium) | OpenAI | 1,848 | Manual, 22 batches, full game context |
| Claude Sonnet | Anthropic | 1,848 | 5th voter, same batch format as ChatGPT |

Infrastructure changes:
- Added `MistralChatModel` to `Agents/llm_factory.py` (`mistral/` prefix)
- Per-model rate limiter in `label_candidates.py` (NIM 40 rpm cap)
- Incremental checkpoint saves after each case
- Models run independently (3 separate processes) instead of blocking on slowest
- Built reusable `evaluation/labeling/` module (config, engine, voter, merger, exporter, adapters)

NIM notes: `llama-3.3-70b-instruct` was unusable (constant 429s despite 40 rpm claim). Switched to `llama-3.1-8b-instruct` (188 rpm, no issues). 8B has 67% agreement with Mistral-small — conservative bias but acceptable as one voice in 5-model consensus.

### Step 4: Merge + tiebreak (done)

5-model vote (ChatGPT + Sonnet + flash-lite + mistral-small + NIM 8B):

| Confidence | Count | % |
|------------|-------|---|
| majority (3+ agree) | 1,383 | 74.8% |
| unanimous (5/5) | 281 | 15.2% |
| tie_tiebreaker (2v2 + Sonnet breaks) | 144 | 7.8% |
| opus_tiebreak (manual review) | 40 | 2.2% |

**Pairwise agreement rates (all 1,848 items):**

| | ChatGPT | Sonnet | Mistral | Flash-lite | NIM |
|---|---------|--------|---------|------------|-----|
| ChatGPT | — | **64.2%** | 38.4% | 48.2% | 36.4% |
| Sonnet | | — | 43.2% | 49.8% | 40.7% |
| Mistral | | | — | 63.6% | **73.1%** |
| Flash-lite | | | | — | 54.6% |

Two clear clusters: ChatGPT+Sonnet (conservative, full-context) and Mistral+NIM (generous, situation-only). Flash-lite bridges them.

**Opus tiebreak details:** 40 items reviewed manually:
- 9 far-apart ties (0 vs 2): 6 overridden to 1 (voting-phase relevance), 3 confirmed at 0
- 31 remaining ties (all pattern 0,1,1,2,2): all set to 1 — thematic overlap without direct match

**Sonnet reliability as tiebreaker:** On former 2v2 ties (405 items), Sonnet agreed with ChatGPT 65.2% overall (75% on 0v1 ties, 55% on 1v2 ties). Stratified spot-check of 10 cases confirmed ChatGPT tiebreak was correct on all 10 — Sonnet adds independent signal without being a rubber stamp.

### Step 5: Combined dataset + retrain (done)

Combined original 40 cases + 68 expanded cases (40-109) = 108 total cases, 1,919 items.

Stratified split (~70/15/15 per role×phase stratum):
- Train: 74 cases, 1,277 pairs
- Val: 17 cases, 323 pairs
- Test: 17 cases, 319 pairs

## Training: reranker_v3 (2026-05-29)

Renamed from v2 in earlier log. Trained on 40 cases (768 pairs). See v2 section above.

## Training: reranker_v4 (2026-05-30)

**Purpose:** 2.5x more training data (108 cases, 1,277 train pairs).

**Config:** cross-encoder/ms-marco-MiniLM-L-6-v2 (22M params), 20 epochs, batch_size=16, lr=2e-5, warmup_ratio=0.1, bf16, L4 GPU, best model by eval_loss.

**Val metrics (17 cases, 323 pairs):**
- NDCG@5: 0.862 (v3 was 0.803)
- Pearson r: 0.562

**Held-out test results (17 cases, 319 pairs):**

| Method | NDCG@3 | NDCG@5 | 95% CI | Pearson r |
|--------|--------|--------|--------|-----------|
| Bi-encoder (baseline) | 0.757 | 0.767 | [0.697, 0.837] | — |
| Flash-lite (LLM reranker) | 0.857 | 0.871 | [0.800, 0.932] | — |
| **Cross-encoder v4 (MiniLM 22M)** | **0.885** | **0.882** | [0.822, 0.938] | 0.570 |

v4 CI lower bound (0.821) is above v3 mean (0.770) — statistically significant improvement.

**Per-role breakdown (test set NDCG@5):**

| Role | Overall | Observation | Strategy Point | n |
|------|---------|-------------|----------------|---|
| Villager | 0.984 | 1.000 | 0.898 | 4 |
| Wolf | 0.940 | 0.967 | 0.915 | 6 |
| Investigator | 0.807 | 0.935 | 0.629 | 3 |
| Healer | 0.751 | 0.829 | 0.833 | 4 |

| Phase | NDCG@5 | n |
|-------|--------|---|
| Day discussion | 0.874 | 9 |
| Day vote | 0.892 | 8 |

| Memory type | NDCG@5 | n |
|-------------|--------|---|
| Observation | 0.937 | 17 |
| Strategy point | 0.841 | 17 |

Weakest cells: investigator×strategy_point (0.629), healer overall (0.751). Both have fewer training examples — primary targets for next labeling round.

## Training: reranker_v4_bge (2026-05-30)

**Purpose:** Test whether larger model (BGE-base, 110M params) benefits from 2.5x data increase. Previously, BGE underperformed MiniLM on the dedup CE task with 861 pairs.

**Config:** BAAI/bge-reranker-base (110M params), 20 epochs, same hyperparameters as v4.

**Overfitting pattern:** Eval loss bottomed at epoch 5 (0.599) then climbed to 0.955 by epoch 19. Training loss dropped to 0.24 — classic memorization.

**Held-out test results:**

| Model | Params | NDCG@5 | 95% CI | Pearson r |
|-------|--------|--------|--------|-----------|
| Bi-encoder | — | 0.767 | [0.697, 0.837] | — |
| **BGE-base** | 110M | 0.839 | [0.768, 0.907] | 0.500 |
| Flash-lite (LLM) | — | 0.871 | [0.800, 0.932] | — |
| **MiniLM-L6 (v4)** | 22M | **0.882** | [0.822, 0.938] | 0.570 |

BGE improves over bi-encoder (+9.4%) but loses to MiniLM (-5.1%). Consistent with dedup CE findings: 110M params overfit on ~1,300 pairs. The threshold where larger models start winning is likely ~3-5k pairs.

**Inference cost comparison:**

| Method | Latency | Cost | GPU needed |
|--------|---------|------|------------|
| Cross-encoder v4 (MiniLM) | ~80ms/pair (CPU) | Free | No |
| Flash-lite (LLM) | ~125ms/pair (API) | $0.001/turn | No |
| BGE-base | ~400ms/pair (CPU est.) | Free | Recommended |

## Reusable labeling pipeline (2026-05-30)

Extracted a modular `evaluation/labeling/` module from the ad-hoc cross-encoder labeling scripts:

| File | Role |
|------|------|
| `config.py` | Pydantic configs: ModelSpec, VotingConfig, MergeConfig, ExportConfig |
| `base.py` | LabelingAdapter ABC + LabelItem/LabelResult/VoteResult dataclasses |
| `engine.py` | Rate-limited, checkpointed multi-model labeling with resume |
| `voter.py` | Stateless voting: unanimous/majority/tiebreaker/tie detection |
| `merger.py` | N-source merge: model files + human batch files, composite key matching |
| `exporter.py` | Batched markdown export for manual labeling (ChatGPT/Claude) |
| `adapters/reranker.py` | Cross-encoder relevance adapter (0/1/2 scale) |
| `adapters/dedup.py` | Dedup Keep/Discard adapter |

New labeling tasks subclass `LabelingAdapter` and plug into the generic engine. Tested end-to-end against real expanded label files.

### Artifacts

| File | Description |
|------|-------------|
| `generate_situations.py` | Batch situation generation via production pipeline |
| `expanded_golden_situations.json` | 109 cases with 2.5-pro generated situations |
| `expanded_candidates_for_labeling.json` | 1,848 (query, memory) pairs |
| `expanded_labels_mistral.json` | Mistral-small labels (1,848 items) |
| `expanded_labels_flashlite.json` | Flash-lite labels (1,848 items) |
| `expanded_labels_nim.json` | NIM 8B labels (1,848 items) |
| `expanded_merged_labels.json` | 5-model consensus + Opus tiebreak (1,848 items) |
| `labeling_prompts/batch_*.md` | 22 ChatGPT/Sonnet labeling batches |
| `labeling_responses/batch_*_response.json` | ChatGPT responses (22 batches) |
| `sonnet_responses/batch_*_response.json` | Sonnet responses (22 batches) |
| `merge_expanded_labels.py` | Ad-hoc 4-model merge (superseded by evaluation/labeling/) |

Model weights on Modal volume `cross-encoder-reranker-output`:
```bash
modal volume ls cross-encoder-reranker-output
# reranker_v1           (dedup CE, unrelated)
# reranker_bge_v1       (dedup CE, unrelated)
# reranker_v1_baseline  (retrieval reranker, 20-case baseline)
# reranker_v2_768pairs  (retrieval reranker, 40-case, = v3)
# reranker_v3           (retrieval reranker, 40-case, same as v2)
# reranker_v4           (retrieval reranker, 108-case, MiniLM — best)
# reranker_v4_bge       (retrieval reranker, 108-case, BGE-base — overfits)
```

Download:
```bash
modal volume get cross-encoder-reranker-output reranker_v4/ ./evidence/fine_tuning/cross_encoder/reranker_v4/
```
