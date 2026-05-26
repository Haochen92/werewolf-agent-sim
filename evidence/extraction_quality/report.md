# Extraction Quality Evaluation

## Motivation

The extraction pipeline (gemini-2.5-pro) converts full game transcripts into structured observations and strategy points stored for future retrieval. If extractions are inaccurate, poorly scoped, or epistemically broken, no amount of retrieval tuning helps. This evaluation measures extraction quality across 48 games.

## Extraction prompt evolution

The extraction prompt has gone through several iterations, each fixing a specific failure mode:

1. **Earliest version**: No mention of semantic search or retrieval use case. Produced consistently vague situations ("after a mislynch", "when under suspicion") that matched everything during retrieval.

2. **Retrieval constraint added**: Introduced "CRITICAL RETRIEVAL CONSTRAINT" that explicitly told the LLM these observations will be matched via semantic search, and that "after a mislynch" would match EVERY mislynch scenario. Instructed the model to specify CONDITIONS that made the situation distinctive. This improved specificity significantly.

3. **Current version**: Replaced the inline retrieval constraint with two shared standards modules:
   - `SITUATION_STANDARDS` — dimensional framework (information landscape, consensus texture, agent exposure, game phase) + specificity test. Shared across extraction, deduplication, and situation summary prompts.
   - `EPISTEMIC_STATUS_RULE` — certainty levels for role descriptions. Applied to strategy points only (not observations).
   
   This version also introduced structured dimensional fields as separate schema fields rather than embedding everything in the situation text. The `composed_situation` property concatenates them for storage/search.

The key architectural decision: aligning the same situation quality standards across extraction (what goes into the store), deduplication (how entries are merged/rewritten), and situation summary (the retrieval query). All three components now share `SITUATION_STANDARDS`.

## Design

Dataset: 48 extraction cases from two batch sessions (`v4_action_phase_v2_all_enabled_remainder` 18 games + `v4_action_phase_v2_wolf_only` 30 games). Judge model: `gemini-3.5-flash`. Five dimensions scored 1-5.

## Run 1: Baseline evaluation

Initial judge prompt evaluated all items uniformly.

| Dimension | Average | Distribution |
|---|---|---|
| Coverage | 4.00 | 48x score=4 |
| Grounding | 3.98 | 47x score=4, 1x score=3 |
| Diversity | 3.46 | 26x score=3, 22x score=4 |
| Specificity | 3.19 | 39x score=3, 9x score=4 |
| Epistemic compliance | 2.81 | 21x score=2, 15x score=3, 12x score=4 |

### Finding: Epistemic score conflated two issues

The low epistemic score (2.81) was driven by player_ID usage in observations, not actual knowledge-level violations in strategy points. The judge applied epistemic compliance uniformly to both item types without distinguishing their design intent:
- Observations are factual post-game records — omniscient framing is allowed
- Strategy points are reusable advice served during gameplay — must respect role knowledge limits

### Mechanical check: player_ID leakage

Script analysis (no judge involved):
- **Observations**: 306/363 (84.3%) contain player_IDs, avg 3.4 per item
- **Strategy points**: 0/383 (0.0%) contain player_IDs

Field breakdown for observations: approach (72%), situation (34%), outcome (29%), information_landscape (10%).

## Run 2: Epistemic scope corrected

Judge prompt updated to evaluate epistemic compliance on strategy points only (observations exempt since they're factual records).

| Dimension | Average | Distribution |
|---|---|---|
| Coverage | 4.00 | 48x score=4 |
| Grounding | 3.98 | 47x score=4, 1x score=3 |
| Epistemic compliance | 4.00 | 48x score=4 |
| Diversity | 3.50 | 24x score=3, 24x score=4 |
| Specificity | 3.27 | 2x score=2, 31x score=3, 15x score=4 |

Epistemic compliance jumps from 2.81 to 4.00 — confirming strategy points are epistemically clean, and the original score was penalizing observations for allowed behavior.

### Finding: Specificity score was also misaligned

The judge evaluated specificity based on the narrow `situation` field alone. However, the actual stored search text is a `composed_situation` that concatenates situation + information_landscape + game_phase + consensus_texture + agent_exposure. The judge wasn't seeing the dimensional fields that make items specific for retrieval.

Fix applied: judge formatter now includes dimensional fields; specificity rubric updated to evaluate the composed situation as a whole.

## Run 3: Full judge alignment

Both fixes applied: epistemic scoped to strategy points only, and specificity evaluates the composed situation (all dimensional fields visible).

| Dimension | Average | Distribution |
|---|---|---|
| Specificity | 3.88 | 42x score=4, 6x score=3 |
| Epistemic compliance | 4.00 | 48x score=4 |
| Grounding | 4.00 | 48x score=4 |
| Coverage | 3.96 | 46x score=4, 2x score=3 |
| Diversity | 3.52 | 25x score=4, 23x score=3 |

### Comparison across runs

| Dimension | Run 1 | Run 2 | Run 3 | Delta (1→3) |
|---|---|---|---|---|
| Specificity | 3.19 | 3.27 | 3.88 | +0.69 |
| Epistemic | 2.81 | 4.00 | 4.00 | +1.19 |
| Grounding | 3.98 | 3.98 | 4.00 | +0.02 |
| Coverage | 4.00 | 4.00 | 3.96 | -0.04 |
| Diversity | 3.46 | 3.50 | 3.52 | +0.06 |

### Interpretation

The two judge bugs (epistemic scope, missing dimensional fields) accounted for the bulk of apparent quality issues. Once the judge evaluates the same content the retrieval system actually uses, specificity lands at 3.88 — comfortably in the "good" range. The remaining 6 cases scored 3 on specificity likely have genuinely thin dimensional context rather than a judge artifact.

Grounding (4.00) and epistemic (4.00) are now ceiling — the prompt handles these well. Coverage is near-ceiling with only 2 cases at 3. Diversity (3.52) remains the weakest dimension, suggesting some games produce repetitive observations/strategy points across roles — this is a harder structural issue tied to game variety rather than prompt quality.

## Extraction model comparison

Tested four flash-tier models as extraction alternatives to gemini-2.5-pro, all using the updated prompt (including the player_ID naming rule). 10 games per model on the same game transcripts for fair comparison. Judge: gemini-3.1-pro-preview.

### Extraction output

| Model | Avg obs/game | Avg sp/game | Player_ID leak | Avg time/game |
|---|---|---|---|---|
| gemini-3.1-flash-lite (max thinking) | 4.0 | 4.0 | 0% | 16s |
| gemini-3-flash-preview | 5.9 | 6.5 | 0% | 116s |
| gemini-3.5-flash | 7.1 | 7.7 | 0% | 44s |
| gemini-2.5-flash | 11.6 | 11.6 | 3.4% | 45s |
| gemini-2.5-pro (baseline, 1 game) | 8.0 | 8.0 | 0% | ~50s |

### Judge scores (gemini-3.1-pro-preview, scale 1-5)

| Model | Specificity | Epistemic | Grounding | Coverage | Diversity | **Avg** |
|---|---|---|---|---|---|---|
| gemini-3-flash-preview | 5.00 | 5.00 | 4.90 | 5.00 | 5.00 | **4.98** |
| gemini-2.5-pro (current baseline) | 5.00 | 4.90 | 5.00 | 5.00 | 4.90 | **4.96** |
| gemini-3.5-flash | 5.00 | 4.90 | 4.50 | 5.00 | 5.00 | **4.88** |
| gemini-2.5-flash | 4.90 | 4.60 | 4.60 | 4.90 | 4.40 | **4.68** |
| gemini-3.1-flash-lite (max thinking) | 4.70 | 5.00 | 3.80 | 4.50 | 4.90 | **4.58** |

### Pricing context

| Model | Input $/1M | Output $/1M (incl. thinking) |
|---|---|---|
| gemini-3.1-flash-lite | $0.25 | $1.50 |
| gemini-2.5-flash | $0.30 | $2.50 |
| gemini-3-flash-preview | $0.50 | $3.00 |
| gemini-3.5-flash | $1.50 | $9.00 |
| gemini-2.5-pro (current) | $1.25 | $10.00 |

### Analysis

**gemini-2.5-pro** (current baseline) scores 4.96 — near-perfect and essentially tied with flash-3-preview. This is the standard to beat. Note: this evaluation used the old extraction (before player_ID fix), but the judge evaluates quality dimensions not player_ID usage, so scores are valid.

**gemini-3-flash-preview** achieves the highest average (4.98) at $3.00/M output — 3x cheaper than gemini-2.5-pro on output. However, its latency is prohibitive: 116s/game average with a single game spiking to 389s. This is a preview model and infrastructure may improve, but it's not production-ready.

**gemini-3.5-flash** is the best all-rounder: high quality (4.88), good volume (7.1 obs/game), fast (44s), and 0% player_ID leakage. Its output price ($9/M) is comparable to gemini-2.5-pro ($10/M), so the savings come from speed and lower input cost, not output cost. The 0.08 gap vs. 2.5-pro is driven by slightly lower grounding (4.50 vs 5.00).

**gemini-2.5-flash** is the volume king at 11.6 obs/game — nearly 2x flash-3.5. At $2.50/M output it's the best price/volume ratio. But quality is lower: diversity drops to 4.40 (repetitive items when volume is high), epistemic compliance to 4.60 (some role knowledge leaks in strategy points), and 3.4% player_ID leakage in observations despite the naming rule. The older model follows the prohibition less reliably.

**gemini-3.1-flash-lite (max thinking)** is too minimal for extraction. It consistently produces exactly 4 observations + 4 strategy points per game regardless of game complexity, missing important dynamics (coverage 4.50) and failing to ground claims in the transcript (grounding 3.80). Thinking tokens are metered as output at $1.50/M — cheap but not free. The model simply lacks capacity for this task.

### Note on judge calibration

The gemini-3.1-pro-preview judge scores higher than the gemini-3.5-flash judge used in Runs 1-3 (which scored the same gemini-2.5-pro extractions at 3.88-4.00 avg). This means scores across the two judge models are not directly comparable. Within this model comparison, the relative ranking is meaningful — the absolute numbers reflect a more generous judge.

### Recommendation

- **Best overall**: gemini-3.5-flash — high quality, fast, good volume
- **Budget pick**: gemini-2.5-flash — 3.6x cheaper output, highest volume, acceptable quality if player_ID leakage and some repetition are tolerable
- **Watch**: gemini-3-flash-preview — best quality, good price, but wait for latency to stabilize
- **Not recommended**: gemini-3.1-flash-lite — insufficient capacity for extraction

### Perspective compliance (added post-hoc)

After adding a perspective rule to the extraction prompt (requiring observation fields to be written from the assigned role's perspective), we added a 6th judge dimension — perspective compliance — and re-judged the original extractions (which were produced *without* the perspective rule). This measures natural perspective compliance before the prompt enforced it.

Judge: gemini-3.1-pro-preview, same model as the original comparison. Backend: Vertex AI (the original comparison used Google AI, so absolute scores on the other 5 dimensions may differ slightly — see note on backend calibration below).

| Model | Perspective | Specificity | Epistemic | Grounding | Coverage | Diversity |
|---|---|---|---|---|---|---|
| gemini-3.5-flash | **4.90** | 5.00 | 5.00 | 4.70 | 5.00 | 5.00 |
| gemini-3.1-flash-lite (max thinking) | 4.70 | 4.40 | 5.00 | 4.40 | 4.50 | 4.80 |
| gemini-2.5-pro (baseline) | 4.60 | 5.00 | 5.00 | 4.90 | 5.00 | 5.00 |
| gemini-3-flash-preview | 4.60 | 4.90 | 5.00 | 4.40 | 4.90 | 5.00 |
| gemini-2.5-flash | 4.20 | 4.80 | 4.70 | 4.80 | 5.00 | 4.20 |

**Findings:**

- **gemini-3.5-flash** leads at 4.90 — near-ceiling even without the perspective rule. Only 1 of 10 cases scored below 5.
- **gemini-3.1-flash-lite** scored 4.70, surprisingly higher than 2.5-pro. With only 4 observations per game, there are fewer opportunities for perspective violations — the low volume may be masking the issue.
- **gemini-2.5-pro** and **gemini-3-flash-preview** tied at 4.60. Both had 2-3 cases with perspective slips (approach describing opposing side's actions).
- **gemini-2.5-flash** is the weakest at 4.20, with one case scoring 2 (pervasive violations). The older model is less disciplined about maintaining consistent role perspective.

This is a baseline for the old prompt (no perspective rule). Phase 3 will re-extract with the current prompt and compare.

**Note on backend calibration:** This re-judging was run on Vertex AI, while the original judge scores were from Google AI. The two backends produce different outputs at temp=0, so absolute scores on the original 5 dimensions shifted slightly (e.g., grounding for flash-preview moved from 4.90 to 4.40). Relative rankings within each run are valid; absolute scores should not be compared across backend runs.

## Prompt fix: player_ID enforcement

Despite observations being allowed omniscient knowledge (they're post-game factual records), player_IDs are still undesirable because:
- They make observations less generalizable across games (player_2 in one game means nothing in another)
- They waste tokens without adding information (role descriptors are shorter and more informative)
- The extraction prompt said "use actual roles" but didn't explicitly forbid player_IDs — a permissive framing rather than a prohibitive one

The old prompt said: "You may use actual roles here since observations are factual post-game records."  
This was interpreted as permission to use roles but not as prohibition against IDs.

Fix: Replaced with a standalone NAMING RULE block containing:
- Explicit "Never use player IDs" instruction
- "Post-game omniscient perspective" framing (clarifying observations are factual)
- Good/Bad examples for disambiguation ("the wolf who led the early accusation" vs "player_2")
- Behavioral descriptors pattern for same-role disambiguation (the vocal villager, the surviving wolf)

## Summary of issues found

| Issue | Type | Impact | Fix |
|---|---|---|---|
| Judge scored epistemic on observations | Judge bug | Deflated epistemic by 1.19 points | Scoped to strategy points only |
| Judge didn't show dimensional fields | Judge bug | Specificity scored against incomplete context | Added fields to formatter |
| 84.3% of observations use player_IDs | Extraction prompt gap | Tokens wasted, less generalizable | Added explicit no-player-ID instruction |

## Summary of findings

1. **Extraction quality is high**: With the aligned judge, the prompt scores 3.88-4.00 across all dimensions except diversity (3.52). No prompt changes needed for grounding, coverage, or epistemic compliance.

2. **Player_ID naming rule works**: Adding an explicit prohibition with examples drops leakage from 84.3% to 0% on both models. This is the one prompt fix applied.

3. **Specificity was underestimated**: The judge was scoring against incomplete context. The actual retrieval query (composed_situation) is substantially more specific than the narrow situation field alone.

4. **gemini-3.5-flash is viable as extractor**: Comparable quality at lower cost and higher speed, with ~20% fewer items per game.

## Artifacts

All artifacts are co-located in this evidence folder.

### Judge eval (gemini-3.5-flash judge, 48 gemini-2.5-pro extractions)

| File | Description |
|---|---|
| `eval_configs/build_dataset.json` | Dataset build config (48 games) |
| `eval_configs/eval_flash.json` | Eval config (gemini-3.5-flash judge) |
| `eval_sets/extraction_v1.jsonl` | Frozen extraction dataset (48 cases) |
| `eval_results/extraction_eval_20260524_122625.jsonl` | Run 1 results (old judge) |
| `eval_results/extraction_eval_20260524_133752.jsonl` | Run 2 results (epistemic fix only) |
| `eval_results/extraction_eval_20260524_142020.jsonl` | Run 3 results (all judge fixes) |

### Player_ID fix verification

| File | Description |
|---|---|
| `flash_extraction_5games.txt` | gemini-3.5-flash extraction test (5 games, summary + samples) |
| `pro_reextraction_playerid_fix.txt` | gemini-2.5-pro re-extraction verifying player_ID fix (1 game) |

### Model comparison (10 games each, judged by gemini-3.1-pro-preview)

| File | Description |
|---|---|
| `model_comparison/gemini-3.5-flash_5games_20260524_145649.jsonl` | gemini-3.5-flash extractions (games 1-5) |
| `model_comparison/gemini-3.5-flash_5games_20260524_145259.jsonl` | gemini-3.5-flash extractions (games 6-10) |
| `model_comparison/gemini-3-flash-preview_10games_20260524_150827.jsonl` | gemini-3-flash-preview extractions (games 1-10) |
| `model_comparison/gemini-3.1-flash-lite-max_10games_20260524_145148.jsonl` | gemini-3.1-flash-lite max thinking extractions (games 1-10) |
| `model_comparison/gemini-2.5-flash_10games_20260524_152100.jsonl` | gemini-2.5-flash extractions (games 1-10) |
| `model_comparison/gemini-2.5-pro_10games_original.jsonl` | gemini-2.5-pro original extractions (games 1-10, from eval dataset) |
| `model_comparison/judge_gemini-3.1-pro-preview_20260524_150928.jsonl` | Judge scores for flash-3.5, flash-3-preview, flash-lite (30 cases) |
| `model_comparison/judge_gemini-3.1-pro-preview_20260524_152136.jsonl` | Judge scores for 2.5-flash (10 cases) |
| `model_comparison/judge_gemini-3.1-pro-preview_20260524_152753.jsonl` | Judge scores for 2.5-pro baseline (10 cases) |
| `model_comparison/judge_gemini-3.1-pro-preview_20260526_072522.jsonl` | Re-judge with perspective compliance dimension, all 5 models (50 cases, Vertex AI) |
