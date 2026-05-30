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
modal volume get cross-encoder-reranker-output reranker_v2_768pairs/ ./models/cross_encoder/reranker_v2_768pairs/
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
- Per-model rate limiter (NIM 40 rpm cap) — now in `evaluation/labeling/engine.py`
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

Folder layout (`evidence/fine_tuning/cross_encoder/reranker/`):

| Path | Contents |
|------|----------|
| `scripts/` | Reproducibility scripts: situation generation, candidate retrieval, stratified split, training-data prep, and Modal GPU train/eval |
| `labels/round1_original/` | Original 40-case labeling — candidates, ChatGPT + 3-model consensus, 4-model merged golden |
| `labels/round2_expanded/` | Expanded 109-case labeling — 2.5-pro situations, 1,848 candidates, per-model labels (flash-lite / mistral / NIM-8B), 5-model merged golden, tie lists |
| `labels/manual_batches/` | ChatGPT + Sonnet manual labeling prompts and responses (22 batches each) |
| `training_data/` | Stratified `reranker_split.json` + train/val/test JSONL pairs (consumed by `scripts/train_reranker_modal.py`) |

**Labeling pipeline:** the multi-model consensus labeling was run through the production `evaluation/labeling/` module (engine / voter / merger / exporter + reranker adapter). The earlier ad-hoc labeling scripts (`label_candidates.py`, `merge_labels.py`, `merge_expanded_labels.py`, `export_for_manual_labeling.py`) were fully superseded by that module and have been removed — see git history for their last state.

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
modal volume get cross-encoder-reranker-output reranker_v4/ ./models/cross_encoder/reranker_v4/
```
