# Fine-tuning: small trained models for dedup and retrieval

> **Write-up: clauses only, not a page. Skim, no detailed read needed.** Triage cards 2–7 keep
> fine-tuning out of the main story: the reranker is kept as interview notes only; three findings go in as
> clauses (the prefilter's opposite-advice example and the embedding gap in block 26, the labeller-agreement
> bias in golden-set construction); dialogue distillation and the selection bandit are skipped
> ([triage](../../writeup/_planning/triage.md)).

This page records four attempts to train small models that could take over two jobs in the memory
pipeline: ranking retrieved memories for a turn, and deciding whether a new lesson duplicates one already
stored. Each section gives the question, how the model was trained and tested, what it achieved, the call
made, and what would change that call. All four ran between 27 and 31 May 2026, on the four-role game of
that time (wolf, villager, healer, investigator) and the memory store built from it. The run-by-run detail
is in each track's experiment log, linked from its section; labelling quality has its own record in
[the context-eval log](../evaluation/labeling/context_eval/experiment_log.md).

## Results and deployment status

- **Question.** Can small fine-tuned models, cheap enough to run on a CPU, replace the model calls the
  memory pipeline makes to rank retrieved memories and to judge duplicates?
- **Tests.** Four tracks, with task-specific evaluation sets: a retrieval
  reranker (17 test turns, 319 labelled pairs); a duplicate prefilter (65 hand-labelled duplicate cases,
  25 of them strategy points); a duplicate classifier (the same 65 cases); an embedding fine-tune (87
  held-out triplets and 64 of the hand-labelled cases).
- **Answer.** The reranker scored similarly to the LLM reranker it was built to replace (NDCG@5 0.882 against 0.871,
  intervals overlapping) at no API cost, and an input/label mismatch diagnostic found a small effect in the checks run.
  The prefilter decided 6 of 25 strategy-point cases alone without error, against 4 of 25 for the
  embedding check, too few cases to act on. The classifier reached 65–69% against the LLM's 83–85%. No
  embedding run improved duplicate separation.
- **What followed.** The classifier and embedding tracks were closed. Both cross-encoders were trained and
  benchmarked, then held: neither is loaded by the game or the server today. The prefilter is still a
  cosine check, the duplicate decision an LLM call, and reranking (off by default) an LLM call.

## Words used here

- **Strategy point:** a stored lesson, written as a situation and a recommended action. **Observation:**
  a stored record of one past move, written as situation, approach and outcome.
- **Bi-encoder (embedding) similarity:** each text is turned into a vector separately and the two are
  compared by cosine similarity, a score ranging from −1 to 1. It is how the store finds candidates.
- **Cross-encoder:** a small model that reads the two texts together and gives one score for the pair.
  It is slower per pair than cosine but sees how the texts relate. Both cross-encoders here are
  MiniLM-L6, a 22-million-parameter model.
- **Dedup:** deciding whether a new lesson duplicates a stored one (**discard**) or is new (**keep**).
  The **prefilter** is the cheap first step that settles obvious cases by similarity alone; only the
  uncertain middle goes to an LLM.
- **NDCG@5:** how well a ranking puts the most relevant memories in its top five, scored against graded
  labels; 1.0 is the ideal order.
- **The May store:** the memory store the cases were drawn from (named `v4_deduped_v2` in the logs).

## The four tracks at a glance

| Track | It would replace | Held-out test | Result | State |
|---|---|---|---|---|
| Retrieval reranker | The LLM reranker (one flash-lite call per turn) | 17 turns, 319 pairs | NDCG@5 0.882; LLM 0.871; embedding order 0.767 | Trained, benchmarked, not wired |
| Dedup prefilter | The cosine cut-offs that settle obvious duplicates | 65 cases (25 strategy points, 40 observations) | Strategy points: 6 of 25 settled without error, against 4; observations: 4 of 40, against 5 | Trained, benchmarked, held |
| Dedup classifier | The LLM keep-or-discard call | 65 cases | 4B model 65–69%; LLM 83–85% | Closed |
| Embedding fine-tune | The embedding model behind the prefilter | 87 triplets; 64 cases | No run widened the duplicate/non-duplicate separation without breaking individual cases | Closed |

The reranker comes first because it produced the most promising task result. The test did not establish equivalence to the LLM or a benefit in play.

**Authorship.** The owner built the labelled datasets; AI coding agents wrote the training code (owner ruling, 2026-10-21). This is a record of dataset work, experiments and deployment decisions. It does not establish personal implementation of the training stack.

## The retrieval reranker

**Question.** After the store returns the ten memories most similar to the turn's situation, an LLM
re-orders them and the top three are shown to the player. Can a cross-encoder rank as well as that LLM
call, without the call? **On 17 held-out turns it scored similarly; equivalence was not established.**

**Setup.** A case is one turn: the situation query written for it, and the top ten observations and top
ten strategy points the May store returned. Each (query, memory) pair was graded 0 (irrelevant), 1
(partly relevant) or 2 (relevant), mapped to training targets 0, 0.25 and 1.0. The data grew in three
rounds, and each model was trained on the next:

| Model | Cases | Training pairs | Scored on | NDCG@5 |
|---|---|---|---|---|
| v1 | 20 | 327 | 4 validation cases | 0.777 |
| v2 (also called v3) | 40 | 579 | 8 validation cases | 0.803 |
| v4 | 108 | 1,277 | 17 validation cases | 0.862 |

Each row is scored on a different set of cases, so the climb shows direction only. On the four cases v1
and v2 shared, both scored 0.777: doubling the data from 20 to 40 cases did not change the ranking there,
so a third round labelled 109 more turns, of which 68 entered the final set (the log does not say why
the other 41 were left out). The final set held 108 cases and 1,919 labelled pairs,
split by case (so no query appears in two splits) and stratified by role and phase into 74 training, 17
validation and 17 test cases (1,277, 323 and 319 pairs); games were not held out, and every test game also
supplied training turns. Training ran on a rented GPU (Modal, one L4) for
20 epochs.

**Result.** On the 17 held-out test cases, v4 scored slightly above the LLM reranker and above the
embedding order it starts from:

| Ranker | NDCG@5 | 95% interval |
|---|---|---|
| Embedding order (no reranking) | 0.767 | 0.697–0.837 |
| LLM reranker (flash-lite) | 0.871 | 0.800–0.932 |
| Cross-encoder v4 | 0.882 | 0.822–0.938 |

The 0.011 lead over the LLM is far inside both intervals, but overlapping individual intervals do not establish equivalence. No paired comparison or equivalence test was recorded. Observations ranked
better than strategy points (0.937 against 0.841, 17 cases each). The weakest cells were the
investigator's strategy points (0.629, 3 cases) and the healer overall (0.751, 4 cases), the roles with
the fewest training cases. A model five times larger (BGE-base, 110 million parameters) trained on the
same data scored 0.839 (0.768–0.907): its validation loss bottomed at epoch 5 and rose after, consistent with overfitting on 1,277 pairs.

**The input/label mismatch diagnosis.** The labellers saw a strategy point in full, situation and action, and were
asked whether recalling it "would help decide what to do". The reranker scores a strategy point by its
situation alone. If the labels rewarded good actions, the model was being trained toward something it
cannot see. This is an input/target mismatch, distinct from train/test data leakage. Two checks investigated it:

1. **Show the model the action.** Two models were trained identically except that one also saw the
   action. Strategy-point NDCG@5 moved from 0.846 to 0.860 (+0.015), with intervals overlapping
   (0.770–0.917 against 0.782–0.929). Observations, unchanged between the two, stayed level (0.937 and
   0.931), consistent with the effect being concentrated in the changed strategy-point input. The small difference did not establish a ranking gain.
2. **Hide the action from the labellers.** The three automated labellers re-graded 240 sampled
   strategy-point pairs twice, with and without the action. Flash-lite changed 0 of 240 labels, Mistral
   11 of 240 (4.6%), Llama 8B 0 of 160 (its other 80 answers did not parse). No change leaned one way.

A third test, on observations, checked the opposite case: stripping an observation to its situation cost
0.026 NDCG@3 (0.928 to 0.902) at the top three the player is shown, with strategy points as a level
control. Observation content is a description of what happened, which the model and the labellers both
saw, so it was kept as matching signal, not counted as a leak.

The call: strategy points stay scored on their situation, observations on their full text, and the
labels were not redone.

**What it would cost to run.** The ONNX benchmark (the model exported to a runtime that drops PyTorch)
was run on the dedup cross-encoder below, which is the same MiniLM-L6 architecture; the reranker itself
was not benchmarked separately. On one CPU core:

| Runtime | Per pair | Memory |
|---|---|---|
| PyTorch, default threads | ~17 ms, using 300% CPU | 900 MB |
| PyTorch, one thread | ~26 ms | 900 MB |
| ONNX, one thread | 16.6 ms, at 89% of one core | 90 MB |

The weights are 87 MB. The reranker log records a further problem on the development machine: local
PyTorch inference, even single-threaded, made the machine unstable, and it names ONNX or a serverless host
as the way to production. The reranker log's own cost table puts the LLM reranker at about 125 ms per
pair and $0.001 per turn.

**How sure we are.**
- *What it rests on:* one test set of 17 turns from 6 games, each of which also supplied training turns (the split held out turns, not games). Per-role figures rest on 3 to 6 turns
  each. No paired test between the cross-encoder and the LLM was recorded.
- *The labels over-credit.* A later check found the merged labels call a memory relevant, where the two
  careful labellers (ChatGPT and Claude Sonnet, which saw full game context) did not, on 514 of 1,848
  round-three items, mostly where three generous automated voters outvoted them (see
  [Where the labels came from](#where-the-labels-came-from)). Re-scoring v4's fixed ranking against the
  careful labellers' grades: observations dropped 0.905 → 0.845 on the 13 test cases that had those
  grades (drop 0.059, interval 0.001–0.118), and by 0.087 (0.022–0.151) with the validation cases added
  (25 cases; the validation cases were used to pick the model, so the true drop is likely nearer 0.06).
  Strategy points did not drop reliably: 0.851 → 0.810 (13 cases, interval −0.031 to +0.113), 0.030 with
  validation (24 cases, −0.017 to +0.077). Under the strict grades v4 still ranked observations 0.108
  above the embedding order (13 cases). The LLM reranker was not re-scored on the strict grades, so the
  level result above is on the merged labels only.
- *The residual in the leak test:* the two careful labellers were not re-tested without the action. The
  strict-grade re-score above used their action-visible grades and strategy-point ranking held (the context-eval log reads this as making the residual moot for ranking), but no action-hidden grades from those two labellers exist, so whether hiding the action would change their grades is untested.
- *Not checked:* any game played with the cross-encoder ranking, and any store after the May store. Today
  a served game retrieves strategy points only, from a different, ten-seat store.

**What would change the call.** A retrain and re-test on today's store, with the careful labellers'
grades, and a reason to rerank in served games, where reranking is off. A relabel and retrain on the
careful labellers' grades was designed on 31 May 2026, approved on 1 June, and deferred the same day,
because the game and the store it would have labelled were about to be rebuilt.

Detail: [reranker log](cross_encoder/reranker/experiment_log.md).

## The dedup prefilter cross-encoder

**Question.** The prefilter settles a new lesson without an LLM when its similarity to the nearest stored
one is very high (discard) or low enough (keep). Can a cross-encoder settle more cases this way, with no
mistakes, than cosine similarity does? **Answer: for strategy points, a little, on too few cases to act
on; for observations, no.**

**Setup.** The model was trained on 861 labelled duplicate decisions (389 discard, 472 keep) taken from
the classifier's dataset below, split 90/10, with each text formatted exactly as the prefilter reads it:
the action alone for a strategy point, situation, approach and outcome joined for an observation. On its
own validation split it scored 78.2% accuracy (average precision 84.0%, F1 0.756). It was then tested on
the 65 hand-labelled cases of the dedup golden set, drawn from 24 games that share no game with the 10
behind the training data (checked by game ID and entry text). For each method, cut-offs were searched for
the widest band of cases it could decide alone with zero errors.

**Result.** The cross-encoder settled more strategy points without error and fewer observations:

| Cases settled alone with no error | Cosine similarity | Cross-encoder |
|---|---|---|
| Strategy points (25: 10 discard, 15 keep) | 4 (4 discards) | 6 (1 discard, 5 keeps) |
| Observations (40: 20 discard, 20 keep) | 5 (4 discards, 1 keep) | 4 (3 discards, 1 keep) |

Allowing one error, cosine settled 7 strategy points and 14 observations, the cross-encoder 8 and 9. The
two methods were good at opposite halves: the cross-encoder found keeps, cosine found discards, so the
plan was a hybrid, the cross-encoder for strategy-point keeps and cosine for discards. The log also
reports the gap between average discard and keep scores (2.106 for the cross-encoder, 0.035 for cosine),
but the two are on different scales (the cross-encoder's score is unbounded, cosine's lies between −1 and
1), so that gap does not compare them.

Both methods failed on the same kind of case: same topic, opposite advice. The cross-encoder's most
confident wrong discard paired "immediately and aggressively lead the accusation against the wolf" with
"avoid taking a strong leadership role or making a direct accusation". Telling opposite advice from the
same advice phrased the other way round needs a reading of what the text means.

A model five times larger (BGE-base, 110 million parameters) overfitted the 861 pairs (average precision
peaked at 0.798 in epoch 5, then fell) and found no zero-error cut-off for either type.

The ONNX benchmark in the reranker section was run on this model: 16.6 ms per pair on one core, 90 MB of
memory. The log estimates about 750 ms a game from 15 dedup calls of 3 pairs each (about 50 ms a call). It
gives no source for either count; the dedup code of the time compared each new lesson with up to 5 stored ones.

**How sure we are.**
- *Sample size:* the strategy-point gain is 2 cases out of 25, and the intervals around 24% and 16%
  overlap heavily. The log estimates 100 or more strategy-point cases are needed to detect a gain of that
  size.
- *Tuned on the test set:* the zero-error cut-offs for both methods were searched on the same 25 cases
  they are reported on, so both rates are best-case figures. No held-out split existed.
- *No fresh data:* only 38 games had been labelled for dedup and 34 were already used, leaving about 22
  fresh strategy-point cases from 4 games. About 25 new games would be needed.

**The call.** Deployment held until the test is rigorous: a larger golden set from new games, split half
for tuning cut-offs and half for testing, with discard and keep rates reported separately. That re-test
was never run, and the cross-encoder is not wired in (see [Deployment status](#deployment-status)).

**What would change it.** A strategy-point gain that survives on 100 or more held-out cases drawn from
today's store.

Detail: [prefilter log](cross_encoder/dedup_prefilter/experiment_log.md); the cosine calibration it
compares against is in [the embedding prefilter log](../dedup/embedding_prefilter/experiment_log.md).

## The dedup classifier

**Question.** The uncertain middle band of duplicate decisions goes to an LLM, which answers keep or
discard. Prompt work had reached 83% agreement with the hand labels and its errors leaned one way (on
flash-3.5: 9 duplicates kept against 1 new lesson discarded). Can a small open model, fine-tuned on
labelled decisions, make that call instead? **These runs did not reach the LLM baseline: the best checkpoints scored 65–69% against 83–85%.**

**Setup.** No training set existed: only the 65 golden cases had hand labels, and they were kept for
testing. A training set was built from 1,412 lessons that several models had extracted from 10 game
transcripts, run through the dedup step against the May store without changing it. Three Gemini models
labelled the 863 cases that reached the LLM step:

- **Where they disagreed (244 cases),** every case was reviewed by hand (Claude and the owner). When two
  of three had said discard, the review overturned them 37% of the time; when two had said keep, 7%.
- **Because of that lean toward discard,** the 373 cases all three called a duplicate were reviewed too:
  80 (21.4%) were not duplicates.
- **The 246 cases all three called new** were trusted without review.

The result was 863 cases, 390 discard and 473 keep. Each training example asked the dedup prompt and
answered with the decision and two or three sentences of reasoning; the 139 hardest cases were shown
three times. Models were fine-tuned with QLoRA (a compact adapter trained on a 4-bit copy of the model)
for 3 epochs on one L4 GPU.

**Result.** The 1.5-billion-parameter model learned a shortcut; the 4-billion model read the text but
missed most duplicates:

| Model (65 golden cases) | Accuracy | Duplicates found | New lessons kept |
|---|---|---|---|
| Qwen2.5 1.5B | 43.1% (28) | 40% | 44% |
| Qwen2.5 1.5B, decision weighted 100× | 46.2% (30) | — | — |
| Qwen3 4B, decision weighted 100×, after epoch 1 | 69.2% | 40% | 94% |
| Qwen3 4B, same run, after epoch 2 | 64.6% | 27% | 97% |
| LLM: flash-lite, tuned prompt | 83.1% | 77% | 88% |
| LLM: flash-3.5, tuned prompt | 84.6% | 70% | 97% |

The 1.5B model called every strategy point a duplicate and almost every observation new (33 of 40): it
had learned the item's type, not its text. Its training accuracy of 93.6% hid this, because that figure
counts every output token, and the decision is one token in about 200 of reasoning. Weighting the
decision token 100 times tested whether that dilution was the cause; the shortcut became total (every
strategy point discard, every observation keep), so this change did not remedy the shortcut; it does not isolate its cause. The 4B model, on the same weighted
setup, made real decisions within each type, but found 27–40% of duplicates and got worse with a second
epoch. Its run was cut off by the GPU provider at about step 330 of 429, so the two saved checkpoints
were tested instead.

**How sure we are.**
- *One test set of 65 cases* (25 strategy points, 40 observations).
- *Size is confounded with model generation:* the 1.5B and 4B models are different Qwen versions (2.5 and
  3), so the results do not isolate model capacity as the explanation.
- *Class balance is not ruled out:* the log dismisses it on the grounds that the data is "60% duplicates",
  but the dataset is 45% duplicates (390 of 863), so the 4B model's lean toward keep may be partly the
  data's.
- *Label noise:* the 246 unreviewed keeps may hold some wrong labels.

**The call.** The track was closed; the decision stays an LLM call. A 7–8B model might narrow the gap,
but at that size the cost advantage over a flash-lite call shrinks.

**What would change it.** About 2,000 labelled cases balanced between strategy points and observations
(609 of the 863 are strategy points), labelled by models from different companies rather than three that
share the same lean, and 100–150 more test cases.

Detail: [classifier log](dedup_classifier/experiment_log.md).

## The embedding fine-tune

**Question.** Off-the-shelf embeddings put true duplicates and distinct lessons close together: on the
golden cases, the average similarity of a duplicate pair was 0.906 and of a distinct pair 0.878. Can
fine-tuning an embedding model push them apart, so the prefilter's cut-offs settle more cases? **Answer:
no run did.**

**Setup.** The base model was gte-modernbert-base (149 million parameters), trained on the same 861
labelled decisions, using the situation text only. Seven runs: the first three failed on setup (an
outdated training interface, out-of-memory on a T4 GPU, a precision error), and four trained. Each was
scored two ways: how often it put a held-out lesson closer to its duplicate than to a non-duplicate (87
held-out triplets), and how far apart duplicate and distinct pairs sat on 64 golden cases (30 duplicate,
34 distinct). The second is the one the prefilter needs. *Gap* is the difference between the two average
similarities (wider is better); *overlap* is how far the most similar distinct pair sits above the least
similar duplicate (smaller is better).

**Result.** Every run that ranked held-out triplets better did so without separating the golden cases
usefully:

| Run | Triplets ranked right (of 87) | Gap | Overlap |
|---|---|---|---|
| Base model | 38 (43.7%) | 0.028 | 0.175 |
| 4: triplet loss, random negatives | 59 (67.8%) | 0.008 | 0.082 |
| 5: triplet loss, hardest negatives | 49.4%, unstable | — | — |
| 6: similarity-target loss | 57 (65.5%) | 0.044 | 0.623 |
| 7: as 6, with a balanced validation split | 41 (47.1%) | 0.080 | 0.683 |

Run 4 pushed every similarity toward 0.97, duplicates and distinct alike, so its smaller overlap reflects
compression, not separation, and its gap shrank. Runs 6 and 7 moved the averages apart but scattered
individual cases, which is what makes cut-offs unreliable. Run 6's checkpoint choice was also blind: its
validation split held only non-duplicates, so the metric was undefined and the last checkpoint was kept.

**The diagnosis.** The training pairs carried the situation text only, while the labels were decided on
every field. Two lessons with the same situation and opposite actions were labelled distinct, and the
model was shown two near-identical texts; about 19 distinct cases had situation similarity above 0.88.
The cross-encoder track above then met the same ceiling with field-matched text.

**How sure we are.** Separation was judged by gap and overlap on the golden cases; the prefilter's own
zero-error sweep was not run on these models. The dataset of 861 pairs is small for a 149-million-
parameter model.

**The call.** Closed. No run separated duplicates well enough to adopt. The log calls the prefilter's ceiling a fundamental limit of similarity methods and suggests a revisit only with 3,000–5,000 labelled pairs; these runs, on 861 situation-only pairs, do not by themselves establish that general limit.

Detail: [embedding log](embedding/experiment_log.md).

## Where the labels came from

**Retrieval labels.** The reranker's graded pairs are in one file,
`evidence/extraction/situation_summary/outputs/retrieval_golden_labels.json`, which other retrieval
evaluations also read. The first 20 cases were labelled by the owner together with Claude and Claude
Opus; the next 20 by a vote of four models (ChatGPT, flash-lite, flash-3.5, Qwen 3.5) with a hand review
that corrected 14 of the 84 labels it checked. For the third round, situations
for 109 new turns were written by gemini-2.5-pro (16 reviewed by hand, 1 rewritten), the May store
returned 1,848 candidates (955 observations, 893 strategy points), and five labellers voted: ChatGPT and
Claude Sonnet, given the batches with full game context, and flash-lite, Mistral Small and Llama 3.1 8B,
given the situation alone. The vote was 3 or more in agreement on 1,383 items, unanimous on 281, a 2–2
tie broken by Sonnet on 144, and reviewed by Claude Opus on 40.

The two groups disagreed in one direction. The [context-eval log](../evaluation/labeling/context_eval/experiment_log.md)
measured it: against the two careful labellers, the merged labels over-credit relevance on 514 of 1,848
items, 458 of them in the majority tier, where the three automated voters (who rarely say "irrelevant")
outvote the two careful ones; the unanimous tier is clean. The two careful labellers themselves agree on
only 80.5% of items (relevant or not), so no single labeller is ground truth. A 150-item human check of
the LLM labels was designed and not run. The labelling engine built for this round is now
`evaluation/src/labeling/`.

**Dedup labels.** The 863 classifier cases (and the 861 pairs the two similarity tracks used from them)
were labelled by three Gemini models with a hand review, as told in the classifier section. The test set
for all three dedup tracks is the 65-case dedup golden set, labelled by hand
(`evaluation/frozen_eval_sets/dedup_v2_golden_labels.json`).

## Deployment status

Checked against the code on 2026-10-26.

- **The training code** is in `training/`: one training loop (`training/engine.py`), an adapter per task
  (`training/adapters/reranker.py::RerankerAdapter`, `training/adapters/dedup.py::DedupAdapter`), GPU
  training on Modal (`training/runner/modal_runner.py`) and CPU evaluation (`training/evaluate.py`). The
  adapters read their training data from this folder. The reranker log records that the CPU evaluation
  reproduces v4's 0.882. The weights live on Modal storage volumes, not in the repository.
  The training code was written by AI coding agents; the owner built the labelled datasets (owner,
  2026-10-21).
- **Neither cross-encoder is in production.** No code in `Agents/` or `server/` loads a cross-encoder or
  an ONNX model. The dedup prefilter is cosine similarity with fixed cut-offs
  (`Agents/memory/deduplication/prefilter.py`); the module docstring of
  `Agents/memory/deduplication/pipeline.py` names the cross-encoder "the planned swap-in … not yet wired
  in".
- **The reranker it would replace is off.** The live reranker is an LLM call
  (`Agents/memory/retrieval/rerank_agent.py::_rerank`). It is off for every role by default
  (`Agents/config/run.py::DEFAULT_RERANKING_CONFIG`), and served games do not turn it on
  (`server/game/run_config.py::game_run_config`, which also limits retrieval to strategy points).
- **The classifier and the embedding model** have no code outside their experiment folders.

"Not in production" is the state, not a finding that the cross-encoders cannot work there: wiring either
in would need a retrain and re-test on today's store first.

## What the four tracks have in common

- **Training metrics hid the failures; the held-out task metric found them.** The classifier's 93.6%
  token accuracy came with 43% correct decisions; the embedding's best triplet score came with a narrower
  gap. Each track was judged on the test that matched its job.
- **The input has to carry what the label judged.** The embedding run trained on situations against
  labels decided on whole lessons, and could not learn them. The reranker's suspected version of the same
  fault (labels that saw the action, a model that does not) was tested and found small.
- **Larger was not better at this data size.** The 110-million-parameter cross-encoder overfit on both tasks and scored below the 22-million one; the 1.5B classifier learned an item-type shortcut. These runs do not establish an optimal model size or a general capacity limit.

Two further ideas, distilling the player model for cheaper dialogue and a learned scorer for which
memories to show, were written up as designs in June 2026 and never built
([`agent_dialogue/`](agent_dialogue/experiment_log.md),
[`memory_selection_bandit/`](memory_selection_bandit/experiment_log.md)).

## Records

| Track | Log | Data |
|---|---|---|
| Reranker | [`cross_encoder/reranker/experiment_log.md`](cross_encoder/reranker/experiment_log.md) | `labels/` (round one, round two, the leak diagnostic; `manual_batches/` holds the ChatGPT and Sonnet batch prompts and replies), `training_data*/` (one folder per input variant), `eval_sitonly_vs_sitact_results.json`, `scripts/` |
| Dedup prefilter | [`cross_encoder/dedup_prefilter/experiment_log.md`](cross_encoder/dedup_prefilter/experiment_log.md) | `eval_modal.py`; training pairs `embedding/pairs_dedup.jsonl` |
| Dedup classifier | [`dedup_classifier/experiment_log.md`](dedup_classifier/experiment_log.md) | `sft_dataset.jsonl`, `agreed_labels.jsonl`, `disagreed_labels.jsonl`, `colabeling_log.jsonl` (617 reviewed decisions), case files per labeller |
| Embedding | [`embedding/experiment_log.md`](embedding/experiment_log.md) | `pairs*.jsonl`, `triplets*.jsonl` |
