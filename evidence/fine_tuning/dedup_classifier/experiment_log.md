# Fine-Tuning: Dedup Classifier

## Motivation

The per-extraction dedup pipeline classifies new memories against existing candidates as Discard (duplicate) or Keep (novel). Multiple rounds of prompt engineering reached an accuracy ceiling — the current best prompt (v11b) achieves 83% on the 65-case golden eval set with flash-3.5, 82% with flash-lite. The primary error mode is under-discarding: the model KEEPs entries it should DISCARD (9 false keeps vs 1 false discard on flash-3.5 v11b). These false keeps accumulate as store noise, relying on periodic batch dedup to clean up.

Fine-tuning targets this because it's a narrow, well-defined binary classification task where prompt engineering can bias toward a class but can't reshape decision boundaries. A fine-tuned model can learn class-specific features from labeled examples.

## Plan (2026-05-27)

### Approach
- Technique: QLoRA (4-bit quantized base + low-rank adapters)
- Base model candidates: Gemma 2 9B-IT or Llama 3.1 8B-Instruct
- Library: Unsloth + Hugging Face TRL (SFTTrainer)
- LoRA config: rank 8-16, alpha 16, target attention layers
- Infrastructure: Modal (per-second billing, no idle cost)
- Output format: classification + reasoning (label + 2-3 sentence rationale). Reasoning acts as chain-of-thought to improve accuracy and interpretability. No merge generation — keep it classification-only.

### Dataset strategy
- Primary source: `eval_sets/dedup_v2.jsonl` — 390 frozen per-extraction cases from 30 games, full input context (new entry + 5 candidates with similarity scores)
- Golden eval: `eval_sets/dedup_v2_golden_labels.json` — 65 human-labeled cases (D=30, K=34, M/K=1). Reserved as held-out test set.
- Additional source: Langfuse traces from recent batches (self-hosted, free). ~13 dedup decisions per game, 200+ recent games available.
- Target: 500-1000 labeled examples minimum
- Format: JSONL with input (memory pair context) and output (D/K label + reasoning)

### Evaluation plan
- Test set: 65 golden-labeled cases (held out from training)
- Metrics: per-class precision, recall, F1 (not just overall accuracy)
- Baseline: flash-3.5 v11b at 83% (21D correct, 33K correct, 9 false keeps, 1 false discard)
- Target: reduce false keeps without increasing false discards

### Estimated cost
- Compute: $5-15 (1-3 training runs x 1-2 hours each)
- Human time: 1-2 weeks including dataset creation

---

## Analysis: Data Inventory and Decision Scope (2026-05-27)

### Existing data audit

| Dataset | Count | Labels | Reliability |
|---------|-------|--------|-------------|
| `dedup_v2_golden_labels.json` | 65 cases | Human D/K | High — ground truth |
| `dedup_v2.jsonl` | 390 cases | Model A/B/C/D (old prompt) | Low — pre-tuning, old 4-option format |
| `dedup_v2_replay_*_v11b.jsonl` | 65 cases | Model D/K (current prompt) | Medium — 83% vs golden |
| `batch_dedup_golden_labels.json` | 152 items / 17 clusters | Human D/K/M | High — but cluster-level, not pair-level |
| `auto_dedup_v1*.jsonl` | 424 cases | Embedding threshold | N/A — auto decisions, no LLM label |
| Langfuse traces | ~4,225 estimated | Model decisions, various prompts | Mixed — depends on which batch/prompt |

### Key findings

**Data gap:** Only 65 human-labeled per-extraction cases exist — well short of the 500-1000 minimum. The 390 cases in `dedup_v2.jsonl` were generated with a pre-tuning 4-option prompt (A/B/C/D), making their decisions unreliable as training labels. Replays only cover the 65 golden-labeled cases.

**Infrastructure exists for scaling:** The `dedup_builder.py` pipeline can pull dedup decisions from Langfuse for any batch run. Per-extraction dedup spans are logged with full context (`_emit_dedup_span()` in `memory_deduplication.py`). Recent batches (v4_action_phase_v2: 53 games, werewolf_flashlite_3_v1: 61 games) should contain decisions made with current or near-current prompts.

**Labeling reliability:** v11b prompt achieves 83% agreement with golden labels. Using model decisions as training labels means ~17% noise — usable but benefits from co-labeling the uncertain cases.

**Error pattern on golden set (flash-3.5 v11b):**
- False Discard (predicted D, should be K): 1 case
- False Keep (predicted K, should be D): 9 cases
- The model under-discards — it's too conservative, keeping entries that are duplicates

**Flash-lite v11b shows similar but more balanced errors:**
- False Discard: 4 cases
- False Keep: 7 cases

### Decision: Binary D/K only (no Merge)

We considered three scope options:

1. **Binary D/K for per-extraction** — replace the real-time API call during gameplay
2. **Tri-class D/K/M for batch triage** — replace the flash-lite triage pass in two-pass batch dedup
3. **Both** — train on D/K first, extend to D/K/M later

We chose **option 1 (binary D/K only)** for the following reasons:

**Merge class imbalance is severe.** The golden labels contain only 2 Merge cases out of 65 per-extraction, and 14 out of 152 in batch labels. Training a three-class model with <5% Merge representation would produce a model that either ignores Merge entirely or overpredicts it. Synthetic augmentation could help but adds complexity and risk for a first fine-tune.

**Merge was already dropped from per-extraction by design.** The current pipeline deliberately classifies Merge cases as Keep during per-extraction, deferring true merge decisions to batch dedup where a more powerful model (2.5-pro) handles the merge with full cluster context. This is a sound architectural decision — merge requires seeing the full cluster, not just a pairwise comparison. Fine-tuning doesn't change this constraint.

**Binary is the right first fine-tune.** Simpler task, clearer evaluation, more data available. The per-extraction classifier runs in real-time during gameplay, so replacing it with a local fine-tuned model yields direct cost and latency savings. If this succeeds, extending to tri-class triage is primarily a dataset problem (accumulating enough M labels), not an architecture change.

### Next steps

1. ~~Re-replay full 390 cases through current v11b prompt~~ → replaced by extraction artifact approach (see below)
2. ~~Pull additional cases from Langfuse~~ → not needed, extraction artifacts provide sufficient volume
3. Build agreement merge script to align 3 model outputs, auto-label agreements, surface disagreements for manual review
4. Define input/output format for fine-tuning examples

---

## Dataset Generation Run (2026-05-27)

### Approach change: extraction artifacts instead of replay

Instead of re-replaying the 390 frozen cases or pulling from Langfuse, we generate fresh dedup cases by running existing extraction artifacts through the per-extraction dedup pipeline against the v4_deduped_v2 store. Advantages:
- No game re-runs needed — extractions already exist from model comparison experiments
- Wider variety of inputs (different extraction models produce different phrasings of the same game events)
- Store is not mutated (`_dedup_without_store_mutation` skips all store writes)
- No Langfuse dependency — results written directly to JSONL

Script: `evidence/fine_tuning/dedup_classifier/generate_dedup_cases.py`

### Extraction sources selected

Selected files based on extraction quality evaluation (see `evidence/extraction/quality/report.md`):

| Source | Quality (Avg) | Files | Games | Entries |
|--------|--------------|-------|-------|---------|
| gemini-3.5-flash (all: single + per-role) | 4.88-4.93 | 4 | 25 | 470 |
| gemini-2.5-pro (all: single + per-role) | 4.96 | 3 | 20 | 440 |
| gemini-3.1-flash-lite per-role (high + medium) | 4.13-4.57 | 2 | 10 | 308 |
| gemini-2.5-flash per-role | 4.43 | 1 | 5 | 194 |
| **Total** | | **10** | **60** | **1412** |

Note: all 60 "games" come from 10 unique game transcripts, extracted by different models. Flash-lite per-role included despite lower judge scores — the judge penalizes diversity/repetition which dedup handles downstream, and per-role coverage (5.00) captures situations single-pass misses. See extraction quality report Phase 4 analysis.

### Multi-model agreement labeling

Three models label the same 1412 entries in parallel. Cases where all 3 agree → auto-label. Disagreements → manual review.

| Model | Output file | Purpose |
|-------|-----------|---------|
| gemini-3.5-flash | `cases_flash35.jsonl` | Primary voter |
| gemini-3.1-flash-lite (thinking=low) | `cases_flashlite.jsonl` | Second voter |
| gemini-2.5-flash | `cases_flash25.jsonl` | Tiebreaker |

Estimated cost: ~$4-8 total across all 3 models.
Estimated wall time: 4-8 hours (running concurrently).

Started: 2026-05-27 10:30 UTC.

### Output format

Each JSONL record contains:
- `new_entry`: full composed situation + action/approach/outcome
- `candidates`: list with per-candidate cosine `similarity` score + full text fields
- `similarity_scores`: embedding prefilter detail (action_sim, content_sim breakdowns)
- `decision`: D or K
- `decision_detail`: model reasoning (for LLM-decided cases)
- `auto`: whether decided by embedding prefilter vs LLM
- `dedup_model`: which model made the decision

Only LLM-decided cases (~60% of total, ~847 estimated) are useful for training — auto decisions are trivial embedding threshold checks.


## Co-labeling Results (2026-05-27)

### Multi-model triage

Three flash models (gemini-3.5-flash, gemini-3.1-flash-lite, gemini-2.5-flash) labeled 863 LLM-decided cases from the extraction artifacts. Results split into unanimous agreement (619 cases) and disagreement (244 cases).

### Phase 1: Disagreement review (244 cases)

All 244 disagreement cases reviewed manually (claude + user). Each case examined against the dedup prompt criteria.

| Original majority | Final D | Final K | Flip rate |
|-------------------|---------|---------|-----------|
| Majority D (2-1)  | —       | —       | 37% flipped to K |
| Majority K (2-1)  | —       | —       | 7% flipped to D  |
| Total              | 97      | 147     | —         |

Key finding: **strong D-bias across all three triage models.** When models disagreed, majority-D was wrong 37% of the time vs majority-K only 7%. This motivated reviewing the unanimous-D cases rather than trusting them.

### Phase 2: Unanimous-D review (373 cases)

All 373 unanimous-D cases reviewed in a multi-pass approach:

**Strategy points (284 cases):**

| Pass | Cases | Flipped to K | Flip rate |
|------|-------|-------------|-----------|
| Pass 1: heuristic-flagged (opposing keywords) | 65 | 17 | 26.2% |
| Pass 2: unflagged, low similarity (<0.85) | 162 | 37 | 22.8% |
| Pass 3: unflagged, high similarity (≥0.85) | 57 | 6 | 10.5% |
| **Strategy total** | **284** | **60** | **21.1%** |

**Observation points (89 cases):**

| Pass | Cases | Flipped to K | Flip rate |
|------|-------|-------------|-----------|
| Full review | 89 | 20 | 22.5% |

**Combined:** 373 unanimous-D cases → 293 confirmed D, 80 flipped to K (21.4% false positive rate).

### Unanimous-K cases (246 cases)

Not reviewed. Given the D-bias pattern (models over-discard, not over-keep), unanimous K labels are expected to be reliable. Trusted as-is.

### Common false-D error patterns

1. **Opposite action directions** (strategy): models failed to distinguish "avoid suspicion" vs "lead discussion", "defend self" vs "accuse others"
2. **Different situations**: same candidate matched to entries from fundamentally different game states
3. **Opposite outcomes** (observation): "plan succeeded" vs "plan failed" treated as duplicates
4. **Different scope/approach**: similar situation but materially different tactical advice

### Co-labeling process findings

1. Using 3 models and labeling where they disagree is fast and efficient. Opus 4.6 high thinking is generally very good at deciding after reading the exact prompt instructions and after a few rounds of calibration. However, sometimes it truncates and summarizes text, evaluating on truncated versions and making sweeping statements. Mitigation: ask it to read full text and reason consistently.
2. Heuristic keyword flagging (opposing direction pairs) was effective for catching the most obvious errors (26% flip rate) but missed many subtler cases — unflagged low-similarity cases still had a 23% flip rate.
3. High-similarity cases (≥0.85) were the most reliable unanimous-D labels (only 10.5% false positive), confirming that embedding similarity correlates with true duplicates.
4. Observation dedup false positives (22.5%) were unexpectedly close to strategy (21.1%), despite observations having a stricter 3-field match requirement.

---

## Final Labeled Dataset Composition

| Source | Cases | D | K | Review method |
|--------|-------|---|---|---------------|
| Disagreement review | 244 | 97 | 147 | Manual (claude + user) |
| Unanimous-D review | 373 | 293 | 80 | Manual (claude + user) |
| Unanimous-K (trusted) | 246 | 0 | 246 | Auto (high confidence) |
| **Total** | **863** | **390** | **473** | — |

**Class balance: 45.2% D / 54.8% K** — well-balanced, no resampling needed.

All manual review decisions logged in `colabeling_log.jsonl` (617 records with label, reasoning, review_pass).

---

## SFT Dataset Construction (2026-05-28)

### Difficulty tiering

Enriched all 863 labeled cases with difficulty scores (1-5):
- **Tier 1** (hardest): unanimous-D flipped to K — all 3 models were wrong
- **Tier 2**: disagreement cases where majority was wrong (37% of majority-D, 7% of majority-K)
- **Tier 3**: disagreement cases where majority was right
- **Tier 4**: unanimous-D confirmed
- **Tier 5** (easiest): unanimous-K (trusted without review)

139 cases in tiers 1-2 (the hardest cases), oversampled 3x during training.

### Reasoning generation

SFT requires model responses with reasoning, not just D/K labels. Reasoning sourced from:

| Source | Cases | Description |
|--------|-------|-------------|
| flash-3.5 replay reasoning (label-matched) | 454 | Existing replay where model agreed with final label |
| Detailed co-labeling reasoning | 82 | Rich reasoning from disagreement review |
| Generated reasoning (flash-lite medium thinking) | 81 | Hard cases with only terse labels |
| Unanimous-K flash-3.5 reasoning | 246 | flash-3.5 replay reasoning for unreviewed cases |
| **Total** | **863** | — |

The 81 generated-reasoning cases were the hardest (unanimous-D flips and disagreements with terse labels). Used `gemini-3.1-flash-lite` with `thinking_level="medium"` to generate reasoning given the prompt, case data, and correct label.

### SFT dataset format

Final dataset: `sft_dataset.jsonl` (863 examples)
- Format: `{"messages": [{"role": "user", "content": "<full dedup prompt>"}, {"role": "assistant", "content": "DECISION: D/K\nREASONING: ..."}], "metadata": {...}}`
- Stats: 392 D / 471 K, 609 strategy_point / 254 observation
- Token length: ~3.3K avg per example, ~2.9M total tokens

Script: `build_sft_dataset.py` (two modes: `--generate-reasoning` and `--build`)

---

## Training (2026-05-28)

### Infrastructure: Modal

Using Modal for serverless GPU compute — per-second billing, no idle cost. Training scripts upload data and run remotely.

Setup: `modal token set`, `modal secret create huggingface HF_TOKEN=hf_xxx`

### Model selection

Chose smaller models than originally planned (9B was overkill for binary classification):
- **Qwen/Qwen2.5-1.5B-Instruct** — primary candidate
- **Qwen/Qwen2.5-3B-Instruct** — if 1.5B underperforms

### Training run 1: qwen1b_run1, attempt 1 (2026-05-28)

**Config:** Qwen 2.5 1.5B, QLoRA rank=16, 3 epochs, batch_size=2, grad_accum=4, lr=2e-4, L4 GPU (24GB)

**Issues encountered during setup:**
1. **Unsloth dependency** — original plan used Unsloth for 2x faster training. Modal container image failed because Unsloth installs from git and the container had no git. Switched to plain transformers/peft.
2. **TRL API change** — `SFTTrainer(tokenizer=...)` renamed to `SFTTrainer(processing_class=...)` in newer TRL.
3. **OOM on T4** — first attempted T4 (16GB) with batch_size=2, max_seq_length=4096. CUDA OOM. Switching to batch_size=1, grad_accum=8 was too slow (~14 hours, 122s/step). Upgraded to L4 (24GB), restored batch_size=2 — ~19s/step, ~2.3 hours total.

**Progress:** Reached step 142/429 (~33%, end of epoch 1). Loss 0.42, token accuracy 88.6%. Saved checkpoint-143.

**Interrupted:** The `modal run` process was running as a background task in the Claude Code session. When the conversation ran out of context and was compacted, the background process was terminated, which killed the Modal ephemeral app. Checkpoint-143 was saved to the Modal volume but the training did not complete.

### Training run 1: qwen1b_run1, attempt 2 (2026-05-28)

Added two fixes to prevent wasted work:
1. **Checkpoint resumption** — script now detects existing checkpoints in the output directory and passes `resume_from_checkpoint` to `trainer.train()`
2. **VolumeCommitCallback** — commits the Modal volume after each epoch checkpoint save, ensuring partial progress survives interruptions

Re-launched from user's terminal (not Claude Code session) to avoid the session-lifetime problem. Resumed from checkpoint-143 (end of epoch 1).

**Training completed:** 429 steps (3 epochs), final loss 0.0845, token accuracy 93.6%. LoRA adapter saved to Modal volume at `/output/qwen1b_run1/lora_adapter`.

Script: `train_modal.py` (L4 GPU, QLoRA, SFTTrainer)
Eval script: `eval_modal.py` (loads LoRA adapter, runs inference on 65 golden cases)

---

## Evaluation: qwen1b_run1 (2026-05-28)

Ran inference on 65 golden eval cases using T4 GPU on Modal. The model generates `DECISION: D/K` + `REASONING: ...` in the same format as the training data.

### Results

| Metric | Qwen 1.5B QLoRA | Flash-3.5 v11b (baseline) |
|--------|-----------------|---------------------------|
| **Accuracy** | **43.1%** (28/65) | **83.1%** (54/65) |
| D precision | 0.39 | 0.95 |
| D recall | 0.40 | 0.70 |
| K precision | 0.45 | 0.79 |
| K recall | 0.44 | 0.97 |

**Confusion matrix (qwen1b_run1):**

|  | pred D | pred K |
|--|--------|--------|
| gold D (30) | 12 | **18** |
| gold K (34) | **19** | 15 |

Decision distribution: 31 D, 34 K — roughly balanced, so the model isn't degenerate, just wrong.

### Analysis: systematic underfitting, not random

At first glance, 43% accuracy looks random. Per-type breakdown reveals it's not — the model learned a **per-type class prior shortcut**:

**Strategy points (25 golden cases):**

|  | pred D | pred K |
|--|--------|--------|
| gold D (10) | **10** | 0 |
| gold K (15) | **15** | 0 |

The model predicts D for *every* strategy point. It gets all 10 true-D correct by default but misclassifies all 15 K cases.

**Observations (40 golden cases):**

|  | pred D | pred K |
|--|--------|--------|
| gold D (20) | 2 | **18** |
| gold K (19+1 M/K) | 4 | **15** |

The model predicts K for almost every observation (33/40). It barely discriminates.

**Root cause:** The model found the cheapest shortcut available — predict based on item type, not text content. This is classic underfitting: the model doesn't have enough capacity (or the right training signal) to learn the actual decision boundary, so it defaults to the strongest statistical prior.

### Why training metrics were misleading

93.6% token accuracy = the model learned to reproduce the output *format* (`DECISION: D/K\nREASONING: ...`). The D/K decision is 1 token out of ~200 in the assistant response, so ~99.5% of the loss gradient teaches format reproduction. The model can achieve high token accuracy by perfectly copying reasoning structure while getting every decision wrong.

### Problem 1: Diluted training signal

The SFT loss is averaged across all output tokens equally. The D/K decision token gets the same weight as every formatting and reasoning token. This means:
- ~0.5% of gradient signal teaches the actual classification
- ~99.5% of gradient signal teaches the model to reproduce flash-3.5's reasoning style
- The model optimizes for the easy 99.5% and treats the decision token as noise

### Problem 2: Dataset imbalance

The training set has two imbalances that enable the per-type shortcut:

| | D | K | Ratio |
|---|---|---|---|
| Strategy points | 261 | 348 | 33:67 |
| Observations | 129 | 125 | 42:58 |
| **SP:Obs overall** | **609** | **254** | **72:28** |

After 3x oversampling of hard cases (difficulty 1-2):

| | D | K | Ratio |
|---|---|---|---|
| Strategy points | 269 | 548 | 33:67 |
| Observations | 135 | 189 | 42:58 |

SP outnumbers observations 2.5:1, and within SP, K heavily outnumbers D. A model that learns "SP → D" and "Obs → K" (or any type-based shortcut) gets rewarded without reading the text.

### Problem 3: Label quality

| Source | Cases | Review | Estimated noise |
|--------|-------|--------|----------------|
| Co-labeled (human reviewed) | 617 | Manual | Low |
| Unanimous-K (3 models agreed) | 246 | None | Unknown — all 3 models agreed, but the D-bias pattern (21% false-D on unanimous-D) suggests unanimous-K labels are more reliable than unanimous-D |

26.4% of co-labeled cases overrode flash-3.5's judgment, meaning the training data has substantial correction from the baseline model. The 246 unanimous-K cases were not human-reviewed — if 5-10% are noisy, that's 12-25 incorrect labels.

---

## Reopened: Diagnostic Plan (2026-05-28)

The 1.5B result is ambiguous: is the underfitting caused by **model size** or **data/training issues**? Three problems identified — diluted signal, dataset imbalance, and the per-type shortcut opportunity. Increasing model size alone won't fix these if the training setup enables shortcuts.

### Fix attempted: Weighted decision loss

Instead of equal loss across all tokens, upweight the decision token so the model is forced to optimize for D/K accuracy:

- Reasoning tokens: weight 1.0 (still contribute gradient for training stability and output structure)
- Decision token (D/K): weight 100x (~33% of total loss vs ~0.5% unweighted)

Rationale: keep the benefits of chain-of-thought supervision (reasoning tokens guide internal representations) while making the decision token the primary optimization target. Pure decision-only training (stripping reasoning entirely) would give only ~1000 tokens of total supervision — too thin for stable training.

### Training run 2: qwen3_4b_run1 (2026-05-28)

Ran Qwen3-4B-Instruct-2507 on the original dataset (with reasoning, no weighted loss) as a baseline before applying fixes. This tests whether model capacity alone resolves the shortcut pattern.

**Config:** Qwen/Qwen3-4B-Instruct-2507, QLoRA rank=16, 3 epochs, batch_size=2, grad_accum=4, lr=2e-4, L4 GPU. Added `enable_thinking=False` for Qwen3 chat template compatibility.

**Status:** Stopped early — training was ~6 hours (429 steps at ~49s/step). At step 30/429 (epoch 0.07), token accuracy was 49.7% (expected to climb to ~94% as model learns format). Stopped to prepare weighted loss instead of waiting for a likely-shortcutting run to finish.

### Training run 3: qwen1b_weighted100x (2026-05-28)

**Purpose:** Isolate whether the diluted loss signal was the problem. Same 1.5B model that failed at 43%, but with 100x decision token weight.

**Config:** Qwen/Qwen2.5-1.5B-Instruct, QLoRA rank=16, 3 epochs, batch_size=2, grad_accum=4, lr=2e-4, L4 GPU, `--decision-weight 100`.

**Training metrics:** Final loss 1.91 (vs 0.08 unweighted). The high loss is expected — the 100x weight heavily penalizes wrong D/K predictions. Training completed in ~2.5 hours (429 steps at ~20s/step).

**Results: 46.2% accuracy (30/65)**

| | Unweighted 1.5B (run 1) | Weighted 100x 1.5B (run 3) |
|---|---|---|
| **Overall** | 43.1% | 46.2% |
| SP accuracy | 40.0% | 40.0% |
| Obs accuracy | 45.0% | 50.0% |

**Per-type confusion matrix:**

Strategy points (25 cases):
```
         pred_D  pred_K
gold_D       10       0   (n=10)
gold_K       15       0   (n=15)
```

Observations (40 cases):
```
         pred_D  pred_K
gold_D        0      20   (n=20)
gold_K        0      20   (n=20)
```

**The weighted loss hardened the shortcut instead of fixing it.** The model now predicts D for every SP and K for every observation with zero exceptions. The unweighted run at least had a few cross-predictions (2 D predictions for observations). Upweighting the decision token just made the model more confident in the per-type prior.

**Conclusion:** The 1.5B model's failure is **not a diluted loss signal problem**. The model genuinely cannot learn within-type D/K discrimination from this dataset at 1.5B parameters. The per-type class prior is the best feature it can extract regardless of how the loss is weighted.

### Training run 4: qwen3_4b_weighted100x (2026-05-28)

**Purpose:** Test whether 4B model capacity resolves the shortcut. The 1.5B weighted result eliminates loss signal as the variable — if 4B also shortcuts, it's a data problem (volume or balance).

**Config:** Qwen/Qwen3-4B-Instruct-2507, QLoRA rank=16, 3 epochs, batch_size=2, grad_accum=4, lr=2e-4, L4 GPU, `--decision-weight 100`.

**Status:** Training interrupted mid-run due to CPU overload. Relaunched with checkpoint resumption. ~5.5 hours estimated total.

**What to look for at eval:**
1. Per-type confusion matrix: does the model predict both D and K within each item type?
2. If yes → model capacity was the bottleneck; consider scaling to 7-8B for better accuracy
3. If no (same per-type shortcut) → the task cannot be learned from 863 examples at any reasonable model size; need more data or different approach

**Decision after this run:**
- If 4B discriminates within types → promising, consider rebalancing data and/or more labeled examples
- If 4B still shortcuts → **stop the classifier fine-tuning track**. The remaining 70-80% of dedup decisions stay as LLM API calls

---

## Future: Dataset Expansion

The current 863 examples have two issues for scaling: type imbalance (72% SP / 28% Obs) and all labels came from 3 Gemini models that share a systematic D-bias. Expanding the dataset addresses both the classifier and cross-encoder.

### How much more data

| Target | Total | New needed | New Obs needed | New SP needed |
|--------|-------|-----------|----------------|---------------|
| Current | 863 | — | — | — |
| 2,000 (balanced) | 2,000 | ~1,140 | ~750 | ~390 |
| 3,000 (balanced) | 3,000 | ~2,140 | ~1,250 | ~890 |

~2,000 balanced examples is the minimum for meaningful improvement — roughly 2.3x current size, with most growth in observations to fix the 72:28 imbalance.

### Labeling reliability from round 1

The 3-Gemini triage showed a strong D-bias that makes auto-labeling asymmetric:

| Agreement type | Error rate | Auto-label? |
|----------------|-----------|-------------|
| Unanimous K (3/3 K) | ~5% est. | Yes — models don't over-keep |
| Majority K (2/3 K) | 6.9% | Yes — still reliable |
| Majority D (2/3 D) | **36.6%** | No — must review |
| Unanimous D (3/3 D) | **21.4%** | No — must review |

**Efficient pipeline:** auto-label all K-majority cases, manually review only D-majority cases. This cuts manual effort to ~40-60% of new cases.

### Diversifying the triage panel

Using 3 Gemini models introduced correlated D-bias — they share similar failure modes. For the next labeling round, use models from different families to get more independent votes:

- 1 Gemini model (flash-3.5 or flash-lite)
- 1 OpenAI model (GPT-4o-mini or similar)
- 1 open-source model (e.g. Qwen or Llama via Together AI)

More independent voters → unanimous agreement is more meaningful → can auto-label more cases confidently.

### Expanding the golden test set

The current golden eval set (65 cases) is small. Reserving ~100-150 of the new labeled cases as additional test data would give more reliable eval metrics, especially per-type breakdowns (currently only 25 SP and 40 Obs test cases).

## Artifacts

| File | Description |
|------|-------------|
| `generate_dedup_cases.py` | Generates dedup cases from extraction artifacts |
| `build_sft_dataset.py` | Builds SFT training dataset with reasoning |
| `train_modal.py` | QLoRA training on Modal (L4 GPU) |
| `eval_modal.py` | Golden set evaluation on Modal (T4 GPU) |
| `sft_dataset.jsonl` | 863 training examples |
| `agreed_labels.jsonl` | Unanimously agreed labels from 3-model triage |
| `disagreed_labels.jsonl` | Disagreement cases from 3-model triage |
| `colabeling_log.jsonl` | Manual review decisions (617 records) |

Model weights stored on Modal volume `dedup-finetune-output`. Download:
```bash
modal volume get dedup-finetune-output qwen1b_run1/ ./local_dedup_classifier/
```