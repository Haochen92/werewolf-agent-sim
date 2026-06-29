# Metrics / Scoring Instruments — Evaluation Apparatus Report

> **Scope: the apparatus.** The de-lucked outcome proxies (`Agents/compute_metrics.py` /
> `Agents/schemas/metrics.py`) + the validation harness that checks them against win. These ARE the
> instruments both eval tiers depend on, so the L2 question is: **which proxies are *validated* against the
> outcome they proxy for, and at what N.** Design (L0) excluded. Lens + skeleton: [`../report.md`](../report.md);
> ledger: [`../source_map.md`](../source_map.md).
>
> **Verdict by basket: ✅ Town · 🟡 Investigator · ⚠️ Deceiver · 🔴 Discussion.** The town basket is the
> trustworthy core both eval tiers rest on; everything else is partial-to-unmeasured.

## Objective the apparatus targets

A win/loss outcome is too lucky and too coarse to rank skill at N=30. The metrics layer replaces it with
**de-lucked outcome proxies** (opportunity-conditioned rates) — but a proxy is only useful if it actually
tracks winning. The validation harness exists to prove that.

## L1 — the instrument

- **Compute surface** `Agents/compute_metrics.py`: `_compute_base_metrics` (raw counts) →
  `_compute_derived_metrics` (de-lucked rates) → `compute_game_metrics` → `ComputedGameMetrics`, a **~50-field
  flat artifact** (`schemas/metrics.py:214-256`). `push_scores_to_langfuse` (`:519-550`) pushes **every
  non-None field indiscriminately** — no curated-basket filter, so unvalidated/diagnostic/plumbing fields land
  in Langfuse co-equal with validated proxies.
- **Validation harness** `evidence/metrics/proxy_win_monotonicity.py` + `core/stats.py::point_biserial`:
  per-proxy point-biserial r vs that proxy's **own faction's win**, expected sign from a design-intent table;
  reads existing `batch_results/*.jsonl` (zero new games); reported twice (pooled N=50 + memory-OFF-only N=30,
  because the memory treatment moves both proxy and win). The 3-faction refinement re-ran the same discipline
  at N=180. `point_biserial` returns NaN on degenerate inputs (<3 rows / constant proxy / single-class).
- **`score_tier_design` (the typed GameScore projection): NOT BUILT** — markdown design only ("Status:
  DESIGN, not implemented"); no `class GameScore` anywhere. Consequence: the SCORE/DIAGNOSTIC/PLUMBING tiering
  lives only in prose, which is exactly what the indiscriminate Langfuse push above realises.

## L2 — trust, per basket

**Town — ✅ VALIDATED (the trustworthy core).** `correct_elimination_rate` +0.65, `town_mislynch_rate` −0.65,
`serial_killer_lynched` +0.64 (n=50) / +0.85 (n=30), `town_vote_accuracy` +0.62, `mislynches` −0.57 — all
|r|≈0.55-0.65, p<0.01, **in both pooled and OFF-only views**; reconfirmed at N=180. The only unambiguously
validated basket.

**Investigator — 🟡 PARTIAL.** The find-*rate* proxies are **NOT validated** — `threat_find_rate` −0.09,
`wolf_find_rate` −0.14, and `investigator_found_wolf_day` **+0.38, p=0.039 — significantly WRONG-SIGN**
(later find ↔ more wins, plausibly game-length-confounded; not length-normalised). N=180 confirms the dead
floor (find rates ~0). What rescues the channel is **conversion**: `investigator_find_to_lynch_rate` +0.396,
p<0.001 — VALIDATED. (So old v5-pilot investigator claims rest on unvalidated proxies — hypothesis only.)

**Deceiver (wolf/SK) — ⚠️ SPLIT.** *Validated:* `sk_power_roles_killed` +0.323, `sk_kill_rate` +0.258 (raw
+0.61 is survival-confounded → de-lucked), `sk_wolf_kills` +0.303 partial|survival (has a mechanism),
`wolf_unconditioned_blending_rate` +0.270. *Tautology shipped-with-caveat:* `suspicion_drawn` (SK −0.714) is
**outcome-proximate** (votes-at-SK is its only removal path) AND **opponent-coupled** (it's
`town_vote_accuracy` from the other seat — one event, never two pieces of evidence); the in-code comment
carries the caveat. *Unmeasured:* wolf **night-offense null** (+0.104, n.s.), **day-offense unmeasured**
(`wolf_steering_rate` can't tell leading a bandwagon from joining it). The wolf's biggest win-correlate is
`sk_lynched` +0.455 — the town removing the SK, an environmental event, not a wolf action.

**Discussion (metrics-proxy) — 🔴 NULL / DEFERRED.** Phase-1 `wolf_lead_score` r=−0.093 (p=0.51, n=53) —
NULL but *cleanly*: lead-vs-blend is a genuinely distinct signal (decorrelated from vote metrics), the infra
works, but active wolf offense carries no win signal and barely happens (127/180 games had no wolf accusing
the eventual mislynch target). Phase-2 LLM tagger deferred. **NOT the v7 loop tagger** (which is built).

**Cross-cutting L2:**
- **Multiple-comparison exposure:** ~30 proxies tested vs win, **no built-in Bonferroni**; the docs apply it
  by hand where it bites (e.g. `sk_unconditioned_blending` +0.196 p=.019 flagged SUGGESTIVE, fails a ~12-test
  Bonferroni). The monotonicity doc explicitly says "ranks proxies by trustworthiness; not a causal claim."
- **Small-N degeneracy on the wolf basket at N=50** (`wolf_blending_rate`/`dissent_rate` NaN — wolves won
  2/30 OFF); the N=180 refinement is what gives the wolf/SK figures power.
- **Tautology discipline applied** (survival↔win for `sk_nights_survived` +0.555; the de-lucked `sk_kill_rate`
  is the skill-bearing replacement). Good apparatus hygiene.

## Verdict + cheapest upgrade

Per the table at top. **Cheapest *trustworthy* upgrade:** not re-running the starved wolf day-offense channel
(Phase-1 already ran it null at n=53), but **graduating the two NEW validated proxies that already exist in
code but sit outside any tiered basket** — `investigator_find_to_lynch_rate` (+0.40) and
`power_roles_killed_by_evil` (−0.40) are computed and validated but the indiscriminate push gives them no
priority. The cheapest *apparatus* upgrade is **building the `GameScore` projection** (currently design-only),
which stops the Langfuse/judge double-counting of `suspicion_drawn`↔`blending` and survival↔kill-rate twins
**by construction**.

## Evidence (code + L2 artifacts)

- **Code:** `Agents/compute_metrics.py`, `Agents/schemas/metrics.py`, `evaluation/src/core/stats.py`,
  `../../metrics/proxy_win_monotonicity.py`, `../../metrics/discussion_lead_vs_blend.py` (both **point at** the
  canonical `core/stats.py`, not copied).
- **L2 artifacts (pointed-at):** `../../metrics/{proxy_win_monotonicity,town_metric_refinement,
  deceiver_metric_refinement,experiment_log,score_tier_design,discussion_scoring_plan}.md` — the validation
  docs are a **shared hub** referenced from 6 other evidence folders (point-at, per the "store the pointer"
  rule).

## Colocation call (JIT, 2026-06-28)

**Stays put — pointed-at.** The validation docs are a shared cross-folder hub; moving them breaks 6 inbound
refs. (Note: `../../metrics/variance_reduction_levers.md` is **mis-filed** in metrics/ — it's A/B
*methodology*, not a metric — and is handled in the [methodology report](../methodology/report.md).)

*(Inspected 2026-06-28. source_map metrics claims verified accurate; sharpenings folded into the ledger.)*
