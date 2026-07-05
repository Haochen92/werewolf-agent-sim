# De-lucked Proxy Metrics — system hub

**What this is.** The one-page assembly of the de-lucked proxy-metrics system, which spans ~7
locations. Read this first if you want everything needed to judge the system's reliability from a
single page.

**What the system is.** Per-role **de-lucked outcome proxies**: decision-level scores computed against
ground-truth roles, then *differenced against luck* (opportunity-conditioned rates) so a proxy ranks
skill rather than the coin-flips baked into a raw win/loss. A proxy is only trusted once it is shown to
track its own faction's win. This measurement core is what both eval tiers rest on.

## THE MAP

| Piece | Where | Role |
|---|---|---|
| Production computation | `../../Agents/compute_metrics.py` + `../../Agents/schemas/metrics.py` | Emits the ~50-field `ComputedGameMetrics` per game; carries the `VALIDATED_BASKET` / `DIAGNOSTIC` / `DO_NOT_USE` tiers. |
| Validation harness | `../../evaluation/src/instrument_validation/proxies/` | The 6 standing runners: `proxy_win_monotonicity` · `proxy_rescue` · `accusation_metrics` · `claim_conversion` · `diagnose_wolf_sk_proxies` (promoted 2026-07-04) · `leverage_anchor_separation` (promoted 2026-07-04); plus `metrics_common` (shared N=180 loader + pre-registered split). |
| Regression tests | `../../tests/test_metrics_audit_proxies.py` · `test_diagnostic_metrics.py` · `test_wolf_blending_metrics.py` | Lock the tiering + audit-graduated proxies. |
| Trust verdict | `../evaluation/metrics/report.md` | The per-basket ✅/🟡/⚠️/🔴 instrument-trust report. |
| Design journey | this folder's `experiment_log.md` + design docs (`town_metric_refinement.md`, `deceiver_metric_refinement.md`, `score_tier_design.md`, `discussion_scoring_plan.md`) | How the v2 de-lucking was reasoned out. |
| Discovery logs | `metrics_audit/proxy_discovery_log.md` · `metrics_audit/scheduler_bias_log.md` | The 2026-07-02 $0 audit: proxy rescue/discovery + scheduler-bias falsification. |

## The twin-folder split

- **`evidence/metrics/` (here) = the design journey** — how the proxies were built and refined (v1 → v2).
- **`evidence/evaluation/metrics/` = the instrument-trust report** — which proxies are *validated*
  against the outcome they proxy for, and at what N.

## Status per basket (verbatim from the trust report's verdict lines)

- **Town — ✅ VALIDATED (the trustworthy core).**
- **Investigator — 🟡 PARTIAL.**
- **Deceiver (wolf/SK) — ⚠️ SPLIT.**
- **Discussion (metrics-proxy) — 🔴 NULL / DEFERRED.**

The trust report's top line summarizes: *Verdict by basket: ✅ Town · 🟡 Investigator · ⚠️ Deceiver ·
🔴→🟡 Discussion* (the 🔴→🟡 reflects the town-side discussion proxy discovered in the 2026-07-02 audit).

*Note: `variance_reduction_levers.md` in this folder is mis-filed — it is A/B methodology, not a metric,
and is handled in the methodology report (per the trust report's colocation call).*
