# Owner check: the echo gate

Each item below is one line a player wrote on the open floor of a Werewolf day, with what that
player saw: the most recent part of the earlier days' summary and today's discussion so far. Label
the KIND of THE LINE:

Judge only THE LINE, against what the table already had (the earlier days and today's discussion shown):
- "A": it adds a new fact: a role claim or counterclaim, or the speaker's own night action or result that the table has not heard yet.
- "B": it adds a new inference, or a different reading of facts already known: a reason, a consequence, or a point of view nobody has put today.
- "C": it asks a pointed question or proposes a test that would move the game (who to check, what someone must explain), and that ask was not already made today.
- "D": it restates what was already said, agrees without a new reason, asks again for what was already asked, or is filler ("nothing to go on yet", "let's hear claims").
If a line does several things, pick the most valuable kind it really delivers. Judge newness strictly against the context shown: a fact or point already on the table is D, however well put.
Whether the line is true or a good move for the speaker's side does not matter.

Write your letter (A, B, C or D) as the `label` of the row with the item's key in
`export/answers_template.json` (a `note` is optional), and save that file as `human.json` in the
packet folder. The JSON block under each item is only a reminder of the key; the answers go in the
answers file. The full guide, with worked examples, is `GUIDE.md`.

---

# Case 89

### s089 (key `voices-06.off:5:player_5:1`)

Speaker: player_5, during the day's discussion.

Earlier days (summary, most recent part):
isitor's role or what they did).
  Night 3: watched player_4; says player_6 visited them (a visit alone does not establish a visitor's role or what they did).
player_10: claimed no role.
  Night 3: went to player_2.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
[Day 3] player_4 (revealed chanteuse, killed night 3), player_5, player_10 (revealed illusionist, voted out day 4) → player_1: player_4 argued player_1's trailseer claim rested on one night 1 follow and an unverifiable night 2 block. player_5 and player_10 said they voted on the same thin case. Defense: player_1 said a block means someone with a block visited them and the Chanteuse is alive, but could not say who. player_1 asked the day 2 voters to explain their votes. Disputed: player_2 said their checks on player_1 read Not suspicious and they would not vote player_1. player_7 said the Necromancer's attack and healer save fit a power role. player_6 said the block story explains the missing follow.
[Day 3] player_6, player_7, player_1 → player_4 (revealed chanteuse, killed night 3): player_6 said player_4 voted player_1 on day 2 without a reason. player_7 wanted player_4 to explain and asked for a concrete check on player_4's night 2. player_1 said three day 2 voters gave no reasons. Defense: player_4 said they voted player_1 because the trailseer claim rested on one follow and an uncheckable block. player_4 said they are not claiming a power role and asked what evidence would change minds. Disputed: player_5 and player_10 gave the same reason for their day 2 votes as player_4.
[Day 3] player_6, player_8 (revealed speculator, killed night 4), player_1 → player_5: player_6 said player_5 voted player_1 on day 2 without a reason. player_8 said player_5 voted without a reason. player_1 said three day 2 voters gave no reasons. Defense: player_5 said they voted player_1 for the untestable night 1 follow and night 2 block. player_5 said that case is thin and they want a real read before a vote.
[Day 3] player_8 (revealed speculator, killed night 4), player_7, player_1 → player_10 (revealed illusionist, voted out day 4): player_8 said player_10 voted player_1 on day 2 without a reason and asked what they saw. player_7 wanted to hear from player_10. player_1 said three day 2 voters gave no reasons. Defense: player_10 said they voted player_1 with no strong reason, the same as player_4's. player_10 corrected an earlier claim that they abstained and said they are open to player_1 being town.
[Day 4] player_1, player_6 → player_10 (revealed illusionist, voted out day 4): player_1 argued player_10 voted player_1 on day 2 with no reason and admitted a night 3 visit to player_2. player_6 made the same case, with low confidence, and said it is the clearest thing they have. Defense: player_10 admitted visiting player_2 on night 3 to learn what they knew, and voting player_1 on day 2 without strong reason; said they are not pushing anyone today.

Today's discussion so far, as the speaker saw it:
player_1: Night 4 check: my follow on player_5 saw no visits from them, and the shot on player_8 needed a visit, so player_5 isn't the reanimated shooter. That leaves player_6 or player_7 as the Necromancer. Both claims match what I can confirm, so tonight I'm following player_6 to test it.

THE LINE:
player_1, a follow on player_5 would have shown a visit to player_8 on night 4, since the shot on player_8 was a visit from someone. Saying you saw no visits doesn't fit that. Either the follow or the night 4 read is off, so which one was it?


## Response for Case 89

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-06.of", "type": "open_floor_line", "kind": _}
]
```

---

# Case 92

### s092 (key `voices-06.off:4:player_5:2`)

Speaker: player_5, during the day's discussion.

Earlier days (summary, most recent part):
ain
It's a tie between ['player_10', 'player_4', 'player_1', 'abstain']. No one is voted out this day.
[Day 3] Night of day 3: player_2 was killed by the wolves last night. Their role is hidden by an illusionist. player_4 was struck down by a sigil last night. They were a chanteuse.

-- Claims made in the day discussion (claims, not facts; a note starting "Record:" or "Rules:" is an exact check by the game master; a plan said in the day binds no one: a player may choose a different target at night) --
player_1: claimed trailseer (day 2).
  Night 1: followed player_8; says they visited no one.
  Night 2: says they tried to follow player_7 and were roleblocked.
player_2: claimed investigator (day 3).
  Night 1: checked player_7, says they read Not suspicious.
  Night 2: checked player_1, says they read Not suspicious.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
[Day 3] player_4 (revealed chanteuse, killed night 3), player_5, player_10 → player_1: player_4 argued player_1's trailseer claim rested on one night 1 follow and an unverifiable night 2 block. player_5 and player_10 said they voted on the same thin case. Defense: player_1 said a block means someone with a block visited them and the Chanteuse is alive, but could not say who. player_1 asked the day 2 voters to explain their votes. Disputed: player_2 said their checks on player_1 read Not suspicious and they would not vote player_1. player_7 said the Necromancer's attack and healer save fit a power role. player_6 said the block story explains the missing follow.
[Day 3] player_6, player_7, player_1 → player_4 (revealed chanteuse, killed night 3): player_6 said player_4 voted player_1 on day 2 without a reason. player_7 wanted player_4 to explain and asked for a concrete check on player_4's night 2. player_1 said three day 2 voters gave no reasons. Defense: player_4 said they voted player_1 because the trailseer claim rested on one follow and an uncheckable block. player_4 said they are not claiming a power role and asked what evidence would change minds. Disputed: player_5 and player_10 gave the same reason for their day 2 votes as player_4.
[Day 3] player_6, player_8, player_1 → player_5: player_6 said player_5 voted player_1 on day 2 without a reason. player_8 said player_5 voted without a reason. player_1 said three day 2 voters gave no reasons. Defense: player_5 said they voted player_1 for the untestable night 1 follow and night 2 block. player_5 said that case is thin and they want a real read before a vote.
[Day 3] player_8, player_7, player_1 → player_10: player_8 said player_10 voted player_1 on day 2 without a reason and asked what they saw. player_7 wanted to hear from player_10. player_1 said three day 2 voters gave no reasons. Defense: player_10 said they voted player_1 with no strong reason, the same as player_4's. player_10 corrected an earlier claim that they abstained and said they are open to player_1 being town.

Today's discussion so far, as the speaker saw it:
player_6: I'm the sigilist. My sigil on player_4 last night struck them down, and the announcement confirms they were a chanteuse, so one wolf is gone. I still have one sigil and will only use it on a player who looks like they're attacking.
player_7: I'm the sentinel, and I've used both watches: on night 2 I watched player_1 and saw player_2, player_3, player_4 and player_9 come to them. On night 3 I watched player_4 and only player_6 came to them, which fits the sigil that struck player_4.
player_1: Since I'm already claimed trailseer, here's the night 3 result: I followed player_10 and they went to player_2. player_2 then died hidden, which fits an illusionist concealing the body. player_10 also said they abstained on day 2, but they voted. I'd vote player_10 today.
player_10: player_1, I won't deny that. On night 3 I went to player_2 because they were claimed investigator and I wanted to see what they knew. I didn't get anything useful from it. I did vote you on day 2 with no strong reason, same as player_4 and player_5, and I'm not pushing anyone today.
player_8: player_7's night 2 watch saw player_4 come to player_1, which is the Chanteuse's block player_1 described. That backs player_1's block story. player_7, did you see anyone else visit player_1 that night? It tells us whether the block was the only visit.
player_7: player_8, yes, I'm the sentinel. On night 2 I watched player_1 and four came: player_2, player_3, player_4 and player_9. Nobody else, so player_4's visit on player_1 was the only block visit there. That's why I think player_1's block story holds.

THE LINE:
player_7, your night 2 watch on player_1 showed four visitors, and player_1 says the block came from player_4. If player_6's sigil claim is true, player_4 was struck on night 3 while it carried the kill, so that is one wolf down. The Illusionist is the live question. I'd test player_8 and player_10 before anyone else.


## Response for Case 92

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-06.of", "type": "open_floor_line", "kind": _}
]
```

---

# Case 93

### s093 (key `voices-03.off:3:player_10:1`)

Speaker: player_10, during the day's discussion.

Earlier days (summary, most recent part):
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_6 was killed by the wolves last night. Their role is hidden by an illusionist.
[Day 2] Here's the vote result for day 2:
  player_1 voted to abstain
  player_2 voted to abstain
  player_3 voted to abstain
  player_4 voted to abstain
  player_5 voted to abstain
  player_7 voted to abstain
  player_8 voted to abstain
  player_9 voted to abstain
  player_10 voted to abstain
The town chose to abstain. No one is eliminated today.
[Day 2] Night of day 2: player_4 was killed by the wolves last night. They were a necromancer.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
None.

Today's discussion so far, as the speaker saw it:
No messages yet.

THE LINE:
Night 2 went through a necromancer kill, so the wolves are still active and two of us are wolves. Player_6 died hidden by an illusionist, so anyone who claims a role should say what they checked or watched. I have no new results to share yet. I'd like the investigator and sentinel to say what they've done so far, starting with whoever has checks or watches left.


## Response for Case 93

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-03.of", "type": "open_floor_line", "kind": _}
]
```

---

# Case 98

### s098 (key `voices-05.on:5:player_5:2`)

Speaker: player_5, during the day's discussion.

Earlier days (summary, most recent part):
lly right if player_10 is a wolf. player_5 argued a wolf carrier's visit would look the same as a check and asked for the result. Defense: player_10 said their night 1 action was an investigation of player_5, which returned Not suspicious. They said the follow fits that and would also fit a wolf visit, so they would not claim more. Disputed: player_9 argued that a check is a visit, so player_9's follow of player_10 to player_5 and player_10's check fit together.
[Day 3] player_2 (revealed vigilante, killed night 3), player_5, player_8, player_9 (revealed trailseer, killed night 4) → player_10 (revealed investigator, voted out day 3): player_2 argued player_9's sighting of player_10 going to player_5 on night 1 fits a wolf visit. player_5 and player_8 wanted player_10 voted. player_9 questioned player_10's check count. Defense: player_10 said their checks on player_5 (night 1) and player_4 (night 2) read Not suspicious. They corrected their check count to zero and said a wolf visit would be hidden from them.
[Day 3] player_7 (revealed chanteuse, killed night 3) → player_2 (revealed vigilante, killed night 3): player_7 argued player_2 only raised the player_9 sighting and pushed the player_10 vote, and asked whether player_2 holds a role or is only reading the board. Defense: player_2 claimed to be the vigilante, said they held fire on nights 1 and 2 with two bullets left, and asked player_4 and player_8 to name their night 2 results.
[Day 4] player_1 (revealed illusionist, voted out day 4) → player_6: player_1 argued player_6 has been quiet since player_7 died, so the Necromancer could be sitting there among players 6, 8 or 9. Defense: player_6 said player_1 named them without any result and asked what night 3 result player_1 saw and why a silent player is suspect. Disputed: player_1 replied they named player_6 only for being quiet, with no result behind it, and are not claiming a role.
[Day 4] player_5 → player_1 (revealed illusionist, voted out day 4): player_5 argued player_1 named player_6 without any result, then asked others for night 3 results, so player_1 should state their own night 3 action. Defense: player_1 said they named player_6 only for being quiet, asked for night 3 results to settle the sentinel-trailseer conflict, and claims no role. Disputed: player_6 argued player_1 named them without saying what they saw on night 3 and asked who to vote and why.
[Day 4] player_1 (revealed illusionist, voted out day 4), player_9 (revealed trailseer, killed night 4) → player_8: player_1 said player_8 and player_9 contradict each other on who was visited; player_9 asked player_8 who came to them on night 3, doubting the sentinel claim. Defense: player_8 said they were roleblocked on night 3, so their watch on player_9 never happened and they learned nothing; night 2 they watched player_10 and no one visited. Disputed: player_9 said they followed player_6 on night 3 and no visit was made in their name, and asked player_8 to name who came to them.

Today's discussion so far, as the speaker saw it:
player_8: I'm the sentinel. Night 4 I watched player_6, and player_9 came to them. Night 3 I was roleblocked, so that watch learned nothing.
player_6: player_8, a watch on me that night would show who came to me, and I did not go anywhere on night 4 that I can confirm for you. Player_9 is dead and their will only covers night 3, so the 'player_9 came to player_6' part can't be checked from the record. Someone asking for the watch result should say whose result it was.

THE LINE:
player_8, your night 4 watch on player_6 is the one thing we can test: if player_9 really went to player_6, that's a visit the record could back up. I'd like to hear who you say came to player_6 on night 4, and whether you think player_6 was the one who visited you on night 3 when you were blocked. My vote today leans player_6 for going quiet while player_9 and player_1 pointed at them.


## Response for Case 98

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-05.on", "type": "open_floor_line", "kind": _}
]
```

---

# Case 99

### s099 (key `voices-06.off:2:player_2:1`)

Speaker: player_2, during the day's discussion.

Earlier days (summary, most recent part):
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_3 was killed by the wolves last night. They were a vigilante.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
None.

Today's discussion so far, as the speaker saw it:
player_1: I'm the trailseer. On night 1 I followed player_8, and they visited no one, so there's no visit to read from that. I'll follow someone else tonight and report what I see.

THE LINE:
Player_1, if you follow player_8 again tonight and they visit someone, that tests your claim directly. I'm not ready to vote yet; I want to see who pushes a lynch with nothing behind it before I commit to a name.


## Response for Case 99

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-06.of", "type": "open_floor_line", "kind": _}
]
```