# Discussion-scoring plan — closing the "discussion is unscored" gap

**Thesis.** Every metric we have scores the *board* (votes, kills, lynches, protections);
nothing scores the *discussion* that drives them. A wolf can talk its way out of a corner and
the scorecard only sees whether it was eventually lynched; a villager can lead the room to the
right read and we only see the vote. Discussion is the highest-leverage, lowest-observability
part of the game and is currently invisible. This plan closes that by **composing the layers we
already persist** (situation state × discourse events × ground truth) rather than enriching the
frozen situation schema.

Three gaps, one strategy:

| Gap | Currently | Closed by |
|---|---|---|
| Discussion quality unscored | only board outcomes | per-day state-trajectory metrics (exposure/info transitions) |
| Deception offense unscored | only concealment + board | fake role-claim rate (from structured day-summary `role_claims`) |
| Wolf day-offense unmeasured | `wolf_steering_rate` conflates lead/blend | lead-vs-blend from `addressed_targets`+`seq` |

Cross-cutting principles (already agreed): recompute-verify every metric on the real compute
path; determinism lives in the rollup, LLM labeling is fine for semantic discussion; side-fields
are never fed back to agents; compose layers, don't enrich the frozen situation schema.

---

## Codebase validation (2026-06-18) — premises checked before building

All load-bearing premises were verified against the code. Two corrections folded in:

- ✅ **Situation/state schema has every field** (`Agents/schemas/memory.py`): `exposure_class`
  (safe/exposed), `info_landscape_class` (info_rich/starved), `consensus_direction`,
  `divergence_sign`, `heat_now`, `public_private_text`. These are the transition vocabulary the
  tagger will reuse.
- ✅ **`day_channel` carries the discourse layer** (`Agents/schemas/game_events.py`):
  `addressed_targets[].stance ∈ {accusation, defense, agreement, neutral}` + monotonic `seq`.
  Confirmed *populated* in the v6ab batch (59% of entries tagged; every entry has `seq`;
  `target` is a `player_id`, joins cleanly to `voted_player`). Phase 1 buildable now, free.
- ✅ **`DaySummaryOutput`** (`Agents/schemas/output.py:148`) has `village_dynamics`
  (information_landscape / consensus / drivers) + `accusations` + `role_claims` + `alliances`
  — **and it IS fed to agents** (serialized into every later prompt). So the core call stands:
  a **separate post-hoc tagger, NOT a field on day_summary** (touching that call is
  freeze-sensitive: gameplay + gold-label drift). `role_claims` + `drivers` already exist as
  partial fake-claim / influence signal.

**Correction 1 — the store does not retain `exposure_class` structurally.** The v6_0 RAW store
(`reextract_cells.py`, 919 obs / 17 cells / 20 games) folds exposure/heat/info-landscape into
the composed `situation` free-text and drops the structured key (it keeps `consensus_direction`,
`players_alive`, `distance_to_parity`, `is_swing`, `net_verdict`, `source_game_winner`,
`role_faction_won`). So the previously cited "488 safe / 327 exposed" distribution is **not
reproducible from the store** — and it doesn't matter: this *strengthens* the conclusion that
the per-day tagger is not merely the de-confounded option but the **only** one (the enum isn't
even queryable, and the obs are selection-gated). (`6.8 obs/(game,role)` does check out.)
  - Side note: per the schema, `exposure_class`/`info_landscape_class` are declared *reranker
    gates*; dropping them in the store means the reranker can't gate on its own declared fields.
    Splitting them into queryable fields next build helps **retrieval**, not this metric. Worth
    confirming the live/deduped store has the same drop (would be a real reranker bug).

**Correction 2 — the store is already full-DAG**, not villager-only (919 obs across all 17
role×phase cells incl. wolf/SK). Doesn't change the plan (flagship is fresh-tagged), noted for
accuracy.

---

## Phase 0 — finish & freeze the board-metric layer (deterministic, no LLM)
Close the deceiver board set so LLM-layer work builds on a stable base. Ship the pending
descriptive metrics, implement `suspicion_drawn` with the per-member alive-window denominator,
recompute-verify each on `batch_results/v6ab_*.jsonl`. No gameplay/prompt impact.

## Phase 1 — validate discussion-signal on EXISTING data (cheap, no new run) — **DONE, see below**
Gate A: does wolf lead-vs-blend (discourse layer) carry signal / beat `wolf_steering_rate`?

## Phase 2 — build the post-hoc state-tagger (FIRST LLM SPEND — needs green light)
A dedicated tagger (`evaluation/experiments/`), **not** bolted onto day_summary, because:
freeze-safe (day_summary feeds agents + conditions gold labels); uniform by construction
(every living player, every day → denominator = player-days, dodges the 6.8-obs selection
confound); runs on the existing 180 now (reads `day_channel` 1..d + roles, contemporaneous, no
outcome leakage). Output = per-(player, day) `exposure_class` + info read. Roll up
deterministically: occupancy, exposed→safe recovery rate, info_starved→info_rich progression.
**Gate B (real go/no-go for the family):** does exposure-trajectory *lead or add* signal beyond
`suspicion_drawn`? If it just tracks it → redundant → stop.

## Phase 3 — compose the rich score (only if Gate B passes)
Influence = state-transition × (`addressed_targets`+`seq`); correctness = × ground-truth roles;
deception offense = persist structured `DaySummaryOutput` (byte-identical, no re-prompt) →
fake role-claim rate from `role_claims`.

## Phase 4 — consolidate, tier, document, freeze
Split `ComputedGameMetrics` into SCORE / DIAGNOSTIC / PLUMBING tiers; write the
available-but-deferred catalog; update evidence + memory.

**Decoupled:** the extractor soft-steer fix runs in parallel and blocks nothing here (it improves
selection *quality*; the tagger owns *coverage*). Shared root cause, different components.

---

## Phase 1 result — Gate A (2026-06-18, `discussion_lead_vs_blend.py`, 180 games)

Wolf day-offense split into **lead** (early in the accusation sequence against the eventual
town-mislynch target) vs **blend** (joined an already-forming pile), from `addressed_targets`
(stance=accusation) ordered by `seq`. lead_score = `1 − rank/(n_accusers−1)` per (wolf, mislynch
target); compared against the re-derived vote-level metrics on the same games.

```
games: 180 | games w/ >=1 wolf accusation on a mislynch day: 53 | lead instances: 73

win-correlation (point-biserial vs wolf_won):
  wolf_steering_rate     r=+0.308 p=0.0008 n=116   (vote-level: majority of wolves vote the lynch)
  wolf_blend_rate        r=+0.270 p=0.0004 n=165   (unconditioned vote blend)
  wolf_lead_score        r=-0.093 p=0.5075 n=53    (active offense: lead the accusation)  NULL
  wolf_lead_binary       r=-0.122 p=0.3840 n=53                                           NULL

decorrelation (pearson):
  lead_score ~ wolf_steering_rate  -0.043
  lead_score ~ wolf_blend_rate     +0.054
```

**Verdict: Gate A FAILS for the metric, but cleanly — and it's a substantive finding, not a
noise result.**

1. **lead-vs-blend is a genuinely distinct signal** (decorrelated from both vote metrics,
   |r|<0.06) — so the discourse-layer *infrastructure* works (join is clean, `seq` orders,
   `addressed_targets` populated). Gate A failing does **not** condemn Phase 2.
2. **But active wolf offense carries no win signal** (r=−0.09, n.s., sign even slightly negative)
   **and barely happens**: in 127/180 games *no* wolf publicly accused the eventual town-mislynch
   target at all. The mislynch is town self-destructing (consistent with the prior "town
   mislynches itself 109/169").
3. **This confirms "wolf = concealment-dominated" at the action level** — previously inferred from
   a measurement gap, now measured directly: the channels that predict wolf wins are *blending*
   (steering +0.31, blend +0.27 — both "vote with the crowd"); *leading* the mislynch does not.
   So the "wolf day-offense unmeasured" gap is now **measured and null**, not open.
4. Note `wolf_steering_rate` is +0.31 / p<.001 on this batch (the earlier "+0.17 n.s." was a
   different epoch) — a *higher* bar than the plan assumed, which lead_score still fails.

**Disposition:** keep `wolf_lead_score` as a DIAGNOSTIC (it describes a real, rare behavior),
not a score-tier metric. Caveat: one operationalization (rank among accusers); an alternative
("accused before the majority of eventual lynch-voters spoke") is possible, but with 53/180
denominator the channel is starved regardless — refinement won't rescue it.

**Impact on the plan:** Phase 1's specific hope (lead-vs-blend = free win) is dead. The
discourse-layer infra is validated, so **Phase 2 (exposure-trajectory tagger) remains the live
path** and its Gate B is the real go/no-go. Phase 2 is the first LLM spend → awaiting green light.
