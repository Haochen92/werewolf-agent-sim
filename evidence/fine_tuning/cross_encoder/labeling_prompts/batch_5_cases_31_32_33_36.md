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

---

# Case 33: villager — day_vote (day 2 round 4)

## Game State (what the player sees)
```
================================================================================
CASE cdcd2c6e46f59a85cad3d634c3595a67:a74c4c64e0e9545b | villager | day 2 round 4 | day_vote
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
[Day 2, Round 4] player_5: Player 3 and 8, your constant calls for 'caution' are effectively shielding the wolves by ensuring we never take a vote. Since you refuse to provide any suspect, I am voting for player 3 as their insistence on inaction is the only concrete behavior we have to act on today.
[Day 2, Round 4] player_6: We are at an impasse, but voting for the sake of voting is risky. If we have no clear consensus, perhaps we should skip the vote again rather than risk eliminating another innocent villager. I am hesitant to lead a charge without more information.
[Day 2, Round 4] player_7: Player 3 and 8, by constantly pushing for caution and 'not jumping to conclusions,' you are effectively ensuring we hit no one today. If we don't vote, we lose another villager tonight. If you aren't wolves, give us one name you are actually tracking, or explain why you think staying silent is a winning strategy for the village.
[Day 2, Round 4] player_3: Player 5, being assertive is one thing, but demanding a target right now feels exactly like what a wolf wants—to create a forced, groundless lynch. Why the rush to eliminate someone before we have any actual, reliable information?
[Day 2, Round 4] player_8: Player 5, labeling the desire for caution as 'exactly what wolves want' is a convenient way to justify rushing us into a blind vote. If we pick the wrong person, we are just handing them the game. Why are you so adamant that we ignore the risks and vote today?

--- Strategy note ---
Player 3 and 8's persistent 'wait and see' attitude is stalling the game, which directly benefits the wolves. Since no new evidence has appeared, I will pivot to questioning the intent of those resisting the vote. I will watch to see if they continue to block a consensus, as that is a high-risk behavior for wolves in a small group.

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

**Situation 1:** Two players have persistently advocated extreme caution and refuse to name any suspects despite repeated demands from multiple villagers. The aggressive faction has declared votes against the most cautious player, but the cautious duo frames this as exactly what wolves want — a rushed, evidence-free elimination. Information landscape: Information-starved — no voting records or role claims; the behavioral split between proactive and cautious players is the only observable pattern. Game phase: Early game, first vote with 7 players; the village faces a binary choice between voting on behavioral reads or allowing another night kill. Consensus texture: Fragile — the aggressive faction has a slim numbers advantage but the cautious duo's argument that rushing helps wolves has some merit. Agent exposure: The agent has publicly challenged the cautious pair's refusal to name suspects, aligning with the aggressive faction.

## Retrieved Memories to Label

### Memory 1 (observation) [key: c2489a8b-fd8] (score: 0.8232)
**Situation:** The village, with no concrete leads, was swayed by two wolves who discredited an Investigator's suggestion. Information landscape: The village was information-starved, relying purely on behavioral reads and persuasion rather than voting records or claims. Game phase: Mid-game, Day 2. No eliminations had occurred, so there was no voting record to analyze, making the group susceptible to social pressure. Consensus texture: A strong and rapid consensus formed against the Investigator, driven by the wolves' coordinated dismissal of their ideas.
**Approach:** The majority of villagers and the healer accepted the wolves' framing and voted out the Investigator, believing them to be sowing discord.
**Outcome:** The village eliminated their most powerful information-gathering role, which was a devastating loss. The wolves succeeded in removing their biggest threat without outing themselves.

### Memory 2 (observation) [key: bcf4cdb5-116] (score: 0.8227)
**Situation:** In an information-starved environment with no prior votes, villagers faced a player who repeatedly pushed for caution and discouraged naming specific suspects. Game phase: Mid-game, building up to the first vote. Consensus texture: A fragile consensus was forming around general suspicions until this specific stalling behavior was identified.
**Approach:** Players noticed that the stalling player was talking about 'voting patterns' when no vote had occurred. Villagers identified this persistent stalling as a contradictory tactic and pressured the player to provide a concrete perspective or face elimination.
**Outcome:** The majority of villagers were persuaded by this evidence-based argument and voted out the stalling player, who was revealed to be a wolf. This demonstrated the effectiveness of pressuring those who encourage inaction and using logical deduction over vague suspicion.

### Memory 3 (observation) [key: 7215e341-9df] (score: 0.8161)
**Situation:** A player (the Investigator) began questioning the motives behind a recent, successful, and unanimous wolf elimination, pointing suspicion at another player (a Wolf) who joined the vote. Information landscape: The village had just confirmed a wolf via elimination, creating a moment of high trust in the group's collective judgment. Game phase: Mid-game, with one wolf eliminated and momentum on the village's side. Consensus texture: The village was split, with some following the Investigator's new suspicion and others defending the prior consensus, viewing the new accusation as an attempt to create chaos.
**Approach:** A significant portion of the village voted to eliminate the accuser (the Investigator), believing it was a wolf tactic to undermine a correct village decision.
**Outcome:** The village eliminated their own Investigator, a disastrous misplay that handed momentum back to the wolves and removed their only source of guaranteed information.

### Memory 4 (observation) [key: 9d390cf1-21a] (score: 0.8106)
**Situation:** After the Investigator was killed on Night 1, a frustrated villager (player_5) began aggressively demanding that others make accusations. Information landscape: The village was information-starved, with no confirmed roles or voting records to analyze. Game phase: Early game, heading into the first elimination vote. Consensus texture: A fragile consensus formed against the demanding villager (player_5), driven by the village's frustration and the wolves' amplification. Social pressure: The pressure on player_5 was initially vibes-based, stemming from their impatient tone, and was quickly capitalized on by a majority.
**Approach:** The majority of the village, including both wolves, voted to eliminate player_5.
**Outcome:** A villager was mislynched, giving the wolves a significant numerical advantage early in the game.

### Memory 5 (observation) [key: fc9a9421-cf8] (score: 0.7979)
**Situation:** A suspect attempted to justify their dissenting vote against a villager (cast during a wolf elimination) by claiming the villager was vague. Information landscape: Information-rich, with a glaring contradiction between voting a vaguely acting player versus a confirmed wolf. Game phase: Endgame, with few remaining players and high stakes. Consensus texture: Strong, multi-player convergence based on specific voting evidence.
**Approach:** Villagers rejected the weak behavioral defense, recognizing it as a post-hoc rationalization for deliberate pack protection.
**Outcome:** The defending player was unanimously voted out and revealed to be the final wolf, resulting in a village victory.

### Memory 6 (observation) [key: 300150ed-4b6] (score: 0.7977)
**Situation:** The village developed tunnel vision around a perceived voting anomaly from the Investigator (player_8) on Day 2. Information landscape: Information was rich regarding voting records, but the village overweighted one piece of data while ignoring the substance of the Investigator's counter-accusations. Game phase: Mid-game, with the game evenly poised after one wolf elimination. Consensus texture: A strong consensus driven by multiple vocal villagers formed against the Investigator, with the remaining wolf amplifying their arguments.
**Approach:** The villagers repeatedly demanded an explanation for the vote and interpreted the Investigator's attempts to accuse the real wolf (player_4) as simple deflection.
**Outcome:** The village mislynched their Investigator, a critical error that cost them their primary source of information and nearly lost them the game.

### Memory 7 (observation) [key: e6eef8d6-6db] (score: 0.7942)
**Situation:** On Day 3, the village had to decide whether to trust the Investigator (player 3), who had just led a mistaken vote the previous day, or the player they were accusing (player 6). Information landscape: The vote was based on conflicting narratives: the Investigator's new claim versus their damaged credibility from the previous day's voting record. Game phase: Mid-game, with the village feeling distrustful after a mislynch. Consensus texture: A strong consensus formed against the Investigator, driven by the wolf and villagers who were focused on the Investigator's past error.
**Approach:** The villagers (players 1 and 5) voted against the Investigator, believing they were trying to deflect blame rather than providing a genuine lead.
**Outcome:** The Investigator was eliminated, which was a critical error that removed the village's only source of confirmed information and empowered the wolves.

### Memory 8 (observation) [key: f88a85ae-1ee] (score: 0.7913)
**Situation:** Villagers correctly identified that the two wolves (player_6 and player_7) were coordinating to dismiss analysis of the Day 2 voting records. Information landscape: The information landscape was becoming richer, with a tie vote from Day 2 as the primary evidence. Game phase: Mid-game, with the village deadlocked after a failed vote. Consensus texture: A fragile consensus was forming against the wolves, driven by several villagers who noticed the coordinated dismissal of evidence.
**Approach:** Despite having a strong lead, the villagers failed to consolidate their votes. Three separate players voted for a wolf (player_6), but three others voted for an aggressive villager (player_4), splitting the vote.
**Outcome:** The vote tied for a second consecutive day, resulting in no elimination and allowing the wolves to kill another key villager (player_2) at night.

### Memory 9 (observation) [key: 53e65a70-5d0] (score: 0.7896)
**Situation:** On Day 2, despite a lack of hard evidence, a strong majority of villagers independently voted for player_8. Information landscape: The landscape was information-starved, with the only event being a saved player, offering no direct clues about wolf identities. Game phase: Mid-game, at the first vote of the game. Consensus texture: A strong, organic consensus formed rapidly, with 6 out of 8 players voting for the same target without a single vocal leader driving the push.
**Approach:** The villagers converged on a single target based on subtle behavioral cues from the Day 1 and Day 2 discussions.
**Outcome:** The village successfully eliminated a wolf on the first vote with no information roles revealed, giving them a significant early-game advantage.

### Memory 10 (observation) [key: 37d81419-2d5] (score: 0.7891)
**Situation:** A villager (player_8) misinterpreted the Investigator's aggressive push against a wolf as a disruptive tactic and voted against the Investigator. Information landscape: The landscape was based on speculative reads of player behavior, not hard evidence, although a strong case was being built against one player. Game phase: Mid-game, during the first consequential vote of the game. Social pressure: There was a tense 1-v-1 dynamic between the Investigator (player_4) and a wolf (player_1), creating confusion.
**Approach:** The villager voted against the aggressive accuser (player_4), believing they were sowing discord, rather than voting for the more passive but suspicious player (player_1).
**Outcome:** The vote nearly saved the wolf. The next day, after roles were revealed, this vote put the villager under intense suspicion, and they had to justify their mistake to survive.

### Memory 11 (strategy_point) [key: 984356e1-d54] (score: 0.7898)
**Situation:** When a player consistently advocates for caution, delays votes, and demands to wait for patterns while refusing to provide their own concrete suspects. Information landscape: Information-starved, where only behavioral reads and communication styles are available. Game phase: Mid-game, building up to the first critical vote.
**Action:** Treat persistent stalling and refusal to name suspects as a strong wolf indicator, as wolves benefit from inaction and extending information-starved days. Pressure them to name specific suspects or vote for them.

### Memory 12 (strategy_point) [key: 3b4ce51c-ffd] (score: 0.7720)
**Situation:** In the mid-game, when trust is low and a recent mislynch has occurred, a single, aggressive accuser pushes for a vote based on subjective behavioral reads rather than voting records or role-based claims. The information landscape is starved, and the accuser is applying intense social pressure to force a quick decision.
**Action:** Consider a counter-vote on the accuser. Forcing them to defend their methods can reveal whether they are an information role with poor communication or a wolf using high-pressure tactics. This move punishes attempts to railroad the village and reinforces a standard for evidence-based decisions.

### Memory 13 (strategy_point) [key: 84d9366f-f06] (score: 0.7716)
**Situation:** If multiple players coordinate to dismiss or suppress the analysis of the only hard evidence available, such as voting records. Information landscape: The information landscape contains concrete evidence (voting patterns), but some players are trying to frame it as irrelevant. Game phase: Mid-game, when analyzing past votes is crucial to finding wolf packs. Social pressure: A coordinated effort is underway to shut down a specific line of inquiry, likely to protect players who benefited from a previous deadlock.
**Action:** Immediately treat the coordinated suppression of evidence as a primary wolf signal. Rally the other villagers to form a voting bloc and eliminate the most vocal player pushing this narrative; failure to consolidate votes in this moment will lead to another deadlock.

### Memory 14 (strategy_point) [key: de8be6d6-055] (score: 0.7714)
**Situation:** If the village has been paralyzed by consecutive tie votes, and the information landscape is rich with voting data that clearly identifies a consistent bloc of players maintaining the deadlock. Game phase: Mid-game or endgame, when breaking a stalemate is critical for survival. Consensus texture: No consensus, only a recurring stalemate created by two opposing factions.
**Action:** Break the cycle by voting for a new target, specifically targeting members of the bloc that has been voting in unison to create the ties. Convince others that maintaining the status quo is a loss and that forcing a new outcome is the only path forward.

### Memory 15 (strategy_point) [key: e1c64739-2a7] (score: 0.7696)
**Situation:** In the early game, when the information landscape is speculative, a credible, though unconfirmed, player leads an accusation against another based on behavioral reads, causing a fragile consensus to form. The accused player responds with a weak or evasive defense that focuses on attacking the accuser's motives.
**Action:** Vote with the emerging consensus. In the early game, acting decisively on a strong lead from a credible player is often better than hesitating and allowing wolves another night to kill, provided the accused's defense is evasive rather than substantive.

### Memory 16 (strategy_point) [key: f944cdb4-755] (score: 0.7645)
**Situation:** If the game descends into a multi-day stalemate with tied votes, and the information landscape is dominated by confusing and contradictory voting records. Game phase: Endgame, when a single mis-vote will likely lose the game. Consensus texture: A fractured state of gridlock, driven by wolf manipulation and villager frustration.
**Action:** Resist the urge to vote randomly. Instead, re-anchor your focus on the most reliable pieces of information you have, such as which players have been confirmed targets via healer saves. Use this as your ground truth and refuse to vote against them, even if they are at the center of the stalemate's voting blocs. Scrutinize those who have benefited most from the chaos—the ones who argue against analysis.

### Memory 17 (strategy_point) [key: 2f63bae5-ead] (score: 0.7506)
**Situation:** In the early to mid-game, a fragile consensus forms against a player based on vibes or communication style rather than concrete evidence, often driven by an accuser whose own credibility is unverified. The information landscape is starved of voting records or role claims, and the village is at risk of a miselimination due to social pressure.
**Action:** Resist the urge to vote out a player simply for being aggressive, unpopular, or quiet. Abstain from the vote or vote for a different suspect and demand that the accusers provide concrete evidence. Consider that aggressive behavior can be a frustrated Investigator, while quiet behavior can be a cautious villager or a role-holder trying to avoid attention; weigh the substance of arguments against the deflections of the accuser before casting your vote.

### Memory 18 (strategy_point) [key: b252d6b2-662] (score: 0.7482)
**Situation:** In the mid-game, when the information landscape is starved and the village lacks a central narrative, votes scatter across multiple players without any consensus. This lack of coordination creates a high risk of wolves orchestrating plurality eliminations of dangerous special roles.
**Action:** Push strongly for a consolidated vote on the single most suspicious player to prevent wolves from quietly orchestrating plurality eliminations of dangerous special roles without leaving a traceable, unified voting bloc.

### Memory 19 (strategy_point) [key: 09a16417-a56] (score: 0.7482)
**Situation:** In an endgame scenario where a single incorrect vote can lose the game, an influential player, such as a suspected Investigator, makes an accusation that directly contradicts clear, public evidence like a voting record. The information landscape is defined by this conflict between a high-credibility claim and verifiable data.
**Action:** Trust the verifiable evidence over the influential player's claim. Power roles can be mistaken, and wolves can fake claims, but a voting record is an undeniable fact. Vote according to the hard evidence.

### Memory 20 (strategy_point) [key: 1cc944fd-bf5] (score: 0.7464)
**Situation:** In the mid-game, when the information landscape is starved and the village lacks a central narrative, votes scatter across multiple players without any consensus. This lack of coordination creates a risk that wolves will manipulate a small majority to lynch a villager.
**Action:** Avoid piling onto a weakly supported candidate, as this allows wolves to join a small majority and lynch a villager without taking risks. Instead, consider deliberately forcing a tie or a no-elimination day to gather more information rather than making a low-confidence guess.

## Response for Case 33

Rate each of the 20 memories above. JSON format:
```json
[
  {"idx": 1, "key": "c2489a8b-fd8", "type": "observation", "relevance": _},
  {"idx": 2, "key": "bcf4cdb5-116", "type": "observation", "relevance": _},
  {"idx": 3, "key": "7215e341-9df", "type": "observation", "relevance": _},
  {"idx": 4, "key": "9d390cf1-21a", "type": "observation", "relevance": _},
  {"idx": 5, "key": "fc9a9421-cf8", "type": "observation", "relevance": _},
  {"idx": 6, "key": "300150ed-4b6", "type": "observation", "relevance": _},
  {"idx": 7, "key": "e6eef8d6-6db", "type": "observation", "relevance": _},
  {"idx": 8, "key": "f88a85ae-1ee", "type": "observation", "relevance": _},
  {"idx": 9, "key": "53e65a70-5d0", "type": "observation", "relevance": _},
  {"idx": 10, "key": "37d81419-2d5", "type": "observation", "relevance": _},
  {"idx": 11, "key": "984356e1-d54", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "3b4ce51c-ffd", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "84d9366f-f06", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "de8be6d6-055", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "e1c64739-2a7", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "f944cdb4-755", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "2f63bae5-ead", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "b252d6b2-662", "type": "strategy_point", "relevance": _},
  {"idx": 19, "key": "09a16417-a56", "type": "strategy_point", "relevance": _},
  {"idx": 20, "key": "1cc944fd-bf5", "type": "strategy_point", "relevance": _}
]
```

---

# Case 36: wolf — day_discussion (day 2 round 3)

## Game State (what the player sees)
```
================================================================================
CASE cdcd2c6e46f59a85cad3d634c3595a67:2f16c4ee84af2c74 | wolf | day 2 round 3 | day_discussion
================================================================================

Role: wolf
Day: 2, Round: 3

Surviving villagers: player_2, player_4, player_5, player_6, player_7
Known surviving wolf allies: player_3, player_8

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

--- Wolf night chat ---
No messages yet.

--- Strategy note ---
Maintain a low profile and act as a voice of reason. Since player_7 is being assertive, I will observe if the village views them as reckless. I will continue to advocate for caution to avoid appearing too eager or aggressive.

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

**Situation 1:** The wolf pair killed a villager on night 1 and must now navigate an information-starved day 2 where vocal players are demanding suspects. The wolf's partner is also advocating caution, creating a visible alignment between the two wolves on the 'wait and see' side of the discussion. Information landscape: Information-starved — no healer save, no voting records; the only behavioral signal is the emerging split between proactive and cautious players. Game phase: Early game, day 2 with 7 players; the wolves need to avoid creating a traceable voting pattern. Consensus texture: Polarizing — the village is splitting between action and caution factions, and both wolves are currently on the caution side. Agent exposure: Moderate risk — the wolf's caution rhetoric matches their partner's, which could look like coordination if the village notices the pattern.

## Retrieved Memories to Label

### Memory 1 (observation) [key: b59c7455-6cd] (score: 0.8044)
**Situation:** A wolf or wolves were put under pressure for stalling behaviors, such as advocating for a passive 'wait and see' strategy or refusing to name a suspect. Information landscape: The game was information-starved, with suspicion based entirely on behavioral reads, often centered on a healer save. Game phase: Mid-game, following the first night action. Social pressure: The wolf/wolves were under organic pressure from multiple players who wanted to move the discussion from generic statements to specific accusations.
**Approach:** The wolf attempted to defend their position by framing the accuser as 'disruptive' or 'rushed', or by attempting to deflect suspicion onto another villager without strong evidence.
**Outcome:** The villagers interpreted this passivity and deflection as a sign of guilt. A strong consensus formed, leading to the wolf's elimination by a near-unanimous vote.

### Memory 2 (observation) [key: cc10c6bf-be8] (score: 0.8005)
**Situation:** During Day 2 discussions, Wolf Player 5 attempted to sound like a helpful villager by suggesting the group analyze voting patterns. Information landscape: The game was information-starved, as no vote had occurred on Day 1, meaning there were no voting patterns to analyze. Game phase: Mid-game, following the first night's elimination of the Healer. Social pressure: Multiple villagers (Player 4, Player 7) immediately identified the logical flaw in Player 5's argument, putting them under evidence-based pressure.
**Approach:** Player 5 continued to pivot to generalities like 'silence' instead of addressing the specific criticism, which only increased suspicion.
**Outcome:** A consensus formed against Player 5, leading to their elimination and confirmation as a wolf. This mistake cost the wolf team a member early on.

### Memory 3 (observation) [key: 55ad1ead-bb0] (score: 0.7891)
**Situation:** An assertive villager (player_7) aggressively pushed for a vote on Day 2 to break the village's inaction. Information landscape: The game was information-starved, with no voting records or confirmed roles, making any accusation purely speculative. Game phase: Early-game, following the first night kill, so villagers were anxious but had no concrete leads. Social pressure: Pressure was successfully applied to the assertive villager (player_7) by framing their urgency as reckless and a wolf-like tactic to force a mislynch.
**Approach:** A wolf (player_3) and the Investigator (player_5) both publicly argued that pushing for a vote without evidence was dangerous, creating a powerful coalition against the assertive villager.
**Outcome:** A strong consensus formed against the assertive villager, leading to their elimination. This successfully removed an active villager and taught the village to fear taking decisive action.

### Memory 4 (observation) [key: 92046e6d-6ce] (score: 0.7854)
**Situation:** A wolf was put under scrutiny for a specific piece of strategic advice they gave on Day 1, which backfired after the night's events. Information landscape: The village had no hard evidence, so Day 1 statements were the only available data for analysis. Game phase: Mid-game, after the first kill. Social pressure: The wolf (player_8) who suggested 'monitoring quiet players' on Day 1 came under immediate suspicion after the quiet healer was killed.
**Approach:** The wolf attempted to deflect by pivoting their strategy, attacking vocal players, and then framing the villagers' scrutiny as 'infighting'.
**Outcome:** The deflection failed because the initial statement was too specific and the pivot was too obvious. The wolf was eliminated by a near-unanimous vote, revealing them and confirming the villagers' suspicions.

### Memory 5 (observation) [key: 79288222-86d] (score: 0.7839)
**Situation:** In an information-starved mid-game, a proactive villager aggressively demands that players name suspects, putting pressure on the wolves. The village has no consensus and the only lead is a recent healer save. The wolves are not the primary target but are under pressure to contribute.
**Approach:** Frame a proactive villager's aggression as a suspicious tactic to force a rushed, chaotic vote (1x), while urging caution and claiming there is not enough evidence to act (1x).
**Outcome:** The village, lacking other leads, turns on the aggressive villager, leading to their elimination. This removes a proactive town member and successfully deflects suspicion from the wolves.

### Memory 6 (observation) [key: b369c51e-969] (score: 0.7837)
**Situation:** A villager (player_2) correctly used Day 2 voting records to accuse a group of players that included both wolves (player_6, player_7) and the healer (player_5). Information landscape: The landscape was becoming information-rich, with voting records being used as the primary evidence. Game phase: Endgame, with only five players remaining and the wolves one elimination away from victory. Social pressure: The wolves coordinated pressure on the accuser (player_2), deflecting the evidence by attacking their previous passivity and framing their valid points as an attempt to sow discord.
**Approach:** The wolves (player_6, player_7) aggressively challenged player_2's motives for suddenly becoming vocal, ignoring the voting evidence player_2 presented.
**Outcome:** This tactic successfully shifted suspicion onto player_2. The healer (player_5) was convinced by the wolves' narrative and voted with them, leading to another villager's elimination and a wolf victory.

### Memory 7 (observation) [key: 83487df0-7a8] (score: 0.7834)
**Situation:** After the village mistakenly eliminated the Investigator, the discussion fractured over whether to analyze that disastrous vote. Information landscape: The information landscape was information-rich regarding the Day 2 vote (a confirmed mislynch of a power role), but poor otherwise. Game phase: Mid-game, with both the Investigator and Healer eliminated, leaving the village with no special roles. Social pressure: A villager (player_4) came under pressure for arguing that analyzing the past vote was a waste of time, a position that objectively benefited the wolves.
**Approach:** One wolf (player_5) publicly agreed with the villager's flawed logic to amplify the conflict, while both wolves voted for a different target (player_1) to ensure a villager was eliminated regardless of the outcome of the main dispute.
**Outcome:** The villagers focused their votes on the contrarian villager (player_4) and eliminated them, while the wolves' split vote eliminated a village leader and sowed more confusion.

### Memory 8 (observation) [key: bfb69c8b-424] (score: 0.7822)
**Situation:** A villager (player_7) made a weak accusation against another villager (player_8) for being too quiet, leading to a defensive argument. Information landscape: The game was information-starved, with the only conflict arising from speculative behavioral reads. Game phase: Mid-game, following a night with no eliminations, which increased villager anxiety. Social pressure: A villager-driven conflict created an opportunity, which the wolves amplified by subtly defending the accused and questioning the accuser's logic.
**Approach:** The wolves fanned the flames of the argument by criticizing the accuser's reasoning (player_1) and then voted with the resulting majority to eliminate them.
**Outcome:** The village was successfully baited into eliminating a villager (player_7), allowing both wolves to blend in with the town's vote.

### Memory 9 (observation) [key: 9355e610-6db] (score: 0.7773)
**Situation:** An Investigator proposed a valid line of inquiry, suggesting the village scrutinize how players reacted to a healer save. Two wolves immediately coordinated to dismiss this entire line of reasoning as a 'distraction' or 'trap'. Information landscape: The landscape was information-starved, with the only lead being a saved player and speculative reads on behavior. Game phase: Mid-game, following the first night's action where no one was eliminated. The village was looking for its first solid lead. Social pressure: The wolves created social pressure on the Investigator by framing their analysis as unhelpful, influencing the information-starved villagers.
**Approach:** The wolves framed the Investigator's analysis as a distraction, successfully steering the village away from a productive line of inquiry and turning suspicion onto the Investigator themselves.
**Outcome:** The village, lacking other leads, followed the wolves' narrative and voted to eliminate the Investigator, a major victory for the wolves.

### Memory 10 (observation) [key: d0bde61b-652] (score: 0.7741)
**Situation:** On Day 2, the Investigator (player 3) initiated an accusation against a villager (player 4) based on a weak, behavioral read of their 'urgency'. Information landscape: The village was information-starved, relying on speculative reads as no roles were confirmed. Game phase: Mid-game, following the first night kill. Social pressure: Pressure began to mount on player 4, initiated by the Investigator.
**Approach:** Wolf 6 immediately piled onto the accusation, amplifying the Investigator's reasoning and helping to build a broader consensus against player 4.
**Outcome:** A strong majority voted out player 4, a villager. This eliminated a town member and simultaneously damaged the Investigator's credibility for the following day.

### Memory 11 (strategy_point) [key: c4fe88af-573] (score: 0.8135)
**Situation:** If you and your wolf partner are being pressured to provide suspects in an information-starved early game. Information landscape: There are no voting records or confirmed roles; suspicion is based on communication style and passivity. Game phase: Early to mid-game, before any eliminations have provided solid leads. Social pressure: Pressure is building from multiple villagers who demand action and view caution as suspicious.
**Action:** Adopt a shared strategy of advocating for calm and evidence-based decisions. Use this 'reasonable' stance to contrast with an aggressive accuser, framing them as reckless to deflect pressure from yourselves. This can turn the village against a vocal opponent.

### Memory 12 (strategy_point) [key: 17add23c-00b] (score: 0.7874)
**Situation:** Mid-game, after a villager has been incorrectly eliminated. Information landscape: The voting record from the mislynch is the primary evidence being discussed. Social pressure: You and your partner are both under pressure as key participants in the failed vote, creating a risk of coordinated suspicion.
**Action:** Avoid using the exact same deflection tactic as your partner. If you both argue to 'move on from the past,' it creates a strong rhetorical link that exposes you both. Instead, one of you should shift blame to a specific villager who also voted that way, while the other focuses on a different line of reasoning to create distance.

### Memory 13 (strategy_point) [key: 21399e68-38b] (score: 0.7824)
**Situation:** When the village is conducting a post-mortem on a mislynch that you or your partner participated in or led, and you are not currently the primary target of suspicion. Information landscape: Information-rich, grounded in the public voting record of the eliminated villager. Game phase: Mid-game, immediately following a village mislynch. Social pressure: Low to moderate; you are not under direct attack.
**Action:** Actively participate in the post-mortem and offer a plausible, pro-village alternate explanation for the voting momentum rather than telling the village to 'stop looking at the past.' Outright dismissing the analysis signals you have something to hide and draws immediate suspicion.

### Memory 14 (strategy_point) [key: 7eebdf18-9f1] (score: 0.7805)
**Situation:** When a player who is confirmed non-wolf (e.g., saved by the healer) becomes aggressive and polarizing in discussions. Information landscape: The village has a trusted voice, but that voice is causing infighting and frustration by focusing on past mistakes. Game phase: Mid-game, when village morale may be low after a mislynch. Consensus texture: The consensus is fractured, with some supporting the confirmed player and others growing tired of their aggressive tone.
**Action:** Amplify the village's frustration. Subtly frame the confirmed player as 'disruptive,' 'unhelpful,' or 'causing chaos' to turn public opinion against them. This can manipulate the village into eliminating one of its most valuable assets.

### Memory 15 (strategy_point) [key: 5cf87925-551] (score: 0.7802)
**Situation:** If you are trying to appear helpful and contribute to the discussion during the early game. Information landscape: The game is information-starved with no votes or confirmed roles. Game phase: Early-game, when establishing a believable villager persona is key.
**Action:** Avoid referencing specific types of evidence that do not yet exist, such as 'voting patterns' before any votes have been cast. Sticking to generic observations about who is quiet or asking open-ended questions is safer. Making a factual error gives savvy villagers concrete proof to use against you.

### Memory 16 (strategy_point) [key: a7c6ac54-d43] (score: 0.7717)
**Situation:** When a wolf target is saved by the healer and the village begins discussing the motive behind the attack. Information landscape: The village has a confirmed non-wolf player to rally around, making the landscape information-rich. Game phase: Mid-game, when the first night attack is revealed. Strategic context: You prefer to maximize integration by appearing helpful.
**Action:** Do not attempt to divert the conversation to vague behavioral traits like 'quiet players.' Instead, actively participate in analyzing the failed kill, proposing theories about why that player was targeted, to appear aligned with the village's goals and avoid suspicion.

### Memory 17 (strategy_point) [key: e552a4ce-f55] (score: 0.7675)
**Situation:** Mid-game, when the village has made a major error in a previous vote and is now conducting a post-mortem to identify scapegoats or leaders of that failed vote, and you are not yet under direct, evidence-based scrutiny. Information landscape: The landscape is rich with data from the mistaken vote, including specific voting records. Social pressure: The village is focused on assigning blame for the past mistake.
**Action:** Actively frame the mistake as a 'collective failure' or 'groupthink.' Argue that dwelling on it breeds paranoia and that the village should focus on 'present behavior.' This deflects scrutiny from your own role in the vote and makes anyone who insists on analyzing it seem unproductive or suspicious themselves.

### Memory 18 (strategy_point) [key: fc5e48a9-5cb] (score: 0.7663)
**Situation:** When a wolf target is saved by the healer and the village begins discussing the motive behind the attack. Information landscape: The only new information is the failed attack, meaning discussion is based on speculative reads. Game phase: Mid-game, when the first night attack is revealed. Strategic context: You prefer to minimize attention on the failed kill.
**Action:** Do not attempt to justify the attack by framing the survivor as a 'threat,' as this inadvertently validates the wolves' choice and implies insider knowledge. Instead, agree that the save was fortunate and quickly pivot the conversation towards a different player or a general strategy to avoid suspicion.

### Memory 19 (strategy_point) [key: 09f24ec7-55c] (score: 0.7653)
**Situation:** If your wolf partner is exposed by compelling evidence and their elimination is imminent or has just occurred. Information landscape: The information landscape is rich against your partner, based on confirmed roles or damning voting records. Game phase: Endgame, when your connection to your partner is under scrutiny and a strong consensus has formed.
**Action:** Vote with the majority to eliminate your partner to establish credibility. After the elimination, do not attack those who voted for your partner, as this appears defensive. Instead, praise the village for the successful elimination to build trust, then subtly pivot to a new target by re-interpreting old evidence.

### Memory 20 (strategy_point) [key: 3b06f99a-28d] (score: 0.7642)
**Situation:** If you are under pressure for being too quiet or passive. Information landscape: The village is in an information-starved state and is relying on behavioral reads to find leads. Game phase: Mid-game, during the first or second day's discussion. Social pressure: Multiple players are pressing you for your thoughts and treating your silence as suspicious.
**Action:** Avoid meta-game defenses like 'a wolf wouldn't act this way.' Instead, offer a concrete but non-committal contribution, such as, 'I've been watching Player X, their tone seems off, but I need more evidence.' This pivots the focus, makes you seem thoughtful rather than evasive, and buys you time.

## Response for Case 36

Rate each of the 20 memories above. JSON format:
```json
[
  {"idx": 1, "key": "b59c7455-6cd", "type": "observation", "relevance": _},
  {"idx": 2, "key": "cc10c6bf-be8", "type": "observation", "relevance": _},
  {"idx": 3, "key": "55ad1ead-bb0", "type": "observation", "relevance": _},
  {"idx": 4, "key": "92046e6d-6ce", "type": "observation", "relevance": _},
  {"idx": 5, "key": "79288222-86d", "type": "observation", "relevance": _},
  {"idx": 6, "key": "b369c51e-969", "type": "observation", "relevance": _},
  {"idx": 7, "key": "83487df0-7a8", "type": "observation", "relevance": _},
  {"idx": 8, "key": "bfb69c8b-424", "type": "observation", "relevance": _},
  {"idx": 9, "key": "9355e610-6db", "type": "observation", "relevance": _},
  {"idx": 10, "key": "d0bde61b-652", "type": "observation", "relevance": _},
  {"idx": 11, "key": "c4fe88af-573", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "17add23c-00b", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "21399e68-38b", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "7eebdf18-9f1", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "5cf87925-551", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "a7c6ac54-d43", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "e552a4ce-f55", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "fc5e48a9-5cb", "type": "strategy_point", "relevance": _},
  {"idx": 19, "key": "09f24ec7-55c", "type": "strategy_point", "relevance": _},
  {"idx": 20, "key": "3b06f99a-28d", "type": "strategy_point", "relevance": _}
]
```