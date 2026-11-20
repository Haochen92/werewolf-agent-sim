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

# Case 728

### Item c05:d4:s5

Game c05, day 4.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 3:
    player_1 voted to eliminate player_6
    player_3 voted to eliminate player_10
    player_6 voted to eliminate player_8
    player_8 voted to eliminate player_1
    player_9 voted to eliminate player_8
    player_10 voted to eliminate player_1
  It's a tie between ['player_8', 'player_1']. No one is voted out this day.

- **game_master:** Night of day 3: player_1 was killed by the wolves last night. Their role is hidden by an illusionist. player_8 was attacked by the serial killer and a sigil last night. They were a chanteuse.

**Today, before this message:**

- **player_9:** I am the Sigilist, and I placed my sigil on player_8 last night, which is why it successfully triggered and struck them.

- **player_3:** Player 9's claim that they sigil-struck player_8 matches what the morning report said about the attack. That makes player_9 likely the real sigilist, which leaves player_6 and player_10 as the ones we need to look at.

**The message — player_6 (proactive round):**

> Player 3, accepting player 9's claim just because it fits the public report is a bit rushed, since anyone could claim that after reading the morning text. We need more than matching the report to clear someone completely.

**Whom does player_6's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 728

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "c05:d4:s5", "type": "message", "accused": _}
]
```

---

# Case 737

### Item c06:d2:s11

Game c06, day 2.

**Since the last discussion:**

- **game_master:** There is no vote on day 1, so no one voted and no one is eliminated.

- **game_master:** Night of day 1: player_4 was killed by the wolves last night. Their role is hidden by an illusionist. player_5 was struck down by a sigil last night. They were a chanteuse.

**Today, before this message:**

- **player_2:** I tried to follow player_4 last night, but I was roleblocked and learned nothing. With player_5 being the Chanteuse and now dead, at least that blocking threat is gone.

- **player_3:** I am the Sigilist, and I placed my sigil on player_5 last night, which is what struck them down and proves they were carrying the wolf attack.

- **player_10:** On night one I watched player_4, and saw that both player_5 and player_6 visited them.

- **player_1:** Player_10 saw player_6 visit player_4 last night right along with the wolf player_5. Since player_4 was the kill, player_6 being there needs explaining—could they be the Illusionist covering the tracks or part of the team?

- **player_6:** I visited player_4 because I used my Trailseer ability to follow them last night, which is why player_10 saw me there. I learned they didn't visit anyone, but player_1 is jumping to conclusions by painting me as a wolf just for investigating the victim.

**The message — player_8 (proactive round):**

> We have a clear contradiction between player_2 and player_6, as both are claiming the Trailseer role. Player_2 claims they were blocked trying to follow player_4, whereas player_6 claims they successfully followed player_4.

**Whom does player_8's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 737

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "c06:d2:s11", "type": "message", "accused": _}
]
```

---

# Case 773

### Item c06:d5:s9

Game c06, day 5.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 4:
    player_3 voted to eliminate player_8
    player_7 voted to eliminate player_8
    player_8 voted to eliminate player_7
    player_9 voted to eliminate player_8
    player_10 voted to eliminate player_8
  Player player_8 has been voted out and was a fortune teller.

- **game_master:** Night of day 4: player_3 was killed by the wolves last night. They were a sigilist. The record of player_3, the sigilist: night 1, set a sigil on player_5, who attacked and was struck down; night 3, set a sigil on player_7; it had no effect.

**Today, before this message:**

- **player_7:** With only three of us left, we really need to re-examine everyone's claims before we commit to a vote. Player_9 and Player_10, let's hear how you reconcile the remaining roles on board.

- **player_9:** Player_10 has verified their sentinel role through consistent night records, and I am the investigator. That leaves Player_7 as the necromancer holding the final threat against us, since all other town roles are accounted for.

- **player_7:** If you are both so certain town is fully accounted for, why did your investigation on player_6 only happen after the wagon was already moving? It is awfully convenient how your results always magically match whatever narrative player_10 is pushing.

- **player_9:** I checked player_6 on night two because their trailseer claim fell apart under scrutiny. Catching an illusionist isn't some magical coordination with player_10, it is simply an investigative result coming to light right when the town needed to see the truth.

- **player_7:** You two have locked arms so tightly that neither of you ever has to prove anything independently. If Player_10 was really watching everything, why didn't they catch who was interfering earlier instead of just echoing Player_9's late investigations? One of you is deflecting to secure a safe endgame.

- **player_9:** Player_10's watches mapped out actual night visits on earlier rounds while you abstained and deflected, player_7. Your desperate attempts to drive a wedge between us only highlight that you are the last threat standing as the necromancer.

**The message — player_10 (discussion round):**

> My watches weren't just echoing anything, player_7; night one caught the exact visits by the dead wolves player_5 and player_6 at player_4's door. Player_9's check on player_6 just lined up with the visits I tracked. You are deflecting because my hard tracking backs up the investigator instead of your evasions.

**Whom does player_10's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 773

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "c06:d5:s9", "type": "message", "accused": _}
]
```

---

# Case 788

### Item d01:d3:s2

Game d01, day 3.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 2:
    player_1 voted to abstain
    player_3 voted to eliminate player_9
    player_4 voted to abstain
    player_5 voted to eliminate player_6
    player_6 voted to abstain
    player_7 voted to abstain
    player_8 voted to abstain
    player_9 voted to abstain
    player_10 voted to eliminate player_9
  The town chose to abstain. No one is eliminated today.

- **game_master:** Night of day 2: player_4 was attacked by the wolves but was saved by the healer!

*Opening round: every player speaks at once, so player_4 had heard no other line today.*

**The message — player_4 (opening round):**

> On night two, I followed player_9 and saw them visit player_4, which is the exact person the wolves attacked.

**Whom does player_4's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 788

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "d01:d3:s2", "type": "message", "accused": _}
]
```

---

# Case 797

### Item d01:d4:s2

Game d01, day 4.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 3:
    player_1 voted to eliminate player_3
    player_3 voted to eliminate player_6
    player_4 voted to eliminate player_3
    player_5 voted to eliminate player_6
    player_6 voted to eliminate player_5
    player_7 voted to eliminate player_3
    player_8 voted to eliminate player_3
    player_9 voted to eliminate player_3
    player_10 voted to eliminate player_5
  Player player_3 has been voted out and was a illusionist.

- **game_master:** Night of day 3: player_1 was attacked by the wolves but was saved by the healer! player_5 was shot by the vigilante last night. They were a necromancer. player_9 was killed by the wolves last night. They were a healer. The record of player_9, the healer: night 1, protected player_7; no attack on them was announced; night 2, protected player_4, who was attacked and saved.

*Opening round: every player speaks at once, so player_6 had heard no other line today.*

**The message — player_6 (opening round):**

> I am the Vigilante, and I'm the one who took out player_5 last night.

**Whom does player_6's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 797

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "d01:d4:s2", "type": "message", "accused": _}
]
```