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

# Case 0

### Item f01:d2:s15

Game f01, day 2.

**Since the last discussion:**

- **game_master:** There is no vote on day 1, so no one voted and no one is eliminated.

- **game_master:** Night of day 1: player_1 was stabbed by the serial killer last night. They were a chanteuse.

*No line was heard today before this message.*

**The message — player_8 (proactive round):**

> It's a massive break for us that the Serial Killer took out a wolf on night one. Since player_1 was the Chanteuse, their block went through before they died. If anyone was blocked or has investigative info, now is the time to start sharing so we can build some leads.

**Whom does player_8's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 0

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "f01:d2:s15", "type": "message", "accused": _}
]
```

---

# Case 61

### Item f02:d4:s1

Game f02, day 4.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 3:
    player_1 voted to eliminate player_10
    player_3 voted to eliminate player_10
    player_5 voted to eliminate player_10
    player_6 voted to eliminate player_10
    player_7 voted to eliminate player_10
    player_9 voted to eliminate player_10
    player_10 voted to eliminate player_1
  Player player_10 has been voted out and was a illusionist.

- **game_master:** Night of day 3: player_6 was killed by a reanimated wolf last night. Their role is hidden by a reanimated illusionist.

*Opening round: every player speaks at once, so player_3 had heard no other line today.*

**The message — player_3 (opening round):**

> I am the Trailseer. I followed player_9 on Night 1, player_10 on Night 2, and player_7 on Night 3, and my results show that none of them made any visits on those nights.

**Whom does player_3's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 61

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "f02:d4:s1", "type": "message", "accused": _}
]
```

---

# Case 71

### Item f02:d4:s15

Game f02, day 4.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 3:
    player_1 voted to eliminate player_10
    player_3 voted to eliminate player_10
    player_5 voted to eliminate player_10
    player_6 voted to eliminate player_10
    player_7 voted to eliminate player_10
    player_9 voted to eliminate player_10
    player_10 voted to eliminate player_1
  Player player_10 has been voted out and was a illusionist.

- **game_master:** Night of day 3: player_6 was killed by a reanimated wolf last night. Their role is hidden by a reanimated illusionist.

**Today, before this message:**

- **player_3:** I am the Trailseer. I followed player_9 on Night 1, player_10 on Night 2, and player_7 on Night 3, and my results show that none of them made any visits on those nights.

- **player_1:** player_3, your claim has a major contradiction. You claim you followed player_10 on Night 2 and they made no visits. But on Night 2, player_2 was killed and their role was hidden by the Illusionist. The Illusionist's visit to hide a body is always visible to a Trailseer, meaning player_10 had to have visited player_2. Since you claim they didn't, you are lying and must be our Necromancer.

- **player_3:** player_1, you're jumping to conclusions to frame me. My results are exactly what the Game Master gave me: player_10 did not make a visit on Night 2. If the Illusionist didn't visit, or if there's another mechanic at play that explains this, my track still stands as factual. Your desperate attempt to twist this into a Necromancer accusation makes you look like the real killer trying to get the last Town investigative role executed.

- **player_5:** player_1 is completely right about the mechanics here. The Illusionist's own visit to hide a body is never hidden by the illusion itself—only the carrier's is. Since player_4 was already voted out on Day 2, there was no Chanteuse alive on Night 2 to block you, player_3. Your track on player_10 is mathematically and mechanically impossible, which means you are definitely lying about being the Trailseer.

- **player_3:** player_5, you and player_1 are assuming we have perfect information about how the night resolved. If player_10 carried the kill and used their own ability on the same target, the concealment rules might have hidden the entire visit. Pushing a mechanical 'contradiction' to execute the only claimed investigative role when we have a Necromancer on the loose is exactly how evils win this.

- **player_1:** player_3, the rules are clear: the Illusionist's own visit to hide the victim is always seen by a Trailseer, even if they also carried the kill. There is no mechanic that hides the Illusionist's own visit. You fabricated your report because you are the Necromancer.

- **player_3:** player_1, you are assuming we have a perfect, textbook understanding of how every role interaction resolved on Night 2. If my result from the Game Master says player_10 didn't visit, then that is the factual result I received. By trying to force a execution based on 'mechanical impossibility' instead of looking at who actually benefits from clearing the last Town investigator, you and player_5 are exposing yourselves as the real threats.

- **player_1:** player_3, trying to brush off the rules as 'textbook assumptions' won't save you. The game rules are absolute: an Illusionist's visit to hide a body is never hidden from a Trailseer. Since player_10 hid player_2 that night, your track is mathematically impossible. Both wolves are already dead, which makes you our Necromancer.

- **player_5:** player_3, trying to hand-wave the game rules as 'textbook assumptions' doesn't work. The rules are absolute in this setup: the Illusionist's own visit to hide a body is never hidden and is always seen by a Trailseer. Since player_10 hid the body, they visited. You fabricated a track, and no amount of deflecting changes that mechanical fact.

- **player_3:** player_5, you are assuming we have a complete grasp of every interaction. If player_10 was somehow stopped, or if another mechanic explains why they didn't visit, executing the only active investigator based on your textbook assumptions is a massive mistake. player_1 is pushing this way too eagerly, and your immediate agreement looks like coordinated evil trying to finish us off.

**The message — player_9 (proactive round):**

> Player_7, we need you to weigh in on this. Player_1 and player_5 have laid out a clear mechanical contradiction in player_3's claim, and your silence makes it hard to coordinate our final votes. What is your read on player_3's defense?

**Whom does player_9's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 71

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "f02:d4:s15", "type": "message", "accused": _}
]
```

---

# Case 89

### Item f03:d2:s16

Game f03, day 2.

**Since the last discussion:**

- **game_master:** There is no vote on day 1, so no one voted and no one is eliminated.

- **game_master:** Night of day 1: player_3 was stabbed by the serial killer last night. They were a sentinel.

**Today, before this message:**

- **player_7:** I am the Trailseer. Last night I followed player_8, and my result shows they visited me.

- **player_2:** That is a very specific result from player_7. player_8, did you actually visit player_7 last night, and if so, can you explain what your role's business was with them without fully claiming if you don't have to?

- **player_8:** Yes, I did visit player_7. I'm the Sigilist, and I placed a sigil on them last night. Since it had no effect, we know player_7 didn't attack anyone, which aligns with them being the Trailseer who spent the night following me.

- **player_5:** The interaction between player_7 and player_8 is incredibly clean. A Trailseer following someone who happened to place a sigil on them creates a perfect loop that is very hard for evil roles to fake-claim on the spot without coordination. We should treat them both as highly likely Town for now.

- **player_9:** The interaction between player_7 and player_8 definitely feels genuine and gives us a solid starting point. With player_3 gone, we need to be careful, so I'd like to hear from some of the quieter folks. player_6, what are your thoughts on the claims so far?

**The message — player_6 (discussion round):**

> I think the interaction between player_7 and player_8 looks highly genuine. It is incredibly risky for two evils to coordinate a specific claim like that so early on. Having two strong town leads this early gives us a great starting core to build on.

**Whom does player_6's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 89

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "f03:d2:s16", "type": "message", "accused": _}
]
```

---

# Case 128

### Item f04:d3:s16

Game f04, day 3.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 2:
    player_1 voted to abstain
    player_2 voted to abstain
    player_3 voted to abstain
    player_5 voted to abstain
    player_6 voted to abstain
    player_7 voted to abstain
    player_8 voted to abstain
    player_9 voted to abstain
    player_10 voted to abstain
  The town chose to abstain. No one is eliminated today.

- **game_master:** Night of day 2: player_5 was killed by the wolves last night. Their role is hidden by an illusionist. player_10 was shot by a reanimated vigilante last night. They were a chanteuse.

**Today, before this message:**

- **player_6:** I am the Investigator. I checked player_3 on Night 1 and they are Not suspicious, but last night I checked player_8 and they are Suspicious.

- **player_8:** player_6, that is a blatant lie. I am town, and your supposed 'investigation' is completely fabricated. With the Chanteuse dead, you wolves are clearly desperate to push a fake result and get an easy mislynch today.

- **player_6:** player_8, of course you're calling me a liar—any wolf caught red-handed would do the same. I have no reason to fabricate a guilty result on Day 3 and put myself in the spotlight. The town needs to trust the hard info: player_8 is suspicious, and we should lynch them today.

- **player_8:** player_6, if you were a real Investigator, you would know that pushing an immediate lynch based on a single result on Day 3—especially when we just had a hidden role death last night—is incredibly reckless. You're desperate to rush this vote because you're a wolf trying to capitalize on a fabricated accusation before the town can piece together what happened to player_5.

- **player_6:** player_8, calling a definitive guilty report 'reckless' is just a standard wolf tactic to buy another night. Why would an Investigator hide a confirmed guilty result while the wolves and the Necromancer whittle us down? The town needs to act on real info, and you are suspicious.

- **player_2:** player_6's result actually makes perfect sense if we look at player_10's death. Since player_10 was shot by a reanimated vigilante, we know the Necromancer attacked last night, which makes them register as Suspicious. If player_6 is telling the truth, player_8 is highly likely to be our Necromancer.

- **player_8:** player_2, you are helping player_6 spin a dangerous narrative. They saw the 'reanimated vigilante' announcement this morning and realized they could use it as perfect cover to fake a 'Suspicious' result on me. It is incredibly easy for a wolf to claim Investigator and frame someone as the Necromancer right after a reanimated kill is publicly announced.

- **player_3:** Player_6's Night 1 result on me is correct—I am indeed town. However, we shouldn't let that completely clear them. A wolf or illusionist knows exactly who is not in their pack, making it incredibly easy to hand out a correct 'Not suspicious' check on Night 1 just to build enough trust to push a fake 'Suspicious' result on Day 3.

**The message — player_9 (proactive round):**

> Building on player_3's caution, we can actually verify if player_6 is telling the truth without blindly guessing. Since player_6 claims to have investigated player_8 last night, that would be a visit. If we have a Trailseer who followed player_6, or a Sentinel who watched player_8, they can confirm if that visit actually happened.

**Whom does player_9's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 128

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "f04:d3:s16", "type": "message", "accused": _}
]
```