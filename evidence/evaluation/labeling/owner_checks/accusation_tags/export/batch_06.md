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

# Case 639

### Item c02:d4:s7

Game c02, day 4.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 3:
    player_3 voted to eliminate player_7
    player_5 voted to eliminate player_7
    player_6 voted to eliminate player_10
    player_7 voted to eliminate player_5
    player_8 voted to eliminate player_10
    player_9 voted to eliminate player_7
    player_10 voted to eliminate player_5
  Player player_7 has been voted out and was a serial killer.

- **game_master:** Night of day 3: player_8 was killed by the wolves last night. They were a trailseer. The record of player_8, the trailseer: night 1, followed player_4; they visited player_7; night 2, followed player_1; they visited no one.

**Today, before this message:**

- **player_6:** Last night on night 3, I watched player_5 and no one visited them.

- **player_3:** Player_6's watch on player_5 gives us a clean slate there for visits. We still need to look closely at everyone's voting records from the past days to find the remaining wolves.

- **player_5:** That clean slate on me is reassuring, but player_3 is right that we need to comb through past voting records to track down whoever is left. Let's look closely at who pushed hardest during those tied votes.

**The message — player_9 (proactive round):**

> If player_6 is indeed the sentinel, we have a solid base to work from. Player_10, your vote against player_5 on day 3 is curious, especially since player_5 was helping us track the serial killer. Could you clarify why you chose that target?

**Whom does player_9's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 639

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "c02:d4:s7", "type": "message", "accused": _}
]
```

---

# Case 688

### Item c03:d6:s6

Game c03, day 6.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 5:
    player_2 voted to eliminate player_4
    player_3 voted to eliminate player_4
    player_4 voted to eliminate player_2
    player_5 voted to eliminate player_4
    player_7 voted to eliminate player_4
    player_8 voted to eliminate player_4
  Player player_4 has been voted out and was a speculator.

- **game_master:** Night of day 5: player_2 was killed by the wolves last night. They were a investigator. The record of player_2, the investigator: night 1, checked player_1: Not suspicious; night 2, checked player_10: Suspicious.

**Today, before this message:**

- **player_3:** On night 5, I followed player_5, and they visited no one.

- **player_5:** Player_3 must be mistaken or fabricating that report, because as the healer I definitely sent my protection out last night. If they really followed me and saw nothing, maybe they're trying to push a false narrative now that numbers are so low.

- **player_3:** Protecting requires a visit, player_5, but my trailseer report from last night shows you visited no one. If you were truly acting as the healer, you would have had to visit someone to protect them. That contradiction makes it pretty clear you aren't who you claim to be.

**The message — player_5 (discussion round):**

> Player_3, your trailseer report is awfully convenient for pushing a lynch, but targeting me ignores how quiet player_7 and player_8 have been. We need to scrutinize everyone's overall position instead of accepting your night log at face value.

**Whom does player_5's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 688

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "c03:d6:s6", "type": "message", "accused": _}
]
```

---

# Case 708

### Item c04:d4:s9

Game c04, day 4.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 3:
    player_1 voted to eliminate player_6
    player_2 voted to eliminate player_10
    player_3 voted to eliminate player_6
    player_4 voted to eliminate player_8
    player_5 voted to eliminate player_6
    player_6 voted to eliminate player_4
    player_7 voted to eliminate player_1
    player_8 voted to eliminate player_6
    player_10 voted to eliminate player_6
  Player player_6 has been voted out and was a illusionist.

- **game_master:** Night of day 3: player_5 was attacked by the wolves and the wolves last night. They were a investigator. The record of player_5, the investigator: night 1, checked player_1: Not suspicious; night 2, checked player_2: Not suspicious. player_7 was shot by the vigilante last night. They were a fortune teller.

**Today, before this message:**

- **player_2:** I am the sigilist. I placed a sigil on player_10 last night, and it had no effect, which is consistent with them not performing an attack.

- **player_10:** On night 3, I watched the investigator, player_5, and saw both player 4 and the now-confirmed illusionist, player 6, visit them. Given that the investigator was killed that same night, player 4 needs to explain exactly why they visited player 5.

- **player_4:** Player_10, your accusation is simply false. I spent that entire night blocking player_8, not visiting the investigator. If you truly watched player_5 and saw me there, you either have a broken watch or you are intentionally lying to deflect attention from your own role. Everyone should consider why a Sentinel would be so eager to frame someone else right now.

- **player_10:** Player 4, your defense is incriminating. The ability to block night actions belongs specifically to the Chanteuse, a wolf role. By claiming you spent your night blocking someone, you have just admitted to being a wolf.

- **player_4:** You're taking a clear slip of the tongue and spinning it into a conviction. I misspoke when I said 'block'—I meant I was taking a defensive action to check or protect player 8. It's desperate to jump on a word choice to avoid answering why you're so focused on my record while ignoring the roles actually in play. Why are you so eager to frame someone before we've even looked at other possibilities?

**The message — player_10 (discussion round):**

> You don't just accidentally say you were blocking someone when that's a precise role ability. My watch caught you directly at the investigator's door the exact night they were killed, and your weak backtracking doesn't erase that obvious wolf slip.

**Whom does player_10's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 708

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "c04:d4:s9", "type": "message", "accused": _}
]
```

---

# Case 712

### Item c04:d5:s7

Game c04, day 5.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 4:
    player_1 voted to eliminate player_4
    player_2 voted to eliminate player_4
    player_3 voted to eliminate player_4
    player_4 voted to eliminate player_10
    player_8 voted to eliminate player_4
    player_10 voted to eliminate player_4
  Player player_4 has been voted out and was a chanteuse.

- **game_master:** Night of day 4: No one died last night.

**Today, before this message:**

- **player_8:** With the wolves removed, our focus must shift entirely to the Necromancer. Since the Necromancer can use the abilities of dead players, we need to be vigilant about any unusual night activity. I have been focusing my protection on player_10 to ensure their sentinel reports remain consistent.

- **player_1:** Player_8 claiming protection on player_10 locks down two claims, assuming they are both town. That leaves player_3 as the primary quiet player we need to press for reads today.

- **player_2:** Player_8 claiming protection on player_10 lines up with player_10's sentinel claim. Since player_10 didn't trigger my sigil on night three either, their passive role-keeping checks out so far.

**The message — player_3 (proactive round):**

> I've been quiet while evaluating how neatly player_8 and player_10 locked their claims together. Since player_1 is pressing me for reads without offering their own role, I'll note that I've been tracking player movements as the trailseer to ensure no anomalies slipped by.

**Whom does player_3's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 712

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "c04:d5:s7", "type": "message", "accused": _}
]
```

---

# Case 725

### Item c05:d3:s11

Game c05, day 3.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 2:
    player_1 voted to eliminate player_8
    player_2 voted to eliminate player_3
    player_3 voted to abstain
    player_6 voted to abstain
    player_7 voted to abstain
    player_8 voted to abstain
    player_9 voted to abstain
    player_10 voted to eliminate player_3
  The town chose to abstain. No one is eliminated today.

- **game_master:** Night of day 2: player_2 was stabbed by the serial killer last night. They were a vigilante. The record of player_2, the vigilante: night 1, held fire. player_7 was killed by the wolves last night. Their role is hidden by an illusionist.

**Today, before this message:**

- **player_1:** On night 2 I attempted to follow player_7, but my action was blocked.

- **player_6:** If player_1 was blocked following player_7 on night 2, that lines up with the wolves silencing anyone looking into their target. It suggests the wolves definitely wanted player_7's final night interactions covered up.

- **player_8:** Since player_1 was roleblocked, they didn't actually learn anything about player_7's visits. Player_6 interprets the block as wolf interference, but an unsuccessful action just means no result was gathered rather than a confirmed interaction.

- **player_9:** If player_1 is telling the truth about being blocked while trying to follow player_7, that means the wolves specifically wanted player_7's interactions concealed. Since player_7's role was hidden when they died that same night, it connects player_7 directly to whatever the pack was doing.

**The message — player_1 (proactive round):**

> Player 8 is right that I didn't get a result on player 7, but being blocked two nights in a row proves the Chanteuse is actively trying to suppress me. We should look closely at who is trying to downplay that interference.

**Whom does player_1's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 725

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "c05:d3:s11", "type": "message", "accused": _}
]
```