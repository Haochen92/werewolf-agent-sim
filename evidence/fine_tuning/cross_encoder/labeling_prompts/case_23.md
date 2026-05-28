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