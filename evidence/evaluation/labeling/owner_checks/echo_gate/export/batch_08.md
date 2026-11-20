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

# Case 116

### s116 (key `voices-04.off:3:player_3:1`)

Speaker: player_3, during the day's discussion.

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
No messages yet.

THE LINE:
Day 2 was all abstains, so we have no votes to read yet. Player_5 got hit by the serial killer and the healer saved them, which means the serial killer is active and the healer is alive. I'd like everyone to name at least one player they'd vote for today, so we get a real voting record to work from.


## Response for Case 116

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-04.of", "type": "open_floor_line", "kind": _}
]
```

---

# Case 117

### s117 (key `voices-05.on:4:player_5:1`)

Speaker: player_5, during the day's discussion.

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
player_1: Sigil on player_2 is a neat check on the vigilante claim. Two bodies have now had hidden roles, so I'd like the sentinel and trailseer to tell us exactly who they saw at their doors on night 3. Player_6 has been quiet, and with player_7 gone, the Necromancer could be sitting there.
player_6: player_1, you named me as the quiet one, but you haven't said what you saw on night 3 or why you think a silent player is the necromancer. Sigil on player_2 doesn't tell us much about the Necromancer. Who do you want us to vote, and why?
player_1: player_6, I only said you'd been quiet, not that you're the necromancer. I have no night 3 result to share and I'm not claiming a role. Player_8 and player_9 contradict each other on who was visited, so I'd rather hear their night 3 targets before anyone votes.
player_9: Sharing my night 3: I followed player_6 and no visit was made in their name, so they did not act unless someone blocked them. That rules them out for anything that night, but it doesn't clear them of the earlier nights. player_8, your sentinel claim should be easy to test: who came to you on night 3?
player_8: player_9, on night 3 I was roleblocked, so my watch on you never happened and I learned nothing about who came to me. Night 2 I watched player_10 and no one visited them. My last watch stays unspent until a claim needs checking.

THE LINE:
I'd vote player_1 for now. They named player_6 as the possible necromancer without any result, then asked the others for night 3 results. player_8 and player_9 both gave theirs, so I want player_1 to say what they did on night 3.


## Response for Case 117

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-05.on", "type": "open_floor_line", "kind": _}
]
```

---

# Case 120

### s120 (key `voices-07.on:2:player_1:1`)

Speaker: player_1, during the day's discussion.

Earlier days (summary, most recent part):
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_7 was attacked by the serial killer but was saved by the healer!

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
None.

Today's discussion so far, as the speaker saw it:
No messages yet.

THE LINE:
Nothing to go on yet, so let's get a clean record. Player_7 was hit by the serial killer and saved, so someone in the healer seat knows who they guarded. Whoever held a night result, say who you visited and what came back, and we can test the claims against each other.


## Response for Case 120

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-07.on", "type": "open_floor_line", "kind": _}
]
```

---

# Case 123

### s123 (key `voices-03.on:3:player_5:1`)

Speaker: player_5, during the day's discussion.

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

THE LINE:
Good day to you all. I'd like to hear from player_10 on the lynch on player_1: what in player_1's play made it worth a vote on day 2? Since the sentinel is gone, the sentinel's night 1 watch on player_10 gives us nothing to lean on, so a direct answer would help us more than another round of general talk.


## Response for Case 123

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-03.on", "type": "open_floor_line", "kind": _}
]
```

---

# Case 124

### s124 (key `voices-07.off:2:player_6:2`)

Speaker: player_6, during the day's discussion.

Earlier days (summary, most recent part):
-- The game master's record (exact; it outranks anything a player or a summary says) --
[Day 1] There is no vote on day 1, so no one voted and no one is eliminated.
[Day 1] Night of day 1: player_7 was attacked by the serial killer but was saved by the healer!

-- Accusations in the day discussion (a summariser's account of what players argued; claims, not facts) --
None.

Today's discussion so far, as the speaker saw it:
player_5: Night 1 was a healer save on player_7, so the healer is alive and that's worth protecting. I'd like the healer and any other power role to claim early. Whoever is claiming, give a target and result so we can cross-check. Nobody has any real evidence yet, so I'm waiting on the first claims before I lean on anyone.

THE LINE:
Agree the healer should come out, but I'd rather see who claims first before anyone commits. Night 1 tells us the SK hit player_7 and got stopped, so keep an eye on who's pushing hardest for an early lynch. I'm holding my info for now and will share it once there's a conflict to test against.


## Response for Case 124

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "voices-07.of", "type": "open_floor_line", "kind": _}
]
```