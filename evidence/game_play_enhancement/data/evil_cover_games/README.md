# Evil covers: paired games (2026-10-18)

**Question:** with R11's cards (claim, never deny), implied role claims (slice 13b) and the covers line
(slice 14), do the evil seats fake-claim in whole games, and what does it do to the balance?

**Method.**
- `after/`: 8 Haiku games at 7f3551f0, deals voices-01..08 (voices on).
- `before/`: the same deals at c61fa762, the silence build (old evil cards, no covers), run from a
  detached worktree. Deals 01–04 are the silence calibration games (`../silence_calibration/games/`),
  run from that same code.
- A deal is the game id's seed: same roles, same seats. Games diverge after the first differing line.
- Scorer: `evaluation/experiments/evil_cover_screen.py games` (`games_scores.json`).
- Cost: $2.52 for the 12 new games. All leak checks pass.

| 8 games each | Before | After |
|---|---|---|
| Winners | town 7, Serial Killer 1 | town 5, **wolves 3** |
| Evil seats that claimed a role (of 24) | 3 | **11** |
| Evil seats voted out | 15 | 10 |
| Evil seats alive at the end | 1 | 5 |
| Day lynches on evil / on everyone else | 15 / 10 | 10 / 13 |

**The three wolf wins, read in full:**
- **voices-06:** the Necromancer claimed the Investigator early as a soft claim ("I kept both my
  checks"). The real Investigator counter-claimed with a real check and was voted out 6–2 on "why
  did you wait until day 2". The engine said what it can: at most one holds it.
- **voices-03:** in the final three, the Illusionist, claiming the Trailseer, said its follow saw
  the Sentinel visit no one; the Sentinel said it watched player_7. Word against word, the Vigilante
  sided with the fake. Earlier the Necromancer said it "held fire", and the real Vigilante caught the
  implied claim and voted it out.
- **voices-02:** no fake claim decided it. The Serial Killer's cover (the Sigilist, matching the
  Trailseer's sighting) still lost 6–1. The town then voted out its own true Sentinel, and the
  Vigilante shot the Healer.

## Reading

1. **The evil seats now claim, and the claims work:** about four times as many claimed (11 of 24
   against 3), fewer were voted out, and the wolves won 3 of 8 games against none.
2. **The balance moved from town-heavy toward even.** 7 of 8 for town was easy; 5 of 8 is closer to
   a contest. Eight games is noise-sized: a direction, not an estimate.
3. **What the town now lacks is judgement between two claimants,** not facts. The engine flags the
   counter-claim. Choosing (the claimant with a result over one without; a story that would have been
   caught by the next night's results) is the seats' job. If the town falls further behind, the lever
   is more cross-night checks for the town, never less support for evil.
