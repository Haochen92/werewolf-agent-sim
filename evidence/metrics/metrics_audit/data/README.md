# metrics_audit / data — artifact index

Recompute-only JSON outputs of the metrics-audit runners. All produced $0 / ZERO-LLM over the N=180
v6ab set. Narrative + interpretation live in the logs one level up; this is just the data plane.

## Workstream 1 — proxy rescue & discovery (`../proxy_discovery_log.md` §3)

- `proxy_rescue.json` — Idea A. Per-candidate point-biserial + partial/stratified correlations for the
  muted wolf-night proxies and the investigator find-rate cluster. Produced by
  `evaluation/src/experiments/proxy_rescue.py`.
- `accusation_metrics.json` — Idea B. Point-biserial (full + 50/50 split) for the six accusation-graph
  candidates. Produced by `evaluation/src/experiments/accusation_metrics.py`.
- `accusation_label_sample.json` — Idea B label-noise guard: 20 random (message, parsed-accusation)
  pairs for human spot-check of `addressed_targets` label quality. Same producer.
- `claim_conversion.json` — Idea C. role_claim coverage probe (0/180 → C0 blocked) + the C1
  find→next-round convergence validation. Produced by `evaluation/src/experiments/claim_conversion.py`.

## Workstream 2 — scheduler bias (`../scheduler_bias_log.md`)

- `floor_access.json`, `gate_silencing.json`, `reveal_withhold.json` — belong to the sibling scheduler
  workstream; described in `../scheduler_bias_log.md`.
- `whiff_conversion.json` — the whiff-conversion audit (`../scheduler_bias_log.md` §3 ③.E). Does an
  attacker convert a silent SK-whiff into action, and which layer fails (visibility / behavior /
  floor)? Layer-1 visibility facts (file:line) + per-set (v5, v6ab) Layer-2 conversion + Layer-3
  floor + the v6ab reasoning scan. Produced by
  `evaluation/src/experiments/whiff_conversion_audit.py`. Verdict: VISIBILITY binds → supports change E.
