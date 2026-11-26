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

# Case 438

### Item b06:d3:s7

Game b06, day 3.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 2:
    player_1 voted to abstain
    player_2 voted to abstain
    player_3 voted to eliminate player_8
    player_4 voted to eliminate player_8
    player_5 voted to eliminate player_8
    player_6 voted to abstain
    player_7 voted to abstain
    player_8 voted to abstain
    player_9 voted to eliminate player_8
  The town chose to abstain. No one is eliminated today.

- **game_master:** Night of day 2: player_1 was attacked by the wolves but was saved by the healer!

*Opening round: every player speaks at once, so player_8 had heard no other line today.*

**The message — player_8 (opening round):**

> I need to clear up my claim from yesterday since I am actually the Sigilist, not the Sentinel, which likely makes player_9 the true Sentinel.

**Whom does player_8's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 438

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "b06:d3:s7", "type": "message", "accused": _}
]
```

---

# Case 453

### Item b06:d4:s13

Game b06, day 4.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 3:
    player_1 voted to eliminate player_5
    player_2 voted to eliminate player_8
    player_3 voted to eliminate player_8
    player_4 voted to eliminate player_8
    player_5 voted to eliminate player_8
    player_6 voted to eliminate player_8
    player_7 voted to eliminate player_8
    player_8 voted to eliminate player_5
    player_9 voted to eliminate player_8
  Player player_8 has been voted out and was a sigilist.
  The record of player_8, the sigilist: night 1, set a sigil on player_1, who did not attack.

- **game_master:** Night of day 3: player_3 was killed by the wolves last night. Their role is hidden by an illusionist.

**Today, before this message:**

- **player_1:** On night 3, my action was blocked and I learned nothing.

- **player_7:** On night three, I protected player_1 again, and no attack was reported.

- **player_9:** On night three, I watched player_1 and saw that player_4 and player_7 both visited them.

- **player_4:** Player 9, seeing my visit on player_1 doesn't automatically make me suspicious when we are all trying to figure out who is who. I wanted to check player_1's interactions directly since their investigator claims have been heavily targeted by night actions.

- **player_5:** Player 4 checking player_1 makes sense given how much pressure is on that claim. Since player_1 also mentioned being roleblocked last night, we should look closer at who is distributing those blocks instead of just assuming every visit is malicious.

- **player_1:** Player 9, if you watched me last night, you left out whoever roleblocked me since blocking counts as a visit. Between player 7's protection and player 4's visit, that roleblocker makes a third visitor you missed.

- **player_9:** I only saw player_4 and player_7 at your door last night, player_1. If blocking is a visit like the rules say, your claim about being roleblocked doesn't match what I actually watched.

**The message — player_1 (discussion round):**

> If blocking counts as a visit, player_9, you should have seen the person who roleblocked me last night. Missing that third visitor pokes a massive hole in your sentinel claim and makes your story fall apart.

**Whom does player_1's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 453

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "b06:d4:s13", "type": "message", "accused": _}
]
```

---

# Case 483

### Item b07:d2:s11

Game b07, day 2.

**Since the last discussion:**

- **game_master:** There is no vote on day 1, so no one voted and no one is eliminated.

- **game_master:** Night of day 1: player_3 was stabbed by the serial killer last night. They were a illusionist. player_7 was killed by the wolves last night. Their role is hidden by an illusionist.

**Today, before this message:**

- **player_4:** I followed player_9 last night and saw them visit player_2.

- **player_6:** I am the investigator, and on night 1 I checked player_5, who came up suspicious.

- **player_8:** Last night I watched player_9 and saw that player_4 visited them.

- **player_9:** On night 1, I placed a sigil on player_2, and they did not attack.

- **player_1:** Player 6, if your investigator check on player 5 came up suspicious, that points right at player 5 for the remaining wolf since the illusionist is already dead. Meanwhile, player 4 and player 8 line up cleanly on player 9's movements.

- **player_5:** Player 6 claiming I'm suspicious is awfully convenient when they could easily be a wolf trying to railroad me. We have a dead illusionist and people throwing around wild checks, so let's look closer at player 6 before jumping on me.

**The message — player_6 (discussion round):**

> Calling it a convenient railroad doesn't make a night one investigator check go away, player_5. If you're town, explain why else my check would flag you.

**Whom does player_6's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 483

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "b07:d2:s11", "type": "message", "accused": _}
]
```

---

# Case 516

### Item b08:d3:s9

Game b08, day 3.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 2:
    player_1 voted to eliminate player_8
    player_2 voted to eliminate player_8
    player_3 voted to eliminate player_8
    player_4 voted to eliminate player_8
    player_5 voted to eliminate player_8
    player_7 voted to eliminate player_8
    player_8 voted to abstain
    player_9 voted to eliminate player_8
    player_10 voted to eliminate player_8
  Player player_8 has been voted out and was a chanteuse.

- **game_master:** Night of day 2: No one died last night.

**Today, before this message:**

- **player_2:** Last night, on night 2, I followed player_9 and learned that player_9 visited player_2.

- **player_5:** Last night, on night 2, I placed a sigil on player_9, and they did not attack.

- **player_7:** On night two, I watched player_9 and saw that both player_2 and player_5 visited them.

- **player_10:** I am the investigator. On night 2, I checked player_1 and they came back suspicious.

- **player_1:** Player_10 calling me suspicious right out of the gate feels like a convenient push to get an easy elimination. If you actually checked me, why drop this now instead of looking at the tangled web of visits around player_9?

**The message — player_10 (discussion round):**

> I'm sharing my result now because dropping hard information is how town actually makes progress, player_1. Pointing at player_9's visits doesn't change the fact that my check on you came back suspicious.

**Whom does player_10's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 516

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "b08:d3:s9", "type": "message", "accused": _}
]
```

---

# Case 534

### Item b08:d4:s16

Game b08, day 4.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 3:
    player_1 voted to eliminate player_10
    player_2 voted to eliminate player_1
    player_3 voted to eliminate player_1
    player_4 voted to eliminate player_1
    player_5 voted to eliminate player_1
    player_7 voted to eliminate player_1
    player_9 voted to eliminate player_1
    player_10 voted to eliminate player_1
  Player player_1 has been voted out and was a illusionist.

- **game_master:** Night of day 3: player_10 was attacked by the wolves but was saved by the healer!

**Today, before this message:**

- **player_2:** Last night on night 3, I followed player_3, and they visited no one.

- **player_7:** Last night I watched player_3, and player_2 visited them.

- **player_9:** I can confirm that last night on Night 3, I targeted player_10 with my protection, which is why they survived the wolf attack.

- **player_10:** Last night on night 3, I checked player_9, and they read not suspicious.

- **player_3:** I can confirm player_2 and player_7's accounts—I stayed home last night and made no visits. With player_9 confirmed as the healer after saving player_10 last night, our town power roles are starting to line up nicely.

- **player_2:** I can back up player_9's healer claim from my own night action. On night 2 I followed player_9, and my result confirms they visited me just as they claimed. Combined with saving player_10 last night, player_9's track record is fully verified.

- **player_5:** Player_4, you haven't shared anything about your nights yet while the rest of us mapped out our roles. What role are you claiming?

- **player_4:** I've been holding my fire as the vigilante because the town has active protective roles and a mistaken shot would hurt us. Since everyone is laying out their claims today, I figured it was time to step in and share my position.

- **player_7:** Player_5's claim checks out with my logs as well. On night 2 I watched player_9 and saw player_5 visit them, which matches their sigilist claim perfectly.

**The message — player_10 (proactive round):**

> Player_7 and player_2's tracking logs match up on player_3 staying put, and player_9's protection of me last night checks out with the healer save. That leaves player_4's delayed vigilante claim as something we should evaluate more closely.

**Whom does player_10's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 534

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "b08:d4:s16", "type": "message", "accused": _}
]
```