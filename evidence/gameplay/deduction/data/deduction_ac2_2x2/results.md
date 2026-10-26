# AC2 2×2: results (2026-10-18)

Votes counted by code from `vote_target` (no judge), 25 valid samples per arm, all four arms shuffled
into one schedule (seed 20261018) so time and server effects fall on every arm alike.

| Arm | player_8 (the real Healer) | player_6 | player_10 | player_4 |
|---|---|---|---|---|
| current, before_note | 9 | 14 | 2 | 0 |
| current, after_note | 9 | 13 | 1 | 2 |
| trimmed (no E1 sentence, no will-visit sentence), before_note | 10 | 13 | 2 | 0 |
| trimmed, after_note | 5 | 15 | 4 | 1 |

Reading: about a third of the votes go to player_8 whatever the arm (pooled 33 of 100). The
differences (5 to 10 of 25) are within sampling noise at n = 25, so neither the placement nor the two
player_8 sentences changes the vote reliably. The n = 3 run's 0 of 6 was luck (at a one-in-three rate,
six misses in a row happen about one time in twelve), and the n = 10 swing of 8/10 against 1/10 on one
prompt was noise around the same rate. Pooled first half 14 of 50, second half 19 of 50: no drift beyond
noise.

Placement (OQ21, decided by the owner 2026-10-18): keep `before_note` as the default. AC2 shows no difference, and the n = 10
screen favoured before_note on AC1 (reads 8 vs 3 of 10, false certainties 2 vs 5) and AC4 (false
certainties 3 vs 1 the other way, within noise). The two player_8 sentences stay: they are true and do
not move the vote.

Open: why a third of the votes still go to player_8. The voters who did cited "accused by three
players" and "healer claim unverifiable" (the R2 pattern), which the block does not address.
