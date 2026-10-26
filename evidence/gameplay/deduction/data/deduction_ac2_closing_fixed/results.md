# AC2 with today's closing call: results (2026-10-18)

The live default (current block, `before_note`) on the frozen AC2 vote turn, with the original game's
closing call rewritten to today's wording ("Before the vote: player_8 gets a last word.", no accuser
count; `hallucination_bench._engine_wording`). The prompt differs from `../deduction_ac2_2x2/`'s
current/before_note arm in that one line only. 25 valid samples; votes counted by code.

| Prompt | player_8 (the real Healer) | player_6 | player_10 |
|---|---|---|---|
| old call ("accused by player_2, player_5 and player_4"), 2×2 arm | 9 | 14 | 2 |
| today's call | 5 | 20 | 0 |

Reading: the vote for player_8 falls from 36% to 20% when the accuser count goes, the direction the
voters' own reasons ("accused by three players") point to; at n = 25 the difference is suggestive,
not decisive. In live games the count no longer exists, so 5 of 25 is the better estimate of the
remaining AC2 failure with the deduction block in place.
