# Post-Game Extraction — how it works today

**Orientation.** When a game finishes, one extraction pass mines the full transcript into structured
**observations** — the episodic memory a future game retrieves against. It is the write side of the memory
system: everything retrieval, dedup, and reranking later operate on enters the store here.

```
finished game ─▶ per-cell extraction fan-out ─▶ observations ─▶ dedup ─▶ store ─▶ (future game) retrieval
                 (one LLM call per role×phase cell)              strategy points: synthesized cross-game, not here
```

The pass runs once per game, off the critical path of play. Its job is narrow and load-bearing: turn a long
transcript into a set of specific, grounded, role-scoped situations that will still make sense as retrieval
targets in a *different* game later on. This doc is the current shipped state; the path that got here is
[experiment_log.md](experiment_log.md), and how the output is *measured* — the extraction judge and how far to
trust it — is written up in [../../evaluation/llm_judge/extraction.md](../../evaluation/llm_judge/extraction.md).

## What it produces (current schema)

Two record types, now populated on **different schedules** — the central v7 change:

- **Observations** — factual, post-game records of what happened from one role's vantage: a situation, the
  approach taken, the outcome. These are extracted here, per game. Each observation carries the **v6
  dimensional fields** (`information_landscape`, `game_phase`, `consensus_texture`, `agent_exposure`) alongside
  the base `situation`; the `composed_situation` concatenates them into the text that retrieval actually
  embeds and matches. A narrow situation string alone matched too many scenarios, so the dimensional fields
  exist to make each record *distinctive* as a search target.
- **Strategy points** — reusable, role-appropriate advice. Under **v7 these are no longer extracted per
  game.** A per-game strategy point is a single-game restatement that just pollutes the store; an SP earns its
  place only by *generalizing across games*, so SPs are synthesized later from cross-game observation clusters
  during consolidation, not minted here. (The legacy dual `{observations, strategy_points}` call survives
  behind a flag for the offline store-builders that still want per-game SPs.)

## Guarantee / contract (present-tense)

- **Full role coverage by construction.** The fixed 9-player, three-faction casting guarantees every game
  contains all six role types, so the fan-out always extracts the full set — villager, wolf, investigator,
  healer, serial_killer, vigilante — without inspecting which roles were present
  ([extraction_agent.py:42-49](../../../Agents/memory/extraction/extraction_agent.py#L42-L49)). This is the
  mechanism that fixes single-pass extraction's central failure: a single all-roles call systematically
  starved the minority roles (healer, investigator), and a dedicated per-cell call cannot (experiment_log §5).
- **Partial extraction beats none.** Each cell runs independently with a primary→backup model fallback. A cell
  that has no schema (villager has no night cell) or exhausts every attempt is dropped, and the surviving
  cells still merge into a result. The pass returns nothing only if *every* cell failed
  ([extraction_agent.py:290-307](../../../Agents/memory/extraction/extraction_agent.py#L290-L307)).
- **Observations name roles, never player IDs.** A player ID (`player_2`) means nothing in a different game, so
  the prompt forbids IDs in observations and requires role or behavioral descriptors instead. This is enforced
  by the prompt and checked by a deterministic script, not by the judge (Verification).
- **Epistemic framing is scoped by record type.** Observations are factual post-game records and may use
  omniscient framing; strategy points must respect in-game role-knowledge limits. The prompt applies the
  epistemic-status rule to strategy points only.
- **What is NOT guaranteed.** Judge *calibration* (no human answer key sits behind the scores);
  **v7 synthesis quality** (the synthesized cross-game strategy points are not judged at all); and the *model
  and mode* recommendations from the quality study, which rest on n=5-10 games and predate the per-cell schema.
  See the gaps table.

## The mechanism / model

- **Live entry point.** `extract_postgame_per_cell`
  ([extraction_agent.py:290](../../../Agents/memory/extraction/extraction_agent.py#L290)), called from the
  orchestrator's post-game node ([orchestrator.py:428](../../../Agents/nodes/orchestrator.py#L428)).
- **The unit is a cell, not a role.** The fan-out is over **(role, phase-group) cells** — 11 in total: the
  villager day cell, plus a day and a night cell for each of the other five roles
  ([cell_units.py](../../../Agents/memory/extraction/cell_units.py)). The day cell covers both public
  discussion and the elimination vote and tags each observation by phase; the night cell covers the secret
  night action. Cells run concurrently on a thread pool.
- **Model.** gemini-2.5-pro (`DEFAULT_PRO_MODEL`) as primary, a backup model on failure, with retries on each.
  2.5-pro is the quality ceiling the study established; the flash-tier alternatives it profiled trade quality
  for cost and are available but not the default. A v7-era A/B (2026-06-19) re-ran the model question on the
  **live v6_1 store** and found **flash-3.5 ≈ pro** with flash-lite correct-but-thinner, so the v7
  consolidation loop — which re-extracts *every* game and is dominated by extraction cost — runs a cheaper
  flash-tier model, while this live per-game graph keeps 2.5-pro (experiment_log §8).
- **Prefix caching.** Every cell shares a byte-identical role/phase-neutral prefix (the transcript and rules).
  With `cache_prefix` on, a Vertex context cache is built from that prefix once and the concurrent cells hit it
  instead of re-sending it; the cache is best-effort and falls back to the full uncached prompt if it can't be
  created ([extraction_agent.py:308-312](../../../Agents/memory/extraction/extraction_agent.py#L308-L312)).
- **Prompt.** The post-game / cell prompts ([Agents/prompts/extraction/](../../../Agents/prompts/extraction/))
  compose the shared `SITUATION_STANDARDS` (the same dimensional standard day-summary and the situation-summary
  query use), the naming rule, the epistemic-status rule, and a perspective rule that locks each field to the
  assigned role's point of view.

## Config / defaults

| Setting | Value | Where |
|---|---|---|
| live extractor | per-cell fan-out (`extract_postgame_per_cell`) | orchestrator.py:428 |
| per-game strategy points | off (v7 default: obs-only; SPs synthesized cross-game) | extraction_agent.py:237-240 |
| extraction model | gemini-2.5-pro, primary→backup + retries (live graph; v7 loop uses a cheaper flash tier — experiment_log §8) | extraction_agent.py |
| prefix caching | on, best-effort Vertex context cache | ExtractionConfig.cache_prefix (config.py:73) |
| cell concurrency | max_workers = 6 | ExtractionConfig (config.py:74) |
| situation framework | v6 dimensional fields → `composed_situation` for retrieval | schemas/memory.py |

The v5 single-pass and per-role extractors still live in the package, but only the offline store-builders and
A/B experiments read them; the live graph runs per-cell (config.py:60-70).

## Verification

**Verdict.** The extraction judge is **de-bugged, not calibrated** (🟡 PARTIAL). The engineering hygiene is
genuinely strong — two real judge bugs were found and fixed — but the judge has no human anchor, its original
dimensions saturate at the ceiling, and v7 synthesis quality is unjudged. The full apparatus write-up, with
the L1/L2 breakdown, is [../../evaluation/llm_judge/extraction.md](../../evaluation/llm_judge/extraction.md);
the essentials:

- **Two judge bug-fixes, verified live.** The judge had been scoring `epistemic_compliance` on observations
  (which legitimately use omniscient framing), deflating it by −1.19; and scoring `specificity` on the narrow
  `situation` field while retrieval uses the composed query. Both were corrected in the judge prompt, lifting
  specificity +0.69. These are real improvements to the instrument, made against design intent — not against a
  golden set.
- **Player-ID leakage is a deterministic check, and it works.** A script (no judge) counts IDs in
  observations: 84.3% before the naming rule, 0% after on most models. The one exception is gemini-2.5-flash,
  which still leaks 3-5%; the production 2.5-pro extractor is at 0%.
- **The original five dimensions saturate.** On the 48-game runs, `coverage`, `grounding`, and `epistemic` all
  cluster at 4.00 — near-zero information as a ranker. Only the two dimensions added later, `strategy_depth`
  (3.95) and `novelty` (2.95), produce differentiated scores. So the judge is a gross-quality floor alarm, not
  a fine ranker — the same resolution limit day-summary's judge has.

**What it can't do.** With no human golden and no measure of the synthesized SP store, the judge can flag a bad
extraction but cannot certify a good one, and it says nothing about whether v7's cross-game synthesis is any
good.

## Current-vs-documented gaps (freshness: 2026-07-02)

Ordered by how misleading each is to a reader. Severity weighs likelihood, impact, and detectability together,
not impact alone.

| # | Gap | State | Severity |
|---|---|---|---|
| 1 | **v7 synthesis quality is unjudged** | The extraction judge is never pointed at the synthesized cross-game strategy points. Synthesis is measured only by the loop's outcome slope and one self-described "underpowered" lexical probe. The instrument to judge it exists (`run_extraction_judge`); it has simply never been aimed at the SP store. | Med-High |
| 2 | **Uncalibrated judge** | No human answer key sits behind the scores; the judge was de-bugged against design intent and face-validated, never validated against labels. The cheapest fix is a small human golden — reference points are the game's critical observations, `coverage`→recall and `grounding`→precision. Method: [../../evaluation/llm_judge/golden_set_method.md](../../evaluation/llm_judge/golden_set_method.md). | Med |
| 3 | **Original dimensions ceiling-saturated** | Five of the eight dimensions pin at 4.00 and carry no ranking signal; only `strategy_depth` and `novelty` move. This is a resolution limit, not a claim the extractions are perfect — the same blind-rubric saturation a golden set (gap 2) would break. | Med |
| 4 | **The May study is v5-era; the model question was later refreshed** | The per-role vs single-pass comparison and the model bake-off ran on the v5 `GameStrategyOutput` (obs+SP) schema, n=5-10 games, across a Google→Vertex backend shift; the *directional* per-role win graduated into the live per-cell design, but the May *absolute* per-dimension numbers are stale. The **model** question, however, was re-answered on the live v6_1 store by a v7-era A/B (2026-06-19, `../../v7_final/extraction_coverage_ab_spec.md`; generated obs colocated in `model_comparison/v7_refresh/`): flash-3.5 ≈ pro. That A/B's own recall metric was **verbosity-confounded** (it scored surface form, not captured information, and was overturned by a manual read) — so it needs a semantic-match rebuild before any pro-vs-cheap recall claim scales. | Low |
| 5 | **2.5-flash still leaks player IDs** | 3-5% of observations under gemini-2.5-flash, despite the naming rule; the older model follows the prohibition less reliably. The production extractor (2.5-pro) is at 0%, so this only bites if a run swaps in 2.5-flash. | Low |

**Open work.** The one credible upgrade that would move the verdict is to point the existing extraction judge
at the v7 synthesized SP store (gap 1) and to build a small human golden for calibration (gap 2). Neither is a
priority while extraction is not the binding constraint — the memory system's measured limit is content
quality after dedup and the investigator-transmission cap, not extraction fidelity.
