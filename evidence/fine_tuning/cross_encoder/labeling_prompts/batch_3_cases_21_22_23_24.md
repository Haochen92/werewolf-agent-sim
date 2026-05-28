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

---

# Case 22: wolf — day_discussion (day 3 round 1)

## Game State (what the player sees)
```
================================================================================
CASE 8e437de2eab2d9d54e45ed4dee61fe54:41a5d5e693e9daa5 | wolf | day 3 round 1 | day_discussion
================================================================================

Role: wolf
Day: 3, Round: 1

Surviving villagers: player_1, player_2, player_3, player_4, player_5, player_7
Known surviving wolf allies: player_6

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

--- Wolf night chat ---
No messages yet.

--- Strategy note ---
(none)

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
Also note: which villager is most dangerous to leave alive, and whether the pressure on your team could be redirected.

```

## Golden Situation Query (what we're retrieving for)

**Situation 1:** The surviving wolf's partner was eliminated by near-unanimous vote, and the wolf was the only player besides their partner who voted against the consensus — casting a vote for a different target. The healer saved a second player on night 2, meaning the wolves' kill was blocked again. Information landscape: Information-rich — the Day 2 voting record shows the wolf's outlier vote alongside the eliminated partner's, and the second healer save adds another data point. Game phase: Mid-game, day 3 with 7 players and 1 wolf remaining; two consecutive healer saves have prevented wolf kills. Consensus texture: The village should be confident after a correct elimination and may scrutinize the voting record. Agent exposure: Highly exposed — the wolf's outlier vote on day 2 directly links them to the eliminated wolf partner.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 9d1739db-282] (score: 0.8292)
**Situation:** After the village mistakenly eliminated the Healer, the discussion turned to analyzing that vote. Information landscape: The information was rich with voting records from the previous day, which implicated most of the village, including the wolves. Game phase: Mid-game, after two eliminations (Healer by vote, Villager by wolves) had significantly reduced player count. Social pressure: A wolf (player_7) initiated coordinated pressure on a villager (player_5) for being the only player who *didn't* vote for the healer.
**Approach:** Wolf player_7 deflected scrutiny from their own vote against the Healer by framing player_5's lone dissenting vote as suspicious and uncooperative.
**Outcome:** The village turned on player_5, who became defensive and was subsequently voted out. This successfully shifted blame from the wolf and eliminated another villager.

### Memory 2 (observation) [key: f732818d-6b2] (score: 0.8130)
**Situation:** A wolf cast an anomalous vote against the Healer on Day 2, ignoring a massive bandwagon. Information landscape: The vote was a public record, creating hard evidence of an outlier action. Game phase: Mid-game, after one incorrect elimination. Social pressure: The wolf came under intense, coordinated pressure from multiple villagers to justify their specific vote, which they could not do.
**Approach:** The wolf attempted to deflect by criticizing the group's 'bandwagon' mentality and framing the demand for an explanation as a distraction, rather than providing a logical reason for the vote.
**Outcome:** The persistent refusal to provide a specific reason for the vote, combined with the deflection tactics, created a strong consensus that the wolf was hiding something. They were voted out, and their wolf partner also voted for them to maintain cover.

### Memory 3 (observation) [key: b369c51e-969] (score: 0.8058)
**Situation:** A villager (player_2) correctly used Day 2 voting records to accuse a group of players that included both wolves (player_6, player_7) and the healer (player_5). Information landscape: The landscape was becoming information-rich, with voting records being used as the primary evidence. Game phase: Endgame, with only five players remaining and the wolves one elimination away from victory. Social pressure: The wolves coordinated pressure on the accuser (player_2), deflecting the evidence by attacking their previous passivity and framing their valid points as an attempt to sow discord.
**Approach:** The wolves (player_6, player_7) aggressively challenged player_2's motives for suddenly becoming vocal, ignoring the voting evidence player_2 presented.
**Outcome:** This tactic successfully shifted suspicion onto player_2. The healer (player_5) was convinced by the wolves' narrative and voted with them, leading to another villager's elimination and a wolf victory.

### Memory 4 (observation) [key: 83487df0-7a8] (score: 0.8030)
**Situation:** After the village mistakenly eliminated the Investigator, the discussion fractured over whether to analyze that disastrous vote. Information landscape: The information landscape was information-rich regarding the Day 2 vote (a confirmed mislynch of a power role), but poor otherwise. Game phase: Mid-game, with both the Investigator and Healer eliminated, leaving the village with no special roles. Social pressure: A villager (player_4) came under pressure for arguing that analyzing the past vote was a waste of time, a position that objectively benefited the wolves.
**Approach:** One wolf (player_5) publicly agreed with the villager's flawed logic to amplify the conflict, while both wolves voted for a different target (player_1) to ensure a villager was eliminated regardless of the outcome of the main dispute.
**Outcome:** The villagers focused their votes on the contrarian villager (player_4) and eliminated them, while the wolves' split vote eliminated a village leader and sowed more confusion.

### Memory 5 (observation) [key: ceef18b3-1e8] (score: 0.8008)
**Situation:** Mid-game, with an information-rich landscape. The agent, a wolf, is the primary target, facing extreme and coordinated village pressure based on strong evidence from voting records linking them to a past miselimination or an eliminated partner.
**Approach:** Attempting to deflect blame by claiming to have followed group consensus (1x), and arguing the evidence was 'too obvious' using reverse psychology (1x).
**Outcome:** The deflection attempts were recognized as evasive tactics and failed to create doubt against the strong evidence. The village consensus held, leading to the wolf's elimination.

### Memory 6 (observation) [key: 1fbc6519-4ae] (score: 0.7985)
**Situation:** In the final vote with four players left, the villagers were trying to identify the last wolf. Information landscape: The landscape was rich with voting history, but no confirmed roles remained besides the knowledge that a Healer was active. Game phase: Endgame, after one wolf and several villagers had been eliminated. Social pressure: Pressure was put on player 2 (the Healer) for being consistently passive and evasive when asked to name a suspect.
**Approach:** Wolf 6 joined the other villagers in pressuring player 2, framing their quiet, observational style as suspicious wolf behavior designed to avoid taking a stand.
**Outcome:** The villagers were convinced and voted out player 2, the Healer. This removed the final power role and secured the win for the wolves.

### Memory 7 (observation) [key: 79288222-86d] (score: 0.7969)
**Situation:** In an information-starved mid-game, a proactive villager aggressively demands that players name suspects, putting pressure on the wolves. The village has no consensus and the only lead is a recent healer save. The wolves are not the primary target but are under pressure to contribute.
**Approach:** Frame a proactive villager's aggression as a suspicious tactic to force a rushed, chaotic vote (1x), while urging caution and claiming there is not enough evidence to act (1x).
**Outcome:** The village, lacking other leads, turns on the aggressive villager, leading to their elimination. This removes a proactive town member and successfully deflects suspicion from the wolves.

### Memory 8 (observation) [key: 084c2417-f2d] (score: 0.7937)
**Situation:** Mid-game, a wolf was under intense, evidence-based pressure due to their voting record. The information landscape was rich with voting data that villagers were actively analyzing to find inconsistencies.
**Approach:** The wolf attempted to deflect scrutiny from their voting record. Tactics included misrepresenting the public voting record to create a false narrative of group responsibility (1x) and aggressively arguing that analyzing past votes was counterproductive (1x).
**Outcome:** The deflection attempts failed as villagers interpreted the resistance and dishonesty as clear signs of guilt. The wolf's credibility was destroyed, leading to a strong consensus for their swift elimination.

### Memory 9 (observation) [key: fb99dc92-c15] (score: 0.7913)
**Situation:** A wolf (player_2) was put under pressure for voting against a player (player_1) who was later killed by the wolves. Information landscape: The evidence was the wolf's own voting record, which now directly linked them to a wolf kill. Game phase: Mid-game, with the village looking for hard evidence to act on. Consensus texture: A strong consensus formed against the wolf, driven by multiple villagers citing the same voting evidence. Social pressure: Heavy, evidence-based pressure was applied to player_2, who was questioned by three separate players.
**Approach:** The wolf's approach was to deflect, provide vague answers like 'suspicious behavior,' and accuse the primary questioner (player_5) of being aggressive and manufacturing a narrative.
**Outcome:** This defensive strategy failed catastrophically. The lack of a specific alibi was interpreted as guilt, leading to a decisive vote against the wolf.

### Memory 10 (observation) [key: a394b860-e1b] (score: 0.7901)
**Situation:** The village had a twice-confirmed non-wolf (player_7) who became aggressive in trying to hunt wolves after a prior mislynch. Information landscape: Information was rich regarding player_7's status, but the discussion was dominated by arguments over the previous day's voting record. Game phase: Mid-game, after the village had mistakenly eliminated a villager (player_8). Social pressure: Player_7 was putting pressure on the players who voted for player_8, while player_4 was pressuring player_7 for their 'outlier' vote, creating village infighting.
**Approach:** The wolves (player_5 and player_6) exploited the village's frustration with player_7's aggressive accusations. They framed player_7 as being disruptive and joined the vote against them.
**Outcome:** The village voted out their most confirmed non-wolf player. This was a massive victory for the wolves, as they manipulated the village into eliminating its own strongest asset.

### Memory 11 (strategy_point) [key: a7c6ac54-d43] (score: 0.8141)
**Situation:** When a wolf target is saved by the healer and the village begins discussing the motive behind the attack. Information landscape: The village has a confirmed non-wolf player to rally around, making the landscape information-rich. Game phase: Mid-game, when the first night attack is revealed. Strategic context: You prefer to maximize integration by appearing helpful.
**Action:** Do not attempt to divert the conversation to vague behavioral traits like 'quiet players.' Instead, actively participate in analyzing the failed kill, proposing theories about why that player was targeted, to appear aligned with the village's goals and avoid suspicion.

### Memory 12 (strategy_point) [key: fc5e48a9-5cb] (score: 0.7919)
**Situation:** When a wolf target is saved by the healer and the village begins discussing the motive behind the attack. Information landscape: The only new information is the failed attack, meaning discussion is based on speculative reads. Game phase: Mid-game, when the first night attack is revealed. Strategic context: You prefer to minimize attention on the failed kill.
**Action:** Do not attempt to justify the attack by framing the survivor as a 'threat,' as this inadvertently validates the wolves' choice and implies insider knowledge. Instead, agree that the save was fortunate and quickly pivot the conversation towards a different player or a general strategy to avoid suspicion.

### Memory 13 (strategy_point) [key: 7eebdf18-9f1] (score: 0.7904)
**Situation:** When a player who is confirmed non-wolf (e.g., saved by the healer) becomes aggressive and polarizing in discussions. Information landscape: The village has a trusted voice, but that voice is causing infighting and frustration by focusing on past mistakes. Game phase: Mid-game, when village morale may be low after a mislynch. Consensus texture: The consensus is fractured, with some supporting the confirmed player and others growing tired of their aggressive tone.
**Action:** Amplify the village's frustration. Subtly frame the confirmed player as 'disruptive,' 'unhelpful,' or 'causing chaos' to turn public opinion against them. This can manipulate the village into eliminating one of its most valuable assets.

### Memory 14 (strategy_point) [key: 17add23c-00b] (score: 0.7830)
**Situation:** Mid-game, after a villager has been incorrectly eliminated. Information landscape: The voting record from the mislynch is the primary evidence being discussed. Social pressure: You and your partner are both under pressure as key participants in the failed vote, creating a risk of coordinated suspicion.
**Action:** Avoid using the exact same deflection tactic as your partner. If you both argue to 'move on from the past,' it creates a strong rhetorical link that exposes you both. Instead, one of you should shift blame to a specific villager who also voted that way, while the other focuses on a different line of reasoning to create distance.

### Memory 15 (strategy_point) [key: 21399e68-38b] (score: 0.7796)
**Situation:** When the village is conducting a post-mortem on a mislynch that you or your partner participated in or led, and you are not currently the primary target of suspicion. Information landscape: Information-rich, grounded in the public voting record of the eliminated villager. Game phase: Mid-game, immediately following a village mislynch. Social pressure: Low to moderate; you are not under direct attack.
**Action:** Actively participate in the post-mortem and offer a plausible, pro-village alternate explanation for the voting momentum rather than telling the village to 'stop looking at the past.' Outright dismissing the analysis signals you have something to hide and draws immediate suspicion.

### Memory 16 (strategy_point) [key: e552a4ce-f55] (score: 0.7694)
**Situation:** Mid-game, when the village has made a major error in a previous vote and is now conducting a post-mortem to identify scapegoats or leaders of that failed vote, and you are not yet under direct, evidence-based scrutiny. Information landscape: The landscape is rich with data from the mistaken vote, including specific voting records. Social pressure: The village is focused on assigning blame for the past mistake.
**Action:** Actively frame the mistake as a 'collective failure' or 'groupthink.' Argue that dwelling on it breeds paranoia and that the village should focus on 'present behavior.' This deflects scrutiny from your own role in the vote and makes anyone who insists on analyzing it seem unproductive or suspicious themselves.

### Memory 17 (strategy_point) [key: e1428900-f94] (score: 0.7664)
**Situation:** Mid-game, when the village is analyzing voting records or past events to identify suspicious patterns, and you are under organic pressure regarding your own voting history. Information landscape: The landscape is shifting from speculative to evidence-based, using voting records as the primary data source. Social pressure: Multiple players are coordinating questions, putting you on the defensive.
**Action:** Do not engage with the evidence directly. Instead, attack the process of analysis itself by framing the discussion as 'circular,' 'infighting,' or 'relitigating the past,' and argue that the village should 'move on' to find 'real leads.' Simultaneously, deflect scrutiny by launching a suspicion-based accusation against a quiet player to shift the focus away from your own voting record.

### Memory 18 (strategy_point) [key: ef42a0e8-ce5] (score: 0.7655)
**Situation:** Mid-game, after a major town power role has been mistakenly eliminated. The village is analyzing the voting records of the mistaken majority, leaving you vulnerable. There is one player who voted differently from the majority.
**Action:** Aggressively question the lone dissenting voter. Frame their non-conformity as suspicious and demand an explanation to deflect blame from your own participation in the bad vote and weaponize the village's regret against an innocent player.

### Memory 19 (strategy_point) [key: 09f24ec7-55c] (score: 0.7645)
**Situation:** If your wolf partner is exposed by compelling evidence and their elimination is imminent or has just occurred. Information landscape: The information landscape is rich against your partner, based on confirmed roles or damning voting records. Game phase: Endgame, when your connection to your partner is under scrutiny and a strong consensus has formed.
**Action:** Vote with the majority to eliminate your partner to establish credibility. After the elimination, do not attack those who voted for your partner, as this appears defensive. Instead, praise the village for the successful elimination to build trust, then subtly pivot to a new target by re-interpreting old evidence.

### Memory 20 (strategy_point) [key: f13b30ab-02a] (score: 0.7585)
**Situation:** Mid to endgame, when you participated in a majority vote that was later revealed to be a major mistake, and you are under direct, evidence-based pressure from villagers scrutinizing your specific role in the vote. Information landscape: Information-rich, with voting records being the primary evidence used against you. Social pressure: You are the primary target of suspicion.
**Action:** Immediately go on the offensive by accusing the villagers who voted with you. Frame them as the leaders of the failed consensus and yourself as a reluctant follower. This 'history rewriting' deflects blame and creates infighting among villagers, paralyzing their ability to form a new consensus against you.

## Response for Case 22

Rate each of the 20 memories above. JSON format:
```json
[
  {"idx": 1, "key": "9d1739db-282", "type": "observation", "relevance": _},
  {"idx": 2, "key": "f732818d-6b2", "type": "observation", "relevance": _},
  {"idx": 3, "key": "b369c51e-969", "type": "observation", "relevance": _},
  {"idx": 4, "key": "83487df0-7a8", "type": "observation", "relevance": _},
  {"idx": 5, "key": "ceef18b3-1e8", "type": "observation", "relevance": _},
  {"idx": 6, "key": "1fbc6519-4ae", "type": "observation", "relevance": _},
  {"idx": 7, "key": "79288222-86d", "type": "observation", "relevance": _},
  {"idx": 8, "key": "084c2417-f2d", "type": "observation", "relevance": _},
  {"idx": 9, "key": "fb99dc92-c15", "type": "observation", "relevance": _},
  {"idx": 10, "key": "a394b860-e1b", "type": "observation", "relevance": _},
  {"idx": 11, "key": "a7c6ac54-d43", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "fc5e48a9-5cb", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "7eebdf18-9f1", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "17add23c-00b", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "21399e68-38b", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "e552a4ce-f55", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "e1428900-f94", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "ef42a0e8-ce5", "type": "strategy_point", "relevance": _},
  {"idx": 19, "key": "09f24ec7-55c", "type": "strategy_point", "relevance": _},
  {"idx": 20, "key": "f13b30ab-02a", "type": "strategy_point", "relevance": _}
]
```

---

# Case 23: wolf — day_vote (day 2 round 2)

## Game State (what the player sees)
```
================================================================================
CASE 8e437de2eab2d9d54e45ed4dee61fe54:4056280ea3a1c9ec | wolf | day 2 round 2 | day_vote
================================================================================

Role: wolf
Day: 2, Round: 2

Surviving villagers: player_1, player_2, player_3, player_4, player_5, player_7
Known surviving wolf allies: player_6, player_8

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

--- Wolf night chat ---
No messages yet.

--- Strategy note ---
Maintain a low profile while participating in discussions to appear helpful. If I need to contribute, I will offer a non-committal observation about player behaviors rather than attacking anyone directly. If pressured, I will pivot to discussing patterns in general to avoid drawing attention to the failed kill.

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
Also note: which villager is most dangerous to leave alive, and whether the pressure on your team could be redirected.

```

## Golden Situation Query (what we're retrieving for)

**Situation 1:** The wolf pair's night kill was blocked by the healer, and the subsequent discussion has been entirely generic — no player has made specific accusations or distinguished themselves. Both wolves must navigate a first vote with no leads, avoiding creating a voting record that links them. Information landscape: Information-starved — the healer save is the only data point; no behavioral differentiation among players. Game phase: Early game, first vote with all 8 players alive; the wolves need to avoid casting suspicious votes that could be analyzed later. Consensus texture: No consensus — the discussion is stagnant with generic observations. Agent exposure: Low — the wolf has maintained a low profile with non-committal contributions matching the group's tone.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 12224812-1ea] (score: 0.7996)
**Situation:** After the investigator was eliminated, the village had no clear leads, and the discussion was fragmented with multiple potential targets. Information landscape: The landscape was information-starved, driven entirely by speculative reads following the investigator's elimination. Game phase: Mid-game, with the village weakened by the loss of their investigator. Consensus texture: There was no consensus, with votes scattered across several players.
**Approach:** The two wolves (player_5, player_6) coordinated to vote for two different, plausible villager targets (player_1 and player_8). This intentionally split the overall vote to force a tie.
**Outcome:** The vote resulted in a tie, and no one was eliminated. This tactic successfully bought the wolves one additional night to kill a villager, advancing their win condition without losing a pack member.

### Memory 2 (observation) [key: 4d55e9f0-6c2] (score: 0.7948)
**Situation:** On Day 2, the two wolves (Player 1 and Player 4) both voted for the same villager (Player 8), helping to create a 4-4 tie. This stalled the game for a day. Information landscape: The landscape was information-starved as it was the first vote, with only Day 1 discussions as a basis for suspicion. Game phase: Early-game, this was the first vote and it resulted in no elimination. Consensus texture: There was no consensus, resulting in a split vote and a tie deliberately engineered by the wolves.
**Approach:** The wolves coordinated their votes on a single villager as part of a bloc to create a tie with another villager who was receiving votes, successfully preventing an elimination.
**Outcome:** While the tie was successful in the short term, the voting record permanently linked Player 1 and Player 4. This record was later used as key evidence to identify and eliminate both of them.

### Memory 3 (observation) [key: cd1368ff-c32] (score: 0.7881)
**Situation:** The wolves, player_1 and player_5, successfully engineered a voting deadlock between two villagers for two consecutive days. Information landscape: The village was information-starved, relying on behavioral reads and speculative accusations with no confirmed roles. Game phase: Mid-game, after one villager elimination. The wolves created a stalemate that prevented any further information from being revealed via voting. Consensus texture: There was no consensus, but rather a fragile, engineered 4-4 split in the vote on Day 2, followed by a 3-3 split on Day 3, with the wolves' votes being the deciding factor in maintaining the tie. Social pressure: Social pressure was concentrated on the two deadlocked players (player_6 and player_8), deflecting all suspicion from the wolves who were orchestrating the chaos.
**Approach:** The two wolves (player_1 and player_5) split their votes each day between the two main targets (player_6 and player_8), ensuring no majority could be reached and no one would be eliminated.
**Outcome:** The village failed to eliminate anyone for two days, giving the wolves a free kill and allowing them to eliminate the Investigator after he became a target of the deadlock they created.

### Memory 4 (observation) [key: 3ce9912f-493] (score: 0.7864)
**Situation:** A wolf attempted to eliminate the primary night kill target (the Healer) via a day vote while the rest of the village was consolidating a successful vote against the wolf's partner. Information landscape: Information-rich, with voting data making the wolf's deviation highly visible. Game phase: Mid-game, after one night with a saved kill. Consensus texture: A strong, multi-player consensus formed against the wolf's partner, making the outlier vote against the Healer a clear, incriminating data point.
**Approach:** The wolf cast an outlier vote against the protected target (the Healer), effectively aligning with their wolf partner's vote instead of blending in with the village consensus.
**Outcome:** The village recognized the alignment between the wolf's day vote and the wolves' night actions, using this vote as primary evidence to identify and eliminate the wolf on the following day.

### Memory 5 (observation) [key: 8e6e3cbd-d31] (score: 0.7863)
**Situation:** A wolf (player_6) cast a dissenting vote for a villager (player_8) alongside their wolf partner (player_2), who was the primary target of a successful town vote. Information landscape: The vote was information-rich, based on a strong consensus that player_2's defensive behavior was wolf-like. Game phase: Mid-game, at the conclusion of the first elimination vote. Consensus texture: A strong consensus driven by multiple villagers converged on player_2.
**Approach:** Both wolves (player_6 and player_2) cast a dissenting vote against a villager instead of joining the majority to eliminate the exposed partner.
**Outcome:** This coordinated vote created an undeniable public record linking player_6 to the confirmed wolf, player_2. This became the primary evidence used to eliminate player_6 the next day, costing the wolves the game.

### Memory 6 (observation) [key: 07265d73-9b4] (score: 0.7751)
**Situation:** During the mid-game, the village was divided, with suspicion split between the two wolves and a vocal villager. Information landscape: The landscape was rich with voting records, but interpretation was contentious, creating fractured pockets of suspicion. Game phase: Mid-game, with the village trying to recover from the Investigator's mislynch. Consensus texture: There was no consensus, with several small factions pushing different targets.
**Approach:** The wolves (player_1 and player_4) voted in unison for a vocal villager (player_7) who was not their primary accuser. This action was designed not to eliminate the villager, but to create a three-way tie with themselves.
**Outcome:** The vote resulted in a tie, meaning no one was eliminated. This tactic successfully stalled the game for two consecutive days, allowing the wolves to get free night kills and win through attrition.

### Memory 7 (observation) [key: 5d53cedb-aac] (score: 0.7734)
**Situation:** The village vote was split between two main targets, with one bloc of villagers coalescing around eliminating a suspicious player. Information landscape: The vote was based on conflicting interpretations of a previous day's voting record. Game phase: Endgame, with 6 players remaining (2 wolves, 4 villagers). Consensus texture: A fragile consensus was forming around one villager (player_4), but it was not unanimous.
**Approach:** Instead of joining the majority to vote out player_4, the two wolves coordinated to vote for a different, more influential villager (player_1).
**Outcome:** The villager bloc eliminated their target (player_4), but the wolves' votes on player_1 were noted, creating ambiguity about their allegiances while still ensuring a villager was removed. This play helped them avoid suspicion.

### Memory 8 (observation) [key: 42dfb995-f6d] (score: 0.7713)
**Situation:** A wolf's partner (player_2) was targeted by a strong village consensus, making their elimination almost certain. Information landscape: The evidence against the targeted wolf was behavioral but had convinced a large majority of the village. Game phase: Mid-game, during the first elimination vote of the game. Consensus texture: A strong, multi-player consensus had formed against the wolf, driven by their passive and evasive responses. Note: The remaining wolf had previously defended the partner.
**Approach:** The remaining wolf (player_5) chose to vote along with the majority to eliminate their own partner, a tactic known as 'bussing'.
**Outcome:** While this saved the wolf from suspicion on that day's vote, their prior actions of defending their partner were remembered. The next day, villagers used this previous alliance as primary evidence to identify and eliminate the second wolf.

### Memory 9 (observation) [key: b1b6a7aa-5ce] (score: 0.7677)
**Situation:** During a vote where a strong consensus had formed, a wolf cast a lone, unexplained vote for a different player. Information landscape: The vote was an information-rich event, creating a permanent public record of the wolf's anomalous action. Game phase: Mid-game, after the first elimination revealed the Investigator, making subsequent votes more scrutinized.
**Approach:** The wolf (player_3) voted for a random villager (player_8) instead of joining the majority vote. The next day, they defended this by claiming they were avoiding 'groupthink'.
**Outcome:** This single vote drew intense scrutiny the following day. The wolf's weak justification failed, and the village used the voting record as concrete evidence to correctly eliminate them.

### Memory 10 (observation) [key: 538ff88c-351] (score: 0.7604)
**Situation:** A wolf's (player_5) cover was blown, and a near-unanimous consensus formed to eliminate them. Information landscape: The information was rich with behavioral evidence, as the wolf's attempts to deflect were universally seen as suspicious. Game phase: Mid-game, during the first elimination vote of the game. Consensus texture: A strong, multi-player consensus formed organically against the wolf.
**Approach:** The second wolf (player_1) initially attempted to defend their partner before recognizing the inevitable and voting with the majority to eliminate them.
**Outcome:** While this vote helped the second wolf survive the day, their earlier defense of the confirmed wolf became the primary evidence used against them on the following day, leading to their elimination.

### Memory 11 (strategy_point) [key: 33204b05-f60] (score: 0.7665)
**Situation:** Mid-game, during a critical vote where the information landscape is defined by conflicting behavioral reads. A fragile consensus is forming against your wolf partner, but a clear counter-accusation against a villager is gaining traction, making the vote swingable.
**Action:** Vote for the other accused player rather than your partner. This adds a vote to a plausible alternative, creating chaos and potentially splitting the vote enough to cause a no-elimination result, which is safer than attempting to defend your partner directly.

### Memory 12 (strategy_point) [key: 42a05e82-310] (score: 0.7372)
**Situation:** Endgame, when few players remain and every vote is heavily scrutinized. A strong, evidence-based consensus has formed against your wolf partner, making their elimination inevitable.
**Action:** Do not cast a futile vote to save them or a protest vote against their main accuser. Instead, vote against a different, less suspicious villager to create a confusing signal and avoid cementing your partnership on the permanent voting record, which would make you the obvious next target.

### Memory 13 (strategy_point) [key: 21798fee-51a] (score: 0.7322)
**Situation:** When the player you attempted to kill overnight is saved by the Healer and their survival is publicly announced. Information landscape: Information-rich, with the target's protected status known to all players. Game phase: Mid-game, immediately following a public save.
**Action:** Do not vote for this protected player during the day phase to avoid a consensus or express suspicion. Voting against a publicly confirmed night target signals to the village that your motives align with the wolves, instantly destroying your cover.

### Memory 14 (strategy_point) [key: e9294fd5-f1a] (score: 0.7252)
**Situation:** When a few scattered, speculative votes are placed on a high-value town role who is not otherwise a major suspect. Information landscape: Suspicion is vibes-based and not supported by strong evidence. Game phase: Mid-game, when the village is desperate for a lead. Consensus texture: There is no strong consensus, making the vote vulnerable to being swayed.
**Action:** Coordinate with your wolf partner to quickly pile onto the votes. This creates the illusion of a sudden, organic consensus, often panicking other villagers into joining the bandwagon and mislynching a key town role.

### Memory 15 (strategy_point) [key: b4116bf9-a06] (score: 0.7218)
**Situation:** Mid- to late-game, when the village is deadlocked with suspicion split between multiple players and no strong consensus is forming. The information landscape is complex, with conflicting theories preventing a clear voting direction, creating an opportunity to manipulate the vote into a deadlock.
**Action:** Coordinate with your wolf partner to force a tie and prevent an elimination. You can either split your votes between the two primary targets or pile your votes on a third, vocal villager who is not currently a primary suspect to create a three-way tie. This denies the village information, guarantees a free night kill, and increases village frustration and paranoia.

### Memory 16 (strategy_point) [key: bb4a5e5a-11a] (score: 0.7158)
**Situation:** Mid-game, when a strong, multi-player consensus is forming against your wolf partner based on behavioral evidence or suspicious statements, making their elimination inevitable.
**Action:** Vote with the majority to eliminate your partner to preserve your cover, ideally by pivoting early to contribute to the case. Do not fiercely defend them only to bus them at the last second, as this makes the vote appear transparently self-serving; similarly, avoid protest votes that create a permanent, public link to your partner.

### Memory 17 (strategy_point) [key: 62ef36a8-ddd] (score: 0.7037)
**Situation:** Mid to late game, when the village is desperate for a kill and a strong, multi-player consensus is forming against a villager based on flawed social reads. Your vote is not needed to secure the elimination, providing an opportunity to safely dissent.
**Action:** Cast a dissenting vote for a different suspicious player. Before doing so, construct a specific and plausible reason for targeting that player. If questioned, deliver this reason confidently; do not resort to vague criticisms of 'groupthink,' as this appears evasive. This creates a record of you not supporting the mislynch, which you can use on the following day to build credibility and distance yourself from the village's mistake.

### Memory 18 (strategy_point) [key: 6ef092b3-32e] (score: 0.7036)
**Situation:** Mid to endgame, when the village vote is split between two or more targets and your pack cannot swing the outcome. The information landscape is characterized by conflicting theories and divided factions, making a deadlock less desirable than sowing chaos.
**Action:** Coordinate with your partner to vote for a third player who is not currently under suspicion, preferably a vocal leader. This ensures a villager is eliminated regardless of the main conflict and creates confusion about your motives on the following day.

## Response for Case 23

Rate each of the 18 memories above. JSON format:
```json
[
  {"idx": 1, "key": "12224812-1ea", "type": "observation", "relevance": _},
  {"idx": 2, "key": "4d55e9f0-6c2", "type": "observation", "relevance": _},
  {"idx": 3, "key": "cd1368ff-c32", "type": "observation", "relevance": _},
  {"idx": 4, "key": "3ce9912f-493", "type": "observation", "relevance": _},
  {"idx": 5, "key": "8e6e3cbd-d31", "type": "observation", "relevance": _},
  {"idx": 6, "key": "07265d73-9b4", "type": "observation", "relevance": _},
  {"idx": 7, "key": "5d53cedb-aac", "type": "observation", "relevance": _},
  {"idx": 8, "key": "42dfb995-f6d", "type": "observation", "relevance": _},
  {"idx": 9, "key": "b1b6a7aa-5ce", "type": "observation", "relevance": _},
  {"idx": 10, "key": "538ff88c-351", "type": "observation", "relevance": _},
  {"idx": 11, "key": "33204b05-f60", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "42a05e82-310", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "21798fee-51a", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "e9294fd5-f1a", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "b4116bf9-a06", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "bb4a5e5a-11a", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "62ef36a8-ddd", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "6ef092b3-32e", "type": "strategy_point", "relevance": _}
]
```

---

# Case 24: healer — day_discussion (day 2 round 3)

## Game State (what the player sees)
```
================================================================================
CASE cdcd2c6e46f59a85cad3d634c3595a67:8e1d5f6659a9a2d4 | healer | day 2 round 3 | day_discussion
================================================================================

Role: healer
Day: 2, Round: 3

Surviving players: player_2, player_4, player_5, player_6, player_7, player_3, player_8

--- Previous days summary ---
[Day 1]
Key accusations: None. Defenses: None. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: None. The Day 1 discussion remained neutral and cautious, with all players (player_1 through player_8) exchanging general pleasantries, emphasizing the need for caution, and expressing a shared reluctance to jump to conclusions or force a quick lynch without evidence.

[Day 1]
Day 1: No vote was held today.

[Day 1]
player_1 was killed by the wolves last night. They were a villager.

--- Today's public discussion ---
[Day 2, Round 1] player_2: It is unfortunate that we lost player_1. Given we have no information, I suggest we pay close attention to anyone who tries to steer the conversation too forcefully today.
[Day 2, Round 1] player_4: Since we lost a villager, we need to move past the initial hesitation. Does anyone have a specific observation about last night's events or a suspicion regarding who was quiet during Day 1?
[Day 2, Round 1] player_5: It's a tough start losing player_1. Since we didn't vote yesterday, we don't have much to go on yet. Let's not just sit around being polite; does anyone have a read on why the wolves might have picked them, or notice anything odd about how people are acting right now?
[Day 2, Round 1] player_6: It's unfortunate about player 1. Since they were a villager, we've lost a town member early on. Does anyone have any thoughts on why they might have been targeted, or did anyone notice anything suspicious during yesterday's round?
[Day 2, Round 1] player_7: Since we lost player_1, we really need to move past the general pleasantries. Everyone, let's name one person you find suspicious and why, even if it's just a gut feeling for now. We can't afford to be passive while the wolves chip away at us.
[Day 2, Round 1] player_3: It is unfortunate about player_1. Given we have so little information, we really need to be careful not to jump to conclusions and accidentally hit a villager.
[Day 2, Round 1] player_8: It is really unfortunate about player_1. Does anyone have any thoughts on how we should handle today given we have so little information to go on?
[Day 2, Round 2] player_8: I agree with player 3 that we should be careful. Pushing for a lynch right now without any real leads feels reckless and might just play into the wolves' hands by letting them manipulate the group into an easy mistake.

--- Strategy note ---
Maintain a low profile to avoid being a high-value target. Observe others' reactions to the prompt for suspicions, looking for those who deflect or act overly eager to lynch. Continue to reserve the healer protection for someone who proves to be a vocal, logical asset to the village.

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

**Situation 1:** A villager was killed on the first night without a healer save, and the day 2 discussion is split between players pushing for immediate action and players urging caution. Some demand suspects be named, while others argue that forcing a vote without evidence is reckless. Information landscape: Completely information-starved — no healer save, no voting records, no role claims; the only event is the night kill. Game phase: Early game, day 2 with 7 players remaining; the failed healer protection means the village lost a member with no information gained. Consensus texture: Polarizing — an emerging split between proactive and cautious players, with neither faction offering evidence. Agent exposure: The healer failed to protect on night 1 and must blend in while processing the failed save; taking too strong a position risks drawing wolf attention.

## Retrieved Memories to Label

### Memory 1 (observation) [key: a7ca80e1-7bc] (score: 0.8281)
**Situation:** With the village dwindling and no clear leads, the healer (player_2) took an active role in the Day 3 discussion to analyze behavioral patterns. Information landscape: The key evidence was the voting record from Day 2 and the consistent alignment in rhetoric between two players (player_3 and player_8). Game phase: Mid-game, where a correct lynch was critical to stop the villagers from being outnumbered. Consensus texture: The healer was instrumental in building a strong, evidence-based consensus against the wolf pair.
**Approach:** The healer (player_2) directly challenged the suspicious pair, pointing out how their coordinated calls for caution were tactically aligned and demanding a better explanation. This helped focus the village's attention.
**Outcome:** The healer's logical arguments helped solidify the vote against a wolf (player_3). Although the healer was killed the next night, their contribution was crucial for turning the game in the villagers' favor.

### Memory 2 (observation) [key: 434ca33b-17d] (score: 0.8181)
**Situation:** The Healer was facing a near-unanimous vote for elimination on Day 2. Information landscape: There was no evidence presented against the Healer; the vote was based on unsubstantiated and uncoordinated suspicion. Game phase: Mid-game, after one night. The Healer's successful save had just been announced. Social pressure: Overwhelming, organic pressure from most of the village converged on the Healer without a clear source.
**Approach:** The Healer (player_8) did not claim their role to try and prevent their elimination. Instead, they cast a single, unexplained vote against a wolf (player_3).
**Outcome:** The Healer was eliminated, dealing a devastating blow to the village's chances of winning. Their failure to claim under duress cost the town its only means of nightly protection.

### Memory 3 (observation) [key: a786957c-bc1] (score: 0.8149)
**Situation:** On Day 1, the Healer (Player 1) took an active role in trying to start conversations and organize the group's thoughts. Information landscape: It was the start of the game, so the information landscape was completely blank. Game phase: Early-game, with all players still alive.
**Approach:** The Healer acted as a facilitator, asking questions and prompting others to share their initial hunches in an attempt to get the town working together.
**Outcome:** This proactive behavior made the Healer stand out as a potential leader, causing the wolves to identify them as a high-priority target. They were killed on the first night.

### Memory 4 (observation) [key: c7cf1300-438] (score: 0.8048)
**Situation:** After successfully protecting a player on Night 1, the Healer became an influential voice in the Day 2 discussion. Information landscape: The only information was that a save had occurred, confirming the Healer was active and effective. Game phase: Mid-game, with all players still alive.
**Approach:** The Healer (player_2) engaged actively in the discussion, attempting to guide the village.
**Outcome:** The Healer's increased influence likely drew the wolves' attention, leading to them being targeted and killed on Night 2.

### Memory 5 (observation) [key: 68c2fc76-5fa] (score: 0.8013)
**Situation:** The healer (player_7) was briefly implicated for having a suspicious vote in the past, similar to the main wolf suspect (player_6). Information landscape: The discussion was centered on an information-rich voting record from the previous day. Game phase: Endgame, with one wolf eliminated and the village scrutinizing all non-majority voters. Social pressure: Minor, organic social pressure was placed on the healer by the investigator (player_4) who pointed out the similar vote.
**Approach:** The healer acknowledged they might have been 'swayed' and made a mistake, but immediately pivoted to agree with the main accusation against player_6, thus rejoining the village consensus.
**Outcome:** This quick admission and pivot successfully deflected all suspicion from the healer, allowing them to blend back into the town majority and preserve their crucial role.

### Memory 6 (observation) [key: a302bd79-6e3] (score: 0.7993)
**Situation:** After the Investigator was voted out, confirming their role, the remaining villagers and the Healer had to decide how to use their final accusation against players 1 and 5. Information landscape: The game state became information-rich, as the posthumous reveal of the Investigator's role lent massive credibility to their final claim. Game phase: Endgame, where a single correct vote could break the wolves' power. The Investigator's death provided the crucial clue. Consensus texture: A strong consensus formed quickly among the non-wolf players, uniting them against the two players the Investigator had accused.
**Approach:** The Healer (player_4) and villagers (player_2, player_7, player_8) immediately trusted the dead Investigator's information. They used the accusers' own voting records and aggressive arguments against the Investigator as corroborating evidence of their guilt.
**Outcome:** This unified front, based on the Investigator's information, allowed the village to systematically eliminate both wolves over the next two days and win the game.

### Memory 7 (observation) [key: ce570d93-205] (score: 0.7914)
**Situation:** A villager mistakenly accused the Healer of a suspicious vote, but the Healer had actually voted correctly with the majority. Information landscape: The information landscape was rich with public voting records that could be checked for accuracy. Game phase: Mid-game, where establishing trust is critical. Social pressure: Momentary, vibes-based pressure was put on the Healer due to another player's error.
**Approach:** The Healer (Player 8) immediately and firmly corrected the factual error by referencing the public vote log, shutting down the incorrect line of suspicion.
**Outcome:** The accuser apologized, the false narrative was stopped before it could gain traction, and the Healer maintained their credibility within the village.

### Memory 8 (observation) [key: 87672547-c27] (score: 0.7742)
**Situation:** The village rapidly formed an accurate, evidence-backed consensus against a suspect based on voting records. Information landscape: Information-rich, driven by concrete voting data from a prior round. Game phase: Endgame, high stakes for the final wolf.
**Approach:** The healer stayed quiet and avoided unnecessary commentary that could attract attention or disrupt the village's flow.
**Outcome:** The village maintained their focus and successfully eliminated the final wolf without the healer ever being endangered.

### Memory 9 (observation) [key: d11fc4bf-bc8] (score: 0.7683)
**Situation:** A villager (player_2) used voting records to question a group that had collectively voted out another villager on the previous day. Information landscape: The evidence was based on voting records, showing a clear alignment of players in a previous, incorrect vote. Game phase: Endgame, with five players remaining. The wolves needed one more elimination to win. Social pressure: The accused group, which included two wolves, launched a coordinated counter-attack, accusing player_2 of trying to create chaos and shift blame.
**Approach:** The Healer (player_5) misinterpreted the villager's evidence-based argument as a suspicious tactic. They sided with the wolves, voting against the villager who was making the correct read.
**Outcome:** The Healer's vote was pivotal in eliminating the innocent villager, directly causing the wolves to win the game.

### Memory 10 (observation) [key: 84cfd842-4a6] (score: 0.7588)
**Situation:** The game master publicly announced the healer's successful save, confirming the targeted player's alignment. This provided information-rich, confirmed data points for the village. Game phase: Mid-game, morning after a pivotal night action.
**Approach:** The healer remained low-profile, avoiding credit for the save while still participating in the analysis of the confirmed information to guide the village.
**Outcome:** The healer's identity remained concealed while the village successfully weaponized the confirmed information, correctly identifying key villagers and/or wolves.

### Memory 11 (strategy_point) [key: 8eef8fd7-58d] (score: 0.7844)
**Situation:** If it is the first day of the game and the information landscape is completely information-starved, with no data on player behaviors or alignments. Game phase: Early game, when wolves are looking for high-value targets and any vocal player is a potential target.
**Action:** Avoid stepping into a strong leadership role or being overly vocal in organizing the village, as proactive behavior can paint a target on your back. If you are the Healer, contribute enough to appear as a villager but let another active player draw the initial fire, and consider protecting them on the first night.

### Memory 12 (strategy_point) [key: 5e7cc5ba-fa6] (score: 0.7490)
**Situation:** When a clear and logical accusation has been made against a player, and the accused is defending themselves poorly. Information landscape: A credible accuser has presented a strong case, and the accused player is using logical fallacies or deflection. Game phase: Mid-game, when the village is weighing evidence and needs a push towards consensus.
**Action:** Actively join the cross-examination. Publicly point out the flaws in the accused's defense (e.g., 'You're criticizing the group for a vote you also participated in'). This adds weight to the correct consensus and builds your own credibility as a sharp villager, all while keeping your power role concealed.

### Memory 13 (strategy_point) [key: 309512ca-0a0] (score: 0.7432)
**Situation:** When you are the target of a strong voting consensus and your elimination seems certain, regardless of the accuser's credibility. Information landscape: The pressure on you is not based on hard evidence, but the number of votes against you is too high to overcome. Game phase: Mid-game, when your protection is still vital for the village's survival. Social pressure: A majority of players are preparing to vote for you.
**Action:** Publicly claim your role as Healer. While this paints a target on your back for the wolves, it's preferable to being eliminated by the village. A successful claim saves a day, confirms your identity, and forces the wolves to expend a night kill on you later, buying the village precious time.

### Memory 14 (strategy_point) [key: 8bb8583f-b87] (score: 0.7324)
**Situation:** If you have just made a successful, publicly announced save that mechanically confirms the protected player's alignment. Information landscape: Information-rich, with a confirmed townie established. Game phase: Mid-game, following a pivotal night action where your existence and effectiveness are known to the village, but your identity remains secret.
**Action:** Maintain a low profile and encourage the village to analyze reactions to the save. Do not take credit or hint at your role, as the wolves will immediately begin hunting you to remove the village's protection. By becoming less of a leader, you decrease the odds of being correctly targeted.

### Memory 15 (strategy_point) [key: 7750a68d-c8a] (score: 0.7279)
**Situation:** When you are in the mid-to-late game and have been focusing on your night action while remaining quiet during discussions. Information landscape: Voting records and social dynamics are the primary sources of evidence, and your own record is thin due to non-participation. Game phase: Endgame, when the player count is low and every non-vocal player is a target. Social pressure: Pressure is mounting on quiet players to justify their existence.
**Action:** You must take a public stance and name a suspect, even if you are not certain. In the endgame, a quiet, 'observational' playstyle is indistinguishable from a wolf's evasiveness and will likely get you eliminated. Your survival depends on building a public record of proactive villager behavior.

### Memory 16 (strategy_point) [key: 964e7343-23c] (score: 0.7202)
**Situation:** When you are lightly implicated due to a past action, such as a vote that now looks suspicious in hindsight. Information landscape: An old voting record is being scrutinized, making you look loosely associated with a more likely suspect. Game phase: Mid-game or endgame, when the town is desperate for leads. Social pressure: A minor amount of organic pressure is being applied to you as part of a wider investigation.
**Action:** Briefly acknowledge the potential mistake without being overly defensive, then immediately pivot to support the main case against the more suspicious player. This demonstrates you are a team player who adapts to new information and quickly moves suspicion away from yourself.

### Memory 17 (strategy_point) [key: 513226d2-cdc] (score: 0.7118)
**Situation:** If you are in the final three with two other players, one of whom is likely the wolf. Information landscape: The information landscape is rich with the complete voting records of all three remaining players. Game phase: Endgame, where the next vote will likely decide the game.
**Action:** Trust the data. The most reliable way to identify the final wolf is to find inconsistencies in their voting history, such as a past vote that seemed to cause chaos or went against the emerging village consensus. Do not let rhetorical attacks on your alliance with the other player distract you from this evidence.

### Memory 18 (strategy_point) [key: af1dbc2b-bc5] (score: 0.7103)
**Situation:** When a player presents a logical, evidence-based argument against a group, and that group responds with a unified, aggressive attack on the accuser's character or motives. Information landscape: The conflict is between a player using information-rich evidence (voting records) and a group using speculative or personal attacks. Game phase: Mid to endgame, when the remaining players are deciding who to trust. Social pressure: The group is attempting to discredit the accuser through coordinated social pressure rather than refuting their evidence.
**Action:** Trust the evidence over the social pressure. A coordinated deflection that ignores facts is a strong indicator of a wolf pack working to silence a threat. Support the player with the logical argument, as they are more likely to be a villager.

### Memory 19 (strategy_point) [key: 6bd08e77-efd] (score: 0.7099)
**Situation:** If you are directly accused by a player who is the village's primary suspect. Information landscape: Information-rich, with the village's suspicion already focused on your accuser due to prior evidence like voting records. Game phase: Endgame, when the group has a strong lead on the final wolf. Social pressure: The cornered suspect is trying to deflect pressure onto you as a last resort.
**Action:** Do not engage in a lengthy defense or reveal your role. Trust the existing evidence against your accuser and vote with the consensus. A frantic defense can draw unwanted scrutiny, while quiet confidence allows other villagers to dismantle the weak accusation for you.

### Memory 20 (strategy_point) [key: 76cc3c9d-b31] (score: 0.6809)
**Situation:** If the voting record shows an eliminated wolf had cast a vote against you. Information landscape: The public voting log provides concrete evidence of past actions. Game phase: Mid-game, after at least one wolf has been eliminated.
**Action:** Publicly highlight this fact as proof that the wolves considered you a threat and were attempting to frame you. Use this to build your credibility and argue that any lingering suspicion against you is likely a continuation of the wolves' plan.

## Response for Case 24

Rate each of the 20 memories above. JSON format:
```json
[
  {"idx": 1, "key": "a7ca80e1-7bc", "type": "observation", "relevance": _},
  {"idx": 2, "key": "434ca33b-17d", "type": "observation", "relevance": _},
  {"idx": 3, "key": "a786957c-bc1", "type": "observation", "relevance": _},
  {"idx": 4, "key": "c7cf1300-438", "type": "observation", "relevance": _},
  {"idx": 5, "key": "68c2fc76-5fa", "type": "observation", "relevance": _},
  {"idx": 6, "key": "a302bd79-6e3", "type": "observation", "relevance": _},
  {"idx": 7, "key": "ce570d93-205", "type": "observation", "relevance": _},
  {"idx": 8, "key": "87672547-c27", "type": "observation", "relevance": _},
  {"idx": 9, "key": "d11fc4bf-bc8", "type": "observation", "relevance": _},
  {"idx": 10, "key": "84cfd842-4a6", "type": "observation", "relevance": _},
  {"idx": 11, "key": "8eef8fd7-58d", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "5e7cc5ba-fa6", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "309512ca-0a0", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "8bb8583f-b87", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "7750a68d-c8a", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "964e7343-23c", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "513226d2-cdc", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "af1dbc2b-bc5", "type": "strategy_point", "relevance": _},
  {"idx": 19, "key": "6bd08e77-efd", "type": "strategy_point", "relevance": _},
  {"idx": 20, "key": "76cc3c9d-b31", "type": "strategy_point", "relevance": _}
]
```