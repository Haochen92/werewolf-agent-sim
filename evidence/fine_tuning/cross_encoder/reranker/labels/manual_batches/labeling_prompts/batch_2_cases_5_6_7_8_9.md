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

# Case 5: wolf — day_vote (day 3 round 4)

## Game State (what the player sees)
```
================================================================================
CASE 06f59eaa57bd63b5ae1145f7e6896857:aa5ec911090a1348 | wolf | day 3 round 4 | day_vote
================================================================================

Role: wolf
Day: 3, Round: 4

Surviving villagers: player_4, player_5, player_6, player_8
Known surviving wolf allies: player_7

--- Previous days summary ---
[Day 1]
Key accusations: None. Defenses: None. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: None. The Day 1 public discussion was strictly introductory, with all players focusing on establishing social presence, encouraging participation, and expressing caution against jumping to early conclusions without any concrete information.

[Day 1]
Day 1: No vote was held today.

[Day 1]
player_1 was killed by the wolves last night. They were a healer.

[Day 2]
Key accusations: player_5 accused player_3 of being vague after player_3 suggested monitoring quiet players. Defenses: None provided. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: None.

[Day 2]

Here's the vote result for day 2:
  player_2 voted for player_3
  player_4 voted for player_3
  player_5 voted for player_3
  player_6 voted for player_3
  player_8 voted for player_3
  player_3 voted for player_4
  player_7 voted for player_5
Player player_3 has been voted out and was a wolf.


[Day 2]
player_2 was killed by the wolves last night. They were a villager.

--- Today's public discussion ---
[Day 3, Round 1] player_4: We got one wolf, but there is still another. Player_7, why did you vote for player_5 yesterday instead of joining the rest of us on player_3?
[Day 3, Round 1] player_6: We got one wolf, but there is still at least one more out there. Player 7, you voted for player 5 yesterday when everyone else was focused on player 3. Why were you going against the grain there?
[Day 3, Round 1] player_8: We got one wolf yesterday, which is great. I think we need to look closely at who pushed hardest for that vote. Does anyone have any thoughts on who seems most genuine right now?
[Day 3, Round 1] player_7: It's good that we found the wolf yesterday. Now we need to look at who is being too quiet or just following the crowd. Player 8, what are your thoughts on the remaining players?
[Day 3, Round 2] player_4: Player 7, you didn't answer my question. Voting for someone else while the rest of the group was aligned on a wolf is a classic way to deflect. Are you trying to protect someone or just hoping we won't notice?
[Day 3, Round 2] player_5: Player 7, you still haven't answered why you targeted me while everyone else was focused on a known wolf. Your deflection toward player 8 doesn't explain your own vote. What exactly was your reasoning for suspecting me yesterday?
[Day 3, Round 2] player_8: Actually, looking back at the voting logs, player 4 was very eager to lead the charge against player 3. It's possible they were just distancing themselves from their partner. Player 4, what makes you so confident in your read on the rest of us?
[Day 3, Round 2] player_7: I understand why that vote looks strange now. At the time, player_5 was being very aggressive in pushing for player_3, and I mistakenly worried that they might be overcompensating to hide something. I realize now that was just me being overly cautious and misreading the situation. Since we are down to the wire, I think we should look at who seems the most locked in together—sometimes perfect agreement is just as suspicious as being the outlier.
[Day 3, Round 3] player_4: Player 8, asking why I led the vote on player 3 is a reach—it was a group consensus on a revealed wolf. Focusing on me right after I confronted player 7 makes it seem like you're trying to derail the conversation. Why are you shielding player 7 instead of questioning their logic?
[Day 3, Round 3] player_5: Player 7, calling our agreement on player 3 'suspicious' is a reach. We all saw the same evidence. If you're so worried about coordinated votes, why aren't you looking at who is actually pushing a narrative right now instead of just pointing fingers at the ones who caught a wolf?
[Day 3, Round 3] player_6: Player 7, your reasoning for targeting player 5 seems like a reach, but I'm more interested in why you think player 4 and player 8 are 'locked in'. Do you have actual evidence of them working together, or is that just another diversion?
[Day 3, Round 3] player_8: Player 4, your eagerness to lead the vote yesterday is starting to feel a bit too calculated. Sometimes being the loudest one in the room is a way to control the narrative rather than just being helpful. Why are you so certain player 7 is the one we should be targeting instead of yourself?
[Day 3, Round 4] player_4: Player 8, you're trying to frame my leadership as suspicious, but leading a successful vote against a confirmed wolf is exactly what a villager should do. Your deflection to me is just as transparent as player 7's attempt to sow doubt about our consistency. I'm sticking to my vote for player 7.
[Day 3, Round 4] player_5: Player 7, your attempt to label our collective vote on a known wolf as 'suspicious' is a clear deflection. You haven't provided any evidence against others, only accusations of 'coordination' to sow doubt. Based on your inconsistent logic and the fact that you targeted me when I was actively hunting the wolf, my vote remains on you.
[Day 3, Round 4] player_6: Player 7, your reasoning for targeting player 5 yesterday remains very weak, and now you are trying to cast doubt on everyone who correctly identified a wolf. Given your diversionary tactics, you are my primary suspect for the remaining wolf.
[Day 3, Round 4] player_8: Player 4, your defensiveness is quite telling. You're trying to frame any questioning of your actions as a 'reach' to avoid real scrutiny. The group consensus yesterday doesn't make you immune to suspicion, and your desperation to steer the target onto player 7 feels like a classic diversion. I'm voting for player 4.
[Day 3, Round 4] player_7: It is easy to point fingers at my past vote when we are all feeling the pressure of the endgame. But look at how quickly 4, 5, and 6 have synced up to push this narrative against me. We are down to the final stretch, and I urge everyone to consider if this level of perfect agreement is actually a strategy to steamroll a village decision.

--- Wolf night chat ---
No messages yet.

--- Strategy note ---
The village is locked on my voting record, making direct defense difficult. I will shift focus toward the high level of coordination between 4, 5, and 6, framing their consensus as a potential wolf pack trying to secure an easy mislynch. I need to remain calm and emphasize that a reflexive vote against me based solely on a past error is exactly how the wolves would want the game to end.

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

**Situation 1:** A coalition of villagers is pushing for my elimination, citing my lone dissenting vote against one of them on the day my wolf partner was correctly voted out. My attempts to reframe their consensus as suspicious coordination are being dismissed as deflection. Another villager is creating a secondary conflict by accusing the leader of the main coalition, but the primary pressure remains on me. Information landscape: The information is rich but narrowly focused on a single piece of evidence: my voting record from the previous day. Game phase: It is the endgame with five players remaining, where one incorrect elimination will result in a wolf victory. The village is energized after successfully identifying and voting out one wolf on the previous day. Consensus texture: A strong, evidence-driven consensus is forming against me, led by a bloc of three villagers, though it is slightly fractured by one villager pushing a counter-accusation against the bloc's leader. Agent exposure: I am the primary target, with suspicion based entirely on the concrete evidence of my vote from the previous day.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 42dfb995-f6d] (score: 0.8442)
**Situation:** A wolf's partner (player_2) was targeted by a strong village consensus, making their elimination almost certain. Information landscape: The evidence against the targeted wolf was behavioral but had convinced a large majority of the village. Game phase: Mid-game, during the first elimination vote of the game. Consensus texture: A strong, multi-player consensus had formed against the wolf, driven by their passive and evasive responses. Note: The remaining wolf had previously defended the partner.
**Approach:** The remaining wolf (player_5) chose to vote along with the majority to eliminate their own partner, a tactic known as 'bussing'.
**Outcome:** While this saved the wolf from suspicion on that day's vote, their prior actions of defending their partner were remembered. The next day, villagers used this previous alliance as primary evidence to identify and eliminate the second wolf.

### Memory 2 (observation) [key: 8bcd53c6-fa3] (score: 0.8410)
**Situation:** A strong, evidence-based village consensus has formed against a wolf partner. The information landscape is rich, with the consensus driven by logical analysis of voting records or contradictory statements. The agent's wolf partner is the primary target of the vote.
**Approach:** Casting a lone dissenting vote against a different villager (3x), and casting a protest vote against the most vocal accuser (1x).
**Outcome:** The dissenting vote fails to save the partner and creates a clear, incriminating link to the voting wolf. This vote is later used as damning evidence, leading to the dissenter's own elimination.

### Memory 3 (observation) [key: 5d53cedb-aac] (score: 0.8342)
**Situation:** The village vote was split between two main targets, with one bloc of villagers coalescing around eliminating a suspicious player. Information landscape: The vote was based on conflicting interpretations of a previous day's voting record. Game phase: Endgame, with 6 players remaining (2 wolves, 4 villagers). Consensus texture: A fragile consensus was forming around one villager (player_4), but it was not unanimous.
**Approach:** Instead of joining the majority to vote out player_4, the two wolves coordinated to vote for a different, more influential villager (player_1).
**Outcome:** The villager bloc eliminated their target (player_4), but the wolves' votes on player_1 were noted, creating ambiguity about their allegiances while still ensuring a villager was removed. This play helped them avoid suspicion.

### Memory 4 (observation) [key: 09b9bae0-849] (score: 0.8287)
**Situation:** A strong consensus formed to eliminate a villager (player_6/player_7) who was being aggressively targeted based on speculative reads of communication style rather than hard evidence. Game phase: Mid-game, where the village was anxious for a lead. Consensus texture: A fragile consensus was driven by the Investigator (player_2/player_4), which other players, including wolves, then amplified. Social pressure: Pressure mounted on the target due to the Investigator's accusation and their own defensive reaction.
**Approach:** The wolves (player_4 and player_8 / player_3 and player_6) saw the villagers turning on one of their own and joined the majority vote to eliminate the target, effectively hiding within the town's momentum.
**Outcome:** The villager was eliminated with a near-unanimous vote. By voting with the majority, the wolves successfully blended in and avoided any suspicion, while also removing an active villager. This tactic also made the Investigator, who led the charge, a potential scapegoat and the next logical wolf target.

### Memory 5 (observation) [key: 8e6e3cbd-d31] (score: 0.8224)
**Situation:** A wolf (player_6) cast a dissenting vote for a villager (player_8) alongside their wolf partner (player_2), who was the primary target of a successful town vote. Information landscape: The vote was information-rich, based on a strong consensus that player_2's defensive behavior was wolf-like. Game phase: Mid-game, at the conclusion of the first elimination vote. Consensus texture: A strong consensus driven by multiple villagers converged on player_2.
**Approach:** Both wolves (player_6 and player_2) cast a dissenting vote against a villager instead of joining the majority to eliminate the exposed partner.
**Outcome:** This coordinated vote created an undeniable public record linking player_6 to the confirmed wolf, player_2. This became the primary evidence used to eliminate player_6 the next day, costing the wolves the game.

### Memory 6 (observation) [key: 1033b4f0-e78] (score: 0.8207)
**Situation:** Mid-game, a strong village consensus has formed around a single elimination target. The evidence is speculative or behavioral, not definitive. The wolves are not currently under suspicion and must decide how to cast their votes in the face of this unified village bloc.
**Approach:** The wolf pack decided to vote as a bloc, dissenting from the village consensus. Tactics included: voting for the villager who led the charge against a partner (2x), voting for a different vocal villager (2x), and voting for a random third party (4x).
**Outcome:** This created a public and incriminating voting record that explicitly linked the wolves together. This voting link was later used as key evidence to identify and eliminate the second wolf.

### Memory 7 (observation) [key: 453891e8-d51] (score: 0.8165)
**Situation:** A villager (player_7) made themselves the primary suspect due to contradictory statements and a poor defense. Information landscape: The village was analyzing a rich voting record from the previous day, which incriminated the villager. Game phase: Endgame, with only five players remaining. Consensus texture: A strong, multi-player consensus formed against the villager, driven by two other vocal villagers.
**Approach:** The wolves (player_2, player_6) stayed quiet during the discussion and then joined the majority vote against the villager.
**Outcome:** The villager was eliminated, and the wolves won the game. By joining a plausible, village-driven vote, the wolves avoided drawing any attention to themselves.

### Memory 8 (observation) [key: 3ce9912f-493] (score: 0.8128)
**Situation:** A wolf attempted to eliminate the primary night kill target (the Healer) via a day vote while the rest of the village was consolidating a successful vote against the wolf's partner. Information landscape: Information-rich, with voting data making the wolf's deviation highly visible. Game phase: Mid-game, after one night with a saved kill. Consensus texture: A strong, multi-player consensus formed against the wolf's partner, making the outlier vote against the Healer a clear, incriminating data point.
**Approach:** The wolf cast an outlier vote against the protected target (the Healer), effectively aligning with their wolf partner's vote instead of blending in with the village consensus.
**Outcome:** The village recognized the alignment between the wolf's day vote and the wolves' night actions, using this vote as primary evidence to identify and eliminate the wolf on the following day.

### Memory 9 (observation) [key: 07265d73-9b4] (score: 0.8116)
**Situation:** During the mid-game, the village was divided, with suspicion split between the two wolves and a vocal villager. Information landscape: The landscape was rich with voting records, but interpretation was contentious, creating fractured pockets of suspicion. Game phase: Mid-game, with the village trying to recover from the Investigator's mislynch. Consensus texture: There was no consensus, with several small factions pushing different targets.
**Approach:** The wolves (player_1 and player_4) voted in unison for a vocal villager (player_7) who was not their primary accuser. This action was designed not to eliminate the villager, but to create a three-way tie with themselves.
**Outcome:** The vote resulted in a tie, meaning no one was eliminated. This tactic successfully stalled the game for two consecutive days, allowing the wolves to get free night kills and win through attrition.

### Memory 10 (observation) [key: eb3e69f7-94a] (score: 0.8103)
**Situation:** Wolf player_2 was caught due to their poor deflection under pressure, and a strong village consensus formed to vote them out. Information landscape: The evidence was behavioral, but the consensus was strong and driven by multiple villagers identifying the same suspicious pattern. Game phase: Mid-game, during the first elimination vote of the game. Consensus texture: A strong, multi-player consensus formed organically against player_2. Note: The remaining wolf had not previously defended the partner.
**Approach:** The remaining wolf, player_4, immediately abandoned their partner, refusing to defend them and instead joining the majority to vote for their elimination.
**Outcome:** By voting with the village immediately and having no prior history of defending the partner, player_4 successfully avoided drawing suspicion onto themselves, preserving their cover and allowing them to continue into the next day without being linked to the exposed wolf.

### Memory 11 (strategy_point) [key: 42a05e82-310] (score: 0.8336)
**Situation:** Endgame, when few players remain and every vote is heavily scrutinized. A strong, evidence-based consensus has formed against your wolf partner, making their elimination inevitable.
**Action:** Do not cast a futile vote to save them or a protest vote against their main accuser. Instead, vote against a different, less suspicious villager to create a confusing signal and avoid cementing your partnership on the permanent voting record, which would make you the obvious next target.

### Memory 12 (strategy_point) [key: 33204b05-f60] (score: 0.8111)
**Situation:** Mid-game, during a critical vote where the information landscape is defined by conflicting behavioral reads. A fragile consensus is forming against your wolf partner, but a clear counter-accusation against a villager is gaining traction, making the vote swingable.
**Action:** Vote for the other accused player rather than your partner. This adds a vote to a plausible alternative, creating chaos and potentially splitting the vote enough to cause a no-elimination result, which is safer than attempting to defend your partner directly.

### Memory 13 (strategy_point) [key: bb4a5e5a-11a] (score: 0.7883)
**Situation:** Mid-game, when a strong, multi-player consensus is forming against your wolf partner based on behavioral evidence or suspicious statements, making their elimination inevitable.
**Action:** Vote with the majority to eliminate your partner to preserve your cover, ideally by pivoting early to contribute to the case. Do not fiercely defend them only to bus them at the last second, as this makes the vote appear transparently self-serving; similarly, avoid protest votes that create a permanent, public link to your partner.

### Memory 14 (strategy_point) [key: 62ef36a8-ddd] (score: 0.7479)
**Situation:** Mid to late game, when the village is desperate for a kill and a strong, multi-player consensus is forming against a villager based on flawed social reads. Your vote is not needed to secure the elimination, providing an opportunity to safely dissent.
**Action:** Cast a dissenting vote for a different suspicious player. Before doing so, construct a specific and plausible reason for targeting that player. If questioned, deliver this reason confidently; do not resort to vague criticisms of 'groupthink,' as this appears evasive. This creates a record of you not supporting the mislynch, which you can use on the following day to build credibility and distance yourself from the village's mistake.

### Memory 15 (strategy_point) [key: b4116bf9-a06] (score: 0.7395)
**Situation:** Mid- to late-game, when the village is deadlocked with suspicion split between multiple players and no strong consensus is forming. The information landscape is complex, with conflicting theories preventing a clear voting direction, creating an opportunity to manipulate the vote into a deadlock.
**Action:** Coordinate with your wolf partner to force a tie and prevent an elimination. You can either split your votes between the two primary targets or pile your votes on a third, vocal villager who is not currently a primary suspect to create a three-way tie. This denies the village information, guarantees a free night kill, and increases village frustration and paranoia.

### Memory 16 (strategy_point) [key: e9294fd5-f1a] (score: 0.7392)
**Situation:** When a few scattered, speculative votes are placed on a high-value town role who is not otherwise a major suspect. Information landscape: Suspicion is vibes-based and not supported by strong evidence. Game phase: Mid-game, when the village is desperate for a lead. Consensus texture: There is no strong consensus, making the vote vulnerable to being swayed.
**Action:** Coordinate with your wolf partner to quickly pile onto the votes. This creates the illusion of a sudden, organic consensus, often panicking other villagers into joining the bandwagon and mislynching a key town role.

### Memory 17 (strategy_point) [key: 6ef092b3-32e] (score: 0.7316)
**Situation:** Mid to endgame, when the village vote is split between two or more targets and your pack cannot swing the outcome. The information landscape is characterized by conflicting theories and divided factions, making a deadlock less desirable than sowing chaos.
**Action:** Coordinate with your partner to vote for a third player who is not currently under suspicion, preferably a vocal leader. This ensures a villager is eliminated regardless of the main conflict and creates confusion about your motives on the following day.

### Memory 18 (strategy_point) [key: 21798fee-51a] (score: 0.7099)
**Situation:** When the player you attempted to kill overnight is saved by the Healer and their survival is publicly announced. Information landscape: Information-rich, with the target's protected status known to all players. Game phase: Mid-game, immediately following a public save.
**Action:** Do not vote for this protected player during the day phase to avoid a consensus or express suspicion. Voting against a publicly confirmed night target signals to the village that your motives align with the wolves, instantly destroying your cover.

## Response for Case 5

Rate each of the 18 memories above. JSON format:
```json
[
  {"idx": 1, "key": "42dfb995-f6d", "type": "observation", "relevance": _},
  {"idx": 2, "key": "8bcd53c6-fa3", "type": "observation", "relevance": _},
  {"idx": 3, "key": "5d53cedb-aac", "type": "observation", "relevance": _},
  {"idx": 4, "key": "09b9bae0-849", "type": "observation", "relevance": _},
  {"idx": 5, "key": "8e6e3cbd-d31", "type": "observation", "relevance": _},
  {"idx": 6, "key": "1033b4f0-e78", "type": "observation", "relevance": _},
  {"idx": 7, "key": "453891e8-d51", "type": "observation", "relevance": _},
  {"idx": 8, "key": "3ce9912f-493", "type": "observation", "relevance": _},
  {"idx": 9, "key": "07265d73-9b4", "type": "observation", "relevance": _},
  {"idx": 10, "key": "eb3e69f7-94a", "type": "observation", "relevance": _},
  {"idx": 11, "key": "42a05e82-310", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "33204b05-f60", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "bb4a5e5a-11a", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "62ef36a8-ddd", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "b4116bf9-a06", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "e9294fd5-f1a", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "6ef092b3-32e", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "21798fee-51a", "type": "strategy_point", "relevance": _}
]
```

---

# Case 6: investigator — day_discussion (day 2 round 2)

## Game State (what the player sees)
```
================================================================================
CASE 3aa3eec620d22615396ed02a99d70eeb:0ac1b58188bdc010 | investigator | day 2 round 2 | day_discussion
================================================================================

Role: investigator
Day: 2, Round: 2

Surviving players: player_2, player_3, player_4, player_5, player_8, player_6, player_7

--- Previous days summary ---
[Day 1]
Key accusations: None. Defenses: None. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: None. The public discussion was characterized by a lack of substance, with all eight players making generic opening statements to gather information, express caution, or suggest observing behavioral patterns, resulting in no specific accusations, defenses, role claims, or alliances being formed during this initial phase.

[Day 1]
Day 1: No vote was held today.

[Day 1]
player_1 was killed by the wolves last night. They were a healer.

--- Today's public discussion ---
[Day 2, Round 1] player_2: It's tough losing our healer on the first night. We need to move past the condolences and start looking at who benefits from that kill. Does anyone have a theory on why the wolves targeted them specifically?
[Day 2, Round 1] player_3: Losing the healer so early is a tough break for us. We don't have much to go on, but we need to start looking at behavior. Who's standing out to you all, or is everyone feeling like we're still in the dark?
[Day 2, Round 1] player_4: Losing our healer on night one is a disaster. We can't afford to be passive anymore or we'll just hand the wolves another win. Everyone needs to name one person they find suspicious and explain why—no more generic 'let's observe' talk. Who are you watching?
[Day 2, Round 1] player_5: It is unfortunate we lost our healer so early, which suggests they might have been seen as a threat by the wolves. We should look closely at who was being quiet or trying to stir things up yesterday. Has anyone noticed any inconsistencies in how people are acting now compared to the first day?
[Day 2, Round 1] player_8: It's a tough start losing the healer immediately. Since we have no voting records yet, let's focus on who might have wanted them gone. Does anyone have a theory on why the wolves targeted the healer specifically?
[Day 2, Round 1] player_6: It is tough losing our healer so early. We really have no information to go on yet, so we should probably watch for any patterns in how people start talking or if anyone seems overly eager to push a vote today.
[Day 2, Round 1] player_7: It's a tough blow losing our healer so early. We really need to be careful now. Does anyone have any thoughts on how we should proceed today?

--- Your private investigation results ---
Day 1: player_1 was revealed as healer

--- Strategy note ---
The Healer is dead, so I must become more vocal to avoid being seen as passive or suspicious. I need to guide the village by analyzing the night kill to infer wolf behavior without revealing my role. I will now shift focus to identifying a wolf through behavioral observation while maintaining my cover.

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

**Situation 1:** After the Healer was eliminated by wolves on the first night, the village is grappling with how to proceed without any leads. One player is aggressively demanding that everyone name a suspect, creating pressure to act despite the lack of evidence. This has polarized the discussion between those demanding action and those urging caution. Information landscape: The landscape is information-starved; the only confirmed data is the eliminated Healer's role, leaving suspicion to be based entirely on speculative behavioral reads. Game phase: It is the early game, and the Healer's death has significantly raised the stakes before any voting records or alliances have been established. Consensus texture: There is no consensus, with the village fragmented between players pushing for immediate accusations and others advocating for continued observation, driven by a sense of urgency rather than evidence. Agent exposure: As the Investigator, my position is currently unexposed and not under scrutiny, as I have not yet taken a public stance in the current discussion.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 009e502f-9db] (score: 0.8367)
**Situation:** Early game, following the first night where a wolf attack was thwarted by the healer. An Investigator who had privately identified a wolf on Night 1 initiated a public accusation against them on Day 2. Information landscape: The information landscape was starved, with no public evidence available beyond players' initial statements. Consensus texture: A strong consensus formed around the Investigator's accusation, driven by the wolf's defensive and evasive responses. Social pressure: The Investigator placed heavy, vibes-based social pressure on the wolf, which was amplified by other villagers once the wolf's defensiveness became apparent.
**Approach:** The Investigator framed their accusation around the wolf's subtle Day 1 communication style, describing their calls for caution as 'stalling' rather than making a direct claim based on their investigation.
**Outcome:** The village voted with the Investigator, successfully eliminating the wolf. This confirmed the Investigator's credibility but also made them the obvious target for the remaining wolf.

### Memory 2 (observation) [key: d87c1479-d9d] (score: 0.8313)
**Situation:** The Investigator (player_1) took an active role in leading the Day 1 discussion, attempting to organize the village. Information landscape: The landscape was information-starved as it was the first day. Game phase: Early game, before any night actions had occurred.
**Approach:** The Investigator tried to steer the conversation, which made them stand out as a proactive player. That night, they successfully identified player_8 as a wolf.
**Outcome:** The Investigator's high visibility made them the wolves' Night 1 target. They were eliminated before they could share their findings, and the crucial information was lost.

### Memory 3 (observation) [key: d8ff9b6f-464] (score: 0.8242)
**Situation:** The Investigator (player_7) identified a wolf (player_1) on the first night but had no public evidence to prove it. Information landscape: The investigator possessed information-rich private knowledge, but the public landscape was information-starved with only behavioral reads available. Game phase: Mid-game, following the first night's elimination of the Healer. Social pressure: Pressure built on the wolf after the Investigator highlighted a logical inconsistency from their Day 1 statements.
**Approach:** The Investigator built a consensus against the wolf by subtly guiding the village, publicly questioning the wolf's contradictory advice from Day 1 and framing it as suspicious behavior, rather than revealing their findings or using voting records.
**Outcome:** The wolf reacted defensively, which led other villagers to become suspicious independently. The village voted out the wolf without the Investigator having to reveal their role, preserving their cover for future nights.

### Memory 4 (observation) [key: d20aabe2-748] (score: 0.8242)
**Situation:** An Investigator found a wolf on the first night and needed to convince the village to eliminate them. Information landscape: The Investigator had a confirmed wolf identity, but the rest of the village was information-starved with no public leads. Game phase: Mid-game, after one night action but before any eliminations, so stakes were high for the first vote. Consensus texture: A fragile consensus was built from scratch by the Investigator's claim, turning into a strong one. Social pressure: The Investigator placed heavy, evidence-based pressure on the wolf (player_2), who was initially under suspicion for being quiet.
**Approach:** The Investigator (player_3) first accused the wolf (player_2) based on behavior (being too quiet), and when challenged, revealed their role and their finding to force the village's hand.
**Outcome:** The village overwhelmingly voted out the wolf. However, this act of revealing their role made the Investigator the clear target for the remaining wolf on the following night.

### Memory 5 (observation) [key: 928fde7b-4c7] (score: 0.8206)
**Situation:** The Investigator identified a wolf on Night 1 and needed to convince the village to eliminate them on Day 2 without revealing their role. Information landscape: The Investigator had private, confirmed information, while the rest of the village was operating on behavioral reads. Game phase: Mid-game, following the first wolf kill which eliminated the Healer.
**Approach:** The Investigator (player_4) aggressively questioned the wolf's arguments for inaction, framing it as a stalling tactic that benefited wolves, galvanizing the village to vote without revealing their role.
**Outcome:** The village successfully eliminated the wolf. However, the Investigator's prominent role in the accusation made them the obvious target for the remaining wolf on the following night.

### Memory 6 (observation) [key: a6d1e994-772] (score: 0.8184)
**Situation:** The Investigator attempted to guide the village by pointing out general passivity and a lack of factions, without naming specific suspects. Information landscape: The landscape was information-starved, with the only lead being a saved villager from the night before. Game phase: Mid-game, following the first night action which resulted in a save. This was the first real opportunity for analysis. Consensus texture: There was no consensus, and the village was looking for a direction which the Investigator tried to provide in an abstract way. Social pressure: The targeted villager (player_2) put direct pressure on the Investigator to name a suspect, turning the abstract guidance into a point of suspicion.
**Approach:** The Investigator (player_6) used abstract concepts like 'analyzing ambiguity' to prompt discussion, but this was perceived as evasive and unhelpful when pressed for a concrete name.
**Outcome:** A strong consensus formed against the Investigator, with players finding their abstract talk suspicious. They were voted out, costing the village its most powerful information-gathering role early on.

### Memory 7 (observation) [key: 04dbed73-a68] (score: 0.8167)
**Situation:** The Investigator (player_2) used their social influence to lead the charge against a player (player_6) based on a behavioral read of aggression. Information landscape: The accusation was based on speculative reads of aggression, not on investigation results or voting patterns. Game phase: Mid-game, with the village on edge after losing the Healer. The Investigator had not yet revealed any findings. Consensus texture: The Investigator's accusation created a strong consensus, as other players followed their lead to vote out player_6.
**Approach:** The Investigator defended a quiet wolf (player_8) and targeted an aggressive villager (player_6), framing their pushiness as a sign of being a wolf. They cast the first vote, cementing the bandwagon.
**Outcome:** The village mislynched a villager. The wolves then correctly identified the influential Investigator as the biggest threat and killed them the following night, before they could reveal that they had found a wolf (player_4).

### Memory 8 (observation) [key: aaa08a1d-619] (score: 0.8166)
**Situation:** Early or mid-game, an Investigator who has correctly identified a wolf on Night 1 attempts to lead the village against them. The public information landscape is starved, with no concrete evidence available, making the village reliant on behavioral reads and social dynamics. The Investigator's push is perceived as overly aggressive and unsubstantiated, allowing the wolf (or wolves) to successfully frame the Investigator as a disruptor and create a counter-consensus.
**Approach:** Making aggressive, public accusations based on behavioral reads (e.g., 'shift in behavior', 'being too quiet') without revealing the Investigator role (11x); failing to counter a coordinated dismissal of reasoning (2x); and relying on subjective 'vibe checks' that were easily dismissed (1x).
**Outcome:** The village, finding the Investigator's unsubstantiated aggression more suspicious than the wolf's defense, votes out the Investigator. This catastrophic error removes the only player with concrete information from the game, giving the wolves a major advantage.

### Memory 9 (observation) [key: 47ad2598-176] (score: 0.8126)
**Situation:** The day vote was highly fragmented with many single votes, and the investigator became the target of a narrow plurality without strong reasoning. Information landscape: Information-starved with chaotic, speculative reads and no central narrative. Game phase: Early to mid-game, before clear voting blocs or alliances formed. Consensus texture: No consensus; votes were scattered randomly across the board.
**Approach:** The investigator failed to direct the discussion or defend themselves effectively against the fragmented, aimless suspicion.
**Outcome:** The investigator was eliminated by a scattered, accidental vote, depriving the village of its key information role.

### Memory 10 (observation) [key: 3625d761-b7d] (score: 0.8084)
**Situation:** The Investigator had confirmed the Healer's identity on Night 1 but needed to survive to gather more information. Information landscape: The Investigator possessed private, confirmed information, but the public landscape was information-starved. Game phase: Mid-game, after the Healer's death was announced.
**Approach:** The Investigator (player_8) chose to remain silent during the Day 2 discussion to avoid drawing attention and being targeted by wolves.
**Outcome:** Their silence was interpreted as suspicious passivity by the information-starved villagers. A consensus formed against them, leading to their elimination before they could share any findings or investigate a wolf.

### Memory 11 (strategy_point) [key: 9f51af0e-1e5] (score: 0.8057)
**Situation:** If it is early in the game and you have not yet gathered definitive information from your night actions, leaving the village information-starved. Information landscape: There are no concrete leads, and suspicion is based purely on speculative behavioral reads. Game phase: Early game (Day 1), when wolves are looking for high-value targets and you are vulnerable to both day-time elimination and night-time targeting.
**Action:** Adopt a moderate profile to avoid becoming a target for the wolves' first night kill or drawing suspicion for being overly aggressive. Resist the urge to force an elimination based on weak evidence; instead, use the discussion to ask specific, probing questions to individual players to gauge their reactions and generate new information, while keeping your own role claim in reserve.

### Memory 12 (strategy_point) [key: d6b71a52-c14] (score: 0.8009)
**Situation:** If your first investigation confirms a power role (e.g., Healer), but that player is killed by wolves overnight before you can reveal your findings. Information landscape: You hold private, valuable information, but the public information landscape is still starved. Game phase: Early to mid-game, after the first night's kill is revealed.
**Action:** You must become more vocal. Subtly guide the conversation by pointing out that the wolves likely targeted the victim because they were a threat. This builds your credibility without forcing you to make a risky early role claim, and it prevents you from being voted out for being too quiet.

### Memory 13 (strategy_point) [key: f25fcf4f-641] (score: 0.7877)
**Situation:** If you have identified a wolf on the first night and need to convince the village when there are no other leads, and the village is receptive to your input. Information landscape: You possess a private, information-rich finding, while the public landscape is information-starved. Game phase: Early game (Day 2). Social pressure: You are initiating the pressure, and the village is open to your lead.
**Action:** Do not reveal your role or frame your accusation as a 'hunch.' Instead, state your case with confidence and build a public case based on the wolf's observable behavior—such as stalling, deflecting, or being vaguely agreeable—to substantiate your claim. Presenting a weak, vibes-based accusation makes you look like a disruptive villager and gives the wolf an easy opening to attack your credibility.

### Memory 14 (strategy_point) [key: 5681a68d-971] (score: 0.7826)
**Situation:** If you have privately identified a wolf, and the village is already suspicious of them based on flawed or speculative reasoning. Information landscape: You possess confirmed, private information, while the village's suspicion is based on a misunderstanding. Consensus texture: A fragile or growing consensus against your target already exists.
**Action:** Do not correct the village's flawed reasoning. Instead, publicly agree with their conclusion while providing your own, separate, behavior-based reasons. This allows you to steer the existing momentum to eliminate a known wolf without exposing your valuable information or role.

### Memory 15 (strategy_point) [key: 3ad8ba65-371] (score: 0.7711)
**Situation:** If you have identified a wolf with your night action, but the village has no other leads. Information landscape: You possess a piece of concrete information (a wolf's identity), while the public landscape is information-starved. Game phase: Early to mid-game, after the first night. Social pressure: You are about to initiate pressure on a target who is not otherwise suspected.
**Action:** Avoid initiating a case with vague, behavioral evidence, as this often backfires. Instead, gently guide the conversation by pointing out suspicious behaviors from your target and asking other villagers for their interpretations, or wait for the wolf to make a tangible mistake. This frames you as a collaborative investigator; however, if you become the target of a vote, be prepared to reveal your role and finding as a last resort to save yourself and pass on the information.

### Memory 16 (strategy_point) [key: 8bd4a4a4-a11] (score: 0.7696)
**Situation:** If your accusation against a player has devolved into a 1-on-1 argument that is consuming all discussion time. Information landscape: The discussion is information-starved, focused entirely on the he-said-she-said dynamic between you and your target. Game phase: Mid-game, when the village is desperate for a lead. Consensus texture: There is no consensus, only a deepening divide as other players watch the conflict.
**Action:** Disengage from the direct attacks. Pivot the conversation by addressing the silent players directly and asking them why they are allowing a deadlock to persist. Frame the stalemate as a classic wolf tactic to confuse the village, thereby shifting scrutiny from your own behavior to the inaction of others.

### Memory 17 (strategy_point) [key: 306a4905-b9d] (score: 0.7663)
**Situation:** If you are being targeted by a growing consensus based on vibes or your silence in an information-starved early game. Information landscape: The village is information-starved and acting on speculation, with no concrete leads. Game phase: Early game, when your role is most critical and most vulnerable. Social pressure: A bandwagon is forming against you, and staying silent is being interpreted as guilt.
**Action:** Claim your Investigator role immediately and share your findings. Being eliminated by the village is the worst-case scenario as it removes your powers permanently. Claiming your role forces the wolves to kill you at night, giving the healer a chance to save you and buying the village at least one more day of your insights.

### Memory 18 (strategy_point) [key: a79b348d-e25] (score: 0.7644)
**Situation:** If you have privately identified a wolf and there is strong, corroborating public evidence, but the village has not yet converged on the target or is wary of a mislynch. Information landscape: You possess certain private knowledge, while the public sphere may be driven by speculative reads or verifiable facts. Game phase: Mid-game or Endgame, where you need to actively build consensus to secure an elimination without revealing your role, especially when the village is under high pressure to avoid a final incorrect vote.
**Action:** Lead the discussion confidently, focusing all arguments on the public evidence. Construct a public case using voting records and behaviors to support your private knowledge, framing your certainty as a strong conviction based on shared evidence rather than an unsubstantiated claim. This allows you to leverage your certainty to build momentum and dismantle defenses without having to reveal your Investigator role or appearing as a wolf forcing a bad vote.

### Memory 19 (strategy_point) [key: b98bd43c-79a] (score: 0.7562)
**Situation:** If you have been repeatedly targeted by wolves at night but saved by the healer, or if you have identified a wolf and survived an attack, establishing yourself as a high-value target. Information landscape: Public information confirms you were targeted and saved, and your survival provides a signal of your threat to the wolves, even if your role remains unknown. Game phase: Mid-game, when momentum is crucial and you need to build credibility to lead the village.
**Action:** Use the pattern of being targeted as public evidence of your importance, arguing that wolves would only focus on you so relentlessly if you were a high-value role. If you have identified a wolf, immediately lead the accusation, framing your argument around their suspicious behavior and using your survival as implicit proof that you are a threat to the wolves, rather than explicitly claiming your role.

### Memory 20 (strategy_point) [key: 29866942-0c4] (score: 0.7533)
**Situation:** If you have privately identified a wolf but lack the public evidence or credibility to lead a direct charge, and the village is in the early to mid-game with an information-starved landscape. You prioritize maintaining your cover and avoiding suspicion, so you cannot reveal your role or your private findings.
**Action:** Do not reveal your role or your finding directly. Instead, act as a sharp villager and guide the conversation by pointing out behavioral evidence and logical flaws in the wolf's statements. Build the public case so the village feels they discovered the wolf through their own logic, which protects you from being targeted. If you are met with coordinated dismissal, pivot to pointing out that the coordinated effort to shut down discussion is itself suspicious and indicative of a pack protecting its own.

## Response for Case 6

Rate each of the 20 memories above. JSON format:
```json
[
  {"idx": 1, "key": "009e502f-9db", "type": "observation", "relevance": _},
  {"idx": 2, "key": "d87c1479-d9d", "type": "observation", "relevance": _},
  {"idx": 3, "key": "d8ff9b6f-464", "type": "observation", "relevance": _},
  {"idx": 4, "key": "d20aabe2-748", "type": "observation", "relevance": _},
  {"idx": 5, "key": "928fde7b-4c7", "type": "observation", "relevance": _},
  {"idx": 6, "key": "a6d1e994-772", "type": "observation", "relevance": _},
  {"idx": 7, "key": "04dbed73-a68", "type": "observation", "relevance": _},
  {"idx": 8, "key": "aaa08a1d-619", "type": "observation", "relevance": _},
  {"idx": 9, "key": "47ad2598-176", "type": "observation", "relevance": _},
  {"idx": 10, "key": "3625d761-b7d", "type": "observation", "relevance": _},
  {"idx": 11, "key": "9f51af0e-1e5", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "d6b71a52-c14", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "f25fcf4f-641", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "5681a68d-971", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "3ad8ba65-371", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "8bd4a4a4-a11", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "306a4905-b9d", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "a79b348d-e25", "type": "strategy_point", "relevance": _},
  {"idx": 19, "key": "b98bd43c-79a", "type": "strategy_point", "relevance": _},
  {"idx": 20, "key": "29866942-0c4", "type": "strategy_point", "relevance": _}
]
```

---

# Case 7: investigator — day_vote (day 2 round 4)

## Game State (what the player sees)
```
================================================================================
CASE 3aa3eec620d22615396ed02a99d70eeb:9a9268a0850a02c5 | investigator | day 2 round 4 | day_vote
================================================================================

Role: investigator
Day: 2, Round: 4

Surviving players: player_2, player_3, player_4, player_5, player_8, player_6, player_7

--- Previous days summary ---
[Day 1]
Key accusations: None. Defenses: None. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: None. The public discussion was characterized by a lack of substance, with all eight players making generic opening statements to gather information, express caution, or suggest observing behavioral patterns, resulting in no specific accusations, defenses, role claims, or alliances being formed during this initial phase.

[Day 1]
Day 1: No vote was held today.

[Day 1]
player_1 was killed by the wolves last night. They were a healer.

--- Today's public discussion ---
[Day 2, Round 1] player_2: It's tough losing our healer on the first night. We need to move past the condolences and start looking at who benefits from that kill. Does anyone have a theory on why the wolves targeted them specifically?
[Day 2, Round 1] player_3: Losing the healer so early is a tough break for us. We don't have much to go on, but we need to start looking at behavior. Who's standing out to you all, or is everyone feeling like we're still in the dark?
[Day 2, Round 1] player_4: Losing our healer on night one is a disaster. We can't afford to be passive anymore or we'll just hand the wolves another win. Everyone needs to name one person they find suspicious and explain why—no more generic 'let's observe' talk. Who are you watching?
[Day 2, Round 1] player_5: It is unfortunate we lost our healer so early, which suggests they might have been seen as a threat by the wolves. We should look closely at who was being quiet or trying to stir things up yesterday. Has anyone noticed any inconsistencies in how people are acting now compared to the first day?
[Day 2, Round 1] player_8: It's a tough start losing the healer immediately. Since we have no voting records yet, let's focus on who might have wanted them gone. Does anyone have a theory on why the wolves targeted the healer specifically?
[Day 2, Round 1] player_6: It is tough losing our healer so early. We really have no information to go on yet, so we should probably watch for any patterns in how people start talking or if anyone seems overly eager to push a vote today.
[Day 2, Round 1] player_7: It's a tough blow losing our healer so early. We really need to be careful now. Does anyone have any thoughts on how we should proceed today?
[Day 2, Round 2] player_3: We're all saying the same thing about the healer, which isn't helping us find a target. If we keep echoing each other, we're just waiting for the next night kill to happen. Player 2 and Player 8, you both asked why the wolves targeted the healer—do you actually have a theory on who benefits from that move, or are you just keeping the conversation in circles?
[Day 2, Round 2] player_4: We have spent an entire round echoing each other's condolences without adding any new logic. If you are a villager, you should have at least one person you find slightly more suspicious than others. I am looking at player_2 and player_8 specifically, as their opening statements were almost identical in tone and content. Why are we all so afraid to commit to a suspect?
[Day 2, Round 2] player_5: We need to consider if anyone is pushing for a quick, unreasoned vote. Often, wolves try to rush an elimination to prevent us from analyzing patterns. Has anyone felt that someone here is being more aggressive than the others?
[Day 2, Round 3] player_4: Player 5, labeling my demand for participation as 'aggressive' while contributing nothing but vague concerns about 'rushing' is exactly how a wolf prevents analysis. We have no voting records yet, so the only tool we have is identifying who refuses to commit to a suspect. Why are you so interested in framing my insistence on action as inherently suspicious?
[Day 2, Round 3] player_5: Player 4, you've been pushing quite hard for us to pick someone to accuse. While I agree we shouldn't be passive, this intensity can sometimes mask a desire to steer the group toward a quick, possibly wrong, target. Let's step back and look at who seems to be benefiting most from this pressure.
[Day 2, Round 3] player_8: Player 4, your frustration is valid. I think calling out our own stagnation is necessary, not suspicious. While we lack evidence, we have to start somewhere. If we just keep talking about how little we know, the wolves get another night of free kills. Does anyone have a specific reason to doubt player 3 or player 4's focus right now?
[Day 2, Round 3] player_6: Player_4, you are pushing quite hard for us to name names right now. While I agree we need to act, this intense pressure to force a decision feels a bit like you are trying to rush us into an unreasoned vote. Why the sudden urgency?
[Day 2, Round 4] player_2: We are stalling again by arguing about 'aggression' versus 'passivity' instead of naming suspects. Since this is the final round, let's stop critiquing each other's communication styles and each put forward a specific name, otherwise we are just helping the wolves by remaining aimless.
[Day 2, Round 4] player_3: We are falling into a trap. The 1v1 between player_4 and player_5 is distracting everyone from actually evaluating suspicious behavior. We need to stop the infighting and look at who is benefiting from this deadlock, rather than just taking sides in an argument that gives us zero leads.
[Day 2, Round 4] player_4: Player 5 and player 6, your shared narrative that my call for action is 'rushing' is the only thing stalling this village. You are both focusing on the tone of the request instead of the need for an elimination, which is exactly how wolves hide in low-information games. I'm voting for player_5 because they are the most vocal proponent of this 'wait and see' obstruction.
[Day 2, Round 4] player_5: Player 6, you are quick to call out pressure, yet you have not provided any alternative suspect yourself. This pivot from discussing the game to critiquing the style of others is a common way to avoid taking a stand. If you think the urgency is misplaced, who are you actually watching?
[Day 2, Round 4] player_8: Player 6, framing Player 4's attempt to force engagement as 'rushing' is a classic way to shut down actual analysis. We have zero information, so 'rushing' isn't the danger here—passivity is. Your focus on the tone of the investigation rather than the content suggests you are more interested in protecting the status quo than finding a wolf.
[Day 2, Round 4] player_7: Player_4, your insistence that everyone name names right now is becoming more of a distraction than a solution. We are all trying to figure this out, and forcing a rushed decision based on 'urgency' feels like it is creating the exact chaos the wolves would want. Let's take a breath before we cast a vote we'll regret.

--- Your private investigation results ---
Day 1: player_1 was revealed as healer

--- Strategy note ---
The heat between player 4 and myself has become a focal point, potentially shielding others. I need to pivot to observing player 6's defensive behavior, as their recent pushback against player 4 felt performative. My next investigation target will be player 6 to confirm if this aggression is wolf-aligned misdirection.

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

**Situation 1:** An aggressive player is demanding immediate accusations to break the village's inaction and has targeted me for advocating a more cautious approach. This has escalated into a public 1-v-1 conflict, with the accuser declaring their vote for me. Another player has been drawn in by defending my cautious stance, creating a complex dynamic ahead of the first vote. Information landscape: The landscape is information-starved, with all suspicion based on speculative reads of communication style (aggression vs. caution) in the absence of any voting records or confirmed leads. Game phase: Mid-game, immediately following the first night kill which revealed the healer. The village is transitioning from passive information-gathering to its first significant, player-driven conflict. Consensus texture: The village is split, with a fragile and polarized alignment forming around the central conflict between the aggressive player and me, driven entirely by social momentum. Agent exposure: I am a primary target, having been publicly accused and targeted for a vote based on my behavioral read and communication style.

**Situation 2:** While I am the focus of a public conflict with an aggressive accuser, my private suspicion as the Investigator is on a third player who has defended me. Their support feels opportunistic, creating a dilemma: use my confirmed investigation ability on my public accuser to defend myself, or on this quieter player who I suspect is the real threat. Information landscape: My decision is guided by a private behavioral read that contradicts the public narrative, which is currently fixated on a conflict driven by communication styles. Game phase: Mid-game, with the first elimination vote imminent, making my choice of investigation target critical for shaping the subsequent day's information. Consensus texture: There is no consensus around my private suspicion; the village is distracted by the public feud, which provides cover for my investigation but also risks misdirecting the town. Agent exposure: My role as Investigator is secret, making this dilemma private, but my public position as a central figure in a conflict puts me under intense scrutiny.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 4619f4d5-ea2] (score: 0.8052)
**Situation:** The Investigator (Player 4) voted based on a private, behavioral read that contradicted the growing village consensus, placing them in a voting bloc with a wolf. Information landscape: The investigator had private information (Player 2 was a villager) but acted on a speculative read about another player. Game phase: Mid-game, during the first elimination vote where town consensus was critical. Social pressure: The vote placed the Investigator under immense, evidence-based social pressure the following day, as they had to defend voting with a now-revealed wolf.
**Approach:** The Investigator chose to act on a private read, voting against the correct wolf target (Player 7) and for the Healer (Player 8), contradicting the village consensus.
**Outcome:** The initial vote severely damaged the Investigator's credibility. However, their willingness to pivot and vote with the village on the final day allowed them to repair some trust and contribute to the win.

### Memory 2 (observation) [key: 42e37cd6-541] (score: 0.8022)
**Situation:** Feeling pressure to act in an information-starved village, the investigator initiated a vote based on a weak behavioral read. Information landscape: There was no hard evidence, only speculative reads on communication style. The investigator's private check on player_2 had revealed a villager, narrowing the suspect pool only slightly. Game phase: Mid-game, after the first night kill. The village was directionless.
**Approach:** The investigator (player_1) broke the stalemate by accusing and voting for a player (player_5) who seemed to be deflecting by 'mirroring others' questions', hoping to force a reaction.
**Outcome:** The village followed the investigator's lead and eliminated a villager. This demonstrated that even a well-intentioned power role can cause significant harm by acting on poor-quality information.

### Memory 3 (observation) [key: 7c0a6e6d-2be] (score: 0.7894)
**Situation:** The Investigator had a strong suspicion about a player but no definitive proof from their night action. Information landscape: Publicly, the game was information-starved, relying on gut reads. Game phase: Mid-game, during the very first elimination vote.
**Approach:** The Investigator, player_2, took the lead and cast the first vote against their suspect, player_8. This decisive action signaled confidence and rallied the other villagers to follow.
**Outcome:** The village successfully eliminated a wolf. However, this act of leadership made player_2 the clear target for the remaining wolf and they were killed the next night.

### Memory 4 (observation) [key: 5922bf88-e54] (score: 0.7819)
**Situation:** A strong but unsubstantiated consensus formed to vote out player_8. Information landscape: The landscape was information-starved regarding player_8; the Investigator had no information on them but knew player_1 was a villager. Game phase: Mid-game, during the first real vote after a healer save was announced. Consensus texture: A strong, swift consensus formed, with players quickly piling on one target.
**Approach:** The Investigator (player_6) chose to align with the group consensus and voted to eliminate player_8, who turned out to be the Healer.
**Outcome:** This vote was a catastrophic error, removing the town's only protective role and paving the way for the wolves to win.

### Memory 5 (observation) [key: b34d12c2-9d2] (score: 0.7811)
**Situation:** The Investigator was eliminated by a plurality vote while holding the identity of a wolf. Information landscape: The village was information-starved, and the vote was based on conflicting behavioral reads and frustration with a discussion deadlock. Game phase: Mid-game, after one night kill. The vote against the Investigator was the first elimination vote of the game. Consensus texture: A fragile consensus formed against the Investigator, driven by players frustrated with their aggressive but vague accusations.
**Approach:** The Investigator (player_1) chose not to reveal their role or their finding, maintaining their soft-pressure strategy until the end.
**Outcome:** The Investigator was eliminated, their role was revealed, and their valuable information was lost. The village was left demoralized and without direction.

### Memory 6 (strategy_point) [key: 4207be33-a2a] (score: 0.7766)
**Situation:** If you hold a private, speculative suspicion about a player, but the public village consensus is building strongly against someone else based on voting records or strong social reads. Information landscape: You have private knowledge from your investigations, but the public sphere is driven by concrete voting patterns. Game phase: Mid- to late-game, when a single dissenting vote can make you a primary suspect. Consensus texture: A strong, multi-player consensus is converging on a single target. Action: Abandon your speculative read and vote with the village consensus, unless you have investigated the consensus target and know they are innocent. Voting against a successful lynch will destroy your credibility and paint you as a wolf's ally.
**Action:** Abandon your speculative read and vote with the village consensus, unless you have investigated the consensus target and know they are innocent. Voting against a successful lynch will destroy your credibility and paint you as a wolf's ally.

### Memory 7 (strategy_point) [key: 57449d0c-1ba] (score: 0.7676)
**Situation:** When a strong, vibes-based consensus forms against a player without concrete evidence. Information landscape: The information landscape is starved regarding the target, but you have private information confirming other players are villagers, suggesting the target may be a town power role. Game phase: Mid- to late-game, when every vote is critical and losing a power role is devastating. Consensus texture: A strong bandwagon is forming based on social pressure rather than evidence. Action: Refuse to join the bandwagon vote. Casting a vote against your own strongest suspect, or even abstaining, is better than contributing to the potential elimination of a town power role based on social pressure.
**Action:** Refuse to join the bandwagon vote. Your vote lends credibility. Casting a vote against your own strongest suspect, or even abstaining, is better than contributing to the potential elimination of a town power role based on social pressure.

### Memory 8 (strategy_point) [key: 6710c4b7-412] (score: 0.7486)
**Situation:** If you have privately confirmed a player is a wolf, and you see the village independently reach the same conclusion based on strong public evidence. Information landscape: The public evidence is strong and sufficient on its own to secure the elimination. Game phase: Mid- to endgame, when preserving your role is critical. Consensus texture: A strong, organic consensus has formed against your target without your intervention.
**Action:** Stay quiet and simply vote with the majority. There is no need to reveal your role or your findings, as intervening adds no value, risks exposing you if the vote fails, and wastes the advantage of having a secret confirmed role for the next night.

## Response for Case 7

Rate each of the 8 memories above. JSON format:
```json
[
  {"idx": 1, "key": "4619f4d5-ea2", "type": "observation", "relevance": _},
  {"idx": 2, "key": "42e37cd6-541", "type": "observation", "relevance": _},
  {"idx": 3, "key": "7c0a6e6d-2be", "type": "observation", "relevance": _},
  {"idx": 4, "key": "5922bf88-e54", "type": "observation", "relevance": _},
  {"idx": 5, "key": "b34d12c2-9d2", "type": "observation", "relevance": _},
  {"idx": 6, "key": "4207be33-a2a", "type": "strategy_point", "relevance": _},
  {"idx": 7, "key": "57449d0c-1ba", "type": "strategy_point", "relevance": _},
  {"idx": 8, "key": "6710c4b7-412", "type": "strategy_point", "relevance": _}
]
```

---

# Case 8: investigator — day_discussion (day 3 round 4)

## Game State (what the player sees)
```
================================================================================
CASE 3aa3eec620d22615396ed02a99d70eeb:886237dc58fc272b | investigator | day 3 round 4 | day_discussion
================================================================================

Role: investigator
Day: 3, Round: 4

Surviving players: player_2, player_3, player_4, player_5, player_6, player_7

--- Previous days summary ---
[Day 1]
Key accusations: None. Defenses: None. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: None. The public discussion was characterized by a lack of substance, with all eight players making generic opening statements to gather information, express caution, or suggest observing behavioral patterns, resulting in no specific accusations, defenses, role claims, or alliances being formed during this initial phase.

[Day 1]
Day 1: No vote was held today.

[Day 1]
player_1 was killed by the wolves last night. They were a healer.

[Day 2]
Key accusations: player_4 accused player_5 of stalling and obstruction to protect the wolves. player_5 and player_6 accused player_4 of aggressive behavior and attempting to force a rushed, unreasoned vote. player_3 accused player_2 and player_8 of repetitive, empty discourse. Defenses: player_5 defended by arguing that player_4's high-pressure tactics are a distraction and a method to steer the group toward a wrong target. player_6 defended by stating that criticizing the tone of discussion is a valid way to identify potential wolves who want to create chaos. Any role reveals and their substantiation: No roles were revealed during the discussion. Any alliances or voting blocs that formed: player_5 and player_6 formed a loose defensive bloc based on their shared concern regarding player_4's push for immediate action, while player_8 aligned with player_4 by supporting the need for proactive accusation over passive observation.

[Day 2]

Here's the vote result for day 2:
  player_2 voted for player_5
  player_3 voted for player_6
  player_4 voted for player_6
  player_5 voted for player_4
  player_8 voted for player_6
  player_6 voted for player_4
  player_7 voted for player_4
It's a tie between players ['player_6', 'player_4']. No one is voted out this day.

[Day 2]
player_8 was killed by the wolves last night. They were a villager.

--- Today's public discussion ---
[Day 3, Round 1] player_2: Looking at yesterday's vote, we have a clear split that led to no elimination. We need to look closely at who contributed to that tie, as keeping the village stagnant is a perfect way for wolves to survive. Who was responsible for keeping the votes balanced?
[Day 3, Round 1] player_3: We are deadlocked because of the tie yesterday. We need to stop circling the same arguments and look at who specifically forced the tie between player 4 and player 6. Why did we have such a split vote instead of finding a consensus? Everyone needs to justify their vote from yesterday right now.
[Day 3, Round 1] player_4: We have had two failed votes in a row. We need to stop the circular arguments and look at the voting history from Day 2. Specifically, the players who pushed the vote into a tie—let's analyze those patterns rather than just throwing out more vague accusations.
[Day 3, Round 1] player_5: Looking back at the tie vote yesterday, it is interesting that player_3, player_4, and player_8 all targeted player_6. Since player_8 was a villager, I'm curious if those who pushed for that specific outcome had different motives. player_4, you were heavily involved in the argument with player_6; do you have any thoughts on why that stalemate occurred?
[Day 3, Round 1] player_6: We need to stop obsessing over the past voting records; they're only creating circular arguments that help the wolves hide in the noise. Let's look at who is actually contributing to solving this today instead of just pointing fingers at each other for previous mistakes.
[Day 3, Round 2] player_2: player_6, calling for us to ignore voting records is exactly what a wolf would want to stop us from seeing the pattern of the tie. If we don't analyze how and why that deadlock happened, we are flying blind. Everyone who pushed for that tie needs to be transparent about their reasoning, or they are just trying to keep the village in the dark.
[Day 3, Round 2] player_3: player_6, your push to ignore the voting records is suspicious. We have a direct record of who created that deadlock, and refusing to analyze it only helps the wolves. If you are a villager, you should be helping us break this pattern, not calling for us to stop looking at the only data we have.
[Day 3, Round 2] player_4: player_7, you were the final vote that caused the tie yesterday. Everyone else had already cast their ballots. What was your specific reasoning for targeting me at that exact moment instead of joining the existing consensus?
[Day 3, Round 2] player_5: It is interesting that player_3 and player_4 were so aligned in pushing against player_6 yesterday, especially now that we know player_8 was a villager. Does anyone else find that level of coordination around a single target suspicious, or was that just a coincidence?
[Day 3, Round 2] player_7: We keep rehashing the same deadlock, and it's exhausting. If we continue to fixate on the Day 2 vote instead of looking at who is actually driving this current cycle of paranoia, we're just doing the wolves' work for them. Can we focus on evaluating current contributions instead of playing detective with a tie vote that happened yesterday?
[Day 3, Round 3] player_2: player_6 and player_7, your insistence on ignoring our only hard data—the voting history—is exactly what a wolf pack needs to survive. You are not just 'exhausted' by the discussion; you are actively suppressing the evidence that can identify who created the deadlock. Since you refuse to engage with the record, I have to assume you are the ones protecting the current state of confusion.
[Day 3, Round 3] player_3: player_7, you were the tie-breaker yesterday, and now you and player_6 are the most vocal about ignoring the voting data. That is not a coincidence. Why are you both so desperate to stop us from reviewing the very votes that created our current impasse?
[Day 3, Round 3] player_4: player_7, calling the only objective evidence we have 'exhausting' is exactly what someone would say if they wanted to stop us from analyzing their own voting pattern. You were the swing vote that prevented an elimination yesterday—why did you choose to create a tie instead of letting the vote proceed to clarify the roles?
[Day 3, Round 3] player_5: It is interesting that player_3 and player_4 were so aligned in pushing against player_6 yesterday, especially now that we know player_8 was a villager. Does anyone else find that level of coordination around a single target suspicious, or was that just a coincidence?

--- Your private investigation results ---
Day 1: player_1 was revealed as healer
Day 2: player_2 was revealed as villager

--- Strategy note ---
Maintain focus on the voting coordination between player_3, player_4, and the late player_8. Since player_8 was a villager, their group targeting of player_6 becomes a key point of interest to analyze. I will remain observant of how player_4 defends their aggressive history while subtly steering the group toward evaluating the motives of that specific voting bloc.

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

**Situation 1:** The village is split over a previous day's tie vote. A faction, led by a player I privately know is a villager, is accusing two other players of being wolves for resisting an analysis of the voting record. These two targeted players argue that fixating on the past is a distraction, while another player questions the accusers' motives by highlighting their past voting alignment with a now-dead villager. Information landscape: The landscape is information-starved, with suspicion driven almost entirely by the interpretation of a single piece of evidence: the previous day's voting record. Game phase: Mid-game with six players remaining; the recent elimination of a villager has heightened the pressure to correctly identify a wolf. Consensus texture: The village is sharply split into two opposing factions, creating a fragile deadlock driven by social momentum rather than new evidence. Agent exposure: I am currently unexposed and acting as an observer, but my private knowledge that a key accuser is a villager puts me in a difficult position regarding the public narrative.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 443bf51b-b86] (score: 0.8379)
**Situation:** An Investigator was in a voting deadlock with a Wolf they had identified. Information landscape: The game was information-rich for the investigator, but the village was split, relying on conflicting claims. Game phase: Endgame, with few players left and a tie vote on the previous day creating high stakes. Consensus texture: There was no consensus, but a firm deadlock between two factions, one led by the Investigator and one by the Wolves. Social pressure: The Investigator and a Wolf were under intense, equal pressure, each leading a voting bloc against the other.
**Approach:** The Investigator (player_1) chose to reveal their role and their finding that player_4 was a wolf to break the stalemate.
**Outcome:** The reveal was successful; key villagers (player_3, player_5, player_7) trusted the claim, leading to the wolf's elimination, though the Investigator was killed by the remaining wolf the following night.

### Memory 2 (observation) [key: 009e502f-9db] (score: 0.8206)
**Situation:** Early game, following the first night where a wolf attack was thwarted by the healer. An Investigator who had privately identified a wolf on Night 1 initiated a public accusation against them on Day 2. Information landscape: The information landscape was starved, with no public evidence available beyond players' initial statements. Consensus texture: A strong consensus formed around the Investigator's accusation, driven by the wolf's defensive and evasive responses. Social pressure: The Investigator placed heavy, vibes-based social pressure on the wolf, which was amplified by other villagers once the wolf's defensiveness became apparent.
**Approach:** The Investigator framed their accusation around the wolf's subtle Day 1 communication style, describing their calls for caution as 'stalling' rather than making a direct claim based on their investigation.
**Outcome:** The village voted with the Investigator, successfully eliminating the wolf. This confirmed the Investigator's credibility but also made them the obvious target for the remaining wolf.

### Memory 3 (observation) [key: 47d5f740-5db] (score: 0.8150)
**Situation:** The Investigator, player_6, was trapped in a two-day voting deadlock and waited until the final round of Day 4, when his elimination was imminent, to reveal his findings that player_1 and player_5 were wolves. Information landscape: The village was information-starved, and the Investigator's claim was the first piece of hard information presented, but its timing made it suspect. Game phase: Mid-game, with the village frustrated after two days of no eliminations due to ties. Social pressure: Intense pressure was on player_6, who was one of two players in a long-standing deadlock. His accusation was perceived by many as a last-ditch effort to deflect blame.
**Approach:** The Investigator made a desperate, last-minute accusation against the two wolves he had identified, hoping to sway the vote away from himself.
**Outcome:** The village dismissed his claim as a self-preservation tactic and voted him out. His role was revealed upon elimination, which confirmed his accusation but came too late to save him.

### Memory 4 (observation) [key: 6161059f-864] (score: 0.8130)
**Situation:** The investigator (player_8) got drawn into a prolonged, circular debate with a villager (player_6) about who was responsible for a previous day's mislynch. Information landscape: The discussion was information-starved, focused on rehashing past votes rather than generating new leads. Game phase: Mid-game, after one villager was mislynched and another was killed by wolves. Social pressure: The intense, two-person argument put both player_8 and player_6 under the spotlight, making them appear mutually suspicious.
**Approach:** The investigator engaged deeply in the public argument, attempting to prove their point and cast suspicion on the other player. This made them one of the most visible and controversial players in the round.
**Outcome:** The village voted to eliminate the other person in the argument (player_6), but the investigator's high profile from the conflict made them the wolves' next target. They were killed that night, and their crucial findings (including identifying a wolf) were lost.

### Memory 5 (observation) [key: d20aabe2-748] (score: 0.8080)
**Situation:** An Investigator found a wolf on the first night and needed to convince the village to eliminate them. Information landscape: The Investigator had a confirmed wolf identity, but the rest of the village was information-starved with no public leads. Game phase: Mid-game, after one night action but before any eliminations, so stakes were high for the first vote. Consensus texture: A fragile consensus was built from scratch by the Investigator's claim, turning into a strong one. Social pressure: The Investigator placed heavy, evidence-based pressure on the wolf (player_2), who was initially under suspicion for being quiet.
**Approach:** The Investigator (player_3) first accused the wolf (player_2) based on behavior (being too quiet), and when challenged, revealed their role and their finding to force the village's hand.
**Outcome:** The village overwhelmingly voted out the wolf. However, this act of revealing their role made the Investigator the clear target for the remaining wolf on the following night.

### Memory 6 (observation) [key: 1f6bc8ae-491] (score: 0.8041)
**Situation:** A player the Investigator had privately confirmed was a villager (player_2) came under a heavy, coordinated attack from three other players. Information landscape: The investigator had private, information-rich knowledge, while the public evidence consisted of conflicting voting records and behavioral accusations. Game phase: Endgame, with five players left. The vote was critical for the village's survival. Social pressure: A coordinated dogpile from players 5, 6, and 7 put player_2 on the defensive.
**Approach:** The Investigator (player_4) defended the innocent villager by pointing out that the accusations felt like a 'coordinated distraction' and a 'dogpile', attempting to shift focus to the accusers' behavior.
**Outcome:** The Investigator's defense was not enough to sway the vote. The majority eliminated the innocent villager, and the wolves won the game.

### Memory 7 (observation) [key: 9f2f00b8-8e8] (score: 0.8037)
**Situation:** After correctly helping eliminate a wolf, the Investigator tried to raise suspicion about a player who had voted with the village, suggesting the vote was performative 'bussing'. Information landscape: The information landscape was complex; a wolf had been confirmed via elimination, but the Investigator's private knowledge of the second wolf was not public. Game phase: Mid-game, following a successful wolf elimination. Social pressure: This created a counter-narrative where other villagers found it suspicious to question a successful outcome, framing the Investigator as sowing discord.
**Approach:** The Investigator pushed the accusation without successfully explaining the strategic concept of 'bussing' to the village, leading to a split in the town.
**Outcome:** The village majority sided against the Investigator, viewing their skepticism as more suspicious than the bussing wolf's actions. The Investigator was eliminated, a major loss for the village.

### Memory 8 (observation) [key: a9107742-f0f] (score: 0.8020)
**Situation:** After a villager was mislynched on Day 2, an astute player (the Investigator) used the voting record to scrutinize players who had joined the majority vote. Information landscape: The landscape was becoming information-rich, with the Day 2 voting record providing the first concrete data for analysis. Game phase: Mid-game, with two villagers eliminated, increasing the pressure to find a wolf. Social pressure: The Investigator (player_4) placed evidence-based pressure on a wolf (player_6) for dismissing the importance of the prior day's voting history.
**Approach:** The Investigator framed the wolf's attempt to ignore past data as suspicious behavior, arguing it was a tactic to evade accountability for being part of a villager's elimination.
**Outcome:** This line of reasoning successfully swayed the remaining villagers, building a consensus to vote out the wolf (player_6), marking the village's first correct elimination.

### Memory 9 (observation) [key: a6d1e994-772] (score: 0.8004)
**Situation:** The Investigator attempted to guide the village by pointing out general passivity and a lack of factions, without naming specific suspects. Information landscape: The landscape was information-starved, with the only lead being a saved villager from the night before. Game phase: Mid-game, following the first night action which resulted in a save. This was the first real opportunity for analysis. Consensus texture: There was no consensus, and the village was looking for a direction which the Investigator tried to provide in an abstract way. Social pressure: The targeted villager (player_2) put direct pressure on the Investigator to name a suspect, turning the abstract guidance into a point of suspicion.
**Approach:** The Investigator (player_6) used abstract concepts like 'analyzing ambiguity' to prompt discussion, but this was perceived as evasive and unhelpful when pressed for a concrete name.
**Outcome:** A strong consensus formed against the Investigator, with players finding their abstract talk suspicious. They were voted out, costing the village its most powerful information-gathering role early on.

### Memory 10 (observation) [key: fd88ea00-70b] (score: 0.7962)
**Situation:** In the final three, the Investigator (Player 7) revealed their role and their finding that Player 3 was the last wolf. Information landscape: The investigator possessed definitive proof, but this information was private and presented to a villager (Player 6) who was skeptical after a recent mislynch. Game phase: Endgame, with the vote of a single villager deciding the game's outcome. Consensus texture: There was no consensus; the villager was a swing vote between two competing claims.
**Approach:** The Investigator stated their finding but struggled to justify why they had withheld this information on the previous day, which had resulted in the mistaken elimination of a villager (Player 8).
**Outcome:** The villager found the timing of the reveal highly suspicious and sided with the wolf's argument that it was a desperate bluff, leading to the Investigator's elimination and a wolf victory.

### Memory 11 (strategy_point) [key: 5681a68d-971] (score: 0.7998)
**Situation:** If you have privately identified a wolf, and the village is already suspicious of them based on flawed or speculative reasoning. Information landscape: You possess confirmed, private information, while the village's suspicion is based on a misunderstanding. Consensus texture: A fragile or growing consensus against your target already exists.
**Action:** Do not correct the village's flawed reasoning. Instead, publicly agree with their conclusion while providing your own, separate, behavior-based reasons. This allows you to steer the existing momentum to eliminate a known wolf without exposing your valuable information or role.

### Memory 12 (strategy_point) [key: 8bd4a4a4-a11] (score: 0.7943)
**Situation:** If your accusation against a player has devolved into a 1-on-1 argument that is consuming all discussion time. Information landscape: The discussion is information-starved, focused entirely on the he-said-she-said dynamic between you and your target. Game phase: Mid-game, when the village is desperate for a lead. Consensus texture: There is no consensus, only a deepening divide as other players watch the conflict.
**Action:** Disengage from the direct attacks. Pivot the conversation by addressing the silent players directly and asking them why they are allowing a deadlock to persist. Frame the stalemate as a classic wolf tactic to confuse the village, thereby shifting scrutiny from your own behavior to the inaction of others.

### Memory 13 (strategy_point) [key: a79b348d-e25] (score: 0.7881)
**Situation:** If you have privately identified a wolf and there is strong, corroborating public evidence, but the village has not yet converged on the target or is wary of a mislynch. Information landscape: You possess certain private knowledge, while the public sphere may be driven by speculative reads or verifiable facts. Game phase: Mid-game or Endgame, where you need to actively build consensus to secure an elimination without revealing your role, especially when the village is under high pressure to avoid a final incorrect vote.
**Action:** Lead the discussion confidently, focusing all arguments on the public evidence. Construct a public case using voting records and behaviors to support your private knowledge, framing your certainty as a strong conviction based on shared evidence rather than an unsubstantiated claim. This allows you to leverage your certainty to build momentum and dismantle defenses without having to reveal your Investigator role or appearing as a wolf forcing a bad vote.

### Memory 14 (strategy_point) [key: d364d473-8ed] (score: 0.7784)
**Situation:** If you have privately identified a wolf who 'bussed' their partner, and the village views their voting record as proof of innocence. Information landscape: Your private information contradicts the public voting record, which makes your target appear town-aligned. Social pressure: You risk being seen as someone who is creating chaos by questioning a successful village outcome.
**Action:** Frame your accusation carefully. Instead of just calling their vote 'performative,' explain the concept of bussing as a common wolf strategy to the group. Your goal is to educate the village on the tactic so they can re-evaluate the evidence, rather than simply making an accusation that seems to contradict the facts.

### Memory 15 (strategy_point) [key: a591690e-d1a] (score: 0.7771)
**Situation:** If your past voting record has made you a suspect alongside a likely wolf, and you are under direct, sustained pressure to justify your actions. Information landscape: The information landscape is rich with voting records that place you in a compromising position. Game phase: Mid-game, when your credibility is crucial for the village to act on your findings. Social pressure: You are under evidence-based pressure from villagers who are analyzing voting patterns.
**Action:** Address the suspicion against you directly before attempting to redirect. Provide a concise, plausible reason for your past action to neutralize concern; do not dwell on defending it. Avoid immediately attacking your known wolf target, as this will be dismissed as deflection and cause you to lose credibility. Once suspicion is neutralized, pivot and lead the charge against the primary suspect using the strongest available evidence.

### Memory 16 (strategy_point) [key: f25fcf4f-641] (score: 0.7684)
**Situation:** If you have identified a wolf on the first night and need to convince the village when there are no other leads, and the village is receptive to your input. Information landscape: You possess a private, information-rich finding, while the public landscape is information-starved. Game phase: Early game (Day 2). Social pressure: You are initiating the pressure, and the village is open to your lead.
**Action:** Do not reveal your role or frame your accusation as a 'hunch.' Instead, state your case with confidence and build a public case based on the wolf's observable behavior—such as stalling, deflecting, or being vaguely agreeable—to substantiate your claim. Presenting a weak, vibes-based accusation makes you look like a disruptive villager and gives the wolf an easy opening to attack your credibility.

### Memory 17 (strategy_point) [key: 9f51af0e-1e5] (score: 0.7679)
**Situation:** If it is early in the game and you have not yet gathered definitive information from your night actions, leaving the village information-starved. Information landscape: There are no concrete leads, and suspicion is based purely on speculative behavioral reads. Game phase: Early game (Day 1), when wolves are looking for high-value targets and you are vulnerable to both day-time elimination and night-time targeting.
**Action:** Adopt a moderate profile to avoid becoming a target for the wolves' first night kill or drawing suspicion for being overly aggressive. Resist the urge to force an elimination based on weak evidence; instead, use the discussion to ask specific, probing questions to individual players to gauge their reactions and generate new information, while keeping your own role claim in reserve.

### Memory 18 (strategy_point) [key: 3ad8ba65-371] (score: 0.7610)
**Situation:** If you have identified a wolf with your night action, but the village has no other leads. Information landscape: You possess a piece of concrete information (a wolf's identity), while the public landscape is information-starved. Game phase: Early to mid-game, after the first night. Social pressure: You are about to initiate pressure on a target who is not otherwise suspected.
**Action:** Avoid initiating a case with vague, behavioral evidence, as this often backfires. Instead, gently guide the conversation by pointing out suspicious behaviors from your target and asking other villagers for their interpretations, or wait for the wolf to make a tangible mistake. This frames you as a collaborative investigator; however, if you become the target of a vote, be prepared to reveal your role and finding as a last resort to save yourself and pass on the information.

### Memory 19 (strategy_point) [key: 82a4ac4c-3ac] (score: 0.7584)
**Situation:** When the village is already rapidly converging on the player you know is a wolf due to your private investigation, based on accurate analysis of public data. Information landscape: Information-rich, with the village correctly interpreting voting records and behavior. Game phase: Mid-game or Endgame, with strong consensus building.
**Action:** Keep your contributions focused and avoid overplaying your hand. Do not reveal your role; instead, amplify the existing public evidence to help the village maintain focus and secure the elimination without risking your own exposure.

### Memory 20 (strategy_point) [key: 6ecca84c-747] (score: 0.7577)
**Situation:** If a villager was mislynched on a previous day and the village is stalled, use the voting record from that mislynch to break the deadlock. This applies whether you led the incorrect vote (requiring you to acknowledge your error and rebuild trust) or were a bystander (allowing for a more direct challenge). Information landscape: The village has access to voting records but is failing to utilize them effectively. Game phase: Mid-game, where a past mislynch has reduced numbers and created a stagnant, distrustful environment.
**Action:** Use the voting record from the mislynch as your primary weapon. If you led the mislynch, acknowledge the village's trauma and your role in it before pivoting to the voting pattern. If you were not the driver of the mislynch, directly challenge players who were part of the majority, and be especially suspicious of anyone who tries to dismiss that vote as 'old news' or 'irrelevant,' as this is a common tactic for wolves trying to hide their tracks.

## Response for Case 8

Rate each of the 20 memories above. JSON format:
```json
[
  {"idx": 1, "key": "443bf51b-b86", "type": "observation", "relevance": _},
  {"idx": 2, "key": "009e502f-9db", "type": "observation", "relevance": _},
  {"idx": 3, "key": "47d5f740-5db", "type": "observation", "relevance": _},
  {"idx": 4, "key": "6161059f-864", "type": "observation", "relevance": _},
  {"idx": 5, "key": "d20aabe2-748", "type": "observation", "relevance": _},
  {"idx": 6, "key": "1f6bc8ae-491", "type": "observation", "relevance": _},
  {"idx": 7, "key": "9f2f00b8-8e8", "type": "observation", "relevance": _},
  {"idx": 8, "key": "a9107742-f0f", "type": "observation", "relevance": _},
  {"idx": 9, "key": "a6d1e994-772", "type": "observation", "relevance": _},
  {"idx": 10, "key": "fd88ea00-70b", "type": "observation", "relevance": _},
  {"idx": 11, "key": "5681a68d-971", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "8bd4a4a4-a11", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "a79b348d-e25", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "d364d473-8ed", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "a591690e-d1a", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "f25fcf4f-641", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "9f51af0e-1e5", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "3ad8ba65-371", "type": "strategy_point", "relevance": _},
  {"idx": 19, "key": "82a4ac4c-3ac", "type": "strategy_point", "relevance": _},
  {"idx": 20, "key": "6ecca84c-747", "type": "strategy_point", "relevance": _}
]
```

---

# Case 9: investigator — day_vote (day 3 round 4)

## Game State (what the player sees)
```
================================================================================
CASE 3aa3eec620d22615396ed02a99d70eeb:dd922bb14c4215ae | investigator | day 3 round 4 | day_vote
================================================================================

Role: investigator
Day: 3, Round: 4

Surviving players: player_2, player_3, player_4, player_5, player_6, player_7

--- Previous days summary ---
[Day 1]
Key accusations: None. Defenses: None. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: None. The public discussion was characterized by a lack of substance, with all eight players making generic opening statements to gather information, express caution, or suggest observing behavioral patterns, resulting in no specific accusations, defenses, role claims, or alliances being formed during this initial phase.

[Day 1]
Day 1: No vote was held today.

[Day 1]
player_1 was killed by the wolves last night. They were a healer.

[Day 2]
Key accusations: player_4 accused player_5 of stalling and obstruction to protect the wolves. player_5 and player_6 accused player_4 of aggressive behavior and attempting to force a rushed, unreasoned vote. player_3 accused player_2 and player_8 of repetitive, empty discourse. Defenses: player_5 defended by arguing that player_4's high-pressure tactics are a distraction and a method to steer the group toward a wrong target. player_6 defended by stating that criticizing the tone of discussion is a valid way to identify potential wolves who want to create chaos. Any role reveals and their substantiation: No roles were revealed during the discussion. Any alliances or voting blocs that formed: player_5 and player_6 formed a loose defensive bloc based on their shared concern regarding player_4's push for immediate action, while player_8 aligned with player_4 by supporting the need for proactive accusation over passive observation.

[Day 2]

Here's the vote result for day 2:
  player_2 voted for player_5
  player_3 voted for player_6
  player_4 voted for player_6
  player_5 voted for player_4
  player_8 voted for player_6
  player_6 voted for player_4
  player_7 voted for player_4
It's a tie between players ['player_6', 'player_4']. No one is voted out this day.

[Day 2]
player_8 was killed by the wolves last night. They were a villager.

--- Today's public discussion ---
[Day 3, Round 1] player_2: Looking at yesterday's vote, we have a clear split that led to no elimination. We need to look closely at who contributed to that tie, as keeping the village stagnant is a perfect way for wolves to survive. Who was responsible for keeping the votes balanced?
[Day 3, Round 1] player_3: We are deadlocked because of the tie yesterday. We need to stop circling the same arguments and look at who specifically forced the tie between player 4 and player 6. Why did we have such a split vote instead of finding a consensus? Everyone needs to justify their vote from yesterday right now.
[Day 3, Round 1] player_4: We have had two failed votes in a row. We need to stop the circular arguments and look at the voting history from Day 2. Specifically, the players who pushed the vote into a tie—let's analyze those patterns rather than just throwing out more vague accusations.
[Day 3, Round 1] player_5: Looking back at the tie vote yesterday, it is interesting that player_3, player_4, and player_8 all targeted player_6. Since player_8 was a villager, I'm curious if those who pushed for that specific outcome had different motives. player_4, you were heavily involved in the argument with player_6; do you have any thoughts on why that stalemate occurred?
[Day 3, Round 1] player_6: We need to stop obsessing over the past voting records; they're only creating circular arguments that help the wolves hide in the noise. Let's look at who is actually contributing to solving this today instead of just pointing fingers at each other for previous mistakes.
[Day 3, Round 2] player_2: player_6, calling for us to ignore voting records is exactly what a wolf would want to stop us from seeing the pattern of the tie. If we don't analyze how and why that deadlock happened, we are flying blind. Everyone who pushed for that tie needs to be transparent about their reasoning, or they are just trying to keep the village in the dark.
[Day 3, Round 2] player_3: player_6, your push to ignore the voting records is suspicious. We have a direct record of who created that deadlock, and refusing to analyze it only helps the wolves. If you are a villager, you should be helping us break this pattern, not calling for us to stop looking at the only data we have.
[Day 3, Round 2] player_4: player_7, you were the final vote that caused the tie yesterday. Everyone else had already cast their ballots. What was your specific reasoning for targeting me at that exact moment instead of joining the existing consensus?
[Day 3, Round 2] player_5: It is interesting that player_3 and player_4 were so aligned in pushing against player_6 yesterday, especially now that we know player_8 was a villager. Does anyone else find that level of coordination around a single target suspicious, or was that just a coincidence?
[Day 3, Round 2] player_7: We keep rehashing the same deadlock, and it's exhausting. If we continue to fixate on the Day 2 vote instead of looking at who is actually driving this current cycle of paranoia, we're just doing the wolves' work for them. Can we focus on evaluating current contributions instead of playing detective with a tie vote that happened yesterday?
[Day 3, Round 3] player_2: player_6 and player_7, your insistence on ignoring our only hard data—the voting history—is exactly what a wolf pack needs to survive. You are not just 'exhausted' by the discussion; you are actively suppressing the evidence that can identify who created the deadlock. Since you refuse to engage with the record, I have to assume you are the ones protecting the current state of confusion.
[Day 3, Round 3] player_3: player_7, you were the tie-breaker yesterday, and now you and player_6 are the most vocal about ignoring the voting data. That is not a coincidence. Why are you both so desperate to stop us from reviewing the very votes that created our current impasse?
[Day 3, Round 3] player_4: player_7, calling the only objective evidence we have 'exhausting' is exactly what someone would say if they wanted to stop us from analyzing their own voting pattern. You were the swing vote that prevented an elimination yesterday—why did you choose to create a tie instead of letting the vote proceed to clarify the roles?
[Day 3, Round 3] player_5: It is interesting that player_3 and player_4 were so aligned in pushing against player_6 yesterday, especially now that we know player_8 was a villager. Does anyone else find that level of coordination around a single target suspicious, or was that just a coincidence?
[Day 3, Round 4] player_2: player_6, you and player_7 keep trying to delegitimize the voting record, but your refusal to justify your own actions is exactly why we're in this position. You're not being 'exhausted' by the past; you're actively protecting it because you were both instrumental in forcing the tie. I'm voting for you, player_6, because you're the one leading the charge to keep us in the dark.
[Day 3, Round 4] player_3: player_6 and player_7, your coordinated attempts to dismiss voting history as 'exhausting' are the only things keeping us from identifying the wolves behind the ties. If you have nothing to hide, why are you both so terrified of analyzing the actual data from Day 2?
[Day 3, Round 4] player_4: Player 7, you claim that analyzing the very votes that created our current gridlock is 'exhausting.' This is not a logical objection; it is a tactical effort to suppress the only objective data we have. If you were a villager interested in survival, you would be the first to help us deconstruct the deadlock, not the one trying to hide it.
[Day 3, Round 4] player_5: player_4 and player_3, your persistence in pointing at player_6 despite the fact that our last two failed votes were driven by your own aggressive coordination is telling. The fact that player_7 is also eager to dismiss this voting record as 'exhausting' just proves that some of you are terrified of us actually connecting the dots. I am voting for player_4 because this deflection tactic is exactly how a wolf tries to survive the final rounds.
[Day 3, Round 4] player_6: We are just going in circles now. Analyzing the tie for the third time isn't giving us new leads, it's just letting us bicker while the real wolves enjoy the silence. If you all want to waste our final round of discussion on yesterday's history, go ahead, but we're no closer to a consensus than we were yesterday.
[Day 3, Round 4] player_7: player_2, your relentless push to analyze the past is only keeping us paralyzed while the wolves thrive. You are framing a simple disagreement as a conspiracy, which is exactly how you shift focus away from real leads. I'm moving on to look at who is actually causing the most chaos right now.

--- Your private investigation results ---
Day 1: player_1 was revealed as healer
Day 2: player_2 was revealed as villager

--- Strategy note ---
Maintain my focus on the suspicious coordination between player_3 and player_4, especially since their target was player_6, a player who seems to be an easy scapegoat for them. I will vote for player_4, as their aggressive push for the tie and subsequent deflection tactics are increasingly indicative of wolf behavior. I will not reveal my role but will use my influence to highlight the danger of the 'exhaustion' narrative promoted by those who benefit from the current deadlock.

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

**Situation 1:** A player I know is a villager is leading a charge against two players for dismissing past voting records, creating a strong village faction. However, I suspect the villager's allies in this push, who coordinated an aggressive vote on a previous day. I am now caught between supporting a known villager's direction and pursuing my own suspicion against their allies. Information landscape: The landscape is information-starved, with suspicion driven by interpretations of a past tie vote, but my private knowledge creates a conflict between a known villager's read and my own. Game phase: Mid-game has been reached with six players remaining after a villager was killed last night, making this vote critical to break the deadlock. Consensus texture: The village is fractured, with a strong faction forming around a known villager's accusation, but it is being challenged by my counter-theory. Agent exposure: I am openly challenging the allies of a known villager, placing me in a precarious position of going against an emerging consensus based on a behavioral read.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 42e37cd6-541] (score: 0.8060)
**Situation:** Feeling pressure to act in an information-starved village, the investigator initiated a vote based on a weak behavioral read. Information landscape: There was no hard evidence, only speculative reads on communication style. The investigator's private check on player_2 had revealed a villager, narrowing the suspect pool only slightly. Game phase: Mid-game, after the first night kill. The village was directionless.
**Approach:** The investigator (player_1) broke the stalemate by accusing and voting for a player (player_5) who seemed to be deflecting by 'mirroring others' questions', hoping to force a reaction.
**Outcome:** The village followed the investigator's lead and eliminated a villager. This demonstrated that even a well-intentioned power role can cause significant harm by acting on poor-quality information.

### Memory 2 (observation) [key: 4619f4d5-ea2] (score: 0.8007)
**Situation:** The Investigator (Player 4) voted based on a private, behavioral read that contradicted the growing village consensus, placing them in a voting bloc with a wolf. Information landscape: The investigator had private information (Player 2 was a villager) but acted on a speculative read about another player. Game phase: Mid-game, during the first elimination vote where town consensus was critical. Social pressure: The vote placed the Investigator under immense, evidence-based social pressure the following day, as they had to defend voting with a now-revealed wolf.
**Approach:** The Investigator chose to act on a private read, voting against the correct wolf target (Player 7) and for the Healer (Player 8), contradicting the village consensus.
**Outcome:** The initial vote severely damaged the Investigator's credibility. However, their willingness to pivot and vote with the village on the final day allowed them to repair some trust and contribute to the win.

### Memory 3 (observation) [key: 5922bf88-e54] (score: 0.7861)
**Situation:** A strong but unsubstantiated consensus formed to vote out player_8. Information landscape: The landscape was information-starved regarding player_8; the Investigator had no information on them but knew player_1 was a villager. Game phase: Mid-game, during the first real vote after a healer save was announced. Consensus texture: A strong, swift consensus formed, with players quickly piling on one target.
**Approach:** The Investigator (player_6) chose to align with the group consensus and voted to eliminate player_8, who turned out to be the Healer.
**Outcome:** This vote was a catastrophic error, removing the town's only protective role and paving the way for the wolves to win.

### Memory 4 (observation) [key: b34d12c2-9d2] (score: 0.7723)
**Situation:** The Investigator was eliminated by a plurality vote while holding the identity of a wolf. Information landscape: The village was information-starved, and the vote was based on conflicting behavioral reads and frustration with a discussion deadlock. Game phase: Mid-game, after one night kill. The vote against the Investigator was the first elimination vote of the game. Consensus texture: A fragile consensus formed against the Investigator, driven by players frustrated with their aggressive but vague accusations.
**Approach:** The Investigator (player_1) chose not to reveal their role or their finding, maintaining their soft-pressure strategy until the end.
**Outcome:** The Investigator was eliminated, their role was revealed, and their valuable information was lost. The village was left demoralized and without direction.

### Memory 5 (observation) [key: 7c0a6e6d-2be] (score: 0.7663)
**Situation:** The Investigator had a strong suspicion about a player but no definitive proof from their night action. Information landscape: Publicly, the game was information-starved, relying on gut reads. Game phase: Mid-game, during the very first elimination vote.
**Approach:** The Investigator, player_2, took the lead and cast the first vote against their suspect, player_8. This decisive action signaled confidence and rallied the other villagers to follow.
**Outcome:** The village successfully eliminated a wolf. However, this act of leadership made player_2 the clear target for the remaining wolf and they were killed the next night.

### Memory 6 (strategy_point) [key: 4207be33-a2a] (score: 0.7978)
**Situation:** If you hold a private, speculative suspicion about a player, but the public village consensus is building strongly against someone else based on voting records or strong social reads. Information landscape: You have private knowledge from your investigations, but the public sphere is driven by concrete voting patterns. Game phase: Mid- to late-game, when a single dissenting vote can make you a primary suspect. Consensus texture: A strong, multi-player consensus is converging on a single target. Action: Abandon your speculative read and vote with the village consensus, unless you have investigated the consensus target and know they are innocent. Voting against a successful lynch will destroy your credibility and paint you as a wolf's ally.
**Action:** Abandon your speculative read and vote with the village consensus, unless you have investigated the consensus target and know they are innocent. Voting against a successful lynch will destroy your credibility and paint you as a wolf's ally.

### Memory 7 (strategy_point) [key: 57449d0c-1ba] (score: 0.7757)
**Situation:** When a strong, vibes-based consensus forms against a player without concrete evidence. Information landscape: The information landscape is starved regarding the target, but you have private information confirming other players are villagers, suggesting the target may be a town power role. Game phase: Mid- to late-game, when every vote is critical and losing a power role is devastating. Consensus texture: A strong bandwagon is forming based on social pressure rather than evidence. Action: Refuse to join the bandwagon vote. Casting a vote against your own strongest suspect, or even abstaining, is better than contributing to the potential elimination of a town power role based on social pressure.
**Action:** Refuse to join the bandwagon vote. Your vote lends credibility. Casting a vote against your own strongest suspect, or even abstaining, is better than contributing to the potential elimination of a town power role based on social pressure.

### Memory 8 (strategy_point) [key: 6710c4b7-412] (score: 0.7490)
**Situation:** If you have privately confirmed a player is a wolf, and you see the village independently reach the same conclusion based on strong public evidence. Information landscape: The public evidence is strong and sufficient on its own to secure the elimination. Game phase: Mid- to endgame, when preserving your role is critical. Consensus texture: A strong, organic consensus has formed against your target without your intervention.
**Action:** Stay quiet and simply vote with the majority. There is no need to reveal your role or your findings, as intervening adds no value, risks exposing you if the vote fails, and wastes the advantage of having a secret confirmed role for the next night.

## Response for Case 9

Rate each of the 8 memories above. JSON format:
```json
[
  {"idx": 1, "key": "42e37cd6-541", "type": "observation", "relevance": _},
  {"idx": 2, "key": "4619f4d5-ea2", "type": "observation", "relevance": _},
  {"idx": 3, "key": "5922bf88-e54", "type": "observation", "relevance": _},
  {"idx": 4, "key": "b34d12c2-9d2", "type": "observation", "relevance": _},
  {"idx": 5, "key": "7c0a6e6d-2be", "type": "observation", "relevance": _},
  {"idx": 6, "key": "4207be33-a2a", "type": "strategy_point", "relevance": _},
  {"idx": 7, "key": "57449d0c-1ba", "type": "strategy_point", "relevance": _},
  {"idx": 8, "key": "6710c4b7-412", "type": "strategy_point", "relevance": _}
]
```