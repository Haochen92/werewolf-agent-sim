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

---

# Case 11: investigator — day_vote (day 2 round 4)

## Game State (what the player sees)
```
================================================================================
CASE 8498d5f44eb1710a7646fb3f5283dc0f:3cb9538eb3af703b | investigator | day 2 round 4 | day_vote
================================================================================

Role: investigator
Day: 2, Round: 4

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
[Day 2, Round 2] player_1: We have no voting records yet, but we have behavioral patterns. Player_2 and player_5, you are both advocating for caution and waiting. How does 'observing' help us when we lose a villager every night? Give us a specific name or a reason why you are suspicious of someone, or I will consider your passivity a deliberate attempt to let the wolves win.
[Day 2, Round 2] player_4: We have all agreed it is fortunate, but that is just a polite consensus. Player_2, you suggested staying cautious and observing reactions—what specifically have you observed so far that makes you hesitant to commit to a suspect? We need more than just waiting.
[Day 2, Round 2] player_6: We have a saved player, but we are just repeating pleasantries. player_2, suggesting we 'stay cautious' and wait is essentially giving the wolves another night to act. Who do you actually find suspicious right now, and why?
[Day 2, Round 3] player_3: It is true we need more than just caution, but we also have to be careful not to rush into a vote and hit a villager by mistake. If player_2 and player_5 feel we should be observing, perhaps they can tell us who they are observing, specifically, and why.
[Day 2, Round 3] player_4: Player_2, your advice to 'observe' is effectively neutral, which is a luxury we don't have. Since you're watching everyone else, tell us: who has caught your eye as suspicious, and who are you ruling out? Answering this shouldn't require more observation time.
[Day 2, Round 3] player_6: player_2, your 'wait and see' advice directly helps the wolves by keeping us stagnant. If we don't pick a lead, we're just waiting for the next night kill. Name one person who you think is suspicious based on their response to the save, or explain why you think staying silent is a better strategy than hunting.
[Day 2, Round 3] player_7: Player_2, you say we need to be cautious, but we have had a full night and no new information. Waiting helps the wolves remain hidden. What specific behavior, beyond just 'caution', would make you suspect someone at this stage?
[Day 2, Round 3] player_2: Player 1, I hear your frustration, and it's justified. Since we have no records, I've been looking at how people are framing these discussions. I'm actually suspicious of player 8, who keeps trying to redirect us to 'analyze' others instead of offering a concrete theory themselves. Could that be a way to stay off the radar?
[Day 2, Round 3] player_5: I understand the frustration, but calling for names this early just creates a target-rich environment for the wolves to exploit. If we just lash out at whoever is most 'vocal,' we're doing the wolves' job for them. I find player_4's insistence on naming someone immediately a bit too eager to jump to a conclusion before we have any real data.
[Day 2, Round 4] player_1: Player 2, your pivot to accusing player 8 immediately after being pressed is a classic deflection. You offered no evidence for why player 8 is suspicious, only that they asked questions, which is exactly what we need right now. I am voting for you because you are actively discouraging investigation while shielding yourself.
[Day 2, Round 4] player_4: Player_5, labeling my demand for information as 'eager to jump to conclusions' is a common deflection. You've had the same amount of information as everyone else, yet you and player_2 are the only ones consistently arguing against active analysis. Why is my request for logic a bigger threat to you than finding the wolves who targeted player_1?
[Day 2, Round 4] player_6: Player_2 and player_5, your attempts to frame active inquiry as 'rushing' is exactly how the village gets paralyzed. We have no data, yet you both actively discourage building any. I am voting for player_2 because their strategy is fundamentally designed to keep us blind until the wolves win.
[Day 2, Round 4] player_8: Player_2, your pivot to accusing me for requesting analysis is a classic diversion. We are all searching for information because we have none, so framing my questions as a way to 'stay off the radar' feels like an attempt to shift the spotlight away from your own lack of contribution. Since we lack voting records, your deflection is the most telling behavior I've seen so far.
[Day 2, Round 4] player_5: I understand the need for action, but let's be careful. By forcing a vote this quickly based purely on tone, aren't we just playing into the wolves' hands by potentially eliminating an innocent who just happens to be less vocal? I'm still observing, and player_4's aggressive push feels like it's designed to force an error from us.

--- Your private investigation results ---
Day 1: player_1 was revealed as villager

--- Strategy note ---
Maintain a low profile while observing the dynamics between the aggressive group and the defensive duo. Since player_2 is targeting player_8, I will watch if player_8 counter-attacks or stays calm. I need to use my next investigation to clarify my stance on these two factions without revealing my role.

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
Lead with how your private findings relate to the public narrative — do they confirm, contradict, or add nothing new? Also note whether your communication style is marking you as a power role.

```

## Golden Situation Query (what we're retrieving for)

**Situation 1:** The village is sharply divided between aggressive players demanding suspects be named and a defensive duo consistently advocating caution. One aggressive player accused a cautious player of deflection, escalating into a confrontation that dominates the discussion. The investigator has privately confirmed the healer-saved player as a villager but has no wolf identifications yet. Information landscape: Publicly information-starved; the investigator holds private villager confirmation but no wolf leads. Game phase: Early game, first vote with all 8 players alive; the aggressive-vs-cautious split is the dominant dynamic. Consensus texture: Split between action and caution factions with no evidence-based consensus. Agent exposure: Low profile — watching from the sidelines with private information that doesn't yet help identify wolves.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 42e37cd6-541] (score: 0.8089)
**Situation:** Feeling pressure to act in an information-starved village, the investigator initiated a vote based on a weak behavioral read. Information landscape: There was no hard evidence, only speculative reads on communication style. The investigator's private check on player_2 had revealed a villager, narrowing the suspect pool only slightly. Game phase: Mid-game, after the first night kill. The village was directionless.
**Approach:** The investigator (player_1) broke the stalemate by accusing and voting for a player (player_5) who seemed to be deflecting by 'mirroring others' questions', hoping to force a reaction.
**Outcome:** The village followed the investigator's lead and eliminated a villager. This demonstrated that even a well-intentioned power role can cause significant harm by acting on poor-quality information.

### Memory 2 (observation) [key: b34d12c2-9d2] (score: 0.8082)
**Situation:** The Investigator was eliminated by a plurality vote while holding the identity of a wolf. Information landscape: The village was information-starved, and the vote was based on conflicting behavioral reads and frustration with a discussion deadlock. Game phase: Mid-game, after one night kill. The vote against the Investigator was the first elimination vote of the game. Consensus texture: A fragile consensus formed against the Investigator, driven by players frustrated with their aggressive but vague accusations.
**Approach:** The Investigator (player_1) chose not to reveal their role or their finding, maintaining their soft-pressure strategy until the end.
**Outcome:** The Investigator was eliminated, their role was revealed, and their valuable information was lost. The village was left demoralized and without direction.

### Memory 3 (observation) [key: 4619f4d5-ea2] (score: 0.8051)
**Situation:** The Investigator (Player 4) voted based on a private, behavioral read that contradicted the growing village consensus, placing them in a voting bloc with a wolf. Information landscape: The investigator had private information (Player 2 was a villager) but acted on a speculative read about another player. Game phase: Mid-game, during the first elimination vote where town consensus was critical. Social pressure: The vote placed the Investigator under immense, evidence-based social pressure the following day, as they had to defend voting with a now-revealed wolf.
**Approach:** The Investigator chose to act on a private read, voting against the correct wolf target (Player 7) and for the Healer (Player 8), contradicting the village consensus.
**Outcome:** The initial vote severely damaged the Investigator's credibility. However, their willingness to pivot and vote with the village on the final day allowed them to repair some trust and contribute to the win.

### Memory 4 (observation) [key: 5922bf88-e54] (score: 0.8003)
**Situation:** A strong but unsubstantiated consensus formed to vote out player_8. Information landscape: The landscape was information-starved regarding player_8; the Investigator had no information on them but knew player_1 was a villager. Game phase: Mid-game, during the first real vote after a healer save was announced. Consensus texture: A strong, swift consensus formed, with players quickly piling on one target.
**Approach:** The Investigator (player_6) chose to align with the group consensus and voted to eliminate player_8, who turned out to be the Healer.
**Outcome:** This vote was a catastrophic error, removing the town's only protective role and paving the way for the wolves to win.

### Memory 5 (observation) [key: 7c0a6e6d-2be] (score: 0.7832)
**Situation:** The Investigator had a strong suspicion about a player but no definitive proof from their night action. Information landscape: Publicly, the game was information-starved, relying on gut reads. Game phase: Mid-game, during the very first elimination vote.
**Approach:** The Investigator, player_2, took the lead and cast the first vote against their suspect, player_8. This decisive action signaled confidence and rallied the other villagers to follow.
**Outcome:** The village successfully eliminated a wolf. However, this act of leadership made player_2 the clear target for the remaining wolf and they were killed the next night.

### Memory 6 (strategy_point) [key: 4207be33-a2a] (score: 0.7613)
**Situation:** If you hold a private, speculative suspicion about a player, but the public village consensus is building strongly against someone else based on voting records or strong social reads. Information landscape: You have private knowledge from your investigations, but the public sphere is driven by concrete voting patterns. Game phase: Mid- to late-game, when a single dissenting vote can make you a primary suspect. Consensus texture: A strong, multi-player consensus is converging on a single target. Action: Abandon your speculative read and vote with the village consensus, unless you have investigated the consensus target and know they are innocent. Voting against a successful lynch will destroy your credibility and paint you as a wolf's ally.
**Action:** Abandon your speculative read and vote with the village consensus, unless you have investigated the consensus target and know they are innocent. Voting against a successful lynch will destroy your credibility and paint you as a wolf's ally.

### Memory 7 (strategy_point) [key: 57449d0c-1ba] (score: 0.7525)
**Situation:** When a strong, vibes-based consensus forms against a player without concrete evidence. Information landscape: The information landscape is starved regarding the target, but you have private information confirming other players are villagers, suggesting the target may be a town power role. Game phase: Mid- to late-game, when every vote is critical and losing a power role is devastating. Consensus texture: A strong bandwagon is forming based on social pressure rather than evidence. Action: Refuse to join the bandwagon vote. Casting a vote against your own strongest suspect, or even abstaining, is better than contributing to the potential elimination of a town power role based on social pressure.
**Action:** Refuse to join the bandwagon vote. Your vote lends credibility. Casting a vote against your own strongest suspect, or even abstaining, is better than contributing to the potential elimination of a town power role based on social pressure.

### Memory 8 (strategy_point) [key: 6710c4b7-412] (score: 0.7323)
**Situation:** If you have privately confirmed a player is a wolf, and you see the village independently reach the same conclusion based on strong public evidence. Information landscape: The public evidence is strong and sufficient on its own to secure the elimination. Game phase: Mid- to endgame, when preserving your role is critical. Consensus texture: A strong, organic consensus has formed against your target without your intervention.
**Action:** Stay quiet and simply vote with the majority. There is no need to reveal your role or your findings, as intervening adds no value, risks exposing you if the vote fails, and wastes the advantage of having a secret confirmed role for the next night.

## Response for Case 11

Rate each of the 8 memories above. JSON format:
```json
[
  {"idx": 1, "key": "42e37cd6-541", "type": "observation", "relevance": _},
  {"idx": 2, "key": "b34d12c2-9d2", "type": "observation", "relevance": _},
  {"idx": 3, "key": "4619f4d5-ea2", "type": "observation", "relevance": _},
  {"idx": 4, "key": "5922bf88-e54", "type": "observation", "relevance": _},
  {"idx": 5, "key": "7c0a6e6d-2be", "type": "observation", "relevance": _},
  {"idx": 6, "key": "4207be33-a2a", "type": "strategy_point", "relevance": _},
  {"idx": 7, "key": "57449d0c-1ba", "type": "strategy_point", "relevance": _},
  {"idx": 8, "key": "6710c4b7-412", "type": "strategy_point", "relevance": _}
]
```

---

# Case 17: healer — day_vote (day 2 round 2)

## Game State (what the player sees)
```
================================================================================
CASE 8e437de2eab2d9d54e45ed4dee61fe54:878d61545c98af70 | healer | day 2 round 2 | day_vote
================================================================================

Role: healer
Day: 2, Round: 2

Surviving players: player_1, player_2, player_3, player_4, player_5, player_7, player_6, player_8

--- Previous days summary ---
[Day 1]
Key accusations: None. Defenses: None. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: None. The Day 1 discussion was characterized by players collectively agreeing to observe behavior and exchange initial thoughts, with no specific accusations, defenses, role claims, or alliances forming.

[Day 1]
Day 1: No vote was held today.

[Day 1]
player_1 was targeted by the wolves last night, but was saved by the healer!

--- Today's public discussion ---
[Day 2, Round 1] player_1: It is fortunate the healer saved me last night. That gives us one concrete piece of information: someone is clearly looking to eliminate me. I suggest we all look closely at who tries to steer the conversation away from the implications of last night's failed kill or who acts unusually quiet today.
[Day 2, Round 1] player_2: It is fortunate that player_1 was saved. We should observe who tries to shift the conversation away from this or who reacts most defensively to the news.
[Day 2, Round 1] player_3: It's interesting that the wolves targeted player_1 right out of the gate. Usually, they go for someone they perceive as a threat or someone who is trying to lead the group. Since player_1 survived thanks to our healer, I think we should keep a close eye on anyone who seems overly interested in discrediting them or redirecting our focus elsewhere.
[Day 2, Round 1] player_4: It is fortunate that player_1 was saved. We should use this as a solid starting point for our investigation. Has anyone noticed if anyone seems particularly dismissive of that event or is trying to shift our attention away from it?
[Day 2, Round 1] player_5: It's fortunate for the village that the healer was successful last night. With no leads yet, we should look closely at how everyone reacts to this early game situation. Has anyone noticed anything unusual?
[Day 2, Round 1] player_7: Since player_1 was targeted last night and saved, we should look closely at how the night played out. Does anyone have thoughts on who might have been the target and why? Let's avoid rushing to conclusions and focus on observed patterns.
[Day 2, Round 1] player_6: It is definitely a huge relief that player_1 was saved last night. The healer did a great job. Since we are still in the early stages, does anyone have any thoughts on how we should proceed today to find the wolves?
[Day 2, Round 1] player_8: It's really good news that player_1 was saved last night. Does anyone have any theories on why the wolves would target them? Maybe they are just casting a wide net for now.

--- Strategy note ---
Continue maintaining a low profile to avoid being identified as the healer. Do not volunteer new theories unless there is a clear shift in player behavior or a specific accusation to address. Focus on blending in with the general consensus to stay off the wolves' radar.

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

**Situation 1:** The healer successfully saved a player on night 1, but the subsequent discussion produced no leads — all players made generic comments about the save without naming suspects. The village enters its first vote with zero differentiation between players. Information landscape: Information-starved — the healer save confirmed one wolf target but generated no actionable suspicion. Game phase: Early game, first vote with all 8 players alive; no behavioral differentiation has emerged. Consensus texture: No consensus — every player's contribution is interchangeable. Agent exposure: The healer must blend in as a generic villager; the lack of discussion content means any distinctive contribution risks standing out.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 42f30e10-562] (score: 0.7802)
**Situation:** In the final vote with four players remaining, the Healer (player 2) was targeted for their passive communication style throughout the game. Information landscape: The information was based entirely on social reads and voting history, as no confirmed roles were left in play. Game phase: Endgame, with one wolf remaining. Social pressure: A coordinated push from the remaining wolf and two villagers targeted the Healer for consistently deflecting questions and not naming suspects.
**Approach:** The Healer attempted to defend their quietness as an observational strategy but failed to take a decisive stance until it was too late, only casting a vote after consensus had already formed against them.
**Outcome:** The Healer was voted out. This was the game-losing move, as it left the final wolf in a 2 vs. 1 situation, guaranteeing their victory.

### Memory 2 (observation) [key: 6aca8c49-eae] (score: 0.7770)
**Situation:** Endgame, with a strong, evidence-based consensus forming against the likely final wolf. The information landscape is rich, driven by voting records. The Healer is not the primary target but may be under minor suspicion or have slight personal doubts.
**Approach:** Voted with the majority to eliminate the wolf (1x), Voiced concern but ultimately voted with the majority (1x).
**Outcome:** Successfully eliminated the final wolf, securing a win for the village. This approach avoided a split vote and solidified the Healer's position as a team player.

### Memory 3 (observation) [key: a8ec1773-30f] (score: 0.7536)
**Situation:** A credible Investigator claim led to a strong consensus against a player who turned out to be a wolf. Information landscape: The village had a strong lead from the Investigator's claim, making the vote seem straightforward. Game phase: Mid-game, at the first elimination vote. Consensus texture: A strong, multi-player consensus was driven by the Investigator's specific, credible claim.
**Approach:** The Healer (player_8), fearing a potential wolf-led bandwagon, voted against the Investigator instead of the accused wolf. This was the only vote against the Investigator besides the wolf's own.
**Outcome:** The wolf was eliminated, but the Healer's dissenting vote was recorded. The next day, after the Investigator was killed, this vote became irrefutable evidence that led to the Healer being mislynched.

### Memory 4 (strategy_point) [key: 4922ee84-da7] (score: 0.7139)
**Situation:** In the mid-game or endgame, a strong consensus is forming against a player based on voting records or other public evidence. You are currently under minor suspicion for a past action, and you need to manage this heat while the village focuses on another target.
**Action:** Do not aggressively defend your past actions, as this can make you seem defensive and draw more suspicion. Instead, vote with the emerging majority to align yourself with the village, help eliminate a likely threat, and reduce the focus on you.

### Memory 5 (strategy_point) [key: 182ebc43-053] (score: 0.7055)
**Situation:** In the mid-game or endgame, a strong consensus is forming against a player, either driven by evidence-based information like voting records or by a credible Investigator claim. You feel uneasy about the target despite the strength of the consensus, and you are not currently under significant suspicion yourself.
**Action:** Briefly voice your skepticism to ensure all angles are considered, but do not cast a lone protest vote against the consensus. Unless you can provide concrete counter-evidence, vote with the group or abstain; voting against the group risks a split vote that is more likely to save a wolf than expose a conspiracy, and it makes you a primary suspect if the claim or evidence is proven true.

## Response for Case 17

Rate each of the 5 memories above. JSON format:
```json
[
  {"idx": 1, "key": "42f30e10-562", "type": "observation", "relevance": _},
  {"idx": 2, "key": "6aca8c49-eae", "type": "observation", "relevance": _},
  {"idx": 3, "key": "a8ec1773-30f", "type": "observation", "relevance": _},
  {"idx": 4, "key": "4922ee84-da7", "type": "strategy_point", "relevance": _},
  {"idx": 5, "key": "182ebc43-053", "type": "strategy_point", "relevance": _}
]
```

---

# Case 18: investigator — day_discussion (day 3 round 1)

## Game State (what the player sees)
```
================================================================================
CASE 8e437de2eab2d9d54e45ed4dee61fe54:259d3c37a9f3e166 | investigator | day 3 round 1 | day_discussion
================================================================================

Role: investigator
Day: 3, Round: 1

Surviving players: player_1, player_2, player_3, player_4, player_5, player_7, player_6

--- Previous days summary ---
[Day 1]
Key accusations: None. Defenses: None. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: None. The Day 1 discussion was characterized by players collectively agreeing to observe behavior and exchange initial thoughts, with no specific accusations, defenses, role claims, or alliances forming.

[Day 1]
Day 1: No vote was held today.

[Day 1]
player_1 was targeted by the wolves last night, but was saved by the healer!

[Day 2]
Key accusations: None. Defenses: None. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: None. The discussion focused on the significance of the survivor of the previous night's attack, with players 1 through 8 generally agreeing that the group should monitor for suspicious behavior, defensive reactions, or attempts to deflect attention from the failed kill. No specific players were accused, no roles were claimed by individuals, and no voting blocs were formed.

[Day 2]

Here's the vote result for day 2:
  player_1 voted for player_8
  player_2 voted for player_8
  player_3 voted for player_8
  player_4 voted for player_8
  player_5 voted for player_8
  player_7 voted for player_8
  player_6 voted for player_2
  player_8 voted for player_2
Player player_8 has been voted out and was a wolf.


[Day 2]
player_3 was targeted by the wolves last night, but was saved by the healer!

--- Today's public discussion ---
No messages yet.

--- Your private investigation results ---
Day 1: player_1 was revealed as villager
Day 2: player_2 was revealed as healer

--- Strategy note ---
Since player_1 was targeted by wolves and saved by the healer, they are likely a high-value villager target. I have confirmed player_1 as a villager, so they are a safe ally. I will now investigate player_2 to see if they are a wolf, as they were active early on in the discussion. I need to keep a low profile and avoid revealing my role, focusing on identifying the wolf pack by checking players who seem to be steering the conversation.

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
Lead with how your private findings relate to the public narrative — do they confirm, contradict, or add nothing new? Also note whether your communication style is marking you as a power role.

```

## Golden Situation Query (what we're retrieving for)

**Situation 1:** The investigator has confirmed both the healer-saved player (villager) and a second player (healer) through two nights of investigation. A wolf was eliminated by near-unanimous vote on day 2, and the investigator was targeted by wolves on night 2 but saved by the healer. Information landscape: The investigator possesses rich private knowledge — confirmed identities of two key village roles — while publicly the village has a wolf elimination and voting records to analyze. Game phase: Mid-game, day 3 with 7 players remaining and 1 wolf left; the investigator's survival via healer save suggests the wolves have identified them. Consensus texture: The village was unified on day 2 and should carry momentum. Agent exposure: High-value target — the wolves targeted the investigator specifically, suggesting they know the role; the healer cannot save the same player consecutively.

**Situation 2:** The investigator knows the healer's identity through private investigation and must protect this information while guiding the village toward the remaining wolf. Revealing the healer's identity would expose them to the wolves, but withholding it means the village operates without knowing who is confirmed. Information landscape: The investigator has more confirmed information than any other player but cannot share it without endangering the healer. Game phase: Mid-game with the investigator at risk of being the wolves' primary night target. Consensus texture: Village should be confident after correctly identifying a wolf. Agent exposure: Under lethal threat — wolves have identified the investigator and will likely target them again.

## Retrieved Memories to Label

### Memory 1 (observation) [key: a49feaa8-ca9] (score: 0.8528)
**Situation:** The investigator had privately confirmed two players (a villager and the healer) as innocent. Information landscape: The investigator possessed private, information-rich knowledge about village allies, while the public landscape was still developing. Game phase: Mid-game.
**Approach:** The investigator used their private knowledge to confidently align with the confirmed innocents, forming a trusted bloc. They aggressively led the accusation against a suspect whose public actions (voting for the confirmed healer) contradicted the investigator's private information.
**Outcome:** This trusted coalition led the discussion, dismantled the suspect's defenses, and ensured the village remained united in voting out the wolf, securing the win without the investigator revealing their role.

### Memory 2 (observation) [key: 3625d761-b7d] (score: 0.8479)
**Situation:** The Investigator had confirmed the Healer's identity on Night 1 but needed to survive to gather more information. Information landscape: The Investigator possessed private, confirmed information, but the public landscape was information-starved. Game phase: Mid-game, after the Healer's death was announced.
**Approach:** The Investigator (player_8) chose to remain silent during the Day 2 discussion to avoid drawing attention and being targeted by wolves.
**Outcome:** Their silence was interpreted as suspicious passivity by the information-starved villagers. A consensus formed against them, leading to their elimination before they could share any findings or investigate a wolf.

### Memory 3 (observation) [key: 928fde7b-4c7] (score: 0.8435)
**Situation:** The Investigator identified a wolf on Night 1 and needed to convince the village to eliminate them on Day 2 without revealing their role. Information landscape: The Investigator had private, confirmed information, while the rest of the village was operating on behavioral reads. Game phase: Mid-game, following the first wolf kill which eliminated the Healer.
**Approach:** The Investigator (player_4) aggressively questioned the wolf's arguments for inaction, framing it as a stalling tactic that benefited wolves, galvanizing the village to vote without revealing their role.
**Outcome:** The village successfully eliminated the wolf. However, the Investigator's prominent role in the accusation made them the obvious target for the remaining wolf on the following night.

### Memory 4 (observation) [key: bb9b8a2c-f53] (score: 0.8413)
**Situation:** The Investigator privately identified a wolf and needed to convince the village to eliminate them without revealing their role. Information landscape: The Investigator had private, certain information supported by public, concrete evidence from the voting record. Game phase: Mid-game, after the Healer was eliminated.
**Approach:** The Investigator (player_4) led the discussion by highlighting voting discrepancies to build a logical case against the wolf, avoiding a role reveal.
**Outcome:** The village voted out the wolf, but the Investigator's high-profile leadership made them a target, leading to their death the following night.

### Memory 5 (observation) [key: a5db9f55-0d8] (score: 0.8306)
**Situation:** In the mid-game to endgame, the Investigator possessed private, information-rich knowledge (identifying both innocent players and wolves). The information landscape combined public voting records and behavioral reads with the Investigator's private findings. The village required active, subtle guidance to solidify the case against wolves without the Investigator revealing their role.
**Approach:** The Investigator chose not to reveal their role. Instead, they actively guided the public discussion by reinforcing correct suspicions, amplifying arguments against suspects, and highlighting incriminating public evidence—such as voting records and deflection tactics—to build a natural consensus.
**Outcome:** The Investigator successfully guided the village to eliminate the wolves without becoming a target or revealing their role. This subtle approach preserved their ability to gather information and contribute to discussions safely, leading to a village victory.

### Memory 6 (observation) [key: 6184533a-22e] (score: 0.8281)
**Situation:** Mid-game, the investigator possesses private, confirmed information about innocent allies, but the public discussion is chaotic, speculative, and lacks clear direction. The village is struggling to find consensus and is at risk of mislynching.
**Approach:** Failing to leverage private knowledge to build a trusted bloc or guide the village, instead either remaining passive and voting with a flawed majority (1x) or actively contributing to deadlock by voting based on personal suspicion rather than confirmed information (1x).
**Outcome:** The investigator's failure to effectively use their private information resulted in the village making critical errors (mislynching innocents, vote deadlocks), ultimately allowing the wolves to win the game. The valuable information was wasted.

### Memory 7 (observation) [key: dffa1e08-f2a] (score: 0.8194)
**Situation:** The Investigator (player_1) was saved by the healer and thus publicly confirmed as town-aligned. Information landscape: The Investigator had public trust but their private investigations had only cleared villagers, giving them no wolf leads to share. Game phase: Early game, after the first night's results were announced.
**Approach:** The Investigator used their credibility to lead the discussion, but targeted a proactive villager (player_6) for being 'too eager', framing their energy as suspicious.
**Outcome:** While the Investigator successfully led the vote, their misjudgment resulted in the elimination of a villager. This also confirmed them as the village leader, making them the wolves' priority target for the following night.

### Memory 8 (observation) [key: fd88ea00-70b] (score: 0.8169)
**Situation:** In the final three, the Investigator (Player 7) revealed their role and their finding that Player 3 was the last wolf. Information landscape: The investigator possessed definitive proof, but this information was private and presented to a villager (Player 6) who was skeptical after a recent mislynch. Game phase: Endgame, with the vote of a single villager deciding the game's outcome. Consensus texture: There was no consensus; the villager was a swing vote between two competing claims.
**Approach:** The Investigator stated their finding but struggled to justify why they had withheld this information on the previous day, which had resulted in the mistaken elimination of a villager (Player 8).
**Outcome:** The villager found the timing of the reveal highly suspicious and sided with the wolf's argument that it was a desperate bluff, leading to the Investigator's elimination and a wolf victory.

### Memory 9 (observation) [key: d8ff9b6f-464] (score: 0.8136)
**Situation:** The Investigator (player_7) identified a wolf (player_1) on the first night but had no public evidence to prove it. Information landscape: The investigator possessed information-rich private knowledge, but the public landscape was information-starved with only behavioral reads available. Game phase: Mid-game, following the first night's elimination of the Healer. Social pressure: Pressure built on the wolf after the Investigator highlighted a logical inconsistency from their Day 1 statements.
**Approach:** The Investigator built a consensus against the wolf by subtly guiding the village, publicly questioning the wolf's contradictory advice from Day 1 and framing it as suspicious behavior, rather than revealing their findings or using voting records.
**Outcome:** The wolf reacted defensively, which led other villagers to become suspicious independently. The village voted out the wolf without the Investigator having to reveal their role, preserving their cover for future nights.

### Memory 10 (observation) [key: 1ab6cc11-497] (score: 0.8089)
**Situation:** Having identified the final wolf on Night 3, the Investigator had to decide when and how to reveal this critical information. Information landscape: The investigator possessed perfect, private information in a public landscape that was otherwise based on speculation. Game phase: Endgame, with only four players remaining (Investigator, two Villagers, one Wolf).
**Approach:** The Investigator waited until the Day 4 discussion to make a clear, public claim against the wolf. They presented the information as a definitive fact and resisted getting drawn into a debate about the timing of the reveal.
**Outcome:** The clear, confident claim rallied the remaining villagers, creating an immediate and unbreakable consensus. The wolf was eliminated, and the town won.

### Memory 11 (observation) [key: a9107742-f0f] (score: 0.8000)
**Situation:** After a villager was mislynched on Day 2, an astute player (the Investigator) used the voting record to scrutinize players who had joined the majority vote. Information landscape: The landscape was becoming information-rich, with the Day 2 voting record providing the first concrete data for analysis. Game phase: Mid-game, with two villagers eliminated, increasing the pressure to find a wolf. Social pressure: The Investigator (player_4) placed evidence-based pressure on a wolf (player_6) for dismissing the importance of the prior day's voting history.
**Approach:** The Investigator framed the wolf's attempt to ignore past data as suspicious behavior, arguing it was a tactic to evade accountability for being part of a villager's elimination.
**Outcome:** This line of reasoning successfully swayed the remaining villagers, building a consensus to vote out the wolf (player_6), marking the village's first correct elimination.

### Memory 12 (observation) [key: a6d1e994-772] (score: 0.7994)
**Situation:** The Investigator attempted to guide the village by pointing out general passivity and a lack of factions, without naming specific suspects. Information landscape: The landscape was information-starved, with the only lead being a saved villager from the night before. Game phase: Mid-game, following the first night action which resulted in a save. This was the first real opportunity for analysis. Consensus texture: There was no consensus, and the village was looking for a direction which the Investigator tried to provide in an abstract way. Social pressure: The targeted villager (player_2) put direct pressure on the Investigator to name a suspect, turning the abstract guidance into a point of suspicion.
**Approach:** The Investigator (player_6) used abstract concepts like 'analyzing ambiguity' to prompt discussion, but this was perceived as evasive and unhelpful when pressed for a concrete name.
**Outcome:** A strong consensus formed against the Investigator, with players finding their abstract talk suspicious. They were voted out, costing the village its most powerful information-gathering role early on.

### Memory 13 (strategy_point) [key: a79b348d-e25] (score: 0.8192)
**Situation:** If you have privately identified a wolf and there is strong, corroborating public evidence, but the village has not yet converged on the target or is wary of a mislynch. Information landscape: You possess certain private knowledge, while the public sphere may be driven by speculative reads or verifiable facts. Game phase: Mid-game or Endgame, where you need to actively build consensus to secure an elimination without revealing your role, especially when the village is under high pressure to avoid a final incorrect vote.
**Action:** Lead the discussion confidently, focusing all arguments on the public evidence. Construct a public case using voting records and behaviors to support your private knowledge, framing your certainty as a strong conviction based on shared evidence rather than an unsubstantiated claim. This allows you to leverage your certainty to build momentum and dismantle defenses without having to reveal your Investigator role or appearing as a wolf forcing a bad vote.

### Memory 14 (strategy_point) [key: 61de853f-6e2] (score: 0.8178)
**Situation:** If you have privately confirmed one or more players as villagers, but revealing your role is too risky. Information landscape: You possess private, information-rich knowledge, while the public sphere is information-starved and prone to speculation. Game phase: Mid-game, when the village is desperate for leads and you need to build influence without becoming a target.
**Action:** Determine your approach based on the village's state: if the town is chaotic or prone to bad decisions, avoid suspicious silence. Instead, subtly guide the conversation by asking probing questions or pointing out logical fallacies in accusations against your confirmed villagers, building a silent alliance. If the village is open to direction, actively and publicly align with the confirmed villager to form a trusted voting bloc, giving your joint accusations more weight.

### Memory 15 (strategy_point) [key: d6b71a52-c14] (score: 0.8168)
**Situation:** If your first investigation confirms a power role (e.g., Healer), but that player is killed by wolves overnight before you can reveal your findings. Information landscape: You hold private, valuable information, but the public information landscape is still starved. Game phase: Early to mid-game, after the first night's kill is revealed.
**Action:** You must become more vocal. Subtly guide the conversation by pointing out that the wolves likely targeted the victim because they were a threat. This builds your credibility without forcing you to make a risky early role claim, and it prevents you from being voted out for being too quiet.

### Memory 16 (strategy_point) [key: 5681a68d-971] (score: 0.8111)
**Situation:** If you have privately identified a wolf, and the village is already suspicious of them based on flawed or speculative reasoning. Information landscape: You possess confirmed, private information, while the village's suspicion is based on a misunderstanding. Consensus texture: A fragile or growing consensus against your target already exists.
**Action:** Do not correct the village's flawed reasoning. Instead, publicly agree with their conclusion while providing your own, separate, behavior-based reasons. This allows you to steer the existing momentum to eliminate a known wolf without exposing your valuable information or role.

### Memory 17 (strategy_point) [key: b98bd43c-79a] (score: 0.8027)
**Situation:** If you have been repeatedly targeted by wolves at night but saved by the healer, or if you have identified a wolf and survived an attack, establishing yourself as a high-value target. Information landscape: Public information confirms you were targeted and saved, and your survival provides a signal of your threat to the wolves, even if your role remains unknown. Game phase: Mid-game, when momentum is crucial and you need to build credibility to lead the village.
**Action:** Use the pattern of being targeted as public evidence of your importance, arguing that wolves would only focus on you so relentlessly if you were a high-value role. If you have identified a wolf, immediately lead the accusation, framing your argument around their suspicious behavior and using your survival as implicit proof that you are a threat to the wolves, rather than explicitly claiming your role.

### Memory 18 (strategy_point) [key: 9c21fe39-320] (score: 0.8007)
**Situation:** If you have been saved by the healer, making you a publicly confirmed town-aligned player. Information landscape: Your alignment is confirmed, giving you immense credibility, but you may lack actionable intelligence. Game phase: Early to mid-game, when you have a significant opportunity to shape the village dynamic.
**Action:** Leverage your trusted status to guide the village's logic and focus their attention on evidence-based reasoning. Act as a facilitator to prevent chaotic mislynches, but allow other vocal villagers to lead direct accusations. This prevents you from appearing dictatorial, keeps the consensus feeling organic, and protects you from being targeted as a high-value player.

### Memory 19 (strategy_point) [key: 82a4ac4c-3ac] (score: 0.8003)
**Situation:** When the village is already rapidly converging on the player you know is a wolf due to your private investigation, based on accurate analysis of public data. Information landscape: Information-rich, with the village correctly interpreting voting records and behavior. Game phase: Mid-game or Endgame, with strong consensus building.
**Action:** Keep your contributions focused and avoid overplaying your hand. Do not reveal your role; instead, amplify the existing public evidence to help the village maintain focus and secure the elimination without risking your own exposure.

### Memory 20 (strategy_point) [key: 29866942-0c4] (score: 0.7917)
**Situation:** If you have privately identified a wolf but lack the public evidence or credibility to lead a direct charge, and the village is in the early to mid-game with an information-starved landscape. You prioritize maintaining your cover and avoiding suspicion, so you cannot reveal your role or your private findings.
**Action:** Do not reveal your role or your finding directly. Instead, act as a sharp villager and guide the conversation by pointing out behavioral evidence and logical flaws in the wolf's statements. Build the public case so the village feels they discovered the wolf through their own logic, which protects you from being targeted. If you are met with coordinated dismissal, pivot to pointing out that the coordinated effort to shut down discussion is itself suspicious and indicative of a pack protecting its own.

### Memory 21 (strategy_point) [key: f25fcf4f-641] (score: 0.7797)
**Situation:** If you have identified a wolf on the first night and need to convince the village when there are no other leads, and the village is receptive to your input. Information landscape: You possess a private, information-rich finding, while the public landscape is information-starved. Game phase: Early game (Day 2). Social pressure: You are initiating the pressure, and the village is open to your lead.
**Action:** Do not reveal your role or frame your accusation as a 'hunch.' Instead, state your case with confidence and build a public case based on the wolf's observable behavior—such as stalling, deflecting, or being vaguely agreeable—to substantiate your claim. Presenting a weak, vibes-based accusation makes you look like a disruptive villager and gives the wolf an easy opening to attack your credibility.

### Memory 22 (strategy_point) [key: 3ad8ba65-371] (score: 0.7783)
**Situation:** If you have identified a wolf with your night action, but the village has no other leads. Information landscape: You possess a piece of concrete information (a wolf's identity), while the public landscape is information-starved. Game phase: Early to mid-game, after the first night. Social pressure: You are about to initiate pressure on a target who is not otherwise suspected.
**Action:** Avoid initiating a case with vague, behavioral evidence, as this often backfires. Instead, gently guide the conversation by pointing out suspicious behaviors from your target and asking other villagers for their interpretations, or wait for the wolf to make a tangible mistake. This frames you as a collaborative investigator; however, if you become the target of a vote, be prepared to reveal your role and finding as a last resort to save yourself and pass on the information.

### Memory 23 (strategy_point) [key: c557f813-1d6] (score: 0.7564)
**Situation:** If you have just successfully led the village to vote out a wolf you investigated. Information landscape: Your arguments have been publicly validated by the wolf's role reveal, making you the most credible voice in the game. Game phase: Mid-game, after a successful, high-profile vote that you orchestrated.
**Action:** Immediately reduce your visibility. Your success has painted a large target on your back. Allow other villagers to lead the next round of discussion. You can guide them subtly, but avoid being the sole accuser again, as the remaining wolves will make you their top priority for the next night kill.

### Memory 24 (strategy_point) [key: 9f51af0e-1e5] (score: 0.7544)
**Situation:** If it is early in the game and you have not yet gathered definitive information from your night actions, leaving the village information-starved. Information landscape: There are no concrete leads, and suspicion is based purely on speculative behavioral reads. Game phase: Early game (Day 1), when wolves are looking for high-value targets and you are vulnerable to both day-time elimination and night-time targeting.
**Action:** Adopt a moderate profile to avoid becoming a target for the wolves' first night kill or drawing suspicion for being overly aggressive. Resist the urge to force an elimination based on weak evidence; instead, use the discussion to ask specific, probing questions to individual players to gauge their reactions and generate new information, while keeping your own role claim in reserve.

### Memory 25 (strategy_point) [key: bd79d243-9a6] (score: 0.7488)
**Situation:** When a suspect tries to deflect blame onto a player you have privately confirmed is a key town role, like the Healer. Information landscape: You have an information advantage, combining public evidence with your private investigation results. Game phase: Mid-game or endgame, when your private information becomes critical to prevent a mislynch. Social pressure: A cornered suspect is trying to sow chaos by accusing a powerful town role.
**Action:** Confidently shut down the accusation without revealing your role or your specific findings. Frame the deflection as a 'desperate move' or 'classic wolf tactic.' Your certainty, backed by the existing public evidence against the suspect, will help solidify the town's consensus.

## Response for Case 18

Rate each of the 25 memories above. JSON format:
```json
[
  {"idx": 1, "key": "a49feaa8-ca9", "type": "observation", "relevance": _},
  {"idx": 2, "key": "3625d761-b7d", "type": "observation", "relevance": _},
  {"idx": 3, "key": "928fde7b-4c7", "type": "observation", "relevance": _},
  {"idx": 4, "key": "bb9b8a2c-f53", "type": "observation", "relevance": _},
  {"idx": 5, "key": "a5db9f55-0d8", "type": "observation", "relevance": _},
  {"idx": 6, "key": "6184533a-22e", "type": "observation", "relevance": _},
  {"idx": 7, "key": "dffa1e08-f2a", "type": "observation", "relevance": _},
  {"idx": 8, "key": "fd88ea00-70b", "type": "observation", "relevance": _},
  {"idx": 9, "key": "d8ff9b6f-464", "type": "observation", "relevance": _},
  {"idx": 10, "key": "1ab6cc11-497", "type": "observation", "relevance": _},
  {"idx": 11, "key": "a9107742-f0f", "type": "observation", "relevance": _},
  {"idx": 12, "key": "a6d1e994-772", "type": "observation", "relevance": _},
  {"idx": 13, "key": "a79b348d-e25", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "61de853f-6e2", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "d6b71a52-c14", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "5681a68d-971", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "b98bd43c-79a", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "9c21fe39-320", "type": "strategy_point", "relevance": _},
  {"idx": 19, "key": "82a4ac4c-3ac", "type": "strategy_point", "relevance": _},
  {"idx": 20, "key": "29866942-0c4", "type": "strategy_point", "relevance": _},
  {"idx": 21, "key": "f25fcf4f-641", "type": "strategy_point", "relevance": _},
  {"idx": 22, "key": "3ad8ba65-371", "type": "strategy_point", "relevance": _},
  {"idx": 23, "key": "c557f813-1d6", "type": "strategy_point", "relevance": _},
  {"idx": 24, "key": "9f51af0e-1e5", "type": "strategy_point", "relevance": _},
  {"idx": 25, "key": "bd79d243-9a6", "type": "strategy_point", "relevance": _}
]
```