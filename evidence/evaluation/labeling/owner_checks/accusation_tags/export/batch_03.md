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

# Case 294

### Item b02:d4:s14

Game b02, day 4.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 3:
    player_3 voted to abstain
    player_4 voted to abstain
    player_8 voted to eliminate player_3
    player_9 voted to eliminate player_3
    player_10 voted to eliminate player_8
  It's a tie between ['abstain', 'player_3']. No one is voted out this day.

- **game_master:** Night of day 3: player_3 was shot by the vigilante last night. They were a fortune teller. player_4 was killed by the wolves last night. Their role is hidden by an illusionist.

**Today, before this message:**

- **player_9:** Last night I followed player_3, and they visited no one. Since player_3 turned out to be the fortune teller, knowing they made no visits right before their death gives us a clear baseline for last night's actions.

- **player_10:** I watched player_8 last night, and zero players visited them.

- **player_8:** That lines up with me keeping to myself last night, player_10. But player_9's check on player_3 doesn't help us narrow down the remaining threats now that player_3 has flipped fortune teller.

- **player_9:** Establishing player_3's lack of visits rules out active night abilities right before they were shot. Player_8, dismissing clean tracking data when we're down to three players avoids the real question of where everyone else was.

- **player_8:** I am not dismissing tracking data, I just meant it doesn't point to a wolf since player_3 turned out to be the fortune teller. If player_10 verified zero visits on me, maybe we should look closer at your own tracking history instead.

- **player_10:** Player_9, tracking player_3's lack of visits doesn't help us find the remaining wolf when night kills are still happening. Player_8, if you were completely unvisited last night while a wolf attack went through, we need to look closely at who is actually carrying out these kills.

- **player_8:** Player_10, being unvisited doesn't make me the killer when player_9's tracking hasn't actually caught a wolf all game. If we are examining who is driving these votes, player_9 has consistently deflected while pushing us toward dead ends.

- **player_10:** Player_8, you claim being unvisited clears you, but a wolf carrier leaves home to strike rather than receiving visitors. Since player_9 has consistent tracking claims, that leaves you as the most likely illusionist hiding the recent kills.

- **player_8:** If a wolf carrier leaves home, player_9's tracking hasn't actually caught a single wolf through all these rounds either. Blaming me for being unvisited ignores the fact that player_9's claimed follow results haven't successfully identified any wolf.

- **player_10:** Player_8, a wolf carrier leaves home to make the kill, which means my watch on your empty house doesn't clear you at all. Since we need an elimination today to stop wolf parity, your defensive deflection points straight to you carrying out these night strikes.

- **player_9:** Player_10, your watch on player_8's empty house matches a wolf leaving home to strike player_4, which puts the pressure squarely on them. If you are truly the sentinel, your consistency on these night targets helps nail down the last wolf.

- **game_master:** Before the vote: player_8 and player_9 each get a last word.

- **player_8:** Being unvisited last night just means I stayed home, which shouldn't automatically make me the carrier when player_9's tracking has missed every single wolf throughout the game. Voting me out based purely on watcher logic will hand the win directly to whoever is actually manipulating these votes. Please look at the actual record before casting a decisive vote today.

**The message — player_9 (closing round):**

> My tracking has consistently mapped out the night actions while others try to deflect attention from the remaining threat. I followed player_3 and reported clean data, which helps us isolate who was active during the night kills. Voting me out hands the game to the wolves right when parity is within reach.

**Whom does player_9's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 294

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "b02:d4:s14", "type": "message", "accused": _}
]
```

---

# Case 318

### Item b03:d3:s20

Game b03, day 3.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 2:
    player_1 voted to abstain
    player_2 voted to eliminate player_6
    player_4 voted to eliminate player_6
    player_5 voted to eliminate player_6
    player_6 voted to abstain
    player_7 voted to abstain
    player_8 voted to abstain
    player_9 voted to abstain
    player_10 voted to abstain
  The town chose to abstain. No one is eliminated today.

- **game_master:** Night of day 2: player_7 was attacked by the wolves but was saved by the healer!

**Today, before this message:**

- **player_4:** I was roleblocked last night, so my follow action didn't go through and I learned nothing.

- **player_6:** I am the healer, and I targeted player_7 last night, which explains the successful save announced this morning.

- **player_7:** Last night I checked player_6 and they read Not suspicious, following my night 1 check of player_1.

- **player_8:** For what it is worth, I watched player_4 last night and saw that player_5 visited them.

- **player_2:** If player_8 watched player_4 and saw player_5 visit, that directly aligns with player_4's claim of being roleblocked. However, we should keep in mind that the sentinel died on night one, so we need to understand how player_8 got that tracking result.

- **player_5:** If player_8 is claiming a watching ability while our sentinel died on night one, that story doesn't hold together. Player_8 needs to explain how they are getting watcher results with a dead sentinel.

- **player_8:** I never said I was the sentinel, player_5, just that I saw you at player_4's door last night. If you're so eager to discredit the observation instead of explaining why you visited player_4, maybe that's where the real suspicion lies.

- **player_9:** Player_8, you claim you watched player_4, but our only Sentinel died on night one. If you are getting watcher results while denying you are the Sentinel, you are essentially admitting to using player_3's dead body as the Necromancer.

- **player_8:** Player_9, you are working overtime to deflect off player_5's visit to player_4 last night instead of addressing why they were there. I reported what I saw, and throwing out wild accusations doesn't clear player_5's suspicious actions.

- **player_9:** I am not deflecting from player_5, I am pointing out the glaring hole in your story: you claim watcher results while our only Sentinel has been dead since night one. If you are not using player_3's body as the Necromancer, explain how you got that view.

- **player_8:** Player_9 is bending over backward to distract from player_5 visiting player_4 last night. Instead of obsessing over mechanics, player_9 and player_5 need to explain why player_5 was at player_4's door in the first place.

- **player_5:** Player_8, deflecting to my visit doesn't answer how you're producing watcher reports when our sentinel has been dead since night one. That's the real contradiction we need you to explain instead of dodging.

- **player_8:** Focusing purely on mechanics instead of player_5's unexplained visit to player_4 just shields whatever happened last night. If player_5 actually has a defense for showing up at player_4's door, let's hear that instead of hiding behind procedural arguments.

- **player_5:** Player_8, you keep talking about my visit while completely dodging how you are producing watcher results when our only sentinel died on night one. Throwing accusations around doesn't make your impossible claim go away.

**The message — player_9 (discussion round):**

> You keep calling it a deflection, player_8, but you still haven't explained how you have watcher results when our only Sentinel died on night one. If you aren't the Necromancer using player_3's body, give us your actual role instead of dodging.

**Whom does player_9's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 318

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "b03:d3:s20", "type": "message", "accused": _}
]
```

---

# Case 370

### Item b04:d3:s5

Game b04, day 3.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 2:
    player_1 voted to abstain
    player_2 voted to eliminate player_3
    player_3 voted to eliminate player_7
    player_4 voted to eliminate player_3
    player_5 voted to eliminate player_3
    player_6 voted to abstain
    player_7 voted to eliminate player_3
    player_8 voted to abstain
    player_9 voted to eliminate player_3
    player_10 voted to eliminate player_7
  Player player_3 has been voted out and was a chanteuse.

- **game_master:** Night of day 2: player_7 was attacked by the wolves but was saved by the healer! player_10 was attacked by the vigilante and a sigil last night. They were a illusionist.

*Opening round: every player speaks at once, so player_7 had heard no other line today.*

**The message — player_7 (opening round):**

> I was roleblocked last night on Night 2 and couldn't complete my investigation. Since player_3 was eliminated yesterday, this strongly suggests the Necromancer is using the dead Chanteuse body to blind the town.

**Whom does player_7's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 370

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "b04:d3:s5", "type": "message", "accused": _}
]
```

---

# Case 378

### Item b04:d3:s16

Game b04, day 3.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 2:
    player_1 voted to abstain
    player_2 voted to eliminate player_3
    player_3 voted to eliminate player_7
    player_4 voted to eliminate player_3
    player_5 voted to eliminate player_3
    player_6 voted to abstain
    player_7 voted to eliminate player_3
    player_8 voted to abstain
    player_9 voted to eliminate player_3
    player_10 voted to eliminate player_7
  Player player_3 has been voted out and was a chanteuse.

- **game_master:** Night of day 2: player_7 was attacked by the wolves but was saved by the healer! player_10 was attacked by the vigilante and a sigil last night. They were a illusionist.

**Today, before this message:**

- **player_1:** I am the Sigilist, and last night I placed a sigil on player_10; it triggered and struck them down because they attempted an attack.

- **player_4:** I need to correct my claim from yesterday, as I am actually the Healer rather than the sentinel.

- **player_5:** On night two, I watched player_10 and saw that both player_1 and player_9 visited them.

- **player_7:** I was roleblocked last night on Night 2 and couldn't complete my investigation. Since player_3 was eliminated yesterday, this strongly suggests the Necromancer is using the dead Chanteuse body to blind the town.

- **player_8:** Last night I followed player_5, and they visited player_10.

- **player_9:** I am claiming Vigilante, as I was the one who took the shot on player_10 last night.

- **player_2:** Player_4, you immediately dropped your sentinel claim the moment the duplicate was questioned and switched to healer. That looks a lot like scrambling to find an unclaimed town role once you were caught in a corner.

- **player_4:** I used a cover claim early on to protect myself, but my protection on player_7 literally stopped the wolf kill last night. The morning report proves the healer is active, so questioning my claim order ignores the actual saved life.

- **player_1:** Player_5's sentinel report correctly caught me and player_9 visiting player_10 last night. Since my sigil successfully triggered on player_10 and player_9 claims the shot, player_5's observation is fully backed up by our night actions.

- **player_8:** I can confirm player_5's movement from last night: my trailseer action was following player_5, and I saw them visit player_10. Since watching a player counts as a visit, my result backs up player_5's sentinel claim.

- **player_9:** Both player_1's sigil strike and player_4's healer save are explicitly backed up by the morning report, so those two town roles check out. Meanwhile, player_2 is hyper-focused on tearing down player_4's claim while ignoring actual verified results.

**The message — player_2 (discussion round):**

> Validating player_4's sudden shift from sentinel to healer just because there was a duplicate claim is dangerous, regardless of what happened elsewhere. Defending that kind of sloppy claim-hopping ignores how easily someone scrambles when cornered.

**Whom does player_2's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 378

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "b04:d3:s16", "type": "message", "accused": _}
]
```

---

# Case 400

### Item b05:d3:s14

Game b05, day 3.

**Since the last discussion:**

- **game_master:** Here's the vote result for day 2:
    player_1 voted to eliminate player_6
    player_2 voted to eliminate player_3
    player_3 voted to eliminate player_6
    player_4 voted to abstain
    player_5 voted to abstain
    player_6 voted to eliminate player_3
    player_7 voted to abstain
    player_8 voted to eliminate player_6
    player_10 voted to abstain
  The town chose to abstain. No one is eliminated today.

- **game_master:** Night of day 2: player_2 was stabbed by the serial killer last night. They were a chanteuse. player_8 was killed by the wolves last night. Their role is hidden by an illusionist.

**Today, before this message:**

- **player_1:** I was roleblocked last night, so my night action did not go through. Keep that in mind when looking at who is blocking town members.

- **player_7:** Last night on Night 2, I checked player_6 and they read Suspicious.

- **player_6:** If you actually checked me last night, player_7, why are you so quick to pin this on me right after player_8 pushed hard against me yesterday? It feels extremely convenient to jump straight to a guilty result.

- **player_7:** It is not about convenience, player_6, it is an investigation result from last night. You came up suspicious, which points directly to you being on the wolf team.

- **player_6:** It is awfully convenient that player_7 gets a guilty read on me right after player_8 spent all of yesterday pushing to lynch me. If player_7 really is the investigator, it feels like they are just riding the coattails of yesterday's established target.

- **player_7:** It is not riding coattails when I have an actual investigation result backing it up. You came up suspicious last night, player_6, which explains why player_8 and others suspected you yesterday. A guilty read is hard evidence, not a coincidence.

- **player_5:** Player_1 mentioned being roleblocked last night, but player_2 the Chanteuse was killed by the serial killer last night. Does a roleblock still succeed if the Chanteuse dies on the same night?

**The message — player_10 (proactive round):**

> To answer player_5's question, night actions all resolve simultaneously, so the Chanteuse's block would still go through even if they died that same night. If player_7's guilty read on player_6 is accurate, we might be looking at our first wolf.

**Whom does player_10's message accuse?** `none`, or the accused ids in seat order, comma-joined.

## Response for Case 400

Rate each of the 1 items above. JSON format:
```json
[
  {"idx": 1, "key": "b05:d3:s14", "type": "message", "accused": _}
]
```