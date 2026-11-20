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

# Case 52

### s052 (key `voices-06.on:2:player_5:2`)

Speaker: player_5, during the day's discussion.

Earlier days (summary, most recent part):
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_3 was killed by the wolves last night. Their role is hidden by an illusionist.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
None.

Today's discussion so far, as the speaker saw it:
player_2: I'm the Investigator. Night 1 I checked player_7: Not suspicious. That clears them of the wolves, so use that when you vote. I'll hold my second check for whoever the day turns on.
player_10: player_2, a check on player_7 is a useful start, but it only helps if the Investigator is genuine. I'd like to see whoever claims Sentinel or Trailseer say who visited whom, since that's the only way we can test the claims against each other before we vote.
player_2: player_10, fair test, but I'm the only Investigator claim, so I'll give you the one fact I have: player_7 read Not suspicious. Sentinel and Trailseer should say who they saw and who they followed, and I'll hold my second check until we know who's lying about it.

THE LINE:
player_2, I'd like to see the Sentinel and Trailseer answer before anyone votes. Until then, one check on player_7 is all we have, and it's only your word. Let's see who speaks up with night results first.


## Response for Case 52

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-06.on", "type": "open_floor_line", "kind": _}
]
```

---

# Case 53

### s053 (key `voices-07.on:2:player_4:2`)

Speaker: player_4, during the day's discussion.

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
Right then, I'll say what I can. Nobody has a result yet, so I'm not voting on a name today. Whoever is claiming a check or follow, give a named player and result, and we can test those claims against each other tonight.


## Response for Case 53

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-07.on", "type": "open_floor_line", "kind": _}
]
```

---

# Case 56

### s056 (key `voices-03.on:3:player_8:1`)

Speaker: player_8, during the day's discussion.

Earlier days (summary, most recent part):
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_6 was killed by the wolves last night. They were a trailseer.
[Day 2] Here's the vote result for day 2:
  player_1 voted to abstain
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

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
None.

Today's discussion so far, as the speaker saw it:
player_2: Two info roles down already, so the wolves are clearly hunting checks. Player_10 drew the sentinel's watch on night 1 and saw no one, which is a useful bit for anyone who claims to be a Trailseer-type. Player_9 and player_10 each pushed a single lynch on day 2, so I'd like them to say why they picked those targets before we vote.
player_9: I went after player_4 on day 2 because they had said almost nothing on day 1 and I wanted them to show their hand. It was a thin read, not a strong one. I'd rather hear what player_4 has to say before we vote again.
player_10: Fair enough, player_2. The sentinel's watch on me showed no visitors on night 1, which only tells us nobody came to me that night, not what I did. I'm not going to claim a role on a thin read. Who do you think is the strongest lead for a wolf so far, and why?
player_7: Both day 2 pushes were thin. I'd like player_9 and player_10 to say what they're looking at beyond gut feel. My vote right now is on player_9 for pushing a lynch with no real basis, but I'd like to hear player_4's answer before locking that in.
player_9: As I said earlier, player_4 had barely spoken on day 1, and that's all I had. It was thin and I won't pretend otherwise. I'll hear player_4 out before we vote again. player_7, does your vote on me come with anything beyond the lynch itself?
player_10: player_7, I didn't push anyone on day 2; I abstained, so I'm not the one who put player_9 in the spotlight. You're voting on player_9 for the same thin push. Is there anything from player_9's day-1 or day-2 play you're basing that on, or is it just the lynch itself?

THE LINE:
Player_9 and player_7 are trading votes over a lynch nobody can back up, so I'd rather see player_4 speak before anyone is locked in. Abstaining today is fine by me, but I'll vote for whoever gives a concrete reason. I'm holding my bullets until a claim contradicts another.


## Response for Case 56

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-03.on", "type": "open_floor_line", "kind": _}
]
```

---

# Case 62

### s062 (key `voices-08.off:3:player_5:1`)

Speaker: player_5, during the day's discussion.

Earlier days (summary, most recent part):
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_4 was stabbed by the serial killer last night. They were a chanteuse. player_10 was killed by the wolves last night. Their role is hidden by an illusionist.
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

-- Claims made in the day discussion (claims, not facts; a note starting "Record:" or "Rules:" is an exact check by the game master; a plan said in the day binds no one: a player may choose a different target at night) --
player_3: claimed healer (day 2).
  Night 1: says they tried to protect player_7 and were roleblocked.

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
[Day 2] player_6 (revealed sigilist, voted out day 2) → player_7: player_6 argued that player_7 is pushing for votes without naming a lynch target. Defense: player_7 said they had no lynch yet, since the only thing to test is player_3's claim, and waiting for tonight's report beats guessing.
[Day 2] player_6 (revealed sigilist, voted out day 2), player_7 → player_3: player_6 and player_7 asked player_3 to name tonight's protection target before the report, so a save could be checked against the attack. Defense: player_3 refused to name tonight's target before the report, said night 1 protection was blocked, and said tonight's report is the test. player_3 also claimed player_4 visited them before dying.

Today's discussion so far, as the speaker saw it:
player_1: I'm the sentinel. Night 2 I watched player_7: player_2 and player_3 both visited them. I have one watch left.
player_7: I'm the Investigator. Night 1 I checked player_5 (Not suspicious), and night 2 I checked player_3 (Not suspicious), so neither is a wolf.

THE LINE:
Two claims clash here. player_7 says player_3 checked Not suspicious, and player_3 says they're the healer and protected player_7 on night 1 before being roleblocked. Night 2 went wrong for player_3 anyway, so whoever is telling the truth about player_3 matters. player_1, did your watch on player_7 show anyone visiting player_3 that night?


## Response for Case 62

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-08.of", "type": "open_floor_line", "kind": _}
]
```

---

# Case 69

### s069 (key `voices-04.off:5:player_2:1`)

Speaker: player_2, during the day's discussion.

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
No messages yet.

THE LINE:
player_9's healer claim is the only one that has stood unchallenged, and player_5's story that player_9 saved them on night 3 is something I'd like to see tested. player_6, your night 3 watch corroborated by player_8's will is the strongest piece of evidence we have, so I'd lean on that for now. Who else has a night result that can be cross-checked?


## Response for Case 69

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-04.of", "type": "open_floor_line", "kind": _}
]
```