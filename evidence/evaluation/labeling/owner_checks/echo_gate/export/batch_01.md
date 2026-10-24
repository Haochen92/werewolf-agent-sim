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

# Case 8

### s008 (key `voices-01.on:2:player_1:1`)

Speaker: player_1, during the day's discussion.

Earlier days (summary, most recent part):
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_3 was stabbed by the serial killer last night. They were a illusionist. player_9 was killed by the wolves last night. Their role is hidden by an illusionist.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
None.

Today's discussion so far, as the speaker saw it:
No messages yet.

THE LINE:
Two dead on night one, one of them a wolf per the record, so the wolves are down a man. player_9's role is hidden, so there's no will to lean on. I'd rather hear people state what they'd do with a check or a watch before anyone starts pointing fingers. Who wants to go first with a claim?


## Response for Case 8

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-01.on", "type": "open_floor_line", "kind": _}
]
```

---

# Case 12

### s012 (key `voices-05.on:4:player_1:1`)

Speaker: player_1, during the day's discussion.

Earlier days (summary, most recent part):
heir role is hidden by an illusionist. player_7 was shot by the vigilante last night. They were a chanteuse.

-- Claims made in the day discussion (claims, not facts; a note starting "Record:" or "Rules:" is an exact check by the game master; a plan said in the day binds no one: a player may choose a different target at night) --
player_9: claimed trailseer (day 2).
  Night 1: followed player_10; says they visited player_5 (a visit alone does not establish what they did there).
  Night 2: says they tried to follow player_3 and were roleblocked.
player_10: claimed investigator (day 2). Record: revealed as investigator when they were voted out on day 3, as claimed.
  Night 1: checked player_5, says they read Not suspicious.
  Night 2: checked player_4, says they read Not suspicious.
player_4: claimed healer (day 3).
  Night 1: protected player_5, says they saved them from an attack. Record: player_5 was attacked and saved by the healer that night.
  Night 2: protected player_9, says there was no attack.
player_5: claimed sigilist (day 3).
player_8: claimed sentinel (day 3).
  Night 2: watched player_10; says no one visited them.
player_2: claimed vigilante (day 3). Record: revealed as vigilante when they died on night 3, as claimed.
  Night 1: says they did not act.
  Night 2: says they did not act.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
[Day 2] player_3, player_5 → player_10 (revealed investigator, voted out day 3): player_3 argued player_9's follow and player_10's check cannot both be fully right if player_10 is a wolf. player_5 argued a wolf carrier's visit would look the same as a check and asked for the result. Defense: player_10 said their night 1 action was an investigation of player_5, which returned Not suspicious. They said the follow fits that and would also fit a wolf visit, so they would not claim more. Disputed: player_9 argued that a check is a visit, so player_9's follow of player_10 to player_5 and player_10's check fit together.
[Day 3] player_2 (revealed vigilante, killed night 3), player_5, player_8, player_9 → player_10 (revealed investigator, voted out day 3): player_2 argued player_9's sighting of player_10 going to player_5 on night 1 fits a wolf visit. player_5 and player_8 wanted player_10 voted. player_9 questioned player_10's check count. Defense: player_10 said their checks on player_5 (night 1) and player_4 (night 2) read Not suspicious. They corrected their check count to zero and said a wolf visit would be hidden from them.
[Day 3] player_7 (revealed chanteuse, killed night 3) → player_2 (revealed vigilante, killed night 3): player_7 argued player_2 only raised the player_9 sighting and pushed the player_10 vote, and asked whether player_2 holds a role or is only reading the board. Defense: player_2 claimed to be the vigilante, said they held fire on nights 1 and 2 with two bullets left, and asked player_4 and player_8 to name their night 2 results.

Today's discussion so far, as the speaker saw it:
player_5: Sharing my night: I'm the sigilist, and my sigil on player_2 struck them down last night, so player_2 did attack, which fits their vigilante claim and the shot on player_7, the chanteuse.

THE LINE:
Sigil on player_2 is a neat check on the vigilante claim. Two bodies have now had hidden roles, so I'd like the sentinel and trailseer to tell us exactly who they saw at their doors on night 3. Player_6 has been quiet, and with player_7 gone, the Necromancer could be sitting there.


## Response for Case 12

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-05.on", "type": "open_floor_line", "kind": _}
]
```

---

# Case 13

### s013 (key `voices-03.off:4:player_8:1`)

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

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
None.

Today's discussion so far, as the speaker saw it:
player_1: Three days of abstaining and nobody has a claim. Player_5 is the only one who has put a name on the table, against player_3. I'd rather we actually vote today than abstain again. player_3, what do you make of player_5's vote?
player_3: player_1, I'm fine with a vote today. player_5, you put me up on day 3 with no reason given. Why me, and what made you pick me over anyone else? Give us something concrete before we vote.
player_5: player_3, fair question. My vote on player_10 was just my read from day 3 with no hard info behind it, and I won't pretend otherwise. I haven't seen anything on you that would make me push you today. If you want a vote, I'd rather it go to someone with a real contradiction, so what did you do on the nights that might help us test people?
player_2: player_5, you have now said your day 3 vote had no information behind it, and it was the only elimination vote on the record. Before anyone else gets pushed, name the role you think player_3 could be. Players 7, 8 and 9 have also abstained every day with no reason given. If we are voting today, I would like a reason from each of you.
player_5: player_2, fair ask. I voted player_10 on day 3 from a read only, not from hard info, and I have nothing to back it up. I don't want to push anyone today without something concrete. Players 7, 8 and 9, if you're going to abstain again, give a reason.

THE LINE:
player_5, your day 3 vote is the only lynch on the record and you admit it had no basis, so I'd like a real reason from you before anyone is voted today. Players 7 and 9 have abstained three days running, so give us one reason, even a thin one. I won't vote on feelings alone.


## Response for Case 13

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-03.of", "type": "open_floor_line", "kind": _}
]
```

---

# Case 14

### s014 (key `voices-06.off:4:player_8:1`)

Speaker: player_8, during the day's discussion.

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

THE LINE:
player_7's night 2 watch saw player_4 come to player_1, which is the Chanteuse's block player_1 described. That backs player_1's block story. player_7, did you see anyone else visit player_1 that night? It tells us whether the block was the only visit.


## Response for Case 14

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-06.of", "type": "open_floor_line", "kind": _}
]
```

---

# Case 15

### s015 (key `voices-07.on:3:player_8:2`)

Speaker: player_8, during the day's discussion.

Earlier days (summary, most recent part):
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_7 was attacked by the serial killer but was saved by the healer!
[Day 2] Here's the vote result for day 2:
  player_1 voted to abstain
  player_2 voted to eliminate player_3
  player_3 voted to abstain
  player_4 voted to abstain
  player_5 voted to eliminate player_2
  player_6 voted to abstain
  player_7 voted to abstain
  player_8 voted to eliminate player_3
  player_9 voted to abstain
  player_10 voted to abstain
The town chose to abstain. No one is eliminated today.
[Day 2] Night of day 2: player_3 was killed by the wolves last night. Their role is hidden by an illusionist. player_5 was stabbed by the serial killer last night. They were a illusionist.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
None.

Today's discussion so far, as the speaker saw it:
player_4: Right then, I'm the Sentinel. Last night I watched player_3 and saw player_1, player_5 and player_10 come to them.
player_1: player_4's report checks out on my end: I did go to player_3 on night 2. That makes player_10's visit to player_3 the interesting part. It was seen, so it wasn't the carrier's kill. player_10, what were you doing there?
player_10: player_1, I did not visit player_3 on night 2. Whatever player_4's report says about my name, I was not at player_3's door that night. Player_4, if you saw me come to player_3, can you say how that matches what the record shows about player_5's visit?
player_4: player_10, my watch on player_3 is what it is: you came to them that night, along with player_1 and player_5. I'm not going to argue the names. Player_5 was the illusionist, so their visit is the conceal, and that's why the kill itself didn't show. So what were you visiting player_3 for, if not the kill?
player_10: player_4, I did not go to player_3 on night 2. I followed player_3 that night and they visited no one, and I went nowhere near their door. A Sentinel watch on player_3 wouldn't show me coming there, so either your report is wrong or it's made up. player_1, you say you went to player_3; what was your reason?
player_1: player_10, I went to player_3 on night 2 because I'm the Investigator and I checked them. They came back Not suspicious, so player_3 is not a wolf. That's the reason I was there. If you only followed player_3, you wouldn't be at their door, so explain what brought player_4's watch to show you visiting them.
player_10: player_1, I didn't go to player_3's door, I followed them and they visited no one. That's the true bit: a follow shows where the follower went, and I went to player_3, which is exactly why player_4's watch caught me. So player_4 seems to be telling the truth on my name. Your Investigator claim is the one that doesn't fit, since a check means you visited player_3 too, and that's a visit I can't see from here.
player_1: Yes, I'm the Investigator. I checked player_3 on night 2: Not suspicious, so they're not a wolf. player_10, following someone is a visit to them, so 'I did not visit player_3' and 'I followed player_3' can't both be true. Which is it?
player_4: player_10, you can't have it both ways. My watch showed you at player_3's door, and a follow doesn't stop at the door, so 'I followed them and they visited no one' still means you went to them. Did you check player_3 or follow them? Pick one. Player_1, your check claim is also unverified, so I'd like to see the vote on the next lynch before I trust either of you.
player_10: player_4, you're right, and I was wrong to deny it. I followed player_3 on night 2, and a follow is a visit, so your watch caught me. They visited no one that night. That means your report checks out on my name, and player_1's check on player_3 fits too. Let's see who gets the next lynch.
player_9: player_10, you first denied going to player_3, then said you followed them. Both can't be the whole truth, and you only changed once pressed. I'd lean toward you for the next lynch unless you give a cleaner account of why you were at player_3's door.
player_10: player_9, fair to press me. I first said I didn't go to player_3, which was a muddle on my part. What I did was follow player_3 on night 2, and they visited no one. That's why player_4's watch caught me. I'd rather see who people vote for than lean on this, so I'm not pushing anyone yet.
player_6: player_10, your account has moved twice: first no visit, then a follow that you say ended in a visit to player_3. A Trailseer following player_3 would be seen there, so the follow story is possible, but you need to say which role you hold if that is what you did. Until then I'd vote player_10 with a stated reason: the changing account.
player_10: player_6, fair question. I'm the Trailseer. Night 1 I followed player_1 and they visited no one. Night 2 I followed player_3, and they visited no one too. That's why my night 2 visit showed up on player_4's watch. Check those against the claims and we'll see who's lying.

THE LINE:
player_10's account has moved twice now, and player_4's watch lines up with the follow story. I'd like player_4 and player_1 to say whether they trust player_10's Trailseer claim before we pick a lynch. Looking at the record, the vote should go to whoever has the least consistent account.


## Response for Case 15

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-07.on", "type": "open_floor_line", "kind": _}
]
```