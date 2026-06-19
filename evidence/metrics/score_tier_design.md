# GameScore tiering — design note (2026-06-18)

**Status:** DESIGN (agreed), not implemented. Captures the metric-surface tiering decision so a future
consumer (LLM judge, frontend MVP score, Langfuse headline) builds against a clean interface, not 57
flat fields.

## The problem (valid concern; not "too many metrics")
~57 `ComputedGameMetrics` fields, but only ~13 are real proxy signals (2–3 de-lucked proxies × 6 roles
= parsimonious — that's the deliverable). The depth is fine; the **surface is flat and undifferentiated**:
1. **Tiering lives in markdown, not the schema** — a consumer can't tell a validated proxy from a raw
   vote-total from a diagnostic split; the LLM judge weights them co-equal.
2. **Correlated signals get double-counted** — fed to a judge/sum, `suspicion_drawn`↔`blending`,
   nested `power_roles_killed_by_{wolves,evil}`, steering↔blending read as independent evidence when
   they're one phenomenon. Degrades the judge.
3. **Every metric is a denominator trap** — 2 bugs in 3 turns; verification cost scales with count.

## Mechanism — typed `GameScore`, by PROJECTION (not a registry, not a forced record split)
A **real typed model** is the honest boundary: a judge handed a `GameScore` *cannot* see diagnostics →
double-counting impossible by construction, not by discipline.
- **Default: projection.** `ComputedGameMetrics` keeps computing everything (flat, back-compat,
  drill-down); `.score()` returns a `GameScore`; `.judge_view()` / `.mvp_view()` if they diverge.
  No record migration (existing flat `computed_metrics` + readers untouched).
- **Optional: nested** `record.score` / `record.diagnostics` — cleaner record but a `schema_version`
  bump + recompute (deterministic, doable). Default to projection unless the nested record is wanted.

## Two principles, two purposes (don't conflate)
- **COMPUTE — every distinguishable ACTION pattern gets a spot, including null ones.** A correlation
  today can DECOUPLE under treatment (memory could move one twin without the other); collapsing
  pre-emptively would hide the very effect we'd want to see. This is a *lens for finding actions/gaps,
  not a rigid taxonomy.* Most computed actions live in **diagnostic**.
- **SCORE — one representative per EMPIRICALLY-independent axis, the most-upstream member** (proximity
  framework: drop outcome-proximate twins to diagnostic). This is the *aggregation* rule — don't sum
  statistical twins.

**Per-faction scoring dissolves the cross-seat mirror:** scores are per-faction, so `suspicion_drawn`
(wolf-concealment) and `town_vote_accuracy` (town-day-quality) never co-occur in one aggregate. The
only overlap that matters is *within*-faction (e.g. `suspicion_drawn`↔`blending`).

## `suspicion_drawn` — kept, as the EFFECT-side of the concealment axis
Not valueless for being an outcome: it reflects blend + redirect ability and is **one of our few
discussion-surface signals** (almost everything else is vote/night mechanics). It's the downstream
**effect**; `blending` is an upstream **cause** on the same axis — keep both (cause+effect aids
diagnosis: did the action move or the result?), but the axis is represented **once** in an aggregate.
It is **composite**: low suspicion = good vote-blend (a) + good verbal redirect (b) + not-caught-in-a-lie
(c) [skills] + not-a-priority-target (d) + weak opposing town (e) [noise]. (b),(c) are the **discussion
actions we don't measure yet** → `suspicion_drawn` is a **stand-in for them until built**, and
**decomposing its causes IS the discussion-metric program.** Tag: composite + opponent-coupled.

## Provisional score basket (one per empirically-independent axis; adjust in the model)
- **town:** `town_vote_accuracy` (day-decision), `serial_killer_lynched` (keystone — kept per user),
  `power_roles_killed_by_evil` (night protection), `investigator_find_to_lynch_rate` (info conversion),
  `vigilante_wolf_kills_rate` (removal).
- **wolf:** `wolf_unconditioned_blending_rate` (concealment; `suspicion_drawn` = effect-side companion).
- **SK:** `sk_unconditioned_blending_rate` (suggestive), `sk_kill_rate` (offense), `sk_killed_wolf`
  (cross-faction).
Everything else → **diagnostic** (validated-but-correlated, conversions, splits, outcomes incl.
suspicion/survival) or **plumbing** (num/denom pairs, raw counts, exit methods, context).

## Builds the action-lens revealed (noted, not in this pass)
- **verbal-blend** (discussion blending, distinct from vote-blending) — `addressed_targets`/messages.
- **wolf-leads-the-SK-lynch** (the wolf's rival-removal *action*, vs the unconverted `wolf_attacked_sk`).
- **decompose `suspicion_drawn`'s causes** = the discussion-action metric set (verbal-blend, redirect
  quality, claim/lie consistency).
- **`day_summary` "who led the lynch"** (LLM) — serves investigator-conversion attribution, wolf-led
  mislynch, AND the confirm-only conversions in one build.
