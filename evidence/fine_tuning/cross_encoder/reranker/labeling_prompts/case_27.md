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

# Case 27: healer — day_vote (day 3 round 4)

## Game State (what the player sees)
```
================================================================================
CASE cdcd2c6e46f59a85cad3d634c3595a67:e20e2e15052855a1 | healer | day 3 round 4 | day_vote
================================================================================

Role: healer
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

--- Strategy note ---
Player 3 and 8 are relying purely on 'both-sides' rhetoric, which mirrors the behavior of wolves in past games who attempt to sow doubt when cornered by evidence. Since they have failed to provide a specific, non-defensive reason for their actions, I am committed to voting for Player 3. I will focus my remaining energy on staying under the radar as the healer to ensure my survival tonight.

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

**Situation 1:** Three players have formed a unified bloc demanding that a cautious duo explain their coordinated inaction, while the duo accuses the bloc of being a wolf team using coordinated pressure. The discussion has devolved into mutual accusations of coordination with neither side presenting new evidence. Information landscape: Information-rich with the Day 2 voting record, but the mislynch has poisoned trust — the aggressive faction was wrong about their target, yet they are using the same rhetoric again. Game phase: Endgame-adjacent, 5 players remaining; one wrong vote likely hands the game to wolves. Consensus texture: Entrenched — both sides have hardened positions with declared vote targets and no possibility of compromise. Agent exposure: The healer is part of the three-player bloc and has committed to voting for a cautious player; the healer's identity remains hidden but they risk being targeted overnight if the bloc successfully eliminates someone.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 6aca8c49-eae] (score: 0.7984)
**Situation:** Endgame, with a strong, evidence-based consensus forming against the likely final wolf. The information landscape is rich, driven by voting records. The Healer is not the primary target but may be under minor suspicion or have slight personal doubts.
**Approach:** Voted with the majority to eliminate the wolf (1x), Voiced concern but ultimately voted with the majority (1x).
**Outcome:** Successfully eliminated the final wolf, securing a win for the village. This approach avoided a split vote and solidified the Healer's position as a team player.

### Memory 2 (observation) [key: 42f30e10-562] (score: 0.7892)
**Situation:** In the final vote with four players remaining, the Healer (player 2) was targeted for their passive communication style throughout the game. Information landscape: The information was based entirely on social reads and voting history, as no confirmed roles were left in play. Game phase: Endgame, with one wolf remaining. Social pressure: A coordinated push from the remaining wolf and two villagers targeted the Healer for consistently deflecting questions and not naming suspects.
**Approach:** The Healer attempted to defend their quietness as an observational strategy but failed to take a decisive stance until it was too late, only casting a vote after consensus had already formed against them.
**Outcome:** The Healer was voted out. This was the game-losing move, as it left the final wolf in a 2 vs. 1 situation, guaranteeing their victory.

### Memory 3 (observation) [key: a8ec1773-30f] (score: 0.7481)
**Situation:** A credible Investigator claim led to a strong consensus against a player who turned out to be a wolf. Information landscape: The village had a strong lead from the Investigator's claim, making the vote seem straightforward. Game phase: Mid-game, at the first elimination vote. Consensus texture: A strong, multi-player consensus was driven by the Investigator's specific, credible claim.
**Approach:** The Healer (player_8), fearing a potential wolf-led bandwagon, voted against the Investigator instead of the accused wolf. This was the only vote against the Investigator besides the wolf's own.
**Outcome:** The wolf was eliminated, but the Healer's dissenting vote was recorded. The next day, after the Investigator was killed, this vote became irrefutable evidence that led to the Healer being mislynched.

### Memory 4 (strategy_point) [key: 182ebc43-053] (score: 0.7369)
**Situation:** In the mid-game or endgame, a strong consensus is forming against a player, either driven by evidence-based information like voting records or by a credible Investigator claim. You feel uneasy about the target despite the strength of the consensus, and you are not currently under significant suspicion yourself.
**Action:** Briefly voice your skepticism to ensure all angles are considered, but do not cast a lone protest vote against the consensus. Unless you can provide concrete counter-evidence, vote with the group or abstain; voting against the group risks a split vote that is more likely to save a wolf than expose a conspiracy, and it makes you a primary suspect if the claim or evidence is proven true.

### Memory 5 (strategy_point) [key: 4922ee84-da7] (score: 0.7331)
**Situation:** In the mid-game or endgame, a strong consensus is forming against a player based on voting records or other public evidence. You are currently under minor suspicion for a past action, and you need to manage this heat while the village focuses on another target.
**Action:** Do not aggressively defend your past actions, as this can make you seem defensive and draw more suspicion. Instead, vote with the emerging majority to align yourself with the village, help eliminate a likely threat, and reduce the focus on you.

## Response for Case 27

Rate each of the 5 memories above. JSON format:
```json
[
  {"idx": 1, "key": "6aca8c49-eae", "type": "observation", "relevance": _},
  {"idx": 2, "key": "42f30e10-562", "type": "observation", "relevance": _},
  {"idx": 3, "key": "a8ec1773-30f", "type": "observation", "relevance": _},
  {"idx": 4, "key": "182ebc43-053", "type": "strategy_point", "relevance": _},
  {"idx": 5, "key": "4922ee84-da7", "type": "strategy_point", "relevance": _}
]
```