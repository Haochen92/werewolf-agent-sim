# Phase 2 step 8: four games on the day with rounds (2026-10-07)

*The games were played, counted and read by an Opus subagent; the reading was reviewed and the
investigator finding (§6) added by Claude. Design record: `discussion_evidence.md` §7.4 step 8.*

## 1. Outcome

- **The mechanics work as designed.** The opening round, the sequential sweep with the per-line
  echo gate and the closing defence all behaved as §7.4 describes, in all four games. Day 1 was
  the opening and the summary only (36 of 36 opening turns passed, 10 model calls). The utterance
  cap was never reached; the closest day was 11 of 12 lines. A full table costs about 30 model
  calls a voting day.
- **The opening produced no contest.** Only the investigator and the vigilante ever spoke in an
  opening: 5 of 106 opening turns across the four games. No evil player claimed a role and no
  counterclaim appeared anywhere. The opening filter held one line, a deduction, correctly.
- **The closing changed no vote.** It ran on 7 of 12 voting days, and the defended player was
  voted out all 7 times.
- **The investigator who claimed in an opening was lynched that day, every time.** Games 1 and 4
  here and the step 6 capture, 7–1 each time. §6 traces why.
- **The sweep plus gate removes the parallel round's pile of identical lines, with two costs.**
  With no claim to react to, a day fills with procedural "building on X" chains and no accusation
  (games 2 and 3, day 2, both ending in an abstention). The gate still errs toward holding: about
  12 of 19 holds in games 1, 2 and 4 were clear repeats, the rest were not, and once (game 1, day
  3) it held an accused player's own defence because the accusations against them were untagged,
  so the "answering someone who named me" exemption never fired. That player never spoke that day
  and was lynched as a villager.
- **Days end when the sweeps run out, not at the cap.** The long reactive exchanges answer
  themselves, but they loop on one rebuttal until the per-pair limit stops them.
- **The judge's labels show no clear change.** Turn-taking and reveal-timing counts are small and
  track one day's topic in each game.

Two rulings followed on the day: held lines count for nothing in the closing (before, a held
echo's accusation tags counted, so the moderator named accusers whose lines nobody had heard, four
of six in game 4 day 2), and the balance questions of §6 are levers for the owner, not pulled.

## 2. Setup

All games on `gemini-3.5-flash-lite` (thinking level medium), memory off, at HEAD `d9e9aee9`,
one process per game, streamed the production way by `evaluation/experiments/phase2_step8_capture.py`.

| game | id | winner | duration | model calls | cost |
|---|---|---|---|---|---|
| game1 | `phase2-step8-game1-c3eec1ba` | villagers, day 4 | 415 s | 118 | $0.44 |
| game2 | `phase2-step8-game2-977d4407` | villagers, day 4 | 398 s | 93 | $0.34 |
| game3 | `phase2-step8-game3-fa007e1d` | wolves, day 4 | 380 s | 119 | $0.37 |
| game4 | `phase2-step8-game4-e2eb516d` | villagers, day 4 | 494 s | 137 | $0.55 |

Game 3 ran into Vertex 429s and 36 of its 115 successful calls went to the rescue model
(`gemini-3.1-flash-lite`); game 4 was played as its replacement and game 3 is kept, marked.
The judge (`gemini-2.5-pro`, `evaluation/experiments/discussion_evidence.py`) read the four games
and re-read the June v2 game `832404e9`, so both sides have the same judge; the re-read matches
the 2026-10-03 read. Baselines: `832404e9` (no rounds, one human seat, no timing or call log),
the step 6 capture of the 4c design, the 4c day rerun and the 4b smoke game. A count a baseline
has no field for is "n/a" in `counts.md`, never approximated.

## 3. Counts (voting days)

| game | openings spoken / turns | lines per day | reactive | sweep lines / turns | held by gate | closings run / defended lynched | seconds per day | calls per day | judge turn_taking / reveal_timing |
|---|---|---|---|---|---|---|---|---|---|
| g1 | 1/27 (+1 held by the filter) | 5, 3, 11 | 10 | 8/17 | 8 | 2/3, 2/2 | 92, 134, 120 | 34, 27, 24 | 5/21, 1/21 |
| g2 | 0/24 | 6, 5, 6 | 6 | 11/14 | 2 | 1/3, 1/1 | 172, 69, 72 | 29, 21, 13 | 0/18, 1/18 |
| g3* | 1/27 | 6, 7, 10 | 8 | 14/19 | 1 | 1/3, 1/1 | 96, 113, 91 | 34, 27, 23 | 5/23, 1/23 |
| g4 | 3/28 | 6, 11, 8 | 12 | 10/18 | 8 | 3/3, 3/3 | 99, 181, 103 | 34, 39, 23 | 0/29, 4/29 |
| 4c capture | 1/22 | 8, 7 | 4 | 10/16 | 6 | 2/2, 2/2 | n/a | n/a | not judged |
| v2 `832404e9` | n/a | 9, 8, 6, 9 | 10 | 22/35 | 8 (old gate) | n/a | n/a | n/a | 0/30, 5/30 |

\* a third of game 3's calls ran on the rescue model.

Voting-day openings took 7–12 s; one stalled seat stretched a round to 66 s. The night added
20–31 calls per game. Per-day detail: `counts.md`.

## 4. Reading of each game

- **Game 1.** On day 2 the investigator opened with a check on the player who had died that night
  and was lynched 7–1. The gate held 4 of 7 sweep lines; two of the holds (player_4 and player_5
  calling the check "convenient") added suspicion, player_7 then made the same point and was kept,
  and the moderator's line named player_4 and player_5, whose lines nobody heard. On day 3
  player_7's defence was held (untagged accusations, §1), player_7 never spoke and was lynched as
  a villager. Day 4 was an 8-line reactive argument, and the serial killer was lynched after the
  closing.
- **Game 2.** Both information roles died on night 1. Day 2 was a procedural "building on" chain
  and the village abstained. On day 3 the gate held player_6's challenge to player_8, a false
  positive, since player_7 said nearly the same thing next and was kept. The wolf was voted out
  after the closing.
- **Game 3 (degraded).** Day 2 was a procedural chain and the village abstained. Day 3 was a
  decent exchange that ended in a tie. On day 4 the investigator's opening was garbled and the
  serial killer's closing turn failed with no line (the bug in §7, since fixed).
- **Game 4.** On day 2 the investigator outed the vigilante in its opening and was lynched 7–1.
  Four genuine repeats were held, yet the moderator named six accusers. Day 3 was the best day of
  the four games, an 11-line argument, and a villager was lynched. On day 4 the serial killer was
  lynched after the closing.

## 5. Against §7.3

- *What the openings contain:* an investigator's result or a vigilante's line; nothing from evil,
  no counterclaim. The opening is a stage with one actor.
- *Whether the opening feels slow:* 7–12 s a round when every seat answers promptly; one stalled
  seat made 66 s. The stage's "preparing" scene and grouped passes were not watched (§8).
- *The closing:* ran on 7 of 12 voting days; the defended player was voted out 7 of 7.
- *Cost:* about 30 calls a voting day on a full table, $0.34–0.55 a game.
- *Judge labels:* no clear change at this sample size.

## 6. The investigator finding

In every Phase 2 game where the investigator claimed in a day 2 opening it was lynched that day:
games 1 and 4 here and the step 6 capture, 7–1 each time. Over the 28 June games (no rounds), 18
investigators claimed on day 2 and 1 was lynched that day. Read in full, the chain has five links.

1. **Seat 1 draws every night 1 action.** The night prompts list the survivors in seat order and
   nobody has a read yet, so the first name is picked. Over the 28 June games the investigator
   checked `player_1` on night 1 in 21, the serial killer hit it in 26, the wolves in 20, the
   healer protected it in 25. In the four games here the investigator checked `player_1` in all
   four, and `player_1` died on night 1 in three (in June the healer's protection of seat 1 kept
   it alive in all but three games).
2. **The result is about a dead player, and the opening asks for it anyway.** The opening rule
   says "state your own night action or its result", so the investigator says "I investigated
   player_1, the healer" after the morning already revealed player_1 as the healer. The table reads
   a result it cannot check as a safe fabrication.
3. **Seven players, one topic.** Everyone else passes the opening, so the sweep hands all seven the
   same single item and the open floor asks for "a contradiction you noticed": seven versions of
   "a convenient claim", held or not.
4. **The closing counted the held ones.** The moderator named three to six accusers, so the vote
   opened on "player_9 has been accused by player_1, player_2, player_4, player_5, player_6 and
   player_7." Ruled out the same day: held lines now count for nothing.
5. **The vote asks for the most suspicious player, and one name is on the table.** Even the
   investigator's defenders voted with the rest; the healer in game 4 gave as its reason that the
   investigator was "drawing universal suspicion and a massive bandwagon".

The June game with the same claim on a dead player (`228eb3f8`: "I investigated player_1 and
found out they were the healer" after player_1 flipped healer) ended the same way, 6 votes
against the investigator. There it was one claim in eighteen; the rounds made it three in three,
because the opening forces the claim out and the sweep makes it the day's only subject.

Levers, for the owner: the night prompts' target list (shuffled, or without a fixed first name;
a prompt-input change, so an epoch); an opening rule that a result the morning already made
public is not worth an opening; the vote's "most suspicious" ask when one name is on the table.

*Pulled the same day (owner's ruling):* the first lever, as a per-agent seeded order of every
player list with the human's board kept in seat order, plus the example read's seat replaced by a
placeholder; the second bias and the fix are recorded in `discussion_evidence.md` §7.5 and checked
offline in `data/night1_target_bias/`. The other two levers stay open.

## 7. Bugs and issues

Found by the tests or the games and fixed on 2026-10-07:

- The stage closed a round at the seated human's ask (`input_request`), which the server sends
  right after `round_opened` and before any of the round's lines, so "nothing to add" listed every
  player (`beatsFor.ts`).
- A turn that failed every attempt lost its round, so a failed closing was stored as an ordinary
  discussion entry (`agent_player.py`; game 3, day 4).
- `tests/leak_test.py`'s wolf output keys lacked `wolf_vote`, so every game reported a false leak.
- An orphaned docstring in `DayChannel` sat under the wrong field.

Left as they are, named for the owner: the gate's strictness, the accusation tags' accuracy
(§9.8: an untagged accusation left the accused no reactive turn and no exemption), and the
procedural days when nothing is claimed.

## 8. Not measured

The stage's feel (no Playwright in this pass); baseline cost and timing (the older records have
none); a count of restated lines the gate kept. With four games, these are readings, not rates.

## 9. Files

- `gameN.{manifest.json,record.json,chunks.jsonl,calls.json}`: see the README.
- `counts.json`, `counts.md`: `evaluation/experiments/phase2_step8_counts.py`.
- `baselines/replay_832404e9.json`; `judge/<game>/`.
- Tests: `tests/engine/test_{sweep,closing,opening_filter,echo_gate,day_rounds,round_payload_leaks}.py`
  and cases added to the translator, announcement, prompt, fallback and bench tests;
  `frontend/src/stage/instruments/turn-dock-heading.test.ts` and cases in `beatsFor`, `foldEvents`
  and `roles` tests.
