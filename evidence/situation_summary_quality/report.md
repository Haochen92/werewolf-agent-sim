# Situation Summary Model Comparison

## Motivation

The situation summary component converts the current game state (visible discussion + private context) into 2-3 semantic search queries used to retrieve relevant observations and strategy points. It runs on every agent turn with gemini-3.1-flash-lite (no thinking). If the summaries are vague, fabricated, or miss the agent's role perspective, retrieval degrades regardless of store quality. This evaluation compares four models to determine whether upgrading from flash-lite improves summary quality enough to justify the cost.

## Design

We compared four models on 15 frozen EvalCase records from the v4 filtering eval dataset, covering four roles (healer, investigator, villager, wolf) across multiple game phases.

**Models tested:**
- gemini-3.1-flash-lite (default) — current production model, no thinking
- gemini-3.1-flash-lite (medium thinking) — same model with thinking enabled
- gemini-2.5-flash — next tier up
- gemini-3.5-flash — latest flash model

The hypothesis: flash-lite may be leaving quality on the table for this task, since situation summaries require synthesizing discussion dynamics, private knowledge, and role perspective into targeted retrieval queries. A more capable model might produce more specific, better-grounded summaries.

We initially tested flash-lite with high thinking, but abandoned it after case 1 took 593 seconds (nearly 10 minutes) — an unacceptable latency for a component that runs on every turn. Medium thinking kept latency under 10 seconds per case.

## Evaluation

Two evaluation approaches were used:

**Pairwise comparison** (gemini-3.1-pro-preview judge): Each alternative model's output was compared head-to-head against flash-lite-default on the same case, with alternating presentation order to reduce position bias. The judge chose a winner based on faithfulness, specificity, retrieval usefulness, non-redundancy, and role perspective.

**Rubric scoring** (gemini-3.1-pro-preview judge): Each model's output was independently scored 1-5 on the same five dimensions. This provides absolute quality levels per dimension rather than just relative rankings.

## Results

### Pairwise comparison (vs flash-lite-default baseline)

3.5-flash dominated the pairwise comparison, winning 14 of 15 cases. 2.5-flash was roughly equal to flash-lite, while medium thinking actually hurt.

| Model | Wins | Losses | Ties | Win rate |
|---|---|---|---|---|
| gemini-3.5-flash | 14 | 1 | 0 | 93% |
| gemini-2.5-flash | 8 | 7 | 0 | 53% |
| gemini-3.1-flash-lite (medium) | 4 | 10 | 1 | 27% |

### Per-dimension rubric scores (1-5 scale, 15 cases)

The rubric scores reveal where each model excels and where it struggles. The overall averages are surprisingly close despite the lopsided pairwise results.

| Model | Faithful | Specific | Retrieval | Non-redund | Role persp | **Avg** |
|---|---|---|---|---|---|---|
| flash-lite-default | 4.40 | 3.87 | 3.73 | 3.80 | 3.80 | **3.92** |
| flash-lite-medium | 4.27 | 3.20 | 3.33 | 3.67 | 3.47 | **3.59** |
| 2.5-flash | 4.93 | 4.00 | 3.60 | 3.40 | 2.73 | **3.73** |
| 3.5-flash | 4.53 | 3.87 | 4.00 | 3.53 | 3.67 | **3.92** |

### Latency

| Model | Avg/case | Total (15 cases) |
|---|---|---|
| flash-lite-default | 2.6s | 40s |
| flash-lite-medium | 4.3s | 64s |
| 2.5-flash | 9.5s | 143s |
| 3.5-flash | 7.0s | 105s |

### Pricing context

| Model | Input $/1M | Output $/1M |
|---|---|---|
| gemini-3.1-flash-lite | $0.25 | $1.50 |
| gemini-2.5-flash | $0.30 | $2.50 |
| gemini-3.5-flash | $1.50 | $9.00 |

## Analysis

### The pairwise vs rubric gap

The most notable finding is the disconnect between pairwise and rubric results. 3.5-flash won 14/15 pairwise comparisons but ties with flash-lite-default on rubric average (3.92). This suggests the pairwise judge is picking up on *consistent* advantages that are small per-dimension but compound across dimensions — when both outputs are placed side by side, the judge consistently prefers 3.5-flash even though the rubric scores look similar in isolation.

This is a useful calibration: pairwise comparison is more sensitive to quality differences than independent rubric scoring.

### Thinking hurts flash-lite for this task

Flash-lite with medium thinking scored the lowest across the board (3.59 avg), worse than flash-lite without thinking (3.92). It was also the worst on the pairwise comparison (4-10-1). The likely explanation: flash-lite lacks the model capacity to benefit from additional reasoning time on this task. Instead, the thinking budget may lead to overthinking or second-guessing, producing less focused summaries. This is consistent with the extraction evaluation where flash-lite with max thinking also underperformed.

### 2.5-flash has a role perspective problem

2.5-flash scored highest on faithfulness (4.93) — it rarely fabricates. But its role perspective score (2.73) is dramatically low, with 6 of 15 cases scoring 1. The judge consistently flagged it for "reading like an omniscient narrator" and ignoring role-specific private knowledge.

A concrete example: in a wolf case (d2r4), the agent IS player_6, but 2.5-flash writes "My wolf ally, player_6, is currently under direct scrutiny" — referring to itself in third person as its own ally. This produces retrieval queries that match "how to defend a teammate" rather than "how to handle being under suspicion as a wolf." Flash-lite-default handles the same case better, writing "my wolf ally, player_6, is facing direct pressure" but then adding "I am currently maintaining a low profile to avoid scrutiny" — at least acknowledging its own position.

For retrieval, this matters: a healer-perspective situation query should retrieve healer-relevant strategies, not generic observations. A model that drops role perspective undermines the retrieval pipeline even if its summaries are factually accurate.

### 3.5-flash wins on retrieval usefulness

3.5-flash's strongest dimension is retrieval usefulness (4.00 vs flash-lite's 3.73). Since the entire point of situation summaries is to drive retrieval, this is the most decision-relevant dimension. The 0.27 gap per case compounds across the 6-8 retrieval calls per game.

## Decision and tradeoffs

**Recommendation: keep flash-lite-default for now, revisit when production latency budget allows 3.5-flash.**

3.5-flash is clearly better on pairwise comparison and the most important dimension (retrieval usefulness), but the improvement is modest on rubric scores (3.92 vs 3.92 average). The cost increase is 6x on input and 6x on output, and latency nearly triples (2.6s → 7.0s). Since situation summary runs on every agent turn (multiple times per game round), the latency and cost compound significantly.

The strongest argument for upgrading: the pairwise judge picked 3.5-flash 14/15 times, suggesting consistent-if-small quality improvements that the rubric doesn't fully capture. If retrieval quality becomes a bottleneck in downstream evaluations, 3.5-flash is the clear upgrade path.

The argument against: flash-lite's current quality (3.92 avg) is adequate, and the retrieval pipeline has other levers (reranking, filtering, store quality) that may yield larger improvements per dollar than upgrading the summary model.

## Lessons

**Pairwise comparison is more sensitive than independent rubric scoring.** When two outputs are evaluated side by side, the judge can detect subtle quality differences that don't show up as score gaps on independent rubric evaluation. For model comparison decisions, pairwise is the more informative signal — but rubric scores explain *why* one model wins.

**Thinking budget is not universally beneficial.** For flash-lite, adding medium thinking made outputs worse (3.59 vs 3.92). The model lacks the capacity to productively use the reasoning time. This held across both extraction and situation summary tasks, suggesting it's a property of the model rather than the task.

**Role perspective is a hidden failure mode.** 2.5-flash's high faithfulness masked its poor role perspective (2.73). A summary that's factually accurate but framed from the wrong viewpoint will retrieve irrelevant memories. This dimension wouldn't be caught by a generic "quality" evaluation — it required the role-specific rubric.

## What's next

The situation summary eval pipeline (`evaluation/experiments/summary_eval.py`) now supports both frozen case scoring and model replay with per-dimension rubric judging. The pairwise experiment (`evaluation/experiments/summary.py`) now returns both per-output dimension scores and the pairwise winner in a single judge call. These tools enable future prompt iteration and model comparison without ad-hoc scripts.

If retrieval quality evaluations show that summary-driven retrieval is a bottleneck, the first lever to pull is upgrading to 3.5-flash. The infrastructure to test this is now in place.

## Artifacts

All artifacts are co-located in this evidence folder.

### Model outputs (15 cases each)

| File | Description |
|---|---|
| `model_comparison/outputs_flash-lite-default_20260524_162057.jsonl` | flash-lite default (no thinking) |
| `model_comparison/outputs_flash-lite-medium_20260524_162057.jsonl` | flash-lite medium thinking |
| `model_comparison/outputs_2.5-flash_20260524_162057.jsonl` | gemini-2.5-flash |
| `model_comparison/outputs_3.5-flash_20260524_162057.jsonl` | gemini-3.5-flash |

### Judge results

| File | Description |
|---|---|
| `model_comparison/judge_pairwise_20260524_162057.jsonl` | Pairwise comparison results (45 comparisons) |
| `model_comparison/rubric_judge_20260524_164203.jsonl` | Independent rubric scores (60 scores, 4 models × 15 cases) |
