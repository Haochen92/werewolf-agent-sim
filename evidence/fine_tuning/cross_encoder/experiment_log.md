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

## Conclusion

The MiniLM (22M) cross-encoder remains the best result:
- **Strategy points:** +8% zero-error vs Gemini (24% vs 16%), wider gap (2.1 vs 0.035)
- **Observations:** slightly worse than Gemini (-2.5% zero-error)
- **Locally deployable:** 79ms/call single-threaded, no GPU, no API cost

The BGE (110M) experiment confirmed that model size isn't the bottleneck — data volume is. Future improvement paths:
1. **More training data** (cross-game dataset + production traces → 2-3k pairs) with MiniLM
2. **ONNX export** for lighter deployment (~150MB vs ~900MB)
3. **Hybrid approach** (CE for strategy points, Gemini for observations)

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
