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

This is a baseline for the old prompt (no perspective rule).

**Note on backend calibration:** This re-judging was run on Vertex AI, while the original judge scores were from Google AI. The two backends produce different outputs at temp=0, so absolute scores on the original 5 dimensions shifted slightly (e.g., grounding for flash-preview moved from 4.90 to 4.40). Relative rankings within each run are valid; absolute scores should not be compared across backend runs.

### Perspective compliance with prompt rule (Phase 3)

Re-extracted the same 10 games using the current prompt (which includes the perspective rule added in commit fc12ca4) and judged with the updated 6-dimension judge. Flash-lite was also switched from `thinking_config: {mode: "max"}` to `thinking_level: "high"` (8192 token budget via factory) since the max mode may be buggy. Flash-preview was skipped (unstable API).

#### Extraction output (with perspective rule)

| Model | Avg obs/game | Avg sp/game | Player_ID leak | Avg time/game |
|---|---|---|---|---|
| gemini-3.1-flash-lite (high thinking) | 4.9 | 4.9 | 0% | 30s |
| gemini-3.5-flash | 8.2 | 7.7 | 0% | 44s |
| gemini-2.5-flash | 12.2 | 11.8 | 0% | 43s |

Flash-lite now produces variable output (4-6 per game) instead of the fixed 4+4 pattern seen with max thinking. 2.5-flash player_ID leakage dropped from 3.4% to 0% — the naming rule in the current prompt is effective across all models.

#### Judge scores (with perspective rule)

| Model | Perspective | Specificity | Epistemic | Grounding | Coverage | Diversity |
|---|---|---|---|---|---|---|
| gemini-3.5-flash | **5.00** | 5.00 | 4.80 | 4.70 | 5.00 | 5.00 |
| gemini-3.1-flash-lite (high thinking) | **5.00** | 3.90 | 5.00 | 3.60 | 4.40 | 4.40 |
| gemini-2.5-flash | **4.80** | 4.80 | 4.40 | 4.40 | 5.00 | 4.00 |

#### Perspective compliance delta (Phase 2 → Phase 3)

| Model | Without rule | With rule | Delta |
|---|---|---|---|
| gemini-3.5-flash | 4.90 | **5.00** | +0.10 |
| gemini-3.1-flash-lite | 4.70 | **5.00** | +0.30 |
| gemini-2.5-flash | 4.20 | **4.80** | +0.60 |

**Findings:**

- The perspective rule lifts all models. The biggest improvement is gemini-2.5-flash (+0.60), the model that had the worst natural perspective compliance.
- **gemini-3.5-flash** and **flash-lite** both reach ceiling (5.00) with the rule — perfect perspective compliance across all 10 games each.
- **gemini-2.5-flash** improves substantially but doesn't reach ceiling (4.80). Two games still scored 4, meaning occasional perspective slips remain even with the explicit rule.
- The other 5 dimensions are comparable to Phase 2 within noise. Flash-lite's lower specificity (3.90 vs 4.40) and grounding (3.60 vs 4.40) may reflect the thinking mode change (high vs max) rather than the prompt change, but the sample size is too small to separate these effects.

**Note:** Phase 2 and Phase 3 are not perfectly controlled — the prompt changed (perspective rule + naming rule), and flash-lite's thinking config changed. The perspective compliance delta is the cleanest signal since it directly measures what the new rule targets.

### Per-role extraction experiment (Phase 4)

Instead of one LLM call extracting all roles simultaneously, per-role extraction makes 4 separate calls — one for each role (wolf, villager, healer, investigator) — using a role-specific prompt that locks the perspective field and asks for 4-8 items per role. Outputs are merged into a single result per game.

Tested on 5 games (subset of the same dataset) with all three models.

#### Extraction output (per-role)

| Model | Avg obs/game | Avg sp/game | Player_ID leak | Avg time/game |
|---|---|---|---|---|
| gemini-3.5-flash | 16.2 | 16.4 | 0% | 136s |
| gemini-2.5-flash | 19.6 | 19.2 | 5.1% obs, 0% sp | 125s |
| gemini-3.1-flash-lite (high thinking) | 15.2 | 15.6 | 0% | 244s |

#### Judge scores (per-role)

| Model | Perspective | Specificity | Epistemic | Grounding | Coverage | Diversity | **Avg** |
|---|---|---|---|---|---|---|---|
| gemini-3.5-flash | 4.80 | 5.00 | 5.00 | 5.00 | 5.00 | 4.80 | **4.93** |
| gemini-2.5-flash | 4.40 | 4.60 | 4.00 | 5.00 | 5.00 | 3.60 | **4.43** |
| gemini-3.1-flash-lite (high thinking) | 4.80 | 3.80 | 4.80 | 4.20 | 5.00 | 3.20 | **4.13** |

#### Single-pass vs per-role comparison

Volume change (per-role relative to single-pass):

| Model | Obs/game | Sp/game | Time/game |
|---|---|---|---|
| gemini-3.5-flash | 8.2 → 16.2 (+98%) | 7.7 → 16.4 (+113%) | 44s → 136s (+3.1x) |
| gemini-2.5-flash | 12.2 → 19.6 (+61%) | 11.8 → 19.2 (+63%) | 43s → 125s (+2.9x) |
| gemini-3.1-flash-lite | 4.9 → 15.2 (+210%) | 4.9 → 15.6 (+218%) | 30s → 244s (+8.1x) |

Quality delta (per-role minus single-pass):

| Model | Perspective | Specificity | Epistemic | Grounding | Coverage | Diversity |
|---|---|---|---|---|---|---|
| gemini-3.5-flash | -0.20 | 0.00 | +0.20 | +0.30 | 0.00 | -0.20 |
| gemini-2.5-flash | -0.40 | -0.20 | -0.40 | +0.60 | 0.00 | -0.40 |
| gemini-3.1-flash-lite | -0.20 | -0.10 | -0.20 | +0.60 | +0.60 | -1.20 |

**Findings:**

- **Volume nearly doubles** with per-role extraction: ~2x more observations and strategy points per game. This is the primary benefit — each role-focused call produces 4-5 items rather than sharing a budget of ~8 items across all roles.
- **Time and cost ~3x higher**: 4 sequential LLM calls per game instead of 1, with inter-call delays.
- **Grounding improves for both models** (+0.30 for 3.5-flash, +0.60 for 2.5-flash). When focused on a single role, the model grounds claims more thoroughly in the transcript.
- **Diversity scores drop** across all models, but this is expected and not a real quality concern. Per-role extraction deliberately covers the same game events from 4 different perspectives — the judge sees overlapping events and scores them as "repetitive," but a wolf's view of a mislynch and a villager's view of the same mislynch are distinct retrieval targets. The diversity metric is not calibrated for per-role output. Perspective scores also dip slightly — possibly the merged output confuses the judge when it sees the same events from 4 perspectives.
- **2.5-flash quality degrades substantially** under per-role (avg 4.43 vs 4.50 single-pass). Epistemic compliance drops to 4.00 (was 4.40) — more items means more chances for knowledge-level violations. Player_ID leakage re-appears at 5.1% despite the naming rule.
- **3.5-flash quality holds** (avg 4.93 vs 4.92 single-pass). The only drops are diversity and perspective on one game (both scored 4), while grounding and epistemic both improve.
- **Flash-lite (high thinking) gets the biggest volume boost** (+210% obs). Grounding and coverage both improve (+0.60 each). Specificity drops to 3.80 (-0.10). Per-role latency is extremely variable (58s–474s per game, avg 244s) — an 8.1x slowdown vs single-pass. See the thinking budget experiment below for a much better configuration.

#### Flash-lite thinking budget experiment: medium vs high

The high thinking budget (8192 tokens) caused extreme latency variance for flash-lite per-role (58s–474s/game). Tested medium thinking (4096 tokens) on the same 5 games.

| Metric | High (8192) | Medium (4096) |
|---|---|---|
| Avg time/game | 244s (58–474s) | 38s (36–40s) |
| Avg obs/game | 15.2 | 14.8 |
| Avg sp/game | 15.6 | 16.0 |
| Judge avg | 4.13 | **4.57** |

Judge score breakdown (high → medium):

| Dimension | High | Medium | Delta |
|---|---|---|---|
| Specificity | 3.80 | **4.40** | +0.60 |
| Epistemic | 4.80 | 4.80 | 0.00 |
| Grounding | 4.20 | 4.20 | 0.00 |
| Coverage | 5.00 | 5.00 | 0.00 |
| Diversity | 3.20 | **4.00** | +0.80 |
| Perspective | 4.80 | **5.00** | +0.20 |

Medium thinking is strictly better: **6.4x faster**, **+0.44 judge avg**, comparable volume, zero latency spikes. The high thinking budget was actively hurting flash-lite — more thinking tokens led to worse and slower output.

Manual inspection confirms medium thinking preserves the quality insights (investigation target selection, failure-mode pivots, pressure tactics) while producing less filler. Medium is also more willing to recommend sharing information ("publicly clear investigated villagers," "prepare to communicate findings before death") vs high thinking's conservative "never reveal your role" in every game.

**Flash-lite medium per-role vs 3.5-flash single-pass:**

| Metric | 3.5-flash single-pass | Flash-lite medium per-role |
|---|---|---|
| Avg items/game | 8.4 obs + 8.0 sp | 14.8 obs + 16.0 sp (**1.9x**) |
| Investigator items (5 games) | 19 | 38 (**2x**) |
| Avg time/game | 44s | 38s (faster) |
| Output price/1M | $9.00 | $1.50 (**6x cheaper**) |
| Judge avg | **4.92** | 4.57 (-0.35) |

The judge gap is real on specificity (-0.60) and grounding (-0.50), but flash-lite medium per-role provides 2x the role coverage at 6x lower cost. For strategy store population with dedup downstream, this is a compelling tradeoff.

#### Judge scores vs actual content quality

The judge scores suggest per-role extraction is equal or slightly worse than single-pass. Manual inspection of the investigator role across all 5 games and all 3 models tells a different story. The size of the information gain depends on how well each model budgets investigator items in single-pass mode.

#### Investigator item counts (5 games)

| Model | Single-pass | Per-role | Gain |
|---|---|---|---|
| flash-lite | 5 obs + 5 sp = 10 | 17 obs + 20 sp = 37 | +270% |
| 3.5-flash | 10 obs + 9 sp = 19 | 19 obs + 20 sp = 39 | +105% |
| 2.5-flash | 15 obs + 14 sp = 29 | 24 obs + 23 sp = 47 | +62% |

#### Flash-lite: catastrophic single-pass undercoverage → massive per-role gain

Single-pass produces exactly 1 obs + 1 sp per game for the investigator. All 5 strategy points converge on a single generic lesson: "guide the village to the wolf without revealing your role." Per-role produces 3-4 obs + 3-5 sp per game, surfacing entire categories of strategy absent from single-pass:

- **Night action target selection**: "Don't waste your investigation on the healer-saved player — their alignment is already confirmed." Single-pass never mentions investigation targeting.
- **Failure-mode strategy**: "When your investigations consistently return villagers, pivot to voting record analysis." Single-pass only covers the success case.
- **Post-save positioning**: "After being healer-saved, don't lead aggressively — observe who's controlling the narrative." Single-pass just notes "you were too visible."
- **Vote train analysis**: "Focus on who *initiated* the vote train vs who joined late — wolves hide in the middle of bandwagons."
- **Pressure tactics**: "Challenge players using 'caution' to stall — demand they name specific suspects."

The best flash-lite per-role insights are competitive with 3.5-flash — concise and actionable. The weakness is signal-to-noise: flash-lite surrounds these good points with filler ("don't reveal your role" repeated in every game, formulaic info_landscape fields). For a strategy store with dedup downstream, the filler is collapsed automatically, so the novel insights survive at flash-lite's much lower price point.

#### 3.5-flash: decent single-pass coverage → meaningful per-role additions

Single-pass already produces 2 obs + 1.8 sp per game for the investigator and covers night_action phases, including the "don't investigate healer-saved player" insight. The gap is smaller but per-role still surfaces novel tactical strategies:

- **Collusion defense**: "When accused of coordination, reframe it as independent players observing the same facts." Not in single-pass.
- **Information preservation**: "Soft-claim or share cleared targets before you die — keeping them secret wastes information the village needs." Novel failure-mode thinking.
- **Bandwagon analysis**: "Closely analyze players who echo your arguments without adding new reasoning — they may be wolves hiding behind your credibility." A meta-deduction technique absent from single-pass.
- **Mislynch recovery**: "Don't blindly join bandwagon votes — use your private knowledge of cleared players to evaluate who's driving the push."
- **Style vs substance**: "Don't assume an aggressive player is a wolf — look at who eagerly jumps on the bandwagon against them, as wolves exploit stylistic disputes for easy mislynches."

#### 2.5-flash: highest single-pass volume → incremental per-role depth

Single-pass produces 3 obs + 2.8 sp per game, already covering night actions, voting, and discussion phases. Per-role gains are more incremental:

- **Healer identification**: "Prioritize investigating potential support roles like the Healer to coordinate protection." Single-pass doesn't cover role-confirmation strategy.
- **Pre-death information sharing**: "If wolves are likely to target you next, consider revealing confirmed villager findings to a trusted player as a secondary information source." Novel survival/legacy thinking.
- **Pattern mirroring**: "When a wolf is eliminated, investigate the player who mirrored their suspicious behavior — wolves often share behavioral patterns."

The gains are real but smaller — 2.5-flash's higher single-pass volume already captures most key investigator situations, so per-role adds depth rather than filling blind spots.

#### Implication for evaluation

The judge's diversity metric penalizes per-role output for covering the same game events from multiple perspectives, but cannot assess whether the output contains strategically novel insights relative to an alternative method. This is a fundamental limitation of LLM-as-judge for comparing extraction approaches: the judge measures surface-level properties within a set (diversity, specificity) but not information gain over the alternative.

The pattern across models is clear: **the less budget a model allocates to minority roles in single-pass, the larger the information gain from per-role extraction.** Flash-lite goes from 1 investigator item/game to 7 — a qualitative leap. 3.5-flash goes from 2 to 4 — still valuable. 2.5-flash goes from 3 to 5 — incremental.

Peak insight quality is surprisingly similar across models — flash-lite's best investigator strategy points are as concise and actionable as 3.5-flash's. The difference is consistency: 3.5-flash maintains high quality across all items, while flash-lite's best ~40% is surrounded by generic filler. With a dedup pipeline downstream, this distinction matters less — dedup collapses the filler and the novel insights from all models survive.

A retrieval-based evaluation — "given a specific in-game situation, does the per-role store return a useful strategy that the single-pass store misses?" — would better capture the downstream value than aggregate judge scores.

**Recommendation:** Per-role extraction is viable for all models when higher volume is needed to populate a strategy store, with the dedup pipeline handling filler collapse. Model choice depends on the tradeoff:
- **gemini-3.5-flash**: best consistency — highest proportion of novel, actionable items. 3x cost overhead.
- **gemini-3.1-flash-lite (medium thinking)**: best value — peak insights are competitive with 3.5-flash at 6x lower cost, 38s/game with stable latency. More filler to dedup than 3.5-flash but comparable speed.
- **gemini-2.5-flash**: not recommended — epistemic compliance drops and player_ID leakage re-emerges under per-role, and single-pass already captures most investigator situations.

**Note:** Per-role results use 5 games vs 10 games for single-pass Phase 3, so the quality comparison has a sample size caveat. The volume and timing comparisons are directional.

### Per-role judge pipeline (Phase 5)

Extended the judge from 6 to 8 dimensions and built two new evaluation tools:

**New dimensions added:**
- **strategy_depth** — Does the strategy point provide concrete conditions, a specific action, and reasoning for WHY it works? (1=generic platitude, 5=specific technique with conditions and learned nuance)
- **novelty** — Does the item capture a non-obvious mechanism, or restate common-sense fundamentals? (1=obvious advice, 5=reframes how you'd approach the situation)

Both dimensions were already demanded by the extraction prompt (lines 187-211 of extraction.py) but never measured by the judge.

**New tools:**
1. `scripts/per_role_judge.py` — judges extraction outputs per-role (each role evaluated separately with all 8 dimensions)
2. `scripts/per_role_comparison.py` — pairwise comparison of 2+ extraction outputs per game × role, with tournament-style W/T/L ranking

#### Per-role judge: flash-lite medium (8 dimensions)

Judged flash-lite medium per-role extraction (5 games, 20 role evaluations). Judge: gemini-3.1-pro-preview.

| Role | Spec | Epist | Ground | Cover | Divers | Persp | **StrDepth** | **Novelty** |
|---|---|---|---|---|---|---|---|---|
| wolf (n=5) | 3.80 | 5.00 | 4.60 | 2.60 | 4.00 | 5.00 | 4.40 | 3.40 |
| villager (n=5) | 4.00 | 5.00 | 5.00 | 2.60 | 3.80 | 5.00 | 4.40 | 3.20 |
| healer (n=5) | 3.20 | 4.60 | 4.20 | 2.80 | 3.80 | 4.40 | 3.40 | 2.40 |
| investigator (n=5) | 3.40 | 4.60 | 3.20 | 2.20 | 4.00 | 5.00 | 3.60 | 2.80 |
| **OVERALL (n=20)** | **3.60** | **4.80** | **4.25** | **2.55** | **3.90** | **4.85** | **3.95** | **2.95** |

**Findings:**
- The new dimensions produce differentiated scores — not ceiling effects. Strategy depth (3.95) is stronger than novelty (2.95), indicating items are tactically specific but often restate known approaches.
- Healer consistently scores lowest across most dimensions — fewer game events to draw on, leading to thinner coverage and less novel insights.
- Coverage (2.55) is the weakest dimension. This is a per-role judge artifact: each role only sees events from its own perspective, so the judge (calibrated for whole-game coverage) rates it low. This is the same dynamic as the diversity issue — the metric isn't calibrated for per-role output.
- Perspective compliance (4.85) and epistemic compliance (4.80) remain near-ceiling, confirming per-role extraction handles these well.

#### Pairwise comparison: flash-lite per-role vs 3.5-flash per-role

Same extraction mode (per-role), different models. 5 games × 4 roles = 20 matchups. Judge: gemini-3.1-pro-preview.

| Role | Flash-lite medium | 3.5-flash |
|---|---|---|
| wolf | 0W 0T 4L (0%) | 4W 0T 0L (100%) |
| villager | 1W 0T 4L (20%) | 4W 0T 1L (80%) |
| healer | 0W 0T 4L (0%) | 4W 0T 0L (100%) |
| investigator | 1W 0T 4L (20%) | 4W 0T 1L (80%) |
| **OVERALL** | **2W 0T 16L (11%)** | **16W 0T 2L (89%)** |

When both models use the same extraction mode, 3.5-flash dominates — 89% win rate with high confidence (most matchups conf=5). The quality gap between models is real and substantial when the extraction approach is held constant.

#### Pairwise comparison: flash-lite per-role vs 3.5-flash single-pass

The key question: can a cheaper model with per-role extraction compete with a stronger model's single-pass output? Flash-lite medium per-role (4 calls × $1.50/M) vs 3.5-flash single-pass (1 call × $9.00/M). 5 games × 4 roles = 20 matchups.

| Role | Flash-lite per-role | 3.5-flash single-pass |
|---|---|---|
| wolf | 2W 0T 3L (40%) | 3W 0T 2L (60%) |
| villager | 2W 0T 3L (40%) | 3W 0T 2L (60%) |
| healer | **3W 0T 2L (60%)** | 2W 0T 3L (40%) |
| investigator | 2W 0T 3L (40%) | 3W 0T 2L (60%) |
| **OVERALL** | **9W 0T 11L (45%)** | **11W 0T 9L (55%)** |

**This is nearly a coin flip.** Flash-lite per-role goes from 11% (vs 3.5-flash per-role) to 45% (vs 3.5-flash single-pass) — the per-role extraction mode closes most of the model quality gap.

Key observations:
- Flash-lite per-role **wins on healer** (60%) — single-pass underallocates attention to healer items, so per-role's dedicated healer call produces better output even from a weaker model.
- Wolf, villager, investigator are all 40-60 splits — close enough that game-specific factors matter more than model quality.
- All 20 matchups completed successfully (0 judge failures) after adding validators for the pairwise judge's output normalization.

**Cost/speed comparison:**

| Config | Items/game | Time/game | Output price/1M | Effective cost | Quality (pairwise) |
|---|---|---|---|---|---|
| 3.5-flash single-pass | 16.4 | 44s | $9.00 | 1x baseline | 55% win rate |
| Flash-lite medium per-role | 30.8 | 38s | $1.50 | ~6x cheaper | 45% win rate |

Flash-lite per-role produces **1.9x more items**, is **faster** (38s vs 44s — the 4 calls run quicker than one large call), costs **6x less**, and achieves **45% pairwise win rate** against 3.5-flash single-pass. With a dedup pipeline downstream that collapses filler, the volume advantage compounds — more unique insights survive dedup at a fraction of the cost.

### gemini-2.5-pro evaluation (Phase 6)

Added gemini-2.5-pro to the per-role pipeline to establish the quality ceiling. Ran both single-pass and per-role extraction on the same 5 games, then judged with the 8-dimension per-role judge and pairwise comparisons against 3.5-flash and flash-lite. Judge: gemini-3.1-pro-preview.

#### Extraction output

| Mode | Avg obs/game | Avg sp/game | Player_ID leak | Avg time/game |
|---|---|---|---|---|
| Single-pass | 8.6 | 9.0 | 0% | 75s (58–111s) |
| Per-role | 18.4 | 20.0 | 0% | 235s (189–275s) |

Per-role doubles volume (+114% obs, +122% sp) at 3.1x the latency — the same pattern seen with other models in Phase 4.

#### Per-role judge scores (8 dimensions)

**gemini-2.5-pro per-role:**

| Role | Spec | Epist | Ground | Cover | Divers | Persp | StrDepth | Novelty |
|---|---|---|---|---|---|---|---|---|
| wolf (n=5) | 5.00 | 5.00 | 4.80 | 2.60 | 4.40 | 5.00 | 5.00 | 4.40 |
| villager (n=5) | 4.80 | 5.00 | 5.00 | 4.40 | 4.80 | 3.80 | 5.00 | 4.60 |
| healer (n=5) | 4.20 | 5.00 | 5.00 | 3.40 | 4.40 | 4.20 | 4.40 | 3.60 |
| investigator (n=5) | 5.00 | 5.00 | 4.20 | 3.80 | 5.00 | 5.00 | 5.00 | 4.40 |
| **OVERALL (n=20)** | **4.75** | **5.00** | **4.75** | **3.55** | **4.65** | **4.50** | **4.85** | **4.25** |

**gemini-2.5-pro single-pass:**

| Role | Spec | Epist | Ground | Cover | Divers | Persp | StrDepth | Novelty |
|---|---|---|---|---|---|---|---|---|
| wolf (n=5) | 4.60 | 5.00 | 4.60 | 2.00 | 4.60 | 5.00 | 4.80 | 3.80 |
| villager (n=5) | 4.40 | 4.40 | 4.80 | 2.40 | 4.40 | 4.40 | 4.60 | 3.80 |
| healer (n=5) | 3.40 | 5.00 | 4.80 | 1.20 | 2.60 | 4.40 | 4.00 | 2.20 |
| investigator (n=5) | 4.20 | 4.80 | 3.60 | 1.40 | 3.80 | 5.00 | 4.40 | 3.20 |
| **OVERALL (n=20)** | **4.15** | **4.80** | **4.45** | **1.75** | **3.85** | **4.70** | **4.45** | **3.25** |

**Delta (per-role minus single-pass):**

| Dimension | Per-role | Single-pass | Delta |
|---|---|---|---|
| Specificity | 4.75 | 4.15 | **+0.60** |
| Epistemic | 5.00 | 4.80 | +0.20 |
| Grounding | 4.75 | 4.45 | +0.30 |
| Coverage | 3.55 | 1.75 | **+1.80** |
| Diversity | 4.65 | 3.85 | **+0.80** |
| Perspective | 4.50 | 4.70 | -0.20 |
| Strategy depth | 4.85 | 4.45 | **+0.40** |
| Novelty | 4.25 | 3.25 | **+1.00** |

Per-role extraction is a clear win on 2.5-pro. The largest gains are coverage (+1.80), novelty (+1.00), and diversity (+0.80) — the dimensions that directly measure how much unique, non-obvious content is extracted. Single-pass healer and investigator coverage scores (1.20 and 1.40) are near-floor, confirming single-pass systematically starves minority roles even with a strong model.

#### Cross-model comparison (8-dim judge, per-role extraction)

| Model | Spec | Epist | Ground | Cover | Divers | Persp | StrDepth | Novelty | **Avg** |
|---|---|---|---|---|---|---|---|---|---|
| **gemini-2.5-pro** | 4.75 | 5.00 | 4.75 | 3.55 | 4.65 | 4.50 | 4.85 | 4.25 | **4.60** |
| flash-lite medium | 3.60 | 4.80 | 4.25 | 2.55 | 3.90 | 4.85 | 3.95 | 2.95 | **3.86** |

2.5-pro per-role scores higher on every dimension except perspective compliance (4.50 vs 4.85 — flash-lite's only advantage). The gap is widest on novelty (+1.30) and strategy depth (+0.90), the two new dimensions that measure insight quality rather than structural correctness.

#### Pairwise comparison: single-pass vs per-role (same model)

| Role | Single-pass wins | Per-role wins |
|---|---|---|
| wolf | 0 (0%) | **5 (100%)** |
| villager | **3 (60%)** | 2 (40%) |
| healer | 1 (20%) | **4 (80%)** |
| investigator | 0 (0%) | **5 (100%)** |
| **OVERALL** | **4 (20%)** | **16 (80%)** |

Per-role dominates at 80% win rate. Single-pass only wins on villager — the role that gets the most attention in single-pass extraction because villager events dominate the transcript. Wolf and investigator are 5-0 sweeps for per-role.

#### Pairwise comparison: 2.5-pro per-role vs 3.5-flash per-role

| Role | 2.5-pro wins | 3.5-flash wins |
|---|---|---|
| wolf | **4 (80%)** | 1 (20%) |
| villager | **3 (60%)** | 2 (40%) |
| healer | **5 (100%)** | 0 (0%) |
| investigator | **4 (80%)** | 1 (20%) |
| **OVERALL** | **16 (80%)** | **4 (20%)** |

2.5-pro dominates 3.5-flash when both use per-role extraction. The healer gap is most striking — 5-0 sweep. 3.5-flash's wins are scattered and low-confidence (the villager win in game 1ef60e08 had conf=1).

#### Pairwise comparison: 2.5-pro per-role vs flash-lite medium per-role

| Role | 2.5-pro wins | Flash-lite wins |
|---|---|---|
| wolf | **5 (100%)** | 0 (0%) |
| villager | **5 (100%)** | 0 (0%) |
| healer | **5 (100%)** | 0 (0%) |
| investigator | **5 (100%)** | 0 (0%) |
| **OVERALL** | **20 (100%)** | **0 (0%)** |

Clean sweep at high confidence (all matchups conf 4-5). The quality gap between 2.5-pro and flash-lite is large and consistent across all roles and games.

#### Findings

**Quality hierarchy for per-role extraction:** gemini-2.5-pro (4.60 avg, 80-100% pairwise) >> gemini-3.5-flash (80% vs flash-lite in Phase 5) >> flash-lite medium (3.86 avg). The gap between pro and flash-lite (0.74 avg, 100% pairwise) is larger than the gap between 3.5-flash and flash-lite (89% vs 11% in Phase 5).

**Per-role is even more beneficial for 2.5-pro than for smaller models.** Per-role wins 80% of matchups against single-pass with 2.5-pro, compared to the more mixed results seen in Phase 4 with flash models. The healer and investigator coverage gains are dramatic (1.20→3.40 and 1.40→3.80) — even a strong model can't adequately cover minority roles in a single pass.

**Cost/quality tradeoff remains the key decision.** 2.5-pro per-role is unambiguously the best extractor, but at significant cost: ~$30/M output tokens vs flash-lite's ~$1.50/M, with 3.1x higher latency per game. The question is whether the 0.74-point judge improvement and 100% pairwise dominance over flash-lite translate to meaningfully better downstream retrieval after dedup collapses both into the strategy store.

**The user's hypothesis holds: 4× flash-lite per-role is faster and cheaper than 1× 2.5-pro single-pass.** Flash-lite per-role runs in 38s/game (vs 75s for 2.5-pro single-pass) at ~20x lower cost, produces 1.7x more items (30.8 vs 17.6), and the per-role judge scores (3.86 avg) are competitive with 2.5-pro single-pass (3.86 avg). The tradeoff is whether flash-lite's lower per-item quality matters after dedup — and whether 2.5-pro per-role's substantially higher per-item quality (4.60 avg) justifies the premium.

#### Cross-mode comparison: best single-pass vs per-role models

The practical question: can per-role extraction from a cheaper model beat the best single-pass model?

**2.5-pro single-pass vs 3.5-flash per-role:**

| Role | 2.5-pro single wins | 3.5-flash per-role wins |
|---|---|---|
| wolf | 1 (20%) | **4 (80%)** |
| villager | 1 (20%) | **4 (80%)** |
| healer | 1 (20%) | **4 (80%)** |
| investigator | 1 (20%) | **4 (80%)** |
| **OVERALL** | **4 (20%)** | **16 (80%)** |

3.5-flash per-role dominates uniformly — 80% across all 4 roles, including wolf where single-pass has full coverage. Per-role 3.5-flash wins on quality, not just coverage.

**2.5-pro single-pass vs flash-lite medium per-role:**

| Role | 2.5-pro single wins | Flash-lite per-role wins |
|---|---|---|
| wolf | **5 (100%)** | 0 (0%) |
| villager | **4 (80%)** | 1 (20%) |
| healer | 1 (20%) | **4 (80%)** |
| investigator | **4 (80%)** | 1 (20%) |
| **OVERALL** | **14 (70%)** | **6 (30%)** |

Flash-lite per-role loses overall (30%) but wins healer 80%. 2.5-pro's per-item quality overcomes flash-lite's coverage advantage on wolf (5-0), villager (4-1), and investigator (4-1). Only healer — the most coverage-starved role — flips to flash-lite.

**Observation quality analysis:**

Single-pass doesn't just undercount minority roles — it produces **redundant** observations across games. Healer observations from 2.5-pro single-pass (8 across 5 games): 5 of 8 are variants of "first night, no information, choose who to protect." After dedup, these collapse to ~2-3 unique situations.

Per-role healer observations (19-21 across 5 games) cover the full arc: first-night targeting, post-save dynamics, wolf retaliatory kills, healer under scrutiny, healer as early casualty, mislynch observation. After dedup, 10+ unique situations survive.

The prompt requests "4-8 items per role" in both modes, but single-pass models produce ~50% of the requested volume and concentrate on the dominant role (wolf). Per-role forces compliance with the per-role target by giving each role a dedicated call.

**Implication:** The single-pass coverage deficit is both quantitative (fewer items) and qualitative (more redundant items). The dedup argument — that lower volume means less downstream work — is inverted here: single-pass output is MORE redundant per item than per-role output, so dedup removes a higher proportion while retaining fewer unique situations.

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

5. **Per-role extraction is strictly better than single-pass** for all models tested. The benefit scales with model capability — 2.5-pro per-role achieves 80% pairwise win rate vs its own single-pass, with the largest gains on coverage (+1.80), novelty (+1.00), and diversity (+0.80).

6. **Model quality hierarchy is clear**: gemini-2.5-pro per-role (4.60 avg) >> 3.5-flash per-role >> flash-lite medium per-role (3.86 avg). 2.5-pro sweeps flash-lite 20-0 and beats 3.5-flash 16-4.

7. **Flash-lite per-role remains the best value**: 4× flash-lite per-role is faster (38s vs 75s) and ~20× cheaper than 1× 2.5-pro single-pass, with comparable aggregate judge scores (3.86 vs 3.86). For strategy store population with dedup downstream, the cost/speed advantage outweighs the per-item quality gap.

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
| `model_comparison/gemini-3.1-flash-lite-high_10games_20260526_080135.jsonl` | Phase 3: flash-lite high thinking re-extraction (10 games, with perspective rule) |
| `model_comparison/gemini-3.5-flash_10games_20260526_080359.jsonl` | Phase 3: 3.5-flash re-extraction (10 games, with perspective rule) |
| `model_comparison/gemini-2.5-flash_10games_20260526_080350.jsonl` | Phase 3: 2.5-flash re-extraction (10 games, with perspective rule) |
| `model_comparison/judge_gemini-3.1-pro-preview_20260526_080415.jsonl` | Phase 3: judge scores for all 3 re-extractions (30 cases, Vertex AI) |
| `model_comparison/gemini-3.5-flash_5games_per-role_20260526_090203.jsonl` | Phase 4: 3.5-flash per-role extraction (5 games, 4 calls/game) |
| `model_comparison/gemini-2.5-flash_5games_per-role_20260526_090106.jsonl` | Phase 4: 2.5-flash per-role extraction (5 games, 4 calls/game) |
| `model_comparison/gemini-3.1-flash-lite-high_5games_per-role_20260526_093903.jsonl` | Phase 4: flash-lite per-role extraction (5 games, 4 calls/game) |
| `model_comparison/judge_gemini-3.1-pro-preview_20260526_090242.jsonl` | Phase 4: judge scores for 3.5-flash + 2.5-flash per-role extractions (10 cases, Vertex AI) |
| `model_comparison/judge_gemini-3.1-pro-preview_20260526_093911.jsonl` | Phase 4: judge scores for flash-lite high per-role extraction (5 cases, Vertex AI) |
| `model_comparison/gemini-3.1-flash-lite-medium_5games_per-role_20260526_101628.jsonl` | Phase 4: flash-lite medium thinking per-role extraction (5 games) |
| `model_comparison/judge_gemini-3.1-pro-preview_20260526_101640.jsonl` | Phase 4: judge scores for flash-lite medium per-role extraction (5 cases, Vertex AI) |
| `model_comparison/per_role_judge_gemini-3.1-pro-preview_20260526_110816.jsonl` | Phase 5: per-role 8-dimension judge scores for flash-lite medium (20 role evals) |
| `model_comparison/comparison_gemini-3.1-pro-preview_20260526_111845.jsonl` | Phase 5: pairwise comparison, flash-lite per-role vs 3.5-flash per-role (18 matchups) |
| `model_comparison/comparison_gemini-3.1-pro-preview_20260526_114150.jsonl` | Phase 5: pairwise comparison, flash-lite per-role vs 3.5-flash single-pass (20 matchups) |
| `model_comparison/gemini-2.5-pro_5games_20260526_120027.jsonl` | Phase 6: 2.5-pro single-pass extraction (5 games) |
| `model_comparison/gemini-2.5-pro_5games_per-role_20260526_121348.jsonl` | Phase 6: 2.5-pro per-role extraction (5 games, 4 calls/game) |
| `model_comparison/per_role_judge_gemini-3.1-pro-preview_20260526_121947.jsonl` | Phase 6: per-role 8-dimension judge scores for 2.5-pro per-role (20 role evals) |
| `model_comparison/per_role_judge_gemini-3.1-pro-preview_20260526_121950.jsonl` | Phase 6: per-role 8-dimension judge scores for 2.5-pro single-pass (20 role evals) |
| `model_comparison/comparison_gemini-3.1-pro-preview_20260526_121952.jsonl` | Phase 6: pairwise comparison, 2.5-pro single-pass vs per-role (20 matchups) |
| `model_comparison/comparison_gemini-3.1-pro-preview_20260526_121958.jsonl` | Phase 6: pairwise comparison, 2.5-pro per-role vs 3.5-flash per-role (20 matchups) |
| `model_comparison/comparison_gemini-3.1-pro-preview_20260526_121959.jsonl` | Phase 6: pairwise comparison, 2.5-pro per-role vs flash-lite per-role (20 matchups) |
| `model_comparison/comparison_gemini-3.1-pro-preview_20260526_123813.jsonl` | Phase 6: cross-mode comparison, 2.5-pro single-pass vs 3.5-flash per-role (20 matchups) |
| `model_comparison/comparison_gemini-3.1-pro-preview_20260526_123811.jsonl` | Phase 6: cross-mode comparison, 2.5-pro single-pass vs flash-lite per-role (20 matchups) |
