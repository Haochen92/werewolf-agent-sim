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