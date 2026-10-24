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

# Case 535

### Item b09:d2:s2

Game b09, day 2.

**Since the last discussion:**

- **game_master:** There is no vote on day 1, so no one voted and no one is eliminated.

- **game_master:** Night of day 1: player_2 was stabbed by the serial killer last night. They were a sentinel. player_5 was killed by the wolves last night. They were a speculator.

*Opening round: every player speaks at once, so player_4 had heard no other line today.*

**The message — player_4 (opening round):**

> Last night I followed player_3, and they visited player_5 and player_1.

**Whom does player_4's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 535

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "b09:d2:s2", "type": "message", "accused": _}
]
```

---

# Case 538

### Item b09:d2:s8

Game b09, day 2.

**Since the last discussion:**

- **game_master:** There is no vote on day 1, so no one voted and no one is eliminated.

- **game_master:** Night of day 1: player_2 was stabbed by the serial killer last night. They were a sentinel. player_5 was killed by the wolves last night. They were a speculator.

**Today, before this message:**

- **player_4:** Last night I followed player_3, and they visited player_5 and player_1.

- **player_7:** I placed a sigil on player_1 last night, and it triggered because they attacked someone, but they survived due to night immunity.

- **player_8:** I am the investigator, and last night I checked player_4; they came back not suspicious.

**The message — player_1 (proactive round):**

> Player_7, claiming a sigil triggered on me sounds like a convenient fabrication to push a mislynch. If you were really holding a sigil, targeting me without any prior reason looks like an attempt to manufacture a suspect while real wolves hide.

**Whom does player_1's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 538

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "b09:d2:s8", "type": "message", "accused": _}
]
```

---

# Case 584

### Item b10:d5:s12

Game b10, day 5.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 4:
    player_1 voted to eliminate player_2
    player_2 voted to eliminate player_4
    player_4 voted to eliminate player_2
    player_5 voted to eliminate player_2
    player_6 voted to eliminate player_2
    player_8 voted to eliminate player_2
    player_9 voted to eliminate player_2
    player_10 voted to eliminate player_4
  Player player_2 has been voted out and was a speculator.

- **game_master:** Night of day 4: player_10 was attacked by the wolves but was saved by the healer!

**Today, before this message:**

- **player_10:** Last night I checked player_4, and they read Not suspicious.

- **player_1:** Player_10 being targeted by wolves twice fits their investigator claim, though we need to keep an eye on who is benefiting from these repeated night attacks. Let's look closer at player_9's voting pattern from yesterday too.

- **player_4:** Thanks for the check, player_10. Following up on player_1's point about player_9, player_9 was heavily pushing the lynch against player_2 yesterday, so examining how the votes aligned there is a good next step.

- **player_5:** Player_10 surviving two attacks shows the wolves are desperate to get rid of them. However, regarding player_1 and player_4 questioning player_9's vote on player_2 yesterday, we should remember that I voted for player_2 as well when they kept their role completely hidden.

**The message — player_9 (proactive round):**

> Player_5 is right that several of us voted for player_2 because they refused to claim a role while deflecting. Voting out someone who hid information all game wasn't just my idea, so trying to isolate me for it now is a stretch.

**Whom does player_9's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 584

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "b10:d5:s12", "type": "message", "accused": _}
]
```

---

# Case 599

### Item b10:d7:s7

Game b10, day 7.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 6:
    player_1 voted to eliminate player_8
    player_4 voted to eliminate player_8
    player_5 voted to eliminate player_8
    player_8 voted to eliminate player_10
    player_9 voted to eliminate player_10
    player_10 voted to eliminate player_8
  Player player_8 has been voted out and was a illusionist.

- **game_master:** Night of day 6: player_10 was attacked by the wolves and the wolves last night. They were a investigator. The record of player_10, the investigator: night 1, checked player_2: Not suspicious; night 2, checked player_1: Not suspicious; night 3, was roleblocked; night 4, checked player_4: Not suspicious; night 5, checked player_8: Suspicious.

**Today, before this message:**

- **player_1:** I am the Vigilante, and I have been roleblocked on nearly every night of this game. We need to locate the remaining wolf and the necromancer today.

- **player_4:** If you've been roleblocked constantly, player_1, that strongly points to the Chanteuse still being active. We need to figure out who is doing the blocking while claims like sigilist are already out there.

- **player_5:** If you are the Vigilante, player_1, how many bullets do you actually have left? Since you have supposedly been roleblocked nearly every night, you shouldn't have spent many unless you fired and missed or hit immunes before.

- **player_1:** I still have two bullets left because I haven't been able to fire a single shot through all those roleblocks. If you're questioning my inventory, player_5, we should look closer at who benefits from keeping the town vigilante completely silenced.

**The message — player_5 (discussion round):**

> You claim you couldn't shoot because of constant roleblocks, player_1, but that is awfully convenient cover. If you are really the Vigilante, how do we verify you haven't just been holding back as a wolf?

**Whom does player_5's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 599

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "b10:d7:s7", "type": "message", "accused": _}
]
```

---

# Case 611

### Item c01:d2:s15

Game c01, day 2.

**Since the last discussion:**

- **game_master:** There is no vote on day 1, so no one voted and no one is eliminated.

- **game_master:** Night of day 1: player_1 was stabbed by the serial killer last night. They were a healer. player_2 was killed by the wolves last night. They were a sigilist.

**Today, before this message:**

- **player_3:** On night one I checked player_8, and they came up not suspicious.

- **player_7:** On night one, I followed player_2 and saw them visit player_9. Since player_2 was the dead sigilist, that visit is worth noting.

- **player_9:** On night one I watched player_3, and no one visited them.

- **player_4:** Player_7, since you tracked player_2 to player_9, did you notice anything else about that visit? Player_3's clean check on player_8 also gives us a helpful starting point to evaluate.

- **player_5:** Building on player_4's question to player_7, if player_2 was dropping a sigil on player_9, we should check if anyone else visited player_9 that night to see if it triggered.

- **player_6:** Since player_9 watched player_3 that night, they wouldn't have caught anyone visiting player_9 where player_2 went. Building on player_5's point, if anyone else happened to watch player_9 instead, that's where we'd find out if player_2's sigil triggered.

- **player_10:** Player_3's check on player_8 gives us a useful starting point, clearing them of being a wolf. We should keep in mind that the serial killer also reads not suspicious to an investigator, so player_8 isn't entirely in the clear.

- **player_3:** Player_10 is spot on about my check on player_8 only clearing wolves and leaving the serial killer open. We need to watch player_8's responses closely to see if that pressure reveals anything.

- **player_7:** Player_4, following someone only tells me who they visited, so I didn't see any other details about player_2's visit to player_9. My ability doesn't show what happened during the visit itself, just the destination.

**The message — player_9 (proactive round):**

> Player_6, you're right that my watch was on player_3, so I couldn't see player_2 visit me. Player_7's tracking of player_2 to my door matches a dead role, which makes player_7's claim worth keeping track of.

**Whom does player_9's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 611

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "c01:d2:s15", "type": "message", "accused": _}
]
```