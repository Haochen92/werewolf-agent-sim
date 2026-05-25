# Per-Extraction Dedup: Golden Labels and Baseline Accuracy

## Motivation

The per-extraction dedup pipeline runs after every game to decide whether newly extracted observations and strategy points are novel (KEEP), redundant (DISCARD), or partially overlapping (MERGE). The batch dedup work ([store_dedup/report.md](../store_dedup/report.md)) showed that store-level cleanup dramatically improved retrieval quality, but we had no way to measure how accurately the LLM makes individual dedup decisions. The existing `dedup_eval.py` used an LLM judge to score decisions — which meant we were evaluating one LLM's judgment with another LLM's judgment, with no ground-truth anchor. We needed human-annotated golden labels so we could measure decision accuracy deterministically and identify systematic biases in the dedup prompt.

## Design and Hypothesis

**Dataset**: 50 cases sampled from 390 total dedup spans across 30 games (v4_action_phase_v2, seed=42). The sample is balanced: 25 observations, 25 strategy points. Each case contains the new entry, its top-k candidate matches with similarity scores, and the LLM's original decision.

**Label scheme**: We used the current D/M/K (Discard/Merge/Keep) scheme rather than the legacy A/B/C/D codes present in the dataset. This meant translating legacy decisions for comparison. The hypothesis was straightforward: human review of 50 cases would establish a reliable accuracy baseline, and the error patterns would reveal specific prompt weaknesses worth fixing.

**Labeling process**: Interactive human-in-the-loop review. For each case, we examined the new entry and its candidates, compared the strategic lessons taught, and assigned D/M/K. When cases were ambiguous, we surfaced the original text to resolve them. We tracked tricky/mislabeled cases in a separate file to accumulate prompt improvement evidence.

### Key schema constraints discovered during labeling

- **Strategy points only support D/K** — no merge. This was confirmed from `StrategyDedupDecisionOutput` in `Agents/memory_deduplication.py`, which is a union of `StrategyDiscard | StrategyKeep`. Strategy points are prescriptive rules; merging two pieces of advice into one is semantically harder than merging two game anecdotes.
- **Strategy point discard-with-rewrite** bridges this gap. `StrategyDiscard` has optional `improved_situation` and `improved_action` fields — the pipeline can discard the new entry but steal its better phrasing to improve the existing one. We used this for 2 cases (28, 33) where the new entry was better written but covered the same lesson.
- **`also_acceptable` for borderline cases**. Some cases genuinely fell between D and M — a specific instance of a well-generalized pattern could be either "discard, it adds nothing" or "merge, it enriches the pattern." Rather than forcing a single label, we added an `also_acceptable` field (used for cases 22 and 35). This avoids penalizing the LLM for a judgment call that humans can't consistently resolve.

## Process and Challenges

### Labeling workflow

We reviewed all 50 cases interactively across two sessions. For each case, the initial pass showed a condensed summary: item type, the LLM's original decision, the new entry's key content, and the top candidate's key content with similarity score. Most cases (especially clear keeps and clear discards) were decided from the summary alone. When a case felt ambiguous, we surfaced the full original JSON text for the new entry and relevant candidates — this happened roughly 15 times out of 50, concentrated in the observation cases.

The workflow evolved as we went. Early on (cases 0-15), we relied more on summaries and quick gut checks. By the mid-twenties, we'd developed a sharper eye for the subtle distinction between "same response to different triggers" vs "different response to same trigger," and started proactively requesting original text for any observation case with similarity > 0.80. This shift was prompted by Case 17, where the summary made two entries look like the same "endgame rejection of wolf deflection," but the full text revealed distinct wolf tactics being countered.

### Challenge: the D/M gradient for observations

The hardest recurring judgment was Discard vs Merge for observations. Both mean "these are about the same thing" — the question is whether the new entry adds anything worth incorporating into the existing text. In practice, nearly every new observation adds *some* specificity (a game phase detail, a player count, a specific outcome). The question became: does this specificity change what an agent would *do* with the information?

Case 22 was the clearest example of this tension. The new entry detected late bussing (wolf joining the correct vote suspiciously late); the candidate detected partner protection (wolf voting against eliminating their partner). The village response was identical ("press with evidence → wolf folds"). Initially it looked like a merge, but the detection heuristic was fundamentally different — an agent reading one wouldn't learn the other. This was a Keep that the LLM mislabeled as Merge.

Conversely, Case 23 was a genuine borderline: a specific "protect effective villager" observation vs an already well-generalized candidate with obs_count=3. The new entry added "revenge targeting" detail but no new strategic dimension. We couldn't confidently choose D or M, so this prompted the `also_acceptable` design decision.

### Challenge: confusing source text

Case 35 initially tripped up both the human reviewer and the LLM. The new entry described a player voting against someone, but the writing made it ambiguous whether the target was a confirmed non-wolf (which would be a distinct observation about voting against cleared players) or just another suspect. On closer reading, the confirmed non-wolf was a different player entirely — the confusing pronoun reference masked what was actually a straightforward "bandwagon with no evidence" pattern, making it a Discard of Candidate 1. The LLM labeled it Keep, likely confused by the same writing ambiguity. This is a data quality issue rather than a prompt issue — the extraction step produced confusingly written text that downstream dedup couldn't parse correctly.

### Challenge: conflicting strategy advice

Case 42 presented two strategy points giving opposite advice for the same situation: "vote for a third target to avoid suspicion" vs "vote with the majority to blend in." Both are valid wolf tactics depending on context. Our initial instinct was that conflicting advice should be merged into a single nuanced entry, but strategy points don't support merge. The right call was Keep — giving the agent two distinct tactical options is better than forcing one. This reframed our thinking: for strategy points, contradiction between entries is a feature (tactical flexibility), not redundancy.

### Design decision: why 50 cases

The 390-case full dataset was too large for careful human review. We considered three sample sizes: 20 (quick but possibly too few error cases to identify patterns), 50 (balanced between effort and statistical coverage), and 100 (thorough but would take multiple sessions). At 50, we expected ~10-15 mismatches at 70-80% accuracy — enough to identify recurring patterns but not so many that labeling fatigue degrades quality. The actual 11 mismatches confirmed this was the right range: enough to see three distinct bias patterns, few enough that each mismatch got careful attention.

### Design decision: tricky cases as a separate artifact

Rather than embedding labeling notes directly into the golden labels JSON, we created a separate `dedup_v2_tricky_cases.md` with full original text for both entries. The rationale: the golden labels file is for automated scoring (structured, machine-readable), while the tricky cases file is for prompt debugging (narrative, human-readable). Keeping them separate means the scorer doesn't need to parse prose, and the prompt engineer doesn't need to decode JSON to understand what went wrong. Each tricky case includes the LLM's decision, the golden label, the tension (why it was wrong), and the prompt implication (what to fix) — a self-contained prompt debugging unit.

## Evaluation Setup

**Golden labels**: 50 cases in `eval_sets/dedup_v2_golden_labels.json`. Distribution: D=19, M=6, K=25.

**Tricky cases**: 7 mislabeled cases documented in `eval_sets/dedup_v2_tricky_cases.md` with full original text for both new entry and candidate, enabling prompt auditing.

**Scorer**: `evaluation/experiments/dedup_score.py` — deterministic, no LLM. Auto-detects legacy vs current scheme. Reports strict accuracy (exact match), lenient accuracy (accepts `also_acceptable`), per-label precision/recall/F1, confusion matrix, and per-item-type breakdown.

**Legacy decision mapping**: The dataset uses legacy codes (A/B/C/D) that must be translated to current D/M/K for comparison. This mapping was non-trivial — see the iteration below.

## Iterations

### Legacy B mapping: one size does not fit all

The initial scorer mapped legacy decisions uniformly: A→D, B→M, C→K, D→K. This produced 66% accuracy. But the mismatch list was suspicious — nearly all strategy point errors showed predicted=M, which is impossible since strategy points don't have merge.

The problem: legacy B (REPLACE) means "these are about the same thing; keep the better one." For observations, this maps to M (merge them). For strategy points, it maps to D (discard the new one, since merge doesn't exist). The LLM was making the correct "same thing" judgment, but the uniform B→M mapping was miscounting it as the wrong decision type.

After splitting the mapping by item type (B→M for observations, B→D for strategy points), accuracy jumped from 66% to 78%. This was purely a scoring fix, not a change in the LLM's behavior — but it taught us that **the legacy-to-current mapping is not a simple lookup table; it's mediated by schema constraints**.

## Results

The baseline LLM (gemini-2.5-flash, the model used during the original 30-game batch) scores 78% strict / 80% lenient on the 50-case golden label set.

| Metric | Overall | Observations | Strategy Points |
|---|---|---|---|
| Strict accuracy | 39/50 (78%) | 18/25 (72%) | 21/25 (84%) |
| Lenient accuracy | 40/50 (80%) | 19/25 (76%) | 21/25 (84%) |

Observations are harder than strategy points. The 12-point gap makes sense: observations require comparing nuanced game anecdotes to decide if they teach the "same lesson," while strategy points are more concrete ("investigate the dissenting voter" is clearly a duplicate of the same advice elsewhere).

### Per-label precision, recall, and F1

The confusion pattern reveals where the LLM systematically errs.

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| D (Discard) | 0.82 | 0.74 | 0.78 | 19 |
| M (Merge) | 0.56 | 0.83 | 0.67 | 6 |
| K (Keep) | 0.83 | 0.80 | 0.82 | 25 |

MERGE has high recall (0.83) but low precision (0.56) — the LLM correctly identifies most true merges, but also incorrectly calls merge on cases that should be discard or keep. In other words, the LLM over-merges. This is the dominant failure mode.

### Confusion matrix

|  | pred D | pred M | pred K |
|---|---|---|---|
| **gold D** | 14 | 2 | 3 |
| **gold M** | 0 | 5 | 1 |
| **gold K** | 3 | 2 | 20 |

Two patterns stand out:

1. **gold_D → pred_M (2 cases)**: The LLM chooses merge when it should discard — it sees surface-level detail differences and wants to incorporate them, even when the existing entry already generalizes the pattern well. Case 24 is the clearest: the exact same "groupthink accusation" tactic in the same situation, but the LLM opted for merge because the new entry had "more specific game state details."

2. **gold_K → pred_M (2 cases)**: The LLM merges entries that are actually distinct. Cases 16 and 21 both involve endgame voting-record analysis, but teach fundamentally different detection heuristics — late bussing (Case 21) vs partner protection (Case 16's candidate). The LLM focused on the similar *villager response* (press with evidence → wolf folds) rather than the distinct *signal being detected*.

## Systematic Biases

The 7 tricky cases revealed three patterns in the dedup prompt's failure modes:

**1. Over-merging when the response is similar but the opposing tactic differs.** (Cases 16, 21) If the correct action for the agent is the same ("trust the evidence"), the LLM concludes the observations are the same — but the wolf tactic being countered is different, which makes the observation teach a different lesson. The prompt should emphasize: if the opposing player's strategy is distinct, the observation is distinct even if the correct response looks similar.

**2. Merge bias over discard when any surface detail differs.** (Cases 22, 24) The LLM defaults to merge whenever the new entry adds any specificity (a game phase detail, a player count, a specific outcome), even when the existing entry already captures the general principle at sufficient abstraction. The prompt should clarify: merge is for when the new entry adds a *meaningfully different tactical dimension*, not just different instance details.

**3. Over-differentiating based on game phase alone.** (Case 40) The LLM kept an entry as distinct because the "too obvious" defense occurred in endgame vs mid-game. But the tactic, defense, and outcome were identical — the phase difference doesn't change the lesson. The prompt should emphasize: a different game phase does not make an observation distinct if the strategic lesson is the same.

These three biases are actionable prompt improvements. They're documented with full original text in `eval_sets/dedup_v2_tricky_cases.md`.

## Lessons

**Ground-truth labels expose biases that LLM judges miss.** The existing `dedup_eval.py` LLM judge scored decision correctness on a 1-5 scale, but it couldn't identify systematic patterns like "over-merging when villager response is similar." That requires comparing predicted vs actual labels across cases and looking at the confusion matrix — which requires knowing the actual correct answer. LLM-as-judge is useful for evaluating *rewrite quality* (which is subjective), but *decision correctness* needs deterministic scoring against ground truth.

**Schema constraints mediate evaluation mappings.** The legacy B→M mapping was correct for observations but wrong for strategy points, because strategy points don't have a merge option. This is easy to miss when translating between decision schemes — the "obvious" mapping (REPLACE≈MERGE) only holds when the target schema supports it. Any time you map between label sets, check whether the target schema constrains which labels are valid for which item types.

**Borderline cases need explicit handling, not forced decisions.** The `also_acceptable` field avoided two problems: (a) penalizing the LLM for a judgment call that humans disagree on, and (b) artificially inflating accuracy by always picking the label that matches the LLM. Reporting both strict and lenient accuracy makes the uncertainty transparent rather than hiding it in either direction.

**A small, well-annotated dataset beats a large noisy one for prompt debugging.** 50 cases was enough to identify three distinct bias patterns with specific prompt fixes. The value wasn't in the accuracy number (78% is a baseline, not a verdict) — it was in the mismatch analysis that showed *why* the LLM errs. The tricky cases file, with full original text and labeled tension, is more useful for prompt improvement than the aggregate metrics.

## What's Next

1. **Prompt refinement**: Apply the three bias corrections to the dedup prompt and re-run scoring to measure improvement. The tricky cases file provides the test cases.
2. **Model comparison via replay**: Use `dedup_replay.py` to run the same 50 cases through different models (gemini-2.5-pro, gemini-3.5-flash) and score against golden labels. The scorer already handles replayed datasets.
3. **LLM judge for rewrite quality**: The deterministic scorer handles D/M/K decision accuracy. For cases where the LLM merges or rewrites, rewrite quality still needs an LLM judge — this is the second layer of evaluation mentioned in the design.
4. **Batch dedup cluster labeling**: 34 clusters in `eval_sets/batch_dedup_clusters_v4.json` still need golden labels. This is a different evaluation target — cluster-level decisions rather than per-extraction decisions.

## Prompt Revision: Observation Dedup v2

### Diagnosis

The baseline observation prompt had two structural weaknesses exposed by the tricky cases:

1. **DISCARD defined as "exact duplicate"** — too narrow. The LLM treated any surface detail difference (player count, game phase, save count) as evidence against DISCARD, falling through to MERGE even when the strategic lesson was identical. This created the merge-bias-over-discard pattern (Cases 22, 24) and the phase/degree over-differentiation (Cases 2, 40).

2. **Decision test only checked the agent's response** — the MERGE/KEEP test asked "would the agent make a different strategic decision?" This is framed from the responder's perspective. When the agent's response is the same ("press with evidence"), the LLM concluded MERGE — but the observation might teach a different *detection heuristic* (late bussing vs partner protection) that the agent must learn independently. Cases 16 and 21 were both victims of this one-sided test.

### Design process

Three independent drafts were produced and compared. All three converged on the same structural fix: a two-stage decision test (lesson identity first, then signal novelty). They diverged on presentation style — narrative prose vs labeled rules vs formulaic branching.

Key design decisions in the final merged version:

- **"An agent reading this learns..." sentence stem** — forces the model to abstract away surface details before comparing. The final version mandates writing these sentences in the reasoning output, not just performing the test mentally. This compliance mechanism matters for flash models that might shortcut reasoning.
- **"Which side changed?" branching** in Stage 2 — creates a clean binary: opponent side differs → KEEP, agent side differs → MERGE. This directly addresses the Cases 16/21 pattern.
- **"No new tactic variant is present"** added to DISCARD definition — explicitly states the absence of what would trigger MERGE, making the D/M boundary a single check.
- **Labeled rules over prose** in Stage 1 (SAME LESSON DIFFERENT DEGREE, SAME LESSON DIFFERENT PHASE, SPECIFIC INSTANCE OF GENERALIZED ENTRY) — more scannable for flash models than embedded narrative.
- **Success/failure outcome axis** added to Stage 2 KEEP conditions — covers Cases 34/37/39 where the same tactic produces opposite results in different conditions.
- **Calibration cascade** (doubt → D over M, doubt → M over K) and obs_count gravity — corrects the baseline's zero-false-discard, high-false-merge bias.

### What's being tested

The revised prompt will be replayed against the same 50 golden-label cases to measure improvement. The baseline is 78% strict / 80% lenient.

## Prompt v2: Multi-Model Replay Results

### Setup

We replayed the 50 golden-label cases with the revised observation dedup prompt (v2) across five models. The production model (gemini-3.1-flash-lite, thinking=low) served as the primary comparison against the baseline, with four alternative models tested to measure whether the prompt regression was model-specific or systematic.

All runs used `evaluation/experiments/dedup_replay.py`, which re-runs dedup decisions on frozen inputs with a specified model. One model (gemini-3-flash-preview) experienced API stalls mid-run, inflating its wall-clock time; its accuracy is included but timing is not comparable.

### Results

Golden label distribution: D=19, M=6, K=25

| Model | Prompt | Strict | Observations | Strategy | Time |
|---|---|---|---|---|---|
| flash-lite (production) | v1 baseline | **78%** | 72% | 84% | ~52s |
| flash-lite (production) | v2 | 60% (-18) | 48% | 72% | ~52s |
| gemini-3.5-flash | v2 | **74%** | 60% | **88%** | 472s |
| gemini-2.5-flash | v2 | 64% | 44% | 84% | 724s |
| gemini-2.5-pro | v2 | 64% | 56% | 72% | 889s |
| gemini-3-flash-preview | v2 | 66% | 52% | 80% | ~3631s* |

\* gemini-3-flash-preview stalled mid-run; wall-clock time not representative of actual inference speed.

### Decision distribution vs golden

| Model | Pred D | Pred M | Pred K | M Recall |
|---|---|---|---|---|
| Golden truth | 19 | 6 | 25 | — |
| flash-lite v1 baseline | 17 | 9 | 24 | 83% |
| flash-lite v2 | 38 | 1 | 11 | 0% |
| gemini-3.5-flash v2 | 27 | 2 | 21 | 0% |
| gemini-2.5-flash v2 | 23 | 6 | 21 | 0% |
| gemini-2.5-pro v2 | 26 | 6 | 18 | 33% |
| gemini-3-flash-preview v2 | 31 | 3 | 16 | 0% |

### Analysis: the calibration cascade over-corrected

The prompt v2 made things worse, not better. The overall accuracy dropped from 78% to 60% on the production model. The cause is clear from the decision distributions: the calibration cascade ("doubt → D over M, doubt → M over K") effectively eliminated MERGE as a viable decision.

**The over-discard problem.** Flash-lite v2 predicted 38 discards — double the golden count of 19. It achieved 100% D recall (never missed a true discard) but at the cost of 44% K recall — it discarded 13 entries that should have been kept and all 6 that should have been merged. The "obs_count gravity" rule and "specific instance of generalized entry → DISCARD" guidance made the model too aggressive at collapsing entries into existing high-count observations.

**MERGE recall collapsed across all models.** The baseline had 83% M recall (5/6 merges identified correctly). Prompt v2 dropped this to 0% for three of four models. Only gemini-2.5-pro recovered any merge recall (33%, 2/6), likely because its stronger reasoning partially resists the calibration pressure. The "doubt → D over M" rule was too blunt — when the model was uncertain between D and M, the calibration always pushed it to D, but most M cases genuinely are in the "uncertain between D and M" zone.

**2.5-flash: merges in the wrong places.** Uniquely, 2.5-flash predicted 6 merges — but all 6 were false positives (KEEPs misclassified as M). It correctly handled none of the 6 actual merges. This suggests the model is applying the merge heuristic but to the wrong cases — it merges when it detects similar *agent responses* (the Stage 2 "agent's own tactic differs" rule) instead of when the *core lesson* is the same with a variant tactic.

**Strategy points improved for 3.5-flash.** The one bright spot: gemini-3.5-flash reached 88% on strategy points (up from the baseline's 84%). The clearer D/K guidance in the prompt helped strategy point decisions. But observations degraded from 72% to 60%, dragging overall accuracy to 74%.

**More expensive models didn't help.** 2.5-pro (889s, ~15 min) and 2.5-flash (724s, ~12 min) both scored 64% — lower than the much faster 3.5-flash (472s, 74%). The production flash-lite (52s) was 17x faster than 2.5-pro but the prompt v2 was the bottleneck, not the model.

### Root cause: two simultaneous problems

The initial diagnosis pointed to the calibration cascade — "doubt → D over M" eliminated MERGE as a viable decision. All five models produced 0-33% M recall against the golden labels' 6 MERGE cases. We hypothesized the calibration override was suppressing correct MERGE predictions and planned prompt v3 to soften it.

This turned out to be half right and half wrong. Two problems were entangled:

1. **The calibration cascade was too aggressive** (correctly diagnosed). Flash-lite v2 predicted 38 discards, double the golden count. The "doubt → D over M" rule and obs_count gravity created a ratchet that collapsed everything into existing entries.
2. **The golden labels themselves were wrong** (not yet diagnosed). Four of the six MERGE labels were incorrect. The models were "failing" on cases that were actually mislabeled — their consistent disagreement with MERGE was signal, not noise.

We couldn't see problem #2 until we revisited the golden labels directly, prompted by the suspiciously uniform M recall failure across all five models.

## Golden Label Revision

### The observation that triggered re-examination

Every model — from the cheapest (flash-lite, ~52s) to the most expensive (2.5-pro, ~889s) — independently decided the same 4-5 MERGE cases should not be merges. When five models with different architectures and capabilities all "fail" on the same cases in the same way, the most parsimonious explanation is that the labels are wrong.

### Case-by-case review

We re-examined all 6 MERGE-labeled cases against three principles derived from the prompt improvement work:

1. **Same situation structure for MERGE.** MERGE requires the entries to share the same functional situation, not just the same topic. A general "wolves target leaders" observation and a specific "wolves target the Investigator using indirect evidence" observation have different triggering situations — different detection signals the agent must learn independently.

2. **MERGE enriches general with concrete.** MERGE's value is adding a specific tactic variant to an existing general pattern: the new entry adds a concrete instance (e.g., "questioning healer save choices" added to "wolves use misdirection in endgame"). The direction matters — merging specifics INTO a general pattern, not merging two equally specific entries.

3. **DISCARD means the existing entry covers everything.** "Covers everything" is about information content, not verbosity. A shorter, more general existing entry can fully cover a longer, more specific new entry if the specific details don't change what the agent would do. The question is whether the new entry adds information the existing entry lacks, not whether it's more or less detailed.

Results of the review:

| Case | Old Label | New Label | Reason |
|---|---|---|---|
| 1 | M | **D** | New entry adds "2 saves" vs existing "3 saves" — degree, not kind. Same lesson. |
| 17 | M | **K** | Different triggering situation: Investigator killed → analyze voting records vs wolf eliminated → analyze records. Different game events initiate the same analysis. |
| 18 | M | **K** | Coordinated two-wolf challenge is a structurally distinct triggering event from solo wolf challenge. |
| 19 | M | M | Correct MERGE: specific tactic (questioning healer save choices) enriches general pattern. |
| 20 | M | M | Correct MERGE: specific approach variant adds detail to same-situation observation. |
| 23 | M | **D** | Same find-and-die Investigator pattern. Existing entry (obs=3) already generalizes this well. |

Four of six MERGE labels changed: 2 became DISCARD, 2 became KEEP. The two surviving MERGEs (Cases 19, 20) were the only cases where a specific tactic variant genuinely enriched an existing general pattern — the narrow band that MERGE is designed to capture.

### Revised golden label distribution (first 50 cases)

| Label | Original | Revised | Change |
|---|---|---|---|
| D (Discard) | 19 | 21 | +2 (from M) |
| M (Merge) | 6 | 2 | -4 |
| K (Keep) | 25 | 27 | +2 (from M) |

### What this means for MERGE

MERGE is genuinely rare — 2 out of 50 cases (4%). An exhaustive search of all 21 observation cases in the dataset with the highest MERGE potential (item_type=observation with legacy decision B) found zero additional true MERGEs beyond the 2 already labeled. The narrow band between "same lesson, discard" and "different lesson, keep" leaves very little room for "same lesson, but with a novel tactic variant worth incorporating."

This rarity is structural, not accidental. For a case to be a true MERGE, it must satisfy three constraints simultaneously: (1) same functional situation as an existing entry, (2) same outcome direction, AND (3) a concrete tactic variant not already captured. Most cases that satisfy (1) and (2) also fail (3) because the existing entry already generalizes the pattern.

### Re-scored results with revised golden labels

Re-scoring all prior replays against the revised labels changes the accuracy picture substantially.

| Model | Prompt | Old Strict | **Revised Strict** | Obs | Strat |
|---|---|---|---|---|---|
| baseline v1 (2.5-flash) | v1 | 78% | **72%** | 60% | 84% |
| flash-lite | v2 | 60% | **64%** | 56% | 72% |
| **3.5-flash** | **v2** | 74% | **80%** | 72% | 88% |
| 2.5-flash | v2 | 64% | **68%** | 52% | 84% |
| 2.5-pro | v2 | 70% | **70%** | 68% | 72% |
| flash-lite | v3 | 56% | **62%** | 52% | 72% |
| 3.5-flash | v3 | 72% | **78%** | 68% | 88% |

The most striking change: **3.5-flash + prompt v2 rose from 74% to 80%**, surpassing the baseline's revised 72%. Its "failure" to predict MERGE was actually correct — it was correctly calling D or K on cases that the golden labels had wrong. The v2 prompt's calibration cascade, which we blamed for over-discarding, was partially vindicated: it correctly suppressed MERGE for the 4 mislabeled cases, and its D/K decisions on those cases were right.

The baseline dropped from 78% to 72% — the original model's MERGE predictions on Cases 1 and 23 (now labeled D) and Cases 17 and 18 (now labeled K) were counted as correct under old labels but wrong under revised ones.

This reframes the experiment. The prompt v2 didn't universally regress — it regressed on flash-lite (64% revised vs 72% baseline) but improved on 3.5-flash (80% vs 72%). The calibration cascade works when paired with a model strong enough to handle the D/K distinction underneath it.

## Prompt v3-v5: Structural Iterations

Despite the golden label revision showing v2 was better than initially thought, we continued iterating to improve observation accuracy. Each iteration tested a specific hypothesis about the prompt structure.

### v3: Softening the calibration (50 cases)

**What changed.** Removed "doubt → D over M" calibration. Softened obs_count gravity to allow MERGE even for high-count entries. Kept the two-stage test structure.

**Why.** The initial (pre-revision) analysis showed 0% M recall across most models, attributed to the calibration cascade being too aggressive.

**What happened.** Flash-lite v3: 62% (vs 64% v2). 3.5-flash v3: 78% (vs 80% v2). Both slightly worse. Softening the calibration didn't help because the remaining M errors were on cases that were actually mislabeled (not yet revised at this point). The underlying Stage 1 structure still had a problem: it decided "DISCARD vs everything else," which meant both D and M cases went to DISCARD before Stage 2 could consider MERGE.

### v4: Restructuring the decision stages (50 cases)

**What changed.** Reversed Stage 1 to gate KEEP (different trigger) vs same-pattern (D or M). Stage 2 then decides D vs M for same-pattern cases. Added "doubt → M over K" calibration to prevent the new structure from over-keeping.

**Why.** The v2/v3 structure made Stage 1 decide "D vs not-D," which short-circuited MERGE consideration — both D and M are "same lesson" cases, so Stage 1 always chose DISCARD before reaching Stage 2. The fix was to make Stage 1 only gate KEEP (structurally different) vs same-pattern, then let Stage 2 handle the D/M split.

**What happened.** Flash-lite v4: **40%** — the worst of all iterations. The M calibration swung too far: flash-lite predicted 25 merges (golden has 2), with observation accuracy cratering to 8%. Every non-KEEP observation case was predicted as MERGE. The "doubt → M over K" rule was as damaging as the original "doubt → D over M" — calibration overrides that push toward a rare label create massive false-positive rates because most "doubted" cases aren't that rare label.

### v5: Removing aggressive calibration (65 cases)

**What changed.** Removed "doubt → M over K" calibration. Added "MERGE is the rarest outcome" framing. Kept the restructured stages (Stage 1 gates KEEP, Stage 2 gates D/M). Clarified DISCARD as a subset test: "If the existing entry already covers everything in the new entry, DISCARD — regardless of relative detail level."

**Why.** v4 proved that calibration overrides don't work — they create ratchets regardless of direction. The structural change (Stage 1 gates KEEP) was sound in principle; the problem was the calibration layered on top.

**What happened.** Tested on the expanded 65-case set (see below). Flash-lite v5: **56.9%** (obs 47.5%, strat 72%). 3.5-flash v5: **40.0%** (obs 32.5%, strat 52%). Both dramatically worse than v2. The restructured stages hurt both models, but 3.5-flash was especially damaged — dropping from its v2 peak of 80% to 40%.

The v5 results revealed a deeper problem with the structural change: **forcing explicit MERGE consideration increases MERGE predictions**. In v2, the model could go straight to DISCARD without ever evaluating whether a case qualifies for MERGE. In v5, every non-KEEP case passes through the D/M decision in Stage 2, giving the model too many opportunities to choose M. Flash-lite v5 predicted 19 merges (golden: 2); 3.5-flash v5 predicted 14. The "MERGE is the rarest outcome" framing wasn't strong enough to counteract the structural invitation to merge.

For 3.5-flash, the damage was even worse: strategy point accuracy dropped from 88% (v2) to 52% (v5), with errors scattering in both directions — 5 D→K errors and 6 K→D errors. The v5 prompt structure confused the model's D/K judgment on strategy points, which v2 handled cleanly.

## Expanded Eval Set

After the golden label revision, we expanded the eval set from 50 to 65 cases to increase statistical coverage and test whether the accuracy patterns held on unseen data. The additional 15 cases were drawn from the full 390-case dataset, selected to cover a range of item types and difficulty levels.

Human review found the 15 new cases were cleaner than the original 50 — 10 clear discards, 5 clear keeps, 0 merges. No borderline M cases were found, further confirming MERGE's rarity.

**Revised golden label distribution (all 65 cases):** D=31, M=2, K=32

## Final Results

The best configuration remains **3.5-flash + prompt v2** at 80% strict accuracy on 50 cases. However, this configuration was not re-run on the expanded 65-case set. The 65-case results for v5 are uniformly poor.

### 50-case comparison (revised golden labels, D=21, M=2, K=27)

| Model | Prompt | Strict | Observations | Strategy |
|---|---|---|---|---|
| baseline v1 (2.5-flash) | v1 | 72% | 60% | 84% |
| flash-lite | v2 | 64% | 56% | 72% |
| **3.5-flash** | **v2** | **80%** | **72%** | **88%** |
| 2.5-flash | v2 | 68% | 52% | 84% |
| 2.5-pro | v2 | 70% | 68% | 72% |
| flash-lite | v3 | 62% | 52% | 72% |
| 3.5-flash | v3 | 78% | 68% | 88% |
| flash-lite | v4 | 40% | 8% | 72% |

### 65-case comparison (revised golden labels, D=31, M=2, K=32)

| Model | Prompt | Strict | Observations | Strategy |
|---|---|---|---|---|
| baseline v1 (2.5-flash) | v1 | 67.7% | 57.5% | 84% |
| flash-lite | v5 | 56.9% | 47.5% | 72% |
| 3.5-flash | v5 | 40.0% | 32.5% | 52% |

The baseline's drop from 72% (50-case) to 67.7% (65-case) is expected — the additional 15 cases include harder examples. But v5 drops further, confirming it's not just harder data.

## Decision and Tradeoffs

**The v2 prompt is the best we've found.** Combined with 3.5-flash, it achieves 80% strict accuracy on 50 cases — the only configuration to beat the baseline. Three iterations of structural prompt changes (v3, v4, v5) all made things worse.

**Reverting to v2 is the right move, but we should keep the v5 prompt live.** The v5 prompt has cleaner definitions and better-structured decision logic. The v2 prompt's advantage comes from its calibration cascade accidentally matching the true MERGE rate — not from inherently better prompt engineering. In production, the pipeline runs flash-lite (not 3.5-flash), where v2's advantage over v5 is smaller (64% vs 57%). Neither is good enough to justify a model change in production — both have ~60% accuracy on the production model.

**The larger issue: observation dedup accuracy is capped by MERGE ambiguity.** Strategy point accuracy is consistently high (72-88%) because the D/K binary is clean. Observation accuracy is consistently low (32-72%) because the D/M/K decision space introduces a rare, ambiguous category (MERGE at ~3%) that models can't reliably distinguish from D or K. The auto-discard threshold at 0.90 similarity handles clear duplicates; the LLM handles clear KEEPs; the middle zone (0.55-0.90 similarity) is where errors concentrate.

**The acceptable tradeoff.** Over-discarding is cheaper than over-keeping. A lost observation will be re-extracted from a future game. A duplicate observation pollutes retrieval permanently. The current system already has the auto-discard threshold as a safety net for high-similarity cases. The LLM dedup layer adds value primarily for the D/K distinction at moderate similarity, where both the baseline and v2 prompts perform reasonably (60-72% obs accuracy).

## Lessons

**When all your models "fail" on the same cases, check the labels first.** Five models spanning three generations independently produced 0% MERGE recall on 4 cases. The initial diagnosis was "calibration cascade over-correction" — a prompt-level explanation. The actual cause was mislabeled golden data. Uniform cross-model failure is stronger evidence of label error than of prompt error, because prompt deficiencies tend to produce model-specific failure patterns.

**Calibration overrides create ratchets regardless of direction.** "Doubt → D over M" eliminated true merges. "Doubt → M over K" (v4) created 25 false merges. Both failed for the same structural reason: when a rare label (M at 3%) is the target of a calibration override, the false-positive rate swamps the correction because most "doubted" cases are not that rare label. The override pushes the model away from its best judgment at exactly the boundary where judgment matters most.

**Forcing explicit consideration of a rare option increases its false-positive rate.** The v2→v5 prompt restructuring moved MERGE from an implicit possibility (the model could choose it) to an explicit decision gate (Stage 2 forces a D/M choice for every same-pattern case). This increased M predictions from 1-2 (v2) to 14-19 (v5) despite adding "MERGE is the rarest outcome" framing. For rare decisions, implicit availability outperforms explicit decision gates — the model should be able to reach M but shouldn't be required to explicitly reject it for every case.

**Stronger models don't compensate for prompt regressions, but they amplify prompt improvements.** Flash-lite showed only modest variation across prompt versions (40-64%). 3.5-flash showed dramatic variation: 80% with v2 but 40% with v5. The stronger model extracted more value from the v2 calibration cascade but was also more sensitive to the v5 structural change. This means prompt improvements paired with model upgrades have multiplicative potential, but prompt regressions are also amplified.

**Golden label iteration is part of the eval process, not a failure of it.** The initial 50-case labeling produced 6 MERGE labels. After cross-model validation, 4 were corrected. The corrections didn't invalidate the evaluation — they strengthened it by producing a more reliable ground truth. Treating golden labels as immutable ignores that the labeling process involves the same ambiguity the LLM faces. The right workflow is: label → score → investigate uniform failures → revise labels → re-score.

## What's Next

1. **Revert to v2 prompt.** The v5 structural changes degraded accuracy. The v2 prompt with its calibration cascade is the best-performing version — revert the observation dedup prompt in `Agents/prompts/dedup.py`.
2. **Evaluate 3.5-flash as production model.** 3.5-flash + v2 achieves 80% vs flash-lite's 64%. The cost/latency tradeoff (~8x slower) may be worth the accuracy gain. Run a cost comparison and check whether the latency increase is acceptable for per-extraction dedup.
3. **Run 3.5-flash + v2 on expanded 65-case set.** The 80% figure is on 50 cases. Validate that it holds on the full 65-case set before committing to a model change.
4. **Consider removing MERGE for observations.** Strategy points already don't support MERGE, and their accuracy is consistently higher. If observation MERGE is genuinely ~3% of cases, removing it simplifies the decision to binary D/K — which may improve accuracy by eliminating the ambiguous middle ground that causes most errors.

## Artifacts

| File | Description |
|---|---|
| `eval_sets/dedup_v2_golden_labels.json` | 65 golden labels (D:31, M:2, K:32) with `also_acceptable` for borderline cases |
| `eval_sets/dedup_v2_sampled.jsonl` | 65 sampled dedup cases (source dataset, expanded from 50) |
| `eval_sets/dedup_v2.manifest.json` | Dataset manifest (390 cases, seed=42) |
| `evaluation/experiments/dedup_score.py` | Deterministic golden-label scorer |
| `evidence/dedup_golden_eval/dedup_score_original_v2.json` | Original baseline scoring (78% strict, old labels) |
| `evidence/dedup_golden_eval/tricky_cases.md` | 7 mislabeled cases with full text and prompt improvement suggestions |
| `evidence/dedup_golden_eval/dedup_prompt_baseline.py` | Frozen baseline prompts (pre-revision) |
| `evidence/dedup_golden_eval/standards_baseline.py` | Frozen situation standards and epistemic status rule |
| `evidence/dedup_golden_eval/observation_prompt_draft_v2.md` | Draft 1: narrative style with worked examples |
| `evidence/dedup_golden_eval/observation_prompt_draft_v2_merged.md` | Draft 2: merged structural version |
| `eval_sets/dedup_v2_replay_flash_lite_prompt_v2.jsonl` | Replay: flash-lite, prompt v2 (50 cases) |
| `eval_sets/dedup_v2_replay_35flash_prompt_v2.jsonl` | Replay: 3.5-flash, prompt v2 (50 cases) |
| `eval_sets/dedup_v2_replay_25flash_prompt_v2.jsonl` | Replay: 2.5-flash, prompt v2 (50 cases) |
| `eval_sets/dedup_v2_replay_25pro_prompt_v2.jsonl` | Replay: 2.5-pro, prompt v2 (50 cases) |
| `eval_sets/dedup_v2_replay_3flash_prompt_v2.jsonl` | Replay: 3-flash-preview, prompt v2 (50 cases) |
| `eval_sets/dedup_v2_replay_flash_lite_prompt_v3.jsonl` | Replay: flash-lite, prompt v3 (50 cases) |
| `eval_sets/dedup_v2_replay_35flash_prompt_v3.jsonl` | Replay: 3.5-flash, prompt v3 (50 cases) |
| `eval_sets/dedup_v2_replay_flash_lite_prompt_v4.jsonl` | Replay: flash-lite, prompt v4 (50 cases) |
| `eval_sets/dedup_v2_replay_flash_lite_prompt_v5.jsonl` | Replay: flash-lite, prompt v5 (65 cases) |
| `eval_sets/dedup_v2_replay_35flash_prompt_v5.jsonl` | Replay: 3.5-flash, prompt v5 (65 cases) |
| `eval_results/dedup_v2_flash_lite_prompt_v2.json` | Score: flash-lite v2 (64%, revised labels) |
| `eval_results/dedup_v2_35flash_prompt_v2.json` | Score: 3.5-flash v2 (80%, revised labels) |
| `eval_results/dedup_v2_25flash_prompt_v2.json` | Score: 2.5-flash v2 (68%, revised labels) |
| `eval_results/dedup_v2_25pro_prompt_v2.json` | Score: 2.5-pro v2 (70%, revised labels) |
| `eval_results/dedup_v2_3flash_prompt_v2.json` | Score: 3-flash-preview v2 (66%, old labels) |
| `eval_results/dedup_v2_flash_lite_prompt_v3.json` | Score: flash-lite v3 (62%, revised labels) |
| `eval_results/dedup_v2_35flash_prompt_v3.json` | Score: 3.5-flash v3 (78%, revised labels) |
| `eval_results/dedup_v2_flash_lite_prompt_v4.json` | Score: flash-lite v4 (40%, revised labels) |
| `eval_results/dedup_v2_baseline_revised.json` | Score: baseline v1 on 65 cases (67.7%, revised labels) |
| `eval_results/dedup_v2_flash_lite_prompt_v5.json` | Score: flash-lite v5 on 65 cases (56.9%, revised labels) |
| `eval_results/dedup_v2_35flash_prompt_v5.json` | Score: 3.5-flash v5 on 65 cases (40.0%, revised labels) |
