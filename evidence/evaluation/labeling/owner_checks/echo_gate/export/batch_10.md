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

# Case 145

### s145 (key `voices-07.off:5:player_2:1`)

Speaker: player_2, during the day's discussion.

Earlier days (summary, most recent part):
ight 1: watched player_5; says no one visited them.
  Night 2: watched player_2; says player_10 visited them (a visit alone does not establish a visitor's role or what they did).
  Night 3: on day 3 said they planned to watch player_10.
player_10: claimed trailseer (day 3). Record: revealed as trailseer when they were voted out on day 4, as claimed.
  Night 1: followed player_1; says they visited no one.
  Night 2: followed player_2; says they visited player_5 (a visit alone does not establish what they did there).
  Night 3: followed player_4; says they visited no one.
player_2: claimed investigator (day 3).
  Night 2: checked player_5, says they read Suspicious. Record: player_5 was revealed as illusionist, as claimed.
player_6: claimed sigilist (day 3).
player_9: claimed healer (day 4). Record: revealed as healer when they died on night 4, as claimed.
  Night 1: protected player_7, says they saved them from an attack. Record: player_7 was attacked and saved by the healer that night.
  Night 2: protected player_7, says there was no attack.
  Night 3: protected player_2, says there was no attack.
player_3: claimed no role.
  Night 1: says they did not act.
  Night 2: says they did not act.
  Night 3: says they did not act.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
[Day 3] player_4 (revealed sentinel, killed night 3) → player_10 (revealed trailseer, voted out day 4): player_4 argued player_10 needs close scrutiny, since player_4's night 2 watch saw player_10 come to player_2. Defense: player_10 said a follow shows only where the target went, so the visit to player_2 fits, and their night 1 follow on player_1 showed no visits. Disputed: player_2 said one of player_4 or player_10 is lying and cannot back up the watch. player_8 asked how the follow claim could be checked.
[Day 4] player_7, player_9 (revealed healer, killed night 4) → player_10 (revealed trailseer, voted out day 4): player_7 argued player_4 was alive and planned a night-3 watch on player_10, so 'visited no one' is doubtful. player_9 argued that claim cannot be checked and player_4 named player_10 on night 2. Defense: player_10 said the night-3 follow showed player_4 visited no one, so the planned watch didn't happen. No wolf was alive to block. The night-2 watch matches their follow of player_2. Disputed: player_3 said the night-2 follow matches player_4's watch and they were not defending player_10 blindly. player_6 said the follow, watch and check line up, so no liar is seen yet.
[Day 4] player_10 (revealed trailseer, voted out day 4) → player_9 (revealed healer, killed night 4): player_10 asked why player_9 protected player_2 on night 3 and what they saw that night, and said they would rather vote on evidence than on the last accuser. Defense: player_9 said they protected player_2 as the only claimed investigator with a check, to keep the info roles alive. No attack was announced, so they learned nothing that night.

Today's discussion so far, as the speaker saw it:
No messages yet.

THE LINE:
Both wolves are dead now, so the only killer left is a non-wolf. Since player_9 protected player_2 on night 3 and no attack was announced, I'd like to hear from player_3 which role they think is still missing from the table. The two checks left are on the investigator and sigilist, so I'll say it plainly: I checked player_5 on night 2 and got Suspicious, which matched their illusionist role.


## Response for Case 145

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-07.of", "type": "open_floor_line", "kind": _}
]
```

---

# Case 146

### s146 (key `voices-08.off:2:player_1:2`)

Speaker: player_1, during the day's discussion.

Earlier days (summary, most recent part):
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_4 was stabbed by the serial killer last night. They were a chanteuse. player_10 was killed by the wolves last night. Their role is hidden by an illusionist.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
None.

Today's discussion so far, as the speaker saw it:
player_3: I'm the healer. Night 1 I meant to protect player_7, but I was roleblocked, so that protection didn't happen. That means the chanteuse, player_4, came to me before they died.
player_7: player_3, if you're the healer, who are you protecting tonight, and does that night's result come back to you? I'm not claiming anything yet, but I'd like to see who else steps up before I use my last check. Everyone else, tell us who you'd vote for and why.
player_3: Yes, I'm the healer. Night 1 my protection on player_7 was blocked, so that's the only thing I've done so far. Tonight I'll protect someone, and a save shows up in the morning report, so you'll see if it worked. player_7, if you're the investigator, I'd hold that last check for a day we actually have a vote to make.

THE LINE:
player_3, you say your night 1 protection on player_7 was blocked. Tonight, name who you protect and I'll be watching for whether a save is announced. If you're the healer, a real save will confirm it fast. Nobody has a vote yet, so I'm not naming a target today.


## Response for Case 146

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-08.of", "type": "open_floor_line", "kind": _}
]
```

---

# Case 151

### s151 (key `voices-07.on:5:player_7:1`)

Speaker: player_7, during the day's discussion.

Earlier days (summary, most recent part):
n night 4, as claimed.
  Night 2: checked player_3, says they read Not suspicious.
  Night 3: checked player_2, says they read Not suspicious.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
[Day 3] player_1 (revealed investigator, killed night 4), player_4, player_6 (revealed sigilist, voted out day 4), player_9 → player_10 (revealed trailseer, voted out day 3): player_1 and player_4 argued player_10 first denied visiting player_3 on night 2, then said they followed player_3. player_6 and player_9 said the changing account justified a lynch vote. Defense: player_10 called the denial a muddle, admitted following player_3 on night 2 (who visited no one), and said to vote on the evidence rather than the slip. Disputed: No one defended player_10. player_4 said the watch showed player_10 at player_3's door, and a follow does not stop at the door.
[Day 3] player_10 (revealed trailseer, voted out day 3), player_4 → player_1 (revealed investigator, killed night 4): player_10 argued an Investigator check means player_1 visited player_3, a visit player_10 cannot see. player_4 said player_1's check claim is unverified. Defense: player_1 said they are the Investigator, checked player_3 on night 2 and got Not suspicious, and asked player_10 whether they denied or followed. Disputed: player_4 said the check claim is unverified and asked to see the next lynch vote before trusting player_1 or player_10.
[Day 3] player_10 (revealed trailseer, voted out day 3) → player_4: player_10 argued a Sentinel watch would not show a follow visit, so player_4's report was either wrong or made up. Defense: player_4 said the watch showed player_10 at player_3's door, refused to argue the names, and asked what player_10 was doing there. Disputed: player_10 later dropped the point, saying player_4 seems to be telling the truth about player_10's name.
[Day 4] player_7 → player_1 (revealed investigator, killed night 4): player_7 argued that player_1's count of two checks already used both, so claiming one check left was inconsistent, and asked for an explanation before the lynch. Defense: player_1 said the night 1 check on player_7 was roleblocked and never happened, so nights 2 and 3 were the two checks. Asked voters to judge the evidence.
[Day 4] player_6 (revealed sigilist, voted out day 4) → player_4: player_6 argued that player_4's night 3 roleblock claim conflicts with the record showing player_4 was attacked and saved that night. Defense: player_4 said both can be true: the attack was stopped by the save, and the separate roleblock stopped the watch on player_2. Said they cannot tell who blocked them.
[Day 4] player_6 (revealed sigilist, voted out day 4) → player_2: player_6 argued that player_2 has only asked questions and has not said what they did on night 3. Defense: player_2 said they are town, will not claim a night-3 action, and that the claims on the table should decide votes. Said asking questions is fine.

Today's discussion so far, as the speaker saw it:
player_4: Night 4 I tried to watch player_2 and was roleblocked too, so that is two nights in a row. The Chanteuse is alive and is blocking me, which narrows the wolf search to player_7, player_8 or player_9.
player_2: player_4 says the Chanteuse blocked them on night 4, but a roleblock report doesn't tell us which of 7, 8 or 9 it was. I'd rather see who made a claim we can check against the wills before we pick a name. I have nothing new to add on the rest.

THE LINE:
I can say from my side that I am not a wolf, so the night-4 roleblock on player_4 came from player_8 or player_9. player_2, you have only said you would rather wait. Did you protect anyone on night 4? If so, who?


## Response for Case 151

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-07.on", "type": "open_floor_line", "kind": _}
]
```

---

# Case 152

### s152 (key `voices-02.off:2:player_10:1`)

Speaker: player_10, during the day's discussion.

Earlier days (summary, most recent part):
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_2 was killed by the wolves last night. They were a sigilist. player_8 was stabbed by the serial killer last night. They were a investigator.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
None.

Today's discussion so far, as the speaker saw it:
player_5: I'm the Trailseer. Night 1 I followed player_4, and they visited player_8, who was stabbed that night, so player_4 is my first suspect.
player_4: I didn't go to player_8 on night 1. My visit that night was to player_9, nothing more. I'm not claiming a role. If player_5 is really the Trailseer, they should say who I visited on night 1 and who visited them, and we can check it against the wills and the deaths.
player_1: player_4 says they went to player_9 on night 1, but player_5's follow puts them at player_8, who was stabbed that night. Both can't be true. Unless player_4 can explain that, I'm voting player_4 today.
player_4: I'm not going to vote on a claim nobody can check. I went to player_9 on night 1 and nobody came to me that I know of. player_5 could be the Trailseer, or a wolf who's read that a follow on me makes a good target. Ask player_5 who they followed on night 2 and who they saw go to whom, so we get something to test.
player_5: player_4, my follow on you night 1 showed you went to player_8 and nowhere else, so player_9 wasn't your visit. You can't both be right about that. Why would you say player_9 when the wolves' victim was player_8? Anyone who wants to check me can ask player_8's stabbing and the morning report.
player_4: I went to player_9 on night 1, and nobody came to me. A follow only shows where I went, so player_5 is reporting a visit I say I didn't make. If player_5 is the Trailseer, they should name who they followed on night 2 and who that player visited, so we have something to test.
player_5: As I said, my follow on player_4 on night 1 showed they went to player_8 and nowhere else. player_8 was the one stabbed, so player_9 wasn't their visit. player_4, why name player_9 when the record points at player_8? I'll follow someone new tonight and post what I see.
player_6: player_4, you say you visited player_9 and nobody came to you, but player_5's follow only shows where you went. Did player_9 say anything about who visited them on night 1? Also player_5, does your follow show player_4 going anywhere besides player_8?
player_4: player_6, player_5's follow is the only thing saying I went to player_8, and I'm not going to confirm a visit I didn't make. I went to player_9 on night 1 and nobody came to me that I know of. player_5, if your night 2 follow shows who I visited, post it now so we can check it against the morning report.
player_5: player_6, my night 1 follow on player_4 showed they went to player_8 and nowhere else, so I can't see a visit to player_9. I didn't get anything on player_9 myself. player_4, you still haven't said who you think came to you, or why you went to player_9.
player_7: For now I'd vote player_4. player_5's follow puts them at player_8, the night 1 stab, and player_4 names player_9 without anyone confirming it. Player_4 should say who visited them that night, if anyone did.
player_4: player_7, I already said it: my night 1 visit was player_9, and nobody came to me that I know of. Player_5's follow is their only claim against me, and I can't confirm a visit I didn't make. If player_5 is the Trailseer, a night 2 follow that names a visit should be checkable in the morning report, so let's see that before anyone votes on it.

THE LINE:
player_5's follow and player_4's 'player_9' visit can't both be right, so the cleanest test is the night 2 results. player_5, if you followed someone last night, post the target and who they visited, and I'd like player_4 to say who they think came to them. Until one of you is checkable, I'm not voting.


## Response for Case 152

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-02.of", "type": "open_floor_line", "kind": _}
]
```

---

# Case 155

### s155 (key `voices-05.off:3:player_3:2`)

Speaker: player_3, during the day's discussion.

Earlier days (summary, most recent part):
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_5 was attacked by the wolves but was saved by the healer!
[Day 2] Here's the vote result for day 2:
  player_1 voted to eliminate player_10
  player_2 voted to eliminate player_10
  player_3 voted to abstain
  player_4 voted to eliminate player_9
  player_5 voted to eliminate player_10
  player_6 voted to eliminate player_9
  player_7 voted to eliminate player_10
  player_8 voted to eliminate player_9
  player_9 voted to eliminate player_10
  player_10 voted to eliminate player_4
Player player_10 has been voted out and was a investigator.
The record of player_10, the investigator: night 1, checked player_5: Not suspicious.
[Day 2] Night of day 2: player_9 was attacked by the wolves but was saved by the healer!

-- Claims made in the day discussion (claims, not facts; a note starting "Record:" or "Rules:" is an exact check by the game master; a plan said in the day binds no one: a player may choose a different target at night) --
player_9: claimed trailseer (day 2).
  Night 1: followed player_10; says they visited player_5 (a visit alone does not establish what they did there).
player_10: claimed investigator (day 2). Record: revealed as investigator when they were voted out on day 2, as claimed.
  Night 1: checked player_5, says they read Not suspicious.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
[Day 2] player_3, player_4 → player_9: player_3 argued the two overlapping night 1 visit claims cannot both be the whole story. player_4 argued one of player_9 and player_10 is probably not telling the whole truth. Defense: player_9 said the follow showed player_10 went to player_5 and nowhere else. A single check fits that, and the result does not show the visit's kind. Disputed: player_1 said the claim fits the night 1 visit and save. player_10 said both claims can be true, as a check and a follow both reach player_5.
[Day 2] player_2, player_3, player_4 → player_10 (revealed investigator, voted out day 2): player_2 asked what player_10 did on night 1 when visiting the attacked player_5. player_3 and player_4 argued player_10's check and player_9's follow conflict over that visit. Defense: player_10 said they are the investigator, checked player_5 on night 1 and got Not suspicious, and both claims can be true. More would reveal their role. Disputed: No one defended player_10 directly. player_1 asked whether they were the healer, and player_9 said their follow does not reveal the visit's purpose.

Today's discussion so far, as the speaker saw it:
player_8: I'm the sentinel. I watched player_9 on night 2 and saw visits from player_1, player_4, player_7 and player_10; player_10 was already dead, so that visit came from the Necromancer using the investigator's body.
player_1: Sentinel claim from player_8 is worth testing. If they watched player_9 and saw four visitors, the Necromancer is the only one who could have gone to player_10's body. I'd like player_8 to say who they watched on night 1 and what came of it, so we can check the claims against each other.
player_8: Night 1 I kept my watches, so there's nothing to compare there. Night 2 I watched player_9 and saw player_1, player_4, player_7 and player_10 come to them. Since player_10 was already dead, that last visit is the Necromancer using the investigator's body. player_1, you're on that list, so tell me what you went to player_9 for.
player_2: player_8, your night 2 watch on player_9 lists four visitors, but the record says the healer protected player_9 that night, and a protection visit would show on a watch. So either the Healer is one of player_1, player_4, player_7, or the list is incomplete. Which one is it?
player_8: player_2, the list is complete: four visitors, and I saw all of them. The healer's protection is one of player_1, player_4 or player_7, and so is the wolf's attack. I won't say which yet, since I want to keep my last watch useful. Test the list against what the three of them say they did.
player_9: I'm the trailseer, and I'll put my night 2 follow on the table: I followed player_4, and they went to me. Player_8's list has player_4 on it, so that part checks out. Whoever else was on that list can be tested against the saved attack, so I'd rather hear player_1 and player_7 say what they did before I vote.

THE LINE:
player_8, your list has player_4 visiting player_9, and player_9's follow also has player_4 going to them. That lines up, so the open question is who the healer is among player_1 and player_7. player_1, you were asked what you went to player_9 for. Answer that directly, and I'd like player_7 to do the same.


## Response for Case 155

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-05.of", "type": "open_floor_line", "kind": _}
]
```