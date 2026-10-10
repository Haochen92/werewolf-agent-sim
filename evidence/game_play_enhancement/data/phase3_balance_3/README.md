# Phase 3: the third balance batch (the necromancer's body and the hidden trace)

Six AI-only games on the ten-seat cast, 2026-10-09, with two evil buffs on top of the second
batch's rules (`../phase3_balance_2/README.md`): the Necromancer may use the same body night after
night, and a conceal that takes also hides the carrier's visit to the concealed victim from the
Sentinel and Trailseer. Four necromancer lineups and two serial killer ones, two games at a time,
same model and capture as before. Six games are a coarse read.

| Game | Drawn seats | Winner | Neutral | Days | Calls | Cost | Rescued turns |
|---|---|---|---|---|---|---|---|
| d01 | necromancer, speculator | town | lost | 4 | 149 | $0.76 | 0 |
| d02 | necromancer, fortune teller | town | lost (1 points) | 5 | 197 | $1.02 | 1 |
| d03 | serial killer, speculator | town | won | 3 | 130 | $0.67 | 3 |
| d04 | serial killer, fortune teller | town | lost (0 points) | 3 | 113 | $0.56 | 4 |
| d05 | necromancer, speculator | town | lost | 4 | 158 | $0.82 | 5 |
| d06 | necromancer, fortune teller | town | lost (0 points) | 5 | 173 | $0.88 | 6 |

Total cost $4.71. The pool was busy again: the rescued-turn count rose through the batch.

## The reading

**The town won all six**, against three of six in the second batch on the same base rules. Put
together, the twelve games on the second batch's rules are town 9, evil 3, and the buffs did not
move that in this sample.

**The buffs barely fired.** The necromancer never had a body on two consecutive nights to reuse:
it stayed put on four of its eleven nights for want of a body, killed through a body four times,
and died on night 3, night 5, day 4 and day 5. Eight conceals took, and three of them hid a visit a
Sentinel or Trailseer would otherwise have seen, in d02, d05 and d06; the pack still lost a wolf
by day 2 or 3 in every game.

**What the town voted on this time.** Of the eleven evil lynches, three were preceded by a naming
result (three investigator reads, one of them with a sentinel sighting). The other eight came from
the day: in d03 the chanteuse was voted out on day 2 after an unexplained visit (the cover break
the discussion-quality review describes); in d04 the illusionist on day 2 after a sentinel saw it
at a saved victim's door beside the chanteuse (the victim lived, so nothing was concealed and
nothing hidden); both serial killers on day 3 with no sigil ever placed on them.

**The one lever the data still points at** is the day, not the night: the evil seats cannot keep
a cover, and the table takes a sighting as a verdict. The prompt changes for that (the cover
story in the strategy note, the ledger's line on what a visit establishes) were made after this
batch, so the next batch reads them.

## Run notes

Two at a time, rescued turns 0 to 6 a game, nothing crashed. The run script is `logs/run_batch.sh`,
the timings `logs/waves.log`. The games ran on the working tree with the two buffs uncommitted;
each manifest lists the dirty paths beside the commit.
