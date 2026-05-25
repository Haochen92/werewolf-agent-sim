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

## Artifacts

| File | Description |
|---|---|
| `eval_sets/dedup_v2_golden_labels.json` | 50 golden labels (D:19, M:6, K:25) with `also_acceptable` for borderline cases |
| `eval_sets/dedup_v2_tricky_cases.md` | 7 mislabeled cases with full text, tension analysis, and prompt improvement suggestions |
| `eval_sets/dedup_v2_sampled.jsonl` | 50 sampled dedup cases (source dataset) |
| `eval_sets/dedup_v2.manifest.json` | Dataset manifest (390 cases, seed=42) |
| `evidence/dedup_golden_eval/dedup_score_original_v2.json` | Baseline scoring results (78% strict, 80% lenient) |
| `evaluation/experiments/dedup_score.py` | Deterministic golden-label scorer |
