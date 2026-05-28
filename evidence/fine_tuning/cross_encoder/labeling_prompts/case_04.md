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

# Case 4: villager — day_discussion (day 3 round 1)

## Game State (what the player sees)
```
================================================================================
CASE 278da20b69d7bcd7970c113f10dc347b:a3facf64db4b602b | villager | day 3 round 1 | day_discussion
================================================================================

Role: villager
Day: 3, Round: 1

Surviving players: player_2, player_3, player_5, player_7, player_8, player_4

--- Previous days summary ---
[Day 1]
Key accusations: None. Defenses: None. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: None. The Day 1 public discussion was characterized by universal caution, as all eight players engaged in introductory remarks that emphasized observing behaviors rather than making immediate accusations. Players focused on establishing a baseline for suspicious activity, with consensus centered on monitoring for aggressive or overly pushy behavior. No specific individuals were targeted or defended, and no players claimed any roles or formed alliances during this initial phase.

[Day 1]
Day 1: No vote was held today.

[Day 1]
player_1 was targeted by the wolves last night, but was saved by the healer!

[Day 2]
Key accusations: player_1 accused player_6 of deflection and stalling; player_3 accused player_6 of evasion; player_6 accused player_5 of forced behavior intended to minimize urgency. Defenses: player_5 defended by clarifying that their 'breathing room' comment referred to the team count rather than a desire to stall; player_6 defended by claiming that their comments on unpredictability were misinterpreted and that they are prioritizing evidence over gut-feeling accusations. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: player_4 and player_6 formed a loose consensus based on the need to avoid hasty voting and focus on concrete behavioral patterns rather than tone.

[Day 2]

Here's the vote result for day 2:
  player_1 voted for player_6
  player_2 voted for player_6
  player_3 voted for player_6
  player_5 voted for player_6
  player_7 voted for player_6
  player_8 voted for player_6
  player_4 voted for player_5
  player_6 voted for player_1
Player player_6 has been voted out and was a wolf.


[Day 2]
player_1 was killed by the wolves last night. They were a villager.

--- Today's public discussion ---
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
Also note: who is being evasive, voting inconsistencies, and unresolved accusations.

```

## Golden Situation Query (what we're retrieving for)

**Situation 1:** A wolf was correctly eliminated by near-unanimous vote, but the sole dissenting voter — who targeted a different player instead of the confirmed wolf — has not yet been scrutinized. The village's most active voice, the healer-saved player who led the accusation, was killed overnight, leaving a leadership vacuum. Information landscape: Information-rich — the Day 2 voting record clearly shows one player broke from the 6-1 consensus to vote for a non-wolf target. Game phase: Mid-game, day 3 with 6 players and 1 wolf remaining; the village lost its key information anchor overnight. Consensus texture: No current consensus — the previous day's unified push lost its driver. Agent exposure: Unnoticed — voted correctly with the majority, no special role or information.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 13870e0b-426] (score: 0.8364)
**Situation:** On Day 3, villagers analyzed the previous day's voting record that eliminated the Healer and noticed a wolf (player_7) was trying to misrepresent the facts. Information landscape: The voting record from Day 2 provided information-rich, concrete evidence to analyze. Game phase: Mid-game, with the town reeling from the loss of the Healer and now hunting for culprits. Consensus texture: A strong consensus formed around player_7, driven by multiple players independently verifying that player_7 was lying about the vote being unanimous.
**Approach:** The villagers meticulously fact-checked player_7's claim that the vote was a 'collective mistake' that everyone agreed to. They used the public voting record to prove this was a lie and build a case.
**Outcome:** This evidence-based approach successfully identified and eliminated a wolf, demonstrating the power of using verifiable game history to expose verbal lies about voting records.

### Memory 2 (observation) [key: 0ac6f17d-6d2] (score: 0.8294)
**Situation:** After the Investigator was mistakenly eliminated, villagers analyzed the vote to find the wolves. Information landscape: The voting record from Day 2 was the primary piece of information-rich evidence. Game phase: Endgame, with only five players remaining and both village power roles gone. Consensus texture: There was no consensus due to active wolf manipulation. The villagers were fractured, with some (player_7, player_6) correctly identifying wolf player_4's suspicious deflection, while others were distracted by the wolf's accusations.
**Approach:** The villagers engaged in circular arguments, allowing wolf player_4 to successfully pit them against each other. They failed to unite against the most suspicious player.
**Outcome:** The vote was a tie, no one was eliminated, and the wolves performed the final kill at night to win. The village's inability to form a consensus from clear voting evidence was their final failure.

### Memory 3 (observation) [key: 8ccbab63-101] (score: 0.8287)
**Situation:** A player (player_5) was accused of being suspicious for casting the sole dissenting vote against the majority that eliminated the Healer. Information landscape: The evidence was a single voting record anomaly, while the accused's accuser (player_7, a wolf) was part of the mistaken majority. Game phase: Mid-game, with the village trying to recover from the major error of voting out their Healer. Social pressure: The accused villager was put under intense pressure from multiple players to justify their vote.
**Approach:** Player_5, a villager, became defensive and attacked the 'bandwagon' logic instead of providing a clear reason for their own vote.
**Outcome:** The village failed to weigh the evidence correctly, interpreting the defensive behavior as guilt and voting out the villager.

### Memory 4 (observation) [key: 07fd072f-959] (score: 0.8271)
**Situation:** After incorrectly eliminating an active villager (player_5) who had accused a wolf pair (player_3, player_8) of stalling, the remaining villagers noticed the same wolf pair continuing their strategy of mutual defense and advocating for caution. Information landscape: The information landscape was becoming richer, using the previous day's voting record and the revealed role of the mislynched villager as key evidence. Game phase: Mid-game, with two villagers eliminated by wolves and one by vote. The village was losing numbers and needed a successful elimination. Consensus texture: A strong consensus formed organically among the remaining villagers (player_2, player_4, player_6) based on the clear behavioral pattern of the wolf pair.
**Approach:** The villagers systematically pointed out the consistent coordination between player_3 and player_8, focusing on their shared rhetoric of inaction across two days. They rejected the wolves' attempts to deflect blame and coordinated their votes.
**Outcome:** The villagers successfully identified and voted out player_3, confirming he was a wolf. This broke the wolf partnership and provided the village with the momentum needed to win.

### Memory 5 (observation) [key: 16fddf0f-3eb] (score: 0.8268)
**Situation:** After a villager was mislynched, the village identified a wolf (Player 3) who had cast a lone, unexplained vote against the healer during that mislynch. Information landscape: The information landscape was rich with voting data from the previous day, allowing players to pinpoint a specific, anomalous action. Game phase: Mid-game, following a failed vote. The village was motivated to correct its course. Consensus texture: A strong consensus was built by three vocal villagers (Players 1, 4, 6) who relentlessly focused their questioning on the wolf's specific action, refusing to be sidetracked by broader arguments about groupthink.
**Approach:** The villagers continuously demanded a specific justification for the vote against the healer. They correctly identified the wolf's attempts to deflect and pivot as evidence of guilt.
**Outcome:** The focused and persistent questioning prevented the wolf from escaping scrutiny, leading to a strong and accurate consensus to vote them out. This corrected the village's course and led directly to a win.

### Memory 6 (observation) [key: a9ee4229-115] (score: 0.8232)
**Situation:** Following the miselimination of player_8, a villager (player_3) who survived a night attack due to a healer save used their heightened credibility to lead an investigation into the players who voted against them. Information landscape: Information-rich, as the previous day's voting record provided concrete data on who pushed the split vote. Game phase: Mid-game, one miselimination has occurred and voting patterns are established. Consensus texture: A strong multi-player convergence formed around analyzing the previous day's voting record. Social pressure: Player_1 and player_5 were under intense evidence-based pressure to explain their prior votes.
**Approach:** Player_3 and their allies aggressively interrogated player_1 and player_5, demanding explanations for their voting choices and pointing out deflections, rather than letting them evade scrutiny.
**Outcome:** The interrogated players failed to provide logical reasons, leading the village to correctly identify and eliminate player_5 as a wolf, and subsequently player_1, demonstrating the effectiveness of using voting records to expose wolf deflections.

### Memory 7 (observation) [key: 8adf1779-c82] (score: 0.8190)
**Situation:** A player was eliminated and revealed to be a wolf, generating the first concrete voting record. Information landscape: Information-rich, with a revealed role and a clear voting record showing who supported and opposed the elimination. Game phase: Mid-game, shifting from behavioral reads to concrete voting analysis. Consensus texture: Strong consensus against the newly revealed wolf's defenders.
**Approach:** Villagers immediately targeted the players who cast dissenting votes instead of joining the majority against the wolf.
**Outcome:** The dissenting voter was forced onto the defensive and ultimately eliminated the next day, confirming the predictive power of voting records.

### Memory 8 (observation) [key: d56c4c50-44b] (score: 0.8136)
**Situation:** After a wolf was eliminated, two players (healer player_4 and investigator player_7) were questioned for voting for a villager (player_8) instead of the confirmed wolf. Information landscape: The voting record from the wolf elimination was the primary source of new, hard evidence for the village. Game phase: Mid-game, with one wolf eliminated and pressure mounting to find the second. Social pressure: Players 4 and 7 were under moderate pressure to explain their votes, which deviated from the successful majority.
**Approach:** The players gave a weak defense, claiming they were 'testing a different lead'. However, another player (wolf player_2) had a far more suspicious voting record, having been the lone dissenter.
**Outcome:** The village successfully weighed the evidence, prioritizing the more egregious voting anomaly of player_2 over the less suspicious votes of players 4 and 7, leading to a correct elimination.

### Memory 9 (observation) [key: b53922e1-0e6] (score: 0.8125)
**Situation:** After the village mistakenly eliminated their Investigator, they were left with no active leads. Information landscape: The landscape became information-starved of new intel but rich with past data, specifically the voting record from the Investigator's elimination. Game phase: Mid-game, Day 3, with the village at an informational disadvantage. Social pressure: The village collectively redirected pressure onto a player who made an anomalous vote during the prior day's chaotic elimination.
**Approach:** The villagers focused on the single, unexplained vote cast by player_3 (a wolf). They relentlessly questioned the wolf's motive and rejected their vague explanations.
**Outcome:** The focused interrogation based on the voting record led the village to correctly identify and eliminate the wolf, recovering from their previous day's mistake.

### Memory 10 (observation) [key: 578f03b1-9fe] (score: 0.8090)
**Situation:** A player who advocated for passivity on Day 1 was put under pressure on Day 2 and attempted to deflect by attacking the very strategy they had previously promoted (deflection via self-contradiction). Information landscape: The village was information-starved, relying solely on behavioral tells and Day 1 conversation logs after the healer's death. Game phase: Mid-game, where the first day's statements became the primary evidence. Consensus texture: A strong consensus formed organically as multiple players independently pointed out the same logical contradiction in the target's statements. Social pressure: The wolf (player_8) was under evidence-based pressure from multiple villagers who noticed their shifting arguments.
**Approach:** The villagers (led by player_3, player_4, player_5) relentlessly questioned the wolf's inconsistent logic, refusing to let them change the subject. They framed the contradiction as a sign of deception.
**Outcome:** The wolf was unable to provide a coherent defense, was voted out, and their role was confirmed. This validated the villagers' strategy of scrutinizing inconsistent statements.

### Memory 11 (strategy_point) [key: 014d6b34-2c6] (score: 0.8020)
**Situation:** When a confirmed investigator has been eliminated and the village needs to identify the final wolf among players who previously voted out the first wolf. Information landscape: Information-rich, with a confirmed wolf elimination and the revelation of the investigator's identity. Game phase: Endgame, with few players remaining and a critical need to find the final threat. Consensus texture: A fragile but forming consensus focused on analyzing the voting behavior from the day the first wolf was eliminated.
**Action:** Scrutinize the players who were notably quiet or hesitant during the wolf's elimination, and pressure them to provide their own distinct suspects; a wolf hiding in the voting majority will often deflect and attack the accusers rather than providing a logical alternate theory.

### Memory 12 (strategy_point) [key: 2b903631-1ef] (score: 0.7950)
**Situation:** When a vocal player survives a night attack (confirmed by a healer save announcement) after being the opposing target in a split vote that led to a miselimination. Information landscape: Information-rich, utilizing the previous day's voting records and the confirmed save to identify anomalies. Game phase: Mid-game, leveraging the confirmed healer save and the first elimination data. Consensus texture: A strong multi-player convergence forming around the saved player's perspective.
**Action:** Rally behind the saved player and aggressively interrogate those who drove the miselimination, demanding logical justifications for their votes and preventing them from pivoting to new topics.

### Memory 13 (strategy_point) [key: a0db6dc0-645] (score: 0.7874)
**Situation:** If the village has just made a clear mistake, such as voting out a fellow villager, and discussion turns to blaming individuals. Information landscape: Trust is low, the village is on the defensive, and the eliminated player's villager role has been confirmed. Game phase: Mid- to late-game, when the number of players is dwindling. Consensus texture: The village is demoralized, and players may aggressively target dissenters or specific individuals to deflect blame from the collective mistake.
**Action:** Resist the urge to get stuck in a cycle of blame. Acknowledge your own role in the mistaken vote before analyzing the behavior of others to maintain objectivity. If a player aggressively targets the only person who voted differently, challenge them directly: ask why they are focusing on the dissenter instead of the group who made the mistake, as this is a common tactic to deflect blame from their own suspicious vote.

### Memory 14 (strategy_point) [key: 3c63e195-43f] (score: 0.7832)
**Situation:** When a player questions the motives behind a recent, successful, and unanimous vote that eliminated a confirmed wolf, specifically suggesting a 'bussing' strategy. Information landscape: Information-rich, as the confirmed wolf's past actions and voters are known. Game phase: Mid-game, right after a wolf has been voted out. Consensus texture: Strong consensus validated by a role reveal.
**Action:** Do not immediately dismiss this player. Seriously consider their argument that a wolf may have 'bussed' to gain trust, and ask the accuser to elaborate on why they find the behavior performative, as they may be an Investigator with crucial information.

### Memory 15 (strategy_point) [key: e4aa0470-b05] (score: 0.7829)
**Situation:** If a player is voted out and revealed to be a villager, resulting in a mislynch. Information landscape: This is a moment of information-rich clarity, confirming the previous day's consensus was wrong. Game phase: Mid- to endgame. Focus on the dissenting voting bloc who voted against the mislynch.
**Action:** Immediately focus all public scrutiny on the members of that dissenting voting bloc. Demand that each one explains their reasoning. Treat evasive answers or attempts to change the subject as strong signs of wolf activity.

### Memory 16 (strategy_point) [key: 0d69b314-fbd] (score: 0.7811)
**Situation:** After the village has successfully voted out a player who was revealed to be a wolf, typically during the mid-game. The information landscape is rich, with the previous day's voting record providing concrete evidence to identify players who may have been allied with the confirmed wolf.
**Action:** Focus suspicion on any player who defended, was hesitant to condemn, or cast a dissenting vote for the now-confirmed wolf. Relentlessly question their reasoning. If a player who previously supported the wolf later voted against them, challenge this as a potential 'bus vote' and make their inconsistent history the central focus. Treat deflection or weak reasoning as strong confirmation of guilt.

### Memory 17 (strategy_point) [key: 41f4badb-495] (score: 0.7788)
**Situation:** If a player who was aggressively accusing others is eliminated and revealed to be a villager, resulting in a mislynch. Information landscape: This is a moment of information-rich clarity, confirming the previous day's consensus was wrong. Game phase: Mid- to endgame. Focus on the voting majority who initiated the lynch.
**Action:** Immediately redirect suspicion onto the player(s) who most aggressively initiated and pushed for that failed elimination. Specifically, analyze whether the eliminated villager was targeted because their accusations were hitting close to home; the players who successfully discredited them were likely wolves deflecting suspicion from themselves or their partners.

### Memory 18 (strategy_point) [key: da44ad05-278] (score: 0.7705)
**Situation:** When reviewing the voting record against an eliminated, confirmed wolf, observe players who only joined the unanimous vote at the very end of the round. If such a player initiates a weak accusation against others the following day, they are likely attempting to shift suspicion. Information landscape: Information-rich, with explicit voting sequences and a confirmed enemy role. Game phase: Endgame, after at least one wolf is eliminated and the search narrows. Social pressure: The accuser is likely trying to preemptively shift suspicion away from themselves.
**Action:** Scrutinize the late voter for 'bussing' or distraction tactics. Immediately challenge them on their voting record: ask why they were hesitant to vote for a confirmed wolf yesterday but are so confident in their new, flimsy accusation today. This pattern is a classic sign of a wolf trying to create a distraction or gain trust.

### Memory 19 (strategy_point) [key: 9d5249e6-94c] (score: 0.7658)
**Situation:** When a player makes an aggressive, evidence-free accusation the day after the village mistakenly eliminated a player. Information landscape: The village is reeling from a mislynch and is fearful of repeating it. Consensus texture: The accuser is attempting to single-handedly drive a consensus based on behavioral reads ('aggression') rather than verifiable evidence.
**Action:** Resist dismissing the claim based on style alone. Force the accuser to provide specific, verifiable evidence that underpins their certainty. If they cannot, suspect them of manipulation; if they can, you may have found an information role who is simply a poor communicator under pressure.

### Memory 20 (strategy_point) [key: 62511a41-1ae] (score: 0.7658)
**Situation:** After the village has mislynched a player who is revealed to be a key power role (e.g., Investigator). The information landscape becomes rich with the definitive evidence of the previous day's voting record and, if applicable, the power role's final findings. This occurs in the mid- to late-game, when the loss of a power role creates an urgent need to correct course.
**Action:** Immediately make the voting record the sole focus of the discussion. Systematically demand that every player who voted for the eliminated power role provide a specific, evidence-based justification. Treat deflection, appeals to 'group responsibility,' or claims of 'going with the flow' as primary signals of guilt. If the power role made a final accusation, treat it as a high-probability lead.

## Response for Case 4

Rate each of the 20 memories above. JSON format:
```json
[
  {"idx": 1, "key": "13870e0b-426", "type": "observation", "relevance": _},
  {"idx": 2, "key": "0ac6f17d-6d2", "type": "observation", "relevance": _},
  {"idx": 3, "key": "8ccbab63-101", "type": "observation", "relevance": _},
  {"idx": 4, "key": "07fd072f-959", "type": "observation", "relevance": _},
  {"idx": 5, "key": "16fddf0f-3eb", "type": "observation", "relevance": _},
  {"idx": 6, "key": "a9ee4229-115", "type": "observation", "relevance": _},
  {"idx": 7, "key": "8adf1779-c82", "type": "observation", "relevance": _},
  {"idx": 8, "key": "d56c4c50-44b", "type": "observation", "relevance": _},
  {"idx": 9, "key": "b53922e1-0e6", "type": "observation", "relevance": _},
  {"idx": 10, "key": "578f03b1-9fe", "type": "observation", "relevance": _},
  {"idx": 11, "key": "014d6b34-2c6", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "2b903631-1ef", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "a0db6dc0-645", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "3c63e195-43f", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "e4aa0470-b05", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "0d69b314-fbd", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "41f4badb-495", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "da44ad05-278", "type": "strategy_point", "relevance": _},
  {"idx": 19, "key": "9d5249e6-94c", "type": "strategy_point", "relevance": _},
  {"idx": 20, "key": "62511a41-1ae", "type": "strategy_point", "relevance": _}
]
```