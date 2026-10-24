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

# Case 101

### s101 (key `voices-04.off:3:player_7:2`)

Speaker: player_7, during the day's discussion.

Earlier days (summary, most recent part):
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_1 was killed by the wolves last night. Their role is hidden by an illusionist. player_10 was stabbed by the serial killer last night. They were a chanteuse.
[Day 2] Here's the vote result for day 2:
  player_2 voted to abstain
  player_3 voted to abstain
  player_4 voted to abstain
  player_5 voted to abstain
  player_6 voted to abstain
  player_7 voted to abstain
  player_8 voted to abstain
  player_9 voted to abstain
The town chose to abstain. No one is eliminated today.
[Day 2] Night of day 2: player_5 was attacked by the serial killer but was saved by the healer!

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
None.

Today's discussion so far, as the speaker saw it:
player_5: I'm the Investigator. Night 1 I checked player_1 and Night 2 I checked player_3, and both read Not suspicious, so neither is a wolf. The Illusionist is still alive among the rest of us, so I want to hear who is claiming what before we vote.
player_9: player_5, you're claiming Investigator. Who else is claiming anything? I'd like to hear from the rest before we pick a lynch, since the only solid facts so far are the two deaths and the save on player_5. Let's get claims from everyone first.
player_5: player_9, I answered already: I checked player_1 on night 1 and player_3 on night 2, both Not suspicious. I'm not asking for a lynch yet. Anyone who claims Investigator now is lying, since I'm the only one. Who has a night result they're willing to share?

THE LINE:
player_5's checks fit the record so far: player_1 was a wolf victim, not a wolf, and player_3 read clean. Before any lynch, I want the Investigator claim tested. Whoever is the Illusionist or Serial Killer can't be told apart yet, so I'd abstain today unless someone gives a concrete night result that conflicts with the record.


## Response for Case 101

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-04.of", "type": "open_floor_line", "kind": _}
]
```

---

# Case 102

### s102 (key `voices-02.off:3:player_3:1`)

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

THE LINE:
player_5, if you were roleblocked last night, then your night 1 follow on player_4 is the only real data we have, and it conflicts with player_4's player_9 claim. Tonight's follow on player_9 is useful, but only if you post what it shows. Whoever the Chanteuse blocks is worth noting too, since a block shows as no visit.


## Response for Case 102

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-02.of", "type": "open_floor_line", "kind": _}
]
```

---

# Case 105

### s105 (key `voices-08.on:2:player_6:1`)

Speaker: player_6, during the day's discussion.

Earlier days (summary, most recent part):
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_4 was stabbed by the serial killer last night. They were a chanteuse. player_10 was killed by the wolves last night. Their role is hidden by an illusionist.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
None.

Today's discussion so far, as the speaker saw it:
No messages yet.

THE LINE:
Good morrow, all. Sadly we have no vote today and little to go on yet. I would like whoever holds a night result to share it plainly, so we can compare claims. I will keep my own counsel until I hear more.


## Response for Case 105

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-08.on", "type": "open_floor_line", "kind": _}
]
```

---

# Case 106

### s106 (key `voices-02.on:4:player_1:1`)

Speaker: player_1, during the day's discussion.

Earlier days (summary, most recent part):
 night. Their role is hidden by an illusionist.

-- Claims made in the day discussion (claims, not facts; a note starting "Record:" or "Rules:" is an exact check by the game master; a plan said in the day binds no one: a player may choose a different target at night) --
player_5: claimed trailseer (day 2).
  Night 1: followed player_4; says they visited player_8 (a visit alone does not establish what they did there).
  Night 2: followed player_6; says they visited no one.
player_4: claimed no role.
  Night 1: says they did not act.
player_6: claimed no role.
  Night 1: says they did not act.
  Night 2: says they did not act.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
[Day 2] player_5, player_6, player_9 (revealed chanteuse, voted out day 3) → player_4 (revealed serial killer, voted out day 2): player_5 said the night 1 follow shows player_4 visited player_8, a kill, making them the top serial killer suspect. player_6 and player_9 said one of them is lying and favoured a vote. Defense: player_4 said they visited nobody on night 1, called player_5's trail one unverified claim, and asked for a second source before any vote. Disputed: player_1 and player_10 asked whether player_5 followed anyone else and wanted the trail and claim checked before voting.
[Day 3] player_9 (revealed chanteuse, voted out day 3) → player_3: player_9 argued that player_3's view that the wolves going after player_5 made the claim genuine was a leap, since a healer save fits a fake trail as well. Defense: player_3 said they called the attack only a point, not proof, agreed a save fits a true or false trail alike, and would not vote on the attack alone.
[Day 3] player_9 (revealed chanteuse, voted out day 3) → player_5: player_9 said player_5's test idea felt insincere, that a healer save is as consistent with a fake trail, and asked for player_5's night 3 follow to be tested before any vote. Defense: player_5 said night 3 has not happened yet, will follow a living player tonight and post the result tomorrow, and that the night 2 follow on player_6 stands. Disputed: player_7 said player_5's night 1 trail fits the record. player_3 said the save is consistent with a true trail and wanted a night 3 test before any vote.
[Day 3] player_7 → player_1: player_7 said whoever pushed for a second source against player_5's trail should be looked at hard, after arguing player_5's night 1 trail fits the facts. Defense: player_1 said a fair test is a new follow on a living player, that they are not voting on the night 1 trail alone, and that they are not claiming anything.
[Day 3] player_7 → player_10: player_7 said whoever pushed for a second source against player_5's trail should be looked at hard, after arguing player_5's night 1 trail fits the facts. Defense: player_10 said they want player_6's held fire and player_5's night 2 follow compared with the announced healer save, and will wait for the next trail before deciding.

Today's discussion so far, as the speaker saw it:
player_5: Night 3 I followed player_3, and they visited no one, so player_3 did not go to anyone that night. I'm still open to a fresh follow on a living player tonight if the town wants another check.
player_7: I am the healer. I protected player_5 on night 2, when the wolves attacked them and it was stopped, and again on night 3 with no attack, so the save is a fact and not just a claim.

THE LINE:
player_5's night 1 trail says player_4 went to player_8, and player_8 was stabbed by the serial killer that night. That fits, and player_4 denied it. Player_6 pushed the second-source demand against that trail on day 2 and still has no role claim. If we vote today, I'd put it on player_6 until they say what they did on nights 1 and 2.


## Response for Case 106

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-02.on", "type": "open_floor_line", "kind": _}
]
```

---

# Case 111

### s111 (key `voices-07.on:5:player_9:1`)

Speaker: player_9, during the day's discussion.

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
player_7: I can say from my side that I am not a wolf, so the night-4 roleblock on player_4 came from player_8 or player_9. player_2, you have only said you would rather wait. Did you protect anyone on night 4? If so, who?
player_2: player_7, I said I'm town and I won't put a night action on the table, so no, I'm not going to say who I protected or didn't. Asking me that is fine, but it doesn't tell us anything about the wolves. What's your read on player_4's sentinel claim? Their watch matches the wills, so it's the one thing we can test.

THE LINE:
player_2, you keep saying you're town but won't answer anything, and that's the one thing this table can't work with. Asking a direct question isn't a wolf tell, so give us something to check. I'm not voting anyone on what we have yet, but I'd like to hear from player_8 before the lynch.


## Response for Case 111

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-07.on", "type": "open_floor_line", "kind": _}
]
```