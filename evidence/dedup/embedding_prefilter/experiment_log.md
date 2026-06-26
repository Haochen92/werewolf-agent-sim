# Embedding pre-filter calibration — experiment log

**The system, in one breath.** A werewolf-playing agent extracts strategy lessons after every game —
*observations* (situation → approach → outcome) and *strategy points* (situation → action) — into a
persistent memory store. Played over many games the store fills with near-duplicates, so a dedup pass
trims them. This chapter is the **cheapest layer of that pass**: a deterministic, **no-LLM**
embedding-similarity pre-filter that sits in front of the LLM dedup and auto-decides the obvious cases.

**Executive summary.** The pre-filter auto-keeps clearly-novel and auto-discards clearly-duplicate
entries from an embedding-similarity score, sending only the ambiguous middle to the LLM. Calibrated to
**zero error** on a 65-case human golden set and a 232-case cross-game set, it auto-decides **~23%** of
cases (live: SP `action_sim` discard ≥0.93 / keep <0.81; OBS `content_sim` discard ≥0.96 / keep <0.935).
Three attempts to push coverage higher — 3072 dimensions, the `SEMANTIC_SIMILARITY` task type, and
multi-dimensional boundaries — **all failed**, for one reason: embeddings capture **topic, not stance**,
so two pieces of advice on the same topic that say *opposite* things embed ~95% alike (**Case 155**:
94.6% similar, contradictory advice). The **~15-30% ceiling is a property of the embedding space, not a
tuning shortfall** — the layer is a conservative triage, and the LLM is irreducible for the middle.

**What to read this as.** A topical deep-dive on the auto-decision layer, in the order the work happened
(late May 2026): design → calibrate → validate → try to beat the ceiling → explain it → instrument. The
cross-dedup chronology is the [parent overview](../experiment_log.md); the negative ablations are kept
*as tried and rejected*, because the "no improvement" findings are the point. Further reading:
[report.md](../report.md) (how it works today) and [per_extraction](../per_extraction/experiment_log.md)
(the LLM dedup this feeds). Eval artifacts: [data/](data/).

---

## Design — a two-ended short-circuit on the discriminating field

Per-role extraction produces 2-3× more items than single-pass (4 LLM calls/game × 4-8 items), which
overwhelms the LLM dedup pipeline. The pre-existing flow short-circuited at only *one* end: it
auto-discarded on the **situation** search score above a high threshold and otherwise paid for an LLM
call — so clearly-*novel* entries still cost a call that only ever said "keep," and the situation score
conflated *same situation* with *same prescription* (two entries can share a situation yet recommend
opposite actions).

The redesign decides on a **more discriminating field** and short-circuits at **both** ends:

- **Strategy points** — embed and compare the **action** field; take the max `action_sim` over candidates.
- **Observations** — embed and compare the **full content** (`situation + approach + outcome`); take max
  `content_sim`.

`sim ≥ discard threshold → auto-discard`; `sim < keep threshold → auto-keep`; otherwise → LLM. On any
embedding failure it falls through to the LLM (fail-open). The 0.55 situation search-score stays as the
candidate-gathering net; only the auto-decision layer changes.

**The two ends are not symmetric, and that drives the thresholds.** An auto-**discard** is irreversible —
a genuinely novel, rare-situation lesson is gone for good — whereas an auto-**keep** is just recoverable
bloat that the offline batch pass can later collapse. So the dangerous end is discard, which is why the
discard thresholds sit at the **near-identical-text extreme** (0.93 / 0.96, well above the keep thresholds
0.81 / 0.935) and why, wherever the calibration is uncertain, the layer defaults to the LLM rather than
auto-discarding.

## Calibrate — zero-error boundaries on the golden set (65)

Using the 65-case golden label set (`dedup_v2_golden_labels.json`: D=30, M=5, K=29, M/K=1), embedded with
`gemini-embedding-001` at 1536D (cached to `golden_eval/embedding_cache.json`), the D/K distributions show
a clean gap:

- **Strategy points** (25: D=10, K=15): all D `action_sim` ≥ 0.813 (5/10 above 0.90), all K ≤ 0.899 →
  zero-error boundary discard ≥0.90, keep <0.81.
- **Observations** (40: D=20, K=19, M=1): all D `content_sim` ≥ 0.936, all K ≤ 0.929 → zero-error boundary
  discard ≥0.96, keep <0.935. (Field-level approach/outcome sims overlapped heavily; the full
  concatenation separates cleanest.)

## Validate — the cross-game set (232) dissolves a small-sample artifact

The golden set holds only "hard" cases (sit_sim 0.70-0.91), so it could be overfit. To check, a broader
distribution: load extractions from 5 games into a store, search extractions from 5 *different* games
against it (`auto_dedup_build_v1_cross_game.json`) → **232 cases** (116 SP + 116 obs), genuinely-novel
items alongside structurally-similar ones. Each was labelled D/K by running the production dedup prompt
through two models:

| Labeler | D | K | Agreement w/ 3.5-flash |
|---|---|---|---|
| gemini-3.5-flash | 93 | 139 | — |
| gemini-3.1-flash-lite | 144 | 88 | 75.4% (175/232) |

(Flash-lite is heavily discard-biased — 54 cases it calls D where 3.5-flash says K, only 3 the reverse —
matching its known over-discard from the prompt-tuning work.)

**The catch:** the golden SP gap at 0.90 was a 25-case artifact. The 116 cross-game SP cases interleave
heavily in 0.83-0.93 (14/41 D below 0.90; 20/75 K above 0.90), so 0.90 is too aggressive a discard line.
The zero-error boundaries on the broader set (identical for *both* labelers):

| Type | Metric | Discard | Keep | Auto-rate (3.5-flash labels) |
|---|---|---|---|---|
| Strategy point | action_sim | ≥0.93 | <0.81 | 14.7% (12D + 5K) |
| Observation | content_sim | ≥0.96 | <0.93\* | 31.0% (7D + 29K) |

\*Production keeps the **more conservative golden value, <0.935** — the cross-game set is clean even at
the looser 0.93, but 0.935 errs toward the LLM. Live constants
(`Agents/memory/deduplication/config.py`): SP `0.93 / 0.81`, OBS `0.96 / 0.935`. SP discard is pinned at
0.93 because even flash-lite — the *discard-biased* labeler — won't auto-discard below it; 0.90 is too
aggressive.

**What it buys, in system terms.** Across the 232 cases: SP 10.3% auto-discard / 4.3% auto-keep / 85.3%
LLM; Obs 6.0% auto-discard / 25.0% auto-keep / 69.0% LLM — **~23% of dedup decisions resolve with no LLM
call.** Against the 2-3× extraction inflation that motivated the layer, that's roughly a quarter of the
dedup load taken off the LLM; the observation auto-keep (unseen-game items below the keep line are
reliably novel) is the biggest single win. (Absolute cost/latency wasn't separately measured — coverage
is the reported figure.)

## Try to beat the ceiling — three ablations, all negative

**3072 dimensions + `SEMANTIC_SIMILARITY` task type** (2×2 factorial, both datasets). Hypothesis: a finer
and/or symmetric embedding might separate D from K better. Zero-error auto-rates:

| Condition | SP golden (25) | SP cross-game (116) | Obs golden (40) | Obs cross-game (116) |
|---|---|---|---|---|
| 1536 + default | 24% | 14.7% | 30% | 31% |
| 1536 + SEMANTIC_SIM | 36% | 16.4% | 40% | 24.1% |
| 3072 + default | 24% | — | 27.5% | — |
| 3072 + SEMANTIC_SIM | 56% | 12.9% | 40% | 25% |

The golden set *overstates* the gain (too few high-sim K cases to expose the cost); on the larger
cross-game set the net auto-rate **drops** (SP 14.7%→12.9%, Obs 31%→25%), because the wider keep zone is
paid for by a tighter discard zone. **Decision: keep 1536 + default** — most robust on the real
distribution.

**Multi-dimensional boundaries.** Hypothesis: a second axis could lower a threshold — for SP, require
`action ≥X AND situation ≥Y`; for obs, use `min(approach, outcome)` for keep. Both fail: in the SP
interleaving zone, D and K span the *full* situation_sim range (complete overlap on both datasets), so
situation_sim adds no separating power; and obs field-level sims are too noisy (genuine duplicates phrase
fields differently — `field<0.90` misfires on 16-32 D cases). **Decision: the 1D signals are optimal.**

## The ceiling, explained — topic, not stance

Every ablation lands on the same wall, and **Case 155** shows why (action_sim 0.946 at 3072 dims, 0.913
at 1536):

> **NEW action**: "Prioritize investigating players who are actively pushing narratives, dismissing
> evidence, or creating deadlocks, rather than players who are already under heavy suspicion or confirmed
> roles, to maximize the chance of identifying a wolf."
>
> **Best candidate action**: "Avoid investigating the most vocal leader or the player most likely to be
> targeted by the wolves. If they are killed, your investigation is wasted; if they are saved by the
> healer, they are already soft-confirmed to the village, making your private investigation redundant.
> Instead, target moderately active players who are harder to read behaviorally."

These embed **94.6% similar** because they share topic, role, phase, and vocabulary — yet the advice is
*opposite* (go after the most active vs. avoid the vocal leader and target moderately-active players).
This is a genuine KEEP. It is the same limitation as "invest in crypto" vs. "don't invest in crypto"
embedding alike: the disagreement lives in the *relational structure* of the advice (target X *instead
of* Y), which embeddings flatten into a topic-level average. A spot-check of the 8 highest-similarity K
cases (0.916-0.946) found 6 clearly-genuine K and only 2 borderline — high similarity reflects topical
overlap, not prescriptive agreement.

This is why **every** lever failed: the D/K interleaving zone (action_sim 0.83-0.93) is irreducible; more
dimensions capture finer *topic* but not *stance*; `SEMANTIC_SIMILARITY` reprojects the space but adds no
relational reasoning; situation_sim is identical for D and K (the situation genuinely *is* similar — the
ambiguity is in the action); field-level sims amplify phrasing noise. So the pre-filter is correctly a
**conservative triage**: near-identical text → safe auto-discard; clearly different topic → safe
auto-keep; the topic-shared middle (agree or disagree?) is the LLM's, and no threshold tuning crosses
that line without sacrificing correctness. The **~15-30% auto-rate is that ceiling**, not a tuning miss.

## Instrument for the future — and the open loop

The calibration would have been far cheaper if similarity scores had been logged from the start (we had
to rebuild a dataset and re-embed frozen artifacts). Now every dedup decision logs its full
`similarity_scores` to Langfuse (`DedupResult` / `DedupCase`; per-candidate sims + the max used), and
`DedupStats` distinguishes `embedding_auto_kept` / `embedding_auto_discarded`. Future tuning reduces to
*pull traces → sweep* — the LLM's decisions on the non-auto cases accrue as free labels, with the golden
set as the principled anchor.

**Open loop (honest):** the layer runs live in every store build, but that wild-trace **re-validation** —
the whole reason the instrumentation exists — **has not been run yet**. "It's live" is not yet "and the
production data agrees"; that's the next step, and future threshold changes should be driven by it (and by
downstream retrieval quality) rather than more calibration sweeps.

## Current live state (2026-06-25)

The thresholds above are live in the online pipeline (`config.py`: SP 0.93/0.81, OBS 0.96/0.935), applied
per new entry, short-circuiting both ends with LLM fallback in the middle. One thing postdates this work:
the **deterministic gate now runs *before* the pre-filter**, so candidates are already
role/phase/bucket-homogeneous when similarity is computed (see [report.md](../report.md)). The ~15-30%
ceiling is unchanged — it's the property of the embedding space explained above, not a tuning target.
Full current-vs-documented gaps: [report.md](../report.md) § *Current-vs-documented gaps*.

## Artifacts

| File | Description |
|---|---|
| `Agents/memory/deduplication/prefilter.py` | Production pre-filter: `_embedding_prefilter_strategy_point()`, `_embedding_prefilter_observation()` |
| `evaluation/experiments/eval_auto_dedup.py` | Calibration sweep: embeds cases, caches, sweeps threshold grid, reports Pareto frontier |
| `evaluation/experiments/auto_dedup_dataset_builder.py` | Builds calibration datasets from extraction JSONL files |
| `evaluation/experiments/auto_dedup_labeler.py` | Labels auto-dedup cases via LLM for golden label creation |
| `eval_sets/auto_dedup_v1.jsonl` | Same-game calibration dataset (192 cases) |
| `eval_sets/auto_dedup_v1_cross_game.jsonl` | Cross-game calibration dataset (232 cases) |
| `evidence/dedup/golden_eval/embedding_cache.json` | Cached embedding sims for 65 golden cases |
| `data/cross_game_embedding_cache.json` | Cached embedding sims for 232 cross-game cases |
| `data/cross_game_golden_labels.json` | 232 golden labels from gemini-3.5-flash |
| `data/cross_game_golden_labels_flash_lite.json` | 232 golden labels from gemini-3.1-flash-lite |
| `data/golden_embedding_cache_3072_dims.json` | Golden set at 3072 dims + SEMANTIC_SIMILARITY |
| `data/cross_game_embedding_cache_3072_dims.json` | Cross-game at 3072 dims + SEMANTIC_SIMILARITY |
| `data/golden_embedding_cache_3072_dims_default_task.json` | Golden set at 3072 dims + default task type |
| `data/golden_embedding_cache_1536_dims_semantic_sim.json` | Golden set at 1536 dims + SEMANTIC_SIMILARITY |
| `data/cross_game_embedding_cache_1536_semantic_sim.json` | Cross-game at 1536 dims + SEMANTIC_SIMILARITY |
