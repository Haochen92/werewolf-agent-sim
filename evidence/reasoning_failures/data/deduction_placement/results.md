# Placement screen: results (2026-10-17)

Judged blind by a chat subagent (no Sonnet API): 24 samples shuffled as S01–S24, the arm withheld,
scored on the measures fixed in README.md before the run. Unblinded with `blind_key.json`.
Verdicts with the deciding quotes: `verdicts.jsonl`; the packet the judge read: `judging_packet.md`.
n = 3 per case per arm, so a difference of one or two samples is noise.

| Case | Measure | before_note | after_note |
|---|---|---|---|
| AC1 | spoke | 1/3 | 2/3 |
| AC1 | says the Chanteuse came to it on night 1 (message or note) | 1/3 | 1/3 |
| AC1 | player_7 possibly, not certainly, the Chanteuse | 2/3 | 2/3 |
| AC1 | read labels player_7 the Chanteuse | 1/3 | 3/3 |
| AC2 | voted player_8 (the original failure) | 0/3 | 0/3 |
| AC2 | voted player_6 or player_10 | 3/3 | 3/3 |
| AC2 | note uses the conditionals | 2/3 | 2/3 |
| AC3 | states player_6 is a wolf from its own check | 1/3 | 3/3 |
| AC3 | avoids calling the statement and the watch a conflict | 3/3 | 3/3 |
| AC4 | vote among player_3 / player_9 / player_10 (abstain = no) | 2/3 | 2/3 |
| AC4 | avoids dismissing player_9 as "unverified" | 3/3 | 2/3 |
| all | samples flagged for a false certainty or an overreach | 1 (S12) | 4 (S01, S06, S20, S21) |

Reading: with the block in place, both arms fix the original failures where the block carries the
line (AC2: no vote for player_8 in 6 of 6; AC3: no "conflict" in 6 of 6; AC4: 5 of 6 keep player_9's
partly confirmed report). After the note, the block's conclusions were taken up more (AC1 read,
AC3 "player_6 is a wolf") but stated more strongly too (4 of the 5 overreaches, including AC4's
original "unverified" vote and AC1's must-not-say). Neither difference is large enough at n = 3 to
rule on. Recommendation (adopted by the owner 2026-10-18): keep `before_note` (the default; it also caches better), and revisit with a
larger n only if live games show the block being ignored.
