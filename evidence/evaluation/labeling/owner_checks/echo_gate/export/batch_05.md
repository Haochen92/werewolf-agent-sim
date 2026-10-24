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

# Case 70

### s070 (key `voices-03.on:4:player_4:1`)

Speaker: player_4, during the day's discussion.

Earlier days (summary, most recent part):
stain
  player_2 voted to abstain
  player_3 voted to abstain
  player_4 voted to abstain
  player_5 voted to abstain
  player_7 voted to abstain
  player_8 voted to abstain
  player_9 voted to eliminate player_4
  player_10 voted to eliminate player_1
The town chose to abstain. No one is eliminated today.
[Day 2] Night of day 2: player_3 was killed by the wolves last night. They were a sentinel. The record of player_3, the sentinel: night 1, watched player_10; saw no one.
[Day 3] Here's the vote result for day 3:
  player_1 voted to abstain
  player_2 voted to eliminate player_9
  player_4 voted to eliminate player_9
  player_5 voted to abstain
  player_7 voted to eliminate player_4
  player_8 voted to eliminate player_4
  player_9 voted to eliminate player_4
  player_10 voted to eliminate player_9
It's a tie between ['player_9', 'player_4']. No one is voted out this day.
[Day 3] Night of day 3: player_10 was killed by the wolves last night. Their role is hidden by an illusionist. The Speculator has picked Town.

-- Claims made in the day discussion (claims, not facts; a note starting "Record:" or "Rules:" is an exact check by the game master; a plan said in the day binds no one: a player may choose a different target at night) --
player_8: claimed no role.
  Night 2: says they did not act.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
[Day 3] player_7, player_2 → player_9: player_7 argued player_9's day-2 lynch push on player_4 had no real basis and said they vote for player_9. player_2 asked player_9 to explain that push before a vote. Defense: player_9 said player_4 had barely spoken on day 1, called it a thin read, and said they would hear player_4 out before voting again. Disputed: player_10 asked player_7 whether the vote on player_9 rests on anything beyond the same thin day-2 push.
[Day 3] player_2 → player_10: player_2 argued player_10 pushed a single day-2 lynch and asked them to explain why before a vote. Defense: player_10 said they did not push anyone on day 2 and abstained, and that the sentinel's watch on them showed no visitors on night 1. (Game record shows player_10 voted to eliminate player_1 on day 2.)
[Day 3] player_10, player_9 → player_7: player_10 asked player_7 whether the vote on player_9 rests on more than the day-2 lynch. player_9 asked the same question about player_7's vote.
[Day 3] player_1 → player_8: player_1 asked player_8 to say whether they are the vigilante and to name the night they would shoot and why they are holding fire. Defense: player_8 said they held fire on nights 1 and 2, are not claiming yet, and need a real contradiction between two claims before shooting.
[Day 3] player_1 → player_4: player_1 argued player_4 has been targeted twice without saying anything and should answer directly. Defense: player_4 said they will not claim a role on a thin read, would not name a night they would shoot, and want someone to make a concrete claim first.

Today's discussion so far, as the speaker saw it:
player_7: I'm the investigator. On night 3 I checked player_9 and got Suspicious, so player_9 is a wolf; please vote them out today.
player_9: I'm not a wolf, so that check on me came back wrong somewhere. Two checks is a lot to sit on for three nights, so why wait until day 4 to call it out? If you're the investigator, say who you checked on nights 1 and 2 and what they came back as.
player_7: player_9, I am the investigator. Night 1 I checked player_2 and got Not suspicious. Night 2 I was roleblocked, so no check. Night 3 I checked you and got Suspicious. Vote player_9 today.
player_9: player_7, I'm the healer, and I'd rather say it now than sit on it. I protected player_8 on night 2 and player_2 on night 3, and nothing was attacked either time. If you checked me Suspicious, one of us is lying, and the healer is Town. Why would an investigator check someone on day 4 and not earlier?
player_7: player_9, I checked you on night 3 and you read Suspicious. I didn't wait to call it out; night 2 I was blocked, and I'd rather have a Suspicious read than a guess. Your healer claim doesn't hold: a save on player_2 on night 3 couldn't have stopped the kill on player_10, and the wolves' only roles that fit your claim are the Chanteuse or the Illusionist. Vote player_9 today.
player_2: I'm player_2 and I wasn't attacked on night 3, so I can't confirm or rule out player_9's save. Only one of the two claims can be true. player_7's check is the only hard result on the table, and a Suspicious read on a real healer would be strange. I'd vote player_9 today unless someone shows a reason not to.
player_9: player_2, player_7's check is one result, and I'm the healer: I protected player_8 on night 2 and player_2 on night 3, and nothing was attacked either time. A save on player_2 doesn't stop the kill on player_10, so that's not a contradiction. If player_7 is the investigator, a Suspicious read on a real healer is the mistake to look at, so I'd like player_7 to say why they checked me on night 3 and not earlier.

THE LINE:
Oh, I hate that player_9 is still standing there so calmly! Their healer claim can't be right, since a save on player_2 couldn't have touched the kill on player_10. player_7's Suspicious read on them fits that, so I lean toward voting player_9 today. player_8, you said you held fire nights 1 and 2. Did you hold fire on night 3 too?


## Response for Case 70

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-03.on", "type": "open_floor_line", "kind": _}
]
```

---

# Case 72

### s072 (key `voices-02.off:4:player_10:2`)

Speaker: player_10, during the day's discussion.

Earlier days (summary, most recent part):
- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_2 was killed by the wolves last night. They were a sigilist. player_8 was stabbed by the serial killer last night. They were a investigator.
[Day 2] Here's the vote result for day 2:
  player_1 voted to eliminate player_4
  player_3 voted to eliminate player_4
  player_4 voted to eliminate player_5
  player_5 voted to eliminate player_4
  player_6 voted to eliminate player_4
  player_7 voted to eliminate player_4
  player_9 voted to eliminate player_4
  player_10 voted to eliminate player_4
Player player_4 has been voted out and was a serial killer.
[Day 2] Night of day 2: player_5 was attacked by the wolves but was saved by the healer!
[Day 3] Here's the vote result for day 3:
  player_1 voted to eliminate player_7
  player_3 voted to abstain
  player_5 voted to eliminate player_9
  player_6 voted to eliminate player_9
  player_7 voted to eliminate player_6
  player_9 voted to eliminate player_5
  player_10 voted to eliminate player_5
It's a tie between ['player_9', 'player_5']. No one is voted out this day.
[Day 3] Night of day 3: player_6 was killed by the wolves last night. Their role is hidden by an illusionist.

-- Claims made in the day discussion (claims, not facts; a note starting "Record:" or "Rules:" is an exact check by the game master; a plan said in the day binds no one: a player may choose a different target at night) --
player_5: claimed trailseer (day 2).
  Night 1: followed player_4; says they visited player_8 (a visit alone does not establish what they did there).
  Night 2: says they tried to follow player_9 and were roleblocked.
  Night 3: on day 3 said they planned to follow player_9.
player_4: claimed no role.
  Night 1: went to player_9.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
[Day 2] player_1, player_5, player_7 → player_4 (revealed serial killer, voted out day 2): player_5 argued a night 1 follow showed player_4 went to player_8, the stabbed player; player_1 said that contradicts player_4's player_9 visit; player_7 would vote player_4. Defense: player_4 said they visited player_9 on night 1 and nobody came to them, denied going to player_8, and refused to confirm a visit they did not make. Disputed: player_6 asked whether player_9 said who visited them and whether the follow shows other destinations; player_10 said they would not vote until one claim was checkable.
[Day 2] player_4 (revealed serial killer, voted out day 2) → player_5: player_4 argued player_5 may not be the Trailseer, or may be a wolf who targeted player_4 with a follow claim, since player_4 says their visit was to player_9. Defense: player_5 repeated that the night 1 follow showed player_4 visited only player_8, and suggested player_4 could be a wolf-side Chanteuse whose block shows as no visit.

Today's discussion so far, as the speaker saw it:
player_5: Night 3 I was roleblocked again trying to follow player_9, so that's two blocks on the same target. Someone wanted player_9 kept out of my follow, so watch who benefits from that.
player_7: Night 3 nobody attacked player_5, and the wolves went for player_6 instead, which fits player_5 being a real trailseer the pack doesn't want to hit. Whoever blocked player_5 twice is a wolf, and the blocker is likely someone who doesn't want player_9 followed. I'd vote player_9 for now unless someone can show why the blocks don't point there.
player_9: player_7, a roleblock only tells us someone was blocked, not who did it. Blocks on player_5 point at whoever is blocking, and I'm not going to explain my night. Voting me on that is a leap. If you want a real read, ask player_5 for a concrete follow result and see if the numbers line up with the blocks.
player_5: Plainly: night 1 I followed player_4 and they went to player_8. Nights 2 and 3 my follow on player_9 was roleblocked, so a wolf Chanteuse is hitting me. player_9, you say a block only shows someone blocked, but you are the one who wanted player_9 kept out of the follow. Vote player_9 for now unless you give a real reason.
player_9: player_5, you're asking me to be the answer to your block, but a roleblock only says someone was blocked, not who did it. I won't say where I went at night. If your follow is real, pick the next target you follow and post exactly where they went, then we can check whether the blocks line up with anyone.

THE LINE:
player_7, your block argument points at player_9 only if the blocker is a wolf who wants the follow stopped. Player_5 has a follow on player_9 blocked twice, so a concrete test: player_5, post your night 1 follow result and name the next target you follow, so we can see whether the blocks match anyone's stated night.


## Response for Case 72

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-02.of", "type": "open_floor_line", "kind": _}
]
```

---

# Case 77

### s077 (key `voices-04.off:2:player_3:1`)

Speaker: player_3, during the day's discussion.

Earlier days (summary, most recent part):
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_1 was killed by the wolves last night. Their role is hidden by an illusionist. player_10 was stabbed by the serial killer last night. They were a chanteuse.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
None.

Today's discussion so far, as the speaker saw it:
No messages yet.

THE LINE:
Night 1 hit player_1 and the serial killer took player_10, so the wolves are down to the illusionist. Nobody has said anything about what they did at night yet. I'd like the Sentinel and Trailseer to come forward if they have results, since a single watch on the right person could cut the field fast.


## Response for Case 77

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-04.of", "type": "open_floor_line", "kind": _}
]
```

---

# Case 78

### s078 (key `voices-06.off:2:player_7:1`)

Speaker: player_7, during the day's discussion.

Earlier days (summary, most recent part):
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_3 was killed by the wolves last night. They were a vigilante.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
None.

Today's discussion so far, as the speaker saw it:
player_1: I'm the trailseer. On night 1 I followed player_8, and they visited no one, so there's no visit to read from that. I'll follow someone else tonight and report what I see.

THE LINE:
Nothing is settled yet, so I'd like to hear from the claimed trailseer first. player_1, if your follow on player_8 gives you anything tonight, say who player_8 went to, and we can check that against the night-two kill. I'm not ready to vote on anyone without more to go on.


## Response for Case 78

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-06.of", "type": "open_floor_line", "kind": _}
]
```

---

# Case 86

### s086 (key `voices-02.off:3:player_3:2`)

Speaker: player_3, during the day's discussion.

Earlier days (summary, most recent part):
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_2 was killed by the wolves last night. They were a sigilist. player_8 was stabbed by the serial killer last night. They were a investigator.
[Day 2] Here's the vote result for day 2:
  player_1 voted to eliminate player_4
  player_3 voted to eliminate player_4
  player_4 voted to eliminate player_5
  player_5 voted to eliminate player_4
  player_6 voted to eliminate player_4
  player_7 voted to eliminate player_4
  player_9 voted to eliminate player_4
  player_10 voted to eliminate player_4
Player player_4 has been voted out and was a serial killer.
[Day 2] Night of day 2: player_5 was attacked by the wolves but was saved by the healer!

-- Claims made in the day discussion (claims, not facts; a note starting "Record:" or "Rules:" is an exact check by the game master; a plan said in the day binds no one: a player may choose a different target at night) --
player_5: claimed trailseer (day 2).
  Night 1: followed player_4; says they visited player_8 (a visit alone does not establish what they did there).
player_4: claimed no role.
  Night 1: went to player_9.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
[Day 2] player_1, player_5, player_7 → player_4 (revealed serial killer, voted out day 2): player_5 argued a night 1 follow showed player_4 went to player_8, the stabbed player; player_1 said that contradicts player_4's player_9 visit; player_7 would vote player_4. Defense: player_4 said they visited player_9 on night 1 and nobody came to them, denied going to player_8, and refused to confirm a visit they did not make. Disputed: player_6 asked whether player_9 said who visited them and whether the follow shows other destinations; player_10 said they would not vote until one claim was checkable.
[Day 2] player_4 (revealed serial killer, voted out day 2) → player_5: player_4 argued player_5 may not be the Trailseer, or may be a wolf who targeted player_4 with a follow claim, since player_4 says their visit was to player_9. Defense: player_5 repeated that the night 1 follow showed player_4 visited only player_8, and suggested player_4 could be a wolf-side Chanteuse whose block shows as no visit.

Today's discussion so far, as the speaker saw it:
player_5: Trailseer here, still the only one claiming it. Last night I was roleblocked, so my follow on player_9 didn't happen. Tonight I'm following player_9 again, and I'll post what I see if it's checkable.
player_6: player_5, if your follow on player_9 tonight shows anyone visiting player_9 that is checkable, post it. Also, player_9 can you say who, if anyone, came to you on night 1? That would confirm or break player_4's claim of visiting you, and it tells us whether player_4 was lying.
player_5: player_6, my night 2 follow on player_9 was blocked, so I have nothing on them from last night. Tonight's follow hasn't happened yet, so I can only post it after the night. If it shows a visit to player_9, I'll say who. Player_9, your answer on who came to you on night 1 would help.
player_9: player_6, I can't say anyone came to me on night 1. I didn't see a watch or anything like that, so I have nothing to check player_4's claim against. What I do see: player_5's night 1 follow put player_4 at player_8, and player_8 was the one stabbed, which fits player_4 being the killer. That makes player_4's visit to player_9 the odd part.
player_7: player_5, you were roleblocked on night 2, so the claim that your follow on player_9 was blocked fits. Your night 1 follow on player_4 is the only checkable piece so far. I'd like to see tonight's follow result before deciding on a lynch. I'm not voting yet.
player_5: player_7, fair ask. Tonight I follow player_9 and I'll post the result in the morning if it shows a visit. Night 1 is the only checkable piece so far, and I'd rather not give a lynch vote before I have that. A block on me on night 2 fits a wolf targeting the Trailseer.
player_10: player_5, you were roleblocked on night 2, so your night 2 follow didn't happen. Tonight's follow on player_9 will be the first real test. Can you say the result plainly in the morning, including if it shows no visitors? Then we can see whether it fits what player_9 says about night 1.
player_5: player_10, yes, I'll post tonight's follow result plainly in the morning, including if no one visited player_9. Night 2 was the block, so I have nothing from that night. Tonight's follow is the first real check.

THE LINE:
Worth noting for the morning: player_5 says the follow on player_9 is tonight's test. If it shows nobody visiting player_9, that tells us little on its own, since a wolf-side block or a hidden kill would look the same. I'd rather see the follow on player_9 and whether player_9 or anyone else was reported as blocked before deciding.


## Response for Case 86

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-02.of", "type": "open_floor_line", "kind": _}
]
```