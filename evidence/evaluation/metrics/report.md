# Metrics / Scoring Instruments — Evaluation Apparatus Report

> **Scope: the apparatus.** The de-lucked outcome proxies (`Agents/compute_metrics.py` /
> `Agents/schemas/metrics.py`) + the validation harness that checks them against win. These ARE the
> instruments both eval tiers depend on, so the L2 question is: **which proxies are *validated* against the
> outcome they proxy for, and at what N.** Design (L0) excluded. Lens + skeleton: [`../report.md`](../report.md);
> ledger: [`../source_map.md`](../source_map.md).
>
> **Verdict by basket: ✅ Town · 🟡 Investigator · ⚠️ Deceiver · 🔴→🟡 Discussion.** The town basket is
> the trustworthy core both eval tiers rest on; everything else is partial-to-unmeasured. **2026-07-02
> metrics-audit update (dated section at tail):** a wolf-night proxy was *rescued* and the first
> town-discussion proxy *discovered* (both diagnostic-tier, not basket-promoted); the wrong-sign
> investigator scare *dissolved* at N; and both the scheduler-starvation and a wolf-offense-helps
> hypothesis were *falsified*. Read the tail for what moved.

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
- **`score_tier_design` (the typed GameScore projection): still NOT BUILT** — markdown design only; no
  `class GameScore`. But a **minimal trust tiering shipped 2026-07-02** as a guardrail short of the full
  projection: `Agents/compute_metrics.py` now carries `VALIDATED_BASKET_METRICS` (11 point-biserial-checked
  proxies), `DIAGNOSTIC_METRICS` (3 audit-graduated, context-not-basket), and `DO_NOT_USE_METRICS` (5
  wrong-sign/uninterpretable); `push_scores_to_langfuse` renames the DNU set with a `dnu_` prefix and tags
  every score with its tier. So a *validated wrong-sign* proxy can no longer be silently averaged into a
  verdict. The full GameScore projection (which would stop the `suspicion_drawn`↔`blending` double-count
  *by construction*) remains the deferred apparatus upgrade.

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

---

## 2026-07-02 metrics-audit update (proxy rescue/discovery + structural-bias falsification)

A $0, zero-LLM audit re-ran the incumbent validation discipline on N=180 v6ab (with split-half
confirmation and pre-registered signs) to probe the basket's *holes* rather than its errors. Full logs +
per-candidate verdicts stay in `evidence/metrics/metrics_audit/` (pointed-at, not copied):
[`proxy_discovery_log.md`](../../metrics/metrics_audit/proxy_discovery_log.md) (workstream 1) and
[`scheduler_bias_log.md`](../../metrics/metrics_audit/scheduler_bias_log.md) (workstream 2). What moved:

**Deceiver (⚠️→ one diagnostic added).** `wolf_power_kill_rate` is the **first wolf-night proxy to clear
the bar** — but only once conditioned on the environment. Pooled it is null (+0.13, n.s.); the mechanism
is that wolves *cannot win when `sk_lynched=0`* (the SK wins by default), so 77/180 games carry zero
wolf-skill information yet dilute the flat correlation. Within `sk_lynched=1` (n=103, 39 wolf wins) it is
**+0.31 (p=.002)**, split-half stable (+0.26 / +0.38) and robust to partialling out both `sk_lynched` and
`game_length` (+0.190, p=.011). This reframes the earlier "wolf night-offense doesn't convert (−0.10)" as
a **not-conditioned-on-the-SK-axis artifact**, not an absence. Adopted **diagnostic**, not basket-promoted
(pending a larger wolf-win N). Corollary: *the flat point-biserial is structurally miscalibrated for wolf
proxies* — any wolf null in the older refinement docs should be re-read as "diluted," not "absent."

**Discussion (🔴→🟡, town side).** `town_accusation_precision` (town accusations on true threats / all)
is the **first town-discussion proxy**: **+0.34 (p<.001)**, both halves p≤.002, Bonferroni-passing.
**Accepted as diagnostic, not independent evidence** — it couples with the already-validated
`town_vote_accuracy` at r=+0.558 (~31% shared variance), so it re-expresses the "town IDs threats"
construct on the discussion surface rather than confirming a good town twice. The metrics-side wolf
lead-vs-blend proxy *stays 🔴 null* — and the audit sharpened *why*: `wolf_accusation_on_town_rate` was
pre-registered **+** (framing offense should help wolves) and came back **−0.33 (p<.001, both halves)** —
a **pre-registered sign FALSIFICATION**. Wolves that attack town lose more; wolves that accuse real
threats win more, the blending mirror of the validated `wolf_unconditioned_blending_rate` (+0.27). Only
the pre-registration makes that a legible finding rather than a silent flip.

**Investigator (🟡, unchanged verdict, softened rationale).** The v5 scare — `investigator_found_wolf_day`
**significantly wrong-sign** (+0.38, p=.039, n=30) — **dissolves at N=180 to +0.15 n.s.**; neither
length-normalizing nor partialling `game_length` pushes it to the expected negative. So the sign confusion
was **small-N noise plus mild length coupling, not a robust backwards relationship**. The find-rate cluster
stays quarantined (`dnu_`), but the rationale downgrades from "significantly wrong-sign" to "null; the
earliness sign is N-fragile." Only the conversion proxy (`investigator_find_to_lynch_rate`) is validated,
now joined by the confirmed timing refinement `investigator_find_next_round_convergence` **+0.31 (both
halves)** — adopted diagnostic, transmission-cluster. A related program is **BLOCKED**: claim-conditioned
joins need `DaySummary.structured.role_claims`, present in **0/180** v6ab and 0/50 v5 (an A4 addition
postdating both epochs) — unbuildable until a post-A4 batch is itself win-validated.

**The nulls are NOT scheduler artifacts (structural-bias falsification).** A sibling workstream tested
whether the role-blind discussion scheduler *starves* the behaviors these proxies measure. It found **no
floor-starvation**: investigator and wolf are the floor-*richest* roles (turns/alive-day 2.45 and 2.04;
investigator spoke-zero rate 0.10), pending-find investigators speak before the vote **58/58 (100%)**,
wolves hold pre-bandwagon proactive floor on **76.5%** of pile-on days (and decline 35% of proactive
offers), and the 12 unconverted investigator finds decompose to **0 no-floor / 0 late-floor** vs 7
withheld / 5 revealed-but-ignored. So the wolf-steering null and investigator non-conversion are
**agent/town behavior, not scheduler-shaped**. One question stays open: the novelty gate's role-selectivity
is **unmeasurable from existing records** (a gated pass and a voluntary pass write the identical marker) —
the 2-field instrumentation to fix it shipped, so a future gate-selectivity audit is unblocked on new
records only.

**The whiff-visibility finding (prices a held game-design change).** When a wolf's night-kill hits the
night-immune SK, the kill *silently whiffs* — and the wolf **never notices 68% of the time** (vs 31% on an
*announced* heal; the wolf's noticing rate tracks visibility). The vigilante, handed an explicit immune
note, converts the whiff to day-action **0.75–0.89 from a ~0 base**. So the binding layer is **visibility,
not wolf skill or scheduler floor** — evidence that supports (does not decide) the held change to disclose
failed kills to the wolf, priced honestly at an epoch reset. Relevant to metrics because `sk_lynched`
(+0.455) is the wolf's biggest win-correlate and is currently an *environmental* event, not a wolf skill.

**Adoption + tiering (shipped).** The three survivors (`wolf_power_kill_rate`, `town_accusation_precision`,
`investigator_find_next_round_convergence`) were adopted into a **`DIAGNOSTIC_METRICS`** tier beside — not
inside — `VALIDATED_BASKET_METRICS`, pushed with `tier="diagnostic"` and carrying their caveats as
attribute docstrings (A2's `sk_lynched` conditioning, B1's r=+0.558 coupling, C1's refinement status). The
`dnu_`-prefixed `DO_NOT_USE_METRICS` (the investigator find-rate cluster + `wolf_steering_rate`) keep them
out of any silent average. Basket promotion of the diagnostics remains pending a larger wolf-win N. All
$0/zero-LLM, ran at `4b1449e`; 9 + 11 logic tests, suite green. Label caveat carried forward: the
accusation graph rides `addressed_targets` self-labels (tuned for scheduling, not measurement), whose
error rate as measurement input is still uncharacterized.

*(Update inspected 2026-07-02 from the metrics-audit logs; findings verified against
`proxy_discovery_log.md` §3 and `scheduler_bias_log.md` §3 + the tiering constants in
`Agents/compute_metrics.py`. Diagnostic-tier, not basket-promoted — the trustworthy core is unchanged.)*
