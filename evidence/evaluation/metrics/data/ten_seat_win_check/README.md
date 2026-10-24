# Ten-seat win check (2026-10-24)

Which play-quality scores go with their side winning on the ten-seat game. Each game's metrics were
recomputed from its record with `compute_game_metrics`, then each score was correlated with its side's
win three ways: over all games, within batch (each batch's mean taken out of both score and win), and
over the memory-off games alone. No model call. Interpretation: [`../../report.md`](../../report.md)
§4 and [`../../experiment_log.md`](../../experiment_log.md) (2026-10-24 entry).

    poetry run python -m evaluation.experiments.ten_seat_win_check \
        --out evidence/evaluation/metrics/data/ten_seat_win_check/summary.json

Run on the working tree at `74dc0bd0` (runner uncommitted at the time). `summary.json` holds every
figure, with each score's 95% range over all games.

## The games

78 ten-seat games whose every night carries its full record (games from 2026-10-11 on). The 41
phase-3 games of 2026-10-09 and 10 record each night's choices but not their outcome, so the ten-seat
scores cannot be rebuilt for them and they are left out.

| Batch | Games | Model | Memory | Winners |
|---|---|---|---|---|
| ten_seat_pilot | 4 | gemini-3.5-flash-lite | off | town 3, necromancer 1 |
| v8_smoke | 1 | gemini-3.5-flash-lite | off | town 1 |
| v8_seeding (`v8_seed_a`–`d`) | 12 | gemini-3.5-flash-lite | off | town 6, wolves 4, serial killer 1, necromancer 1 |
| v8_demo | 20 | claude-haiku-5-5 | on | town 8, wolves 7, necromancer 3, serial killer 2 |
| v8_gate_haiku | 4 | claude-haiku-5-5 | on | town 2, wolves 1, serial killer 1 |
| v8_luna_memory | 3 | gpt-6-luna | on | town 2, wolves 1 |
| cache_ab_2026_10_13 | 2 | gpt-6-luna | on | town 1, wolves 1 |
| evil_cover_games | 12 | claude-haiku-5-5 | off | town 9, wolves 3 |
| persona_voice_games | 16 | claude-haiku-5-5 | off | town 11, necromancer 3, serial killer 2 |
| silence_calibration | 4 | claude-haiku-5-5 | off | town 3, serial killer 1 |
| **All** | **78** | | **49 off** | **town 46, wolves 17, lone killer 15** |

"June" below is the direction the nine-seat check registered for the score; "new" marks a score new
to the ten-seat game. Cells are the correlation with the side's win (p).

## Results

| Score | Side | June | Games (side wins) | All games | Within batch | Memory off (games) |
|---|---|---|---|---|---|---|
| `correct_elimination_rate` | town | + | 78 (46) | +0.49 (p<0.001) | +0.55 (p<0.001) | +0.48 (p<0.001) (49) |
| `town_mislynch_rate` | town | - | 78 (46) | -0.45 (p<0.001) | -0.49 (p<0.001) | -0.48 (p<0.001) (49) |
| `mislynches` | town | - | 78 (46) | -0.38 (p<0.001) | -0.43 (p<0.001) | -0.41 (p=0.003) (49) |
| `town_vote_accuracy` | town | + | 78 (46) | +0.37 (p<0.001) | +0.42 (p<0.001) | +0.24 (p=0.095) (49) |
| `wolf_elimination_rate` | town | + | 78 (46) | +0.17 (p=0.145) | +0.25 (p=0.031) | +0.12 (p=0.415) (49) |
| `lone_killer_lynched` | town | + | 78 (46) | +0.38 (p<0.001) | +0.40 (p<0.001) | +0.43 (p=0.002) (49) |
| `power_roles_killed_by_evil` | town | - | 78 (46) | -0.55 (p<0.001) | -0.55 (p<0.001) | -0.43 (p=0.002) (49) |
| `town_accusation_precision` | town | + | 73 (44) | +0.29 (p=0.012) | +0.26 (p=0.025) | +0.13 (p=0.384) (46) |
| `healer_town_save_rate` | town | + | 75 (44) | -0.03 (p=0.786) | -0.07 (p=0.574) | -0.12 (p=0.434) (47) |
| `healer_save_rate` | town | + | 75 (44) | -0.05 (p=0.640) | -0.09 (p=0.463) | -0.10 (p=0.505) (47) |
| `healer_friendly_fire_save_rate` | town | - | 75 (44) | -0.20 (p=0.090) | -0.15 (p=0.214) | — (47) |
| `investigator_find_to_lynch_rate` | town | + | 20 (11) | +0.29 (p=0.220) | +0.27 (p=0.318) | +0.26 (p=0.537) (8) |
| `investigator_wolves_found` | town | + | 78 (46) | -0.02 (p=0.853) | +0.10 (p=0.396) | -0.01 (p=0.967) (49) |
| `investigator_find_next_round_convergence` | town | + | 0 (0) | — | — | — (0) |
| `vigilante_correct_shot_rate` | town | + | 19 (12) | +0.29 (p=0.234) | +0.25 (p=0.315) | +0.34 (p=0.238) (14) |
| `vigilante_evil_shots` | town | + | 78 (46) | +0.14 (p=0.207) | +0.13 (p=0.261) | +0.10 (p=0.481) (49) |
| `vigilante_friendly_fire_shots` | town | - | 78 (46) | -0.10 (p=0.364) | -0.15 (p=0.192) | -0.19 (p=0.203) (49) |
| `sentinel_watches_naming_evil` | town | new | 78 (46) | +0.12 (p=0.297) | +0.13 (p=0.249) | +0.19 (p=0.188) (49) |
| `trailseer_follows_naming_evil` | town | new | 78 (46) | +0.03 (p=0.808) | +0.04 (p=0.756) | +0.03 (p=0.864) (49) |
| `sigilist_hits` | town | new | 78 (46) | +0.20 (p=0.086) | +0.18 (p=0.111) | +0.12 (p=0.401) (49) |
| `wolf_unconditioned_blending_rate` | wolves | + | 70 (17) | +0.29 (p=0.016) | +0.36 (p=0.002) | +0.22 (p=0.159) (41) |
| `wolf_blending_rate` | wolves | + | 0 (0) | — | — | — (0) |
| `wolf_power_kill_rate` | wolves | + | 78 (17) | +0.17 (p=0.145) | +0.24 (p=0.037) | +0.04 (p=0.782) (49) |
| `chanteuse_blocks_real` | wolves | new | 78 (17) | +0.31 (p=0.006) | +0.28 (p=0.014) | +0.45 (p=0.001) (49) |
| `chanteuse_blocks_critical` | wolves | new | 78 (17) | +0.10 (p=0.366) | +0.03 (p=0.807) | +0.18 (p=0.215) (49) |
| `chanteuse_blocks_wasted` | wolves | new | 78 (17) | +0.03 (p=0.818) | +0.06 (p=0.594) | -0.08 (p=0.572) (49) |
| `illusionist_conceals` | wolves | new | 78 (17) | +0.10 (p=0.361) | +0.15 (p=0.192) | +0.04 (p=0.805) (49) |
| `illusionist_conceals_hid_record` | wolves | new | 78 (17) | -0.11 (p=0.316) | +0.01 (p=0.923) | -0.09 (p=0.558) (49) |
| `sk_kill_rate` | lone_killer | + | 45 (7) | +0.25 (p=0.097) | +0.25 (p=0.100) | +0.17 (p=0.384) (29) |
| `sk_power_roles_killed` | lone_killer | + | 45 (7) | +0.48 (p<0.001) | +0.58 (p<0.001) | +0.47 (p=0.011) (29) |
| `sk_unconditioned_blending_rate` | lone_killer | + | 29 (7) | -0.04 (p=0.823) | -0.10 (p=0.604) | -0.26 (p=0.340) (16) |
