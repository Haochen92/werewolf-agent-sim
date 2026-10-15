# Rule errors in the revised-prompt Sonnet 5.5 points (2026-10-12)

The same screen, on the 176 points of the batched Sonnet 5.5 re-synthesis with the mechanics,
phase and length rules (`ccb9b96a`; `strategy_points_sonnet2.json`, store
`memory_stores/v8_seed_synth_sonnet2`). Opus subagent; Claude checked the saved-shot announcement
and the block-as-visit rule against the rules text. One read, not a measurement.

**19 of 176 flagged (10.8%): 7 high, 12 medium.** The earlier sets: Sonnet 32/164 (20%), flash-lite
14/150 (9%).

| Key | Cell | Claim | The rule | Conf. |
|---|---|---|---|---|
| 6d335414 | chanteuse/day_discussion | Day 1 after a night-one death | Day 1 comes first, discussion only | high |
| 8c3e39dc | chanteuse/day_discussion | a night-one visit report on Day 1, leaning to abstain | no night before Day 1, no vote on it | high |
| 4f50a5d9 | illusionist/night_action | a lone wolf carries only when the Sigilist is dead | a lone wolf always carries; the pack kills every night | high |
| 22f301bf | sigilist/day_discussion | "no effect" when the target was protected | a Healer save has its own result | high |
| 57238ce9 | sigilist/day_vote | same | same | high |
| 4c23d7ef | sigilist/night_action | a strike removes a Necromancer attacking directly | it attacks only through a body, which a sigil cannot punish | high |
| af542291 | sigilist/night_action | a sigil for the lone killer; a strike reveals the Sigilist | the Serial Killer is immune; the morning names "a sigil", not who | high |
| 2832b90f | illusionist/day_discussion | a night result on Day 1 or 2, drift to abstain | no night result or vote on Day 1 | med |
| 0e0038b7 | chanteuse/night_action | a block is seen only by the blocked player | blocking is a visit, seen by a Sentinel or Trailseer | med |
| e260d410 | fortune_teller/day_vote | a body's unused bullets go to the Necromancer | a body gives its ability with no use limit, no carry-over | med |
| b28a0ba7 | illusionist/night_action | (situation) the pack decides who carries | rotation by seat order | med |
| 67c61831 | investigator/day_vote | Suspicious means a wolf | a Necromancer reads Suspicious on a night it attacks | med |
| 969a5bb5 | sigilist/day_discussion | a Sentinel reports where you went | a watch shows who visited the target | med |
| a596b562 | sigilist/day_discussion | "no effect" when an attacker was protected | the Healer save has its own result | med |
| 4da29324 | trailseer/night_action | a blocked follow is evidence about the player followed | the block was on the Trailseer | med |
| f02e57b8 | vigilante/day_discussion | a night-immune target is the Serial Killer | also a night-1 Necromancer or a self-betting Fortune Teller | med |
| 7e2e396c | sigilist/night_action | a strike on a carrier removes a wolf or killer | a sigil cannot remove either lone killer | med |
| 213decd1 | vigilante/night_action | at three or four alive a wolf kill ends the game | at four, one wolf against two plays on | med |
| e8aa442c | vigilante/night_action | the shot is hidden unless it kills | every attacked player is announced, saved or not | med |

**Town night points that prescribe day actions: 1 of 32** (549964d2, Trailseer), against 31 of 34
mentioning day acts in the first Sonnet set (that one a regex pointer; this one a read).

**Gone since the first Sonnet set:** the Necromancer immune every night; results reaching a dead or
blocked player; written wills; a blocked shot wasting a bullet; a neutral that kills. The pack
choosing its carrier is down from 5 to 1, and only in a situation.
**Still there:** the sigil's "no effect" misread (3), the sigil against a lone killer (3), Day 1
events that need a night before it (3).
