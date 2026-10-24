# Scales and scores: how labels and judgements are measured

This page covers how the project puts a number on a label or a judgement: the scale a label is written
on, how a judge or model is scored against a golden set, and how two versions are compared. It is
shared by the two pages that use it most: [golden sets](../labeling/report.md), where labels are made,
and [LLM judges](../llm_judge/report.md), where models give them. Scores that code computes from a game
record to say how well agents played (vote accuracy, decision grades) are in [metrics](../metrics/report.md);
the safeguards on a comparison (power, drift, the arm guard) are in [experimental controls](../experimental_controls/report.md).
How it all fits together is in [the hub](../report.md).

## Three questions, kept apart

Measuring a judgement takes three steps, and each has its own kind of number. Mixing them up is the
commonest mistake: McNemar, for example, is not a score but a test for comparing two versions.

| Layer | The question | Examples |
|---|---|---|
| **1. The scale** | What does one label or verdict record? | yes or no; keep, discard or merge; relevance 0, 1 or 2; a 1–5 rubric score |
| **2. The score against a golden set** | How well do a judge's labels match the trusted ones? | accuracy, precision and recall, kappa, NDCG, the Brier score |
| **3. The comparison** | Is version B better than version A on the same cases, beyond chance? | McNemar, Wilcoxon, Fisher, with an interval |

## Layer 1. The scale of one label

| Scale | What it records | Example in the project | Who gives it |
|---|---|---|---|
| **Binary** | Yes or no | Is this statement a factual error? Should the echo gate hold this line? | The census reader; the expectation judge; the echo gate; a person |
| **Categorical** | One of a fixed set of classes | Keep, discard or merge (dedup); accusation, defense, agreement or neutral (each message's own tag); A–D for a silent turn's line (new fact, new inference, a question, a restatement) | The dedup model; the speaker; blind readers; a person |
| **Graded (ordinal)** | A degree, where order matters | Retrieval relevance 0, 1 or 2; 1–5 rubric scores for faithfulness or specificity | The reranker labellers; the memory-component judges |
| **Pairwise preference** | Which of two outputs is better | Two situation summaries side by side | The situation-summary judge |
| **Coverage of reference points** | How many of the points a person listed an output includes | A day summary against the points a correct one must contain | Planned for the extraction judges ([golden_set_method.md](../llm_judge/golden_set_method.md)) |
| **Probability** | How likely something is | A player's read of another seat ("70% wolf") | The players themselves |

**Choosing a scale.** The narrower the scale, the easier it is to label consistently and to check. A
binary or categorical label with a clear rule is the first choice. A graded scale is worth it when the
degree changes what happens next, as with relevance, where a partly relevant memory should rank below a
fully relevant one. A 1–5 rubric is the last choice: in this project the extraction judges' scores
bunched near the top of the scale on any dimension the prompt forced to exist, and the situation-summary
judge's scores were flat across prompt versions. Pairwise preference avoids that bunching, because the
judge only has to say which output is better.

## Layer 2. Scoring a judge or model against a golden set

The golden set is taken as the truth; the judge's labels are scored against it. The score depends on the
scale.

| Scale | Score | What it tells you | Example in the project |
|---|---|---|---|
| Binary | **Precision and recall** (with accuracy and a confusion table) | Precision: of what the judge flagged, how much was real. Recall: of what was real, how much it flagged | The census reader: precision about 0.8 on private notes, with 2–3 misses in 15 rejections; the tell detector: 0.93 precision and 87% recall on discussion |
| Binary or categorical | **Agreement**, with **Cohen's kappa** | How often the judge matches the person, and how much of that is beyond chance (kappa 0 = chance, 1 = perfect) | The decision tags: 96.1% agreement (± 3.8%) against a bar of 90% set beforehand; kappa is built into the calibration stage from 2026-10-23 |
| Categorical | **Accuracy per class, with a confusion table** | Which classes the judge confuses | The dedup model against the 65 human labels: 78% strict, with merge over-called (precision 0.56) |
| Graded, used to rank | **NDCG@k** (and hit@k) | Whether the most relevant items come first; a 2 placed below a 0 costs more than the reverse | The reranker: NDCG@5 of 0.882; the situation-summary prompts, settled at +0.06 and −0.08 |
| 1–5 rubric | **Agreement within one point, weighted kappa, rank correlation, and the mean difference** | Whether the judge ranks outputs as a person would, and whether it runs high or low | Designed for the application judge (about 28 blind cases), never run |
| Pairwise | **Win rate, and agreement with a person's preference** | Which version a judge prefers, and whether a person would agree | Situation-summary model comparison, with the order of the two outputs alternated so the judge's preference for one position cancels out |
| Reference points | **Coverage** (the share of points included) | Whether the content is right, not just present | Planned only |
| Probability | **The Brier score** (the mean squared gap between the stated probability and what turned out true) | How well calibrated a player's guesses are | Players' reads, in [metrics](../metrics/report.md) |

**Why plain accuracy is not enough for a subjective 1–5 score.** Exact agreement on a five-point scale is
rare even between two people, and it treats a 4 against a 5 the same as a 1 against a 5. Agreement within
one point and weighted kappa give partial credit for near misses; rank correlation asks whether the judge
orders outputs the way a person does; the mean difference shows whether it is simply lenient. None of
these has been run in the project: no 1–5 judge has been scored against people.

**Every score needs its interval.** Most checks here are small (tens of items), so a rate alone overstates
what is known. The project reports exact (Clopper–Pearson) intervals. Items from the same game are not
independent, so when a sample bunches in a few games even that interval is too narrow; a bootstrap by game
is designed but not built ([plan.md](../labeling/plan.md)), and the owner checks spread their samples across
games instead.

## Layer 3. Comparing two versions

| Design | Test | When | Example in the project |
|---|---|---|---|
| The same cases under both versions, a yes-or-no outcome per case | **McNemar** (exact): only the cases where the two versions differ count | Prompt or model changes on a frozen test set | The July prompt bundle: 29 cases better, 11 worse, p = 0.003; the October fixes: 24 better, 14 worse, p = 0.14 (a direction, not proof) |
| The same cases or deals, a score per case | **Wilcoxon** (signed-rank) | Paired decision scores in game A/Bs | The whole-game memory comparisons ([whole games](../evaluation_scopes/game/report.md)) |
| Two independent groups, a rate each | **Fisher's exact test** | Win rates from unpaired batches | `core/stats.compare_proportions` |
| One judge against a person, binary | **McNemar on the disagreements** | Does the judge lean one way (flag too much or too little)? | Part of the acceptance gate in the calibration stage, from 2026-10-23 |

Before comparing versions, re-judge the same outputs once to see how far the totals move with no change
at all: on the nine-seat factual-error test set that noise floor was 1 to 2 of 267, so smaller differences mean
nothing ([factual_errors](../factual_errors/report.md), step 4). The code for all of these is in
`evaluation/src/core/stats.py`.

## Where the project stands

- **Built and used:** precision and recall, accuracy with confusion tables, NDCG, the Brier score, McNemar,
  Wilcoxon, Fisher, exact intervals.
- **Built on 2026-10-23, not yet used on real labels:** agreement with kappa, the bias test and the
  acceptance gate, in the labelling pipeline's calibration stage.
- **Not built:** weighted kappa and rank correlation for 1–5 judges; the bootstrap interval by game;
  coverage scoring for reference points.
- **The gap that matters:** the 1–5 rubric judges have never been scored against people at all, so their
  numbers show direction only.

## What we would do differently next time

| Stage | Change | What was done | What it would buy |
|---|---|---|---|
| Design | **1. Choose the scale and the score before building a judge** | 1–5 rubrics were the default for the memory-component judges; the extraction judges' scores bunched near 5, and the situation-summary judge's were flat across versions | Judges whose numbers can move, and a known way to check them |
| Design | **2. Prefer binary or categorical labels with a written rule**, a graded scale only where the degree changes what happens, pairwise for relative quality | The rubric scale came first, the question second | Labels that people and models give consistently, scored with plain precision and recall |
| Check | **3. Report every score with its interval and its noise floor** | Done for the factual-error test set and the July test; not for most judge numbers | No small difference read as a result |

**Bottom line.** The project uses the standard scores for each kind of label, and the comparisons between
versions use the right paired tests. What is missing is on the subjective side: the 1–5 judges have no
score against people, and the scores that would measure them are not built.

*Written 2026-10-23 from the records linked above and `evaluation/src/core/stats.py`.*
