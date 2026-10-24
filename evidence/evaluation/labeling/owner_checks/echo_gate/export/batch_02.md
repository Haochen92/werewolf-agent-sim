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

# Case 17

### s017 (key `voices-03.off:2:player_9:1`)

Speaker: player_9, during the day's discussion.

Earlier days (summary, most recent part):
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_6 was killed by the wolves last night. Their role is hidden by an illusionist.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
None.

Today's discussion so far, as the speaker saw it:
No messages yet.

THE LINE:
Player_6 is gone with a hidden role, so we have no info from that night. I'd like everyone to say whether anyone was blocked or protected overnight so we can narrow down who could have been targeted. I'll keep an open mind on everyone until we see votes.


## Response for Case 17

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-03.of", "type": "open_floor_line", "kind": _}
]
```

---

# Case 18

### s018 (key `voices-04.on:4:player_6:1`)

Speaker: player_6, during the day's discussion.

Earlier days (summary, most recent part):
ight) --
player_8: claimed trailseer (day 2).
  Night 1: followed player_10; says they visited player_7 (a visit alone does not establish what they did there).
  Night 2: followed player_9; says they visited player_8 (a visit alone does not establish what they did there).
player_7: claimed sigilist (day 2). Record: revealed as sigilist when they were voted out on day 2, as claimed.
  Night 1: says they did not act.
player_5: claimed investigator (day 3).
  Night 2: checked player_8, says they read Not suspicious.
player_9: claimed no role.
  Night 2: went to player_8.
player_4: claimed no role.
  Night 2: says they did not act.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
[Day 2] player_8, player_9, player_2, player_3 → player_7 (revealed sigilist, voted out day 2): player_8 claimed player_10 visited player_7 on night 1 as a block; player_9 said this conflicts with player_7's clean report and leaned toward voting player_7. Defense: player_7 said they placed nothing, visited no one, got no roleblock notice, and that a lone follow is one claim against their word. Disputed: player_5 argued that if player_8's follow is real, player_7 was blocked and so is Town. player_6 said both player_8's and player_7's accounts cannot be true.
[Day 2] player_7 (revealed sigilist, voted out day 2), player_3 → player_8: player_7 argued player_8's follow conflicts with player_7's no-block morning report, so either the follow or the report is off; player_3 said player_8's account only holds if honest. Defense: player_8 said the follow was real, that a blocked player is told so in the morning, and asked player_7 for the exact morning report wording. Disputed: player_9 argued player_7 should recheck the morning report since both accounts cannot be right; player_2 said player_8 gave a specific result naming player_7.
[Day 2] player_7 (revealed sigilist, voted out day 2) → player_9: player_7 said the players pushing against them, namely player_9, have no night 1 result of their own.
[Day 3] player_5, player_8 → player_4 (revealed serial killer, voted out day 3): player_5 argued player_4 never answered for their night 2 and would be voted if they could not answer. player_8 argued player_4 left their night unchecked and should be voted today unless they gave something firmer. Defense: player_4 said they stayed home on night 2 and went to nobody, claimed no role, and called player_5's check and player_8's follow unverified claims.
[Day 3] player_4 (revealed serial killer, voted out day 3) → player_9: player_4 argued player_9's visit to player_8 fits the night 2 save, so player_9 should be tested before anyone else. Defense: player_9 said they went to player_8 on night 2, gave no more of their night, and asked player_4 to explain their own night first. Disputed: player_2 argued player_9's visit fits the save, that player_8's follow is consistent with player_9 as healer, and that player_5's check is only one claim.

Today's discussion so far, as the speaker saw it:
player_3: I'm the Fortune Teller, and I've already scored my two points. My night 3 bet on player_5 hit, so player_5 really was the Investigator. That means player_5's night 2 check on player_8 is genuine, and it's worth weighing that when we look at player_8's trailseer claim.
player_6: I'm the sentinel. On night 2 I watched player_8 and saw player_2, player_4, player_5 and player_9 come to them, so player_4's claim of visiting nobody was false.
player_8: I must speak plainly, though it may cost me. I am the trailseer. On night 3 I followed player_5, and they went to player_9. Player_5 claimed investigator, so that visit may have been a check.
player_9: player_6's night 2 watch checks out against what I know: I went to player_8 that night, and the serial killer's attack means player_4 did too, so player_4's 'nobody' was false. That leaves player_2 as the one visitor to player_8 I can't account for, with no claim to explain it. I'd vote player_2 today.
player_2: player_9, I went to no one on night 2 and I have no role to show for it. I am not going to hang my name on a claim I cannot back. If you want a test, the sentinel's watch on player_8 is the cleanest thing we have, and you should answer why you went there rather than pointing at me.
player_3: I'm not going to claim anything I can't prove, but the arithmetic is worth doing. If player_6's watch is real, the visitors to player_8 on night 2 were 2, 4, 5 and 9. Player_4 was the serial killer and player_5 the investigator, so the wolf carrier and the healer were 2 and 9, one each. Player_9, if you're the healer, say so and we can check it against the save.

THE LINE:
Sharing my night 2 watch on player_8: 2, 4, 5 and 9 came to them. player_2, you said you went to no one, but you're on that list. Explain that visit before anyone else gets pushed.


## Response for Case 18

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-04.on", "type": "open_floor_line", "kind": _}
]
```

---

# Case 24

### s024 (key `voices-07.on:2:player_7:1`)

Speaker: player_7, during the day's discussion.

Earlier days (summary, most recent part):
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_7 was attacked by the serial killer but was saved by the healer!

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
None.

Today's discussion so far, as the speaker saw it:
player_3: Night 1 gave us a save on player_7, so the serial killer is active and can't be struck at night. Nobody has claimed anything yet. I'd like the Investigator, Sentinel or Trailseer to come forward with a check or watch, because one of those results is the only thing that will let us sort the table. Until then I have no vote to cast.
player_5: Night 1 was a save on player_7, so whoever is holding a watch or follow should speak up with what they saw. I'd rather see a Sentinel or Trailseer claim with a named visitor than a vague 'nobody visited me'. Until someone gives a concrete result, I'm not voting on a name.

THE LINE:
Agreed the save tells us little until someone with a watch or follow posts a named visitor. Suggest anyone holding a Sentinel or Trailseer result post it now, even a blank one, so we can test claims against each other rather than against silence.


## Response for Case 24

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-07.on", "type": "open_floor_line", "kind": _}
]
```

---

# Case 25

### s025 (key `voices-03.off:5:player_8:1`)

Speaker: player_8, during the day's discussion.

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
[Day 3] Here's the vote result for day 3:
  player_1 voted to abstain
  player_2 voted to abstain
  player_3 voted to abstain
  player_5 voted to eliminate player_3
  player_7 voted to abstain
  player_8 voted to abstain
  player_9 voted to abstain
  player_10 voted to abstain
The town chose to abstain. No one is eliminated today.
[Day 3] Night of day 3: player_10 was killed by the wolves last night. Their role is hidden by an illusionist. The Speculator has picked Town.
[Day 4] Here's the vote result for day 4:
  player_1 voted to eliminate player_5
  player_2 voted to eliminate player_5
  player_3 voted to eliminate player_5
  player_5 voted to eliminate player_3
  player_7 voted to eliminate player_5
  player_8 voted to eliminate player_5
  player_9 voted to eliminate player_3
Player player_5 has been voted out and was a illusionist.
[Day 4] Night of day 4: player_1 was killed by the wolves last night. They were a speculator.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
[Day 4] player_2, player_3, player_8 → player_5 (revealed illusionist, voted out day 4): player_2 argued player_5's day 3 vote was the only elimination vote and had no basis. player_3 asked why player_5 put them up with no reason. player_8 argued the same. Defense: player_5 said its day 3 vote was a read on player_10 with no hard information. Said it is not pushing anyone today and asked abstainers for reasons.
[Day 4] player_2, player_8 → player_7: player_2 argued player_7 abstained every day with no reason given. player_8 argued player_7 abstained three days running and should give at least one reason. Defense: player_7 said it abstained because it had nothing to go on and will not vote on a bare read. Asked player_9 to give its reason too.
[Day 4] player_2, player_8 → player_9: player_2 argued player_9 abstained every day with no reason given. player_8 argued player_9 abstained three days running and should give at least one reason. Defense: player_9 said nobody has put up anything concrete, so it will not vote on a bare read. Asked holders of night roles to state what they would have learned.

Today's discussion so far, as the speaker saw it:
player_7: I'm the Investigator. I checked player_2 on night 1 and player_3 on night 3, and both read Not suspicious, so both are clear. That leaves the surviving wolf as player_8 or player_9, and I'll use my last check on whichever one looks worse.
player_2: player_7, you say you checked me, and I'm town, so that result is fine. But a Chanteuse could claim Investigator too, and the clears would then point the table at 8 and 9. I'd like to hear from the other night roles before anyone votes on the Investigator claim.

THE LINE:
player_7, you say you checked player_2 on night 1 and player_3 on night 3, which is two checks, and then say you'll use your last check now. That's three. Which is it? If you're really the Investigator, explain that before anyone accepts the clears. I'd vote player_7 today on that count.


## Response for Case 25

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-03.of", "type": "open_floor_line", "kind": _}
]
```

---

# Case 29

### s029 (key `voices-07.on:2:player_5:1`)

Speaker: player_5, during the day's discussion.

Earlier days (summary, most recent part):
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_7 was attacked by the serial killer but was saved by the healer!

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
None.

Today's discussion so far, as the speaker saw it:
player_3: Night 1 gave us a save on player_7, so the serial killer is active and can't be struck at night. Nobody has claimed anything yet. I'd like the Investigator, Sentinel or Trailseer to come forward with a check or watch, because one of those results is the only thing that will let us sort the table. Until then I have no vote to cast.

THE LINE:
Night 1 was a save on player_7, so whoever is holding a watch or follow should speak up with what they saw. I'd rather see a Sentinel or Trailseer claim with a named visitor than a vague 'nobody visited me'. Until someone gives a concrete result, I'm not voting on a name.


## Response for Case 29

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-07.on", "type": "open_floor_line", "kind": _}
]
```