# Situation Summary — chronological overview

**What this is.** The spine of the situation-summary quality workstream, in the order it happened. It has two
threads that met in the middle: first a **model comparison** (is flash-lite good enough to generate retrieval
queries?), then a **human-anchored retrieval golden** and the prompt iteration it drove (do the queries
actually retrieve the right memories?). It ends where [report.md](report.md) begins — that companion doc is the
destination, the current shipped state, which carried this study's endpoints one step further into the v6
cell-situation schema. How the output is *measured* — the two summary judges and the NDCG golden — is written
up in the funnel apparatus report
[../../evaluation/llm_judge/agent_decision.md](../../evaluation/llm_judge/agent_decision.md) (Stage 1).

The two original documents are preserved verbatim: the model-comparison report as **Appendix A**, the
golden-label retrieval log as **Appendix B**, so the curated arc and the original records can be read side by
side. Section numbers (`§N`) are for navigation; the dated tables live in the appendices.

**What situation-summary is.** On every agent turn, before the agent decides, one LLM call turns the current
game state into 1-2 semantic-search queries that retrieve the episodic memories the agent reasons with. It is
the front door of the memory *read* path, so query quality bounds retrieval quality no matter how good the
store is. That is why the workstream exists.

**Reading contract.** Sections are in time order, and each states what it tested and what it found. The arc
keeps its real corrections in place: a "core dilemma" dimension that felt right and scored negative (§3), and a
retrieval metric whose early wins were partly an unlabeled-item artifact that later labeling corrected (§4).
For the current shipped state, jump to [report.md](report.md).

---

## 0 · Origin — the query generator, and two unknowns

Situation-summary sits at the head of the retrieval pipeline: `game state → queries → semantic search →
retrieved memories → decision`. If the queries are vague, fabricated, or written from the wrong role's
viewpoint, retrieval degrades regardless of store quality. Two things were unknown. Was the cheap production
model (flash-lite) leaving quality on the table (§1)? And — the deeper question — did the pipeline actually
retrieve the *right* memories, something never checked against human ground truth (§2)? The two threads
answered these in turn.

## 1 · Model comparison — is flash-lite good enough?

Four models were compared on 15 frozen cases with two graders: a pairwise-preference judge (each model vs
flash-lite, order alternated) and an independent 1-5 rubric on five dimensions (faithfulness, specificity,
retrieval usefulness, non-redundancy, role perspective). The recommendation was **keep flash-lite** — the gain
from 3.5-flash was modest on rubric average, at 6× the cost and ~3× the latency, on a call that fires every
turn. Three findings outlasted the decision:

- **Pairwise is more sensitive than an independent rubric.** 3.5-flash won 14/15 pairwise while the rubric
  averages *tied* (both 3.92). Side by side, a judge detects small consistent advantages that isolated scoring
  misses — pairwise for the decision, rubric for the *why*.
- **Thinking hurt flash-lite.** Medium thinking scored *worse* than no thinking (3.59 vs 3.92). The model lacks
  the capacity to use the reasoning budget productively — the same effect the extraction study saw.
- **Role perspective is a hidden failure mode.** 2.5-flash was the most faithful model (4.93) yet scored 2.73
  on role perspective, writing omniscient queries — in one wolf case referring to *itself* in the third person
  as its own ally. A factually accurate query framed from the wrong viewpoint retrieves the wrong strategies. A
  generic "quality" score would have missed this; the role-specific dimension caught it.

The catch: every number here came from an *ungrounded* LLM judge. That is what the second thread set out to
fix.

## 2 · Building a human-anchored retrieval golden

Model comparison told us which query *looked* better to a judge, not which one *retrieved* better. So the
workstream built a golden set for retrieval correctness — the strongest anchor in the memory pipeline. The
design (Method A, query-forward): for each case, a human co-creates the ideal situation query from the exact
prompt inputs, runs top-10 semantic search against the frozen `v4_deduped_v2` store, and labels each retrieved
memory on a **3-point graded scale** (2 = highly relevant, 1 = partially, 0 = not), which enables **NDCG**.
Twenty cases were labelled across four roles and two phases — 340 relevance judgments. The baseline came out at
**NDCG@10 ≈ 0.83**: embedding retrieval was already doing a reasonable job, with the most headroom in top-3
precision and on strategy points (written more generically than observations, so they match less precisely).

## 3 · Prompt iteration, judged by NDCG

With a grounded metric in hand, the prompt was iterated and each version scored on the golden. This is where
the metric earned its keep by *overturning* intuitions:

- **Structured over prose (embedding alignment).** A structured query using the store's own dimensional labels
  embed-matched stored entries better than natural prose — same items retrieved, higher similarity. This is the
  first sighting of the alignment lever that v6 later made structural (§5).
- **Core dilemma: falsified in place.** A fifth "core dilemma" dimension (the agent's specific tradeoff) was
  added in v2 on the theory that state-similar cases can face different *decisions*. On clean cases it scored
  **net-negative (−0.084)**: it pushed the model toward abstract framing over concrete game events. It was
  removed in v4 — the single biggest improvement of the iteration.
- **Investigator lens fix (v4b).** Front-loading how the agent's private findings relate to the public
  narrative recovered an investigator regression.

Shipped **v4b**: +0.061 NDCG over the v1 captured baseline on expanded labels, with the largest gain on the
weakest role (villager, +0.196).

## 4 · The unlabeled-item trap, and its correction

The early golden-vs-captured gap (+0.112 NDCG) was partly an artifact: when a captured query retrieved items
the golden set never labelled, those items scored 0 by default, inflating the gap. **Phase 2 union labeling**
(labelling the 108 previously-unlabelled items) corrected it: the true improvement settled at **+0.061**, and
investigator flipped from −0.040 to **+0.042** — it had been improving all along, masked by the unlabeled
penalty. This is a methodological correction kept in place, not a headline: it is why the report's numbers are
the expanded-label figures, and why the auto-augmented golden is flagged as only directional.

## 5 · What graduated, and what did not

The iteration's endpoints graduated; the metric's staleness did not get fixed:

- **The v4b design** — structured dimensional fields, no core dilemma, investigator-lens-first — carried into
  the live **v6 cell-situation schema**, which makes the extraction↔summary alignment *structural*: the query
  is now composed by the *same* per-cell schema as the stored observation, so they embed-match by construction
  rather than by a shared prose convention (report.md, "What it produces").
- **flash-lite** stayed the production model (the model comparison held).
- **What did not carry forward:** currency. The golden and every NDCG number are anchored to the `v4_deduped_v2`
  store and 2026-05 prompts; the golden later grew to 108 cases via 4-model-consensus auto-labels, never
  human-re-validated. The cheapest fix — re-baseline NDCG against the v6_1 store, offline and free — is still
  open (report.md gap 1).

---

## Recurring threads

- **Two graders, two blind spots** (§1, §2) — the ungrounded content judges (pairwise + rubric) can rank and
  can catch a gross failure mode but cannot certify; the grounded NDCG golden can rank retrieval but cannot
  separate a bad query from a thin store. Neither alone is enough.
- **Grounding beats rubric intuition** (§3, §4) — the golden overturned two rubric-era reads: core dilemma
  *felt* right and scored negative, and the first gap was inflated by unlabeled items. A grounded metric earns
  its cost by being *wrong-proof* in ways a rubric is not.
- **Alignment is the lever** (§3, §5) — queries that share the store's structure embed-match better; v6 turns
  that from a prompt nudge into a schema guarantee.
- **Store coverage keeps leaking in** (§2, §3) — villager/wolf day_vote "query" weaknesses were really
  store-coverage gaps; NDCG through stage 1 can't fully separate them.
- **Everything is v4-stale** (§5) — golden + prompts on `v4_deduped_v2`, pre-v6; the single most-stale headline
  in the funnel.

## Artifacts

| Beat | Artifact | What it holds |
|---|---|---|
| §1 | `model_comparison/outputs_*.jsonl`, `judge_pairwise_*.jsonl`, `rubric_judge_*.jsonl` | 4-model outputs + pairwise + rubric judge results |
| §2-§4 | `retrieval_golden_labels.json` | the graded-relevance golden (⚠️ shared asset — also read by reranker training + context_eval; do not move) |
| §3 | `regenerated_situations_v*.json`, `quality_judge_results*.json`, `prompt_versions/` | per-version regenerated queries + judge scores + checkpointed prompts |
| §2-§4 | `staging/case_*.json` | per-case labeling inputs (the prompt the model saw) |
| destination | [report.md](report.md) | current shipped state (v6 cell schema) + freshness/gap tracking |
| apparatus | [../../evaluation/llm_judge/agent_decision.md](../../evaluation/llm_judge/agent_decision.md) | the L1/L2 measurement write-up (Stage 1) |

## Limitations / future work

Carried to the destination doc's gaps table ([report.md](report.md#current-vs-documented-gaps-freshness-2026-07-02)),
criticality-ordered and freshness-dated: the shipped prompt and golden are v5-era (gap 1), the summary-content
judges are uncalibrated (gap 2), the golden is partly machine-augmented (gap 3), and query quality is entangled
with store coverage (gap 4). The credible next step is a free v6_1 re-baseline of the NDCG golden before any
further prompt tuning is worth crediting.

---

## Appendix A — original model-comparison report (2026-05-24, verbatim)

> Preserved unedited as the original dated record of the model-comparison thread (§1), superseded by the
> curated narrative above. Written as a standalone `report.md`; its title and any file paths are
> period-accurate. The current shipped state and pointers live in [report.md](report.md).

---

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


---

## Appendix B — original golden-label retrieval log (2026-05-27, verbatim)

> Preserved unedited as the original dated record of the golden-label retrieval + prompt-iteration thread
> (§2-§4), superseded by the curated narrative above. It was written as this folder's `experiment_log.md`;
> its file paths and store versions (`v4_deduped_v2`, etc.) are period-accurate and may not resolve against
> current code. The current shipped state and pointers live in [report.md](report.md).

---

# Situation Summary — Experiment Log

## Context

The situation summary component generates 1-3 semantic search queries per agent
turn to retrieve relevant episodic memories. It has been evaluated once (model
comparison, see `report.md`), but retrieval quality has never been validated
against human ground truth. All prior retrieval evaluation used uncalibrated
LLM-judge scoring.

### Pipeline position

Situation summary is the query generator for the entire episodic memory
retrieval pipeline:

```
Game state → Situation summary (queries) → Semantic search → Filter/rerank → Agent decision
```

Two factors determine retrieval quality:
1. **Extraction ↔ summary alignment** — stored memory situation fields and
   generated queries live in the same semantic space (enforced by shared
   SITUATION_STANDARDS, but never empirically validated)
2. **Situation criticality** — queries capture the most important game dynamics
   for the agent's current decision

### What's missing

No golden labels exist for retrieval correctness. The retrieval eval uses
LLM-judge scores (relevance 1-5, efficiency 1-5) with no human calibration.
We cannot attribute retrieval failures to bad queries vs. bad store entries vs.
alignment gaps without ground truth.

---

## Experiment: Golden-Label Retrieval Evaluation

### Objective

Create a human-labeled golden set that validates whether the situation summary
pipeline retrieves the right memories, and provides a calibrated baseline for
future prompt/model changes.

### Method (Query-Forward, Method A)

We chose a query-forward approach over full store scanning because the
extraction pipeline is well-tuned — if a relevant memory exists, it should
appear in the top N via embedding similarity.

**Step 1 — Co-create golden situation queries.**
For each eval case, review the exact inputs the situation summary prompt
receives (visible discussion, private context, surviving players, day summaries,
strategy note). Write or edit "ideal" situation queries that capture the
critical game dynamics. Compare against pipeline-captured situations to identify
gaps.

**Step 2 — Run retrieval with golden situations.**
Semantic search top 10 per situation against the v4_deduped_v2 store. This
produces the retrieval candidate set for labeling.

**Step 3 — Label retrieval correctness (3-point graded scale).**
For each retrieved memory, label:
- **2 = Highly relevant** — directly addresses the game dynamic in the query
- **1 = Partially relevant** — related dynamic but different angle/phase/specificity
- **0 = Not relevant** — different situation entirely

### Metrics

- **NDCG@k** (k=3, 5, 10) — ranking quality with graded relevance
- **Precision@k** — fraction of top-k that is relevant (collapsing 2+1 vs 0)
- Per-role and per-phase breakdowns

### Dataset

Source: `eval_sets/v4_filtering_eval.jsonl` (40 cases, 10 per role, balanced
day_discussion / day_vote).

Sample: 15-20 cases stratified across 4 roles. Namespace sizes are manageable
(3-47 observations per namespace, 2-35 strategy points).

### Pinned artifacts (for reproducibility)

| Artifact | Path | SHA-256 (prefix) |
|---|---|---|
| Dataset | `eval_sets/v4_filtering_eval.jsonl` | `c13c8511f095` |
| Observations store | `memory_stores/v4_deduped_v2/observations.json` | `33d9ad3ea4f2` |
| Strategy points store | `memory_stores/v4_deduped_v2/strategy_points.json` | `91cd6e244b9b` |

Store: v4_deduped_v2 (194 observations, 205 strategy points, 11 namespaces).
Golden labels are only valid against these exact artifact versions.

---

## Log

### 2026-05-27 — Plan finalized

- Agreed on Method A (query-forward) over Method B (full store scan)
- Labeling scheme: 3-point graded relevance (0/1/2) enabling NDCG
- Built labeling tool: `evaluation/experiments/labeling/situation_retrieval_labeler.py`
  - `show`: renders exact prompt inputs (what the model sees)
  - `retrieve`: runs live retrieval against v4_deduped_v2 store
  - `label`: records golden situations + graded relevance labels
  - `sample`: balanced case selection across roles
  - `progress`: labeling status tracker
- Golden labels output: `evidence/extraction/situation_summary/retrieval_golden_labels.json`
- Next step: select cases and begin co-creating golden situations

### 2026-05-27 — Structured vs natural prose A/B test

Tested whether golden situation queries should use explicit dimensional labels
(matching the SITUATION_STANDARDS format used in stored memories) or natural
prose. Ran both variants on case 1 (healer, day 2, day_vote).

**Result: same items retrieved, same ranking, but structured scores consistently
higher.**

| Item | Natural (A) | Structured (B) | Delta |
|---|---|---|---|
| Obs 1 (vote with majority) | 0.7838 | 0.7921 | +0.008 |
| Obs 2 (healer voted out for passivity) | 0.7827 | 0.7853 | +0.003 |
| Obs 3 (healer dissented at first vote) | 0.7353 | 0.7813 | +0.046 |
| SP 1 (vote with majority, manage heat) | 0.7424 | 0.7757 | +0.033 |
| SP 2 (don't cast lone protest vote) | 0.7404 | 0.7706 | +0.030 |

The biggest jump (+0.046) was on Obs 3, whose stored situation field uses
explicit "Consensus texture" and "Game phase" labels — matching the structured
query format closely.

**Decision: use structured dimensional format for all golden situation queries.**
The store entries are written with SITUATION_STANDARDS dimensional labels
(information landscape, consensus texture, agent exposure, game phase), so
queries using the same vocabulary land closer in embedding space. This also
implies the production situation summary prompt may benefit from encouraging
dimensional structure in its output — a testable hypothesis for future prompt
iteration.

### 2026-05-27 — Cases 0-1 labeled

- Case 0 (healer, day 3, day_discussion): 10 obs + 10 strat labeled. Good
  retrieval quality — top items directly relevant. Some redundancy in
  healer-visibility observations.
- Case 1 (healer, day 2, day_vote): 3 obs + 2 strat labeled (thin namespace).
  Store coverage gap — no entries for information-starved first-vote dynamics.
  Retrieved items relevant for healer voting behavior but mostly from endgame
  contexts.
- Observation: day_summaries are the primary input when discussion hasn't
  started yet (round 1 cases). Day summary quality is an unevaluated upstream
  dependency that gates situation summary quality.
- Next step: continue labeling across remaining roles

### 2026-05-27 — Cases 2, 6 labeled + redundant situation pattern

- Case 2 (investigator, day 2, day_discussion): 10 obs + 10 strat labeled.
  Pipeline produced two situations — a generic landscape dump and a
  role-specific version. The generic one was an inferior subset of the
  role-specific one. Merged into a single integrated query and re-labeled.
- Case 6 (wolf, day 2, day_discussion): 10 obs + 10 strat labeled. Same
  redundant pattern caught before labeling. Merged to single query.
- Case 0 retroactively checked — two situations were genuinely distinct
  (village dynamics vs healer-specific exposure tradeoff). No merge needed.
- **Labeling principle established**: label based on situation match, not
  advice transferability. A strategy point with good advice but a different
  situation (e.g., endgame vs early-game) gets relevance=1, not 2.

### 2026-05-27 — Core dilemma dimension identified

During labeling, observed that the four SITUATION_STANDARDS dimensions
(information landscape, consensus texture, agent exposure, game phase)
describe the game *state* but not the *decision*. Two cases can have identical
dimensional profiles but face fundamentally different retrieval needs:

- "Should I follow a tone-based consensus when I have no unique info?"
- "How do I share private findings without outing myself as investigator?"
- "Should I reveal my role to prevent my own elimination?"

The missing element is the **core dilemma** — the specific strategic tension
or tradeoff the agent faces. The four dimensions act as the indexing key
(find similar states); the core dilemma acts as the discriminator (find
similar *choices* within similar states).

**Decision: add "Core dilemma" to SITUATION_STANDARDS as a fifth element.**
Constrained to one sentence describing the agent's specific tradeoff. Updated
both SITUATION_STANDARDS (shared across extraction, dedup, and situation
summary) and SITUATION_SUMMARY_SUFFIX (query generation instructions).

**Also applied: reduce max situations from 1-3 to 1-2.** Labeling revealed
the pipeline never produces 3 useful situations, and frequently fills the
second slot with a redundant angle of the first. Changed "1-3" to "1-2" and
replaced "Do not describe the same conflict from multiple angles" with
"Only write a second situation if it captures a genuinely independent
decision. Two views of the same conflict is one situation, not two."

**Open question: propagate to extraction prompts?** Existing store entries
have implicit dilemmas in ~60-70% of strategy points and ~30-40% of
observations. If the retrieval eval shows the implicit dilemmas are
sufficient for matching, no change needed. If NDCG reveals a gap between
state-similar but dilemma-different cases, updating extraction to produce
explicit dilemma fields is the next lever. Defer until golden-label eval
is complete.

### 2026-05-27 — Labeling complete (20/20) + NDCG baseline

Completed all 20 golden labels across 4 roles and 2 phases. Final batch
(cases 35, 37, 38, 39) all from game cdcd2c6e, providing cross-perspective
coverage of the same game from villager, wolf, and investigator viewpoints.

**Totals**: 176 observation labels + 164 strategy labels = 340 relevance
judgments. Distribution: 74 highly relevant (2), 91 partially relevant (1),
11 not relevant (0) for observations; 44/64/56 for strategy points.

**NDCG results (golden situations, v4_deduped_v2 store):**

| Metric | Observations | Strategy Points | Combined |
|---|---|---|---|
| NDCG@3 | 0.791 | 0.737 | 0.780 |
| NDCG@5 | 0.804 | 0.746 | 0.783 |
| NDCG@10 | 0.910 | 0.858 | 0.830 |

Observations rank better than strategy points at all cutoffs.

**Per-role (combined NDCG@10):**

| Role | NDCG@10 | n |
|---|---|---|
| healer | 0.900 | 4 |
| wolf | 0.844 | 6 |
| investigator | 0.825 | 5 |
| villager | 0.762 | 5 |

Villager retrieval is weakest — cases 13 (0.771) and 35 (0.634) drag it
down. Both are day_vote cases where strategy point rankings are poor
(SP NDCG@3 = 0.168 for both), suggesting the store lacks good strategy
entries for villager voting with behavioral-only evidence.

**Per-phase (combined NDCG@10):**

| Phase | NDCG@10 | n |
|---|---|---|
| day_discussion | 0.818 | 11 |
| day_vote | 0.845 | 9 |

Phases are comparable at @10, but day_vote is weaker at @3 (0.721 vs
0.829), meaning the most relevant vote strategies aren't surfacing at
the top of the ranked list.

**Interpretation**: Overall NDCG@10 of 0.83 is a solid baseline. The
embedding retrieval is doing a reasonable job of surfacing relevant
memories, but there's room for improvement in top-3 precision. The
strategy point rankings are consistently worse than observations,
likely because strategy point situations are written more generically
(broader applicability = less precise semantic match).

**Coverage gaps identified during labeling**:
- villager/day_vote: thin strategy coverage for behavioral-evidence-only voting
- wolf/day_vote: no "wolf as target" strategies, no "hopeless case" entries
- investigator/day_vote: small namespace with few entries

**Next steps**:
1. Run `--include-captured` comparison to measure golden vs pipeline
   situation gap (requires embedding API)
2. Decide whether extraction prompts need core dilemma update based
   on the gap between state-similar but dilemma-different cases
3. Consider whether store coverage gaps warrant new extraction passes

### 2026-05-27 — Golden vs captured situations comparison

Ran retrieval with the pipeline-captured situations (what the model actually
produced) and compared NDCG@5 against the golden situation baselines.

**Mean NDCG@5: golden 0.783 vs captured 0.671 (delta = +0.112)**

The situation summary prompt is leaving 11.2 pp of retrieval quality on the
table relative to hand-crafted queries.

| Case | Role | Golden@5 | Captured@5 | Delta | Unlabeled |
|---|---|---|---|---|---|
| 14 | wolf | 0.934 | 0.364 | +0.570 | 21 |
| 34 | villager | 0.754 | 0.192 | +0.563 | 19 |
| 39 | wolf | 0.820 | 0.515 | +0.305 | 7 |
| 38 | wolf | 1.000 | 0.723 | +0.277 | 9 |
| 37 | wolf | 0.717 | 0.460 | +0.256 | 8 |
| 16 | healer | 0.754 | 0.934 | -0.180 | 0 |
| 1 | healer | 0.879 | 0.986 | -0.107 | 0 |
| 2 | investigator | 0.830 | 0.927 | -0.097 | 12 |

**Caveat: unlabeled items.** When captured situations retrieve items not in
the golden set, those items get relevance=0 by default. Cases with high
unlabeled counts (14: 21, 34: 19, 12: 17) likely have inflated deltas —
the true captured NDCG could be higher. A fair comparison would require
labeling the union of golden and captured retrievals.

**Patterns in the worst cases:**
- Cases 14, 34, 37, 38, 39 (all large deltas) are from the same game
  (cdcd2c6e). The pipeline situations for these cases may have been
  too generic or missed the core dilemma dimension.
- Wolf cases show the largest average gap — the pipeline struggles most
  with wolf-specific strategic tensions.
- Cases where captured > golden (1, 2, 16) are mostly healer/investigator
  with 0 unlabeled — the pipeline sometimes produces better queries than
  our hand-crafted ones for simpler role dynamics.

**Interpretation:**
The 11.2 pp gap confirms that improving the situation summary prompt is a
viable lever for retrieval quality. However, the unlabeled item problem means
the true gap is probably smaller (maybe 5-8 pp after proper labeling). The
wolf-heavy worst cases suggest the core dilemma dimension is most impactful
for complex multi-agent strategic situations.

**Next steps:**
1. ~~Persist indexed store to avoid re-embedding~~ ✓ done (indexed_cache.pkl, 6.2 MB)
2. ~~Regenerate with updated prompt to isolate prompt impact~~ ✓ done (see below)
3. Label the union of golden + captured retrievals for a fair comparison

---

### Regenerated situation eval (flash-lite, core dilemma prompt)

Regenerated all 20 cases using the current prompt (core dilemma dimension,
1-2 situations) with `gemini-3.1-flash-lite` at `temperature=0.0`,
`thinking=medium`. All cases produced exactly 2 situations.

**Three-way NDCG@5 comparison:**

| Metric | Golden | Old captured | New regen | New−Old |
|--------|--------|-------------|-----------|---------|
| Overall mean | 0.7829 | 0.6725 | 0.7023 | +0.0298 |
| Clean subset (n=6, unlbl≤4) | 0.8768 | 0.8749 | 0.7907 | −0.0842 |

**Per-role means:**

| Role | Golden | Old cap | New regen | Delta |
|------|--------|---------|-----------|-------|
| healer (n=4) | 0.8781 | 0.9127 | 0.7903 | −0.1224 |
| investigator (n=5) | 0.7755 | 0.7598 | 0.8156 | +0.0558 |
| villager (n=5) | 0.6574 | 0.5046 | 0.6220 | +0.1174 |
| wolf (n=6) | 0.8301 | 0.5797 | 0.6162 | +0.0365 |

**Interpretation:**
- The raw overall delta (+0.030) is misleading — on clean cases where
  scoring is reliable (both old and new have ≤4 unlabeled items), the
  new prompt is **worse** by −0.084.
- Healer regressed most (−0.122). The old captured situations for healer
  cases were already near-golden quality. The new prompt's core dilemma
  framing may be over-specializing queries for complex roles at the
  expense of simpler healer dynamics.
- Villager improved most (+0.117), suggesting the core dilemma dimension
  helps the weakest-performing role by adding strategic context that was
  previously missing.
- Wolf improved slightly (+0.037) but still far below golden (0.830).
  The core dilemma framing alone isn't sufficient for wolf retrieval.
- The improvements on high-unlabeled cases (villager, wolf, investigator)
  may partly reflect lucky retrieval of unlabeled items that happen to be
  relevant but scored as 0. Need union labeling to confirm.

**Key takeaway:**
The core dilemma prompt update is **not a clear win for retrieval quality**.
The healer regression on clean cases is concerning. The improvements on
complex roles are promising but confounded by the unlabeled item problem.

---

### Prompt iteration: structured schema + dimensional fields

Iterated through several prompt versions to improve retrieval quality.
Key insight: the free-form `list[str]` situation output was format-mismatched
with the indexed store, where entries use explicit dimensional labels
(`Information landscape:`, `Game phase:`, etc.) composed from structured
extraction fields.

**Changes tested:**

1. **v2 (free-form, core dilemma)**: Original prompt with core dilemma as 5th
   dimension. Free-form text output.
2. **v3 (structured schema)**: `SituationEntry` with 5 required fields matching
   extraction schema. Composed via `_compose_situation()` to match indexed format.
3. **v4 (remove core dilemma)**: Dropped core dilemma from SITUATION_STANDARDS —
   it's redundant with the 4 dimensions and was pushing models toward abstract
   framing over concrete events.
4. **v4b (investigator lens fix)**: Changed investigator lens from "also note
   whether findings align" to "Lead with how your private findings relate to the
   public narrative." Also tested lens placement (bottom = worse, original = better).

**NDCG@5 results across all variants:**

| Prompt + Model | Overall | Clean (n=7) | Healer | Investigator | Villager | Wolf |
|---|---|---|---|---|---|---|
| Golden | 0.783 | 0.845 | 0.878 | 0.776 | 0.657 | 0.830 |
| Old captured (v1) | 0.673 | 0.823 | 0.913 | 0.760 | 0.505 | 0.580 |
| v2 free-form, flash-lite | 0.702 | 0.791 | 0.790 | 0.816 | 0.622 | 0.616 |
| v2 free-form, 2.5-pro | 0.682 | 0.734 | 0.765 | 0.773 | 0.579 | 0.634 |
| v3 structured, flash-lite | 0.688 | 0.807 | 0.852 | 0.760 | 0.558 | 0.627 |
| v3 structured, 2.5-pro | 0.690 | 0.820 | 0.833 | 0.725 | 0.545 | 0.685 |
| v4 no-dilemma, flash-lite | 0.708 | 0.811 | 0.874 | 0.668 | 0.700 | 0.638 |
| v4 no-dilemma, 2.5-pro | 0.700 | 0.815 | 0.897 | 0.654 | 0.563 | 0.721 |
| **v4b lens-fix, flash-lite** | **0.721** | **0.804** | 0.874 | 0.720 | 0.700 | 0.638 |

**Pairwise quality judge (captured v1 vs regenerated v2, 3.1-pro judge):**

| Metric | v2 free-form | v3 structured |
|---|---|---|
| Win rate (regen) | 55% (11-9) | 50% (10-10) |
| role_perspective delta | +0.40 | +0.50 |
| specificity delta | −0.60 | −0.65 |
| retrieval_usefulness delta | −0.20 | −0.50 |

**Key findings:**
- Structured schema (v3) improved clean-subset NDCG by closing the format
  gap with indexed store entries.
- Removing core dilemma (v4) was the biggest single improvement — stopped
  models from abstracting and pushed toward concrete game events.
- Model capability matters less than prompt format: flash-lite matches or
  beats 2.5-pro on most variants. Pro helps wolf cases specifically.
- Investigator lens fix (v4b) recovered investigator regression by
  front-loading private findings in the situation description.
- Flash-lite fails structured output with optional/nullable fields; all
  fields must be required strings.

**Final prompt (v4b) vs old captured (original labels, 340 items):**
- Overall: +0.049 (0.721 vs 0.673)
- Villager: +0.196 (0.700 vs 0.505) — largest per-role improvement
- Wolf: +0.058 (0.638 vs 0.580)
- Healer: −0.039 (0.874 vs 0.913) — small regression, acceptable
- Investigator: −0.040 (0.720 vs 0.760) — small regression, improved from v4

Note: 108 items (28% of v4b retrieval set) were unlabeled and scored as 0,
biasing results for cases where v4b retrieved different items than the golden set.

### Phase 2: Expanded labels (union labeling)

Labeled the 108 unlabeled items retrieved by v4b across 14 cases (Opus 4.6
auto-labels, relevance 0/1/2). This eliminates the unlabeled-item bias.

**v4b vs old captured (expanded labels, 448 items, 0 unlabeled):**

| | Golden | Old Captured | v4b Regen | Delta |
|---|---|---|---|---|
| Overall | 0.774 | 0.701 | 0.762 | **+0.061** |
| Healer | 0.878 | 0.913 | 0.874 | −0.039 |
| Investigator | 0.776 | 0.769 | 0.811 | **+0.042** |
| Villager | 0.643 | 0.489 | 0.701 | **+0.212** |
| Wolf | 0.814 | 0.680 | 0.696 | +0.016 |

**What changed with expanded labels:**
- Overall improvement is slightly larger (+0.061 vs +0.049)
- Investigator flipped from −0.040 to +0.042 — was actually improving all along,
  masked by unlabeled penalty on items that v4b retrieved but golden set didn't cover
- Villager improvement even stronger (+0.212 vs +0.196)
- Wolf improvement much smaller (+0.016 vs +0.058) — was inflated by unlabeled items
- Cases with most unlabeled items showed biggest corrections: case 34 (+0.415),
  case 35 (+0.439), case 30 (+0.265)

**Next steps:**
1. Cross-encoder reranker to close remaining gap on retrieval side
2. Consider per-role prompt tuning if investigator continues to lag

### Phase 3: Exponential NDCG gains + skewed training labels

Switched from linear NDCG gains (`rel`) to exponential (`2^rel - 1`).
Rationale: a grade-2 memory (exact same dilemma) is much more valuable
than grade-1 (related but different angle). Exponential gains make a 2
worth 3x a 1 (was 2x).

Also skewed cross-encoder training labels: 0→0.0, 1→0.25, 2→1.0 (was
0.0/0.5/1.0). The model now learns that partial relevance is closer to
irrelevant than to highly relevant.

**Re-scored existing 20 cases with exponential NDCG (golden situations):**

| Metric | Observations | Strategy Points | Combined |
|---|---|---|---|
| NDCG@3 | 0.719 | 0.678 | 0.711 |
| NDCG@5 | 0.715 | 0.689 | 0.708 |
| NDCG@10 | 0.795 | 0.766 | 0.732 |

Scores are lower than linear NDCG (was 0.783 combined @5) because
exponential gains penalize 1-before-2 ranking errors more heavily.

**Per-role (combined NDCG@5, exponential):**

| Role | NDCG@5 | n |
|---|---|---|
| healer | 0.834 | 4 |
| wolf | 0.767 | 6 |
| investigator | 0.705 | 5 |
| villager | 0.538 | 5 |

Villager dropped furthest (0.657→0.538) — confirms the store lacks
highly-relevant entries for villager voting scenarios. Partial matches
dominate the top slots.

**Golden vs captured (exponential NDCG@5):**

Mean: golden 0.708 vs captured 0.640 (delta = +0.068)

Largest gaps: case 34 (+0.545), case 14 (+0.485), case 38 (+0.312).
All wolf/villager cases from the same game (cdcd2c6e).
