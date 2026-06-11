# v5 Baseline + Memory-On Proxy Signal (interim, 2026-06-11)

Aggregation of the per-game de-lucked proxies (`computed_metrics`) across the v5 seeding run.
**Directional / hypothesis-generating only** — the memory-ON arm is the v5_1 *build* games
(`all_enabled`, unpaired, growing store), NOT the clean paired A/B. Treat as a pilot for Phase C
sizing + demonstrator-role selection, not as the effect itself.

## Arms
- **memory-OFF (N=30):** v5_0 seeding (20 `all_disabled` extraction-on) + 10 extraction-off baseline pad.
- **memory-ON (N=14):** v5_1 build games (`all_enabled`), batches b1+b2+b3(partial). (b4 → 20 running.)
- Classified per-record by `memory_config` (not filename).

## Faction win-rate
| faction | OFF (N=30) | ON (N=14) | Δ |
|---|---|---|---|
| villagers | 67% | 50% | −17pp |
| serial_killer | 27% | ~21% | ~−6pp |
| wolves | 7% | ~30% | **+23pp** |

## Proxy movers (memory-ON − memory-OFF), biggest first
| proxy | OFF mean(sd,n) | ON mean(sd,n) | Δ |
|---|---|---|---|
| investigator_threat_find_lift | 1.54 (0.96,27) | **2.21 (0.61,11)** | **+0.66** |
| investigator_found_wolf_day | 1.63 (0.74,19) | 1.25 (0.66,8) | −0.38 |
| vigilante_correct_shot_rate | 0.62 (0.46,21) | 0.35 (0.45,10) | −0.27 |
| wolf_steering_rate | 0.75 (0.43,12) | 0.50 (0.43,8) | −0.25 |
| mislynches | 0.90 (0.91,30) | 1.14 (0.99,14) | +0.24 |
| investigator_threat_find_rate | 0.54 (0.36,27) | **0.78 (0.28,11)** | **+0.24** |
| wolf_blending_rate | 0.50 (0.50,14) | 0.33 (0.47,6) | −0.17 |
| wolf_dissent_rate | 0.50 (0.50,14) | 0.67 (0.47,6) | +0.17 |
| town_vote_accuracy | 0.71 (0.28,30) | 0.62 (0.22,14) | −0.09 |
| correct_elimination_rate | 0.69 (0.32,30) | 0.60 (0.32,14) | −0.09 |
| town_mislynch_rate | 0.31 (0.32,30) | 0.40 (0.32,14) | +0.09 |

(Full table: `scripts`-free, regenerate from `computed_metrics` in `batch_results/v5_*.jsonl`.)

## Reads (tentative)
1. **Investigator is the clearest memory beneficiary.** `threat_find_lift` +0.66 with variance
   *shrinking* (0.96→0.61), `threat_find_rate` +0.24 (bounded [0,1], low ON-variance 0.28),
   `wolf_find_rate` +0.11 — a coherent cluster. **This revises the prior wolf-blending demonstrator
   hypothesis** (imported from the old system): on v5, the investigator, not the wolf, shows the
   cleanest dense-proxy lift. A strong Phase C demonstrator candidate (large effect + low variance →
   fewer games for power).
2. **Town voting may degrade under memory** — accuracy −0.09, mislynches +0.24, mislynch_rate +0.09,
   matching the town win-rate drop. Candidate evidence for a retrieval **distraction/overload** effect
   (better investigator info not converting to better votes). Worth an A/B arm: memory-on raw
   (top_k=3) vs memory-on reranked/filtered.
3. **Wolf story is incoherent at this N** — win-rate +23pp but `blending` −0.17 and `steering` −0.25
   *fell*. The old +36pp wolf-blending mechanism is NOT reproduced; the wolf wins may be SK-driven
   board states or noise. Do not assume wolf-memory is the demonstrator without the paired A/B.

## Caveats (do not over-read)
- Confounded (unpaired build games, growing store), unequal/small N (30 vs 14), population sd shown.
- Several proxies have small sub-N (computed only when the role/condition occurs: wolf_blending 14/6,
  wolf_steering 12/8, vigilante_correct_shot 21/10).
- Next: the **paired** A/B (same `game_id`, memory diff) sized off these variances; per-proxy effect
  size + proper power, McNemar on win-rate. See `report.md` statistical design + [[project-metrics]].
