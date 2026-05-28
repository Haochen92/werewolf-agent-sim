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

# Case 21: villager — day_vote (day 2 round 2)

## Game State (what the player sees)
```
================================================================================
CASE 8e437de2eab2d9d54e45ed4dee61fe54:3ad1245d1fa8623e | villager | day 2 round 2 | day_vote
================================================================================

Role: villager
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
Continue treating player_1 as a protected anchor. Shift focus to analyzing the content of contributions, as everyone is currently being too agreeable and non-committal. I will remain silent for now to observe if anyone breaks this pattern of platitudes with a concrete, testable suspicion.

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
Also note: who is being evasive, voting inconsistencies, and unresolved accusations.

```

## Golden Situation Query (what we're retrieving for)

**Situation 1:** The healer saved a player on night 1, giving the village one confirmed wolf target, but the day 2 discussion produced nothing beyond generic reactions to the save. All players agree the save is important and suggest monitoring behavior, but no one has offered a specific suspect or theory. Information landscape: Information-starved — the healer save is the only data point; all player contributions are interchangeable generic observations. Game phase: Early game, first vote with all 8 players alive; the village risks going to vote blind. Consensus texture: No consensus — the discussion stagnated in polite agreement with no differentiation. Agent exposure: Invisible — the agent chose to remain silent to observe but no one broke the pattern of platitudes.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 1ed6c526-fe3] (score: 0.8237)
**Situation:** The village had no leads or confirmed roles, leading to a scattered discussion. Information landscape: The landscape was information-starved, with suspicion based purely on speculative reads of early-game communication. Game phase: Early-game (Day 2), after a night with no wolf kill but before any roles were revealed through elimination.
**Approach:** A large number of villagers (five players) formed a bandwagon and voted to eliminate a quiet villager (player_5) without any concrete evidence.
**Outcome:** The village wasted a vote eliminating one of their own, lost a day of progress, and gave the wolves a numbers advantage.

### Memory 2 (observation) [key: 3ebecdce-6fc] (score: 0.8140)
**Situation:** A player (player_1) was publicly saved by the healer, confirming them as town. Despite this information-rich scenario, a massive, unexplained voting consensus formed against the Healer (player_8) on Day 2.
**Approach:** The village, including the confirmed villager and the Investigator, failed to leverage the information of the save and instead formed a majority vote to eliminate the Healer (player_8).
**Outcome:** The village eliminated its only protective role, leaving them vulnerable to wolf attacks. This mistake directly enabled the wolves' subsequent kills and erased the town's advantage.

### Memory 3 (observation) [key: 3edc3901-721] (score: 0.8077)
**Situation:** On the first voting day, the village had no concrete evidence and only general suspicions based on early, generic statements. Information landscape: The environment was information-starved, with no voting records or claims to analyze yet. Game phase: Early game, before the first elimination. Consensus texture: No consensus existed, leading to a day of discussion without a vote.
**Approach:** Rather than forcing a vote on a weak hunch and potentially eliminating a villager, the players discussed generally and allowed the day to end with no elimination. This meant the first concrete data point would be the wolves' night kill.
**Outcome:** Although this gave the wolves a free kill attempt (which was saved by the healer), it prevented a mislynch. The subsequent day began with a known target (the saved player_1), which helped focus the discussion.

### Memory 4 (observation) [key: 60b03843-046] (score: 0.8060)
**Situation:** A player (player_5) who pushed for a mislynch on Day 2 attempted to cast suspicion on a player who was just publicly saved by the healer. Information landscape: The landscape was information-rich, combining the Day 2 voting record with the new fact of a confirmed wolf target. Game phase: Mid-game, with a clear opportunity to identify a wolf based on their reaction to the healer's save. Consensus texture: A strong, unified consensus formed organically among the villagers and the healer against player_5, driven by clear evidence of deflection.
**Approach:** The villagers and healer focused on player_5's illogical attempt to discredit the save, using it as the final piece of evidence needed to confirm their suspicions from the previous day's vote.
**Outcome:** Player_5, a wolf, was decisively voted out, demonstrating how a wolf's poor attempt at misdirection can provide the village with the certainty it needs.

### Memory 5 (observation) [key: 53e65a70-5d0] (score: 0.8056)
**Situation:** On Day 2, despite a lack of hard evidence, a strong majority of villagers independently voted for player_8. Information landscape: The landscape was information-starved, with the only event being a saved player, offering no direct clues about wolf identities. Game phase: Mid-game, at the first vote of the game. Consensus texture: A strong, organic consensus formed rapidly, with 6 out of 8 players voting for the same target without a single vocal leader driving the push.
**Approach:** The villagers converged on a single target based on subtle behavioral cues from the Day 1 and Day 2 discussions.
**Outcome:** The village successfully eliminated a wolf on the first vote with no information roles revealed, giving them a significant early-game advantage.

### Memory 6 (observation) [key: c2489a8b-fd8] (score: 0.8042)
**Situation:** The village, with no concrete leads, was swayed by two wolves who discredited an Investigator's suggestion. Information landscape: The village was information-starved, relying purely on behavioral reads and persuasion rather than voting records or claims. Game phase: Mid-game, Day 2. No eliminations had occurred, so there was no voting record to analyze, making the group susceptible to social pressure. Consensus texture: A strong and rapid consensus formed against the Investigator, driven by the wolves' coordinated dismissal of their ideas.
**Approach:** The majority of villagers and the healer accepted the wolves' framing and voted out the Investigator, believing them to be sowing discord.
**Outcome:** The village eliminated their most powerful information-gathering role, which was a devastating loss. The wolves succeeded in removing their biggest threat without outing themselves.

### Memory 7 (observation) [key: 2b17e5ca-2d8] (score: 0.8026)
**Situation:** On Day 2, with no confirmed roles or strong leads, the discussion stagnated and the vote was split between three different players. The information landscape was information-starved, with accusations based on vibes rather than evidence. A fragile plurality formed against player_1, who was not the initial focus of the day's discussion.
**Approach:** A combination of villagers and wolves (player_3 and player_6) piled onto player_1, who had only received one vote prior, to secure a plurality elimination and break the stagnation.
**Outcome:** Player_1 was revealed to be a villager. The fractured voting allowed the wolves to easily eliminate a villager without exposing themselves, as the blame was spread across multiple villagers, effectively using a villager-initiated mislynch to their advantage.

### Memory 8 (observation) [key: a2b72438-810] (score: 0.7971)
**Situation:** A massive voting bandwagon formed against a quiet villager (player_8) on Day 2, despite the village having confirmed information that player_7 was saved by the Healer. Information landscape: The key piece of information was the Healer's save, yet the vote was driven by speculation and pressure against a quiet player. Game phase: Mid-game, after the first night action revealed a failed wolf attack. Consensus texture: A strong, multi-player consensus formed rapidly against player_8, with six of the eight players voting together.
**Approach:** The majority of the village, including the wolves, Investigator, and Healer, voted to eliminate player_8, who had been quiet. The wolves (player_5, player_6) joined this consensus to hide.
**Outcome:** A villager was eliminated, wasting the information advantage gained from the healer's save. The wolves successfully eliminated a villager without drawing any suspicion to themselves.

### Memory 9 (observation) [key: bcf4cdb5-116] (score: 0.7937)
**Situation:** In an information-starved environment with no prior votes, villagers faced a player who repeatedly pushed for caution and discouraged naming specific suspects. Game phase: Mid-game, building up to the first vote. Consensus texture: A fragile consensus was forming around general suspicions until this specific stalling behavior was identified.
**Approach:** Players noticed that the stalling player was talking about 'voting patterns' when no vote had occurred. Villagers identified this persistent stalling as a contradictory tactic and pressured the player to provide a concrete perspective or face elimination.
**Outcome:** The majority of villagers were persuaded by this evidence-based argument and voted out the stalling player, who was revealed to be a wolf. This demonstrated the effectiveness of pressuring those who encourage inaction and using logical deduction over vague suspicion.

### Memory 10 (observation) [key: 09bd03c1-5fd] (score: 0.7911)
**Situation:** On Day 2, a voting bloc formed to eliminate player_8. Information landscape: The landscape was shifting from information-starved to information-rich, as the Day 2 vote was the first real data point and it yielded a confirmed wolf. Game phase: Mid-game, after one night action (a saved player) but before the first successful elimination. Consensus texture: A fragile consensus formed, with four votes on one player (player_8) and three on another (player_2), but it was enough to secure an elimination.
**Approach:** A group of villagers (and the healer/investigator) converged their votes on player_8, successfully identifying and eliminating a wolf.
**Outcome:** The vote succeeded, revealing a wolf and providing the village with a list of players who voted correctly, thereby increasing trust among that voting bloc.

### Memory 11 (strategy_point) [key: e1c64739-2a7] (score: 0.7377)
**Situation:** In the early game, when the information landscape is speculative, a credible, though unconfirmed, player leads an accusation against another based on behavioral reads, causing a fragile consensus to form. The accused player responds with a weak or evasive defense that focuses on attacking the accuser's motives.
**Action:** Vote with the emerging consensus. In the early game, acting decisively on a strong lead from a credible player is often better than hesitating and allowing wolves another night to kill, provided the accused's defense is evasive rather than substantive.

### Memory 12 (strategy_point) [key: 984356e1-d54] (score: 0.7361)
**Situation:** When a player consistently advocates for caution, delays votes, and demands to wait for patterns while refusing to provide their own concrete suspects. Information landscape: Information-starved, where only behavioral reads and communication styles are available. Game phase: Mid-game, building up to the first critical vote.
**Action:** Treat persistent stalling and refusal to name suspects as a strong wolf indicator, as wolves benefit from inaction and extending information-starved days. Pressure them to name specific suspects or vote for them.

### Memory 13 (strategy_point) [key: f944cdb4-755] (score: 0.7339)
**Situation:** If the game descends into a multi-day stalemate with tied votes, and the information landscape is dominated by confusing and contradictory voting records. Game phase: Endgame, when a single mis-vote will likely lose the game. Consensus texture: A fractured state of gridlock, driven by wolf manipulation and villager frustration.
**Action:** Resist the urge to vote randomly. Instead, re-anchor your focus on the most reliable pieces of information you have, such as which players have been confirmed targets via healer saves. Use this as your ground truth and refuse to vote against them, even if they are at the center of the stalemate's voting blocs. Scrutinize those who have benefited most from the chaos—the ones who argue against analysis.

### Memory 14 (strategy_point) [key: b252d6b2-662] (score: 0.7331)
**Situation:** In the mid-game, when the information landscape is starved and the village lacks a central narrative, votes scatter across multiple players without any consensus. This lack of coordination creates a high risk of wolves orchestrating plurality eliminations of dangerous special roles.
**Action:** Push strongly for a consolidated vote on the single most suspicious player to prevent wolves from quietly orchestrating plurality eliminations of dangerous special roles without leaving a traceable, unified voting bloc.

### Memory 15 (strategy_point) [key: 84d9366f-f06] (score: 0.7312)
**Situation:** If multiple players coordinate to dismiss or suppress the analysis of the only hard evidence available, such as voting records. Information landscape: The information landscape contains concrete evidence (voting patterns), but some players are trying to frame it as irrelevant. Game phase: Mid-game, when analyzing past votes is crucial to finding wolf packs. Social pressure: A coordinated effort is underway to shut down a specific line of inquiry, likely to protect players who benefited from a previous deadlock.
**Action:** Immediately treat the coordinated suppression of evidence as a primary wolf signal. Rally the other villagers to form a voting bloc and eliminate the most vocal player pushing this narrative; failure to consolidate votes in this moment will lead to another deadlock.

### Memory 16 (strategy_point) [key: 2f63bae5-ead] (score: 0.7301)
**Situation:** In the early to mid-game, a fragile consensus forms against a player based on vibes or communication style rather than concrete evidence, often driven by an accuser whose own credibility is unverified. The information landscape is starved of voting records or role claims, and the village is at risk of a miselimination due to social pressure.
**Action:** Resist the urge to vote out a player simply for being aggressive, unpopular, or quiet. Abstain from the vote or vote for a different suspect and demand that the accusers provide concrete evidence. Consider that aggressive behavior can be a frustrated Investigator, while quiet behavior can be a cautious villager or a role-holder trying to avoid attention; weigh the substance of arguments against the deflections of the accuser before casting your vote.

### Memory 17 (strategy_point) [key: de8be6d6-055] (score: 0.7291)
**Situation:** If the village has been paralyzed by consecutive tie votes, and the information landscape is rich with voting data that clearly identifies a consistent bloc of players maintaining the deadlock. Game phase: Mid-game or endgame, when breaking a stalemate is critical for survival. Consensus texture: No consensus, only a recurring stalemate created by two opposing factions.
**Action:** Break the cycle by voting for a new target, specifically targeting members of the bloc that has been voting in unison to create the ties. Convince others that maintaining the status quo is a loss and that forcing a new outcome is the only path forward.

### Memory 18 (strategy_point) [key: 1cc944fd-bf5] (score: 0.7275)
**Situation:** In the mid-game, when the information landscape is starved and the village lacks a central narrative, votes scatter across multiple players without any consensus. This lack of coordination creates a risk that wolves will manipulate a small majority to lynch a villager.
**Action:** Avoid piling onto a weakly supported candidate, as this allows wolves to join a small majority and lynch a villager without taking risks. Instead, consider deliberately forcing a tie or a no-elimination day to gather more information rather than making a low-confidence guess.

### Memory 19 (strategy_point) [key: 3b4ce51c-ffd] (score: 0.7232)
**Situation:** In the mid-game, when trust is low and a recent mislynch has occurred, a single, aggressive accuser pushes for a vote based on subjective behavioral reads rather than voting records or role-based claims. The information landscape is starved, and the accuser is applying intense social pressure to force a quick decision.
**Action:** Consider a counter-vote on the accuser. Forcing them to defend their methods can reveal whether they are an information role with poor communication or a wolf using high-pressure tactics. This move punishes attempts to railroad the village and reinforces a standard for evidence-based decisions.

### Memory 20 (strategy_point) [key: 1e0fde37-272] (score: 0.7206)
**Situation:** When analyzing a past unanimous mislynch of a confirmed power role, and one player aggressively singles out another's participation while ignoring their own identical vote. Information landscape: Information-rich, using documented voting records and a confirmed flipped role. Game phase: Mid-game, right after a significant elimination provides concrete data. Social pressure: Vibes-based pressure weaponizing a previous group mistake.
**Action:** Scrutinize the player selectively weaponizing the unanimous vote; wolves often use the cover of a group mislynch to set up their next target by framing a villager's cautious behavior as protecting a wolf, conveniently omitting their own role in the power role's death.

## Response for Case 21

Rate each of the 20 memories above. JSON format:
```json
[
  {"idx": 1, "key": "1ed6c526-fe3", "type": "observation", "relevance": _},
  {"idx": 2, "key": "3ebecdce-6fc", "type": "observation", "relevance": _},
  {"idx": 3, "key": "3edc3901-721", "type": "observation", "relevance": _},
  {"idx": 4, "key": "60b03843-046", "type": "observation", "relevance": _},
  {"idx": 5, "key": "53e65a70-5d0", "type": "observation", "relevance": _},
  {"idx": 6, "key": "c2489a8b-fd8", "type": "observation", "relevance": _},
  {"idx": 7, "key": "2b17e5ca-2d8", "type": "observation", "relevance": _},
  {"idx": 8, "key": "a2b72438-810", "type": "observation", "relevance": _},
  {"idx": 9, "key": "bcf4cdb5-116", "type": "observation", "relevance": _},
  {"idx": 10, "key": "09bd03c1-5fd", "type": "observation", "relevance": _},
  {"idx": 11, "key": "e1c64739-2a7", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "984356e1-d54", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "f944cdb4-755", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "b252d6b2-662", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "84d9366f-f06", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "2f63bae5-ead", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "de8be6d6-055", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "1cc944fd-bf5", "type": "strategy_point", "relevance": _},
  {"idx": 19, "key": "3b4ce51c-ffd", "type": "strategy_point", "relevance": _},
  {"idx": 20, "key": "1e0fde37-272", "type": "strategy_point", "relevance": _}
]
```