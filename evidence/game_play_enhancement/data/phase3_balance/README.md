# Phase 3: the balance run

Ten AI-only games on the full ten-seat cast, 2026-10-09, after the wiring was committed
(6dda451b..d9717d50) and the review's six fixes landed: gemini-3.5-flash-lite (thinking medium),
memory off, captured the production way by `evaluation/experiments/phase3_capture.py` (the same
files per game as `../phase3_games/`: manifest, record, chunks, calls). Each of the four lineups
was dealt two or three times. Read together with the three first games in `../phase3_games/`,
that is thirteen games on the cast. Ten games are a coarse read: they can say whether a side ever
wins and how fast the town finds evil, not anything finer.

| Game | Drawn seats | Winner | Neutral | Days | Calls | Cost | Rescued turns |
|---|---|---|---|---|---|---|---|
| b01 | serial killer, speculator | town | won | 4 | 134 | $0.64 | 1 |
| b02 | serial killer, fortune teller | town | won (5 points) | 4 | 119 | $0.62 | 0 |
| b03 | necromancer, speculator | town | won | 5 | 214 | $1.15 | 1 |
| b04 | necromancer, fortune teller | town | lost (0 points) | 3 | 119 | $0.60 | 1 |
| b05 | serial killer, speculator | town | won | 4 | 163 | $0.82 | 1 |
| b06 | necromancer, speculator | town | lost | 6 | 229 | $1.22 | 1 |
| b07 | serial killer, fortune teller | town | lost (0 points) | 3 | 99 | $0.52 | 0 |
| b08 | necromancer, fortune teller | town | lost (0 points) | 4 | 153 | $0.81 | 0 |
| b09 | serial killer, speculator | town | lost | 3 | 97 | $0.47 | 0 |
| b10 | necromancer, speculator | town | lost | 7 | 272 | $1.43 | 0 |

Total cost $8.30. A rescued turn is one the primary model bounced (a 429) and the rescue
model took; it is a different model's turn and is counted so the games with any can be weighed.

## The reading

**The town won all ten, and all thirteen with the first games.** No wolf, serial killer or
necromancer win on this cast yet. The neutral is the only other side that wins: the speculator
won four of six (every time it picked, it picked Town), the fortune teller two of seven.

**The town votes evil out with very few misses.** Over the thirteen games the table voted 33
times: 16 wolves, 11 lone killers, 5 town, 1 neutral. All 39 evil seats died; 27 by vote,
the vigilante shot 7 (3 of them on a night the sigil struck the same player), a sigil alone
killed 2, the serial killer killed 3 wolves. The first evil lynch came on day 2 in six games and
day 3 in six (one game, b10, took until day 6).

**What preceded the town's votes.** Of the 27 evil lynches, 11 were preceded by a town night
result that had named the player: 7 an investigator's Suspicious, 3 a sigil's "immune" result on
the serial killer, 1 a sentinel's sighting at a death. A preceding result does not by itself
show why the table voted as it did; the day-2 summaries of b02 and b09 do show the sigilist's
result argued and accepted. The other 16 had no such result before them: claims checked against
the record, visits argued from the trails, and from day 4 on the process of elimination, since
by then the dead roles are public and the living evil are few.

Two mechanics stand out as stronger than the sheet expected:

- **The sigil finds the serial killer.** A sigil on an attacker who is immune gives the sigilist
  the record "immune", and on this cast the only player immune every night is the serial killer
  (the necromancer only on night 1 and it cannot attack then, a self-betting fortune teller is
  not an attacker, a borrowed attack evades the sigil). Three of the six serial killer lynches
  followed exactly that (b02 and b09 on day 2, b05 on day 4), with the sigilist claiming "set a
  sigil on X, they attacked and survived"; in b02 the sigilist argued that a vigilante could not
  have survived by immunity, which undid the killer's cover claim. The immune string names no
  role, but the deduction is one step. The serial killer's silent whiff is no cover against a
  sigil.
- **Three information roles on ten seats, and visits by name.** The sentinel and trailseer see
  names at doors; a killer visits every night; the investigator reads the pack and an attacking
  necromancer. With a healer on top (13 of the 51 kill attempts by the pack and the lone killers
  over the thirteen games were saved), evil loses a member a day from day 2 and never reaches parity.

**What evil did with its nights.** Night 1 kills landed on town 12 times of 19, on the neutral 5
times, on another evil 2 (the serial killer hit a wolf once, the chanteuse the necromancer once).
The serial killer's targets over all nights: town 9, wolves 3. Evil never coordinated against
the information roles in particular; the night-1 lot spreads the first kill, and from night 2
the pack mostly took whoever had accused it.

## What the sheet offers as dials (nothing is ruled here)

The sheet lists dials for a town that is too strong; the owner rules. The ones this reading
points at, in the order of their likely effect:

1. **The sentinel reports factions instead of names** (sheet, "Shared rules"): the sighting
   still says a killer came, not which seat. This blunts the strongest single read.
2. **The sigil's immune result** (RULED 2026-10-09, built): an immune attacker reads exactly as
   a quiet night, "Your sigil had no effect", in the result word, the record and the will, so the
   serial killer is not named by one night's luck.
3. **The investigator's read of an attacking necromancer** stays; it fired rarely.
4. **The neutral**: the speculator's pick of Town is a sure thing while the town always wins;
   it corrects itself once the other sides can win. The fortune teller's third self-bet (sheet)
   is not the lever.

Changing the pack (a third wolf, or the chanteuse's block every night) is the blunt option and
should wait until the reads are blunted, since the losses are information losses, not number
losses.

## Run notes

- **Load.** Five games at once overloaded the Vertex shared pool: every game of the first wave
  logged 429s, four finished on the rescue model's turns and one crashed; all five of the second
  wave crashed within two minutes. Two games at a time ran with no 429 at all. The crashed first
  attempts' logs are kept in `logs/failed_first_attempt/`; the ten games here are the four that
  finished in wave 1 (b01, b03, b04, b05, with the rescued turns counted above) and the six rerun
  two at a time.
- **The crash was a bug, fixed:** when the rescue model also bounced, the stall sentinel reached
  the turn resolver (`'object' has no attribute 'message'`) instead of the typed fallback.
  `Agents/turn/agent_player.py`, with a test in `tests/engine/test_model_fallback.py`.
- The run scripts are `logs/run_waves.sh` (the first attempt) and `logs/run_rest.sh` (the rerun);
  `logs/waves.log` has the timings.
