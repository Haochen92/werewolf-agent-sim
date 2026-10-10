# Phase 3: the summaries replayed (2026-10-10)

Instead of new games, the day summaries that went wrong in the Phase 3 games were replayed: each
case is one day of one captured game, and the summariser is handed exactly what production handed
it (`evaluation/experiments/summary_claim_replay.py`), five samples per case. Two arms, one checkout
each: **committed** (56b21471, before the fixes, run from a worktree) and **fixed** (the working
tree with the summariser's two instruction changes). Every sample's structured output is scored
twice, by the summary's own fields and by the claim ledger built from it with the current ledger
code (`ledger_bad_current_code`), so the ledger fix is measured on both arms' summaries.

The cases came from reading five games by hand (`../phase3_reads/`) and scanning all 31 games for
the two error signatures: a claimed action on oneself that can only have been done to the speaker
(3 summaries), and the copied record check "no attack on X was ever announced" against a record
showing an attack on X (3 summaries). Controls are true claims a speaker made by describing its
action without setting its claim field; the summary and the ledger must keep them.

| Case | Player | Kind | Committed: summary / ledger bad | Fixed: summary / ledger bad |
|---|---|---|---|---|
| e06 day 2 | player_2 | invented_claim | 0 / 0 of 5 | 0 / 0 of 5 |
| d06 day 3 | player_3 | self_action | 3 / 0 of 5 | 1 / 0 of 5 |
| e01 day 3 | player_2 | self_action | 1 / 0 of 5 | 1 / 0 of 5 |
| b02 day 2 | player_6 | record_check | 1 / 1 of 5 | 0 / 0 of 5 |
| b09 day 2 | player_1 | record_check | 1 / 1 of 5 | 0 / 0 of 5 |
| c03 day 2 | player_6 | record_check | 0 / 0 of 5 | 0 / 0 of 5 |
| e02 day 3 | player_9 | control | 0 / 0 of 5 | 1 / 1 of 5 |
| e03 day 2 | player_4 | control | 0 / 0 of 5 | 0 / 0 of 5 |
| e05 day 2 | player_2 | control | 0 / 0 of 5 | 0 / 0 of 5 |
| e06 day 3 | player_5 | control | 2 / 0 of 5 | 2 / 0 of 5 |

## Reading

- **The ledger fix does its job on either summariser.** The self-targeted actions the summariser
  still writes (committed 4 of 10 samples, fixed 2 of 10) never reach the ledger.
- **The record-check wording fix does its job.** The copied line came back in 2 of 15 committed
  samples and 0 of 15 fixed ones.
- **The invented chanteuse claim (e06 day 2) did not recur** in 10 samples on either arm: it is a
  rare error, so the replay cannot show the instruction change preventing it; the ledger rule is
  what guards against it, and an offline test pins it.
- **One regression found and fixed before this table.** The first ledger rule also dropped the
  role when every claimed action was self-targeted, and so lost a true vigilante whose "held my
  fire" the summariser had written as shooting itself (e02 day 3). The role now goes only when it
  is the chanteuse resting on a self-block, the one action a player is told was done to them.
- **One control sample lost by the summariser itself** (e02 day 3, fixed arm, 1 of 5): the summary
  left the vigilante's claim out entirely. Possibly the new "something done to a player is not a
  claim" instruction applied to "I was roleblocked" in the same sentence; one sample cannot say.
  Committed lost 0 of 5 on that case.

Ten cases, five samples: a regression check on known failures, not a rate.
