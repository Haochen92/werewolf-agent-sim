# Paired memory A/B — FULL report

Same-epoch baseline: 30 games. * = Wilcoxon p<0.05 (uncorrected; Bonferroni over the ≤3 pre-registered primaries = 0.017).

## RAW arms (rerank off) — off vs on
### raw wolf_only (faction=wolves), N=30
- win: off 33%[17%,53%] -> on 30%[15%,49%] (Δ-3%, McNemar p=1.000)
  - town_vote_accuracy (+): 0.560 -> 0.627 (Δ+0.067, p=0.290)
  - town_mislynch_rate (-): 0.530 -> 0.406 (Δ-0.124, p=0.042) *
  - mislynches (-): 1.400 -> 1.033 (Δ-0.367, p=0.048) *
  - correct_elimination_rate (+): 0.470 -> 0.594 (Δ+0.124, p=0.058)
  - serial_killer_lynched (+): 0.600 -> 0.733 (Δ+0.133, p=0.285)
  - sk_nights_survived (+): 3.400 -> 3.433 (Δ+0.033, p=0.982)
  - healer_town_save_rate (+): 0.370 -> 0.479 (Δ+0.109, p=0.195)
  - vigilante_friendly_fire_shots (-): 0.333 -> 0.400 (Δ+0.067, p=0.646)

### raw serial_killer_only (faction=serial_killer), N=30
- win: off 40%[23%,59%] -> on 20%[8%,39%] (Δ-20%, McNemar p=0.146)
  - town_vote_accuracy (+): 0.560 -> 0.643 (Δ+0.083, p=0.243)
  - town_mislynch_rate (-): 0.530 -> 0.343 (Δ-0.187, p=0.029) *
  - mislynches (-): 1.400 -> 1.067 (Δ-0.333, p=0.189)
  - correct_elimination_rate (+): 0.470 -> 0.657 (Δ+0.187, p=0.031) *
  - serial_killer_lynched (+): 0.600 -> 0.800 (Δ+0.200, p=0.083)
  - sk_nights_survived (+): 3.400 -> 3.433 (Δ+0.033, p=0.957)
  - healer_town_save_rate (+): 0.370 -> 0.510 (Δ+0.140, p=0.167)
  - vigilante_friendly_fire_shots (-): 0.333 -> 0.467 (Δ+0.133, p=0.400)

### raw town_only (faction=villagers), N=30
- win: off 27%[12%,46%] -> on 43%[25%,63%] (Δ+17%, McNemar p=0.267)
  - town_vote_accuracy (+): 0.560 -> 0.710 (Δ+0.149, p=0.053)
  - town_mislynch_rate (-): 0.530 -> 0.362 (Δ-0.168, p=0.036) *
  - mislynches (-): 1.400 -> 1.033 (Δ-0.367, p=0.128)
  - correct_elimination_rate (+): 0.470 -> 0.638 (Δ+0.168, p=0.028) *
  - serial_killer_lynched (+): 0.600 -> 0.767 (Δ+0.167, p=0.197)
  - sk_nights_survived (+): 3.400 -> 3.033 (Δ-0.367, p=0.288)
  - healer_town_save_rate (+): 0.370 -> 0.598 (Δ+0.228, p=0.005) *
  - vigilante_friendly_fire_shots (-): 0.333 -> 0.267 (Δ-0.067, p=0.644)

## RERANKED arms (observations reranking) — off vs on
### rerank wolf_only (faction=wolves), N=30
- win: off 33%[17%,53%] -> on 20%[8%,39%] (Δ-13%, McNemar p=0.344)
  - town_vote_accuracy (+): 0.560 -> 0.587 (Δ+0.026, p=0.689)
  - town_mislynch_rate (-): 0.530 -> 0.437 (Δ-0.093, p=0.347)
  - mislynches (-): 1.400 -> 1.100 (Δ-0.300, p=0.186)
  - correct_elimination_rate (+): 0.470 -> 0.563 (Δ+0.093, p=0.360)
  - serial_killer_lynched (+): 0.600 -> 0.567 (Δ-0.033, p=0.763)
  - sk_nights_survived (+): 3.400 -> 3.467 (Δ+0.067, p=0.699)
  - healer_town_save_rate (+): 0.370 -> 0.469 (Δ+0.099, p=0.329)
  - vigilante_friendly_fire_shots (-): 0.333 -> 0.367 (Δ+0.033, p=0.817)

### rerank serial_killer_only (faction=serial_killer), N=30
- win: off 40%[23%,59%] -> on 23%[10%,42%] (Δ-17%, McNemar p=0.267)
  - town_vote_accuracy (+): 0.560 -> 0.704 (Δ+0.143, p=0.040) *
  - town_mislynch_rate (-): 0.530 -> 0.352 (Δ-0.178, p=0.046) *
  - mislynches (-): 1.400 -> 1.033 (Δ-0.367, p=0.221)
  - correct_elimination_rate (+): 0.470 -> 0.648 (Δ+0.178, p=0.041) *
  - serial_killer_lynched (+): 0.600 -> 0.767 (Δ+0.167, p=0.166)
  - sk_nights_survived (+): 3.400 -> 3.200 (Δ-0.200, p=0.451)
  - healer_town_save_rate (+): 0.370 -> 0.453 (Δ+0.083, p=0.252)
  - vigilante_friendly_fire_shots (-): 0.333 -> 0.333 (Δ+0.000, p=1.000)

### rerank town_only (faction=villagers), N=30
- win: off 27%[12%,46%] -> on 60%[41%,77%] (Δ+33%, McNemar p=0.013)
  - town_vote_accuracy (+): 0.560 -> 0.686 (Δ+0.126, p=0.053)
  - town_mislynch_rate (-): 0.530 -> 0.369 (Δ-0.161, p=0.077)
  - mislynches (-): 1.400 -> 0.900 (Δ-0.500, p=0.015) *
  - correct_elimination_rate (+): 0.470 -> 0.631 (Δ+0.161, p=0.067)
  - serial_killer_lynched (+): 0.600 -> 0.767 (Δ+0.167, p=0.132)
  - sk_nights_survived (+): 3.400 -> 3.300 (Δ-0.100, p=0.642)
  - healer_town_save_rate (+): 0.370 -> 0.361 (Δ-0.009, p=0.951)
  - vigilante_friendly_fire_shots (-): 0.333 -> 0.300 (Δ-0.033, p=0.819)

## ALL-ON arm (all roles, raw) — off vs on
### all_enabled (faction=villagers), N=30
- win: off 27%[12%,46%] -> on 50%[31%,69%] (Δ+23%, McNemar p=0.167)
  - town_vote_accuracy (+): 0.560 -> 0.687 (Δ+0.126, p=0.058)
  - town_mislynch_rate (-): 0.530 -> 0.325 (Δ-0.205, p=0.039) *
  - mislynches (-): 1.400 -> 0.867 (Δ-0.533, p=0.050)
  - correct_elimination_rate (+): 0.470 -> 0.675 (Δ+0.205, p=0.030) *
  - serial_killer_lynched (+): 0.600 -> 0.867 (Δ+0.267, p=0.046) *
  - sk_nights_survived (+): 3.400 -> 3.100 (Δ-0.300, p=0.261)
  - healer_town_save_rate (+): 0.370 -> 0.477 (Δ+0.107, p=0.264)
  - vigilante_friendly_fire_shots (-): 0.333 -> 0.267 (Δ-0.067, p=0.593)

## PRE-REGISTERED CALLED SHOTS
### rerank-town — paired raw vs reranked, N=30 (predict: town_vote_accuracy UP vs raw)
  - town_vote_accuracy: raw 0.710 -> rerank 0.686 (Δ-0.023, Wilcoxon p=0.518)

### rerank-wolf — paired raw vs reranked, N=30 (predict: town detection DOWN vs raw)
  - town_vote_accuracy: raw 0.627 -> rerank 0.587 (Δ-0.041, Wilcoxon p=0.681)
  - mislynches: raw 1.033 -> rerank 1.100 (Δ+0.067, Wilcoxon p=0.654)

### all-on — predict NO town collapse vs baseline (contra pilot)
  (see ALL-ON arm above: villager win + town_vote_accuracy vs baseline)
