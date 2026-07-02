"""Re-runnable $0 deterministic audit surface — regression checks over game-run records.

Every module here is recompute-only (ZERO LLM, no network): given a new ``batch_results/`` batch it
re-derives the same structural / behavioral facts, so an audit that passed on the frozen epoch can be
re-run as a regression check on any later run. Distinct from ``experiments/studies/`` (concluded
one-shot design screens) — these are meant to be re-run.

- ``dimension_audit``          — $0 audit of the v6 situation-dimension fields (schema/fill sanity).
- ``scheduler_access_audit``   — does the role-blind scheduler starve specific roles' floor access?
- ``whiff_conversion_audit``   — does an attacker convert a silent SK night-immune whiff into action?
- ``proxy_rescue``             — power-role de-luck proxy rescue/discovery over the v6ab set.
- ``accusation_metrics``       — town accusation precision + convergence proxies.
- ``claim_conversion``         — investigator find → next-round conversion proxy.
- ``recall_flags``             — deterministic pivotal-turn flagger (recall attention anchor).
- ``dedup_score``              — golden-label scorer for the dedup classifier (console ``eval-dedup-score``).
- ``metrics_common``           — shared v6ab loader + pre-registered 50/50 split for the metrics runners.
"""
