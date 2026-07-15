# De-lucked Proxy Metrics — system hub

**What this is.** The one-page assembly of the de-lucked proxy-metrics system, which spans ~7
locations. Read this first if you want everything needed to judge the system's reliability from a
single page.

**What the system is.** Per-role **de-lucked outcome proxies**: decision-level scores graded against
ground-truth roles, then *normalized by opportunity* so a proxy ranks skill rather than the coin-flips
baked into a raw win/loss ("de-lucked" is the house label — read it as *opportunity-normalized*, bounded
precisely in `report.md` §1). A proxy is only trusted once it is shown to track its own faction's win.
This measurement core is what both eval tiers rest on.

## THE MAP

| Piece | Where | Role |
|---|---|---|
| Production computation | `../../Agents/compute_metrics.py` + `../../Agents/schemas/metrics.py` | Emits the 63-field `ComputedGameMetrics` per game; carries the `VALIDATED_BASKET` / `DIAGNOSTIC` / `DO_NOT_USE` tiers. |
| Validation harness | `../../evaluation/src/instrument_validation/proxies/` | The 7 standing runners: `proxy_win_monotonicity` · `proxy_rescue` · `accusation_metrics` · `claim_conversion` · `diagnose_wolf_sk_proxies` (promoted 2026-07-04) · `leverage_anchor_separation` (promoted 2026-07-04) · `proxy_followup_rescue` (2026-07-07: incremental-validity + vigilante re-test, both null); plus `metrics_common` (shared N=180 loader + pre-registered split). |
| Regression tests | `../../tests/test_metrics_audit_proxies.py` · `test_diagnostic_metrics.py` · `test_wolf_blending_metrics.py` | Lock the tiering + audit-graduated proxies. |
| Trust verdict | `../evaluation/metrics/report.md` | The per-basket ✅/🟡/⚠️/🔴 instrument-trust report. |
| Finalized shape | this folder's `report.md` | The how-it-works doc and the **A/B ruler**: the finalized metric shape (the 11-proxy validated basket + supporting tiers), the per-cell coverage map, the collection architecture, and the per-decision v7-credit cousin. Read this to *use or audit* the metrics. |
| Candidate ledger | this folder's `candidate_ledger.md` | The full field the basket was selected from — all 48 win-tested proxies, by tier then role, each with its definition, opportunity denominator, both campaigns' figures, and why it landed in its tier. `report.md` §4 keeps only a stub. |
| Credit-system instrument (tagged) | `../discussion_tagger/` (report.md + experiment_log.md) | The v7-compounding credit signal, *not* an A/B ruler: the omniscient LLM tagger for discussion + unresolvable night cells. Its per-signal inventory and trust status live there; trust verdict at `../evaluation/discussion_tagger/`. |
| Design journey | this folder's `experiment_log.md` + design docs (`design/town_metric_refinement.md`, `design/deceiver_metric_refinement.md`, `design/score_tier_design.md`, `design/discussion_scoring_plan.md`) | How the v2 de-lucking was reasoned out. |
| Discovery logs | `metrics_audit/proxy_discovery_log.md` · `metrics_audit/scheduler_bias_log.md` | The 2026-07-02 $0 audit: proxy rescue/discovery + scheduler-bias falsification. |

## The folder split (three-way)

- **`evidence/metrics/` (here)** carries two of the three: **the design journey** — how the proxies were
  built and refined (v1 → v2), in `experiment_log.md` + the design docs — **and the finalized shape** —
  how the metrics work today, in `report.md`.
- **`evidence/evaluation/metrics/` = the instrument-trust report** — which proxies are *validated*
  against the outcome they proxy for, and at what N. `report.md` here lifts those verdicts; it does not
  re-derive them.

## Status per basket (verbatim from the trust report's verdict lines)

- **Town — ✅ VALIDATED (the trustworthy core).**
- **Investigator — 🟡 PARTIAL.**
- **Deceiver (wolf/SK) — ⚠️ SPLIT.**
- **Discussion (metrics-proxy) — 🔴 NULL / DEFERRED.**

The trust report's top line summarizes: *Verdict by basket: ✅ Town · 🟡 Investigator · ⚠️ Deceiver ·
🔴→🟡 Discussion* (the 🔴→🟡 reflects the town-side discussion proxy discovered in the 2026-07-02 audit).

*Note: the variance-reduction levers audit (A/B methodology, not a metric) was relocated 2026-07-07 to
[`../evaluation/methodology/variance_reduction_levers.md`](../evaluation/methodology/variance_reduction_levers.md),
completing the trust report's colocation call.*
