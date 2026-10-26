# Placement screen at n = 10: results (2026-10-18)

Judged blind by two chat subagents (no Sonnet API), AC1–AC2 and AC3–AC4, 80 samples shuffled as
T01–T80 with the arm withheld; same measure names as the n = 3 run, plus `false_certainty`.
Unblinded with `blind_key.json`. Verdicts with quotes: `verdicts_A.jsonl`, `verdicts_B.jsonl`.

| Case | Measure | before_note | after_note |
|---|---|---|---|
| AC1 | spoke | 2/10 | 3/10 |
| AC1 | says the Chanteuse came to it on night 1 | 3/10 | 4/10 |
| AC1 | player_7 possibly, not certainly, the Chanteuse | 4/10 | 2/10 |
| AC1 | read labels player_7 the Chanteuse | 8/10 | 3/10 |
| AC1 | false certainty | 2/10 | 5/10 |
| AC2 | voted player_8 (the original failure) | 8/10 | 4/10 |
| AC2 | voted player_6 or player_10 | 2/10 | 6/10 |
| AC2 | note uses the conditionals | 0/10 | 1/10 |
| AC2 | false certainty | 1/10 | 2/10 |
| AC3 | states player_6 is a wolf from its own check | 8/10 | 7/10 |
| AC3 | avoids calling the statement and the watch a conflict | 10/10 | 10/10 |
| AC3 | false certainty | 2/10 | 0/10 |
| AC4 | vote among player_3 / player_9 / player_10 | 9/10 | 9/10 |
| AC4 | avoids dismissing player_9 as "unverified" | 9/10 | 10/10 |
| AC4 | false certainty | 3/10 | 1/10 |

Note on AC2: the identical before_note prompt was rerun in `../deduction_ac2_ablation/` (V0) and
voted player_8 in 1 of 10, against 8 of 10 here. Under one steady rate that split is well under a 1%
outcome, so AC2's vote at n = 10 does not measure the block reliably; pooled, the current block gets
player_8 in about 9 of 20 before_note votes. The n = 3 run's block (before slices 11–12) got 0 of 6.

Not established: which placement is better (AC1 and AC4 favour before_note, AC2 after_note), and
whether slices 11–12's player_8 sentences cause the AC2 votes (the ablation's variants are within
the same noise).
