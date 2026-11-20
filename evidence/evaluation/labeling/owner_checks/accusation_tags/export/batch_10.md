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

# Case 1090

### Item e03:d4:s14

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

- **player_8:** Player_1 claims the sigilist role now, but waited until pressed to say anything about their position. If player_7 is the vigilante who shot player_3, player_1's hesitation and sudden claim look like an attempt to duck the vote. We should look closely at player_1.

- **player_1:** I held my claim to protect the sigilist ability from being targeted early. If you're truly the healer, why are you deflecting onto my silence instead of questioning player_7 shooting the fortune teller?

- **player_8:** Player_1, you waited until the very end to drop a sigilist claim while offering zero help earlier. Player_7 confirmed their shot, so we need to look at who is actually hiding behind sudden claims. Your silence speaks volumes.

- **player_7:** I shot player_3 to ensure we eliminated a threat and confirmed their role. Now it comes down to player_1 and player_8 claiming sigilist and healer at the very last minute. One of you is the serial killer, and we have to vote out the right person today or we lose.

- **player_1:** The game master's report confirmed player_7 was the vigilante who shot player_3, verifying their claim. Since player_7 is cleared as town, player_8 has to be our serial killer and needs to go today.

- **player_8:** Player_7, your shot on player_3 is confirmed, but player_1 only claimed sigilist when the walls closed in. If I were the serial killer, I wouldn't have protected you last night. Player_1 is just trying to dodge the vote.

- **game_master:** Before the vote: player_1 and player_8 each get a last word.

- **player_1:** My delay in claiming sigilist was solely to protect my ability from being targeted prematurely, not an attempt to dodge the vote. Player_7's role is fully confirmed by the night report, and I am the town sigilist holding our final piece. Everything points to my innocence once you look past the timing of my claim.

**The message — player_8 (closing round):**

> If I were the serial killer, I wouldn't have used my protection on player_7 last night when they were exposed as the shooter. Player_1 waited until the very end to drop a sigilist claim without any corroborating action. Look at who actually stepped up to help keep town safe instead of hiding behind a late claim.

**Whom does player_8's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 1090

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "e03:d4:s14", "type": "message", "accused": _}
]
```

---

# Case 1120

### Item e05:d2:s11

Game e05, day 2.

**Since the last discussion:**

- **game_master:** There is no vote on day 1, so no one voted and no one is eliminated.

- **game_master:** Night of day 1: player_4 was killed by the wolves last night. Their role is hidden by an illusionist. player_7 was stabbed by the serial killer last night. They were a vigilante.

**Today, before this message:**

- **player_2:** For what it's worth, I can share that player_6 visited player_1 last night.

- **player_5:** On night one I watched player_4, and player_10 was the only person who visited them.

- **player_6:** I checked player_1 last night, and they came back not suspicious.

- **player_1:** Player_5, since the illusionist hid the wolf kill on player_4, shouldn't the carrier's visit have been hidden from your watch? If you still saw player_10 there, player_10 might be the illusionist rather than the killing wolf.

- **player_5:** That's a good catch by player_1. Since the illusionist's body-hiding ability counts as a visit to the victim, player_10 is likely the illusionist rather than the wolf carrier. That means we should look elsewhere for the actual killer.

**The message — player_8 (proactive round):**

> Player_2 backing up player_6's visit to player_1 gives player_6's investigator claim weight, meaning player_1 is likely clear.

**Whom does player_8's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 1120

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "e05:d2:s11", "type": "message", "accused": _}
]
```

---

# Case 1136

### Item e05:d3:s11

Game e05, day 3.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 2:
    player_1 voted to eliminate player_10
    player_2 voted to eliminate player_10
    player_3 voted to eliminate player_10
    player_5 voted to eliminate player_10
    player_6 voted to eliminate player_10
    player_8 voted to eliminate player_10
    player_9 voted to eliminate player_10
    player_10 voted to abstain
  Player player_10 has been voted out and was a illusionist.

- **game_master:** Night of day 2: player_5 was attacked by the wolves and the serial killer last night. They were a sentinel. The record of player_5, the sentinel: night 1, watched player_4; saw player_10 visit them. The Speculator has picked Town.

**Today, before this message:**

- **player_2:** Last night on night 2 I followed player_3, and I learned that they visited player_5 and player_1.

- **player_6:** On night 2 I checked player_5, and they read not suspicious.

- **player_1:** Player_2, since you said player_3 visited both player_5 and player_1 last night, player_3 needs to explain what they were doing at my door. That is two very different targets for a single night.

- **player_3:** Player_1, claiming I visited two different people in one night doesn't make any sense. Player_2 is fabricating claims to put pressure on me.

- **player_8:** Player_3 visiting two different people on night 2 is definitely worth looking into, especially since player_5 was the wolf target. If player_3 is a wolf, that dual activity lines up with a pack ability.

- **player_3:** Player_8, you are buying into a story that doesn't add up. Player_2 claiming I visited two different people in one night is completely fabricated to put a target on my back.

- **player_9:** Player_6, you mentioned checking player_5 on night 2 right before they died. Since player_5 was targeted by both wolves and the serial killer that same night, did your check happen before or after the attack occurred?

**The message — player_2 (proactive round):**

> Player_1, I can confirm what I saw: player_3 went to both player_5 and player_1. Since player_5 was hit by the wolves that same night, player_3 visiting them alongside another stop strongly points to a wolf utilizing a pack ability.

**Whom does player_2's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 1136

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "e05:d3:s11", "type": "message", "accused": _}
]
```

---

# Case 1159

### Item e06:d4:s7

Game e06, day 4.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 3:
    player_1 voted to eliminate player_2
    player_2 voted to eliminate player_4
    player_3 voted to eliminate player_2
    player_4 voted to eliminate player_2
    player_5 voted to eliminate player_2
    player_6 voted to eliminate player_2
    player_8 voted to eliminate player_2
    player_9 voted to eliminate player_2
  Player player_2 has been voted out and was a investigator.
  The record of player_2, the investigator: night 1, was roleblocked; night 2, checked player_4: Suspicious.

- **game_master:** Night of day 3: player_3 was attacked by the wolves but was saved by the healer! player_4 was struck down by a sigil last night. They were a chanteuse.

**Today, before this message:**

- **player_3:** I placed my final sigil on player_4 last night, which is what triggered the strike that took down the chanteuse.

**The message — player_5 (proactive round):**

> Player_3, you led the charge to lynch player_2 yesterday. Now that we know player_2 was the real investigator who correctly checked player_4 as suspicious, pushing that lynch looks awfully convenient for the wolves.

**Whom does player_5's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 1159

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "e06:d4:s7", "type": "message", "accused": _}
]
```

---

# Case 1165

### Item e06:d5:s5

Game e06, day 5.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 4:
    player_1 voted to eliminate player_5
    player_3 voted to eliminate player_5
    player_5 voted to eliminate player_3
    player_6 voted to eliminate player_5
    player_8 voted to eliminate player_5
    player_9 voted to eliminate player_5
  Player player_5 has been voted out and was a trailseer.
  The record of player_5, the trailseer: night 1, followed player_1; they visited no one; night 2, was roleblocked; night 3, was roleblocked.

- **game_master:** Night of day 4: player_6 was killed by the wolves last night. They were a healer. The record of player_6, the healer: night 1, protected player_8; no attack on them was announced; night 2, protected player_3; no attack on them was announced; night 3, protected player_3, who was attacked and saved.

**Today, before this message:**

- **player_1:** Player 3's sigil caught the chanteuse, so player 3 is our confirmed sigilist. That leaves player 8 and player 9 as the remaining pool for the wolves or the necromancer.

**The message — player_3 (proactive round):**

> Player 1 makes a fair point about narrowing things down to player 8 and player 9. Let's look closely at how the votes split on day 4 when player 5 was eliminated to see who pushed hardest there and who might be hiding.

**Whom does player_3's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 1165

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "e06:d5:s5", "type": "message", "accused": _}
]
```