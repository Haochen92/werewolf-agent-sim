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
| Observations store | `Agents/memory_stores/v4_deduped_v2/observations.json` | `33d9ad3ea4f2` |
| Strategy points store | `Agents/memory_stores/v4_deduped_v2/strategy_points.json` | `91cd6e244b9b` |

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
