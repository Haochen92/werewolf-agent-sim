# Phase 3: the first ten-seat games

The first AI-only games after the wiring (2026-10-09), captured the production way by
`evaluation/experiments/phase3_capture.py`: gemini-3.5-flash-lite (thinking medium), memory off,
the rules block composed from each game's lineup. Per game: `<label>.manifest.json` (provenance,
usage, cost), `<label>.record.json` (roles, lineup, the neutral's result, every night record, the
day channel and summaries, the resolutions, the leak check), `<label>.chunks.jsonl` (every stream
chunk) and `<label>.calls.json` (every model call). `game1.chunks.jsonl` is also the test suite's
captured fixture (`notebooks/fixtures/chunk_catalogue_phase3.jsonl`).

| Game | Lineup (drawn seats) | Winner | Neutral | Days | Calls | Cost |
|---|---|---|---|---|---|---|
| game1 | serial killer, fortune teller (drawn) | town | fortune teller won (2 points) | 3 | 95 | $0.46 |
| game2 | necromancer, fortune teller (forced) | town | fortune teller lost (died night 1, concealed) | 5 | 178 | $0.92 |
| game3 | necromancer, speculator (forced) | town | speculator won (picked Town on night 3) | 4 | 139 | $0.68 |

## What the games showed

**The rules ran as the sheet says.** In game1 the sigilist placed a sigil on the chanteuse on
night 1, the chanteuse carried the pack's kill and was struck down; the sentinel saw the sigilist
and the trailseer at the chanteuse's door, and the trailseer saw the chanteuse visit the pack's
victim and the player it blocked. The illusionist concealed the trailseer's body on night 2 ("Their
role is hidden by an illusionist"), and the pack's victim was attacked by the wolves and the serial
killer on the same night. The vigilante's record read out at its death: "night 1, was roleblocked;
night 2, held fire". The fortune teller named the illusionist's role on its bet and scored two
points the night the vigilante shot it, and won beside the town.

In game2 the necromancer acted through three bodies on three nights: it watched through the dead
sentinel (and saw four visitors at one door), blocked the vigilante through the dead chanteuse, and
followed the investigator through the dead trailseer. The investigator read it Not suspicious on a
night it did not attack. The healer saved the investigator from the wolves on two nights running.
The town found both wolves by vote and the necromancer last, on day 5.

**The table used the new information.** Day 2 of game1 opened with the trailseer and the sentinel
stating their trails, the vigilante confirming it had been visited, and the sigilist claiming its
hit; the serial killer reasoned aloud, correctly, that the chanteuse's two visits were the pack's
kill and a block. The lone killers survived to the last votes in both games.

**Two bugs the live games found, both fixed before game3:**
- The reads a turn produced came from the lineup's own read class and the turn effects rejected
  them (game1's first attempt crashed on the first opening turn; the offline test's fake model had
  emitted no reads, and now does).
- A blocked action spent its use: game2's vigilante lost a bullet to a block. The sheet now says a
  blocked action spends nothing.

**One false positive in the leak check:** a line in the pack's chat shared its phrasing with
another player's private read ("claimed an investigator check on player_8"), and the reads check,
which treats only the public channel and the summaries as shared vocabulary, flagged it. The
capture now gives the check the pack's chat as well.

In game3 the necromancer killed through the dead illusionist's body on night 3, and the morning
named the wolves; the trailseer who followed the necromancer that night saw it visit no one, which
is the stealth the sheet promises. The speculator picked Town on night 3, the morning announced
"The Speculator has picked Town" without the seat, and it won beside the town the next day. The
sigilist's second sigil struck the chanteuse on night 2 (its first, on the speculator, missed). The
table voted the illusionist out on day 3 and the necromancer on day 4.

**Open, for the reading pass:** the day 1 opening is still thin on claims; the fortune teller died
on night 1 of game2 before any bet could settle (the pack's lot fell on it), so its play is seen in
game1 only; the vigilante held fire every night of game3 (two bullets unspent); the abstain vote
on game3's day 2 (five abstentions against a split) is the first no-lynch day seen in the ten-seat
game.
