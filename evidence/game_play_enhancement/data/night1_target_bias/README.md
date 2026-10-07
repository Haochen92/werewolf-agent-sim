# Night 1 target choice (2026-10-07)

Runner: `evaluation/experiments/night1_target_bias_check.py` (design record: `discussion_evidence.md`
§7.5). Night 1 of the investigator, the healer and the serial killer replayed on 32 recorded boards
(the roles of the 28 June games and the four step 8 games) through the real prompts and
`run_agent`, on the game model (`gemini-3.5-flash-lite`), one call per board per role per arm. In
every run the templates carry the example read with no seat in it (`"player": "<exact player_id>"`).

Two runs, in order:

## Run 1: seat order against a seeded shuffle (`results_order_check.jsonl`, `summary_order_check.md`)

The first fix tried: each agent reads the player lists in its own seeded order. Arms `ordered`
(seat order) and `shuffled`.

| arm | target = lowest-numbered other seat | target = first name shown |
|---|---|---|
| ordered | 94 / 96 | 94 / 96 |
| shuffled | 95 / 96 | 15 / 96 |

**The model follows the number, not the order.** With the list shuffled, seat 1 was shown first in
1 to 9 of 32 calls per role and the target was still the lowest-numbered other seat in 95 of 96;
every actor in seat 1 took seat 2. The shuffle was taken out (that run's code is in git history
before the lot commit). The placeholder was never copied into a read (0 of 192).

## Run 2: without and with the drawn default (`results.jsonl`, `summary.md`)

As built: on night 1 the engine draws a default by lot per game, night and player (the pack as
one) and the prompt offers it. Arms `plain` (the lot line empty) and `lot`.

| arm | target = seat 1 | target = the lot | distinct targets, all roles | boards where all three roles hit one seat |
|---|---|---|---|---|
| plain | 78 / 96 | – | 3 (seat 1: 78, seat 2: 16, seat 3: 2) | 16 / 32 |
| lot | 14 / 96 | 95 / 96 | 9 (from 6 to 16 each) | 0 / 32 |

The agents take the lot in 95 of 96 calls; the one that did not (a serial killer, board
`df131788`) took seat 1. Night 1 actions now land on every seat, and on no board do the check,
the protection and the kill all fall on the same player. Placeholder copied: 0 of 192.

Files: `results*.jsonl` one row per call (arm, board, role, actor, the lot or the first name
shown, the target, the flags, the players the reads named, whether a read copied the
placeholder); `summary*.md` the runner's tables.
