# Phase 3: six games on the stronger seat model (2026-10-10)

Six AI-only games with gemini-3.5-flash in every seat and as the summariser (thinking at its
default, minimal), memory off, at commit fb193104 (the record fixes, the reanimated naming and the
necromancer's clean included; the sentence that an illusionist carrying its own kill is invisible at
that door was added only after this batch). Captured by `evaluation/experiments/phase3_capture.py`
with `GOOGLE_GENAI_MODEL=gemini-3.5-flash`, two games at a time (`logs/run_batch.sh`). The run's
usage meter has no price for gemini-3.5-flash, so cost is computed from the recorded tokens at $1.50
in, $0.15 cached and $9.00 out per million (a third-party listing, not checked against Google's
page); flash-lite at its recorded $0.30, $0.03 and $2.50.

| Game | Drawn seats | Winner | Neutral | Days | Calls | Cost | Time | Rescued turns |
|---|---|---|---|---|---|---|---|---|
| f01 | serial killer, speculator | town | won | 3 | 135 | $2.22 | 8 min | 0 |
| f02 | necromancer, fortune teller | town | won (4 points) | 5 | 171 | $2.95 | 11 min | 0 |
| f03 | serial killer, fortune teller | town | lost (0 points) | 5 | 206 | $3.00 | 17 min | 6 |
| f04 | necromancer, speculator | town | won | 5 | 167 | $2.61 | 11 min | 3 |
| f05 | serial killer, speculator | town | won | 4 | 165 | $2.49 | 12 min | 2 |
| f06 | necromancer, fortune teller | necromancer | won (2 points) | 5 | 186 | $3.05 | 14 min | 3 |

| Per game, mean | flash, this batch | flash-lite, batch 4 |
|---|---|---|
| Winner | town 5, necromancer 1 | town 5, necromancer 1 |
| Cost | $2.72 | $0.72 |
| Model calls | 172 | 141 |
| Time | 12 min | 8 min |
| Lines heard | 40 | 29 |
| Words per line | 52 | 32 |

## The audit

Read by three Opus agents on the rubric of `../phase3_reads/README.md`, with a discussion-quality read;
quotes checked against the transcripts (`../phase3_reads/transcripts/f01` to `f06`).

| | flash, 6 games, ~240 heard lines | flash-lite, 10 games, ~345 heard lines |
|---|---|---|
| A invented fact | 1 | 2 |
| B summary error | 9 (1.5 a game) | 22 (2.2 a game) |
| C invalid deduction | 16 (one line in 15) | 28 (one line in 12) |
| D evil seat misstating a rule it believed | 6 | 2 |
| E night error | 2 | 6 |

**The discussion is the clear gain.** Longer days with real claim contests (two healers, an investigator
against a necromancer, a fake speculator against the real one), cross-examination that breaks a
cover ("If you were the Healer and player_8 was the Investigator, who roleblocked me?", f02), counting
arguments from the record ("player_8 only had four visitors… There is mathematically zero room for a
Sigilist", f01), and players correcting each other's rule claims. Evil covers are more coherent: the
necromancer of f06 won on a fake fortune teller claim the table could not separate from the real one.

**Invalid deductions fall less than the replay suggested.** On the frozen turns the stronger model made
1 error in 50 samples against flash-lite's 11; in full games it makes about one per 15 heard lines
against one per 12. The full games are not the replay's hand-picked failures, the lines are longer and
say more, and more claims are contested; but the honest reading is that the stronger model removes the
specific confusions the replay held (a sighting as proof, the empty house, the necromancer's timeline)
and still misreads abilities elsewhere: a sigil's "no effect" read as "did not attack" (f03), a
reported block taken as proof of the blocked player's role (f05), the investigator's check cap ignored
(f06). The evil seats' own rule misstatements rose (6), partly because they argue far more.

**What decided games.** f02: four players asserted that "the Illusionist's visit to hide a body is always
visible to a Trailseer" and voted out the real trailseer, whose empty trail was right because the
illusionist had carried its own kill; the rule was not yet in the prompts (owner's ruling the same
day; the sentence is now in the shared rules and the illusionist's card). f04: one invalid deduction
made a 2–2 tie. f06: a deliberate lie (the necromancer's fortune teller claim) won the game, which is
play. Outside the rubric, some lynches had no public reasoning behind them (a player nobody discussed,
f03; the investigator lynched right after the table said it trusted it, f04). Measured over all town
votes, outright contradiction is rare (7% of votes on flash, 6% on flash-lite); votes from a voter who
accused no one that day are 36% on flash against 70% on flash-lite; see discussion_evidence.md §8.4.

**The summariser on flash still errs**, about one and a half times a game, in a different way from the
flash-lite errors the replay targeted: dropped accounts and accusers, a healer claim given another
player's night breakdown. The invented-claim and self-action shapes did not appear.
