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

## A third arm: gemini-3.5-flash as summariser (2026-10-10)

The same ten cases, five samples each, on the fixed code with `GOOGLE_GENAI_MODEL=gemini-3.5-flash`
(`generations_fixed_flash_summariser.jsonl`): no bad summary and no bad ledger entry in 30 positive
samples, no true claim lost from the ledger in 20 controls (one control summary left a claim out; the
ledger still had it from the speaker's field). Against flash-lite on the fixes (2 bad summaries, 0 bad
ledger entries, 1 control lost), the stronger summariser also stops writing the self-targeted actions
the ledger otherwise has to drop. About four summary calls a game, so the estimated extra cost is $0.06
to $0.12 a game.

## Claim retention: denials and rebuttals (2026-10-10)

After review, the summariser was given a way to keep a denial ("I didn't visit anyone last night", "I
held my fire", "I kept my second watch"): a claimed night action `no_action`, with the player named if
the denial names one, under a role claim of `none` when no role is claimed; and an instruction to keep
every rebuttal of an accusation. The ledger shows a denial as the claimant's word ("Night 2: says they
did not act"), and a later action claimed for the same night keeps the denial as history. Six denial
cases were added (every spoken denial found in batches 2 to 4 and the flash games had been dropped:
c03 days 4 and 5, c04 day 3, e03 day 2, f02 day 5, f06 day 3), and all sixteen cases were replayed on
three arms: the committed code (a worktree at fb193104), the fix on flash-lite, and the fix with
gemini-3.5-flash as summariser. Ledger built with the current code:

| Arm | Bad positives | True claims lost (controls) | Denials lost |
|---|---|---|---|
| committed, flash-lite | 0/30 | 1/20 | 30/30 (the schema could not hold one) |
| fixed, flash-lite | 0/30 | 2/20 | 7/30 |
| fixed, gemini-3.5-flash | 0/30 | 2/20 | 0/30 |

Flash-lite misses the denial when it sits beside other claimed actions (f02 day 5: the sigils of nights 1
and 4 kept, "I didn't visit on Night 3" dropped, 5 of 5); the stronger summariser keeps all of them. The
controls lost are the summariser leaving a true claim out entirely (e05 day 2, 2 of 5 on both fixed arms,
0 of 5 before): possibly a cost of the longer instructions, not established at five samples. The first
scoring flagged three flash-lite samples on e06 day 2 as invented claims; they were empty no-role
entries ("claimed no role" with nothing in it), which the ledger now leaves out.

## Roleblocks and empty results (2026-10-10, from the Luna games)

The Luna audit found the summariser filing "I was roleblocked" as a denial ("says they did not act"), a
regression of the claim retention above, and results the claim record could not hold (a watch that saw no
one, a follow that went nowhere, a sigil with no effect). The fix: result words no_visitors, no_effect and
roleblocked, and an instruction that a roleblock is the attempt, never a denial; the ledger shows "says they
tried to follow and were roleblocked", "followed p7; says they visited no one", "says it had no effect".
Five cases were added (three roleblocks: l03 day 2, l04 day 3, l01 day 3; an empty follow, l01 day 2; a sigil
with no effect, l01 day 4) and run with the denial and control cases, before and after, with Luna and
flash-lite as summariser (`--kinds roleblock result_word denial control`). Bad samples through the current
ledger:

| Summariser | Roleblock filed as a denial | Empty result dropped | Denial lost | True claim lost (controls) |
|---|---|---|---|---|
| Luna, before → after | 15/15 → 0/15 | 10/10 → 0/10 | 0/30 → 0/30 | 8/20 → 6/20 |
| flash-lite, before → after | 6/15 → 0/15 | 10/10 → 0/10 | 5/30 → 7/30 | 2/20 → 0/20 |

Luna's lost controls are a transcription habit, not the change: it does not credit a role nobody named (e05
day 2, a sighting reported without "I followed": 5 of 5) and records "held my fire" as a denial without
inferring the vigilante (e02 day 3); flash-lite infers both.
