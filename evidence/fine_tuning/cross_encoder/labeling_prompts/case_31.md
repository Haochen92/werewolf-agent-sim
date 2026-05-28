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

# Case 31: investigator — day_vote (day 3 round 4)

## Game State (what the player sees)
```
================================================================================
CASE cdcd2c6e46f59a85cad3d634c3595a67:c6e919431c6e84b0 | investigator | day 3 round 4 | day_vote
================================================================================

Role: investigator
Day: 3, Round: 4

Surviving players: player_2, player_4, player_6, player_3, player_8

--- Previous days summary ---
[Day 1]
Key accusations: None. Defenses: None. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: None. The Day 1 discussion remained neutral and cautious, with all players (player_1 through player_8) exchanging general pleasantries, emphasizing the need for caution, and expressing a shared reluctance to jump to conclusions or force a quick lynch without evidence.

[Day 1]
Day 1: No vote was held today.

[Day 1]
player_1 was killed by the wolves last night. They were a villager.

[Day 2]
Key accusations: player_5 accused player_3 of shielding wolves by pushing for inaction and refusing to identify suspects; player_7 accused both player_3 and player_8 of similar passive behavior that prevents the village from making necessary moves. Defenses: player_3 defended by arguing that player_5's push for a forced lynch is a tactic used by wolves to create blind, groundless eliminations; player_8 defended by labeling player_5's urgency as a manipulative strategy designed to rush the group into a risky and potentially fatal mistake. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: player_3 and player_8 formed a tactical alignment based on a shared philosophy of extreme caution and avoiding premature voting to prevent the accidental elimination of a villager.

[Day 2]

Here's the vote result for day 2:
  player_2 voted for player_5
  player_4 voted for player_5
  player_5 voted for player_3
  player_6 voted for player_5
  player_7 voted for player_3
  player_3 voted for player_5
  player_8 voted for player_5
Player player_5 has been voted out and was a villager.


[Day 2]
player_7 was killed by the wolves last night. They were a villager.

--- Today's public discussion ---
[Day 3, Round 1] player_2: It is concerning we have lost two more villagers. We really need to look at the voting records from yesterday. Who pushed the hardest for the player_5 vote, and does that align with who is trying to lead the conversation now?
[Day 3, Round 1] player_4: We've lost two villagers in two nights. Since everyone voted for player 5, that's not a reliable way to clear anyone. I'm looking at who seems most eager to push a narrative today. Player 3 and 8, you two have been linked in your approach—are you both still confident in each other?
[Day 3, Round 1] player_6: We lost another villager last night, which is tough. Looking at the voting history, player_3 and player_8 were both pushing hard for inaction yesterday, which feels like it might have been an attempt to protect player_5 before the bandwagon took off. What do you two think about that?
[Day 3, Round 1] player_3: It is a quiet start to the day. We have lost two more people, and we are down to just four of us. We need to be careful with who we suspect now, as one wrong move means the wolves win. Does anyone have any actual leads on who might be working together?
[Day 3, Round 1] player_8: We have very few players left, and we need to be incredibly careful with our next vote. Looking back at yesterday's outcome, it is clear that being too quick to push for a lynch led us to eliminate another villager. I think it is important we re-evaluate why we were so convinced by that momentum before we commit to another target today.
[Day 3, Round 2] player_2: Player 3 and 8, you keep emphasizing caution, but your tactical alignment during the vote for player 5 is what stands out. If you are both villagers, how do you explain the push for inaction that left us vulnerable? We need a clear answer, not just a reminder to be careful.
[Day 3, Round 2] player_4: Player 3 and 8, you two defended each other yesterday to stall the vote. Since player 5 turned out to be a villager, it's clear the bandwagon was a distraction. Why are you both still using the exact same 'be careful' rhetoric today? It feels like you're trying to keep the focus away from yourselves while we dwindle down.
[Day 3, Round 2] player_6: Player 3 and 8, you keep mentioning caution, but at this stage, caution is indistinguishable from stalling. If you're both villagers, why aren't you pointing fingers at anyone? Silence is exactly what the wolves want right now.
[Day 3, Round 2] player_8: Player 2 and 6, you are both pointing fingers at us for caution, but your own rush to point blame feels like a coordinated distraction. We were all lost yesterday, and pinning it on us just because we wanted to be sure is exactly how the wolves want us to operate. Let's look at who stands to gain from this infighting.
[Day 3, Round 3] player_2: Player 3 and 8, you keep talking about 'cautious' voting, but caution at this stage is indistinguishable from stalling. If you were truly just being careful, you would be helping us analyze the remaining players, not just defending your own inaction. Give us a specific reason to trust you, or I'm ready to vote for the one of you who seems the most evasive.
[Day 3, Round 3] player_4: Player 8, calling our scrutiny 'coordinated' is a classic deflection. If you were a villager, you'd be trying to narrow down the wolves instead of just attacking the people questioning your previous stalling. Give us a name and a reason, or stop pretending your caution is for the village's benefit.
[Day 3, Round 3] player_6: Player_3, your attempt to frame our concern as 'wolf-like infighting' is just another layer of misdirection. If you and player_8 were truly interested in winning, you'd be helping us narrow down the pool instead of questioning why we're looking at you. I'm voting for player_3.
[Day 3, Round 3] player_3: It is interesting how you three are so perfectly aligned in your questioning today. If you're all villagers, why does your suspicion feel like a pre-planned script rather than organic investigation? By focusing only on me and player 8, you're effectively ignoring every other possibility, which is exactly how you steer a vote to an easy target.
[Day 3, Round 3] player_8: It is interesting that both of you are pushing the exact same narrative at the exact same time. If you were truly villagers looking for wolves, you would be exploring different angles rather than just repeating that my caution is suspicious. This level of coordination makes me wonder if the real threat is the alliance forming between the two of you.
[Day 3, Round 4] player_2: Player 3, claiming that our shared suspicion is 'pre-planned' is just another deflection. If you were a villager, you would address the specific issue of why you stalled on Day 2 instead of trying to paint every other player as a conspirator. I have seen enough; my vote is going to you.
[Day 3, Round 4] player_4: Player 3 and 8, you're still deflecting. You haven't named a single person you find suspicious, only attacked us for questioning you. If you're town, you should be hunting wolves, not just defending your own inaction. Who is your suspect, and why?
[Day 3, Round 4] player_6: Player 3, your claim that we are following a 'script' is just a mirror of your own defensive tactics. We aren't a scripted group; we are just villagers noticing that you and player 8 have been moving in lockstep since Day 1, always advocating for inaction while the rest of us lose numbers. If we are being manipulated, it's by those who benefit from keeping this game at a standstill. I'm sticking with my vote for player 3.
[Day 3, Round 4] player_3: Player 2, 4, and 6, you are all echoing the exact same points about my caution, which really makes me wonder who is actually leading this group. If we are down to just four, and you are all acting as a single unit, why should I trust that this isn't a team of wolves trying to isolate me and player 8? We have been down this road before with a 'coordinated' push that killed a villager, and I refuse to be the next victim of that same trap.
[Day 3, Round 4] player_8: We have reached a critical point, and accusing each other of being a 'team' is exactly how we lose. If you really believe player 3 and I are a duo, you are ignoring the obvious coordination happening between the two of you right now. I'm voting for player 2.

--- Your private investigation results ---
Day 1: player_1 was revealed as villager
Day 2: player_2 was revealed as healer

--- Strategy note ---
Since player_2 (the healer) is under scrutiny, I must protect them by redirecting the focus back to the inconsistent behavior of player_3 and player_8. I will use the final moments to emphasize that their tactical stalling is the only consistent pattern in this game, framing it as a threat to the village's survival. My goal is to ensure a vote against one of them without revealing my role.

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

**Situation 1:** The investigator has secretly identified the healer through night investigation and must protect them from being eliminated by a village faction that is pressing all cautious players. Three players have formed a bloc targeting one of two cautious players, and the cautious duo is accusing the bloc of being wolves. Information landscape: The investigator knows the healer's identity privately, while publicly the village relies on the Day 2 mislynch voting record and behavioral reads. Game phase: Endgame-adjacent, 5 players remaining after a mislynch and an overnight kill; one wrong elimination likely ends the game. Consensus texture: Entrenched — a three-player bloc vs a two-player defensive pair, with mutual accusations of coordination. Agent exposure: The investigator is part of the three-player bloc and is committed to protecting the healer without revealing either role.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 4619f4d5-ea2] (score: 0.7902)
**Situation:** The Investigator (Player 4) voted based on a private, behavioral read that contradicted the growing village consensus, placing them in a voting bloc with a wolf. Information landscape: The investigator had private information (Player 2 was a villager) but acted on a speculative read about another player. Game phase: Mid-game, during the first elimination vote where town consensus was critical. Social pressure: The vote placed the Investigator under immense, evidence-based social pressure the following day, as they had to defend voting with a now-revealed wolf.
**Approach:** The Investigator chose to act on a private read, voting against the correct wolf target (Player 7) and for the Healer (Player 8), contradicting the village consensus.
**Outcome:** The initial vote severely damaged the Investigator's credibility. However, their willingness to pivot and vote with the village on the final day allowed them to repair some trust and contribute to the win.

### Memory 2 (observation) [key: b34d12c2-9d2] (score: 0.7748)
**Situation:** The Investigator was eliminated by a plurality vote while holding the identity of a wolf. Information landscape: The village was information-starved, and the vote was based on conflicting behavioral reads and frustration with a discussion deadlock. Game phase: Mid-game, after one night kill. The vote against the Investigator was the first elimination vote of the game. Consensus texture: A fragile consensus formed against the Investigator, driven by players frustrated with their aggressive but vague accusations.
**Approach:** The Investigator (player_1) chose not to reveal their role or their finding, maintaining their soft-pressure strategy until the end.
**Outcome:** The Investigator was eliminated, their role was revealed, and their valuable information was lost. The village was left demoralized and without direction.

### Memory 3 (observation) [key: 42e37cd6-541] (score: 0.7620)
**Situation:** Feeling pressure to act in an information-starved village, the investigator initiated a vote based on a weak behavioral read. Information landscape: There was no hard evidence, only speculative reads on communication style. The investigator's private check on player_2 had revealed a villager, narrowing the suspect pool only slightly. Game phase: Mid-game, after the first night kill. The village was directionless.
**Approach:** The investigator (player_1) broke the stalemate by accusing and voting for a player (player_5) who seemed to be deflecting by 'mirroring others' questions', hoping to force a reaction.
**Outcome:** The village followed the investigator's lead and eliminated a villager. This demonstrated that even a well-intentioned power role can cause significant harm by acting on poor-quality information.

### Memory 4 (observation) [key: 5922bf88-e54] (score: 0.7583)
**Situation:** A strong but unsubstantiated consensus formed to vote out player_8. Information landscape: The landscape was information-starved regarding player_8; the Investigator had no information on them but knew player_1 was a villager. Game phase: Mid-game, during the first real vote after a healer save was announced. Consensus texture: A strong, swift consensus formed, with players quickly piling on one target.
**Approach:** The Investigator (player_6) chose to align with the group consensus and voted to eliminate player_8, who turned out to be the Healer.
**Outcome:** This vote was a catastrophic error, removing the town's only protective role and paving the way for the wolves to win.

### Memory 5 (observation) [key: 7c0a6e6d-2be] (score: 0.7535)
**Situation:** The Investigator had a strong suspicion about a player but no definitive proof from their night action. Information landscape: Publicly, the game was information-starved, relying on gut reads. Game phase: Mid-game, during the very first elimination vote.
**Approach:** The Investigator, player_2, took the lead and cast the first vote against their suspect, player_8. This decisive action signaled confidence and rallied the other villagers to follow.
**Outcome:** The village successfully eliminated a wolf. However, this act of leadership made player_2 the clear target for the remaining wolf and they were killed the next night.

### Memory 6 (strategy_point) [key: 4207be33-a2a] (score: 0.7456)
**Situation:** If you hold a private, speculative suspicion about a player, but the public village consensus is building strongly against someone else based on voting records or strong social reads. Information landscape: You have private knowledge from your investigations, but the public sphere is driven by concrete voting patterns. Game phase: Mid- to late-game, when a single dissenting vote can make you a primary suspect. Consensus texture: A strong, multi-player consensus is converging on a single target. Action: Abandon your speculative read and vote with the village consensus, unless you have investigated the consensus target and know they are innocent. Voting against a successful lynch will destroy your credibility and paint you as a wolf's ally.
**Action:** Abandon your speculative read and vote with the village consensus, unless you have investigated the consensus target and know they are innocent. Voting against a successful lynch will destroy your credibility and paint you as a wolf's ally.

### Memory 7 (strategy_point) [key: 6710c4b7-412] (score: 0.7380)
**Situation:** If you have privately confirmed a player is a wolf, and you see the village independently reach the same conclusion based on strong public evidence. Information landscape: The public evidence is strong and sufficient on its own to secure the elimination. Game phase: Mid- to endgame, when preserving your role is critical. Consensus texture: A strong, organic consensus has formed against your target without your intervention.
**Action:** Stay quiet and simply vote with the majority. There is no need to reveal your role or your findings, as intervening adds no value, risks exposing you if the vote fails, and wastes the advantage of having a secret confirmed role for the next night.

### Memory 8 (strategy_point) [key: 57449d0c-1ba] (score: 0.7377)
**Situation:** When a strong, vibes-based consensus forms against a player without concrete evidence. Information landscape: The information landscape is starved regarding the target, but you have private information confirming other players are villagers, suggesting the target may be a town power role. Game phase: Mid- to late-game, when every vote is critical and losing a power role is devastating. Consensus texture: A strong bandwagon is forming based on social pressure rather than evidence. Action: Refuse to join the bandwagon vote. Casting a vote against your own strongest suspect, or even abstaining, is better than contributing to the potential elimination of a town power role based on social pressure.
**Action:** Refuse to join the bandwagon vote. Your vote lends credibility. Casting a vote against your own strongest suspect, or even abstaining, is better than contributing to the potential elimination of a town power role based on social pressure.

## Response for Case 31

Rate each of the 8 memories above. JSON format:
```json
[
  {"idx": 1, "key": "4619f4d5-ea2", "type": "observation", "relevance": _},
  {"idx": 2, "key": "b34d12c2-9d2", "type": "observation", "relevance": _},
  {"idx": 3, "key": "42e37cd6-541", "type": "observation", "relevance": _},
  {"idx": 4, "key": "5922bf88-e54", "type": "observation", "relevance": _},
  {"idx": 5, "key": "7c0a6e6d-2be", "type": "observation", "relevance": _},
  {"idx": 6, "key": "4207be33-a2a", "type": "strategy_point", "relevance": _},
  {"idx": 7, "key": "6710c4b7-412", "type": "strategy_point", "relevance": _},
  {"idx": 8, "key": "57449d0c-1ba", "type": "strategy_point", "relevance": _}
]
```