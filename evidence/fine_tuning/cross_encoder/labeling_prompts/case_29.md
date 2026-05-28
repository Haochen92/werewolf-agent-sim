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

# Case 29: investigator — day_vote (day 2 round 4)

## Game State (what the player sees)
```
================================================================================
CASE cdcd2c6e46f59a85cad3d634c3595a67:8a06a0efa7b00373 | investigator | day 2 round 4 | day_vote
================================================================================

Role: investigator
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

--- Your private investigation results ---
Day 1: player_1 was revealed as villager

--- Strategy note ---
Maintain a neutral but observant profile while waiting for the next investigation result to act. Avoid pushing for a vote today to prevent drawing unnecessary attention while my information is still limited. I will continue to monitor who is being overly cautious, as that might indicate an attempt to avoid scrutiny.

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

**Situation 1:** The village is split between players demanding action and a cautious duo blocking any vote. The investigator has only confirmed a now-dead player as villager and has no wolf leads. The aggressive faction is targeting the most cautious player for their insistence on inaction. Information landscape: Publicly information-starved; the investigator's private knowledge is useless (confirmed a dead villager). All suspicion is behavioral. Game phase: Early game, first vote with 7 players; the investigator must decide whether the cautious players or aggressive players are more suspicious, and use their next investigation wisely. Consensus texture: Split between action and caution factions, with the action faction beginning to coalesce around one cautious player. Agent exposure: Neutral — the investigator has been observing without committing and wants to preserve their cover for future investigations.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 42e37cd6-541] (score: 0.8273)
**Situation:** Feeling pressure to act in an information-starved village, the investigator initiated a vote based on a weak behavioral read. Information landscape: There was no hard evidence, only speculative reads on communication style. The investigator's private check on player_2 had revealed a villager, narrowing the suspect pool only slightly. Game phase: Mid-game, after the first night kill. The village was directionless.
**Approach:** The investigator (player_1) broke the stalemate by accusing and voting for a player (player_5) who seemed to be deflecting by 'mirroring others' questions', hoping to force a reaction.
**Outcome:** The village followed the investigator's lead and eliminated a villager. This demonstrated that even a well-intentioned power role can cause significant harm by acting on poor-quality information.

### Memory 2 (observation) [key: b34d12c2-9d2] (score: 0.8159)
**Situation:** The Investigator was eliminated by a plurality vote while holding the identity of a wolf. Information landscape: The village was information-starved, and the vote was based on conflicting behavioral reads and frustration with a discussion deadlock. Game phase: Mid-game, after one night kill. The vote against the Investigator was the first elimination vote of the game. Consensus texture: A fragile consensus formed against the Investigator, driven by players frustrated with their aggressive but vague accusations.
**Approach:** The Investigator (player_1) chose not to reveal their role or their finding, maintaining their soft-pressure strategy until the end.
**Outcome:** The Investigator was eliminated, their role was revealed, and their valuable information was lost. The village was left demoralized and without direction.

### Memory 3 (observation) [key: 4619f4d5-ea2] (score: 0.8155)
**Situation:** The Investigator (Player 4) voted based on a private, behavioral read that contradicted the growing village consensus, placing them in a voting bloc with a wolf. Information landscape: The investigator had private information (Player 2 was a villager) but acted on a speculative read about another player. Game phase: Mid-game, during the first elimination vote where town consensus was critical. Social pressure: The vote placed the Investigator under immense, evidence-based social pressure the following day, as they had to defend voting with a now-revealed wolf.
**Approach:** The Investigator chose to act on a private read, voting against the correct wolf target (Player 7) and for the Healer (Player 8), contradicting the village consensus.
**Outcome:** The initial vote severely damaged the Investigator's credibility. However, their willingness to pivot and vote with the village on the final day allowed them to repair some trust and contribute to the win.

### Memory 4 (observation) [key: 7c0a6e6d-2be] (score: 0.8012)
**Situation:** The Investigator had a strong suspicion about a player but no definitive proof from their night action. Information landscape: Publicly, the game was information-starved, relying on gut reads. Game phase: Mid-game, during the very first elimination vote.
**Approach:** The Investigator, player_2, took the lead and cast the first vote against their suspect, player_8. This decisive action signaled confidence and rallied the other villagers to follow.
**Outcome:** The village successfully eliminated a wolf. However, this act of leadership made player_2 the clear target for the remaining wolf and they were killed the next night.

### Memory 5 (observation) [key: 5922bf88-e54] (score: 0.7854)
**Situation:** A strong but unsubstantiated consensus formed to vote out player_8. Information landscape: The landscape was information-starved regarding player_8; the Investigator had no information on them but knew player_1 was a villager. Game phase: Mid-game, during the first real vote after a healer save was announced. Consensus texture: A strong, swift consensus formed, with players quickly piling on one target.
**Approach:** The Investigator (player_6) chose to align with the group consensus and voted to eliminate player_8, who turned out to be the Healer.
**Outcome:** This vote was a catastrophic error, removing the town's only protective role and paving the way for the wolves to win.

### Memory 6 (strategy_point) [key: 4207be33-a2a] (score: 0.7766)
**Situation:** If you hold a private, speculative suspicion about a player, but the public village consensus is building strongly against someone else based on voting records or strong social reads. Information landscape: You have private knowledge from your investigations, but the public sphere is driven by concrete voting patterns. Game phase: Mid- to late-game, when a single dissenting vote can make you a primary suspect. Consensus texture: A strong, multi-player consensus is converging on a single target. Action: Abandon your speculative read and vote with the village consensus, unless you have investigated the consensus target and know they are innocent. Voting against a successful lynch will destroy your credibility and paint you as a wolf's ally.
**Action:** Abandon your speculative read and vote with the village consensus, unless you have investigated the consensus target and know they are innocent. Voting against a successful lynch will destroy your credibility and paint you as a wolf's ally.

### Memory 7 (strategy_point) [key: 57449d0c-1ba] (score: 0.7637)
**Situation:** When a strong, vibes-based consensus forms against a player without concrete evidence. Information landscape: The information landscape is starved regarding the target, but you have private information confirming other players are villagers, suggesting the target may be a town power role. Game phase: Mid- to late-game, when every vote is critical and losing a power role is devastating. Consensus texture: A strong bandwagon is forming based on social pressure rather than evidence. Action: Refuse to join the bandwagon vote. Casting a vote against your own strongest suspect, or even abstaining, is better than contributing to the potential elimination of a town power role based on social pressure.
**Action:** Refuse to join the bandwagon vote. Your vote lends credibility. Casting a vote against your own strongest suspect, or even abstaining, is better than contributing to the potential elimination of a town power role based on social pressure.

### Memory 8 (strategy_point) [key: 6710c4b7-412] (score: 0.7312)
**Situation:** If you have privately confirmed a player is a wolf, and you see the village independently reach the same conclusion based on strong public evidence. Information landscape: The public evidence is strong and sufficient on its own to secure the elimination. Game phase: Mid- to endgame, when preserving your role is critical. Consensus texture: A strong, organic consensus has formed against your target without your intervention.
**Action:** Stay quiet and simply vote with the majority. There is no need to reveal your role or your findings, as intervening adds no value, risks exposing you if the vote fails, and wastes the advantage of having a secret confirmed role for the next night.

## Response for Case 29

Rate each of the 8 memories above. JSON format:
```json
[
  {"idx": 1, "key": "42e37cd6-541", "type": "observation", "relevance": _},
  {"idx": 2, "key": "b34d12c2-9d2", "type": "observation", "relevance": _},
  {"idx": 3, "key": "4619f4d5-ea2", "type": "observation", "relevance": _},
  {"idx": 4, "key": "7c0a6e6d-2be", "type": "observation", "relevance": _},
  {"idx": 5, "key": "5922bf88-e54", "type": "observation", "relevance": _},
  {"idx": 6, "key": "4207be33-a2a", "type": "strategy_point", "relevance": _},
  {"idx": 7, "key": "57449d0c-1ba", "type": "strategy_point", "relevance": _},
  {"idx": 8, "key": "6710c4b7-412", "type": "strategy_point", "relevance": _}
]
```