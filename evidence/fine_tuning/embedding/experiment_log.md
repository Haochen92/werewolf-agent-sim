# Fine-Tuning: Embedding and Cross-Encoder

## Motivation

Off-the-shelf Gemini embeddings lack domain-specific discrimination for the werewolf memory store. The similarity gap between true duplicates and genuinely distinct entries is approximately 10%, creating a narrow margin that forces the downstream dedup classifier to make fine-grained distinctions from near-identical similarity scores. This limits both retrieval precision (fetching memories that look relevant but aren't) and dedup clustering quality.

Two-stage approach: first train a cross-encoder reranker (additive, no migration), then evaluate whether full embedding replacement is justified.

## Plan (2026-05-27)

### Stage 1: Cross-Encoder Reranker

**Goal:** Replace the current LLM-based reranking API call (flash-lite with reasoning) with a local fine-tuned cross-encoder. Benefits beyond reranking — the learned similarity discrimination also improves dedup clustering by widening the similarity distribution.

- Base model: BAAI/bge-reranker-base (110M params)
- Library: Sentence Transformers
- Training: pairs with relevance labels from dedup decisions
- Inference: runs locally on CPU, ~10-50ms per query, no API cost
- Estimated cost: $2-3 compute, 2-3 days work

### Stage 2: Full Embedding Replacement (conditional)

**Goal:** Replace Gemini embeddings entirely with a domain-specific model that pushes apart entries that are semantically different in the werewolf context.

- Base model: BAAI/bge-large-en-v1.5 (335M params)
- Loss: MultipleNegativesRankingLoss or TripletLoss
- Requires full re-embedding of memory store (not a gradual migration)
- Only proceed if Stage 1 demonstrates meaningful domain discrimination improvement
- Estimated cost: $3-5 compute, 1-2 weeks work

### Dataset strategy (shared across both stages)

Primary source: dedup decisions map directly to training pairs:
- DISCARD (A duplicates B) → positive pair (should be close)
- KEEP within same cluster → hard negative (currently close but shouldn't be)
- MERGE (same situation, different tactics) → soft positive

Secondary source: reranking traces (LLM reranker promote/demote decisions)

Target: 1000-3000 pairs. Quality of hard negatives matters most.

### Evaluation plan

Build retrieval benchmark BEFORE training:
- 50-100 test queries (situation descriptions from real games) with known relevant memories
- Metrics: Recall@5, Recall@10, MRR, similarity distribution gap
- Must measure impact on BOTH retrieval and dedup pipelines
- Benchmark comparison: Gemini baseline → +reranker → +fine-tuned embedding → combined

### Dependencies
- Dedup classifier (Project 1) should be complete first — lower risk, teaches workflow, labels feed into this dataset
- Win-rate or decision-quality baseline needed before full embedding replacement

---

## Execution Log

### Model selection (2026-05-28)

Changed base model from bge-large-en-v1.5 (335M) to **Alibaba-NLP/gte-modernbert-base** (149M):
- Matches bge-large quality (64.38 vs 64.23 MTEB v1) at less than half the parameters
- 8192 token context (vs 512 for bge), though our situation texts average ~90 tokens
- ModernBERT architecture, Apache 2.0 license
- Well-supported by sentence-transformers for fine-tuning

Decided to skip Stage 1 (cross-encoder) and go directly to Stage 2 (embedding fine-tuning):
- Dataset is already ready from Project 1 dedup labels (861 triplets)
- Eval infrastructure exists (`eval_auto_dedup.py` measures embedding quality on golden set)
- Store re-embedding is not a blocker — stores are rebuilt per experiment anyway
- Cross-encoder would need reranking trace data from Langfuse, unclear volume available

### Dataset preparation (2026-05-28)

Built training pairs from Project 1's 863 labeled dedup cases:
- 389 DISCARD cases → positive pairs (anchor situation ~ duplicate candidate situation)
- 472 KEEP cases → hard negatives (anchor situation !~ closest candidate situation)
- Format: triplets (anchor, positive, negative) for TripletLoss
- 861 triplets total, 90/10 train/eval split
- Output: `triplets.jsonl`, `pairs.jsonl`

Script: `build_pairs.py`
Training script: `train_modal.py` (Modal T4, sentence-transformers)

### Training run 1: gte_base_run1 (2026-05-28)

**Config:** gte-modernbert-base, TripletLoss, 5 epochs, batch_size=32, lr=2e-5, T4 GPU

**Result:** Failed. Two issues:

1. **Missing `accelerate` dependency** — sentence-transformers v5.5.1 requires `accelerate>=1.1.0` for the Trainer, but it wasn't listed in the Modal image `pip_install`. Fixed by adding it explicitly.

2. **Legacy API (`model.fit`)** — the initial script used the pre-v3 sentence-transformers API (`model.fit()` with `InputExample` + `DataLoader`). This ran but produced garbage results: `eval_val_cosine_accuracy: 0`, `train_loss: 3.304`. The `TripletEvaluator` also changed its return type from float to dict in v5, causing a `TypeError` crash on the final eval print.

**Fix:** Rewrote to use the v3+ `SentenceTransformerTrainer` API with HuggingFace `Dataset` format, proper `SentenceTransformerTrainingArguments`, and `eval_strategy="epoch"` with `load_best_model_at_end=True`.

### Training run 2: gte_base_run2 (2026-05-28)

**Config:** Same model, SentenceTransformerTrainer API, batch_size=32, bf16=True, T4 GPU

**Result:** OOM at step 35/125 (partway through epoch 2). Epoch 1 completed successfully with checkpoint saved.

Root cause: two compounding issues:
- **bf16 on T4** — T4 is Turing architecture (compute capability 7.5), bf16 requires Ampere (8.0+). PyTorch falls back to fp32, doubling memory usage.
- **batch_size=32 with TripletLoss** — each training example processes 3 texts (anchor, positive, negative), so effective forward pass batch is 96 sequences. Combined with fp32 fallback, this exceeded T4's 16GB.

**Fix:** Switched to `fp16=True` (T4 has native fp16), reduced batch_size to 16 with `gradient_accumulation_steps=2` (effective batch still 32).

### Training run 3: gte_base_run3 (2026-05-28)

**Config:** gte-modernbert-base, TripletLoss, 5 epochs, batch_size=16, grad_accum=2, fp16=True, T4 GPU

**Result:** Failed immediately. `ValueError: Attempting to unscale FP16 gradients.` — ModernBERT's weights are stored in fp16, so PyTorch's GradScaler (used by fp16 mixed precision) can't unscale gradients that are already fp16.

**Fix:** Switched to L4 GPU (Ampere, native bf16 support) with `bf16=True`.

### Training run 4: gte_base_run4 (2026-05-28)

**Config:** gte-modernbert-base, TripletLoss, 5 epochs, batch_size=16, grad_accum=2, bf16=True, lr=2e-5, L4 GPU

**Result:** Completed successfully in ~68 seconds.
- `val_cosine_accuracy`: 0.678 (67.8%)
- Eval trajectory: ~0.609 at epoch 2-3, improved to 0.678 by epoch 5
- `load_best_model_at_end=True` with `metric_for_best_model="val_cosine_accuracy"`

**Model download:**
```bash
modal volume get embedding-finetune-output gte_base_run4/ ./evidence/fine_tuning/embedding/gte_base_run4/
```

**Note:** Model weights (~600MB) are gitignored. Download from Modal volume on other machines.

### Evaluation: gte_base_run4 (2026-05-28)

Compared base (Alibaba-NLP/gte-modernbert-base) vs fine-tuned on Modal T4 GPU.
Eval script: `eval_modal.py`

**Triplet accuracy (87 held-out eval triplets):**

| Model | Accuracy | Correct | Mean margin |
|-------|----------|---------|-------------|
| Base (gte-modernbert-base) | 43.7% | 38/87 | -0.0173 |
| Fine-tuned (gte_base_run4) | **67.8%** | 59/87 | +0.0176 |
| Delta | **+24.1%** | +21 | +0.0349 |

Base model scores below random (50%) because the "hard negatives" in our dataset are KEEP cases that already had high embedding similarity — the base model naturally sees them as similar.

**Golden set similarity distributions (64 cases: 30 D, 34 K):**

| Metric | Base | Fine-tuned | Delta |
|--------|------|------------|-------|
| D mean similarity | 0.9055 | 0.9779 | +0.0724 |
| K mean similarity | 0.8777 | 0.9695 | +0.0918 |
| Gap (D-K means) | 0.0279 | 0.0084 | **-0.0195** |
| Overlap (K_max - D_min) | 0.1748 | 0.0815 | -0.0933 |

**Analysis: triplet accuracy improved but golden set gap worsened.**

The fine-tuned model learned to discriminate triplets (+24.1% accuracy), but did so by pushing all similarities toward 1.0 (~0.97 for both D and K), compressing everything into a narrow band. The gap between D and K means *decreased* from 2.79% to 0.84%, making threshold-based auto-dedup *harder*, not easier.

The overlap metric improved (0.1748 → 0.0815), but this is misleading — it reflects compression, not better separation.

**Conclusion: the fine-tuned embedding is not useful for dedup in its current form.**

**Root causes:**
1. **Random negative sampling** — `build_pairs.py` pairs each anchor with a random negative from the KEEP pool. Most random negatives are "easy" (obviously different), so the model optimizes for trivial discrimination and doesn't learn the fine-grained D/K boundary.
2. **Small dataset** — 861 triplets is limited for a 149M parameter model. The model overfits to the training distribution without generalizing.
3. **TripletLoss limitations** — TripletLoss with random negatives is known to converge to a collapsed representation. Hard negative mining or MultipleNegativesRankingLoss would force the model to learn finer distinctions.

**Potential improvements (if revisited):**
- Hard negative mining: pair each anchor with its *closest* non-duplicate instead of random
- MultipleNegativesRankingLoss or supervised contrastive loss
- More training data from additional games
- Curriculum learning: start with easy negatives, progressively add harder ones

---

## Round 2: Hard Negative Mining (2026-05-28)

### Why the first round failed: detailed analysis

Contrastive learning (TripletLoss) teaches the model: "make the anchor closer to the positive than to the negative." The quality of learning depends entirely on **how hard the negatives are**.

**Round 1 used random negatives.** For each anchor (a situation text from a D case), we paired it with a randomly-selected KEEP case's situation text. But most KEEP cases describe completely different game situations — they're "easy" negatives that the model can already distinguish without learning anything new.

Example of an easy triplet (random negative):
- Anchor: "As seer, confirmed villager role on Day 2"
- Positive (D case): "As seer, verified villager identity early in game" ← true duplicate
- Negative (random K): "As werewolf, voted to eliminate the doctor at night" ← obviously different

The model learns to separate these trivially (different roles, different actions, different phases), but this doesn't help with the hard cases like:
- "As villager, defended an accused player" vs "As villager, accused a suspicious player" ← same role/situation, opposite actions, but random sampling rarely pairs these

**The result was representation collapse.** Because most triplets were easy, the model found a shortcut: push all embeddings into a small region near 1.0 similarity. This trivially satisfies TripletLoss (margin already exceeded for easy cases) but destroys the fine-grained discrimination we need. On the golden set, both D and K cases ended up at ~0.97 similarity — the gap *shrank* from 2.79% to 0.84%.

### What hard negative mining changes

**Hard negative mining** replaces the random negative with the **closest** KEEP case for each anchor — the one the model is most likely to confuse with a true duplicate.

How it works:
1. Compute embeddings for all ~800 unique situation texts using the base model (gte-modernbert-base)
2. For each D case anchor, compute cosine similarity against ALL K case situations
3. Select the K case with the **highest similarity** as the negative — this is the "hardest" negative because the model currently thinks it's almost a duplicate, but the human label says it's not

Example of a hard triplet (mined negative):
- Anchor: "As seer, confirmed villager role on Day 2"
- Positive (D case): "As seer, verified villager identity early in game" ← true duplicate
- Negative (hardest K): "As seer, revealed werewolf identity on Day 2" ← same role, same phase, but critically different action

Now the model must learn that "confirmed villager" vs "revealed werewolf" is a meaningful distinction, even though the surrounding context is nearly identical. This is exactly the kind of discrimination the dedup system needs.

**Why we use the base model's own embeddings for mining:** We want to find negatives that are hard *for the model we're about to fine-tune*. Using the base model's similarity ensures we're targeting its specific blind spots. If we used a different model's embeddings, we might mine cases that are hard for that model but already easy for ours.

The same logic applies symmetrically for K cases: we find the closest D case as the "hard positive" — teaching the model what a true duplicate looks like even when the anchor is a KEEP case.

### Infrastructure note

The hard negative mining requires computing embeddings for all texts, which is a transformer forward pass. This ARM (aarch64) machine runs PyTorch transformer inference very slowly (no AVX-512 SIMD), so the mining computation runs on Modal T4 GPU where it takes seconds.

Script: `build_pairs_modal.py`
Output: `triplets_hard.jsonl` (same format and count as `triplets.jsonl`, but with mined negatives)

### Training run 5: gte_hard_run1 — TripletLoss with hard negatives (2026-05-28)

**Config:** gte-modernbert-base, TripletLoss, 5 epochs, batch_size=16, grad_accum=2, bf16=True, L4 GPU. Same as run 4 but using `triplets_hard.jsonl` (hard-mined negatives) instead of `triplets.jsonl` (random negatives).

**Result:** Training unstable. Gradient norms spiked to 100+, loss oscillated between 0.5-7.0, eval accuracy 49.4% (random-level). The hard negatives were *too* hard for TripletLoss — with a fixed margin, the model couldn't make progress on triplets where anchor-positive and anchor-negative similarities were within a few percent of each other.

**Conclusion:** TripletLoss is not the right loss function for this dataset. Hard negatives are necessary for learning, but TripletLoss's fixed margin doesn't adapt to the difficulty. Pivoting to CosineSimilarityLoss which learns continuous similarity scores rather than binary margin comparisons.

---

## Round 3: CosineSimilarityLoss (2026-05-28)

### Why CosineSimilarityLoss

TripletLoss teaches relative ordering (anchor closer to positive than negative by a fixed margin). CosineSimilarityLoss teaches absolute similarity targets: "these two texts should have similarity 1.0" (duplicates) or "these two should have similarity 0.0" (non-duplicates). This has two advantages for our dataset:

1. **No margin tuning** — the loss directly pushes similarities toward target values rather than enforcing a fixed gap
2. **Naturally handles hard cases** — the gradient is proportional to how far the current similarity is from the target, so hard cases (currently near 0.5) get stronger gradients than easy cases (already near the target)

### Dataset: pairs.jsonl

Converted from the same 861 labeled cases:
- D cases (389): `sentence1=anchor, sentence2=positive, label=1.0`
- K cases (472): `sentence1=anchor, sentence2=negative, label=0.0`

### Training run 6: gte_cosine_run1 (2026-05-28)

**Config:** gte-modernbert-base, CosineSimilarityLoss, 5 epochs, batch_size=16, grad_accum=2, bf16=True, lr=2e-5, L4 GPU

**Validation metric bug:** EmbeddingSimilarityEvaluator reports NaN for Pearson/Spearman during training. Root cause: the 90/10 split on pairs.jsonl (shuffled by triplets.jsonl's seed) put all 87 eval examples in the K class (label=0.0). Correlation is undefined when one variable is constant — SciPy emits `ConstantInputWarning` and returns NaN.

This is a validation-reporting bug, not a training failure. The model still trains on the full loss and checkpoints are saved. The `load_best_model_at_end` with `metric_for_best_model="val_spearman_cosine"` silently falls back to the last checkpoint (since all values are NaN, no "best" is found).

**Fix applied for future runs:** Stratified train/eval split (proportional D/K in both sets) and switched `metric_for_best_model` to `eval_loss` (lower is better).

**Eval results (gte_cosine_run1 vs base, from eval_modal.py):**

| Metric | Base | Fine-tuned (cosine) | Delta |
|--------|------|---------------------|-------|
| Triplet accuracy | 43.7% (38/87) | **65.5%** (57/87) | **+21.8%** |
| Mean margin | -0.0173 | +0.0967 | +0.1140 |

| Golden set metric | Base | Fine-tuned (cosine) | Delta |
|-------------------|------|---------------------|-------|
| D mean similarity | 0.9055 | — | — |
| K mean similarity | 0.8777 | — | — |
| Gap (D-K) | 0.0279 | 0.0435 | **+0.0157** |
| Overlap (K_max - D_min) | 0.1748 | 0.6233 | **+0.4485 (worse)** |

**Analysis:**

CosineSimilarityLoss improved over both the base model and TripletLoss run 4:
- Triplet accuracy: 43.7% → 65.5% (vs 67.8% for TripletLoss run 4 — comparable)
- Golden set gap: 0.0279 → 0.0435 (**improved**, vs 0.0084 for TripletLoss which was *worse* than base)
- Margin: the cosine model has a larger mean margin (+0.0967 vs +0.0176 for TripletLoss)

However, overlap worsened dramatically (0.1748 → 0.6233). This means the distributions are more spread out — some K cases have very high similarity and some D cases have very low similarity. The model learned to separate *on average* but individual outliers got worse.

**Interpretation:** The gap improvement (+0.0157) is the right direction but modest. The overlap degradation suggests the model is moving means apart but losing consistency on individual cases. This could be because:
1. The eval labels were all-negative (NaN metric), so `load_best_model_at_end` didn't select the true best checkpoint
2. 861 pairs is still small for a 149M model
3. The binary labels (0.0/1.0) may be too coarse — some K cases are borderline duplicates that should have soft labels

### Training run 7: gte_cosine_run2 — stratified split fix (2026-05-28)

**Config:** Same as run 6 but with stratified train/eval split and `metric_for_best_model="eval_loss"`.

**Eval results:**
- Triplet accuracy: 47.1% (41/87) — barely above base (43.7%), much worse than run 6 (65.5%)
- Golden set gap: 0.0796 (+0.0517 vs base) — best gap of any run
- Golden set overlap: 0.6829 — worst overlap of any run
- Similarity distributions collapsed to ~0.70 mean (vs base ~0.90)

The proper checkpoint selection didn't help — the model still spreads distributions rather than learning fine discrimination.

---

## Conclusion: Embedding Fine-Tuning (2026-05-28)

**All embedding fine-tuning approaches failed to improve auto-dedup performance.** Across 7 training runs with 3 loss functions (TripletLoss, CosineSimilarityLoss) and 3 negative mining strategies (random, hard, N/A):

| Run | Loss | Negatives | Triplet acc | Golden gap | Golden overlap |
|-----|------|-----------|-------------|------------|----------------|
| Base (no fine-tuning) | — | — | 43.7% | 0.0279 | 0.1748 |
| Run 4 (TripletLoss random) | Triplet | random | **67.8%** | 0.0084 ↓ | 0.0815 |
| Run 5 (TripletLoss hard) | Triplet | hard | 49.4% | — | — |
| Run 6 (Cosine run1) | Cosine | N/A | 65.5% | 0.0435 ↑ | 0.6233 ↑ |
| Run 7 (Cosine run2) | Cosine | N/A | 47.1% | **0.0796** ↑ | 0.6829 ↑ |

Every model improved either triplet accuracy or gap on average, but worsened overlap (individual case reliability). The models learned to move D/K means apart but destroyed calibration on outlier cases — exactly the behavior that makes auto-dedup thresholds unreliable.

**Root cause identified:** All training pairs used **situation text only**, but D/K labels were determined by comparing **all fields** (situation + action/approach/outcome). This creates contradictory training signal — cases with identical situations but different approaches are labeled K, while the model sees only the identical situations. ~19 K cases in the dataset have situation similarity > 0.88, making the signal inherently noisy for situation-only models.

This root cause was confirmed when pivoting to the cross-encoder experiments (see `evidence/fine_tuning/cross_encoder/experiment_log.md`), which tested full-field and field-matched text and found the same fundamental ceiling.

**Recommendation:** Embedding fine-tuning is not viable with the current dataset size (861 examples) for improving auto-dedup. The ~15-30% auto-rate ceiling identified in the prior embedding pre-filter calibration work (`evidence/dedup/embedding_prefilter/experiment_log.md`) is a fundamental limit of similarity-based approaches, not a model quality issue. Further embedding work should only be revisited with 3-5k+ labeled pairs.
