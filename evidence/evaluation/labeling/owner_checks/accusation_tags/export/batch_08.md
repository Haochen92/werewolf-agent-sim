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

# Case 859

### Item d03:d2:s11

Game d03, day 2.

**Since the last discussion:**

- **game_master:** There is no vote on day 1, so no one voted and no one is eliminated.

- **game_master:** Night of day 1: player_1 was attacked by the wolves but was saved by the healer! player_4 was stabbed by the serial killer last night. They were a sigilist.

**Today, before this message:**

- **player_1:** Last night I checked player_7 and saw that both player_8 and player_9 visited them.

- **player_5:** For what it's worth, last night I followed player_9, and I saw them visit player_7.

- **player_9:** I am the investigator, and I checked player_7 last night; they read not suspicious.

**The message — player_6 (proactive round):**

> Player 1, you said you checked player_7, but it sounds like you meant you watched them since you saw who visited. Player 9's visit to player_7 matches what player_1 and player_5 reported, so those claims line up cleanly.

**Whom does player_6's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 859

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "d03:d2:s11", "type": "message", "accused": _}
]
```

---

# Case 881

### Item d03:d3:s11

Game d03, day 3.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 2:
    player_1 voted to eliminate player_8
    player_2 voted to eliminate player_8
    player_3 voted to eliminate player_8
    player_5 voted to eliminate player_8
    player_6 voted to eliminate player_8
    player_7 voted to eliminate player_8
    player_8 voted to eliminate player_7
    player_9 voted to eliminate player_8
    player_10 voted to eliminate player_8
  Player player_8 has been voted out and was a chanteuse.

- **game_master:** Night of day 2: player_5 was killed by the wolves last night. Their role is hidden by an illusionist. player_9 was attacked by the serial killer but was saved by the healer! The Speculator has picked Town.

**Today, before this message:**

- **player_1:** On night two, I watched player_9 and saw both player_3 and player_6 visit them.

- **player_3:** I am the healer, and I targeted player_9 last night to successfully protect them from the serial killer's attack.

- **player_9:** Last night I checked player_2, and they read Suspicious.

- **player_2:** It is awfully convenient for player_9 to suddenly drop a suspicious check on me right now. If they really investigated me last night, why wait until now to manufacture pressure instead of sharing it immediately? That feels like a fabricated target to me.

- **player_9:** I checked you last night, Player 2, so sharing this result the very next morning is just how information works. The healer saved me and player_1's watch confirmed the visitors, but you're deflecting because that suspicious read hit a bit too close to home.

- **player_2:** If you really had a check on me, why stay completely silent about it yesterday while we were dealing with player_8? Dropping a suspicious read right after the healer saved you feels like a very convenient way to deflect attention.

- **player_9:** Player 2, yesterday was day two, and my investigation was on night two—we couldn't discuss a result from a night that hadn't happened yet. You're scrambling because the check caught you, and player_1 and player_3 have already backed up my night.

**The message — player_2 (discussion round):**

> You are claiming your second check right after being protected, which conveniently uses up your entire ability set with zero prior hints. If you have already burned both investigations across nights one and two, we have no way to verify if this target is real or manufactured.

**Whom does player_2's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 881

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "d03:d3:s11", "type": "message", "accused": _}
]
```

---

# Case 936

### Item d05:d3:s0

Game d05, day 3.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 2:
    player_1 voted to abstain
    player_2 voted to eliminate player_3
    player_3 voted to eliminate player_2
    player_4 voted to abstain
    player_6 voted to abstain
    player_7 voted to abstain
    player_8 voted to eliminate player_2
    player_9 voted to eliminate player_3
    player_10 voted to abstain
  The town chose to abstain. No one is eliminated today.

- **game_master:** Night of day 2: player_3 was killed by the wolves last night. Their role is hidden by an illusionist.

*Opening round: every player speaks at once, so player_1 had heard no other line today.*

**The message — player_1 (opening round):**

> Last night I watched player_3, and saw both player_2 and player_10 visit them. We need to hear why both of them were at the investigator claim's door right before they died.

**Whom does player_1's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 936

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "d05:d3:s0", "type": "message", "accused": _}
]
```

---

# Case 948

### Item d05:d4:s10

Game d05, day 4.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 3:
    player_1 voted to eliminate player_2
    player_2 voted to eliminate player_1
    player_4 voted to eliminate player_2
    player_6 voted to eliminate player_2
    player_7 voted to eliminate player_2
    player_8 voted to eliminate player_2
    player_9 voted to eliminate player_1
    player_10 voted to eliminate player_2
  Player player_2 has been voted out and was a chanteuse.

- **game_master:** Night of day 3: player_1 was attacked by the wolves but was saved by the healer! player_9 was shot by the vigilante last night. They were a illusionist.

**Today, before this message:**

- **player_6:** I am the Vigilante, and I am the one who shot the illusionist player_9 last night.

- **player_10:** Last night I followed player_4 and saw them visit player_1. Since player_1 was attacked by the wolves last night and saved by the healer, player_4 looks like the wolf carrier.

- **player_4:** Player_10, you caught me visiting player_1 because I spent last night protecting them from the wolf attack. If I were the wolf carrier, player_1 would be dead instead of saved by my heal.

- **player_8:** Player_4's claim as the Healer lines up with player_10 seeing them visit player_1 during the night save. Since both wolves are already gone, our main threat now is finding the Necromancer among the remaining unverified players like player_7.

**The message — player_4 (proactive round):**

> Player 10, a protective visit looks identical to an attack from the outside, but my heal is the reason player 1 survived the night. Since both wolves are already dead, your suspicion here is way off base.

**Whom does player_4's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 948

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "d05:d4:s10", "type": "message", "accused": _}
]
```

---

# Case 985

### Item d06:d5:s6

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

**The message — player_8 (proactive round):**

> Player 5 is quick to narrow the pool down to player_10 and me, but let's look closer at player_3's claims. Player 3 has given us check results without much independent verification beyond their own word.

**Whom does player_8's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 985

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "d06:d5:s6", "type": "message", "accused": _}
]
```