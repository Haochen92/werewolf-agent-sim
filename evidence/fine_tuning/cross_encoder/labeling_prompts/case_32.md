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

# Case 32: villager — day_discussion (day 2 round 4)

## Game State (what the player sees)
```
================================================================================
CASE cdcd2c6e46f59a85cad3d634c3595a67:dd8dc76fe192c429 | villager | day 2 round 4 | day_discussion
================================================================================

Role: villager
Day: 2, Round: 4

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
[Day 2, Round 3] player_5: Player 3 and 8, you're both advocating for caution, but in an information-starved game, 'wait and see' is exactly what the wolves want to hear. Doing nothing today just guarantees we lose another villager tonight. If you're truly looking for wolves, tell us who you're watching instead of just telling us to be quiet.

--- Strategy note ---
Continue observing the consensus against taking action. Since player_8 and player_3 are actively discouraging voting, I will monitor them as potential wolves trying to stall. Remain silent unless a clear opportunity arises to challenge this 'wait and see' rhetoric effectively.

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

**Situation 1:** A villager was killed on night 1 with no healer save, and the day 2 discussion has polarized between players demanding action and two players advocating extreme caution. The cautious pair refuses to name suspects and frames any push for a vote as reckless, while the vocal players argue that inaction guarantees another night kill. Information landscape: Completely information-starved — no healer save, no voting records; the only differentiating data is the communication-style split between the two factions. Game phase: Early game, day 2 with 7 players; the village needs to generate information through a vote but risks mislynching. Consensus texture: Polarizing — a clear behavioral divide is emerging but no evidence supports either side. Agent exposure: The agent has been monitoring the cautious pair as potential wolves but has not yet publicly challenged them.

## Retrieved Memories to Label

### Memory 1 (observation) [key: a48c4d74-498] (score: 0.8162)
**Situation:** The Day 2 discussion started with all players making generic, non-committal statements about the first night kill. Information landscape: The landscape was information-starved, with no votes or claims made yet. Game phase: Mid-game, just after the first night kill was announced. Consensus texture: A fragile consensus of inaction existed, with everyone echoing polite but useless sentiments.
**Approach:** Two villagers (player_4 and player_5) actively broke the pattern, calling out the stagnant conversation and demanding that players, especially vocal ones, name specific suspects and provide reasons.
**Outcome:** The village remained focused on the logic of the request rather than the tone, forcing a wolf (player_1) into a defensive posture. Their subsequent deflection became the central point of suspicion that led to their elimination.

### Memory 2 (observation) [key: 07fd072f-959] (score: 0.8114)
**Situation:** After incorrectly eliminating an active villager (player_5) who had accused a wolf pair (player_3, player_8) of stalling, the remaining villagers noticed the same wolf pair continuing their strategy of mutual defense and advocating for caution. Information landscape: The information landscape was becoming richer, using the previous day's voting record and the revealed role of the mislynched villager as key evidence. Game phase: Mid-game, with two villagers eliminated by wolves and one by vote. The village was losing numbers and needed a successful elimination. Consensus texture: A strong consensus formed organically among the remaining villagers (player_2, player_4, player_6) based on the clear behavioral pattern of the wolf pair.
**Approach:** The villagers systematically pointed out the consistent coordination between player_3 and player_8, focusing on their shared rhetoric of inaction across two days. They rejected the wolves' attempts to deflect blame and coordinated their votes.
**Outcome:** The villagers successfully identified and voted out player_3, confirming he was a wolf. This broke the wolf partnership and provided the village with the momentum needed to win.

### Memory 3 (observation) [key: a9ee4229-115] (score: 0.8052)
**Situation:** Following the miselimination of player_8, a villager (player_3) who survived a night attack due to a healer save used their heightened credibility to lead an investigation into the players who voted against them. Information landscape: Information-rich, as the previous day's voting record provided concrete data on who pushed the split vote. Game phase: Mid-game, one miselimination has occurred and voting patterns are established. Consensus texture: A strong multi-player convergence formed around analyzing the previous day's voting record. Social pressure: Player_1 and player_5 were under intense evidence-based pressure to explain their prior votes.
**Approach:** Player_3 and their allies aggressively interrogated player_1 and player_5, demanding explanations for their voting choices and pointing out deflections, rather than letting them evade scrutiny.
**Outcome:** The interrogated players failed to provide logical reasons, leading the village to correctly identify and eliminate player_5 as a wolf, and subsequently player_1, demonstrating the effectiveness of using voting records to expose wolf deflections.

### Memory 4 (observation) [key: 578f03b1-9fe] (score: 0.8044)
**Situation:** A player who advocated for passivity on Day 1 was put under pressure on Day 2 and attempted to deflect by attacking the very strategy they had previously promoted (deflection via self-contradiction). Information landscape: The village was information-starved, relying solely on behavioral tells and Day 1 conversation logs after the healer's death. Game phase: Mid-game, where the first day's statements became the primary evidence. Consensus texture: A strong consensus formed organically as multiple players independently pointed out the same logical contradiction in the target's statements. Social pressure: The wolf (player_8) was under evidence-based pressure from multiple villagers who noticed their shifting arguments.
**Approach:** The villagers (led by player_3, player_4, player_5) relentlessly questioned the wolf's inconsistent logic, refusing to let them change the subject. They framed the contradiction as a sign of deception.
**Outcome:** The wolf was unable to provide a coherent defense, was voted out, and their role was confirmed. This validated the villagers' strategy of scrutinizing inconsistent statements.

### Memory 5 (observation) [key: 721ed82e-b65] (score: 0.8019)
**Situation:** In an information-starved mid-game, with no hard evidence and discussion stalled, a proactive villager attempts to force a lead through aggressive tactics. The village consensus is fragile, and players are anxious for a lead but wary of being rushed. The agent is the one applying pressure, making them a target for deflection.
**Approach:** Attempting to generate a lead by targeting quiet players (4x), aggressively demanding names to break a stalemate (1x), or aggressively questioning a single passive player (1x).
**Outcome:** The tactic backfires. Wolves or other players successfully reframe the proactive villager's aggression or chosen target as disruptive, chaotic, or a diversion. The village turns on the accuser, resulting in a costly mislynch and demonstrating the danger of aggressive, unsupported accusations in an info-starved environment.

### Memory 6 (observation) [key: 13870e0b-426] (score: 0.7992)
**Situation:** On Day 3, villagers analyzed the previous day's voting record that eliminated the Healer and noticed a wolf (player_7) was trying to misrepresent the facts. Information landscape: The voting record from Day 2 provided information-rich, concrete evidence to analyze. Game phase: Mid-game, with the town reeling from the loss of the Healer and now hunting for culprits. Consensus texture: A strong consensus formed around player_7, driven by multiple players independently verifying that player_7 was lying about the vote being unanimous.
**Approach:** The villagers meticulously fact-checked player_7's claim that the vote was a 'collective mistake' that everyone agreed to. They used the public voting record to prove this was a lie and build a case.
**Outcome:** This evidence-based approach successfully identified and eliminated a wolf, demonstrating the power of using verifiable game history to expose verbal lies about voting records.

### Memory 7 (observation) [key: 0ac6f17d-6d2] (score: 0.7961)
**Situation:** After the Investigator was mistakenly eliminated, villagers analyzed the vote to find the wolves. Information landscape: The voting record from Day 2 was the primary piece of information-rich evidence. Game phase: Endgame, with only five players remaining and both village power roles gone. Consensus texture: There was no consensus due to active wolf manipulation. The villagers were fractured, with some (player_7, player_6) correctly identifying wolf player_4's suspicious deflection, while others were distracted by the wolf's accusations.
**Approach:** The villagers engaged in circular arguments, allowing wolf player_4 to successfully pit them against each other. They failed to unite against the most suspicious player.
**Outcome:** The vote was a tie, no one was eliminated, and the wolves performed the final kill at night to win. The village's inability to form a consensus from clear voting evidence was their final failure.

### Memory 8 (observation) [key: 8adf1779-c82] (score: 0.7944)
**Situation:** A player was eliminated and revealed to be a wolf, generating the first concrete voting record. Information landscape: Information-rich, with a revealed role and a clear voting record showing who supported and opposed the elimination. Game phase: Mid-game, shifting from behavioral reads to concrete voting analysis. Consensus texture: Strong consensus against the newly revealed wolf's defenders.
**Approach:** Villagers immediately targeted the players who cast dissenting votes instead of joining the majority against the wolf.
**Outcome:** The dissenting voter was forced onto the defensive and ultimately eliminated the next day, confirming the predictive power of voting records.

### Memory 9 (observation) [key: d56c4c50-44b] (score: 0.7935)
**Situation:** After a wolf was eliminated, two players (healer player_4 and investigator player_7) were questioned for voting for a villager (player_8) instead of the confirmed wolf. Information landscape: The voting record from the wolf elimination was the primary source of new, hard evidence for the village. Game phase: Mid-game, with one wolf eliminated and pressure mounting to find the second. Social pressure: Players 4 and 7 were under moderate pressure to explain their votes, which deviated from the successful majority.
**Approach:** The players gave a weak defense, claiming they were 'testing a different lead'. However, another player (wolf player_2) had a far more suspicious voting record, having been the lone dissenter.
**Outcome:** The village successfully weighed the evidence, prioritizing the more egregious voting anomaly of player_2 over the less suspicious votes of players 4 and 7, leading to a correct elimination.

### Memory 10 (observation) [key: ecd420cb-420] (score: 0.7907)
**Situation:** In a mid-game, information-starved environment, a heated and circular argument between two players consumed the entire discussion phase. The rest of the village became spectators, failing to pivot the conversation to productive topics. This created a chaotic and fractured consensus, allowing wolves to hide easily.
**Approach:** Allowed a heated 1v1 argument to derail the day's discussion instead of actively pivoting to more productive targets. The village ultimately took sides in the conflict during the vote.
**Outcome:** A villager involved in the argument was mislynched (in one case, the Investigator). The wolves successfully used the infighting as cover, putting the village at a numerical disadvantage without identifying any real threats.

### Memory 11 (strategy_point) [key: f71e8766-3af] (score: 0.7988)
**Situation:** In the early game, when the village is information-starved and discussion is dominated by vague, vibes-based accusations or aggressive demands to force a vote, the village faces a binary conflict. The lack of voting records or confirmed roles creates pressure to take a side, often leading to mislynches.
**Action:** Challenge the accuser's methodology and point out that pressuring players based on subjective vibes or forcing a vote without evidence are low-information strategies. Resist the urge to become the primary defender of the accused, as this can tie your fate to theirs; instead, redirect the group's focus towards analyzing the accuser's motives or looking for logical fallacies. Additionally, if you feel impatient, resist the urge to force the issue yourself; aggressive, evidence-free demands can be framed by wolves as sowing chaos, so prioritize asking targeted questions to build an information base.

### Memory 12 (strategy_point) [key: bab6a351-a85] (score: 0.7929)
**Situation:** When one or more players consistently advocate for inaction, such as urging the group to 'wait and see' or skipping votes, especially if they defend each other's passivity. Information landscape: The village is information-starved, and suspicion is based on behavioral patterns and shared rhetoric rather than hard evidence. Game phase: Mid-game, when failing to eliminate a wolf guarantees losing another villager. Consensus texture: The call for inaction is preventing a consensus from forming around any particular suspect.
**Action:** Publicly frame this 'wait and see' attitude as a pro-wolf strategy, as it guarantees wolves another kill. Label any coordination between passive players as a suspicious pattern. Challenge the passive players to each name a suspect independently, arguing that true villagers should be actively hunting; their refusal or inability to do so can expose them as having no interest in finding wolves.

### Memory 13 (strategy_point) [key: 014d6b34-2c6] (score: 0.7797)
**Situation:** When a confirmed investigator has been eliminated and the village needs to identify the final wolf among players who previously voted out the first wolf. Information landscape: Information-rich, with a confirmed wolf elimination and the revelation of the investigator's identity. Game phase: Endgame, with few players remaining and a critical need to find the final threat. Consensus texture: A fragile but forming consensus focused on analyzing the voting behavior from the day the first wolf was eliminated.
**Action:** Scrutinize the players who were notably quiet or hesitant during the wolf's elimination, and pressure them to provide their own distinct suspects; a wolf hiding in the voting majority will often deflect and attack the accusers rather than providing a logical alternate theory.

### Memory 14 (strategy_point) [key: 18268625-d31] (score: 0.7754)
**Situation:** If suspicion against a player is based on a complex behavioral read, and multiple players instantly coordinate to dismiss the entire analytical method as invalid. Information landscape: The village is information-starved, with no confirmed roles or voting records to analyze. Game phase: Early game, when the village is trying to establish its first lead. Consensus texture: Multiple players are not just disagreeing with a conclusion, but are actively trying to shut down a specific line of inquiry.
**Action:** Treat the coordinated dismissal itself as potential evidence of a wolf pack working together. Ask the dismissive players why they are so eager to prevent a particular type of analysis, shifting the focus from the original target to the coordinated defense.

### Memory 15 (strategy_point) [key: 9d5249e6-94c] (score: 0.7713)
**Situation:** When a player makes an aggressive, evidence-free accusation the day after the village mistakenly eliminated a player. Information landscape: The village is reeling from a mislynch and is fearful of repeating it. Consensus texture: The accuser is attempting to single-handedly drive a consensus based on behavioral reads ('aggression') rather than verifiable evidence.
**Action:** Resist dismissing the claim based on style alone. Force the accuser to provide specific, verifiable evidence that underpins their certainty. If they cannot, suspect them of manipulation; if they can, you may have found an information role who is simply a poor communicator under pressure.

### Memory 16 (strategy_point) [key: a0db6dc0-645] (score: 0.7683)
**Situation:** If the village has just made a clear mistake, such as voting out a fellow villager, and discussion turns to blaming individuals. Information landscape: Trust is low, the village is on the defensive, and the eliminated player's villager role has been confirmed. Game phase: Mid- to late-game, when the number of players is dwindling. Consensus texture: The village is demoralized, and players may aggressively target dissenters or specific individuals to deflect blame from the collective mistake.
**Action:** Resist the urge to get stuck in a cycle of blame. Acknowledge your own role in the mistaken vote before analyzing the behavior of others to maintain objectivity. If a player aggressively targets the only person who voted differently, challenge them directly: ask why they are focusing on the dissenter instead of the group who made the mistake, as this is a common tactic to deflect blame from their own suspicious vote.

### Memory 17 (strategy_point) [key: 6de91cd0-a3b] (score: 0.7680)
**Situation:** If a player is being aggressively inquisitive, demanding concrete statements from quiet players, and other players are condemning the aggressor's style. Information landscape: It is early in the game, and suspicion is based on communication styles because no voting records or claims exist yet. Social pressure: An aggressive player is putting pressure on a passive one, and the village is reacting to the style of the accusation rather than the content.
**Action:** Defend the aggressive player's right to ask hard questions, even if you disagree with their target. Frame it as a necessary part of information gathering. Attacking an aggressive player's style is a classic wolf tactic to eliminate villagers who are actively hunting them.

### Memory 18 (strategy_point) [key: 2b903631-1ef] (score: 0.7651)
**Situation:** When a vocal player survives a night attack (confirmed by a healer save announcement) after being the opposing target in a split vote that led to a miselimination. Information landscape: Information-rich, utilizing the previous day's voting records and the confirmed save to identify anomalies. Game phase: Mid-game, leveraging the confirmed healer save and the first elimination data. Consensus texture: A strong multi-player convergence forming around the saved player's perspective.
**Action:** Rally behind the saved player and aggressively interrogate those who drove the miselimination, demanding logical justifications for their votes and preventing them from pivoting to new topics.

### Memory 19 (strategy_point) [key: ee58bfad-005] (score: 0.7645)
**Situation:** In the early game, when the village is information-starved and discussion is stagnant—either due to players offering generic platitudes and calls to 'wait and see' or due to multiple players opening with identical, non-committal statements—the village is at risk of passivity. The game lacks voting records or claims, and the group is failing to generate leads.
**Action:** Seize control of the conversation to break the deadlock. Call out the passivity or the synchronized, scripted-sounding nature of the contributions, and directly challenge players to provide a specific, reasoned suspicion to force individual engagement and prevent wolves from hiding behind group inaction.

### Memory 20 (strategy_point) [key: d322503b-b9c] (score: 0.7612)
**Situation:** When a strong consensus forms against one player based on a single piece of evidence, like a peculiar vote. Information landscape: The village is fixated on one piece of information while a larger context might be missing. Game phase: Mid-game, when a single mis-vote can be costly. Consensus texture: A strong consensus is being driven by a few vocal players.
**Action:** Before committing to the vote, pause and consider the motives of those pushing the hardest. Ask if the target's counter-arguments or accusations have any merit. Over-focusing on one data point can cause tunnel vision that wolves can easily exploit.

## Response for Case 32

Rate each of the 20 memories above. JSON format:
```json
[
  {"idx": 1, "key": "a48c4d74-498", "type": "observation", "relevance": _},
  {"idx": 2, "key": "07fd072f-959", "type": "observation", "relevance": _},
  {"idx": 3, "key": "a9ee4229-115", "type": "observation", "relevance": _},
  {"idx": 4, "key": "578f03b1-9fe", "type": "observation", "relevance": _},
  {"idx": 5, "key": "721ed82e-b65", "type": "observation", "relevance": _},
  {"idx": 6, "key": "13870e0b-426", "type": "observation", "relevance": _},
  {"idx": 7, "key": "0ac6f17d-6d2", "type": "observation", "relevance": _},
  {"idx": 8, "key": "8adf1779-c82", "type": "observation", "relevance": _},
  {"idx": 9, "key": "d56c4c50-44b", "type": "observation", "relevance": _},
  {"idx": 10, "key": "ecd420cb-420", "type": "observation", "relevance": _},
  {"idx": 11, "key": "f71e8766-3af", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "bab6a351-a85", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "014d6b34-2c6", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "18268625-d31", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "9d5249e6-94c", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "a0db6dc0-645", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "6de91cd0-a3b", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "2b903631-1ef", "type": "strategy_point", "relevance": _},
  {"idx": 19, "key": "ee58bfad-005", "type": "strategy_point", "relevance": _},
  {"idx": 20, "key": "d322503b-b9c", "type": "strategy_point", "relevance": _}
]
```