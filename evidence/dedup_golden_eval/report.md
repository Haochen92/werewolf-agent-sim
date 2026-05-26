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

**Revised golden label distribution (all 65 cases, after round 2 revision):** D=30, M=5, K=29, M/K=1

## Final Results

The best configuration is **3.5-flash + prompt v8** at 80.0% strict accuracy on the full 65-case set.

### Full comparison (65 cases, current golden labels: D=30, M=5, K=29, M/K=1)

| Model | Prompt | Accuracy | D recall | K recall | M recall |
|---|---|---|---|---|---|
| flash-lite | v5 | 60.0% | 70% | 45% | 80% |
| flash-lite | v6 | 67.7% | 93% | 41% | 60% |
| flash-lite | v7 | 69.2% | 77% | 55% | 100% |
| flash-lite | v8 | **69.2%** | 83% | 52% | 80% |
| 3.5-flash | v5 | 72.3% | 70% | 76% | 60% |
| 3.5-flash | v6 | 75.4% | 90% | 66% | 40% |
| 3.5-flash | v7 | 75.4% | 60% | 93% | 60% |
| **3.5-flash** | **v8** | **80.0%** | **77%** | **90%** | 40% |

3.5-flash v8 achieves the best balance: 77% D recall and 90% K recall, with 88% strategy point accuracy and 75% observation accuracy. Flash-lite v8 (69.2%) is verified deterministic at temperature 0 (5 identical runs).

## Prompt v6: Flat Prompt with Calibration Cascade (65 cases)

### What changed

Rather than iterating further on the two-stage structure (v2-v5), we reverted to a flat single-pass prompt — closer to the original v1 structure but incorporating the content-level insights from v2. The key additions:

- **Dimensional situation comparison** for observations: information landscape, consensus texture, agent exposure, game phase — each with explicit guidance on when a dimension difference makes situations "different."
- **Calibration cascade**: "When uncertain: prefer D over M, and M over K." This was the v2 insight that worked on 3.5-flash: a gentle nudge toward the more conservative decision.
- **Clearer MERGE definition**: MERGE requires same situation + same outcome + different tactic variant. The "different tactic variant" criterion was sharpened: different tactic *category* (accusation vs deflection), not different wording of the same tactic.

### Why

v3-v5 showed that structural changes to the prompt (two-stage decision gates, explicit MERGE consideration) consistently hurt accuracy. The calibration cascade worked when embedded in a flat structure (v2) but failed when combined with structural gates (v4, v5). The hypothesis: return to a flat prompt, keep the good content from v2's definitions, and let the calibration cascade do its work without structural interference.

### Results

| Model | Prompt | Accuracy | D recall | K recall | M recall |
|---|---|---|---|---|---|
| flash-lite | v5 | 60.0% | 70% | 45% | 80% |
| flash-lite | **v6** | **67.7%** | **93%** | 41% | 60% |
| 3.5-flash | v5 | 72.3% | 70% | 76% | 60% |
| 3.5-flash | **v6** | **75.4%** | **90%** | 66% | 40% |

v6 improved overall accuracy for both models (+7.7pp flash-lite, +3.1pp 3.5-flash). The pattern was clear: D recall jumped dramatically (70%→93% flash-lite, 70%→90% 3.5-flash) but K recall suffered (45%→41% flash-lite, 76%→66% 3.5-flash).

**The calibration cascade worked exactly as designed — too well.** "Prefer D over M, M over K" created a ratchet that pushed uncertain cases toward D. Since many K cases sit in the "uncertain between D and K" zone (similarity 0.55-0.85), the cascade systematically consumed them. Flash-lite's 41% K recall meant it was discarding more than half of genuinely novel entries.

## Golden Label Revision: Round 2

### Motivation

The v6 results exposed a new signal: we had 32 cases where at least one model (flash-lite or 3.5-flash, using v6 prompt) disagreed with the golden label. Some of these were genuine model errors, but the v5→v6 accuracy jump (after the first golden label revision) taught us that model disagreements sometimes expose label errors. We reviewed all 32 disagreement cases one-by-one with full text.

### Process

Each of the 32 cases was examined with complete text for the new entry and all relevant candidates. The review applied the retrieval test as the primary criterion for situation comparison: would a semantic search query matching situation A also retrieve situation B? This test hadn't been fully internalized during the first labeling round.

### Results: 10 labels changed

| Case | Old | New | Key reason |
|---|---|---|---|
| 8 | D | **K** | Different agent position: confirmed non-wolf with high credibility vs general villager under suspicion |
| 16 | M | **M/K** | Genuinely ambiguous — either interpretation defensible |
| 17 | D | **D** | Confirmed after full review (no change) |
| 18 | K | **K** | Confirmed (no change) |
| 27 | D | **K** | Aggressive player might be frustrated Investigator — distinct situational scope |
| 29 | D | **K** | Behavioral test + meta-accusation = distinct action from simple challenge |
| 34 | D | **K** | Same approach, opposite outcome (success vs failure) — teaches risk/reward |
| 36 | D | **K** | Different triggering situation despite surface similarity |
| 37 | D | **K** | Success vs failure of same approach |
| 38 | K | **M** | Same situation, different target choice = tactic variant |

### Revised golden label distribution (65 cases)

| Label | Previous | Revised | Change |
|---|---|---|---|
| D (Discard) | 31 | 30 | -1 |
| M (Merge) | 2 | 5 | +3 |
| K (Keep) | 32 | 29 | -3 |
| M/K (either acceptable) | 0 | 1 | +1 |

MERGE increased from 2 to 5 cases — still rare (~8%) but no longer negligibly small. The M/K label for Case 16 acknowledges genuine ambiguity rather than forcing a single answer.

### Key insights from labeling that informed prompt revision

Six distinct patterns emerged during the case-by-case review:

1. **Retrieval test as ground truth**: The decisive test for "same vs different" situation is whether a semantic search query matching one would also retrieve the other. Two entries teaching the same lesson in semantically different situations must exist separately — otherwise the agent never sees the relevant entry when it needs it.

2. **Confidence posture**: "Treat accusation as ground truth and act immediately" vs "probe to evaluate alignment before committing" point in the same direction but lead to meaningfully different agent behavior → KEEP.

3. **Agent exposure**: Different agent positions (confirmed non-wolf with high credibility vs general villager under suspicion) create different situations even with the same trigger event.

4. **Conflicting strategies**: Opposite actions for the same situation are by definition different hypotheses → KEEP. Both give the agent tactical flexibility.

5. **Success vs failure**: Same approach with opposite outcomes teaches risk/reward → always KEEP.

6. **One-off vs persistent**: 1x vs 2+ crosses the qualitative one-off → persistent threshold (MERGE tactic variant), but 2x vs 3x is just degrees of persistence (DISCARD).

## Prompt v7: Removing the Calibration Cascade (65 cases)

### What changed

Incorporated all six insights from the golden label review into both the observation and strategy prompts:

**Observation prompt:**
- Replaced situation comparison with explicit retrieval test: "would a semantic search query matching situation A also retrieve situation B?"
- Added one-off vs persistent distinction in approach comparison
- Added explicit success vs failure → KEEP in outcome comparison
- Added two new examples (M for one-off→persistent, K for success/failure)
- **Removed the entire CALIBRATION section** — no more "prefer D over M, M over K"

**Strategy prompt:**
- Added new SITUATION COMPARISON section with retrieval test and dimensional checks (information landscape, agent exposure with example, consensus texture, game phase)
- Added confidence posture and conflicting strategies as KEEP examples in DECISION TEST
- **Removed CALIBRATION NOTE** — no more "when in doubt, DISCARD"

### Why

The v6 results showed the calibration cascade killed K recall (41% flash-lite, 66% 3.5-flash). The cascade was a blunt instrument: it applied the same "prefer D" bias to every uncertain case, regardless of whether the uncertainty was genuine (borderline D/K) or false (surface similarity masking genuine novelty). The hypothesis: remove the cascade entirely and rely on the improved decision criteria to guide the model's judgment.

### Results

| Model | v6 Accuracy | v7 Accuracy | v6 D | v7 D | v6 K | v7 K | v6 M | v7 M |
|---|---|---|---|---|---|---|---|---|
| flash-lite | 67.7% | **69.2%** | 93% | 77% | 41% | **55%** | 60% | **100%** |
| 3.5-flash | 75.4% | 75.4% | 90% | 60% | 66% | **93%** | 40% | 60% |

Removing the cascade worked for K recall: flash-lite jumped from 41%→55%, 3.5-flash from 66%→93%. M recall also improved. But D recall dropped sharply: flash-lite 93%→77%, 3.5-flash 90%→60%.

**The pendulum swung too far.** Flash-lite predicted M 16 times (gold: 5) — it was using MERGE as a safe middle ground when uncertain, the mirror image of v6's over-discard. 3.5-flash predicted K too aggressively on cases where the surface situation looked different but the underlying action was the same.

The calibration cascade is a lever with no neutral position: present = over-discard, absent = over-merge/over-keep. The next iteration targets this directly.

## Prompt v8: Targeted Anti-Merge Calibration (65 cases, in progress)

### What changed

Added narrow calibration notes to both prompts, targeting the specific failure modes exposed by v7:

**Observation prompt:** "MERGE requires a clearly distinct tactic variant — a different category of action, not a different description of the same action. If you are unsure whether the approach difference is a genuine tactic variant or just different wording, choose DISCARD."

**Strategy prompt:** "Focus on what the agent would DO, not on how the entries are worded. If both entries point the agent toward the same target, timing, and risk tradeoff, they are the same hypothesis — DISCARD, even if the reasoning or phrasing differs."

### Why

v7's error analysis showed two distinct failure modes:

1. **Observation D→M errors** (4 cases): flash-lite saw minor wording differences in the approach field and called them "tactic variants" warranting MERGE. E.g., "protect the vocal player" vs "protect the accusatory player" — same action, different description. The calibration targets this: MERGE requires a different *category* of action.

2. **Strategy D→K errors** (8 cases for 3.5-flash): the model saw different reasoning or phrasing and concluded the hypotheses were different, even when the recommended action was identical. The calibration targets this: focus on what the agent would *do*, not on how the advice is *worded*.

These are surgical corrections, not directional cascades. They don't say "prefer D over everything" — they say "this specific type of difference is not enough for M" and "this specific type of difference is not enough for K."

### Results

| Model | v7 Accuracy | v8 Accuracy | v7 D | v8 D | v7 K | v8 K | v7 M | v8 M |
|---|---|---|---|---|---|---|---|---|
| flash-lite | 69.2% | 69.2% | 77% | **83%** | 55% | 52% | 100% | 80% |
| 3.5-flash | 75.4% | **80.0%** | 60% | **77%** | 93% | 90% | 60% | 40% |

**3.5-flash v8 at 80.0% is the best configuration on the full 65-case set.** The targeted calibration recovered D recall (60%→77%, +17pp) while barely touching K recall (93%→90%, -3pp). Strategy point accuracy reached 88% (22/25), observation accuracy 75% (30/40). This is the sweet spot: the calibration note addresses the specific D→K failure mode (same action described differently) without creating a general bias.

**Flash-lite v8 ties with v7 at 69.2%** but with a healthier internal balance: D recall recovered 6pp while K and M dropped modestly. Flash-lite's K recall (52%) remains its ceiling problem — it over-discards genuinely novel entries regardless of prompt version, consistently classifying 9 of 29 K cases as D. The remaining 20 errors are spread: 4 D→M (over-merge on same-action cases), 5 K→M (treating distinct situations as tactic variants), and 6 K→D (collapsing genuinely different entries).

**The targeted calibration works better than directional cascades.** "MERGE requires a clearly distinct tactic variant" is a criterion, not a bias — it tells the model what M means, not to avoid M. "Focus on what the agent would DO" grounds the D/K distinction in behavior, not wording. These surgical corrections recovered D recall without the ratchet effect that killed K in v6.

## Cost and Latency Analysis: flash-lite vs 3.5-flash

### Pricing (per 1M tokens, paid tier)

| Model | Input | Output (incl thinking) |
|---|---|---|
| flash-lite 3.1 | $0.25 | $1.50 |
| 3.5-flash | $1.50 | $9.00 |

Per-token ratio: 6x for both input and output.

### Per-game economics

The dedup pipeline runs ~15.6 LLM calls per game (390 spans across 25 games in the eval dataset). Each call sends ~1,163 input tokens (new entry + candidates) and receives ~200 output tokens. Flash-lite additionally generates ~400 thinking tokens per call (thinking=low mode).

| Dimension | flash-lite | 3.5-flash | Delta |
|---|---|---|---|
| Cost/case | $0.0012 | $0.0035 | 3x |
| Cost/game (15.6 cases) | $0.019 | $0.055 | 3x |
| Cost/1000 games | $18.58 | $55.29 | +$36.72 |
| Latency/case | ~1s | ~7s | 7x |
| Latency/game | ~15s | ~109s | +94s |

The per-case ratio is 3x (not 6x) because flash-lite's thinking tokens inflate its output cost, narrowing the effective gap.

### What the accuracy gap costs in practice

Per 1000 games (15,600 dedup decisions):

- **Flash-lite (69.2%)**: ~4,805 wrong decisions. K recall at 52% means ~7.3 novel entries wrongly discarded per game.
- **3.5-flash (80.0%)**: ~3,120 wrong decisions. K recall at 90% means ~1.4 novel entries wrongly discarded per game.

The K recall gap (52% vs 90%) is the critical difference. Over-discarded entries from common situations will be re-extracted from future games, but entries from rare game states may be permanently lost. 3.5-flash's lower D recall (77% vs 83%) produces a few extra duplicates, but those are cleaned up by the existing batch dedup pipeline.

### Decision

**Keep flash-lite as the production model.** The 3x cost multiplier and 7x latency increase are meaningful, and flash-lite's accuracy improved with further prompt fine-tuning (see v9/v9d below). The batch dedup pipeline provides a safety net for both over-discard (rare but impactful) and over-keep (common but recoverable).

## Prompt v9/v9d: Strategy-Focused Fine-Tuning (65 cases)

### Diagnosis

v8 flash-lite's 20 errors broke down as:
- **K→D (9)**: 6 strategy_points, 3 observations — biggest problem
- **K→M (5)**: all observations — mis-merging when situation is different
- **D→M (4)**: all observations — over-merging when should discard
- **D→K (1)** and **M→D (1)**: minor

Strategy K→D was the highest-count targetable error. Analysis of the LLM reasoning on cases 32, 42, 48 revealed flash-lite was rationalizing at too high an abstraction level — it sees theme overlap (e.g., "both about voting when partner is doomed") and ignores that the actual actions conflict (vote with majority vs vote for a third target; acknowledge mistake vs deny mistake).

### Experiments tried

| Variant | Change | Overall | Strategy | K recall | Outcome |
|---|---|---|---|---|---|
| v8 (baseline) | — | 69.2% | 72.0% | 52% | — |
| v9 | + DISCARD verification check | 70.8% | 76.0% | 55% | +1 strategy fix (case 8) |
| v9b | + ACTION CHECK in output format | 67.7% | 68.0% | 48% | Regressed — structured output confused flash-lite |
| v9c | + ACTION COMPARISON section (parallel to SITUATION COMPARISON) | 69.2% | 72.0% | 52% | Net zero — added noise, didn't help |
| **v9d** | **v9 + action-before-situation field ordering** | **73.8%** | **84.0%** | **59%** | **+3 more strategy fixes (cases 32, 42, 45)** |

### What changed in v9d (production prompt)

Two changes from v8:

1. **DISCARD verification check** (replaces CALIBRATION): Before choosing DISCARD, the model must verify both (a) situations are functionally the same and (b) recommended actions point in the same direction. If either fails, KEEP.

2. **Action-before-situation field ordering**: In both the new extraction template and existing entries formatting, Action is presented before Situation. This causes flash-lite to anchor on action differences before getting absorbed by situation similarity.

### Why action-first ordering works

Flash-lite's K→D errors on strategy points consistently showed the model noticing situation similarity first and then rationalizing action differences as "tactical variations of the same strategy." By presenting the action field first, the model encounters conflicting advice ("vote with majority" vs "vote for a third target") before it sees the similar situation framing that would cause it to lump them together.

This is a presentation-order effect, not a content change — the same information is shown, just reordered. It specifically helps strategy points where action direction is the key discriminator. It had no effect on observation accuracy (67.5% unchanged) because observation errors are dominated by M calibration issues, not action-direction blindness.

### Results

| Model | v8 | v9d | Delta |
|---|---|---|---|
| flash-lite overall | 69.2% | **73.8%** | +4.6pp |
| flash-lite strategy | 72.0% | **84.0%** | +12.0pp |
| flash-lite observation | 67.5% | 67.5% | 0 |
| flash-lite K recall | 52% | **59%** | +7pp |
| flash-lite K precision | 0.94 | **1.00** | +0.06 |
| 3.5-flash overall | 80.0% | 80.0% | 0 |
| 3.5-flash strategy | 88.0% | 88.0% | 0 |

The v9d changes had no effect on 3.5-flash — it was already at 88% strategy accuracy, leaving no room for improvement on strategy K→D errors.

### Remaining errors (flash-lite v9d, 17 total)

**Strategy (4 errors)**: Cases 8, 27, 29, 48 — K→D where flash-lite still misses genuinely different situations or conflicting actions. These appear to be at the model's capability ceiling for this prompt structure.

**Observation (13 errors)**: 9 of 13 involve M — either over-merging (D→M: 4 cases) or mis-merging when situations differ (K→M: 5 cases). The model is too generous in what it considers a "distinct tactic variant." Tightening M criteria risks breaking the 4/5 correct M predictions; loosening for K→M would worsen D→M. These pull in opposite directions.

### Key lessons from v9 tuning

**Presentation order matters more than explicit instructions.** The DISCARD verification check (v9) helped modestly (+1.6pp), but adding an ACTION COMPARISON section with detailed criteria (v9c) added zero value. The action-first field reorder (v9d) added +3pp on top of v9 — more impact than any textual instruction. For small models, how you present information matters more than how much you explain.

**Structured output requirements can hurt small models.** v9b added an ACTION CHECK field to the output format, forcing flash-lite to explicitly state each entry's core action. This regressed accuracy by -3.1pp, likely because the additional output structure interfered with flash-lite's reasoning flow.

**Observation accuracy appears to be at flash-lite's ceiling.** The 13 observation errors are dominated by M calibration — a problem where the fixes for different error types conflict. Further observation tuning offers diminishing returns without either dropping M from per-extraction dedup or upgrading the model.

## Decision and Tradeoffs

**The prompt has been through four distinct phases**, each teaching a different lesson about calibration:

1. **Phase 1 (v2-v5)**: Structural prompt changes (two-stage decision gates) consistently degraded accuracy. The flat prompt structure is better because it lets the model reason holistically rather than through forced sequential gates.

2. **Phase 2 (v6)**: A flat prompt with a directional calibration cascade ("prefer D over M over K") improved D recall to 93% but crushed K recall to 41%. The cascade is a blunt instrument that can't distinguish genuine uncertainty from false confidence.

3. **Phase 3 (v7-v8)**: Removing the cascade entirely caused over-merge. Targeted calibration (v8) addresses specific failure modes without biasing the overall distribution.

4. **Phase 4 (v9-v9d)**: Presentation-order tuning. Reordering fields (action before situation) had more impact than adding explicit comparison criteria or structured output requirements. For small models, information architecture matters more than instruction volume.

**The model matters as much as the prompt.** 3.5-flash consistently outperforms flash-lite by 6-8pp regardless of prompt version. Flash-lite's K recall reached 59% on v9d (up from a ceiling of 55%), while 3.5-flash sits at 90%. The gap has narrowed from 10.8pp (v8) to 6.2pp (v9d).

**Over-discarding is still cheaper than over-keeping**, but the margin is smaller than we initially assumed. A discarded novel entry will be re-extracted from a future game — but only if a similar game situation occurs. For rare situations, over-discard means permanent information loss. The ideal operating point balances D and K recall, not maximizes one at the expense of the other.

## Lessons

**When all your models "fail" on the same cases, check the labels first.** Five models spanning three generations independently produced 0% MERGE recall on 4 cases. The initial diagnosis was "calibration cascade over-correction" — a prompt-level explanation. The actual cause was mislabeled golden data. Uniform cross-model failure is stronger evidence of label error than of prompt error, because prompt deficiencies tend to produce model-specific failure patterns.

**Calibration cascades create ratchets regardless of direction.** "Doubt → D over M" eliminated true merges (v2). "Doubt → M over K" created 25 false merges (v4). Removing all calibration caused over-merge (v7). The lesson isn't "calibration is bad" — it's that *directional* calibration (prefer X over Y) creates a ratchet that kills the non-preferred category. Targeted calibration ("this specific pattern is not sufficient for X") avoids the ratchet by addressing failure modes directly.

**Forcing explicit consideration of a rare option increases its false-positive rate.** The v2→v5 prompt restructuring moved MERGE from an implicit possibility to an explicit decision gate. This increased M predictions from 1-2 to 14-19 despite adding "MERGE is the rarest outcome" framing. For rare decisions, implicit availability outperforms explicit decision gates.

**Stronger models amplify both prompt improvements and regressions.** Flash-lite showed modest variation across prompt versions (60-69%). 3.5-flash showed dramatic variation: 82% (v2 baseline) to 40% (v5) to 75% (v6-v7). The stronger model extracts more value from good prompts but is also more sensitive to bad ones. This means prompt improvements paired with model upgrades have multiplicative potential.

**Golden label iteration is part of the eval process, not a failure of it.** Two rounds of label revision changed 14 labels total (4 in round 1, 10 in round 2). Each round was triggered by cross-model disagreement analysis. The corrections consistently strengthened the ground truth. The right workflow is: label → score → investigate uniform failures → revise labels → re-score.

**The retrieval test grounds abstract similarity judgments.** "Are these situations the same?" is subjective. "Would a search query for situation A retrieve situation B?" is concrete and testable. This reframing resolved several labeling disagreements and gave the LLM a more operational decision criterion. When building prompts for similarity judgment, anchor to the downstream use case (retrieval) rather than abstract semantic similarity.

## Rewrite Quality Analysis

Judged by gemini-3.1-pro-preview on four dimensions (1-5 scale): decision_correctness, merge_quality, information_preservation, and fabrication_detected (boolean). Cases without rewrites (KEEP or DISCARD-without-rewrite) receive automatic 5s on merge_quality and info_preservation. Two types of rewrite exist: MERGE produces a combined observation (merged situation, approach, outcome), and DISCARD-with-rewrite overwrites the existing strategy point's situation and action fields with improved text from the new entry.

### Flash-Lite v9d

Of 65 cases, 19 produced rewrites: 14 MERGE (all observations) and 5 DISCARD-with-rewrite (all strategy points). 0% fabrication rate.

**MERGE rewrites (14 observation cases)**

| Quality | Count | Cases |
|---|---|---|
| Perfect (mq=5, ip=5) | 8 | 4 gold=K/M/K, 2 gold=M, 2 gold=D — correct merges and compatible false merges |
| Mediocre (ip 3-4) | 4 | 2 gold=D (unnecessary merges), 1 gold=M/K, 1 gold=D |
| Destructive (ip ≤ 2) | 2 | 1 gold=M (ip=2), 1 gold=K (ip=1) |
| **Avg** | | **mq=4.36, ip=4.21** |

Against golden labels, the 14 merges break down as: 4 correct (gold=M, 3 scored ip ≥ 4, 1 scored ip=2), 5 false merges from K (2 destructive, 3 perfect/mediocre), 4 false merges from D (unnecessary rewrites), and 1 ambiguous (gold=M/K).

**DISCARD-with-rewrite (5 strategy point cases)**

| Quality | Count | Cases |
|---|---|---|
| Perfect (mq=5, ip=5) | 2 | Both gold=D or gold=K — correct decisions with clean improvement |
| Mediocre (ip 3-4) | 2 | gold=D (ip=3), gold=K (ip=4) |
| Destructive (ip ≤ 2) | 1 | gold=D (ip=1, mq=1) — overwrote conflicting strategy entirely |
| **Avg** | | **mq=3.80, ip=3.60** |

**Overall: 19 rewrites, avg mq=4.21, ip=4.05. IP distribution: 5:11, 4:3, 3:2, 2:1, 1:2.**

### 3.5-Flash v9d

Of 65 cases, 11 produced rewrites: 5 MERGE (all observations) and 6 DISCARD-with-rewrite (all strategy points). 0% fabrication rate.

**MERGE rewrites (5 observation cases)**

| Quality | Count | Cases |
|---|---|---|
| Perfect (mq=5, ip=5) | 4 | 2 gold=M (correct), 1 gold=K, 1 gold=D |
| Mediocre (ip 3-4) | 1 | gold=K (ip=4) |
| Destructive (ip ≤ 2) | 0 | — |
| **Avg** | | **mq=4.80, ip=4.80** |

3.5-flash produced only 5 merges vs flash-lite's 14 — it correctly avoids most false merges, which eliminates the destructive rewrites entirely.

**DISCARD-with-rewrite (6 strategy point cases)**

| Quality | Count | Cases |
|---|---|---|
| Perfect (mq=5, ip=5) | 4 | All gold=D — correct decisions with clean improvement |
| Mediocre (ip 3-4) | 1 | gold=D (ip=3) — same case (fe46f8eb0ad4) that flash-lite also scored ip=3 |
| Destructive (ip ≤ 2) | 1 | gold=K (ip=2, mq=3) — wrong decision; overwrote a genuinely different strategy |
| **Avg** | | **mq=4.33, ip=4.17** |

**Overall: 11 rewrites, avg mq=4.55, ip=4.45. IP distribution: 5:8, 4:1, 3:1, 2:1.**

### Cross-Model Comparison

| Dimension | Flash-lite (19 rewrites) | 3.5-flash (11 rewrites) |
|---|---|---|
| Avg merge_quality | 4.21 | 4.55 |
| Avg info_preservation | 4.05 | 4.45 |
| Perfect rewrites | 10/19 (53%) | 8/11 (73%) |
| Destructive rewrites | 3/19 (16%) | 1/11 (9%) |
| Fabrication | 0% | 0% |

3.5-flash's advantage is primarily **fewer rewrites, not better rewrites**. When both models rewrite the same case, the quality gap is modest — the shared mediocre case (fe46f8eb0ad4, ip=3 for both) and the shared perfect cases confirm this. 3.5-flash's higher averages come from avoiding the 9 false merges that produce flash-lite's worst scores.

The one case where both models score poorly — fe46f8eb0ad4, a strategy DISCARD-with-rewrite — scores ip=3 on both models. This is a prompt issue, not a model issue: the rewrite instructions don't give enough guidance on what to preserve when improving an existing strategy point's fields.

### When rewrites fail: prompt vs model

The destructive rewrites (ip ≤ 2) fall into two categories:

**Wrong decision → bad rewrite (both models).** Flash-lite's 2 destructive observation merges and 3.5-flash's 1 destructive strategy rewrite all have decision_correctness ≤ 2. The entries were incompatible — combining them was impossible regardless of rewrite instructions. Fixing decision accuracy (the D/M/K prompt) would prevent these.

**Mediocre rewrites on correct decisions (prompt issue).** The shared ip=3 case (fe46f8eb0ad4) has decision_correctness=5 on both models — the decision was right, but the rewrite lost nuance. Flash-lite's 4 mediocre observation merges include 2 correct decisions (gold=D, gold=M/K) where the model combined entries adequately but dropped minor details. The current rewrite instructions say "output the final merged observation fields" and "MUST list ALL distinct tactics" but don't specify how to preserve situational context, outcome nuance, or observation counts during the merge.

## What's Next

1. **Tune rewrite instructions**: The mediocre cases on correct decisions indicate the rewrite prompt section needs improvement. Both models share the same weak case (fe46f8eb0ad4), confirming this is a prompt issue. The merge instruction ("MUST list ALL distinct tactics") addresses approach but not situation or outcome preservation.
2. **Consider dropping M from per-extraction dedup**: Flash-lite produces 9 false merges vs 4 correct ones. Removing M and letting batch dedup handle merging would eliminate the 2 destructive observation rewrites and all false-merge noise.
3. **Revisit model upgrade if further accuracy is needed**: The flash-lite/3.5-flash gap narrowed from 10.8pp to 6.2pp with v9d. If observation accuracy needs to improve beyond what M-removal provides, the model upgrade ($36.72/1000 games) is the remaining lever.

## Artifacts

| File | Description |
|---|---|
| `eval_sets/dedup_v2_golden_labels.json` | 65 golden labels (D:30, M:5, K:29, M/K:1) after two revision rounds |
| `eval_sets/dedup_v2_sampled.jsonl` | 65 sampled dedup cases (source dataset, expanded from 50) |
| `eval_sets/dedup_v2.manifest.json` | Dataset manifest (390 cases, seed=42) |
| `evaluation/experiments/dedup_score.py` | Deterministic golden-label scorer (matches by case_id or index) |
| `scripts/dedup_model_comparison.py` | Multi-file comparison script — scores all replay files and prints table |
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
| `eval_sets/dedup_v2_replay_flash_lite_prompt_v6.jsonl` | Replay: flash-lite, prompt v6 (65 cases) |
| `eval_sets/dedup_v2_replay_35flash_prompt_v6.jsonl` | Replay: 3.5-flash, prompt v6 (65 cases) |
| `eval_sets/dedup_v2_replay_flash_lite_prompt_v7.jsonl` | Replay: flash-lite, prompt v7 (65 cases) |
| `eval_sets/dedup_v2_replay_35flash_prompt_v7.jsonl` | Replay: 3.5-flash, prompt v7 (65 cases) |
| `eval_sets/dedup_v2_replay_flash_lite_prompt_v8.jsonl` | Replay: flash-lite, prompt v8 (65 cases) |
| `eval_sets/dedup_v2_replay_flash_lite_prompt_v8_verified.jsonl` | Replay: flash-lite, prompt v8 verified (5 identical runs confirm determinism) |
| `eval_sets/dedup_v2_replay_35flash_prompt_v8.jsonl` | Replay: 3.5-flash, prompt v8 (65 cases) |
| `eval_sets/dedup_v2_replay_flash_lite_prompt_v9.jsonl` | Replay: flash-lite, prompt v9 (65 cases, 70.8%) |
| `eval_sets/dedup_v2_replay_flash_lite_prompt_v9d.jsonl` | Replay: flash-lite, prompt v9d (65 cases, 73.8% — production) |
| `eval_sets/dedup_v2_replay_35flash_prompt_v9d.jsonl` | Replay: 3.5-flash, prompt v9d (65 cases, 80.0%) |
| `eval_configs/dedup/dedup_v2_judge_v9d.json` | Config: judge flash-lite v9d with gemini-3.1-pro-preview |
| `eval_configs/dedup/dedup_v2_judge_35flash_v9d.json` | Config: judge 3.5-flash v9d with gemini-3.1-pro-preview |
| `eval_results/dedup_judge_flash_lite_v9d.jsonl` | Judge results: flash-lite v9d rewrite quality (19 rewrites) |
| `eval_results/dedup_judge_35flash_v9d.jsonl` | Judge results: 3.5-flash v9d rewrite quality (11 rewrites) |
