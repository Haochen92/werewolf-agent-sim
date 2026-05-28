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

# Case 25: healer — day_vote (day 2 round 4)

## Game State (what the player sees)
```
================================================================================
CASE cdcd2c6e46f59a85cad3d634c3595a67:a5cf867687cc2f4f | healer | day 2 round 4 | day_vote
================================================================================

Role: healer
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
Maintain a low profile to avoid being a wolf target. Observe the vocal players to see who is pushing for a lynch and who is urging caution. I will continue to act as a neutral participant to keep my role hidden while keeping my protection ability for a crucial night.

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

**Situation 1:** The village is deadlocked between a vocal faction demanding an immediate vote and a cautious duo who refuse to name suspects, arguing that a forced vote helps wolves. The vocal faction has escalated to directly voting for the most cautious player, framing their inaction as wolf-aligned behavior. Information landscape: Information-starved — no voting records, no role claims; the only evidence is the communication-style difference between the two factions. Game phase: Early game, first vote with 7 players; the village risks either a mislynch based on tone or no elimination at all. Consensus texture: Fragile and combative — the village is split into two camps arguing about whether voting itself is helpful. Agent exposure: The healer is maintaining a low profile within the cautious group but needs to avoid drawing wolf attention while deciding whether the aggressive or cautious players are more likely to be wolves.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 42f30e10-562] (score: 0.7983)
**Situation:** In the final vote with four players remaining, the Healer (player 2) was targeted for their passive communication style throughout the game. Information landscape: The information was based entirely on social reads and voting history, as no confirmed roles were left in play. Game phase: Endgame, with one wolf remaining. Social pressure: A coordinated push from the remaining wolf and two villagers targeted the Healer for consistently deflecting questions and not naming suspects.
**Approach:** The Healer attempted to defend their quietness as an observational strategy but failed to take a decisive stance until it was too late, only casting a vote after consensus had already formed against them.
**Outcome:** The Healer was voted out. This was the game-losing move, as it left the final wolf in a 2 vs. 1 situation, guaranteeing their victory.

### Memory 2 (observation) [key: a8ec1773-30f] (score: 0.7931)
**Situation:** A credible Investigator claim led to a strong consensus against a player who turned out to be a wolf. Information landscape: The village had a strong lead from the Investigator's claim, making the vote seem straightforward. Game phase: Mid-game, at the first elimination vote. Consensus texture: A strong, multi-player consensus was driven by the Investigator's specific, credible claim.
**Approach:** The Healer (player_8), fearing a potential wolf-led bandwagon, voted against the Investigator instead of the accused wolf. This was the only vote against the Investigator besides the wolf's own.
**Outcome:** The wolf was eliminated, but the Healer's dissenting vote was recorded. The next day, after the Investigator was killed, this vote became irrefutable evidence that led to the Healer being mislynched.

### Memory 3 (observation) [key: 6aca8c49-eae] (score: 0.7911)
**Situation:** Endgame, with a strong, evidence-based consensus forming against the likely final wolf. The information landscape is rich, driven by voting records. The Healer is not the primary target but may be under minor suspicion or have slight personal doubts.
**Approach:** Voted with the majority to eliminate the wolf (1x), Voiced concern but ultimately voted with the majority (1x).
**Outcome:** Successfully eliminated the final wolf, securing a win for the village. This approach avoided a split vote and solidified the Healer's position as a team player.

### Memory 4 (strategy_point) [key: 182ebc43-053] (score: 0.7458)
**Situation:** In the mid-game or endgame, a strong consensus is forming against a player, either driven by evidence-based information like voting records or by a credible Investigator claim. You feel uneasy about the target despite the strength of the consensus, and you are not currently under significant suspicion yourself.
**Action:** Briefly voice your skepticism to ensure all angles are considered, but do not cast a lone protest vote against the consensus. Unless you can provide concrete counter-evidence, vote with the group or abstain; voting against the group risks a split vote that is more likely to save a wolf than expose a conspiracy, and it makes you a primary suspect if the claim or evidence is proven true.

### Memory 5 (strategy_point) [key: 4922ee84-da7] (score: 0.7458)
**Situation:** In the mid-game or endgame, a strong consensus is forming against a player based on voting records or other public evidence. You are currently under minor suspicion for a past action, and you need to manage this heat while the village focuses on another target.
**Action:** Do not aggressively defend your past actions, as this can make you seem defensive and draw more suspicion. Instead, vote with the emerging majority to align yourself with the village, help eliminate a likely threat, and reduce the focus on you.

## Response for Case 25

Rate each of the 5 memories above. JSON format:
```json
[
  {"idx": 1, "key": "42f30e10-562", "type": "observation", "relevance": _},
  {"idx": 2, "key": "a8ec1773-30f", "type": "observation", "relevance": _},
  {"idx": 3, "key": "6aca8c49-eae", "type": "observation", "relevance": _},
  {"idx": 4, "key": "182ebc43-053", "type": "strategy_point", "relevance": _},
  {"idx": 5, "key": "4922ee84-da7", "type": "strategy_point", "relevance": _}
]
```