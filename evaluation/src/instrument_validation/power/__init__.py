"""Power / MDE gate for the compounding measurement plan (§0.1) — the pre-registered home.

No code yet. The plan requires an MDE table BEFORE any paid run: a $0 script that resamples existing
per-game records (v2, v6ab, run-1), injects a known true effect (0 / +0.1 / +0.15 / +0.2), runs the
planned slope analysis many times, and reports detection rate at N∈{4,5,10,20}/gen × {6,8,10} gens —
the minimal detectable slope at the affordable N. Reuse the de-luck loader
(``evaluation.src.instrument_validation.proxies.metrics_common.load_v6ab``) + ``decision_scoring``;
printed on each run (the 2026-07-05 readout is summarised in ``evidence/execution_plan/report.md`` §2;
its full table is in git history at 24dfd3a7). Until a current table exists, the compounding paid
runs stay gated (a powered live test is a costed deferral, not a coin flip).
"""
