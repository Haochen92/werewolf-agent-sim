# Proxy-vs-Win Monotonicity Check (2026-06-11)

The validation step the v2 metrics design required but deferred ("correlate each proxy with its
faction's win across games; drop proxies that don't move with winning"). Run on the **existing**
v5 games — 30 memory-off + 20 memory-on (arm definitions:
`evidence/memory_system/effectiveness/v5_baseline_proxy_analysis.md`) — zero new games.

Method: point-biserial correlation of each `computed_metrics` proxy against its **own faction's
win**, expected sign per the design-intent table in `experiment_log.md`. Reported pooled (N=50;
more power, but the memory treatment moves both proxy and win → can inflate r) and memory-OFF-only
(N=30; treatment-free). Regenerate: `poetry run python evidence/metrics/proxy_win_monotonicity.py`
(uses `evaluation/src/core/stats.py`).

| proxy | faction | expected | pooled r (N=50) | OFF-only r (N=30) | verdict (pooled) |
|---|---|---|---|---|---|
| `correct_elimination_rate` | villagers | + | +0.65 (p=0.000, n=50) | +0.64 (p=0.000, n=30) | ok (sig.) |
| `mislynches` | villagers | - | -0.57 (p=0.000, n=50) | -0.55 (p=0.002, n=30) | ok (sig.) |
| `town_mislynch_rate` | villagers | - | -0.65 (p=0.000, n=50) | -0.64 (p=0.000, n=30) | ok (sig.) |
| `town_vote_accuracy` | villagers | + | +0.62 (p=0.000, n=50) | +0.57 (p=0.001, n=30) | ok (sig.) |
| `serial_killer_lynched` | villagers | + | +0.64 (p=0.000, n=50) | +0.85 (p=0.000, n=30) | ok (sig.) |
| `wolf_elimination_rate` | villagers | + | +0.37 (p=0.008, n=50) | +0.26 (p=0.171, n=30) | ok (sig.) |
| `power_roles_killed_by_wolves` | villagers | - | -0.34 (p=0.016, n=50) | -0.29 (p=0.119, n=30) | ok (sig.) |
| `healer_save_rate` | villagers | + | +0.10 (p=0.486, n=50) | -0.13 (p=0.483, n=30) | ok (weak) |
| `healer_town_save_rate` | villagers | + | +0.36 (p=0.010, n=50) | +0.33 (p=0.079, n=30) | ok (sig.) |
| `healer_friendly_fire_save_rate` | villagers | - | -0.31 (p=0.030, n=50) | -0.44 (p=0.014, n=30) | ok (sig.) |
| `healer_wolf_block_rate` | villagers | + | +0.28 (p=0.051, n=50) | +0.16 (p=0.395, n=30) | ok (weak) |
| `investigator_threat_find_rate` | villagers | + | -0.09 (p=0.540, n=44) | -0.03 (p=0.889, n=27) | ⚠️ WRONG SIGN |
| `investigator_threat_find_lift` | villagers | + | -0.02 (p=0.894, n=44) | +0.04 (p=0.835, n=27) | ⚠️ WRONG SIGN |
| `investigator_wolf_find_rate` | villagers | + | -0.14 (p=0.348, n=44) | -0.30 (p=0.128, n=27) | ⚠️ WRONG SIGN |
| `investigator_wolves_found` | villagers | + | +0.25 (p=0.076, n=50) | +0.13 (p=0.499, n=30) | ok (weak) |
| `investigator_found_wolf_day` | villagers | - | +0.38 (p=0.039, n=30) | +0.43 (p=0.069, n=19) | ⚠️ WRONG SIGN (sig.) |
| `vigilante_correct_shot_rate` | villagers | + | +0.30 (p=0.081, n=36) | +0.43 (p=0.050, n=21) | ok (weak) |
| `vigilante_evil_shots` | villagers | + | +0.15 (p=0.302, n=50) | +0.15 (p=0.421, n=30) | ok (weak) |
| `vigilante_friendly_fire_shots` | villagers | - | -0.29 (p=0.042, n=50) | -0.36 (p=0.049, n=30) | ok (sig.) |
| `vigilante_bullets_unused` | villagers | · | +0.16 (p=0.259, n=50) | +0.22 (p=0.244, n=30) | context |
| `vigilante_shots_taken` | villagers | · | -0.16 (p=0.259, n=50) | -0.22 (p=0.244, n=30) | context |
| `wolf_blending_rate` | wolves | + | — (n=20) | — (n=14) | degenerate |
| `wolf_dissent_rate` | wolves | - | — (n=20) | — (n=14) | degenerate |
| `wolf_steering_rate` | wolves | + | -0.06 (p=0.771, n=24) | +0.26 (p=0.418, n=12) | ⚠️ WRONG SIGN |
| `wolf_power_role_targeting_rate` | wolves | + | +0.21 (p=0.148, n=50) | +0.09 (p=0.636, n=30) | ok (weak) |
| `wolf_killed_healer_day` | wolves | - | -0.51 (p=0.041, n=16) | +0.00 (p=1.000, n=9) | ok (sig.) |
| `wolf_killed_investigator_day` | wolves | - | +0.33 (p=0.231, n=15) | +0.71 (p=0.047, n=8) | ⚠️ WRONG SIGN |
| `sk_nights_survived` | serial_killer | + | +0.31 (p=0.028, n=50) | +0.17 (p=0.374, n=30) | ok (sig.) |
| `sk_kills_landed` | serial_killer | · | +0.35 (p=0.013, n=50) | +0.37 (p=0.045, n=30) | context |
| `game_length` | villagers | · | +0.25 (p=0.082, n=50) | +0.33 (p=0.077, n=30) | context |
| `tie_count` | villagers | · | -0.00 (p=0.991, n=50) | -0.00 (p=1.000, n=30) | context |
| `no_vote_count` | villagers | · | — (n=50) | — (n=30) | context |

## Read

- **Validated (strong): the town *decision-quality* basket.** `town_vote_accuracy`,
  `correct_elimination_rate`, `mislynches`/`town_mislynch_rate`, `serial_killer_lynched` all
  correlate with villager win at |r|≈0.55–0.65, p<0.01, in BOTH pooled and OFF-only views.
  These are the right proxies to power the Phase C A/B — and they are exactly the movers behind
  the v5 pilot's "memory degrades town decision-making" read, which this strengthens.
- **Validated (moderate):** `healer_town_save_rate` / `healer_friendly_fire_save_rate` (the
  good-play/error split works; the undifferentiated `healer_save_rate` is ~zero, as the v2 design
  predicted), `vigilante_friendly_fire_shots`, `sk_nights_survived` (the SK's designed core proxy).
- **NOT validated: the investigator rate proxies.** `threat_find_rate`/`threat_find_lift`/
  `wolf_find_rate` are ~zero or wrong-sign — finding threats does not predict villager wins in
  these 50 games. `investigator_found_wolf_day` is significantly *backwards* pooled (later find ↔
  more villager wins; plausibly game-length confounded — villager wins take longer, and the
  earliness proxy isn't length-normalized). Consequence: the v5 pilot's investigator claims
  ("memory helps perception but it doesn't convert") rest on unvalidated proxies and should be
  treated as hypothesis only.
- **Underpowered, not invalidated:** the wolf social proxies. `wolf_blending_rate`/`dissent_rate`
  are degenerate here (defined in few games; wolves won only 2/30 OFF) and `wolf_steering_rate` is
  ~zero at n=24. The old-system evidence for blending (12%→48% across two batches) is unaffected,
  but v5 cannot yet confirm it; the wolf basket needs the A/B's larger paired N.
- Caveat: this validates *monotonicity on v5 data at modest N*, with proxies sharing games
  (rows are not independent tests). It ranks proxies by trustworthiness; it is not a causal claim.
