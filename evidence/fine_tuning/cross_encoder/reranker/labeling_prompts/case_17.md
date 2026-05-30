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

# Case 17: healer — day_vote (day 2 round 2)

## Game State (what the player sees)
```
================================================================================
CASE 8e437de2eab2d9d54e45ed4dee61fe54:878d61545c98af70 | healer | day 2 round 2 | day_vote
================================================================================

Role: healer
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
Continue maintaining a low profile to avoid being identified as the healer. Do not volunteer new theories unless there is a clear shift in player behavior or a specific accusation to address. Focus on blending in with the general consensus to stay off the wolves' radar.

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

**Situation 1:** The healer successfully saved a player on night 1, but the subsequent discussion produced no leads — all players made generic comments about the save without naming suspects. The village enters its first vote with zero differentiation between players. Information landscape: Information-starved — the healer save confirmed one wolf target but generated no actionable suspicion. Game phase: Early game, first vote with all 8 players alive; no behavioral differentiation has emerged. Consensus texture: No consensus — every player's contribution is interchangeable. Agent exposure: The healer must blend in as a generic villager; the lack of discussion content means any distinctive contribution risks standing out.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 42f30e10-562] (score: 0.7802)
**Situation:** In the final vote with four players remaining, the Healer (player 2) was targeted for their passive communication style throughout the game. Information landscape: The information was based entirely on social reads and voting history, as no confirmed roles were left in play. Game phase: Endgame, with one wolf remaining. Social pressure: A coordinated push from the remaining wolf and two villagers targeted the Healer for consistently deflecting questions and not naming suspects.
**Approach:** The Healer attempted to defend their quietness as an observational strategy but failed to take a decisive stance until it was too late, only casting a vote after consensus had already formed against them.
**Outcome:** The Healer was voted out. This was the game-losing move, as it left the final wolf in a 2 vs. 1 situation, guaranteeing their victory.

### Memory 2 (observation) [key: 6aca8c49-eae] (score: 0.7770)
**Situation:** Endgame, with a strong, evidence-based consensus forming against the likely final wolf. The information landscape is rich, driven by voting records. The Healer is not the primary target but may be under minor suspicion or have slight personal doubts.
**Approach:** Voted with the majority to eliminate the wolf (1x), Voiced concern but ultimately voted with the majority (1x).
**Outcome:** Successfully eliminated the final wolf, securing a win for the village. This approach avoided a split vote and solidified the Healer's position as a team player.

### Memory 3 (observation) [key: a8ec1773-30f] (score: 0.7536)
**Situation:** A credible Investigator claim led to a strong consensus against a player who turned out to be a wolf. Information landscape: The village had a strong lead from the Investigator's claim, making the vote seem straightforward. Game phase: Mid-game, at the first elimination vote. Consensus texture: A strong, multi-player consensus was driven by the Investigator's specific, credible claim.
**Approach:** The Healer (player_8), fearing a potential wolf-led bandwagon, voted against the Investigator instead of the accused wolf. This was the only vote against the Investigator besides the wolf's own.
**Outcome:** The wolf was eliminated, but the Healer's dissenting vote was recorded. The next day, after the Investigator was killed, this vote became irrefutable evidence that led to the Healer being mislynched.

### Memory 4 (strategy_point) [key: 4922ee84-da7] (score: 0.7139)
**Situation:** In the mid-game or endgame, a strong consensus is forming against a player based on voting records or other public evidence. You are currently under minor suspicion for a past action, and you need to manage this heat while the village focuses on another target.
**Action:** Do not aggressively defend your past actions, as this can make you seem defensive and draw more suspicion. Instead, vote with the emerging majority to align yourself with the village, help eliminate a likely threat, and reduce the focus on you.

### Memory 5 (strategy_point) [key: 182ebc43-053] (score: 0.7055)
**Situation:** In the mid-game or endgame, a strong consensus is forming against a player, either driven by evidence-based information like voting records or by a credible Investigator claim. You feel uneasy about the target despite the strength of the consensus, and you are not currently under significant suspicion yourself.
**Action:** Briefly voice your skepticism to ensure all angles are considered, but do not cast a lone protest vote against the consensus. Unless you can provide concrete counter-evidence, vote with the group or abstain; voting against the group risks a split vote that is more likely to save a wolf than expose a conspiracy, and it makes you a primary suspect if the claim or evidence is proven true.

## Response for Case 17

Rate each of the 5 memories above. JSON format:
```json
[
  {"idx": 1, "key": "42f30e10-562", "type": "observation", "relevance": _},
  {"idx": 2, "key": "6aca8c49-eae", "type": "observation", "relevance": _},
  {"idx": 3, "key": "a8ec1773-30f", "type": "observation", "relevance": _},
  {"idx": 4, "key": "4922ee84-da7", "type": "strategy_point", "relevance": _},
  {"idx": 5, "key": "182ebc43-053", "type": "strategy_point", "relevance": _}
]
```