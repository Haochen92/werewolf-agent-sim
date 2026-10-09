# Phase 3: the second balance batch (the sigil ruling and the caps)

Six AI-only games on the ten-seat cast, 2026-10-09, after three rules changes taken from the
first balance run (`../phase3_balance/README.md`): a sigil on an immune attacker reads exactly as
a quiet night ("Your sigil had no effect"); the Investigator has 2 checks for the game; the
Sentinel has 2 watches. Everything else as the first run: gemini-3.5-flash-lite (thinking
medium), memory off, two games at a time, captured by `evaluation/experiments/phase3_capture.py`.
One game per lineup plus a second serial killer + speculator and a second necromancer + fortune
teller. Six games are a coarse read, and read against the thirteen before them.

| Game | Drawn seats | Winner | Neutral | Days | Calls | Cost | Rescued turns |
|---|---|---|---|---|---|---|---|
| c01 | serial killer, speculator | serial killer | lost | 4 | 137 | $0.64 | 0 |
| c02 | serial killer, fortune teller | wolves | lost (0 points) | 4 | 135 | $0.60 | 3 |
| c03 | necromancer, speculator | town | won | 6 | 194 | $0.91 | 9 |
| c04 | necromancer, fortune teller | town | won (2 points) | 5 | 192 | $0.81 | 9 |
| c05 | serial killer, speculator | serial killer | lost | 4 | 138 | $0.63 | 2 |
| c06 | necromancer, fortune teller | town | lost (0 points) | 5 | 152 | $0.83 | 1 |

Total cost $4.42. c03 and c04 ran while the shared pool was busy: nine turns each went to
the rescue model, so those two are the least clean games of the six.

## The reading

**Evil won three of six, after none of thirteen.** The serial killer won twice (c01, c05) and
the wolves once (c02). All three evil wins came in the serial killer lineups, and all three
necromancer lineups went to the town, as every necromancer game before had. In the thirteen
earlier games the serial killer lineups went to the town six times of six.

**The table lost its aim.** Fourteen votes: 7 evil, 3 town, 4 neutral, against 27 evil of 33
before. The first evil lynch came on day 3 in three games and never in two (c01, c05: the town
voted out the speculator, then the vigilante or nobody, while the serial killer and the pack took
two a night). The neutral became the scapegoat: with fewer results to vote on, the town voted
out the unverifiable seat four times.

**Which change did it.** The games cannot separate the two cleanly, but they lean one way:

- *The sigil.* A sigil landed on the serial killer twice in the three serial killer games, and
  the serial killer survived to win both (c01, c05); in the first run every such sigil was
  followed by the serial killer's lynch. The "no effect" record gave the sigilist nothing to
  claim, and no serial killer was named by a sigil.
- *The caps.* The investigator made 1 or 2 checks a game against 2.5 before, the sentinel 2
  watches against 2.1 (the third check or watch some games show is the necromancer's, through
  the dead holder's body, which spends nothing of the holder's; a blocked watch in c02 spent
  nothing either, and no count went below zero). The caps bit little in count, as
  the games are short, but the capped roles now sit out nights, and the every-night rhythm that
  swept the doors is gone. The necromancer games, where the sigil cannot apply (a borrowed attack
  evades it), still went to the town on days 5 and 6 by elimination, so the caps alone did not
  move that lineup.

So the sigil ruling is the likely lever for the serial killer lineups, and nothing yet moves the
necromancer lineups, where the town wins late by counting. The vigilante reading Suspicious, the
dial proposed and not ruled, is aimed at the pack, which won once here.

**What this batch does not say.** Six games, two of them with nine rescued turns each. A
three-of-six is a contest, not a balance; the next batch should repeat the same rules before
anything else changes, so the rate has a second reading.

## Run notes

Two games at a time still met the shared pool's limits in the afternoon (13 and 12 bounced calls
in c03 and c04 against 2 to 4 in the others), all taken by the rescue model; nothing crashed,
which is the rescue-stall fix (05b5365f) doing its job. The run script is `logs/run_batch.sh`,
the timings `logs/waves.log`. The games ran on the working tree with the three changes
uncommitted; each manifest lists the dirty paths beside the commit.
