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
