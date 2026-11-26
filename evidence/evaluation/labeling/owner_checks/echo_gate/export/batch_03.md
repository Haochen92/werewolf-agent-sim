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

# Case 30

### s030 (key `voices-03.on:5:player_4:1`)

Speaker: player_4, during the day's discussion.

Earlier days (summary, most recent part):
yer_4 had barely spoken on day 1, called it a thin read, and said they would hear player_4 out before voting again. Disputed: player_10 asked player_7 whether the vote on player_9 rests on anything beyond the same thin day-2 push.
[Day 3] player_2 → player_10: player_2 argued player_10 pushed a single day-2 lynch and asked them to explain why before a vote. Defense: player_10 said they did not push anyone on day 2 and abstained, and that the sentinel's watch on them showed no visitors on night 1. (Game record shows player_10 voted to eliminate player_1 on day 2.)
[Day 3] player_10, player_9 (revealed chanteuse, voted out day 4) → player_7: player_10 asked player_7 whether the vote on player_9 rests on more than the day-2 lynch. player_9 asked the same question about player_7's vote.
[Day 3] player_1 → player_8: player_1 asked player_8 to say whether they are the vigilante and to name the night they would shoot and why they are holding fire. Defense: player_8 said they held fire on nights 1 and 2, are not claiming yet, and need a real contradiction between two claims before shooting.
[Day 3] player_1 → player_4: player_1 argued player_4 has been targeted twice without saying anything and should answer directly. Defense: player_4 said they will not claim a role on a thin read, would not name a night they would shoot, and want someone to make a concrete claim first.
[Day 4] player_7, player_2 → player_9 (revealed chanteuse, voted out day 4): player_7 said player_9 read Suspicious on night 3, so a wolf; player_2 said that check is the only hard result and a Suspicious healer read would be strange. Defense: player_9 claimed to be the healer, protecting player_8 on night 2 and player_2 on night 3 with no attacks, and said one Suspicious read should not decide a lynch. Disputed: player_7 argued player_9's save on player_2 could not stop the night 3 kill on player_10, and only a Chanteuse or Illusionist fits that claim.
[Day 4] player_5 (revealed illusionist, killed night 4) → player_9 (revealed chanteuse, voted out day 4): player_5 argued player_9's healer claim cannot stand because player_10 was shown to be the healer; later said they spoke too quickly and nothing was announced. Defense: player_9 said player_10's role was hidden with no announced reveal, kept the healer claim, and asked player_5 for their night 1 and 2 results. Disputed: player_5 withdrew the premise, saying nothing was announced about player_10's role, and asked how saves work when no attack came.
[Day 4] player_9 (revealed chanteuse, voted out day 4) → player_7: player_9 argued that if player_7 checked them Suspicious one of them is lying, and asked why an investigator would wait until day 4 to check someone. Defense: player_7 said they checked player_9 on night 3 and got Suspicious, was blocked on night 2, and preferred a Suspicious read to a guess. Disputed: player_2 said player_7's check is the only hard result on the table, and a Suspicious read on a real healer would be strange.

Today's discussion so far, as the speaker saw it:
player_8: I'm the vigilante. I held fire on nights 1 and 2, was roleblocked on night 3, and shot player_5 on night 4. I have one bullet left.

THE LINE:
player_8, your shot on player_5 fits the record, since player_5 was an illusionist. The useful test is your bullet: if you name a target tomorrow, that target should be someone the table can check against the night results. I'd rather we follow the claims that line up with the record than chase the quiet ones.


## Response for Case 30

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-03.on", "type": "open_floor_line", "kind": _}
]
```

---

# Case 31

### s031 (key `voices-04.off:5:player_3:2`)

Speaker: player_3, during the day's discussion.

Earlier days (summary, most recent part):
lves and the serial killer last night. Their role is hidden by an illusionist.

-- Claims made in the day discussion (claims, not facts; a note starting "Record:" or "Rules:" is an exact check by the game master; a plan said in the day binds no one: a player may choose a different target at night) --
player_5: claimed investigator (day 3).
  Night 1: checked player_1, says they read Not suspicious.
  Night 2: checked player_3, says they read Not suspicious.
player_9: claimed healer (day 4).
  Night 2: protected player_5, says they saved them from an attack. Record: player_5 was attacked and saved by the healer that night.
  Night 3: protected player_5, says they saved them from an attack. Record: player_5 was attacked and saved by the healer that night.
player_8: claimed trailseer (day 4). Record: revealed as trailseer when they were voted out on day 4, as claimed.
  Night 1: followed player_10; says they visited player_7 (a visit alone does not establish what they did there).
  Night 2: followed player_3; says they visited no one.
  Night 3: followed player_9; says they visited player_5 (a visit alone does not establish what they did there).
player_6: claimed sentinel (day 4).
  Night 1: watched player_2; says no one visited them.
  Night 3: watched player_9; says player_8 visited them (a visit alone does not establish a visitor's role or what they did).
player_7: claimed sigilist (day 4).
  Night 1: says they did not act.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
[Day 4] player_6, player_7, player_9, player_5 → player_8 (revealed trailseer, voted out day 4): player_6 wanted player_8 to answer the night 1 question. player_7 and player_9 argued player_8's night 1 claim lacks support, since player_7 got no block or visit. player_5 said that would make it wrong. Defense: player_8 stood by the night 1 follow showing player_10 visiting player_7. Said a block only shows if it takes, so player_7 may have been unblocked. Asked player_7 to check. Disputed: player_6 confirmed the night 3 follow of player_9 via their own watch, and player_9 called that visit true. player_2 pressed player_8 to answer the night 1 question before any vote.
[Day 4] player_8 (revealed trailseer, voted out day 4) → player_7: player_8 argued player_7's no-message argument fails because a block shows only if it takes. player_8 asked who stabbed player_10 on night 1 if not player_7. Defense: player_7 said they took no action on night 1 and cannot say who the serial killer was. Argued a chanteuse visit always produces a block message, so no message means no visit.
[Day 4] player_3 → player_6: player_3 asked how player_6 learned of the night 3 visit to player_9, since only a watch or follow shows it. Asked whether player_6 holds a role that would give that knowledge. Defense: player_6 said they are the sentinel, watched player_9 on night 3 and saw player_8 come to them, and watched player_2 on night 1 with no visitors.

Today's discussion so far, as the speaker saw it:
player_2: player_9's healer claim is the only one that has stood unchallenged, and player_5's story that player_9 saved them on night 3 is something I'd like to see tested. player_6, your night 3 watch corroborated by player_8's will is the strongest piece of evidence we have, so I'd lean on that for now. Who else has a night result that can be cross-checked?
player_4: player_9's healer claim is gone with them, so nothing about player_5 can be checked against it now. player_5's check claim and player_6's watch are the two results we can test. I'd like player_5 to say what they read on player_3 and whether player_3 has a claim to back it.
player_5: As I said earlier, I checked player_3 on night 2 and they read Not suspicious. player_3 has made no role claim, so I can't add more on them. Both my checks are used, so I'm not holding anything else. player_6 and player_7 have claimed roles; their night details are the ones we can test.

THE LINE:
player_6, your night 3 watch on player_9 is the only result that's been checked, and it checks out via player_8's will. But that only confirms player_8 went to player_9, not that you're the Sentinel. player_7, you say you took no action on night 1. If you're the sigilist, a sigil on someone who didn't attack would show as no effect, so could you say who you placed one on, if anyone?


## Response for Case 31

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-04.of", "type": "open_floor_line", "kind": _}
]
```

---

# Case 33

### s033 (key `voices-07.off:2:player_3:1`)

Speaker: player_3, during the day's discussion.

Earlier days (summary, most recent part):
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_7 was attacked by the serial killer but was saved by the healer!

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
None.

Today's discussion so far, as the speaker saw it:
No messages yet.

THE LINE:
Nothing to go on yet, so I'll ask for claims with specifics. Night 1 the serial killer hit player_7 and the healer saved them, so the healer is somewhere in the room. Anyone who holds a night result, say what you saw and who you watched or followed. I'm not voting anyone today without a read.


## Response for Case 33

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-07.of", "type": "open_floor_line", "kind": _}
]
```

---

# Case 38

### s038 (key `voices-05.off:6:player_2:1`)

Speaker: player_2, during the day's discussion.

Earlier days (summary, most recent part):
them from attacks. Disputed: player_7 said both players cannot have saved player_9 on the same night and asked player_4 to state each night's save.
[Day 4] player_4 (revealed healer, voted out day 4) → player_7 (revealed chanteuse, killed night 4): player_4 said player_7's Healer claim is false because player_4 was the one protecting player_9 on nights 2 and 3. player_4 also said player_7 has been silent about their night. Defense: player_7 said they protected player_5 on night 1 and player_9 on nights 2 and 3. player_7 asked player_4 to say which saves they made each night. Disputed: player_8 said their night 3 watch on player_7 saw no visitors, so player_7 did not carry the night 3 kill and was not healer that night.
[Day 4] player_2, player_4 (revealed healer, voted out day 4) → player_8: player_2 said player_8's night 2 list names dead player_10 and asked for an explanation. player_4 said the list may be off because it names player_10. Defense: player_8 said dead player_10 cannot be a living visitor, so that name is the Necromancer checking player_9 through a dead Investigator's body. The other three names are real visitors. Disputed: player_1 asked that player_8's list be tested before anyone votes.
[Day 4] player_1 (revealed illusionist, voted out day 5) → player_5: player_1 said player_5's Sigilist claim is unproven. player_5 has shown no placed sigil and has not said what they did on nights 1 and 2. Defense: player_5 said they are the real Sigilist, placed no sigils so player_1's claim is false, and asked why player_1's only action was a sigil on a non-attacker. Disputed: player_7 asked both Sigilist claimants to say where their sigils went.
[Day 5] player_1 (revealed illusionist, voted out day 5), player_9 → player_5: player_1 argued player_5 claims sigilist but has not said where their night 1 or 2 sigils went. player_9 said they lean player_5 for the same reason. Defense: player_5 said they placed no sigils on nights 1 or 2, so have none to show, and both sigils are unspent. player_5 also said player_1's night 2 visit fits no real Sigilist.
[Day 5] player_5 → player_1 (revealed illusionist, voted out day 5): player_5 argued player_1's claimed night 2 sigil on player_9 is a visit that player_8's watch shows, and that a visit like that does not fit a real Sigilist. Defense: player_1 argued the night 2 visit was the sigil itself, since placing a sigil is a visit, and the sigil had no effect, matching player_8's list.
[Day 5] player_1 (revealed illusionist, voted out day 5) → player_9: player_1 said whoever is the real Trailseer should explain what player_9's night 4 follow would have shown before the block, questioning the Trailseer claim. Defense: player_9 said their night 4 follow on player_1 was roleblocked, so they learned nothing. Their night 2 follow on player_4 showed player_4 going to them, which fits a save. Disputed: player_5 argued player_9's night 1 follow matching player_10's check on player_5 is a point in player_9's favour.

Today's discussion so far, as the speaker saw it:
No messages yet.

THE LINE:
Four alive, and the necromancer is one of player_3 or player_6, so we have to get it right today. player_3 abstained twice and has never said what they did at night. I'd vote player_3 if we vote now, but I want a claim from both of them before anyone locks in.


## Response for Case 38

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-05.of", "type": "open_floor_line", "kind": _}
]
```

---

# Case 47

### s047 (key `voices-08.off:4:player_5:1`)

Speaker: player_5, during the day's discussion.

Earlier days (summary, most recent part):
wolves last night. Their role is hidden by an illusionist.
[Day 2] Here's the vote result for day 2:
  player_1 voted to eliminate player_6
  player_2 voted to abstain
  player_3 voted to eliminate player_6
  player_5 voted to abstain
  player_6 voted to eliminate player_7
  player_7 voted to eliminate player_6
  player_8 voted to eliminate player_3
  player_9 voted to eliminate player_7
Player player_6 has been voted out and was a sigilist.
[Day 2] Night of day 2: player_3 was attacked by the wolves and the serial killer last night. Their role is hidden by an illusionist.
[Day 3] Here's the vote result for day 3:
  player_1 voted to eliminate player_8
  player_2 voted to eliminate player_7
  player_5 voted to abstain
  player_7 voted to eliminate player_2
  player_8 voted to eliminate player_7
  player_9 voted to eliminate player_1
Player player_7 has been voted out and was a investigator.
The record of player_7, the investigator: night 1, checked player_5: Not suspicious; night 2, checked player_3: Not suspicious.
[Day 3] Night of day 3: player_1 was attacked by the wolves and the serial killer last night. They were a sentinel. The record of player_1, the sentinel: night 1, watched player_6; saw no one; night 2, watched player_7; saw player_2 and player_3 visit them.

-- Claims made in the day discussion (claims, not facts; a note starting "Record:" or "Rules:" is an exact check by the game master; a plan said in the day binds no one: a player may choose a different target at night) --
player_3: claimed healer (day 2).
  Night 1: says they tried to protect player_7 and were roleblocked.
player_1: claimed sentinel (day 3). Record: revealed as sentinel when they died on night 3, as claimed.
  Night 2: watched player_7; says player_2 and player_3 visited them (a visit alone does not establish a visitor's role or what they did).
player_7: claimed investigator (day 3). Record: revealed as investigator when they were voted out on day 3, as claimed.
  Night 1: checked player_5, says they read Not suspicious.
  Night 2: checked player_3, says they read Not suspicious.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
[Day 2] player_6 (revealed sigilist, voted out day 2) → player_7 (revealed investigator, voted out day 3): player_6 argued that player_7 is pushing for votes without naming a lynch target. Defense: player_7 said they had no lynch yet, since the only thing to test is player_3's claim, and waiting for tonight's report beats guessing.
[Day 2] player_6 (revealed sigilist, voted out day 2), player_7 (revealed investigator, voted out day 3) → player_3: player_6 and player_7 asked player_3 to name tonight's protection target before the report, so a save could be checked against the attack. Defense: player_3 refused to name tonight's target before the report, said night 1 protection was blocked, and said tonight's report is the test. player_3 also claimed player_4 visited them before dying.

Today's discussion so far, as the speaker saw it:
No messages yet.

THE LINE:
Player_1's night 2 watch said player_2 and player_3 visited player_7. Player_3 is now dead, so only player_2 can be checked against that. player_2, what did you do on night 2, and who did you go to?


## Response for Case 47

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-08.of", "type": "open_floor_line", "kind": _}
]
```