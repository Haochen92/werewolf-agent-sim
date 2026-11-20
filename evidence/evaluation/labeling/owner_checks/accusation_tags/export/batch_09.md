# Owner check: whom does each message accuse?

Read the lines before each message, then the message. Write your label in the matching row of
`answers_template.json` (same key), and save the filled file as `human.json` in the packet folder.
The full guide, with worked examples, is `GUIDE.md`.

A message ACCUSES a player when it suspects or blames that player of being evil or of lying.
- Suspicion counts even when hedged ("they are my top suspect, though I'm not certain").
- Saying a player's claim or report is false counts: that blames them of lying.
- It does NOT accuse a player it defends or supports, agrees with, or mentions with no clear
  stance. Passing commentary, such as noting that someone has been quiet, is not an accusation.
- A question accuses only when it plainly casts suspicion; a plain request for information does not.
Judge this message only, reading it in the light of the lines before it: a player it accused
earlier, but not in this message, is not accused here. Dead players can be accused too.

The label is `none`, or the ids of every accused player in seat order (lowest seat number
first), comma-joined with no spaces.

For example `player_4`, or `player_3,player_10` (seat 3 before seat 10).

---

# Case 990

### Item d06:d5:s11

Game d06, day 5.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 4:
    player_2 voted to eliminate player_5
    player_3 voted to eliminate player_6
    player_5 voted to eliminate player_6
    player_6 voted to eliminate player_8
    player_8 voted to eliminate player_6
    player_10 voted to eliminate player_5
  Player player_6 has been voted out and was a vigilante.
  The record of player_6, the vigilante: night 1, held fire; night 2, held fire; night 3, held fire.

- **game_master:** Night of day 4: player_3 was attacked by the vigilante but was saved by the healer!

**Today, before this message:**

- **player_2:** Last night, on night four, I targeted player_3 with my protection and successfully blocked the attack.

- **player_3:** On night three, I checked player_5 and they read not suspicious.

- **player_5:** Player two's claim of protecting player_3 last night directly matches the GM record of the healer saving them from the attack. That strongly supports player_2 as the real healer, leaving player_8 and player_10 to scrutinize for remaining threats.

- **player_8:** Player 5 is quick to narrow the pool down to player_10 and me, but let's look closer at player_3's claims. Player 3 has given us check results without much independent verification beyond their own word.

- **player_5:** player_8, questioning player_3 seems counterproductive when the healer's save on them is verified by the morning reports. If we are looking for threats, we should focus on who is attempting to deflect from the confirmed information we have rather than challenging the players that information validates.

- **player_8:** Just because player_3 survived doesn't mean their check results are infallible, player_5. We can acknowledge the healer's save while still questioning whether player_3's claimed checks actually point us anywhere real.

- **player_5:** player_8 raises a fair point that a confirmed save doesn't automatically verify every past check. However, player_3's claimed checks align reasonably with the known events so far, so dismissing them outright might be premature. Let's hear what player_10 has to contribute regarding their claimed sigil results.

- **player_10:** My sigil on player_7 on night two successfully struck them down, confirming they were attacking. With both wolves eliminated, we should focus on anyone trying to undermine verified town actions.

**The message — player_2 (proactive round):**

> Since player_6 was voted out on day four, the vigilante attack on player_3 last night had to come from the necromancer using player_6's dead body. That means we need to hunt the necromancer instead of arguing over player_3's checks.

**Whom does player_2's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 990

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "d06:d5:s11", "type": "message", "accused": _}
]
```

---

# Case 1014

### Item e01:d3:s9

Game e01, day 3.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 2:
    player_1 voted to abstain
    player_2 voted to eliminate player_5
    player_3 voted to eliminate player_5
    player_4 voted to abstain
    player_5 voted to eliminate player_9
    player_6 voted to eliminate player_5
    player_8 voted to abstain
    player_9 voted to abstain
    player_10 voted to eliminate player_5
  It's a tie between ['abstain', 'player_5']. No one is voted out this day.

- **game_master:** Night of day 2: player_8 was attacked by the wolves and the serial killer last night. Their role is hidden by an illusionist.

**Today, before this message:**

- **player_5:** Last night I watched player_2, and player_6 was the one who visited them.

- **player_1:** Player_5's watch on player_2 caught player_6 visiting them last night. Since player_2 claimed trailseer, we should ask player_2 who they targeted to see if player_6's visit matches their path.

**The message — player_2 (proactive round):**

> I was roleblocked last night, so I didn't target anyone. But player_5's watch catching player_6 visiting me makes total sense, since blocking counts as a visit and player_6 is likely the Chanteuse who hit me.

**Whom does player_2's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 1014

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "e01:d3:s9", "type": "message", "accused": _}
]
```

---

# Case 1020

### Item e01:d3:s17

Game e01, day 3.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 2:
    player_1 voted to abstain
    player_2 voted to eliminate player_5
    player_3 voted to eliminate player_5
    player_4 voted to abstain
    player_5 voted to eliminate player_9
    player_6 voted to eliminate player_5
    player_8 voted to abstain
    player_9 voted to abstain
    player_10 voted to eliminate player_5
  It's a tie between ['abstain', 'player_5']. No one is voted out this day.

- **game_master:** Night of day 2: player_8 was attacked by the wolves and the serial killer last night. Their role is hidden by an illusionist.

**Today, before this message:**

- **player_5:** Last night I watched player_2, and player_6 was the one who visited them.

- **player_1:** Player_5's watch on player_2 caught player_6 visiting them last night. Since player_2 claimed trailseer, we should ask player_2 who they targeted to see if player_6's visit matches their path.

- **player_2:** I was roleblocked last night, so I didn't target anyone. But player_5's watch catching player_6 visiting me makes total sense, since blocking counts as a visit and player_6 is likely the Chanteuse who hit me.

- **player_6:** I didn't block anyone, player_2. I'm a sigilist, and I placed a sigil on you last night because your conflicting claims made you worth testing.

- **player_9:** Player_6 claims to be the sigilist and says they placed a sigil on player_2 last night. However, I am actually the sigilist, so player_6 is fabricating a false role claim.

- **player_6:** Player 9, you're just jumping in to claim my role after I shared why I visited player_2. If you were actually the sigilist, you would have spoken up earlier instead of opportunistically grabbing the claim right after me.

- **player_9:** I didn't jump in opportunistically, I spoke up because you're claiming the role I actually hold. If you really placed a sigil on player_2, let's see if you can actually back up that fabricated story.

- **player_6:** Player 9, waiting until after I explained my visit to claim the exact same role is way too convenient. If you actually had actions to report from the last two nights, you should have brought them up before I spoke.

**The message — player_9 (discussion round):**

> Player_6, you only claimed sigilist to explain away the visit player_5 caught you making last night. Calling me opportunistic doesn't change the fact that you manufactured a fake claim to cover your tracks.

**Whom does player_9's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 1020

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "e01:d3:s17", "type": "message", "accused": _}
]
```

---

# Case 1052

### Item e02:d4:s9

Game e02, day 4.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 3:
    player_3 voted to eliminate player_5
    player_4 voted to eliminate player_7
    player_5 voted to eliminate player_8
    player_6 voted to eliminate player_5
    player_7 voted to eliminate player_3
    player_8 voted to eliminate player_3
    player_9 voted to eliminate player_5
    player_10 voted to eliminate player_5
  Player player_5 has been voted out and was a necromancer.

- **game_master:** Night of day 3: player_4 was killed by the wolves last night. Their role is hidden by an illusionist.

**Today, before this message:**

- **player_3:** For last night, night 3, I watched player_6 and nobody visited them.

- **player_7:** I'll claim my role now since the town needs all surviving claims on the table; I am the sigilist.

- **player_8:** I want to share that I was roleblocked last night on night 3, so my protection did not go through.

- **player_6:** Player 7 just claimed sigilist, but I am holding that exact role. Since I know my own alignment and profession, player_7 is caught in a blatant lie.

- **player_7:** You're claiming sigilist now right after I stepped forward? That looks like a defensive counter-claim to push suspicion away from yourself.

- **player_6:** I spoke first and called out your fake claim immediately, player_7. You're the one scrambling with a late counter-claim because you got caught trying to steal a town role. Let's see your targets or what you've actually done with those sigils.

**The message — player_7 (discussion round):**

> You waited until I stepped forward before suddenly claiming the exact same role. If you had those sigils all along, you would have brought them up earlier instead of pulling a convenient counter-claim.

**Whom does player_7's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 1052

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "e02:d4:s9", "type": "message", "accused": _}
]
```

---

# Case 1083

### Item e03:d4:s6

Game e03, day 4.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 3:
    player_1 voted to eliminate player_2
    player_2 voted to eliminate player_1
    player_3 voted to eliminate player_2
    player_7 voted to eliminate player_2
    player_8 voted to eliminate player_2
  Player player_2 has been voted out and was a illusionist.

- **game_master:** Night of day 3: player_3 was attacked by the serial killer and the vigilante last night. They were a fortune teller.

**Today, before this message:**

- **player_7:** Last night I targeted player_3 with my final shot, confirming they were the fortune teller.

- **player_1:** If you are the vigilante, why shoot player_3 when they were already targeted? We need to figure out if player_8 is the serial killer or our remaining town role.

- **player_8:** I've kept quiet because I'm the healer, and I protected player_7 last night. Meanwhile, player_1 is pushing hard against me without claiming any role themselves or explaining where they were during these attacks.

- **player_1:** I haven't claimed yet because I'm the sigilist holding my last sigil for the final threat. If you're really the healer who protected player_7, you should be helping us find the serial killer instead of deflecting onto my silence.

**The message — player_8 (discussion round):**

> Player_1 claims the sigilist role now, but waited until pressed to say anything about their position. If player_7 is the vigilante who shot player_3, player_1's hesitation and sudden claim look like an attempt to duck the vote. We should look closely at player_1.

**Whom does player_8's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 1083

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "e03:d4:s6", "type": "message", "accused": _}
]
```