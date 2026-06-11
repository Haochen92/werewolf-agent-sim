# Paired memory A/B — results

Same-epoch fresh baseline: 30 games (game_id-matched, full proxies).

## wolf_only (faction = wolves), N_paired = 30

- **Win rate:** off 33% [17%,53%] -> on 30% [15%,49%] (delta -3%)
- **McNemar (paired):** b(off-only)=7, c(on-only)=6, discordant=13, **p=1.000**
- **Validated proxies (paired off->on mean, Wilcoxon p):**
  - `town_vote_accuracy` (+): off 0.560 -> on 0.627 (delta +0.067, Wilcoxon p=0.290, n=30)
  - `town_mislynch_rate` (-): off 0.530 -> on 0.406 (delta -0.124, Wilcoxon p=0.042, n=30)
  - `mislynches` (-): off 1.400 -> on 1.033 (delta -0.367, Wilcoxon p=0.048, n=30)
  - `correct_elimination_rate` (+): off 0.470 -> on 0.594 (delta +0.124, Wilcoxon p=0.058, n=30)
  - `serial_killer_lynched` (+): off 0.600 -> on 0.733 (delta +0.133, Wilcoxon p=0.285, n=30)
  - `sk_nights_survived` (+): off 3.400 -> on 3.433 (delta +0.033, Wilcoxon p=0.982, n=30)
  - `healer_town_save_rate` (+): off 0.370 -> on 0.479 (delta +0.109, Wilcoxon p=0.195, n=30)
  - `vigilante_friendly_fire_shots` (-): off 0.333 -> on 0.400 (delta +0.067, Wilcoxon p=0.646, n=30)

## serial_killer_only (faction = serial_killer), N_paired = 30

- **Win rate:** off 40% [23%,59%] -> on 20% [8%,39%] (delta -20%)
- **McNemar (paired):** b(off-only)=9, c(on-only)=3, discordant=12, **p=0.146**
- **Validated proxies (paired off->on mean, Wilcoxon p):**
  - `town_vote_accuracy` (+): off 0.560 -> on 0.643 (delta +0.083, Wilcoxon p=0.243, n=30)
  - `town_mislynch_rate` (-): off 0.530 -> on 0.343 (delta -0.187, Wilcoxon p=0.029, n=30)
  - `mislynches` (-): off 1.400 -> on 1.067 (delta -0.333, Wilcoxon p=0.189, n=30)
  - `correct_elimination_rate` (+): off 0.470 -> on 0.657 (delta +0.187, Wilcoxon p=0.031, n=30)
  - `serial_killer_lynched` (+): off 0.600 -> on 0.800 (delta +0.200, Wilcoxon p=0.083, n=30)
  - `sk_nights_survived` (+): off 3.400 -> on 3.433 (delta +0.033, Wilcoxon p=0.957, n=30)
  - `healer_town_save_rate` (+): off 0.370 -> on 0.510 (delta +0.140, Wilcoxon p=0.167, n=30)
  - `vigilante_friendly_fire_shots` (-): off 0.333 -> on 0.467 (delta +0.133, Wilcoxon p=0.400, n=30)

## town_only (faction = villagers), N_paired = 30

- **Win rate:** off 27% [12%,46%] -> on 43% [25%,63%] (delta +17%)
- **McNemar (paired):** b(off-only)=4, c(on-only)=9, discordant=13, **p=0.267**
- **Validated proxies (paired off->on mean, Wilcoxon p):**
  - `town_vote_accuracy` (+): off 0.560 -> on 0.710 (delta +0.149, Wilcoxon p=0.053, n=30)
  - `town_mislynch_rate` (-): off 0.530 -> on 0.362 (delta -0.168, Wilcoxon p=0.036, n=30)
  - `mislynches` (-): off 1.400 -> on 1.033 (delta -0.367, Wilcoxon p=0.128, n=30)
  - `correct_elimination_rate` (+): off 0.470 -> on 0.638 (delta +0.168, Wilcoxon p=0.028, n=30)
  - `serial_killer_lynched` (+): off 0.600 -> on 0.767 (delta +0.167, Wilcoxon p=0.197, n=30)
  - `sk_nights_survived` (+): off 3.400 -> on 3.033 (delta -0.367, Wilcoxon p=0.288, n=30)
  - `healer_town_save_rate` (+): off 0.370 -> on 0.598 (delta +0.228, Wilcoxon p=0.005, n=30)
  - `vigilante_friendly_fire_shots` (-): off 0.333 -> on 0.267 (delta -0.067, Wilcoxon p=0.644, n=30)
