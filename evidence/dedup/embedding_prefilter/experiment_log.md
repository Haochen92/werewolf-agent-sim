
## Embedding Pre-filter for Deterministic Auto-Decisions

### Motivation

Per-role extraction produces 2-3x more items than single-pass extraction (4 LLM calls per game x 4-8 items each), which overwhelms the LLM dedup pipeline. The existing dedup flow uses only situation embedding similarity from InMemoryStore search: items below `DEDUP_SIMILARITY_THRESHOLD` (0.55) bypass dedup entirely, and everything above gets an LLM call. This is wasteful — many cases are obvious duplicates or obviously novel, and the LLM call adds latency and cost without changing the outcome.

The idea: add a content-aware embedding pre-filter that compares more than just situation similarity. For strategy points, embed and compare the **action** field. For observations, embed and compare the **full content** (situation + approach + outcome concatenated). Use these similarities to make deterministic keep/discard decisions before LLM fallback.

### Design

**Strategy points**: After `store.search` finds candidates by situation similarity, embed `[new_action, cand1_action, cand2_action, ...]`, compute cosine similarity between new and each candidate's action. Take max action_sim. If action_sim >= discard threshold -> auto-discard. If action_sim < keep threshold -> auto-keep. Otherwise -> LLM.

**Observations**: Embed full content strings `f"{situation} {approach} {outcome}"` for new entry and all candidates. Take max content_sim. If content_sim >= discard threshold -> auto-discard. If content_sim < keep threshold -> auto-keep. Otherwise -> LLM.

On any embedding failure, fall through to LLM (fail-open).

### Calibration on Golden Set (65 cases)

Used the existing 65-case golden label set (`dedup_v2_golden_labels.json`: D=30, M=5, K=29, M/K=1) to find zero-error threshold boundaries. Embedded all cases using `gemini-embedding-001` at 1536D, cached to `evidence/dedup/per_extraction/embedding_cache.json`.

**Strategy points (25 cases: D=10, K=15)**

Action similarity distribution shows a gap between D and K:
- All D cases with action_sim >= 0.813; 5 of 10 D cases above 0.90
- All K cases with action_sim <= 0.899
- Zero-error boundary: discard >= 0.90, keep < 0.81

**Observations (40 cases: D=20, K=19, M=1)**

Content similarity is a stronger discriminator than field-level (approach/outcome) sims:
- All D cases with content_sim >= 0.936
- All K cases with content_sim <= 0.929
- Zero-error boundary: discard >= 0.96, keep < 0.935

Field-level approach/outcome sims were also computed but showed heavy D/K overlap, making them unsuitable as standalone discriminators. Content_sim (the full concatenation) captures all three fields at once and produces cleaner separation.

### Cross-Game Validation (232 cases)

The golden set only contains "hard" cases (sit_sim 0.70-0.91) because all cases were originally selected as LLM-worthy. To validate that the thresholds hold on a broader distribution, we built a cross-game calibration dataset.

**Dataset construction** (`evaluation/experiments/auto_dedup_dataset_builder.py`): Load extraction JSONL from 5 games into an InMemoryStore, then search extractions from 5 *different* games against that store. This produces genuinely novel items (from unseen games) alongside structurally similar ones, covering a broader similarity spectrum than the golden set.

Config: `configs/eval/auto_dedup_build_v1_cross_game.json`. Store: gemini-3.5-flash extractions from 5 games. Search: gemini-2.5-flash extractions from 10 games (5 overlapping with store, 5 unseen). Output: 232 cases (116 SP + 116 obs) in `eval_sets/auto_dedup_v1_cross_game.jsonl`.

**Labeling**: Each case was labeled D/K by running the production dedup prompt through two models:

| Labeler | D | K | Agreement with 3.5-flash |
|---|---|---|---|
| gemini-3.5-flash | 93 | 139 | — |
| gemini-3.1-flash-lite | 144 | 88 | 75.4% (175/232) |

Flash-lite is heavily discard-biased: 54 cases where 3.5-flash says K but lite says D, only 3 the other way. This matches flash-lite's known over-discard tendency from the prompt tuning experiments (K recall 52-59% vs 3.5-flash's 90%).

**Calibration results**: Swept thresholds against both label sets. The zero-error boundaries are identical regardless of which labeler is used:

| Type | Metric | Discard threshold | Keep threshold | Auto-rate (3.5-flash labels) |
|---|---|---|---|---|
| Strategy point | action_sim | >= 0.93 | < 0.81 | 14.7% (12D + 5K) |
| Observation | content_sim | >= 0.96 | < 0.93 | 31.0% (7D + 29K) |

All per-case decisions show zero errors at these thresholds across the full 232-case pool, for both label sets.

### Threshold Choice

The golden set (25 SP cases) showed a clean gap at action_sim 0.90 — all D above 0.903, all K below 0.899. The cross-game set (116 SP cases) reveals this was a small-sample artifact: 14/41 D cases fall below 0.90, and 20/75 K cases sit above 0.90. The D/K distributions heavily interleave in the 0.83-0.93 range.

Production thresholds:

| Constant | Value | Rationale |
|---|---|---|
| `SP_ACTION_DISCARD_THRESHOLD` | 0.93 | Zero-error boundary on cross-game set with *both* labelers. The golden set (25 SP) showed a gap at 0.90, but the cross-game set (116 SP) reveals D/K interleaving in 0.83-0.93. Critically, even flash-lite — the discard-biased labeler (D=144 vs 3.5-flash's D=93) — places the zero-error boundary at 0.93. When the model that maximally favors discard still can't justify auto-discarding below 0.93, 0.90 is too aggressive. |
| `SP_ACTION_KEEP_THRESHOLD` | 0.81 | Below lowest D in golden set (0.813); zero errors on cross-game |
| `OBS_CONTENT_DISCARD_THRESHOLD` | 0.96 | Zero errors on both golden and cross-game sets |
| `OBS_CONTENT_KEEP_THRESHOLD` | 0.935 | Zero errors on golden set; cross-game confirms clean separation at 0.93 |

### Impact

On the cross-game dataset (232 cases), applying all four thresholds:
- SP: 10.3% auto-discard, 4.3% auto-keep, 85.3% LLM
- Obs: 6.0% auto-discard, 25.0% auto-keep, 69.0% LLM
- Combined: ~23% of cases auto-decided, saving LLM calls

The observation auto-keep is the biggest win — items from unseen games with content_sim < 0.935 are reliably novel. The SP auto-rate is lower because action similarity in werewolf games is structurally compressed (many strategies recommend similar actions in different situations).

### Experiment: 3072 dimensions + SEMANTIC_SIMILARITY task type

**Hypothesis**: The 1536-dim `gemini-embedding-001` with default task type (`RETRIEVAL_DOCUMENT`) may compress the similarity space, limiting D/K separation. Two independent interventions could improve it: (1) increasing to 3072 dimensions for finer-grained similarity scores, and (2) using `SEMANTIC_SIMILARITY` task type instead of `RETRIEVAL_DOCUMENT` since dedup is a symmetric similarity task, not asymmetric retrieval.

**Method**: 2×2 factorial design on both the golden set (65 cases) and cross-game set (232 cases), sweeping thresholds with the same grid. Each combination computes fresh embeddings cached to a separate file.

| Condition | Dims | Task Type |
|---|---|---|
| Baseline | 1536 | RETRIEVAL_DOCUMENT (default) |
| Task-only | 1536 | SEMANTIC_SIMILARITY |
| Dims-only | 3072 | RETRIEVAL_DOCUMENT (default) |
| Both | 3072 | SEMANTIC_SIMILARITY |

**Results — SP zero-error auto rates:**

| Condition | Golden (25 SP) | Cross-game (116 SP) |
|---|---|---|
| 1536 + default | 24% (≥0.90, <0.81) | 14.7% (≥0.93, <0.81) |
| 1536 + SEMANTIC_SIM | 36% (≥0.91, <0.87) | 16.4% (≥0.94, <0.86) |
| 3072 + default | 24% (≥0.91, <0.82) | — |
| 3072 + SEMANTIC_SIM | 56% (≥0.92, <0.89) | 12.9% (≥0.95, <0.88) |

**Results — Obs zero-error auto rates:**

| Condition | Golden (40 obs) | Cross-game (116 obs) |
|---|---|---|
| 1536 + default | 30% (≥0.96, <0.94) | 31% (≥0.96, <0.93) |
| 1536 + SEMANTIC_SIM | 40% (≥0.95, <0.93) | 24.1% (≥0.97, <0.92) |
| 3072 + default | 27.5% (≥0.96, <0.94) | — |
| 3072 + SEMANTIC_SIM | 40% (≥0.96, <0.94) | 25% (≥0.97, <0.93) |

**Analysis**:

1. **SEMANTIC_SIMILARITY widens the keep zone** — at 1536 dims, the keep threshold rises from <0.81 to <0.86 for SP (more K cases auto-kept). But this comes at the cost of tighter discard thresholds (0.93→0.94 for SP), because genuinely-different items (labeled K) now cluster closer to duplicates.
2. **3072 dims amplify the effect** but don't help independently — on the golden set, dims-only (3072+default) gives identical SP auto rates to baseline. The benefit only appears when combined with SEMANTIC_SIMILARITY.
3. **Golden set overstates improvement** — the 25 SP golden cases don't have enough high-sim K cases to expose the tightened discard boundary. The 116 SP cross-game cases reveal heavy K/D interleaving in the 0.88-0.95 range at 3072 dims + SEMANTIC_SIM.
4. **Cross-game results are negative** — SP auto rate drops from 14.7% to 12.9% with both changes. Obs drops from 31% to 25%. The wider keep zone doesn't compensate for the tighter discard zone on the larger dataset.

**Decision**: Keep the current configuration (1536 dims, default `RETRIEVAL_DOCUMENT` task type). The baseline is the most robust on the cross-game dataset. Neither 3072 dims nor SEMANTIC_SIMILARITY improve net auto-decision coverage.

**Takeaway**: The similarity space is fundamentally mixed — items that are semantically similar can be genuinely novel (same situation, different lesson). No amount of embedding tuning can separate these without the LLM's reasoning about information content. The embedding pre-filter should remain conservative and let the LLM handle the gray zone.

### Experiment: Multi-dimensional threshold boundaries

**Hypothesis**: The 1D thresholds (action_sim for SP, content_sim for obs) may miss useful signal from other similarity dimensions. Two specific ideas: (1) For SP, use situation_sim as a second axis — requiring both high action AND high situation similarity for auto-discard could lower the action threshold. (2) For obs, use field-level sims (approach_sim, outcome_sim) for auto-keep — divergent approach or outcome is strong evidence for K.

**Method**: Sweep 2D threshold grids on both golden (65) and cross-game (232) datasets at 1536 dims. For SP: `action≥X AND sit≥Y → D`, `action<X' OR sit<Y' → K`. For obs: `content≥X → D`, `min(approach, outcome) < Y → K`.

**SP results**: In the interleaving zone (action_sim 0.85-0.93), D and K cases span the full situation_sim range:
- Golden: D sit_sim 0.778-0.876, K sit_sim 0.734-0.853 — complete overlap
- Cross-game: D sit_sim 0.787-0.878, K sit_sim 0.805-0.883 — complete overlap

Adding sit_sim as a discard requirement only removes correct D cases (from 12 to 7-11 on cross-game) without filtering any K cases. Using sit_sim for keep (OR condition) introduces 3-24 wrong keeps depending on threshold. Situation similarity provides no additional separating power.

**Obs field-level keep results**: Using `min(approach, outcome) < threshold` as a keep signal produces high error rates across all thresholds:
- Cross-game: field<0.86 → 47K correct, 14D wrong; field<0.90 → 62K correct, 32D wrong
- Golden: field<0.86 → 14K correct, 4D wrong; field<0.90 → 19K correct, 16D wrong

The problem: genuine duplicates can have divergent per-field phrasing while conveying the same lesson. Content_sim (full concatenation) averages out field-level noise; individual field sims amplify it.

**Decision**: The current 1D thresholds (action_sim for SP, content_sim for obs) are using the optimal signals. Neither situation_sim nor field-level sims provide additional zero-error separating power.

### What's next

The embedding pre-filter calibration is complete. All plausible improvements have been tested:
- Threshold grid sweeps on 65 human-labeled + 232 LLM-labeled cases
- Cross-model validation (3.5-flash + flash-lite labelers)
- Higher dimensions (3072) and task type (SEMANTIC_SIMILARITY) — no improvement
- Multi-dimensional boundaries (situation_sim, field-level sims) — no improvement

Future threshold adjustments should be driven by downstream retrieval quality rather than further calibration sweeps. If retrieval demands more aggressive discard or keep, the logged `similarity_scores` in Langfuse traces provide the data needed to re-sweep quickly.

### Key Learning: Why Embedding Similarity Has a Fundamental Ceiling

The calibration experiments above all converge on the same finding: the embedding pre-filter's auto-decision coverage plateaus around 15-30% regardless of how we tune it — higher dimensions, different task types, multi-dimensional boundaries. This section explains *why*, with concrete evidence from the dataset.

#### Embeddings capture topic, not position

Embedding models represent text as high-dimensional vectors that encode *what a text is about* — its topic, domain, entities, and vocabulary. They do not encode *what stance the text takes* on that topic. This means two texts can embed as nearly identical while giving contradictory advice.

**Case 155** from the cross-game dataset illustrates this clearly (action_sim = 0.946 at 3072 dims, 0.913 at 1536 dims):

> **NEW entry action**: "Prioritize investigating players who are actively pushing narratives, dismissing evidence, or creating deadlocks, rather than players who are already under heavy suspicion or confirmed roles, to maximize the chance of identifying a wolf."
>
> **Best candidate action**: "Avoid investigating the most vocal leader or the player most likely to be targeted by the wolves. If they are killed, your investigation is wasted; if they are saved by the healer, they are already soft-confirmed to the village, making your private investigation redundant. Instead, target moderately active players who are harder to read behaviorally."

These embed as 94.6% similar because they share the same topic (investigation targeting), role (investigator), game phase (early game), and vocabulary (investigate, players, active, target). The embedding model sees "both texts are about investigation targeting strategy for the investigator role in early game." But the actual advice directly contradicts: the new entry says to go after the *most active* players pushing narratives, while the candidate says to *avoid* the most vocal leader and target *moderately* active players instead. This is a genuine KEEP — the new entry teaches a different (arguably opposing) lesson.

This is not an isolated case. The spot-check of the 8 highest-similarity K cases in the cross-game dataset (action_sim 0.916-0.946) found 6 clear genuine K cases and only 2 borderline. The pattern is consistent: high embedding similarity reflects topical overlap, not prescriptive agreement.

#### Why this is a hard problem for embeddings

The issue is analogous to a well-known limitation in NLP: "Invest in crypto" and "Don't invest in crypto" embed very similarly in most models because they share all the same content words and differ only in a negation that carries minimal weight in the embedding space. For strategy points, the equivalent is two pieces of advice about the same tactical situation that disagree on *what to do*. The situation, role, game phase, and tactical vocabulary are identical — the disagreement lives in the relational structure of the advice (target X *instead of* Y), which embeddings flatten into a topic-level average.

This explains several observations from the calibration:
1. **The D/K interleaving zone (action_sim 0.83-0.93) is irreducible.** In this range, items share the same topic and game context but may teach the same lesson (D) or a different one (K). No embedding trick can separate these — it requires understanding what the advice *means*, not just what it's *about*.
2. **Higher dimensions (3072) didn't help.** More dimensions capture finer topical distinctions but don't introduce the ability to detect prescriptive disagreement. The D/K interleaving zone shifts but doesn't shrink.
3. **SEMANTIC_SIMILARITY task type didn't help.** Switching from retrieval-oriented to similarity-oriented embeddings changes how the space is projected but doesn't add the relational reasoning needed to tell "same advice" from "opposite advice on the same topic."
4. **Situation_sim provides no additional signal.** Both D and K cases have the same range of situation similarity because the *situation is genuinely similar* — that's not the ambiguity. The ambiguity is in the action.
5. **Field-level sims (approach, outcome) don't help for observations either.** Genuine duplicates can use different phrasing for the same approach or outcome, making field-level sims too noisy. Content_sim averages out the noise; individual fields amplify it.

#### Implications for the pre-filter design

The embedding pre-filter is correctly designed as a *conservative triage layer*, not a replacement for LLM reasoning:
- **High similarity (above discard threshold)**: Very high embedding similarity means near-identical text — not just the same topic but the same phrasing. These are safe to auto-discard because textual near-identity implies prescriptive agreement.
- **Low similarity (below keep threshold)**: Very low embedding similarity means different topics entirely. Safe to auto-keep because different topics cannot be duplicates.
- **Middle zone (LLM fallback)**: Items that share a topic but may or may not agree on what to do. Only an LLM can reason about whether "investigate active players" and "avoid investigating the most vocal leader" are the same advice or contradictory advice.

The ~15-30% auto-decision rate is not a failure of tuning — it's the natural ceiling of what topical similarity can determine without reasoning. The pre-filter eliminates the trivially obvious cases; the LLM handles the rest. Attempts to push beyond this ceiling (by lowering the discard threshold or raising the keep threshold) will always sacrifice correctness because they cross into the zone where topical similarity ≠ prescriptive agreement.

### Instrumentation for Future Calibration

A key lesson from this work: the threshold calibration would have been much simpler if embedding similarities had been logged from the start. We had to retroactively build a dataset builder, compute embeddings from frozen extraction artifacts, create a labeling pipeline, and run a separate calibration sweep — all because the production dedup flow didn't record the similarity scores that the auto-layer needs to calibrate against.

Going forward, every dedup decision now logs its full embedding similarities to Langfuse via the `similarity_scores` field on `DedupResult` and `DedupCase`. Each span records per-candidate sims (`action_sim_c1`, `content_sim_c1`, etc.) and the max sim used for the threshold decision. The batch entry points also distinguish embedding-auto from situation-only-auto in `DedupStats` (via `embedding_auto_kept` / `embedding_auto_discarded`).

This means future threshold tuning reduces to: pull traces → extract cases with `similarity_scores` → sweep. No re-embedding, no dataset builder, no separate labeling run. The LLM decisions on the non-auto cases serve as free labeled data accumulating over time — exactly the "log tuples and find where the boundary sits" approach, but with golden-labeled calibration as the principled anchor and production traces as the ongoing validation.

The tracing infrastructure (`_emit_dedup_span` → Langfuse span → `fetch_dedup_cases()` → `DedupDatasetRecord`) was already in place for decision-level eval. Adding `similarity_scores` to the existing span output was a one-field change that unlocks continuous threshold monitoring without any new infrastructure.

## Embedding Pre-filter Artifacts

| File | Description |
|---|---|
| `Agents/memory_deduplication.py` | Production pre-filter: `_embedding_prefilter_strategy_point()`, `_embedding_prefilter_observation()` |
| `evaluation/experiments/eval_auto_dedup.py` | Calibration sweep: embeds cases, caches, sweeps threshold grid, reports Pareto frontier |
| `evaluation/experiments/auto_dedup_dataset_builder.py` | Builds calibration datasets from extraction JSONL files |
| `evaluation/experiments/auto_dedup_labeler.py` | Labels auto-dedup cases via LLM for golden label creation |
| `evaluation/core/config_schema.py` | `AutoDedupDatasetBuildConfig`, `AutoDedupCalibrationConfig` |
| `evaluation/data/datasets.py` | `AutoDedupRecord`, `read_auto_dedup_dataset()`, `write_auto_dedup_dataset()` |
| `configs/eval/auto_dedup_build_v1.json` | Same-game dataset config (192 cases) |
| `configs/eval/auto_dedup_build_v1_cross_game.json` | Cross-game dataset config (232 cases) |
| `eval_sets/auto_dedup_v1.jsonl` | Same-game calibration dataset (192 cases) |
| `eval_sets/auto_dedup_v1_cross_game.jsonl` | Cross-game calibration dataset (232 cases) |
| `evidence/dedup/per_extraction/embedding_cache.json` | Cached embedding sims for 65 golden cases |
| `evidence/dedup/embedding_prefilter/cross_game_embedding_cache.json` | Cached embedding sims for 232 cross-game cases |
| `evidence/dedup/embedding_prefilter/cross_game_golden_labels.json` | 232 golden labels from gemini-3.5-flash |
| `evidence/dedup/embedding_prefilter/cross_game_golden_labels_flash_lite.json` | 232 golden labels from gemini-3.1-flash-lite |
| `evidence/dedup/embedding_prefilter/golden_embedding_cache_3072_dims.json` | Golden set at 3072 dims + SEMANTIC_SIMILARITY |
| `evidence/dedup/embedding_prefilter/cross_game_embedding_cache_3072_dims.json` | Cross-game at 3072 dims + SEMANTIC_SIMILARITY |
| `evidence/dedup/embedding_prefilter/golden_embedding_cache_3072_dims_default_task.json` | Golden set at 3072 dims + default task type |
| `evidence/dedup/embedding_prefilter/golden_embedding_cache_1536_dims_semantic_sim.json` | Golden set at 1536 dims + SEMANTIC_SIMILARITY |
| `evidence/dedup/embedding_prefilter/cross_game_embedding_cache_1536_semantic_sim.json` | Cross-game at 1536 dims + SEMANTIC_SIMILARITY |
