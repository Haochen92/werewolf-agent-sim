You are labeling retrieval results for a werewolf social deduction game's episodic memory system.

A player in a specific game situation is retrieving past experiences from memory to inform their decision.
For each retrieved memory, rate how relevant it would be to recall in the current situation.

## Relevance Scale
- **2** (Highly relevant): Directly addresses the same game dynamic, information landscape, or strategic challenge. The player would clearly benefit from recalling this.
- **1** (Partially relevant): Related (similar role, overlapping themes, adjacent phase) but different angle or specificity. Useful background but not a direct match.
- **0** (Not relevant): Different situation entirely. Recalling it would not help.

## Key Factors
- Same type of strategic challenge? (voting record analysis, information-starved play, role exposure management)
- Comparable game phase? (early/mid/endgame)
- Same role dynamics?
- Would recalling this memory actually help the player decide what to do?

For EACH case below, read the game state and golden situation query, then rate every retrieved memory.
Respond with a JSON array per case containing objects with "key" (the 12-char prefix shown) and "relevance" (0/1/2).


---

# Case 8: healer — day_discussion (day 2 round 2)

## Game State (what the player sees)
```
================================================================================
CASE 8498d5f44eb1710a7646fb3f5283dc0f:45d6fbcec9c90a34 | healer | day 2 round 2 | day_discussion
================================================================================

Role: healer
Day: 2, Round: 2

Surviving players: player_1, player_3, player_4, player_6, player_7, player_8, player_2, player_5

--- Previous days summary ---
[Day 1]
Key accusations: None. Defenses: None. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: None. The Day 1 discussion was characterized by universal caution, with all eight players (player_1, player_2, player_3, player_4, player_5, player_6, player_7, and player_8) exchanging polite greetings and general inquiries about potential suspicious behavior without identifying or accusing any specific individuals.

[Day 1]
Day 1: No vote was held today.

[Day 1]
player_1 was targeted by the wolves last night, but was saved by the healer!

--- Today's public discussion ---
[Day 2, Round 1] player_1: It is fortunate the healer saved me last night. Being targeted is a clear indicator that someone wanted me gone, and now that I am safe, I intend to use this second chance to help us hunt the wolves. We cannot afford to stay silent or play it safe—who here has a theory on why the wolves targeted me, and who among us is staying suspiciously quiet?
[Day 2, Round 1] player_3: It's good news that someone was saved last night. We should focus on the voting records from now on to see who might be trying to steer the group.
[Day 2, Round 1] player_4: It is fortunate that player_1 was saved last night. This gives us a concrete starting point. Let's focus on why the wolves might have targeted them and see if anyone tries to downplay the significance of this save or shift the conversation away from it.
[Day 2, Round 1] player_6: It's fortunate the healer saved player_1 last night. This gives us a solid starting point. I'm curious to hear everyone's thoughts on why the wolves might have targeted them, or if anyone sees a pattern in how the night went.
[Day 2, Round 1] player_7: It's interesting that the wolves went for player_1 last night. Usually, that suggests they saw someone as a threat or a potential leader. We should keep an eye on how everyone reacts to this reveal, as it might tell us more about who is trying to push the narrative.
[Day 2, Round 1] player_8: It's fortunate the healer saved player_1 last night. Since we have a confirmed town-aligned player, let's focus our analysis on that. Why do you think the wolves targeted player_1 specifically? Let's use this as a starting point to pressure those who are trying to shift the conversation elsewhere.
[Day 2, Round 1] player_2: It is definitely good news that player_1 was saved last night. Since we do not have much information yet, we should probably stay cautious and focus on observing how everyone reacts to this news before jumping to any conclusions.
[Day 2, Round 1] player_5: It is definitely a relief that player_1 was saved last night. That gives us a bit more breathing room to figure out what is going on. Has anyone noticed anything strange in the way people are reacting to that news so far?

--- Strategy note ---
Maintain a low profile to avoid being identified as the Healer after the successful save. Observe who reacts most strongly to the save announcement, as wolves often redirect focus or feign surprise. Avoid leadership roles and contribute only when necessary to blend in as a standard villager.

--- Situation standards (shared) ---
SITUATION DESCRIPTION STANDARDS

These standards apply everywhere a game situation is described: a mid-game
situation summary, a post-game observation scenario, a strategy point's
situation field, or a rewritten entry during deduplication.

DIMENSIONAL FRAMEWORK:
Ground situation descriptions in these dimensions as relevant:

- Information landscape: Is the village information-rich (confirmed roles,
  voting evidence, caught lies) or information-starved (no leads, speculative
  reads)? What TYPE of evidence is driving suspicion: voting records,
  communication style, behavioral patterns, or concrete claims?
- Consensus texture: How aligned is the village? Unified, fragile, split,
  or no consensus? Is it driven by evidence or social momentum? (Do not
  describe who is under pressure — that belongs in agent exposure.)
- Agent exposure: What is the agent's position — driving the push, aligned
  with consensus, under indirect scrutiny, or the primary target? What is
  the basis — specific evidence, behavioral reads, association with another
  player, or nothing concrete?
- Game phase: Early (no eliminations, no data), mid (some data, roles
  emerging), or endgame (few players, high stakes per vote)? What changed
  most recently?


SPECIFICITY TEST:
Before finalizing any situation description, check: if this were used as a
semantic search query, would it match only situations with similar dynamics,
or would it match any game where something vaguely similar happened? If the
latter, add qualifying detail from the dimensional framework.

--- Role-specific lens ---
Also note: who most needs protection, whether your activity level risks exposing you, and whether it's time to claim.

```

## Golden Situation Query (what we're retrieving for)

**Situation 1:** The healer's successful night-1 save was publicly announced, confirming one player as a wolf target. The discussion is in early stages with all players reacting to the save but no accusations made — everyone is analyzing reactions and looking for who shifts the conversation. Information landscape: Information-starved — the healer save is the only data point; all reads are based on initial reactions. Game phase: Early game, day 2 round 2 with all 8 players alive. Consensus texture: No consensus — the discussion is in the shared-observation phase with no suspect named. Agent exposure: The healer must maintain a low profile to avoid identification; appearing too knowledgeable about the save's implications could reveal the role.

## Retrieved Memories to Label

### Memory 1 (observation) [key: c7cf1300-438] (score: 0.8327)
**Situation:** After successfully protecting a player on Night 1, the Healer became an influential voice in the Day 2 discussion. Information landscape: The only information was that a save had occurred, confirming the Healer was active and effective. Game phase: Mid-game, with all players still alive.
**Approach:** The Healer (player_2) engaged actively in the discussion, attempting to guide the village.
**Outcome:** The Healer's increased influence likely drew the wolves' attention, leading to them being targeted and killed on Night 2.

### Memory 2 (observation) [key: a7ca80e1-7bc] (score: 0.8131)
**Situation:** With the village dwindling and no clear leads, the healer (player_2) took an active role in the Day 3 discussion to analyze behavioral patterns. Information landscape: The key evidence was the voting record from Day 2 and the consistent alignment in rhetoric between two players (player_3 and player_8). Game phase: Mid-game, where a correct lynch was critical to stop the villagers from being outnumbered. Consensus texture: The healer was instrumental in building a strong, evidence-based consensus against the wolf pair.
**Approach:** The healer (player_2) directly challenged the suspicious pair, pointing out how their coordinated calls for caution were tactically aligned and demanding a better explanation. This helped focus the village's attention.
**Outcome:** The healer's logical arguments helped solidify the vote against a wolf (player_3). Although the healer was killed the next night, their contribution was crucial for turning the game in the villagers' favor.

### Memory 3 (observation) [key: a786957c-bc1] (score: 0.8036)
**Situation:** On Day 1, the Healer (Player 1) took an active role in trying to start conversations and organize the group's thoughts. Information landscape: It was the start of the game, so the information landscape was completely blank. Game phase: Early-game, with all players still alive.
**Approach:** The Healer acted as a facilitator, asking questions and prompting others to share their initial hunches in an attempt to get the town working together.
**Outcome:** This proactive behavior made the Healer stand out as a potential leader, causing the wolves to identify them as a high-priority target. They were killed on the first night.

### Memory 4 (observation) [key: 434ca33b-17d] (score: 0.7963)
**Situation:** The Healer was facing a near-unanimous vote for elimination on Day 2. Information landscape: There was no evidence presented against the Healer; the vote was based on unsubstantiated and uncoordinated suspicion. Game phase: Mid-game, after one night. The Healer's successful save had just been announced. Social pressure: Overwhelming, organic pressure from most of the village converged on the Healer without a clear source.
**Approach:** The Healer (player_8) did not claim their role to try and prevent their elimination. Instead, they cast a single, unexplained vote against a wolf (player_3).
**Outcome:** The Healer was eliminated, dealing a devastating blow to the village's chances of winning. Their failure to claim under duress cost the town its only means of nightly protection.

### Memory 5 (observation) [key: 68c2fc76-5fa] (score: 0.7880)
**Situation:** The healer (player_7) was briefly implicated for having a suspicious vote in the past, similar to the main wolf suspect (player_6). Information landscape: The discussion was centered on an information-rich voting record from the previous day. Game phase: Endgame, with one wolf eliminated and the village scrutinizing all non-majority voters. Social pressure: Minor, organic social pressure was placed on the healer by the investigator (player_4) who pointed out the similar vote.
**Approach:** The healer acknowledged they might have been 'swayed' and made a mistake, but immediately pivoted to agree with the main accusation against player_6, thus rejoining the village consensus.
**Outcome:** This quick admission and pivot successfully deflected all suspicion from the healer, allowing them to blend back into the town majority and preserve their crucial role.

### Memory 6 (observation) [key: 84cfd842-4a6] (score: 0.7867)
**Situation:** The game master publicly announced the healer's successful save, confirming the targeted player's alignment. This provided information-rich, confirmed data points for the village. Game phase: Mid-game, morning after a pivotal night action.
**Approach:** The healer remained low-profile, avoiding credit for the save while still participating in the analysis of the confirmed information to guide the village.
**Outcome:** The healer's identity remained concealed while the village successfully weaponized the confirmed information, correctly identifying key villagers and/or wolves.

### Memory 7 (observation) [key: a302bd79-6e3] (score: 0.7846)
**Situation:** After the Investigator was voted out, confirming their role, the remaining villagers and the Healer had to decide how to use their final accusation against players 1 and 5. Information landscape: The game state became information-rich, as the posthumous reveal of the Investigator's role lent massive credibility to their final claim. Game phase: Endgame, where a single correct vote could break the wolves' power. The Investigator's death provided the crucial clue. Consensus texture: A strong consensus formed quickly among the non-wolf players, uniting them against the two players the Investigator had accused.
**Approach:** The Healer (player_4) and villagers (player_2, player_7, player_8) immediately trusted the dead Investigator's information. They used the accusers' own voting records and aggressive arguments against the Investigator as corroborating evidence of their guilt.
**Outcome:** This unified front, based on the Investigator's information, allowed the village to systematically eliminate both wolves over the next two days and win the game.

### Memory 8 (observation) [key: ce570d93-205] (score: 0.7776)
**Situation:** A villager mistakenly accused the Healer of a suspicious vote, but the Healer had actually voted correctly with the majority. Information landscape: The information landscape was rich with public voting records that could be checked for accuracy. Game phase: Mid-game, where establishing trust is critical. Social pressure: Momentary, vibes-based pressure was put on the Healer due to another player's error.
**Approach:** The Healer (Player 8) immediately and firmly corrected the factual error by referencing the public vote log, shutting down the incorrect line of suspicion.
**Outcome:** The accuser apologized, the false narrative was stopped before it could gain traction, and the Healer maintained their credibility within the village.

### Memory 9 (observation) [key: 87672547-c27] (score: 0.7382)
**Situation:** The village rapidly formed an accurate, evidence-backed consensus against a suspect based on voting records. Information landscape: Information-rich, driven by concrete voting data from a prior round. Game phase: Endgame, high stakes for the final wolf.
**Approach:** The healer stayed quiet and avoided unnecessary commentary that could attract attention or disrupt the village's flow.
**Outcome:** The village maintained their focus and successfully eliminated the final wolf without the healer ever being endangered.

### Memory 10 (observation) [key: d11fc4bf-bc8] (score: 0.7247)
**Situation:** A villager (player_2) used voting records to question a group that had collectively voted out another villager on the previous day. Information landscape: The evidence was based on voting records, showing a clear alignment of players in a previous, incorrect vote. Game phase: Endgame, with five players remaining. The wolves needed one more elimination to win. Social pressure: The accused group, which included two wolves, launched a coordinated counter-attack, accusing player_2 of trying to create chaos and shift blame.
**Approach:** The Healer (player_5) misinterpreted the villager's evidence-based argument as a suspicious tactic. They sided with the wolves, voting against the villager who was making the correct read.
**Outcome:** The Healer's vote was pivotal in eliminating the innocent villager, directly causing the wolves to win the game.

### Memory 11 (strategy_point) [key: 8bb8583f-b87] (score: 0.7700)
**Situation:** If you have just made a successful, publicly announced save that mechanically confirms the protected player's alignment. Information landscape: Information-rich, with a confirmed townie established. Game phase: Mid-game, following a pivotal night action where your existence and effectiveness are known to the village, but your identity remains secret.
**Action:** Maintain a low profile and encourage the village to analyze reactions to the save. Do not take credit or hint at your role, as the wolves will immediately begin hunting you to remove the village's protection. By becoming less of a leader, you decrease the odds of being correctly targeted.

### Memory 12 (strategy_point) [key: 8eef8fd7-58d] (score: 0.7609)
**Situation:** If it is the first day of the game and the information landscape is completely information-starved, with no data on player behaviors or alignments. Game phase: Early game, when wolves are looking for high-value targets and any vocal player is a potential target.
**Action:** Avoid stepping into a strong leadership role or being overly vocal in organizing the village, as proactive behavior can paint a target on your back. If you are the Healer, contribute enough to appear as a villager but let another active player draw the initial fire, and consider protecting them on the first night.

### Memory 13 (strategy_point) [key: 5e7cc5ba-fa6] (score: 0.7154)
**Situation:** When a clear and logical accusation has been made against a player, and the accused is defending themselves poorly. Information landscape: A credible accuser has presented a strong case, and the accused player is using logical fallacies or deflection. Game phase: Mid-game, when the village is weighing evidence and needs a push towards consensus.
**Action:** Actively join the cross-examination. Publicly point out the flaws in the accused's defense (e.g., 'You're criticizing the group for a vote you also participated in'). This adds weight to the correct consensus and builds your own credibility as a sharp villager, all while keeping your power role concealed.

### Memory 14 (strategy_point) [key: 309512ca-0a0] (score: 0.7148)
**Situation:** When you are the target of a strong voting consensus and your elimination seems certain, regardless of the accuser's credibility. Information landscape: The pressure on you is not based on hard evidence, but the number of votes against you is too high to overcome. Game phase: Mid-game, when your protection is still vital for the village's survival. Social pressure: A majority of players are preparing to vote for you.
**Action:** Publicly claim your role as Healer. While this paints a target on your back for the wolves, it's preferable to being eliminated by the village. A successful claim saves a day, confirms your identity, and forces the wolves to expend a night kill on you later, buying the village precious time.

### Memory 15 (strategy_point) [key: 7750a68d-c8a] (score: 0.7133)
**Situation:** When you are in the mid-to-late game and have been focusing on your night action while remaining quiet during discussions. Information landscape: Voting records and social dynamics are the primary sources of evidence, and your own record is thin due to non-participation. Game phase: Endgame, when the player count is low and every non-vocal player is a target. Social pressure: Pressure is mounting on quiet players to justify their existence.
**Action:** You must take a public stance and name a suspect, even if you are not certain. In the endgame, a quiet, 'observational' playstyle is indistinguishable from a wolf's evasiveness and will likely get you eliminated. Your survival depends on building a public record of proactive villager behavior.

### Memory 16 (strategy_point) [key: 964e7343-23c] (score: 0.7107)
**Situation:** When you are lightly implicated due to a past action, such as a vote that now looks suspicious in hindsight. Information landscape: An old voting record is being scrutinized, making you look loosely associated with a more likely suspect. Game phase: Mid-game or endgame, when the town is desperate for leads. Social pressure: A minor amount of organic pressure is being applied to you as part of a wider investigation.
**Action:** Briefly acknowledge the potential mistake without being overly defensive, then immediately pivot to support the main case against the more suspicious player. This demonstrates you are a team player who adapts to new information and quickly moves suspicion away from yourself.

### Memory 17 (strategy_point) [key: 6bd08e77-efd] (score: 0.6942)
**Situation:** If you are directly accused by a player who is the village's primary suspect. Information landscape: Information-rich, with the village's suspicion already focused on your accuser due to prior evidence like voting records. Game phase: Endgame, when the group has a strong lead on the final wolf. Social pressure: The cornered suspect is trying to deflect pressure onto you as a last resort.
**Action:** Do not engage in a lengthy defense or reveal your role. Trust the existing evidence against your accuser and vote with the consensus. A frantic defense can draw unwanted scrutiny, while quiet confidence allows other villagers to dismantle the weak accusation for you.

### Memory 18 (strategy_point) [key: 513226d2-cdc] (score: 0.6938)
**Situation:** If you are in the final three with two other players, one of whom is likely the wolf. Information landscape: The information landscape is rich with the complete voting records of all three remaining players. Game phase: Endgame, where the next vote will likely decide the game.
**Action:** Trust the data. The most reliable way to identify the final wolf is to find inconsistencies in their voting history, such as a past vote that seemed to cause chaos or went against the emerging village consensus. Do not let rhetorical attacks on your alliance with the other player distract you from this evidence.

### Memory 19 (strategy_point) [key: 76cc3c9d-b31] (score: 0.6749)
**Situation:** If the voting record shows an eliminated wolf had cast a vote against you. Information landscape: The public voting log provides concrete evidence of past actions. Game phase: Mid-game, after at least one wolf has been eliminated.
**Action:** Publicly highlight this fact as proof that the wolves considered you a threat and were attempting to frame you. Use this to build your credibility and argue that any lingering suspicion against you is likely a continuation of the wolves' plan.

### Memory 20 (strategy_point) [key: af1dbc2b-bc5] (score: 0.6745)
**Situation:** When a player presents a logical, evidence-based argument against a group, and that group responds with a unified, aggressive attack on the accuser's character or motives. Information landscape: The conflict is between a player using information-rich evidence (voting records) and a group using speculative or personal attacks. Game phase: Mid to endgame, when the remaining players are deciding who to trust. Social pressure: The group is attempting to discredit the accuser through coordinated social pressure rather than refuting their evidence.
**Action:** Trust the evidence over the social pressure. A coordinated deflection that ignores facts is a strong indicator of a wolf pack working to silence a threat. Support the player with the logical argument, as they are more likely to be a villager.

## Response for Case 8

Rate each of the 20 memories above. JSON format:
```json
[
  {"idx": 1, "key": "c7cf1300-438", "type": "observation", "relevance": _},
  {"idx": 2, "key": "a7ca80e1-7bc", "type": "observation", "relevance": _},
  {"idx": 3, "key": "a786957c-bc1", "type": "observation", "relevance": _},
  {"idx": 4, "key": "434ca33b-17d", "type": "observation", "relevance": _},
  {"idx": 5, "key": "68c2fc76-5fa", "type": "observation", "relevance": _},
  {"idx": 6, "key": "84cfd842-4a6", "type": "observation", "relevance": _},
  {"idx": 7, "key": "a302bd79-6e3", "type": "observation", "relevance": _},
  {"idx": 8, "key": "ce570d93-205", "type": "observation", "relevance": _},
  {"idx": 9, "key": "87672547-c27", "type": "observation", "relevance": _},
  {"idx": 10, "key": "d11fc4bf-bc8", "type": "observation", "relevance": _},
  {"idx": 11, "key": "8bb8583f-b87", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "8eef8fd7-58d", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "5e7cc5ba-fa6", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "309512ca-0a0", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "7750a68d-c8a", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "964e7343-23c", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "6bd08e77-efd", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "513226d2-cdc", "type": "strategy_point", "relevance": _},
  {"idx": 19, "key": "76cc3c9d-b31", "type": "strategy_point", "relevance": _},
  {"idx": 20, "key": "af1dbc2b-bc5", "type": "strategy_point", "relevance": _}
]
```